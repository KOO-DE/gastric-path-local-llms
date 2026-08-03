# Baseline LLM Extraction

Experimental code for extracting 16 clinical fields from gastric cancer pathology reports using baseline LLMs.

---

## File Structure

```
baseline/
├── config_baseline.py      # Baseline prompts (without KSP): Zero-shot / Few-shot / CoT
├── config_ksp.py           # Prompts with KSP guidelines: Zero-shot / Few-shot / CoT
├── extract_main.py         # Main extraction script (vLLM-based)
├── run_baseline.sh         # Full experiment automation script
└── utils.py                # Data loading, preprocessing, and JSON parsing utilities
```

---

## Supported Models

| Model Key | Model Name | Parameters |
|---|---|---|
| `qwen` | Qwen2.5-7B-Instruct | 7B |
| `qwen14b` | Qwen2.5-14B-Instruct | 14B |
| `gemma3` | Gemma3-12B-IT | 12B |
| `llama` | Llama-3.1-8B-Instruct | 8B |
| `med42` | Llama3-Med42-8B | 8B |
| `medgemma` | MedGemma-4B-IT | 4B |

---

## Target Extraction Fields (16)

| Field | Type | Description |
|---|---|---|
| TumorLocation | array | Tumor location (GEJ/Upper third, Middle third, Lower third) |
| TumorCircumference | array | Circumferential wall involvement |
| TumorSize | number | Maximum tumor size (cm) |
| Histologic_type | array | WHO histologic type |
| Lauren_type | array | Lauren classification |
| Differentiation | array | Degree of differentiation |
| ProximalMargin | number | Proximal resection margin distance (cm) |
| DistalMargin | number | Distal resection margin distance (cm) |
| LymphovascularInvasion | string | Lymphovascular invasion (Yes/No) |
| PerineuralInvasion | string | Perineural invasion (Yes/No) |
| T_stage | string | T stage |
| N_stage | string | N stage |
| M_stage | string | M stage |
| Staging | string | AJCC 8th edition overall stage |
| MetastaticLymphNode | integer | Number of metastatic lymph nodes |
| HarvestedLymphNode | integer | Number of harvested lymph nodes |

---

## Environment Setup

```bash
pip install vllm transformers pandas scikit-learn tqdm openpyxl
```

- Python 3.11
- CUDA 12.2
- A6000 GPU × 4

---

## Usage

### 1. Single model / strategy

```bash
python extract_main.py \
    --model qwen \
    --prompt_type zero_shot \
    --input pathology_reports.xlsx \
    --output results/qwen_zero_shot.csv \
    --config baseline
```

### 2. With KSP guidelines

```bash
python extract_main.py \
    --model qwen \
    --prompt_type zero_shot_ksp \
    --input pathology_reports.xlsx \
    --output results/qwen_zero_shot_ksp.csv \
    --config ksp
```

### 3. Batch run across all models / strategies

```bash
for pred in results/*.csv; do
    model=$(basename $pred .csv)
    python extract_main.py \
        --model $model \
        --prompt_type zero_shot \
        --input pathology_reports.xlsx \
        --output results/${model}_zero_shot.csv \
        --config baseline
done
```

---

## Arguments

| Argument | Description | Default |
|---|---|---|
| `--model` | Model key (qwen, qwen14b, gemma3, llama, med42, medgemma) | Required |
| `--prompt_type` | Prompt strategy (zero_shot, few_shot, cot / zero_shot_ksp, few_shot_ksp, cot_ksp) | Required |
| `--input` | Input pathology report file (.xlsx) | Required |
| `--output` | Output result file (.csv) | Required |
| `--config` | Prompt configuration (baseline / ksp) | baseline |
| `--tensor_parallel` | Tensor parallel size | 4 |
| `--batch_size` | Batch size | 8 |
| `--max_tokens` | Maximum output tokens | 512 |

---

## Output Files

### Extraction Result CSV
- Original data columns + 16 extracted fields
- Location: `results/{model}_{prompt_type}.csv`

### Computational Efficiency Metrics JSON
- Model load time, inference time, throughput, GPU peak memory, JSON parsing success rate
- Location: `results/{model}_{prompt_type}_metrics.json`
