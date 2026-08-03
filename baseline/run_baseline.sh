#!/bin/bash
# run_experiments.sh
# Full experiment execution script
# - Sequential execution per model, tensor_parallel=4 (uses 4 GPUs)
#
# Usage:
#   bash run_experiments.sh baseline     # baseline_scratch experiments
#   bash run_experiments.sh ksp          # baseline_ksp experiments
#   bash run_experiments.sh all          # all experiments

EXPERIMENT=${1:-"baseline"}
INPUT="/data/kude/llms_project/experiment/pathology_reports.xlsx"
RESULTS_DIR="output_np"
#MODELS=("qwen" "gemma3" "llama" "med42" "medgemma" "qwen14b")
MODELS=("med42" "medgemma")

mkdir -p ${RESULTS_DIR}

run_model() {
    local MODEL=$1
    local PROMPT=$2
    local CONFIG=$3
    OUTPUT="${RESULTS_DIR}/${MODEL}_${PROMPT}.csv"
    echo "[$(date '+%H:%M:%S')] ${MODEL} / ${PROMPT} starting..."
    python extract_main.py \
        --model ${MODEL} \
        --prompt_type ${PROMPT} \
        --input ${INPUT} \
        --output ${OUTPUT} \
        --config ${CONFIG} \
        --tensor_parallel 4 \
        --batch_size 8
    echo "[$(date '+%H:%M:%S')] ${MODEL} / ${PROMPT} done"
}

run_baseline() {
    echo "========================================"
    echo "Baseline Scratch experiments starting"
    echo "========================================"
    for MODEL in "${MODELS[@]}"; do
        echo "--- ${MODEL} ---"
        run_model ${MODEL} zero_shot baseline
        run_model ${MODEL} few_shot  baseline
        run_model ${MODEL} cot       baseline
    done
}

run_ksp() {
    echo "========================================"
    echo "Baseline KSP experiments starting"
    echo "========================================"
    for MODEL in "${MODELS[@]}"; do
        echo "--- ${MODEL} ---"
        run_model ${MODEL} zero_shot_ksp ksp
        run_model ${MODEL} few_shot_ksp  ksp
        run_model ${MODEL} cot_ksp       ksp
    done
}

case ${EXPERIMENT} in
    baseline)
        run_baseline
        ;;
    ksp)
        run_ksp
        ;;
    all)
        run_baseline
        run_ksp
        ;;
    *)
        echo "Usage: bash run_experiments.sh [baseline|ksp|all]"
        exit 1
        ;;
esac

echo "========================================"
echo "All done!"
echo "========================================"
