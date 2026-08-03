"""
Merge LoRA adapter into base model and save
Saves in a format directly loadable by vLLM
"""
import argparse
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

parser = argparse.ArgumentParser()
parser.add_argument("--base_model",   required=True, help="Base model path (e.g. /data/kude/models/Qwen2.5-7B-Instruct)")
parser.add_argument("--adapter_path", required=True, help="LoRA adapter path (e.g. outputs/qwen_cpt_expA)")
parser.add_argument("--output_path",  required=True, help="Merged model save path (e.g. /data/kude/models/Qwen2.5-7B-CPT-expA)")
args = parser.parse_args()

print(f"Base model: {args.base_model}")
print(f"Adapter: {args.adapter_path}")
print(f"Output: {args.output_path}")

# 1. Load base model
print("\n[1/4] Loading base model...")
model = AutoModelForCausalLM.from_pretrained(
    args.base_model,
    torch_dtype=torch.float16,
    trust_remote_code=True,
    device_map="cpu",  # merging can be done on CPU
)

# 2. Load LoRA adapter
print("[2/4] Loading LoRA adapter...")
model = PeftModel.from_pretrained(model, args.adapter_path)

# 3. Merge adapter
print("[3/4] Merging adapter...")
model = model.merge_and_unload()

# 4. Save
print(f"[4/4] Saving to: {args.output_path}")
model.save_pretrained(args.output_path)
tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
tokenizer.save_pretrained(args.output_path)

print("\nDone!")
print(f"vLLM model path: {args.output_path}")
