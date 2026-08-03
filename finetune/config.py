"""
LoRA Fine-tuning configuration file
Experiment A: r=16 (conservative)
Experiment B: r=64 (aggressive)
"""
BASE_CONFIG = {
    # Data
    "train_data": "data/train.jsonl",
    "val_data":   "data/val.jsonl",
    # Training
    "num_train_epochs": 3,
    "per_device_train_batch_size": 1,
    "per_device_eval_batch_size": 1,
    "gradient_accumulation_steps": 16,
    "learning_rate": 2e-4,
    "lr_scheduler_type": "cosine",
    "warmup_ratio": 0.05,
    "weight_decay": 0.01,
    "max_seq_length": 8192,
    "fp16": True,
    # LoRA common
    "lora_target_modules": [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ],
    "lora_dropout": 0.05,
    "lora_bias": "none",
    # Saving / logging
    "save_steps": 50,
    "eval_steps": 50,
    "logging_steps": 10,
    "save_total_limit": 2,
    "load_best_model_at_end": True,
    "metric_for_best_model": "eval_loss",
    "report_to": "none",
}
EXP_A = {
    **BASE_CONFIG,
    "exp_name":      "ft_r16",
    "lora_r":        16,
    "lora_alpha":    32,
    "learning_rate": 2e-4,
    "output_dir":    "outputs/ft_r16",
}
EXP_B = {
    **BASE_CONFIG,
    "exp_name":      "ft_r64",
    "lora_r":        64,
    "lora_alpha":    128,
    "learning_rate": 1e-4,
    "output_dir":    "outputs/ft_r64",
}
EXPERIMENTS = {"A": EXP_A, "B": EXP_B}
