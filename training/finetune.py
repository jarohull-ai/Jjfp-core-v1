"""
JFP-Core-v1 QLoRA Fine-tuning Script
Model: Qwen/Qwen2.5-7B-Instruct
Hardware: RTX 2060 (6GB VRAM)
Method: QLoRA (4-bit quantization via bitsandbytes)
"""

import os
import json
import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
)
from peft import (
    LoraConfig,
    get_peft_model,
    TaskType,
    prepare_model_for_kbit_training,
)

# ─── CONFIG ──────────────────────────────────────────────────────────────────
MODEL_ID        = "Qwen/Qwen2.5-7B-Instruct"
DATASET_PATH    = os.path.join(os.path.dirname(__file__), "dataset.jsonl")
OUTPUT_DIR      = "./jfp-core-v1-lora"
MAX_SEQ_LENGTH  = 512
BATCH_SIZE      = 1
GRAD_ACCUM      = 8
LEARNING_RATE   = 2e-4
NUM_EPOCHS      = 3
LORA_R          = 16
LORA_ALPHA      = 32
LORA_DROPOUT    = 0.05
TARGET_MODULES  = ["q_proj", "k_proj", "v_proj", "o_proj"]

# ─── 4-BIT QUANTIZATION CONFIG ───────────────────────────────────────────────
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
)

# ─── LOAD TOKENIZER ──────────────────────────────────────────────────────────
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(
    MODEL_ID,
    trust_remote_code=True,
    padding_side="right",
)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# ─── LOAD MODEL ──────────────────────────────────────────────────────────────
print("Loading model in 4-bit (QLoRA)...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    quantization_config=bnb_config,
    device_map="auto",
    trust_remote_code=True,
    torch_dtype=torch.bfloat16,
)
model.config.use_cache = False
model.config.pretraining_tp = 1

# ─── PREPARE FOR KBIT TRAINING ───────────────────────────────────────────────
model = prepare_model_for_kbit_training(model)

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
    messages = example["messages"]
    # Apply chat template (Qwen2.5 format)
    text = tokenizer.apply_chat_template(
        messages,
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
    desc="Tokenizing dataset",
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
    fp16=False,
    bf16=True,
    logging_steps=10,
    save_strategy="epoch",
    save_total_limit=2,
    optim="paged_adamw_8bit",
    report_to="none",
    dataloader_pin_memory=False,
    gradient_checkpointing=True,
    group_by_length=True,
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
print("Starting QLoRA training...")
trainer.train()

# ─── SAVE ADAPTER ────────────────────────────────────────────────────────────
print("Saving LoRA adapter...")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print(f"\n{'='*60}")
print("TRAINING COMPLETE - adapter saved to ./jfp-core-v1-lora")
print(f"{'='*60}")
