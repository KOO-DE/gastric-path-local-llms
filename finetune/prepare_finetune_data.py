"""
Fine-tuning data preparation script
- Generate (report text, ground-truth JSON) pairs
- Stratified split into train (70%) / val (10%) / test (20%)
"""

import pandas as pd
import json
import argparse
import os
from sklearn.model_selection import train_test_split

parser = argparse.ArgumentParser()
parser.add_argument("--gold",       required=True, help="Path to gold_standard.csv")
parser.add_argument("--reports",    required=True, help="Path to pathology_reports.xlsx")
parser.add_argument("--output_dir", default="finetune_data", help="Output directory")
args = parser.parse_args()

os.makedirs(args.output_dir, exist_ok=True)

# ── 1. Load data ───────────────────────────────────────────────────────────────
print("[1/4] Loading data...")
gold = pd.read_csv(args.gold, encoding='utf-8-sig')
path = pd.read_excel(args.reports)
print(f"  gold: {len(gold)} records, reports: {len(path)} records")

# ── 2. Matching ────────────────────────────────────────────────────────────────
print("[2/4] Matching records...")
gold['Sex_norm'] = gold['Sex'].map({'Male': 'm', 'Female': 'f'})
path['Sex_norm'] = path['Sex'].str.lower().str.strip()
gold['Op_date_norm'] = pd.to_datetime(gold['Op_date']).dt.date
path['OP_Date_norm'] = pd.to_datetime(path['OP_Date']).dt.date

merged = pd.merge(
    path, gold,
    left_on=['Sex_norm', 'OP_AGE', 'OP_Date_norm'],
    right_on=['Sex_norm', 'Age',   'Op_date_norm'],
    how='inner'
)
print(f"  Matched: {len(merged)} records")

# ── 3. Build ground-truth JSON ─────────────────────────────────────────────────
print("[3/4] Building ground-truth JSON...")

def normalize_margin(val):
    if pd.isna(val):
        return None
    val = str(val).strip().lower()
    if val in ['free', '0', 'negative']:
        return 'free'
    elif val in ['involved', '1', 'positive']:
        return 'involved'
    return val

def normalize_invasion(val):
    if pd.isna(val):
        return None
    val = str(val).strip().lower()
    if val in ['1', 'yes', 'present', 'positive']:
        return 'positive'
    elif val in ['0', 'no', 'absent', 'negative']:
        return 'negative'
    return val

def normalize_array(val):
    """Pipe/semicolon-delimited string → list"""
    if pd.isna(val):
        return None
    val = str(val).strip()
    if '|' in val:
        return [v.strip() for v in val.split('|') if v.strip()]
    elif ';' in val:
        return [v.strip() for v in val.split(';') if v.strip()]
    return [val] if val else None

def normalize_int(val):
    try:
        return int(float(val))
    except:
        return None

def normalize_float(val):
    try:
        return float(val)
    except:
        return None

def build_answer(row):
    return {
        "TumorLocation":          normalize_array(row.get('Tumor_location')),
        "TumorCircumference":     normalize_array(row.get('Tumor_circumference')),
        "TumorSize":              normalize_float(row.get('Tumor_size_cm')),
        "Histologic_type":        normalize_array(row.get('Histology')),
        "Lauren_type":            normalize_array(row.get('Lauren_type')),
        "Differentiation":        normalize_array(row.get('Differentiation')),
        "GrossType":              str(row.get('Depth_of_tumor', '')).strip() or None,
        "ProximalMargin":         normalize_margin(row.get('Proximal_margin_cm')),
        "DistalMargin":           normalize_margin(row.get('Distal_margin_cm')),
        "LymphovascularInvasion": normalize_invasion(row.get('Lymphovascular_invasion')),
        "PerineuralInvasion":     normalize_invasion(row.get('Perineural_invasion')),
        "T_stage":                str(row.get('T_stage', '')).strip() or None,
        "N_stage":                str(row.get('N_stage', '')).strip() or None,
        "M_stage":                str(row.get('M_stage', '')).strip() or None,
        "Staging":                str(row.get('Stage_8th_TNM', '')).strip() or None,
        "MetastaticLymphNode":    normalize_int(row.get('Metastatic_LN_count')),
        "HarvestedLymphNode":     normalize_int(row.get('Harvested_LN_count')),
    }

records = []
for _, row in merged.iterrows():
    report = str(row['PathologyReport']).strip()
    answer = build_answer(row)
    records.append({
        "CHKID":         row['CHKID'],
        "ID":            row['ID'],
        "Sex_reg":       row['Sex_norm'],
        "OP_Age":        row['OP_AGE'],
        "OperationDate": str(row['OP_Date_norm']),
        "report":        report,
        "answer":        answer,
        "T_stage":       str(row.get('T_stage', 'Unknown')).strip(),  # for stratification
    })

df = pd.DataFrame(records)
print(f"  Records created: {len(df)}")

# ── 4. Stratified split (by T_stage) ──────────────────────────────────────────
print("[4/4] Splitting data (stratified by T_stage)...")

# Handle unknown T_stage values
df['T_stage_strat'] = df['T_stage'].replace({'Unknown': 'T1a', 'nan': 'T1a'}).fillna('T1a')  # map Unknown to most frequent class

# train 70% / temp 30%
train_df, temp_df = train_test_split(
    df, test_size=0.3, random_state=42,
    stratify=df['T_stage_strat']
)

# temp → val 33% / test 67% (10% / 20% of total)
val_df, test_df = train_test_split(
    temp_df, test_size=0.667, random_state=42,
    stratify=temp_df['T_stage_strat']
)

print(f"  train: {len(train_df)} records")
print(f"  val:   {len(val_df)} records")
print(f"  test:  {len(test_df)} records")

# ── 5. Save ────────────────────────────────────────────────────────────────────
def save_jsonl(df, path):
    with open(path, 'w', encoding='utf-8') as f:
        for _, row in df.iterrows():
            f.write(json.dumps({
                "CHKID":  row['CHKID'],
                "ID":     row['ID'],
                "report": row['report'],
                "answer": row['answer'],
            }, ensure_ascii=False) + '\n')

save_jsonl(train_df, os.path.join(args.output_dir, 'train.jsonl'))
save_jsonl(val_df,   os.path.join(args.output_dir, 'val.jsonl'))
save_jsonl(test_df,  os.path.join(args.output_dir, 'test.jsonl'))

print(f"\nDone! Saved to: {args.output_dir}/")
print(f"  train.jsonl: {len(train_df)} records")
print(f"  val.jsonl:   {len(val_df)} records")
print(f"  test.jsonl:  {len(test_df)} records")
