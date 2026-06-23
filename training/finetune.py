"""
JFP-Core-v1 LoRA Fine-tuning Script
Model:    Qwen/Qwen2.5-7B-Instruct
Hardware: AMD RX 9060 XT 8GB VRAM + ROCm
Method:   LoRA (fp16, no bitsandbytes — not supported on ROCm)
"""

import os
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

# ─── DEVICE CHECK ────────────────────────────────────────────────────────────
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {device}")
if device == "cuda":
    print(f"GPU: {torch.cuda.get_device_name(0)}")

# ─── LOAD TOKENIZER ──────────────────────────────────────────────────────────
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(
    MODEL_ID,
    trust_remote_code=True,
    padding_side="right",
)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# ─── LOAD MODEL (fp16, no quantization) ──────────────────────────────────────
print("Loading model in fp16...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True,
)
model.config.use_cache = False
model.config.pretraining_tp = 1

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
model.print_trainable_parameters()

# ─── LOAD DATASET ────────────────────────────────────────────────────────────
print("Loading dataset...")
raw_data = []
with open(DATASET_PATH, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            raw_data.append(json.loads(line))
print(f"Loaded {len(raw_data)} examples.")

# ─── TOKENIZE ────────────────────────────────────────────────────────────────
def tokenize(example):
    """Apply Qwen2.5 chat template and tokenize."""
    text = tokenizer.apply_chat_template(
        example["messages"],
        tokenize=False,
        add_generation_prompt=False,
    )
    tokenized = tokenizer(
        text,
        truncation=True,
        max_length=MAX_SEQ_LENGTH,
        padding="max_length",
        return_tensors=None,
    )
    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized

dataset = Dataset.from_list(raw_data)
tokenized_dataset = dataset.map(
    tokenize,
    remove_columns=dataset.column_names,
    desc="Tokenizing",
)

# ─── TRAINING ARGUMENTS ──────────────────────────────────────────────────────
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=NUM_EPOCHS,
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRAD_ACCUM,
    learning_rate=LEARNING_RATE,
    lr_scheduler_type="cosine",
    warmup_ratio=0.05,
    fp16=True,
    bf16=False,
    logging_steps=10,
    save_strategy="epoch",
    save_total_limit=2,
    optim="adamw_torch",
    report_to="none",
    gradient_checkpointing=True,
    group_by_length=True,
    dataloader_pin_memory=False,
)

# ─── DATA COLLATOR ───────────────────────────────────────────────────────────
data_collator = DataCollatorForSeq2Seq(
    tokenizer=tokenizer,
    model=model,
    padding=True,
    pad_to_multiple_of=8,
)

# ─── TRAINER ─────────────────────────────────────────────────────────────────
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    data_collator=data_collator,
    tokenizer=tokenizer,
)

# ─── TRAIN ───────────────────────────────────────────────────────────────────
print("Starting LoRA training on ROCm...")
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
