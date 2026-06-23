"""
JFP LoRA Fine-tuning - Qwen2.5-1.5B na CPU
Minimalny skrypt treningowy bez GPU/Colab
"""

import os
import sys
import logging
import torch
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    TrainerCallback,
)
from peft import LoraConfig, get_peft_model, TaskType
from huggingface_hub import HfApi

# ── Konfiguracja ──────────────────────────────────────────────
MODEL_NAME = "Qwen/Qwen2.5-1.5B"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "jfp-lora-adapter")
MAX_LENGTH = 512
EPOCHS = 3
BATCH_SIZE = 1
LR = 2e-4
DATASET_PATH = os.path.join(os.path.dirname(__file__), "training", "dataset.jsonl")
LOG_PATH     = os.path.join(os.path.dirname(__file__), "training", "train_full.log")
HF_REPO_ID   = "jarohullowicki/jfp-lora-qwen2.5-1.5b"

# ── Logger (plik + stdout) ────────────────────────────────────
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_PATH, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("jfp")

class ProgressCallback(TrainerCallback):
    """Loguje postęp co 100 kroków."""
    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs and state.global_step % 100 == 0 and state.global_step > 0:
            loss = logs.get("loss", "?")
            lr   = logs.get("learning_rate", "?")
            log.info(
                f"[KROK {state.global_step:>4}/{state.max_steps}] "
                f"epoch={state.epoch:.2f}  loss={loss}  lr={lr}"
            )

def main():
    log.info("=" * 60)
    log.info("JFP LoRA Fine-tuning - Qwen2.5-1.5B @ CPU")
    log.info("=" * 60)

    device = torch.device("cpu")
    log.info(f"Urządzenie: {device}")

    # ── Tokenizer ─────────────────────────────────────────────
    log.info(f"[1/5] Ładowanie tokenizera: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # ── Model ─────────────────────────────────────────────────
    log.info("[2/5] Ładowanie modelu (CPU, float32)...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float32,   # float32 dla CPU
        device_map="cpu",
        trust_remote_code=True,
    )
    model.config.use_cache = False

    # ── LoRA ──────────────────────────────────────────────────
    log.info("[3/5] Konfiguracja LoRA...")
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # ── Dataset ───────────────────────────────────────────────
    log.info("[4/5] Przygotowanie danych...")
    raw_dataset = Dataset.from_json(DATASET_PATH)
    log.info(f"  Załadowano przykładów: {len(raw_dataset)}")

    def format_and_tokenize(example):
        # Konwertuj format chat (messages) na płaski tekst
        parts = []
        for msg in example["messages"]:
            role = msg["role"].upper()
            parts.append(f"### {role}:\n{msg['content']}")
        text = "\n\n".join(parts)
        out = tokenizer(
            text,
            truncation=True,
            max_length=MAX_LENGTH,
            padding="max_length",
        )
        out["labels"] = out["input_ids"][:]
        return out

    tokenized = raw_dataset.map(format_and_tokenize, remove_columns=raw_dataset.column_names)

    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    # ── Trening ───────────────────────────────────────────────
    log.info("[5/5] Rozpoczynam trening...")
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=4,
        learning_rate=LR,
        fp16=False,                   # wyłączone dla CPU
        bf16=False,
        logging_steps=100,
        save_strategy="epoch",
        report_to="none",
        use_cpu=True,
        dataloader_num_workers=0,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized,
        data_collator=data_collator,
        callbacks=[ProgressCallback()],
    )

    trainer.train()

    # ── Zapis adaptera ─────────────────────────────────────────
    log.info(f"Zapisywanie adaptera LoRA do: {OUTPUT_DIR}")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    log.info("✓ Adapter zapisany lokalnie.")

    # ── Push na HF Hub ─────────────────────────────────────────
    log.info(f"Wysyłanie adaptera na HF Hub: {HF_REPO_ID}")
    try:
        model.push_to_hub(HF_REPO_ID, commit_message="JFP LoRA adapter - Qwen2.5-1.5B CPU training")
        tokenizer.push_to_hub(HF_REPO_ID, commit_message="JFP tokenizer")
        log.info(f"✓ Push zakończony: https://huggingface.co/{HF_REPO_ID}")
    except Exception as e:
        log.error(f"✗ Push nieudany: {e}")
        log.info(f"  Adapter dostępny lokalnie: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
