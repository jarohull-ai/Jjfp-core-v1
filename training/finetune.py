"""
JFP-Core-v1 LoRA Fine-tuning Script
Model:    Qwen/Qwen2.5-1.5B-Instruct
Hardware: AMD RX 9060 XT 8GB VRAM + ROCm
Method:   LoRA (bfloat16, no bitsandbytes — not supported on ROCm)
"""

import os

# ─── ROCm / GPU Hang prevention — MUST be set before torch import ─────────────
os.environ["HSA_ENABLE_SDMA"]        = "0"          # wyłącz SDMA — główna przyczyna GPU Hang na RDNA4
os.environ["ROCR_VISIBLE_DEVICES"]   = "0"          # explicit GPU 0
os.environ["PYTORCH_HIP_ALLOC_CONF"] = "max_split_size_mb:512"  # ogranicz fragmentację VRAM
os.environ["HSA_OVERRIDE_GFX_VERSION"] = "11.0.0"  # gfx1200 (RDNA4) → emuluj gfx1100 (RDNA3) dla PyTorch 2.5.1+rocm6.2

import json
import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
)
from peft import (
    LoraConfig,
    get_peft_model,
    TaskType,
)

# ─── CONFIG ──────────────────────────────────────────────────────────────────
MODEL_ID       = "Qwen/Qwen2.5-1.5B-Instruct"
DATASET_PATH   = "/home/jaro/Jjfp-core-v1/training/dataset.jsonl"
OUTPUT_DIR     = "/home/jaro/Jjfp-core-v1/jfp-lora-adapter"
MAX_SEQ_LENGTH = 512
BATCH_SIZE     = 2
GRAD_ACCUM     = 4
LEARNING_RATE  = 2e-4
NUM_EPOCHS     = 3
LORA_R         = 16
LORA_ALPHA     = 32
LORA_DROPOUT   = 0.05
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj"]
IGNORE_INDEX   = -100

# ─── DEVICE CHECK ────────────────────────────────────────────────────────────
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {device}")
if device == "cuda":
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

# ─── LOAD TOKENIZER ──────────────────────────────────────────────────────────
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(
    MODEL_ID,
    trust_remote_code=True,
    padding_side="right",
)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# ─── LOAD DATASET (przed modelem — potrzebny do warmup_steps) ────────────────
print("Loading dataset...")
raw_data = []
with open(DATASET_PATH, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            raw_data.append(json.loads(line))
print(f"Loaded {len(raw_data)} examples.")

# ─── LOAD MODEL (bfloat16, explicit cuda:0 — stabilne na ROCm/RDNA4) ─────────
print("Loading model in bfloat16...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.bfloat16,
    device_map={"": "cuda:0"},
    trust_remote_code=True,
)
model.config.use_cache = False
model.config.pretraining_tp = 1

# ─── ROCm/RDNA4 PATCH ────────────────────────────────────────────────────────
# peft 0.19.1 używa cast_adapter_dtype — wyłącz, bo HIP nie obsługuje fp32→fp16 cast
try:
    import peft.tuners.tuners_utils as _tuners_utils
    for _fn in ("cast_adapter_dtype", "_cast_adapter_dtype", "cast_mixed_precision_params"):
        if hasattr(_tuners_utils, _fn):
            setattr(_tuners_utils, _fn, lambda *a, **kw: None)
            print(f"[OK] ROCm patch: {_fn} neutralized (peft {__import__('peft').__version__})")
except Exception as e:
    print(f"[WARN] ROCm patch failed: {e}")

# ─── LORA CONFIG ─────────────────────────────────────────────────────────────
lora_config = LoraConfig(
    r=LORA_R,
    lora_alpha=LORA_ALPHA,
    lora_dropout=LORA_DROPOUT,
    target_modules=TARGET_MODULES,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)

model = get_peft_model(model, lora_config)

# Utrzymaj wagi adaptera w bfloat16 — zgodność z dtype modelu na ROCm
for name, param in model.named_parameters():
    if param.requires_grad:
        param.data = param.data.to(torch.bfloat16)
model.print_trainable_parameters()

# ─── TOKENIZE z maskowaniem labels ───────────────────────────────────────────
def tokenize(example):
    """
    Tokenizuje przykład z chat template Qwen2.5.
    Maskuje tokeny system+user w labels (IGNORE_INDEX=-100),
    model uczy się generować TYLKO odpowiedź assistant.
    """
    messages = example["messages"]

    # Pełny tekst: system + user + assistant
    full_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False,
    )
    # Prefix: system + user (bez ostatniej odpowiedzi assistant)
    prefix_text = tokenizer.apply_chat_template(
        messages[:-1],
        tokenize=False,
        add_generation_prompt=True,  # dodaje <|im_start|>assistant\n
    )

    tokenized = tokenizer(
        full_text,
        truncation=True,
        max_length=MAX_SEQ_LENGTH,
        padding="max_length",
        return_tensors=None,
    )
    prefix_ids = tokenizer(
        prefix_text,
        truncation=True,
        max_length=MAX_SEQ_LENGTH,
        return_tensors=None,
    )["input_ids"]
    prefix_len = len(prefix_ids)

    # Maskuj system+user — gradient tylko na tokenach assistant
    labels = tokenized["input_ids"].copy()
    labels[:prefix_len] = [IGNORE_INDEX] * prefix_len
    tokenized["labels"] = labels
    return tokenized

dataset = Dataset.from_list(raw_data)
tokenized_dataset = dataset.map(
    tokenize,
    remove_columns=dataset.column_names,
    desc="Tokenizing",
)

# ─── TRAINING ARGUMENTS ──────────────────────────────────────────────────────
# warmup_steps skalowany do rozmiaru datasetu (~5% kroków)
steps_per_epoch = len(raw_data) // (BATCH_SIZE * GRAD_ACCUM)
total_steps     = steps_per_epoch * NUM_EPOCHS
warmup_steps    = max(10, total_steps // 20)
print(f"Steps/epoch: {steps_per_epoch} | Total steps: {total_steps} | Warmup: {warmup_steps}")

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRAD_ACCUM,
    learning_rate=LEARNING_RATE,
    lr_scheduler_type="cosine",
    warmup_steps=warmup_steps,
    fp16=False,
    bf16=True,
    logging_steps=10,
    logging_first_step=True,
    save_strategy="epoch",
    save_total_limit=2,
    optim="adamw_torch",
    report_to="none",
    gradient_checkpointing=True,
    dataloader_pin_memory=False,
    # ROCm/RDNA4 fix: wyłącz num_items_in_batch — powoduje HIP kernel error na gfx1201
    average_tokens_across_devices=False,
)

# ─── DATA COLLATOR ───────────────────────────────────────────────────────────
data_collator = DataCollatorForSeq2Seq(
    tokenizer=tokenizer,
    model=model,
    padding=True,
    pad_to_multiple_of=8,
    label_pad_token_id=IGNORE_INDEX,
)

# ─── ROCm/RDNA4 PATCH: wyłącz _get_num_items_in_batch — powoduje HIP kernel error ──
# Transformers próbuje liczyć tokeny na GPU przez .ne(-100).sum() — crash na gfx1201
from transformers import Trainer as _BaseTrainer

class ROCmTrainer(_BaseTrainer):
    def _get_num_items_in_batch(self, batch_samples, device=None):
        # Zwróć None — Trainer pominie normalizację loss per-token
        return None

# ─── TRAINER ─────────────────────────────────────────────────────────────────
trainer = ROCmTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator,
    processing_class=tokenizer,
)

# ─── TRAIN ───────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("Starting LoRA training on ROCm...")
print(f"Dataset: {len(raw_data)} examples | Epochs: {NUM_EPOCHS}")
print(f"{'='*60}\n")
trainer.train()

# ─── SAVE ADAPTER ────────────────────────────────────────────────────────────
print("Saving LoRA adapter...")
os.makedirs(OUTPUT_DIR, exist_ok=True)
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print(f"\n{'='*60}")
print("TRAINING COMPLETE")
print(f"Adapter saved to: {OUTPUT_DIR}")
print(f"{'='*60}")
