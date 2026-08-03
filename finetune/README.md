# LoRA Fine-tuning

Experimental code for LoRA fine-tuning to extract information from gastric cancer pathology reports.

---

## File Structure

```
finetune/
├── config.py                   # LoRA hyperparameter settings (ExpA r=16 / ExpB r=64)
├── prepare_finetune_data.py    # Training data preparation (train/val/test split)
├── train.py                    # LoRA Fine-tuning main training script
├── merge_adapter.py            # LoRA adapter → base model merging
├── inference_qwen.py           # Qwen-series inference (vLLM-based)
├── inference_gemma.py          # Gemma3 inference (transformers-based)
└── inference_llama.py          # Llama-series inference (vLLM-based)
```

---

## Experimental Design

| Experiment | Model | LoRA r | alpha | Learning rate | KSP |
|---|---|---|---|---|---|
| ExpA | Qwen2.5-7B | 16 | 32 | 2e-4 | Excluded |
| ExpB | Qwen2.5-7B | 64 | 128 | 1e-4 | Excluded |
| ExpA+KSP | Qwen2.5-7B | 16 | 32 | 2e-4 | Included |
| ExpB+KSP | Qwen2.5-7B | 64 | 128 | 1e-4 | Included |
| ExpA | Gemma3-12B | 16 | 32 | 2e-4 | Excluded |
| ExpB | Gemma3-12B | 64 | 128 | 1e-4 | Excluded |
| ExpA | Llama3.1-8B | 16 | 32 | 2e-4 | Excluded |
| ExpB | Llama3.1-8B | 64 | 128 | 1e-4 | Excluded |
| ExpA+KSP | Llama3.1-8B | 16 | 32 | 2e-4 | Included |
| ExpB+KSP | Llama3.1-8B | 64 | 128 | 1e-4 | Included |

> Gemma3-12B KSP variant was excluded due to OOM during training.

---

## Common Training Configuration

| Parameter | Value |
|---|---|
| epochs | 3 |
| per_device_train_batch_size | 1 |
| gradient_accumulation_steps | 16 |
| effective_batch_size | 16 |
| max_seq_length | 8192 |
| lr_scheduler | cosine |
| warmup_ratio | 0.05 |
| weight_decay | 0.01 |
| precision | bf16 |
| LoRA target modules | q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj |

---

## Data Split

A total of 2,378 cases were split using T-stage stratified sampling:

| Set | Count | Ratio |
|---|---|---|
| train | 1,661 | 70% |
| val | 237 | 10% |
| test | 476 | 20% |

### Data Preparation

```bash
python prepare_finetune_data.py \
    --gold gold_standard_2378.csv \
    --reports pathology_reports.xlsx \
    --output_dir data/
```

---

## Training

### Qwen2.5-7B

```bash
# ExpA (r=16, without KSP)
CUDA_VISIBLE_DEVICES=0 python train.py \
    --model_path /data/kude/models/Qwen2.5-7B-Instruct \
    --exp A \
    --train_data data/train.jsonl \
    --val_data data/val.jsonl \
    --output_dir models/qwen_a

# ExpB (r=64, without KSP)
CUDA_VISIBLE_DEVICES=1 python train.py \
    --model_path /data/kude/models/Qwen2.5-7B-Instruct \
    --exp B \
    --train_data data/train.jsonl \
    --val_data data/val.jsonl \
    --output_dir models/qwen_b

# ExpA+KSP
CUDA_VISIBLE_DEVICES=2 python train.py \
    --model_path /data/kude/models/Qwen2.5-7B-Instruct \
    --exp A \
    --train_data data/train.jsonl \
    --val_data data/val.jsonl \
    --output_dir models/qwen_a_ksp \
    --use_ksp

# ExpB+KSP
CUDA_VISIBLE_DEVICES=3 python train.py \
    --model_path /data/kude/models/Qwen2.5-7B-Instruct \
    --exp B \
    --train_data data/train.jsonl \
    --val_data data/val.jsonl \
    --output_dir models/qwen_b_ksp \
    --use_ksp
```

### Gemma3-12B (without KSP only)

```bash
CUDA_VISIBLE_DEVICES=0 python train.py \
    --model_path /data/kude/models/gemma-3-12b-it \
    --exp A \
    --train_data data/train.jsonl \
    --val_data data/val.jsonl \
    --output_dir models/gemma_a

CUDA_VISIBLE_DEVICES=1 python train.py \
    --model_path /data/kude/models/gemma-3-12b-it \
    --exp B \
    --train_data data/train.jsonl \
    --val_data data/val.jsonl \
    --output_dir models/gemma_b
```

### Llama3.1-8B

```bash
CUDA_VISIBLE_DEVICES=0 python train.py \
    --model_path /data/kude/models/Llama-3.1-8B-Instruct \
    --exp A \
    --train_data data/train.jsonl \
    --val_data data/val.jsonl \
    --output_dir models/llama_a

CUDA_VISIBLE_DEVICES=1 python train.py \
    --model_path /data/kude/models/Llama-3.1-8B-Instruct \
    --exp B \
    --train_data data/train.jsonl \
    --val_data data/val.jsonl \
    --output_dir models/llama_b

CUDA_VISIBLE_DEVICES=2 python train.py \
    --model_path /data/kude/models/Llama-3.1-8B-Instruct \
    --exp A \
    --train_data data/train.jsonl \
    --val_data data/val.jsonl \
    --output_dir models/llama_a_ksp \
    --use_ksp

CUDA_VISIBLE_DEVICES=3 python train.py \
    --model_path /data/kude/models/Llama-3.1-8B-Instruct \
    --exp B \
    --train_data data/train.jsonl \
    --val_data data/val.jsonl \
    --output_dir models/llama_b_ksp \
    --use_ksp
```

> **Note:** Multi-GPU NCCL errors occurred during Llama3.1-8B training; each run was executed on a single GPU using `CUDA_VISIBLE_DEVICES`.

---

## Adapter Merging

After training, merge the LoRA adapter into the base model to produce a format loadable by vLLM:

```bash
python merge_adapter.py \
    --base_model /data/kude/models/Qwen2.5-7B-Instruct \
    --adapter_path models/qwen_a \
    --output_path merge/qwen_a

python merge_adapter.py \
    --base_model /data/kude/models/Qwen2.5-7B-Instruct \
    --adapter_path models/qwen_b \
    --output_path merge/qwen_b
```

---

## Inference

### Qwen (vLLM)

```bash
python test.py \
    --model_path merge/qwen_a \
    --test_data data/test.jsonl \
    --output_dir results

python test.py \
    --model_path merge/qwen_b_ksp \
    --test_data data/test.jsonl \
    --output_dir results \
    --use_ksp
```

### Gemma3 (transformers)

> Gemma3 uses a multimodal architecture that causes vLLM compatibility issues after merging; inference is therefore performed using the transformers library.

```bash
python test_gemma.py \
    --model_path merge/gemma_a \
    --test_data data/test.jsonl \
    --output_dir results
```

### Llama (vLLM)

```bash
python test_llama.py \
    --model_path merge/llama_a \
    --test_data data/test.jsonl \
    --output_dir results
```
