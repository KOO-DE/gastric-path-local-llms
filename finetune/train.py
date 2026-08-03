"""
LoRA Fine-tuning Main Training Script
- Input: (pathology report text, ground-truth JSON) pairs
- Output: fine-tuned LoRA adapter
- --use_ksp: include KSP guidelines in the system prompt
- Supports Qwen/Gemma3/Llama via apply_chat_template
"""

import argparse
import json
import math
import os
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset
from config import EXPERIMENTS

# ── Argument parsing ───────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--model_path", required=True, help="Model path")
parser.add_argument("--exp", required=True, choices=["A", "B"], help="Experiment selection")
parser.add_argument("--train_data", default=None)
parser.add_argument("--val_data",   default=None)
parser.add_argument("--output_dir", default=None)
parser.add_argument("--use_ksp", action="store_true", help="Include KSP guidelines in system prompt")
args = parser.parse_args()

cfg = EXPERIMENTS[args.exp]
if args.train_data: cfg["train_data"] = args.train_data
if args.val_data:   cfg["val_data"]   = args.val_data
if args.output_dir: cfg["output_dir"] = args.output_dir

if args.use_ksp and args.output_dir is None:
    cfg["output_dir"] = cfg["output_dir"] + "_ksp"

print(f"\n{'='*60}")
print(f"Experiment: {cfg['exp_name']} | Model: {args.model_path}")
print(f"LoRA r={cfg['lora_r']}, alpha={cfg['lora_alpha']}, lr={cfg['learning_rate']}")
print(f"KSP guidelines: {'included' if args.use_ksp else 'excluded'}")
print(f"Output: {cfg['output_dir']}")
print(f"{'='*60}\n")

# ── System Prompt ──────────────────────────────────────────────────────────────
KSP_GUIDELINE = """
[Korean Society of Pathologists - Standardized Pathology Report for Gastric Cancer, 2nd Edition (2023)]

GROSS TYPE:
- Early gastric cancer (EGC): Type I, IIa, IIb, IIc, III (Japanese guideline)
- Advanced gastric cancer (AGC): Borrmann type 1, 2, 3, 4, unclassifiable (type 5)

TUMOR LOCATION:
- Involvement: Upper/Middle/Lower third of stomach, Esophagus, Duodenum
- Center: Cardia/Fundus/Body/Antrum/Pylorus + Lesser/Greater curvature/Anterior/Posterior wall

HISTOLOGIC TYPE (WHO 5th edition):
- Tubular adenocarcinoma (well/moderately/poorly differentiated)
- Papillary adenocarcinoma, Mucinous adenocarcinoma
- Poorly cohesive carcinoma (PCC): signet ring cell type / NOS
- Mixed adenocarcinoma, and others

LAUREN CLASSIFICATION:
- Intestinal: WD/MD tubular and papillary adenocarcinoma
- Diffuse: PCC and SRC
- Indeterminate: solid type PD adenocarcinoma
- Mixed: intestinal and diffuse in similar proportions

DIFFERENTIATION: Well differentiated (WD) / Moderately differentiated (MD) / Poorly differentiated (PD)

DEPTH OF INVASION (pT, AJCC 8th):
- pT1a: lamina propria/muscularis mucosae
- pT1b: submucosa, pT2: proper muscle, pT3: subserosa, pT4a: serosa, pT4b: adjacent structures

LYMPH NODE: metastasis in X out of Y regional lymph nodes
- pN0: 0, pN1: 1-2, pN2: 3-6, pN3a: 7-15, pN3b: >=16

LYMPHOVASCULAR INVASION / PERINEURAL INVASION: Not identified / Present
""".strip()

BASE_SYSTEM_PROMPT = """You are an expert pathologist specializing in gastric cancer pathology report analysis.
Extract the following fields from the given gastric cancer pathology report and return a JSON object.
Return ONLY a valid JSON object, no explanation."""

KSP_SYSTEM_PROMPT = """You are an expert pathologist specializing in gastric cancer pathology report analysis.

The following guidelines are from the Korean Society of Pathologists (KSP) Standardized Pathology Report for Gastric Cancer, 2nd Edition (2023). Use these as reference:

""" + KSP_GUIDELINE + """

---

Extract the following fields from the given gastric cancer pathology report and return a JSON object.
Return ONLY a valid JSON object, no explanation."""

SYSTEM_PROMPT = KSP_SYSTEM_PROMPT if args.use_ksp else BASE_SYSTEM_PROMPT

# ── Load tokenizer ─────────────────────────────────────────────────────────────
print("[1/5] Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(
    args.model_path,
    trust_remote_code=True,
)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.pad_token_id = tokenizer.eos_token_id

# ── Prompt template ────────────────────────────────────────────────────────────
def make_prompt(report: str, answer: dict = None) -> str:
    user_msg = "Pathology report:\n" + report + "\n\nExtract the fields as JSON:"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_msg},
    ]
    if answer is not None:
        messages.append({
            "role": "assistant",
            "content": json.dumps(answer, ensure_ascii=False)
        })
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )
    else:
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

# ── Load and tokenize data ─────────────────────────────────────────────────────
print("[2/5] Loading and tokenizing data...")

def load_jsonl(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]

def tokenize_dataset(records, max_length):
    input_ids_list = []
    labels_list = []

    for rec in records:
        # Full prompt (with answer)
        full_prompt = make_prompt(rec['report'], rec['answer'])
        # Prompt only (to determine assistant start position)
        prompt_only = make_prompt(rec['report'])

        full_tokens   = tokenizer.encode(full_prompt, add_special_tokens=False)
        prompt_tokens = tokenizer.encode(prompt_only, add_special_tokens=False)

        # Truncate
        if len(full_tokens) > max_length:
            full_tokens = full_tokens[:max_length]

        # Padding
        pad_len   = max_length - len(full_tokens)
        input_ids = full_tokens + [tokenizer.pad_token_id] * pad_len

        # Assistant response start position
        assistant_start = len(prompt_tokens)

        # Labels: set prompt tokens to -100 (exclude from loss), train only on assistant response
        labels = [-100] * assistant_start + full_tokens[assistant_start:]
        labels = labels[:max_length] + [-100] * pad_len

        input_ids_list.append(input_ids)
        labels_list.append(labels)

    return Dataset.from_dict({
        "input_ids": input_ids_list,
        "labels":    labels_list,
    })

train_records = load_jsonl(cfg["train_data"])
val_records   = load_jsonl(cfg["val_data"])

print(f"  train: {len(train_records)} records, val: {len(val_records)} records")

train_dataset = tokenize_dataset(train_records, cfg["max_seq_length"])
val_dataset   = tokenize_dataset(val_records,   cfg["max_seq_length"])
print(f"  Tokenization complete")

# ── Load model ─────────────────────────────────────────────────────────────────
print("\n[3/5] Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    args.model_path,
    torch_dtype=torch.bfloat16,
    trust_remote_code=True,
)
model.config.use_cache = False

# ── LoRA configuration ─────────────────────────────────────────────────────────
print("[4/5] Configuring LoRA...")
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=cfg["lora_r"],
    lora_alpha=cfg["lora_alpha"],
    target_modules=cfg["lora_target_modules"],
    lora_dropout=cfg["lora_dropout"],
    bias=cfg["lora_bias"],
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# ── Training ───────────────────────────────────────────────────────────────────
print("\n[5/5] Starting training...")

total_steps = math.ceil(
    len(train_dataset) / (cfg["per_device_train_batch_size"] * cfg["gradient_accumulation_steps"])
) * cfg["num_train_epochs"]
print(f"  Estimated total steps: {total_steps}")

training_args = TrainingArguments(
    output_dir=cfg["output_dir"],
    num_train_epochs=cfg["num_train_epochs"],
    per_device_train_batch_size=cfg["per_device_train_batch_size"],
    per_device_eval_batch_size=cfg["per_device_eval_batch_size"],
    gradient_accumulation_steps=cfg["gradient_accumulation_steps"],
    learning_rate=cfg["learning_rate"],
    lr_scheduler_type=cfg["lr_scheduler_type"],
    warmup_ratio=cfg["warmup_ratio"],
    weight_decay=cfg["weight_decay"],
    fp16=False,
    bf16=True,
    logging_steps=cfg["logging_steps"],
    save_steps=cfg["save_steps"],
    eval_steps=cfg["eval_steps"],
    eval_strategy="steps",
    save_total_limit=cfg["save_total_limit"],
    load_best_model_at_end=cfg["load_best_model_at_end"],
    metric_for_best_model=cfg["metric_for_best_model"],
    gradient_checkpointing=True,
    dataloader_num_workers=4,
    report_to=cfg["report_to"],
    ddp_find_unused_parameters=None,
)

def data_collator(features):
    input_ids = torch.tensor([f["input_ids"] for f in features], dtype=torch.long)
    labels    = torch.tensor([f["labels"]    for f in features], dtype=torch.long)
    return {"input_ids": input_ids, "labels": labels}

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    data_collator=data_collator,
)

trainer.train()

# ── Save ───────────────────────────────────────────────────────────────────────
print(f"\nSaving model to: {cfg['output_dir']}")

import gc
torch.cuda.empty_cache()
gc.collect()

model = model.cpu()
model.save_pretrained(cfg["output_dir"], safe_serialization=True, max_shard_size="2GB")
tokenizer.save_pretrained(cfg["output_dir"])
print("Done!")
