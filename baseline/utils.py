"""
utils.py
Common utility functions
- Data loading
- JSON parsing (zero_shot, few_shot, cot)
- Result saving
"""

import json
import re
import pandas as pd
from pathlib import Path

# ── Target extraction fields ───────────────────────────────────────────────────
EXTRACTION_FIELDS = [
    "TumorLocation",
    "TumorCircumference",
    "TumorSize",
    "Histologic_type",
    "Lauren_type",
    "Differentiation",
    "ProximalMargin",
    "DistalMargin",
    "LymphovascularInvasion",
    "PerineuralInvasion",
    "T_stage",
    "N_stage",
    "M_stage",
    "Staging",
    "MetastaticLymphNode",
    "HarvestedLymphNode",
]

# ── Data loading ───────────────────────────────────────────────────────────────
def load_reports(input_path: str) -> pd.DataFrame:
    """
    Load xlsx or csv file
    Columns: Age, Sex, OperationDate, PathologyReport (+ additional columns)
    """
    path = Path(input_path)
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(input_path, encoding="utf-8-sig")
    else:
        df = pd.read_excel(input_path, header=0)
    return df

def get_report_texts(df: pd.DataFrame) -> list:
    texts = []
    for text in df["PathologyReport"].fillna(""):
        text = str(text)
        text = text.replace("병  리  진  단", "").strip()
        idx = text.find("◈ 검사항목")
        if idx > 0:
            text = text[:idx].strip()
        lines = [l for l in text.split("\n")
                 if "등록일시" not in l and "등록자" not in l]
        text = "\n".join(lines).strip()
        texts.append(text)
    return texts

# ── JSON parsing ───────────────────────────────────────────────────────────────
def _extract_json_str(text: str) -> str | None:
    """Extract JSON string from text"""
    # <json>...</json> tags
    m = re.search(r"<json>\s*(\{.*?\})\s*</json>", text, re.DOTALL)
    if m:
        return m.group(1)
    # First {...} block
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        return m.group(0)
    return None


def parse_response(text: str, prompt_type: str) -> dict:
    """
    Parse model output
    - zero_shot / few_shot: direct JSON output
    - cot: <reasoning>...</reasoning><json>...</json> format
    """
    if text is None:
        return {}

    text = text.strip()

    json_str = _extract_json_str(text)
    if json_str is None:
        return {}

    try:
        parsed = json.loads(json_str)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


# ── Output DataFrame construction ──────────────────────────────────────────────
def build_output_df(df: pd.DataFrame, results: list[dict]) -> pd.DataFrame:
    """
    Append extraction result columns to the original df
    results: [{field: value, ...}, ...] with length == len(df)
    """
    out = df.copy()
    for field in EXTRACTION_FIELDS:
        out[field] = [r.get(field) for r in results]
    return out


# ── Result saving ──────────────────────────────────────────────────────────────
def save_results(df: pd.DataFrame, output_path: str, model_key: str):
    """Save results (csv or xlsx)"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.suffix.lower() == ".csv":
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
    else:
        df.to_excel(output_path, index=False, engine="openpyxl")

    print(f"[{model_key}] Saved: {output_path} ({len(df)} records)")
