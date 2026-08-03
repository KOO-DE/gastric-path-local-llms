# Rule-Based versus LoRA Fine-Tuned Open-Source Large Language Models for Structured Extraction from Korean Gastric Cancer Pathology Reports

> **Rule-Based versus LoRA Fine-Tuned Open-Source Large Language Models for Structured Extraction from Korean Gastric Cancer Pathology Reports**
>
> Author information will be added upon publication.

---

## Overview

This repository contains the code for structured information extraction from gastric cancer surgical pathology reports using locally deployed open-source large language models (LLMs). We compare five open-source LLMs (with Qwen2.5-14B as sub-analysis) against a rule-based system across 16 standardized clinical fields, and evaluate the effect of LoRA fine-tuning and KSP 2nd Edition (Korean Society of Pathologists, 2023) guideline-based prompting.

---

## Key Features

- **16 clinical fields** extracted from gastric cancer surgical pathology reports
- **5 open-source LLMs** evaluated (+ Qwen2.5-14B for sub-analysis): Qwen2.5-7B, Gemma3-12B, Llama3.1-8B, Med42-8B, MedGemma-4B
- **3 prompting strategies**: Zero-shot, Few-shot, Chain-of-Thought (CoT)
- **KSP guideline integration**: Effect of KSP 2nd Edition (2023) as system prompt
- **LoRA fine-tuning**: ExpA (r=16) and ExpB (r=64) for Qwen2.5-7B, Gemma3-12B, Llama3.1-8B
    - ExpA = low-rank configuration (r=16, α=32, lr=2e-4)
    - ExpB = high-rank configuration (r=64, α=128, lr=1e-4)
- **Comparison with rule-based system** based on MySQL SQL queries
- **Local deployment**: All models run on-premise without external API calls

---

## Extracted Fields (16)

| Field | Type | Description |
|---|---|---|
| TumorLocation | array | Tumor location along stomach axis |
| TumorCircumference | array | Circumferential wall involvement |
| TumorSize | numeric | Largest tumor dimension (cm) |
| Histologic_type | array | WHO histologic type |
| Lauren_type | categorical | Lauren classification |
| Differentiation | array | Differentiation grade |
| ProximalMargin | numeric | Proximal resection margin distance (cm) |
| DistalMargin | numeric | Distal resection margin distance (cm) |
| LymphovascularInvasion | binary | Lymphovascular invasion (Yes/No) |
| PerineuralInvasion | binary | Perineural invasion (Yes/No) |
| T_stage | categorical | Pathologic T stage |
| N_stage | categorical | Pathologic N stage |
| M_stage | categorical | Pathologic M stage |
| Staging | categorical | AJCC 8th edition overall stage |
| MetastaticLymphNode | numeric | Number of metastatic lymph nodes |
| HarvestedLymphNode | numeric | Number of harvested lymph nodes |

---

## Repository Structure

```
├── baseline/                    # Baseline LLM extraction
│   ├── config_baseline.py       # Baseline prompt (Zero-shot / Few-shot / CoT)
│   ├── config_ksp.py            # KSP 2nd Edition guideline prompt
│   ├── extract_main.py          # Main extraction script (vLLM)
│   ├── utils.py                 # Data loading and parsing utilities
│   └── run_baseline.sh          # Automated experiment script
│
├── finetune/                    # LoRA fine-tuning
│   ├── config.py                # LoRA hyperparameters (ExpA / ExpB)
│   ├── prepare_finetune_data.py # Train/val/test data preparation
│   ├── train.py                 # Fine-tuning main script
│   ├── merge_adapter.py         # Merge LoRA adapter into base model
│   ├── test_qwen.py             # Qwen inference (vLLM)
│   ├── test_gemma.py            # Gemma3 inference (transformers)
│   └── test_llama.py            # Llama inference (vLLM)
│
├── rule_based/                  # Rule-based extraction system
│   ├── histologic_type.sql      # Histologic type
│   ├── differentiation.sql      # Differentiation grade
│   ├── lauren_type.sql          # Lauren classification
│   ├── invasion.sql             # Lymphovascular / perineural invasion
│   ├── lymph_node.sql           # Metastatic / harvested lymph node count
│   ├── margin.sql               # Proximal / distal resection margin
│   ├── tumor_site.sql           # Tumor location and circumference
│   ├── tumor_size.sql           # Tumor size
│   ├── staging.sql              # T/N/M stage and AJCC 8th overall stage
│   └── README.md                # Rule-based system documentation
│
├── evaluation.py                # Evaluation script (four-quadrant null handling)
├── metrics_ALL_configs.csv      # Aggregate performance metrics for all 40 configurations
└── requirements.txt             # Python dependencies
```

---

## Models

| Model Key | Model | Parameters | Domain |
|---|---|---|---|
| `qwen` | Qwen2.5-7B-Instruct | 7B | General |
| `qwen14b` | Qwen2.5-14B-Instruct | 14B | General (sub-analysis) |
| `gemma3` | Gemma3-12B-IT | 12B | General |
| `llama` | Llama-3.1-8B-Instruct | 8B | General |
| `med42` | Llama3-Med42-8B | 8B | Medical |
| `medgemma` | MedGemma-4B-IT | 4B | Medical |

---

## Environment

```bash
pip install -r requirements.txt
```

- Python 3.11
- CUDA 12.2
- NVIDIA A6000 × 4 (48GB each)

---

## Quick Start

### 1. Baseline Extraction

```bash
# Run all baseline experiments (Zero-shot / Few-shot / CoT)
bash baseline/run_baseline.sh baseline

# Run all KSP experiments
bash baseline/run_baseline.sh ksp

# Run all experiments
bash baseline/run_baseline.sh all
```

Or run a single model/strategy:

```bash
python baseline/extract_main.py \
    --model llama \
    --prompt_type few_shot \
    --input pathology_reports.xlsx \
    --output results/llama_few_shot.csv \
    --config baseline \
    --tensor_parallel 4
```

### 2. Fine-tuning

```bash
# Train (example: Llama3.1-8B ExpB)
CUDA_VISIBLE_DEVICES=0 python finetune/train.py \
    --model_path /path/to/Llama-3.1-8B-Instruct \
    --exp B \
    --train_data data/train.jsonl \
    --val_data data/val.jsonl \
    --output_dir models/llama_b

# Merge adapter
python finetune/merge_adapter.py \
    --base_model /path/to/Llama-3.1-8B-Instruct \
    --adapter_path models/llama_b \
    --output_path merge/llama_b

# Inference
python finetune/test_llama.py \
    --model_path merge/llama_b \
    --test_data data/test.jsonl \
    --output_dir results
```

### 3. Evaluation

```bash
python evaluation.py \
    --pred results/llama_b_pred.csv \
    --gold data/test.jsonl \
    --output metrics/llama_b_metrics.csv
```

---

## Main Results

### Baseline — Report-level Exact Match

| Model | Zero-shot | Few-shot | CoT |
|---|---|---|---|
| Qwen2.5-14B | 0.221 | 0.187 | 0.192 |
| Gemma3-12B | 0.036 | 0.186 | 0.050 |
| Llama3.1-8B | 0.015 | **0.302** | 0.037 |
| Qwen2.5-7B | 0.009 | 0.214 | 0.065 |
| Med42-8B | 0.013 | 0.133 | 0.002 |
| MedGemma-4B | 0.003 | 0.064 | 0.005 |

### Fine-tuning — Report-level Exact Match

| Model | Config | Report EM |
|---|---|---|
| Llama3.1-8B | Low-rank (r=16) | **0.7353** |
| Llama3.1-8B | High-rank (r=64) | 0.7311 |
| Gemma3-12B | High-rank (r=64) | 0.6975 |
| Qwen2.5-7B | High-rank (r=64) | 0.6975 |
| Gemma3-12B | Low-rank (r=16) | 0.6786 |
| Qwen2.5-7B | Low-rank (r=16) | 0.6597 |
| Rule-based | — | 0.4706 |

---

## Detailed Documentation

- [Baseline Extraction README](baseline/README.md)
- [Fine-tuning README](finetune/README.md)
- [Rule-based System README](rule_based/README.md)

---

## Citation

> Manuscript under preparation. Citation will be added upon publication.

---

## Data Availability

The pathology report texts and patient-level data used in this study are not publicly available due to patient privacy regulations and institutional policy. Researchers who wish to access the de-identified data may submit a reasonable request to the corresponding author, subject to IRB approval from Chungnam National University Hospital.

---

## Reproduction Guide

To reproduce the main results, follow the steps in order:

1. **Baseline extraction** — Run `baseline/run_baseline.sh` for all prompting strategies (Zero-shot, Few-shot, CoT) and KSP guideline variants.
2. **LoRA fine-tuning** — Prepare data with `finetune/prepare_finetune_data.py`, train with `finetune/train.py`, merge adapter with `finetune/merge_adapter.py`, and run inference with the model-specific scripts.
3. **Evaluation** — Run `evaluation.py` on the test set (476 records) to compute all metrics.

Note: Pathology report data is required to run the pipeline. See Data Availability above.

---

## metrics_ALL_configs.csv

This file contains aggregate performance metrics for all 40 evaluated configurations (rule-based, 5 baseline models × 3 strategies, 5 KSP-modified models × 3 strategies, Qwen2.5-14B × 3 strategies, and 3 fine-tuned models × 2 LoRA configurations). Key columns:

| Column | Description |
|---|---|
| `config` | Experiment configuration name |
| `Level` | `field` (per-variable) or `report` (report-level) |
| `Field` | Variable name or `ALL` for summary |
| `Type` | Variable type (array / categorical / numeric / binary) |
| `N` | Total number of test records (476) |
| `F1` | F1 Score (array / binary variables) |
| `MacroF1` | Macro F1 Score (categorical variables) |
| `Kappa` | Cohen's Kappa (categorical variables) |
| `TolAcc_0.5` | Tolerance Accuracy within ±0.5 cm (numeric variables) |
| `AUROC` | Area under ROC curve (binary variables) |
| `HallucinationRate` | Proportion of cases where model predicted a value despite gold being null |
| `MissRate_validGold` | Proportion of cases where gold has a value but model predicted null |
| `ReportExactMatch` | Proportion of reports where all 16 fields are correctly extracted |
| `OverallAverage_4Q` | Overall average accuracy across 16 fields (four-quadrant null handling) |
| `OverallAverage_ref` | Reference overall average (legacy null-exclusion method, not used in main analysis) |
