"""
evaluation.py
Structured Information Extraction Evaluation Script for Gastrectomy Pathology Reports

Supports two input formats:
  1. "gp" format: A single CSV containing both gold (g_Field) and prediction (p_Field) columns
     (e.g., rule-based prediction file, fine-tuning test_results_*.csv)
  2. "baseline" format: A CSV containing only prediction values (Field columns),
     with gold standard retrieved from a separate test.jsonl by CHKID
     (e.g., baseline LLM zero-shot / few-shot / CoT prediction files)

Usage:
  # gp format (rule-based, fine-tuning)
  python evaluation_final.py --mode gp --pred rule_based_pred.csv --output eval_out.csv \\
      [--test-ids test.jsonl]   # specify to restrict evaluation to 476 test records; omit to use all rows

  # baseline format (zero-shot / few-shot / CoT baseline)
  python evaluation_final.py --mode baseline --pred qwen_few_shot.csv --output eval_out.csv \\
      --test-jsonl test.jsonl --margin-gold gold_standard_test476.csv
"""

import argparse
import json
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, f1_score, roc_auc_score,
    mean_absolute_error, mean_squared_error, cohen_kappa_score,
)

warnings.filterwarnings("ignore")

# ══════════════════════════════════════════════════════════════════════════
# Field type definitions
# ══════════════════════════════════════════════════════════════════════════
ARRAY_FIELDS       = {"TumorLocation", "TumorCircumference", "Histologic_type", "Differentiation"}
CATEGORICAL_FIELDS = {"T_stage", "N_stage", "M_stage", "Staging"}
LAUREN_FIELDS      = {"Lauren_type"}
BINARY_FIELDS      = {"LymphovascularInvasion", "PerineuralInvasion"}
NUMERIC_FIELDS     = {"TumorSize", "ProximalMargin", "DistalMargin",
                      "MetastaticLymphNode", "HarvestedLymphNode"}

ALL_FIELDS = [
    "TumorLocation", "TumorCircumference", "TumorSize",
    "Histologic_type", "Lauren_type", "Differentiation",
    "ProximalMargin", "DistalMargin",
    "LymphovascularInvasion", "PerineuralInvasion",
    "T_stage", "N_stage", "M_stage", "Staging",
    "MetastaticLymphNode", "HarvestedLymphNode",
]

TOLERANCE = {
    "TumorSize": 0.5, "ProximalMargin": 0.5, "DistalMargin": 0.5,
    "MetastaticLymphNode": 1.0, "HarvestedLymphNode": 2.0,
}

NULL_VALUES = {"", "null", "none", "unknown", "nan", "na", "n/a"}

# ══════════════════════════════════════════════════════════════════════════
# Normalization mappings
# ══════════════════════════════════════════════════════════════════════════
HISTOLOGY_MAP = {
    "tubular adenocarcinoma, well differentiated":       "Well differentiated (W/D) adenocarcinoma",
    "tubular adenocarcinoma, moderately differentiated":  "Moderately differentiated (M/D) adenocarcinoma",
    "tubular adenocarcinoma, poorly differentiated":      "Poorly differentiated (P/D) adenocarcinoma",
    "poorly cohesive carcinoma, signet ring cell type":   "Poorly cohesive carcinoma / Signet ring cell carcinoma",
    "poorly cohesive carcinoma, nos":                     "Poorly cohesive carcinoma / Signet ring cell carcinoma",
    "poorly cohesive carcinoma":                          "Poorly cohesive carcinoma / Signet ring cell carcinoma",
    "signet ring cell carcinoma":                         "Poorly cohesive carcinoma / Signet ring cell carcinoma",
    "mixed adenocarcinoma":                               "Mixed type (tubular adenocarcinoma and/or PCC)",
    "mucinous adenocarcinoma":                            "Mucinous carcinoma",
    "papillary adenocarcinoma":                           "Papillary carcinoma",
    "adenocarcinoma with lymphoid stroma":                "Gastric carcinoma with lymphoid stroma",
}
DIFFERENTIATION_MAP = {
    "well differentiated (w/d)":       "Well differentiated",
    "well differentiated":             "Well differentiated",
    "moderately differentiated (m/d)": "Moderately differentiated",
    "moderately differentiated":       "Moderately differentiated",
    "poorly differentiated (p/d)":     "Poorly differentiated",
    "poorly differentiated":           "Poorly differentiated",
    "signet ring/poorly cohesive":     "Signet ring/Poorly cohesive",
    "signet ring cell":                "Signet ring/Poorly cohesive",
    "poorly cohesive":                 "Signet ring/Poorly cohesive",
}
TUMOR_LOCATION_MAP = {
    "gej/upper third": "GEJ/Upper third", "upper third": "GEJ/Upper third",
    "middle third": "Middle third", "lower third": "Lower third",
    "cardia": "GEJ/Upper third", "fundus": "GEJ/Upper third",
    "body": "Middle third", "angle": "Middle third",
    "antrum": "Lower third", "pylorus": "Lower third",
}
TUMOR_CIRCUMFERENCE_MAP = {
    "anterior wall": "Anterior wall", "posterior wall": "Posterior wall",
    "lesser curvature": "Lesser curvature", "greater curvature": "Greater curvature",
}

# ══════════════════════════════════════════════════════════════════════════
# Utility functions (fully deterministic: uses only lists/dicts, no set iteration order dependency)
# ══════════════════════════════════════════════════════════════════════════
def is_null(val):
    if val is None: return True
    if isinstance(val, float) and np.isnan(val): return True
    return str(val).strip().lower() in NULL_VALUES

def normalize_mx(val):
    if is_null(val): return None
    v = str(val).strip().upper()
    return "M0" if v in {"MX", "PMX"} else str(val).strip()

def normalize_tnm(val):
    if is_null(val): return None
    v = str(val).strip()
    return v[1:] if v.startswith(("p", "P")) else v

def normalize_staging(val):
    if is_null(val): return None
    return re.sub(r"[Mm][Xx]", "M0", str(val).strip())

def _parse_list(s):
    """Parse string into a list (preserving original order). Returns None on failure."""
    if s.startswith("["):
        try:
            items = json.loads(s)
            return [str(i).strip() for i in items if str(i).strip()]
        except Exception:
            try:
                import ast
                items = ast.literal_eval(s)
                return [str(i).strip() for i in items if str(i).strip()]
            except Exception:
                return None
    if "|" in s:
        return [v.strip() for v in s.split("|") if v.strip()]
    if ";" in s:
        return [v.strip() for v in s.split(";") if v.strip()]
    return None

def deserialize_array(val):
    """For set-based comparison (F1 computation). Order does not affect F1 (only intersection/union sizes are used)."""
    if val is None: return None
    if isinstance(val, set): return val if val else None
    if isinstance(val, list): return set(str(i).strip() for i in val if str(i).strip()) or None
    s = str(val).strip()
    if is_null(s): return None
    items = _parse_list(s)
    if items is not None:
        return set(items) or None
    return {s} if s else None

def normalize_pred_array(val, field):
    if is_null(val): return None
    items = deserialize_array(val)
    if items is None: return None
    normalized = set()
    for item in items:
        item_lower = item.strip().lower()
        if field == "Histologic_type":
            mapped = HISTOLOGY_MAP.get(item_lower, item.strip())
        elif field == "Differentiation":
            mapped = DIFFERENTIATION_MAP.get(item_lower, item.strip())
        elif field == "TumorLocation":
            mapped = TUMOR_LOCATION_MAP.get(item_lower, item.strip())
        elif field == "TumorCircumference":
            mapped = TUMOR_CIRCUMFERENCE_MAP.get(item_lower, item.strip())
        else:
            mapped = item.strip()
        normalized.add(mapped)
    return normalized

def extract_first(val):
    """Deterministically extract the 'true first' value from an array or scalar (for Lauren_type).
    Preserves original list order without going through a set, so the result is stable across runs."""
    if is_null(val):
        return None
    s = str(val).strip()
    items = _parse_list(s)
    if items is not None:
        return items[0] if items else None
    return normalize_str(val)

def normalize_binary(val):
    if is_null(val): return None
    v = str(val).strip().lower()
    if v in {"yes", "present", "1", "true", "positive"}: return 1
    if v in {"no", "absent", "0", "false", "negative"}: return 0
    return None

def normalize_str(val):
    if is_null(val): return None
    return str(val).strip()

def normalize_numeric(val):
    if is_null(val): return None
    try: return float(val)
    except Exception: return None

def apply_stage_normalization(field, values):
    """Normalization pipeline for T_stage/N_stage/M_stage/Staging (takes a list as input)."""
    result = list(values)
    if field == "M_stage":
        result = [normalize_mx(v) for v in result]
    if field == "Staging":
        result = [normalize_staging(v) for v in result]
    if field in {"T_stage", "N_stage", "M_stage"}:
        result = [normalize_tnm(v) for v in result]
    return result

# ══════════════════════════════════════════════════════════════════════════
# Field-level metric functions (all take pure list inputs)
# ══════════════════════════════════════════════════════════════════════════
def evaluate_array_field(gold_list, pred_list, field):
    tp = fp = fn = exact = total = 0
    n_gold_valid = 0
    miss_count = 0
    for g, p in zip(gold_list, pred_list):
        g_set = deserialize_array(g)
        p_set = normalize_pred_array(p, field)
        if g_set is not None:
            n_gold_valid += 1
            if p_set is None:
                miss_count += 1
        if g_set is None and p_set is None:
            exact += 1; total += 1; continue
        if g_set is None or p_set is None:
            g_set = g_set or set(); p_set = p_set or set()
            total += 1; fn += len(g_set); fp += len(p_set); continue
        total += 1
        inter = g_set & p_set
        tp += len(inter); fp += len(p_set - g_set); fn += len(g_set - p_set)
        if g_set == p_set: exact += 1
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = 2*precision*recall/(precision+recall) if (precision+recall) > 0 else 0.0
    return {
        "N": total, "ExactAcc": round(exact/total, 4) if total > 0 else 0,
        "Precision": round(precision, 4), "Recall": round(recall, 4), "F1": round(f1, 4),
        "HallucinationRate": round(fp/(tp+fp), 4) if (tp+fp) > 0 else 0.0,
        "MissRate_N": round(miss_count/total, 4) if total > 0 else None,
        "MissRate_validGold": round(miss_count/n_gold_valid, 4) if n_gold_valid > 0 else None,
    }

def evaluate_categorical_field(gold_list, pred_list):
    """gold/pred are already normalized lists (None or string)."""
    pairs     = list(zip(gold_list, pred_list))
    total     = len(pairs)
    both_null = sum(1 for g, p in pairs if g is None and p is None)
    n_gold_valid = sum(1 for g, p in pairs if g is not None)
    miss_count = sum(1 for g, p in pairs if g is not None and p is None)  # gold present / pred absent = miss
    valid     = [(g, p) for g, p in pairs if g is not None and p is not None]
    n_valid   = len(valid)
    if n_valid == 0:
        return {"N": total, "N_valid": 0, "BothNull": both_null,
                "Accuracy": None, "MacroF1": None, "Kappa": None,
                "MissRate_N": None, "MissRate_validGold": None, "HallucinationRate": None}
    y_true = [g for g, p in valid]; y_pred = [p for g, p in valid]
    acc      = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    try: kappa = cohen_kappa_score(y_true, y_pred)
    except Exception: kappa = None
    hallucination = sum(1 for g, p in pairs if g is None and p is not None)
    return {
        "N": total, "N_valid": n_valid, "BothNull": both_null,
        "Accuracy": round(acc, 4), "MacroF1": round(macro_f1, 4),
        "Kappa": round(kappa, 4) if kappa is not None else None,
        "MissRate_N": round(miss_count/total, 4),
        "MissRate_validGold": round(miss_count/n_gold_valid, 4) if n_gold_valid > 0 else None,
        "HallucinationRate": round(hallucination/total, 4),
    }

def evaluate_binary_field(gold_list, pred_list):
    pairs     = [(normalize_binary(g), normalize_binary(p)) for g, p in zip(gold_list, pred_list)]
    total     = len(pairs)
    both_null = sum(1 for g, p in pairs if g is None and p is None)
    n_gold_valid = sum(1 for g, p in pairs if g is not None)
    miss_count = sum(1 for g, p in pairs if g is not None and p is None)
    valid     = [(g, p) for g, p in pairs if g is not None and p is not None]
    n_valid   = len(valid)
    if n_valid == 0:
        return {"N": total, "N_valid": 0, "BothNull": both_null,
                "Accuracy": None, "F1": None, "AUROC": None,
                "MissRate_N": None, "MissRate_validGold": None, "HallucinationRate": None}
    y_true = [g for g, p in valid]; y_pred = [p for g, p in valid]
    acc = accuracy_score(y_true, y_pred)
    f1  = f1_score(y_true, y_pred, zero_division=0)
    try: auroc = roc_auc_score(y_true, y_pred)
    except Exception: auroc = None
    hallucination = sum(1 for g, p in pairs if g is None and p is not None)
    return {
        "N": total, "N_valid": n_valid, "BothNull": both_null,
        "Accuracy": round(acc, 4), "F1": round(f1, 4),
        "AUROC": round(auroc, 4) if auroc is not None else None,
        "MissRate_N": round(miss_count/total, 4),
        "MissRate_validGold": round(miss_count/n_gold_valid, 4) if n_gold_valid > 0 else None,
        "HallucinationRate": round(hallucination/total, 4),
    }

def evaluate_numeric_field(gold_list, pred_list, field):
    pairs     = [(normalize_numeric(g), normalize_numeric(p)) for g, p in zip(gold_list, pred_list)]
    total     = len(pairs)
    both_null = sum(1 for g, p in pairs if g is None and p is None)
    n_gold_valid = sum(1 for g, p in pairs if g is not None)
    miss_count = sum(1 for g, p in pairs if g is not None and p is None)
    valid     = [(g, p) for g, p in pairs if g is not None and p is not None]
    n_valid   = len(valid)
    if n_valid == 0:
        return {"N": total, "N_valid": 0, "BothNull": both_null,
                "MAE": None, "RMSE": None, "MissRate_N": None, "MissRate_validGold": None, "HallucinationRate": None}
    y_true = np.array([g for g, p in valid]); y_pred = np.array([p for g, p in valid])
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    hallucination = sum(1 for g, p in pairs if g is None and p is not None)
    tol_ranges = [0, 0.5, 1.0, 1.5, 2.0] if field in {"TumorSize", "ProximalMargin", "DistalMargin"} else [0, 1, 2, 3, 4, 5]
    tol_acc_dict = {f"TolAcc_{t}": round(float(np.mean(np.abs(y_true-y_pred) <= t)), 4) for t in tol_ranges}
    result = {
        "N": total, "N_valid": n_valid, "BothNull": both_null,
        "MAE": round(mae, 4), "RMSE": round(rmse, 4),
        "MissRate_N": round(miss_count/total, 4),
        "MissRate_validGold": round(miss_count/n_gold_valid, 4) if n_gold_valid > 0 else None,
        "HallucinationRate": round(hallucination/total, 4),
    }
    result.update(tol_acc_dict)
    return result

def is_field_correct(g, p, field):
    if field in ARRAY_FIELDS:
        return deserialize_array(g) == normalize_pred_array(p, field)
    elif field in LAUREN_FIELDS:
        return extract_first(g) == extract_first(p)
    elif field in CATEGORICAL_FIELDS:
        return normalize_str(g) == normalize_str(p)
    elif field in BINARY_FIELDS:
        return normalize_binary(g) == normalize_binary(p)
    elif field in NUMERIC_FIELDS:
        gn = normalize_numeric(g); pn = normalize_numeric(p)
        if gn is None and pn is None: return True
        if gn is None or pn is None: return False
        return abs(gn - pn) <= TOLERANCE.get(field, 0.5)
    return False

# ══════════════════════════════════════════════════════════════════════════
# Unified field evaluation with type branching
# ══════════════════════════════════════════════════════════════════════════
def evaluate_one_field(field, gold_list, pred_list):
    gold_list = list(gold_list); pred_list = list(pred_list)
    if field in {"T_stage", "N_stage", "M_stage", "Staging"}:
        gold_list = apply_stage_normalization(field, gold_list)
        pred_list = apply_stage_normalization(field, pred_list)

    if field in ARRAY_FIELDS:
        metrics = evaluate_array_field(gold_list, pred_list, field)
        field_type = "array"
        correct = [is_field_correct(g, p, field) for g, p in zip(gold_list, pred_list)]
    elif field in LAUREN_FIELDS:
        g_first = [extract_first(v) for v in gold_list]
        p_first = [extract_first(v) for v in pred_list]
        metrics = evaluate_categorical_field(g_first, p_first)
        field_type = "categorical"
        correct = [g == p for g, p in zip(g_first, p_first)]
    elif field in CATEGORICAL_FIELDS:
        g_norm = [normalize_str(v) for v in gold_list]
        p_norm = [normalize_str(v) for v in pred_list]
        metrics = evaluate_categorical_field(g_norm, p_norm)
        field_type = "categorical"
        correct = [g == p for g, p in zip(g_norm, p_norm)]
    elif field in BINARY_FIELDS:
        metrics = evaluate_binary_field(gold_list, pred_list)
        field_type = "binary"
        correct = [is_field_correct(g, p, field) for g, p in zip(gold_list, pred_list)]
    elif field in NUMERIC_FIELDS:
        metrics = evaluate_numeric_field(gold_list, pred_list, field)
        field_type = "numeric"
        correct = [is_field_correct(g, p, field) for g, p in zip(gold_list, pred_list)]
    else:
        raise ValueError(f"Unknown field: {field}")
    return field_type, metrics, correct

def overall_average(field_metrics):
    """field_metrics: {field: (field_type, metrics_dict)} -> overall average (%) using standard classification metrics.
    [Reference only] Based on per-field standard metrics (F1/MacroF1/TolAcc).
    Null-null / miss / hallucination cases follow the standard convention of using only valid pairs (both non-null).
    The final metric adopted in the paper is overall_average_4q() below; this function is still used
    for computing individual metrics in per-field detail tables (Tables 5, 7, 9, 10, 11, etc.)."""
    vals = []
    for field, (field_type, metrics) in field_metrics.items():
        if field_type == "array": vals.append(metrics["F1"])
        elif field_type == "categorical": vals.append(metrics["MacroF1"])
        elif field_type == "binary": vals.append(metrics["F1"])
        elif field_type == "numeric":
            if field in {"TumorSize", "ProximalMargin", "DistalMargin"}: vals.append(metrics["TolAcc_0.5"])
            elif field == "MetastaticLymphNode": vals.append(metrics["TolAcc_1"])
            elif field == "HarvestedLymphNode": vals.append(metrics["TolAcc_2"])
    return float(np.mean(vals) * 100)

def field_correctness_4q(field, gold_list, pred_list):
    """Compute per-record correctness for a single field using the four-quadrant rule:
    gold=null & pred=null  -> correct
    gold=null & pred=value -> incorrect (Hallucination)
    gold=value & pred=null -> incorrect (Miss)
    gold=value & pred=value -> correct only if values match
      (set equality for arrays, within-tolerance for numerics)
    is_field_correct() already implements this rule exactly, so it is reused directly."""
    gold_list = list(gold_list); pred_list = list(pred_list)
    if field in {"T_stage", "N_stage", "M_stage", "Staging"}:
        gold_list = apply_stage_normalization(field, gold_list)
        pred_list = apply_stage_normalization(field, pred_list)
    if field in LAUREN_FIELDS:
        return [extract_first(g) == extract_first(p) for g, p in zip(gold_list, pred_list)]
    elif field in CATEGORICAL_FIELDS:
        return [normalize_str(g) == normalize_str(p) for g, p in zip(gold_list, pred_list)]
    else:
        return [is_field_correct(g, p, field) for g, p in zip(gold_list, pred_list)]

def overall_average_4q(field_data):
    """[Final adopted metric] field_data: {field: (gold_list, pred_list)} -> (overall average (%), per-field accuracy dict)
    For each of the 16 fields, computes accuracy based on the four-quadrant rule (over all N records),
    then takes the simple mean of these 16 per-field accuracies as the overall average.
    Unlike overall_average(), null/miss/hallucination cases are NOT excluded — all are counted as incorrect —
    so models that output null to avoid errors are explicitly penalized."""
    field_accs = {}
    for field in ALL_FIELDS:
        gold_list, pred_list = field_data[field]
        correct = field_correctness_4q(field, gold_list, pred_list)
        field_accs[field] = sum(correct) / len(correct)
    overall = sum(field_accs.values()) / len(field_accs) * 100
    return overall, field_accs

# ══════════════════════════════════════════════════════════════════════════
# Data loading (supports two formats)
# ══════════════════════════════════════════════════════════════════════════
def load_gp(pred_path, test_ids=None):
    """g_Field/p_Field pair format. If test_ids is provided, filters to matching CHKIDs only."""
    df = pd.read_csv(pred_path, encoding="utf-8-sig")
    if "CHKID" in df.columns:
        df["CHKID"] = df["CHKID"].astype(str)
        if test_ids is not None:
            df = df[df["CHKID"].isin(test_ids)]
    df = df.reset_index(drop=True)
    return {field: (df[f"g_{field}"].tolist(), df[f"p_{field}"].tolist()) for field in ALL_FIELDS}, df

def load_baseline(pred_path, test_jsonl_path, margin_gold_path=None):
    """Baseline format with prediction columns only. Gold standard is retrieved from test_jsonl by CHKID."""
    with open(test_jsonl_path, "r", encoding="utf-8") as f:
        test_records = [json.loads(l) for l in f]
    test_ids = set(str(r["CHKID"]) for r in test_records)
    gold_by_chkid = {str(r["CHKID"]): dict(r["answer"]) for r in test_records}

    if margin_gold_path:
        margin_df = pd.read_csv(margin_gold_path, encoding="utf-8-sig")
        margin_df["CHKID"] = margin_df["CHKID"].astype(str)
        margin_map = margin_df.set_index("CHKID")[["Proximal_margin_cm", "Distal_margin_cm"]].to_dict("index")
        for chkid, vals in margin_map.items():
            if chkid in gold_by_chkid:
                gold_by_chkid[chkid]["ProximalMargin"] = vals["Proximal_margin_cm"]
                gold_by_chkid[chkid]["DistalMargin"] = vals["Distal_margin_cm"]

    df = pd.read_csv(pred_path, encoding="utf-8-sig")
    df["CHKID"] = df["CHKID"].astype(str)
    df = df[df["CHKID"].isin(test_ids)].reset_index(drop=True)
    chkid_list = df["CHKID"].tolist()

    result = {}
    for field in ALL_FIELDS:
        gold_list = [gold_by_chkid[c].get(field) for c in chkid_list]
        pred_list = df[field].tolist()
        result[field] = (gold_list, pred_list)
    return result, df

# ══════════════════════════════════════════════════════════════════════════
# Main evaluation routine
# ══════════════════════════════════════════════════════════════════════════
def evaluate(field_data, n_records, output_path=None):
    """field_data: {field: (gold_list, pred_list)} -> returns result DataFrame (and saves if output_path provided)"""
    field_results = []
    field_metrics_for_avg = {}
    field_correct_map = {}

    for field in ALL_FIELDS:
        gold_list, pred_list = field_data[field]
        field_type, metrics, correct = evaluate_one_field(field, gold_list, pred_list)
        field_metrics_for_avg[field] = (field_type, metrics)
        field_correct_map[field] = correct
        row = {"Level": "field", "Field": field, "Type": field_type}
        row.update(metrics)
        field_results.append(row)

    overall_ref = overall_average(field_metrics_for_avg)              # reference (standard classification metric average)
    overall_4q, field_accs_4q = overall_average_4q(field_data)         # [final adopted] four-quadrant method

    n = n_records
    report_correct = [all(field_correct_map[f][i] for f in ALL_FIELDS) for i in range(n)]
    rem = float(np.mean(report_correct))
    rem_count = int(np.sum(report_correct))

    report_row = {
        "Level": "report", "Field": "ALL", "Type": "report",
        "N": n, "ReportExactMatch": round(rem, 4), "ReportExactCount": rem_count,
        "OverallAverage_4Q": round(overall_4q, 4),   # final adopted metric
        "OverallAverage_ref": round(overall_ref, 4), # reference (standard classification metric average)
    }

    result_df = pd.DataFrame(field_results + [report_row])
    print(f"\nOverall Average [Four-Quadrant Method, Final Adopted]: {overall_4q:.2f}%")
    print(f"Overall Average [Standard Classification Metric Average, Reference]: {overall_ref:.2f}%")
    print(f"Report-level Exact Match: {rem*100:.2f}% ({rem_count}/{n})")

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        result_df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"Saved: {output_path}")

    return result_df, report_correct


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["gp", "baseline"])
    parser.add_argument("--pred", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--test-ids", default=None, help="(gp mode) Path to test.jsonl to restrict evaluation to 476 records; omit to use all rows")
    parser.add_argument("--test-jsonl", default=None, help="(baseline mode, required) Path to gold standard test.jsonl")
    parser.add_argument("--margin-gold", default=None, help="(baseline mode) CSV for ProximalMargin/DistalMargin cm correction")
    args = parser.parse_args()

    if args.mode == "gp":
        test_ids = None
        if args.test_ids:
            with open(args.test_ids, "r", encoding="utf-8") as f:
                test_ids = set(str(json.loads(l)["CHKID"]) for l in f)
        field_data, df = load_gp(args.pred, test_ids=test_ids)
        evaluate(field_data, len(df), args.output)
    else:
        if not args.test_jsonl:
            raise ValueError("--test-jsonl is required in baseline mode.")
        field_data, df = load_baseline(args.pred, args.test_jsonl, args.margin_gold)
        evaluate(field_data, len(df), args.output)
