"""
extract_main.py
Common extraction main script
"""

import argparse
import sys
import time
import json
from pathlib import Path
from tqdm import tqdm
import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"

import pandas as pd
from utils import load_reports, get_report_texts, parse_response, build_output_df, save_results, EXTRACTION_FIELDS

# ── Model configurations ───────────────────────────────────────────────────────
MODEL_CONFIGS = {
    "qwen": {
        "model_path": "/data/kude/models/Qwen2.5-7B-Instruct",
        "dtype": "float16",
        "max_model_len": 8192,
        "gpu_memory_utilization": 0.85,
    },
    "qwen14b": {
        "model_path": "/data/kude/models/Qwen2.5-14B-Instruct",
        "dtype": "float16",
        "max_model_len": 8192,
        "gpu_memory_utilization": 0.85,
    },
    "gemma3": {
        "model_path": "/data/kude/models/gemma-3-12b-it",
        "dtype": "bfloat16",
        "max_model_len": 8192,
        "gpu_memory_utilization": 0.85,
    },
    "llama": {
        "model_path": "/data/kude/models/Llama-3.1-8B-Instruct",
        "dtype": "float16",
        "max_model_len": 8192,
        "gpu_memory_utilization": 0.85,
    },
    "med42": {
        "model_path": "/data/kude/models/Llama3-Med42-8B",
        "dtype": "float16",
        "max_model_len": 8192,
        "gpu_memory_utilization": 0.85,
    },
    "medgemma": {
        "model_path": "/data/kude/models/medgemma-4b-it",
        "dtype": "bfloat16",
        "max_model_len": 8192,
        "gpu_memory_utilization": 0.85,
    },
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model",           required=True, choices=list(MODEL_CONFIGS.keys()))
    parser.add_argument("--prompt_type",     required=True)
    parser.add_argument("--input",           required=True)
    parser.add_argument("--output",          required=True)
    parser.add_argument("--config",          default="baseline", choices=["baseline", "ksp"])
    parser.add_argument("--tensor_parallel", type=int, default=4)
    parser.add_argument("--batch_size",      type=int, default=8)
    parser.add_argument("--max_tokens",      type=int, default=512)
    return parser.parse_args()


def main():
    args = parse_args()

    # Load config
    if args.config == "baseline":
        from config_baseline import get_messages, PROMPT_TYPES
    else:
        from config_ksp import get_messages, PROMPT_TYPES

    if args.prompt_type not in PROMPT_TYPES:
        print(f"Error: prompt_type '{args.prompt_type}' not in {PROMPT_TYPES}")
        sys.exit(1)

    cfg = MODEL_CONFIGS[args.model]
    print(f"\n{'='*60}")
    print(f"Model:  {args.model} ({cfg['model_path']})")
    print(f"Strategy: {args.prompt_type}")
    print(f"Config: {args.config}")
    print(f"Output: {args.output}")
    print(f"{'='*60}\n")

    # Load model
    import torch
    from vllm import LLM, SamplingParams
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(cfg["model_path"], trust_remote_code=True)

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    model_load_start = time.time()
    llm = LLM(
        model=cfg["model_path"],
        dtype=cfg["dtype"],
        max_model_len=cfg["max_model_len"],
        gpu_memory_utilization=cfg["gpu_memory_utilization"],
        tensor_parallel_size=args.tensor_parallel,
        trust_remote_code=True,
    )
    model_load_time = time.time() - model_load_start
    print(f"  Model load time: {model_load_time:.1f}s")

    sampling_params = SamplingParams(
        temperature=0.0,
        max_tokens=args.max_tokens,
    )

    # Load data
    print(f"[1/3] Loading data: {args.input}")
    df = load_reports(args.input)
    reports = get_report_texts(df)
    print(f"  Total {len(reports)} reports")

    # Build prompts
    print(f"[2/3] Starting inference...")
    prompts = []
    for report in reports:
        messages = get_messages(args.prompt_type, report)
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        prompts.append(prompt)

    # Inference
    results = []
    parse_success = 0
    parse_fail = 0

    inference_start = time.time()

    for i in tqdm(range(0, len(prompts), args.batch_size), desc=f"{args.model}/{args.prompt_type}"):
        batch = prompts[i:i + args.batch_size]
        outputs = llm.generate(batch, sampling_params)
        for out in outputs:
            text = out.outputs[0].text
            parsed = parse_response(text, args.prompt_type)
            if parsed:
                parse_success += 1
            else:
                parse_fail += 1
            results.append({field: parsed.get(field) for field in EXTRACTION_FIELDS})

    inference_time = time.time() - inference_start
    total_time = model_load_time + inference_time

    gpu_peak_mem = 0
    if torch.cuda.is_available():
        gpu_peak_mem = torch.cuda.max_memory_allocated() / 1024**3

    n = len(reports)
    parse_rate = parse_success / n * 100

    print(f"\n{'='*60}")
    print(f"[Computational Efficiency Metrics]")
    print(f"  Model load time:  {model_load_time:.1f}s")
    print(f"  Inference time:   {inference_time:.1f}s")
    print(f"  Total time:       {total_time:.1f}s")
    print(f"  Throughput:       {n/inference_time:.2f} reports/sec")
    print(f"  GPU Peak Memory:  {gpu_peak_mem:.1f} GB")
    print(f"[JSON Parsing Success Rate]")
    print(f"  Success: {parse_success} / Fail: {parse_fail}")
    print(f"  Parse success rate: {parse_rate:.2f}%")
    print(f"{'='*60}\n")

    # Save results
    print(f"[3/3] Saving results...")
    out_df = build_output_df(df, results)
    save_results(out_df, args.output, f"{args.model}_{args.prompt_type}")

    # Save computational efficiency metrics
    metrics_path = str(args.output).replace('.csv', '_metrics.json').replace('.xlsx', '_metrics.json')
    metrics = {
        "model":              args.model,
        "prompt_type":        args.prompt_type,
        "config":             args.config,
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
    print(f"  Computational efficiency metrics saved: {metrics_path}")


if __name__ == "__main__":
    main()
