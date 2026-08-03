"""
config_baseline.py
Baseline version — no KSP guidelines, minimal prompts
- Zero-shot / Few-shot / CoT
- Mx = M0 rule included
"""

import json

# ── Common field definitions ───────────────────────────────────────────────────
FIELD_DEFINITIONS = """Extract the following fields from the gastric cancer pathology report and return a JSON object:

- TumorLocation (array): location(s) of tumor along the stomach axis.
  Values: "GEJ/Upper third", "Middle third", "Lower third"
  Note: Do NOT include wall information here.
        Wall information belongs to TumorCircumference field.

- TumorCircumference (array): circumferential wall involvement.
  Values: "Anterior wall", "Posterior wall", "Lesser curvature", "Greater curvature"

- TumorSize (number): largest tumor dimension in cm

- Histologic_type (array): WHO histologic type(s).
  Values: "Well differentiated (W/D) adenocarcinoma",
  "Moderately differentiated (M/D) adenocarcinoma",
  "Poorly differentiated (P/D) adenocarcinoma",
  "Poorly cohesive carcinoma / Signet ring cell carcinoma",
  "Mixed type (tubular adenocarcinoma and/or PCC)",
  "Mucinous carcinoma", "Papillary carcinoma",
  "Gastric carcinoma with lymphoid stroma",
  "Neuroendocrine tumor", "Other"

- Lauren_type (array): Lauren classification.
  Values: "Intestinal", "Diffuse", "Mixed", "Indeterminate", "Unknown"

- Differentiation (array): differentiation grade(s).
  Values: "Well differentiated", "Moderately differentiated",
  "Poorly differentiated", "Signet ring/Poorly cohesive"

- ProximalMargin (number): proximal resection margin distance in cm. null if involved.

- DistalMargin (number): distal resection margin distance in cm. null if involved.

- LymphovascularInvasion (string): "Yes" or "No"

- PerineuralInvasion (string): "Yes" or "No"

- T_stage (string): T stage. Values: "T1a", "T1b", "T2", "T3", "T4a", "T4b"

- N_stage (string): N stage. Values: "N0", "N1", "N2", "N3a", "N3b"

- M_stage (string): M stage. Values: "M0", "M1"
  Note: "Mx" or "MX" means no distant metastasis confirmed — treat as "M0"

- Staging (string): AJCC 8th edition overall stage.
  Values: "IA", "IB", "IIA", "IIB", "IIIA", "IIIB", "IIIC", "IV"

- MetastaticLymphNode (integer): number of metastatic lymph nodes

- HarvestedLymphNode (integer): total number of harvested lymph nodes

Rules:
- If a field is not mentioned in the report, use null
- Return ONLY a valid JSON object, no explanation"""

# ── Zero-shot ──────────────────────────────────────────────────────────────────
ZERO_SHOT_SYSTEM = """You are an expert pathologist specializing in gastric cancer pathology report analysis.

""" + FIELD_DEFINITIONS

ZERO_SHOT_USER = "Pathology report:\n{report}\n\nExtract the fields as JSON:"

# ── Few-shot ───────────────────────────────────────────────────────────────────
FEW_SHOT_SYSTEM = """You are an expert pathologist specializing in gastric cancer pathology report analysis.

""" + FIELD_DEFINITIONS

FEW_SHOT_EXAMPLES = [
    {
        "report": """Stomach, subtotal gastrectomy:
Tubular adenocarcinoma, moderately differentiated
1) gross type: Borrmann type 3
2) size: 5.0 x 4.0 cm
3) site: antrum, posterior wall, lesser curvature
4) histologic type: tubular adenocarcinoma, moderately differentiated
5) differentiation: moderate
6) Lauren classification: intestinal type
7) depth of invasion: invades subserosa (pT3)
8) lymphovascular invasion: present
9) perineural invasion: absent
10) perigastric lymph node metastasis: metastasis in 3 out of 25 lymph nodes
11) proximal resection margin: free (safety margin, 6.0 cm)
12) distal resection margin: free (safety margin, 2.5 cm)
* pTNM stage (AJCC 8th): pT3N2M0""",
        "answer": {
            "TumorLocation": ["Lower third"],
            "TumorCircumference": ["Posterior wall", "Lesser curvature"],
            "TumorSize": 5.0,
            "Histologic_type": ["Moderately differentiated (M/D) adenocarcinoma"],
            "Lauren_type": ["Intestinal"],
            "Differentiation": ["Moderately differentiated"],
            "ProximalMargin": 6.0,
            "DistalMargin": 2.5,
            "LymphovascularInvasion": "Yes",
            "PerineuralInvasion": "No",
            "T_stage": "T3",
            "N_stage": "N2",
            "M_stage": "M0",
            "Staging": "IIIA",
            "MetastaticLymphNode": 3,
            "HarvestedLymphNode": 25
        }
    },
    {
        "report": """Stomach, total gastrectomy:
Poorly cohesive carcinoma, signet ring cell type
1) gross type: EGC type IIc
2) size: 2.0 x 1.5 cm
3) site: body, anterior wall
4) histologic type: poorly cohesive carcinoma, signet ring cell type
5) differentiation: poorly differentiated
6) Lauren classification: diffuse type
7) depth of invasion: invades lamina propria (pT1a)
8) lymphovascular invasion: not identified
9) perineural invasion: not identified
10) perigastric lymph node metastasis: no metastasis in 18 regional lymph nodes
11) proximal resection margin: free (safety margin, 3.2 cm)
12) distal resection margin: free (safety margin, 8.0 cm)
* pTNM stage (AJCC 8th): pT1aN0Mx""",
        "answer": {
            "TumorLocation": ["Middle third"],
            "TumorCircumference": ["Anterior wall"],
            "TumorSize": 2.0,
            "Histologic_type": ["Poorly cohesive carcinoma / Signet ring cell carcinoma"],
            "Lauren_type": ["Diffuse"],
            "Differentiation": ["Signet ring/Poorly cohesive"],
            "ProximalMargin": 3.2,
            "DistalMargin": 8.0,
            "LymphovascularInvasion": "No",
            "PerineuralInvasion": "No",
            "T_stage": "T1a",
            "N_stage": "N0",
            "M_stage": "M0",
            "Staging": "IA",
            "MetastaticLymphNode": 0,
            "HarvestedLymphNode": 18
        }
    },
    {
        "report": """Stomach, total gastrectomy:
Tubular adenocarcinoma, poorly differentiated
1) gross type: Borrmann type 4
2) size: 9.0 x 8.0 cm
3) site: whole stomach, all walls
4) histologic type: tubular adenocarcinoma, poorly differentiated
5) Lauren classification: indeterminate type
6) depth of invasion: directly invades adjacent structure, pancreas (pT4b)
7) lymphovascular invasion: present
8) perineural invasion: present
9) lymph node metastasis: metastasis in 20 out of 35 lymph nodes
10) proximal resection margin: involved by carcinoma
11) distal resection margin: free (safety margin, 0.2 cm)
12) distant metastasis: liver metastasis identified
* pTNM stage (AJCC 8th): pT4bN3bM1""",
        "answer": {
            "TumorLocation": ["GEJ/Upper third", "Middle third", "Lower third"],
            "TumorCircumference": ["Anterior wall", "Posterior wall", "Lesser curvature", "Greater curvature"],
            "TumorSize": 9.0,
            "Histologic_type": ["Poorly differentiated (P/D) adenocarcinoma"],
            "Lauren_type": ["Indeterminate"],
            "Differentiation": ["Poorly differentiated"],
            "ProximalMargin": None,
            "DistalMargin": 0.2,
            "LymphovascularInvasion": "Yes",
            "PerineuralInvasion": "Yes",
            "T_stage": "T4b",
            "N_stage": "N3b",
            "M_stage": "M1",
            "Staging": "IV",
            "MetastaticLymphNode": 20,
            "HarvestedLymphNode": 35
        }
    },
]

FEW_SHOT_USER = "Pathology report:\n{report}\n\nExtract the fields as JSON:"

# ── CoT ───────────────────────────────────────────────────────────────────────
COT_SYSTEM = """You are an expert pathologist specializing in gastric cancer pathology report analysis.

""" + FIELD_DEFINITIONS + """

Extract the fields using the following steps:
Step 1. Read the report carefully.
Step 2. For potentially ambiguous fields (Histologic_type, Lauren_type, Differentiation, T/N/M stage, Staging), briefly reason before deciding.
Step 3. Output the final JSON object.

Format your response as:
<reasoning>
[brief reasoning for ambiguous fields only]
</reasoning>
<json>
{JSON object}
</json>"""

COT_USER = "Pathology report:\n{report}"

# ── get_messages function ──────────────────────────────────────────────────────
def get_messages(prompt_type: str, report: str) -> list:
    if prompt_type == "zero_shot":
        return [
            {"role": "system", "content": ZERO_SHOT_SYSTEM},
            {"role": "user",   "content": ZERO_SHOT_USER.format(report=report)},
        ]
    elif prompt_type == "few_shot":
        messages = [{"role": "system", "content": FEW_SHOT_SYSTEM}]
        for ex in FEW_SHOT_EXAMPLES:
            messages.append({"role": "user",      "content": FEW_SHOT_USER.format(report=ex["report"])})
            messages.append({"role": "assistant", "content": json.dumps(ex["answer"], ensure_ascii=False)})
        messages.append({"role": "user", "content": FEW_SHOT_USER.format(report=report)})
        return messages
    elif prompt_type == "cot":
        return [
            {"role": "system", "content": COT_SYSTEM},
            {"role": "user",   "content": COT_USER.format(report=report)},
        ]
    else:
        raise ValueError(f"Unknown prompt_type: {prompt_type}")


PROMPT_TYPES = ["zero_shot", "few_shot", "cot"]
