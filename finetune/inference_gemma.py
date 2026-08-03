"""
Gemma3 Fine-tuned Model Test Inference Script (transformers-based)
"""

import argparse
import json
import os
import re
import time
import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM
from tqdm import tqdm

os.environ["TOKENIZERS_PARALLELISM"] = "false"

FIELDS = [
    "TumorLocation", "TumorCircumference", "TumorSize",
    "Histologic_type", "Lauren_type", "Differentiation",
    "ProximalMargin", "DistalMargin",
    "LymphovascularInvasion", "PerineuralInvasion",
    "T_stage", "N_stage", "M_stage", "Staging",
    "MetastaticLymphNode", "HarvestedLymphNode",
]

KSP_GUIDELINE = """
[Korean Society of Pathologists - Standardized Pathology Report for Gastric Cancer, 2nd Edition (2023)]

TUMOR LOCATION: Values: GEJ/Upper third, Middle third, Lower third
TUMOR CIRCUMFERENCE: Values: Anterior wall, Posterior wall, Lesser curvature, Greater curvature
HISTOLOGIC TYPE: Well differentiated (W/D) adenocarcinoma, Moderately differentiated (M/D) adenocarcinoma,
  Poorly differentiated (P/D) adenocarcinoma, Poorly cohesive carcinoma / Signet ring cell carcinoma,
  Mixed type (tubular adenocarcinoma and/or PCC), Mucinous carcinoma, Papillary carcinoma,
  Gastric carcinoma with lymphoid stroma, Neuroendocrine tumor, Other
LAUREN: Intestinal / Diffuse / Indeterminate / Mixed / Unknown
DIFFERENTIATION: Well differentiated / Moderately differentiated / Poorly differentiated / Signet ring/Poorly cohesive
LVI / PNI: Yes / No
T stage: T1a, T1b, T2, T3, T4a, T4b
N stage: N0, N1, N2, N3a, N3b
M stage: M0, M1 (Mx = M0)
STAGING: IA, IB, IIA, IIB, IIIA, IIIB, IIIC, IV
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


def parse_output(text: str) -> dict:
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path",     required=True)
    parser.add_argument("--test_data",      default="data/test.jsonl")
    parser.add_argument("--output_dir",     default="results")
    parser.add_argument("--use_ksp",        action="store_true")
    parser.add_argument("--batch_size",     type=int, default=4)
    parser.add_argument("--max_new_tokens", type=int, default=512)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    SYSTEM_PROMPT = KSP_SYSTEM_PROMPT if args.use_ksp else BASE_SYSTEM_PROMPT

    print(f"[1/4] Loading test data: {args.test_data}")
    with open(args.test_data, 'r', encoding='utf-8') as f:
        records = [json.loads(line) for line in f]
    print(f"  Total {len(records)} records")

    print(f"\n[2/4] Loading model: {args.model_path}")
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    model_load_start = time.time()
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()
    model_load_time = time.time() - model_load_start
    print(f"  Model load time: {model_load_time:.1f}s")

    print(f"\n[3/4] Starting inference...")
    predictions = []
    parse_success = 0
    parse_fail = 0

    inference_start = time.time()
    for i in tqdm(range(0, len(records), args.batch_size), desc="Inference"):
        batch = records[i:i + args.batch_size]
        batch_texts = []
        for rec in batch:
            user_msg = "Pathology report:\n" + rec['report'] + "\n\nExtract the fields as JSON:"
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ]
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            if isinstance(text, list):
                text = text[0]
            batch_texts.append(str(text))

        inputs = tokenizer(
            batch_texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=8192,
        ).to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
            )

        input_len = inputs["input_ids"].shape[1]
        for output in outputs:
            text = tokenizer.decode(output[input_len:], skip_special_tokens=True).strip()
            pred = parse_output(text)
            if pred:
                parse_success += 1
            else:
                parse_fail += 1
            predictions.append(pred)

    inference_time = time.time() - inference_start
    total_time = model_load_time + inference_time

    gpu_peak_mem = 0
    if torch.cuda.is_available():
        gpu_peak_mem = torch.cuda.max_memory_allocated() / 1024**3

    n = len(records)
    parse_rate = parse_success / n * 100

    print(f"\n{'='*60}")
    print(f"  Model load time:    {model_load_time:.1f}s")
    print(f"  Inference time:     {inference_time:.1f}s")
    print(f"  Throughput:         {n/inference_time:.2f} reports/sec")
    print(f"  GPU Peak Memory:    {gpu_peak_mem:.1f} GB")
    print(f"  Parse success rate: {parse_rate:.2f}% ({parse_success}/{n})")
    print(f"{'='*60}\n")

    print(f"[4/4] Saving results...")
    rows = []
    for rec, pred in zip(records, predictions):
        row = {
            "Sex_reg":       rec.get("Sex_reg", ""),
            "OP_Age":        rec.get("OP_Age", ""),
            "OperationDate": rec.get("OperationDate", ""),
            "CHKID":         rec.get("CHKID", ""),
            "ID":            rec.get("ID", ""),
        }
        for field in FIELDS:
            row[f"g_{field}"] = rec["answer"].get(field) if rec.get("answer") else None
        for field in FIELDS:
            row[f"p_{field}"] = pred.get(field)
        rows.append(row)

    df = pd.DataFrame(rows)
    model_name = os.path.basename(args.model_path.rstrip("/"))
    ksp_suffix = "_ksp" if args.use_ksp else ""
    output_file = os.path.join(args.output_dir, f"test_results_{model_name}{ksp_suffix}.csv")
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"  Saved: {output_file}")

    metrics_path = output_file.replace('.csv', '_metrics.json')
    metrics = {
        "model_path":         args.model_path,
        "use_ksp":            args.use_ksp,
        "n_reports":          n,
        "model_load_time_s":  round(model_load_time, 2),
        "inference_time_s":   round(inference_time, 2),
        "total_time_s":       round(total_time, 2),
        "reports_per_sec":    round(n / inference_time, 4),
        "sec_per_report":     round(inference_time / n, 4),
        "gpu_peak_memory_gb": round(gpu_peak_mem, 2),
        "parse_success":      parse_success,
        "parse_fail":         parse_fail,
        "parse_success_rate": round(parse_rate, 4),
    }
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"  Metrics saved: {metrics_path}")


if __name__ == "__main__":
    main()
