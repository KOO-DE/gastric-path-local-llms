"""
config_ksp.py
Version with KSP 2nd edition guidelines included in the System Prompt
- Zero-shot / Few-shot / CoT
- Mx = M0 rule included
- 3 few-shot examples (including pM1 case)
"""

import json

# KSP guidelines
KSP_GUIDELINE = """
[Korean Society of Pathologists - Standardized Pathology Report for Gastric Cancer, 2nd Edition (2023)]

GROSS TYPE:
- Early gastric cancer (EGC): Type I, IIa, IIb, IIc, III (Japanese guideline)
- Advanced gastric cancer (AGC): Borrmann type 1, 2, 3, 4, unclassifiable (type 5)
- Determined by macroscopic examination

TUMOR LOCATION:
- Involvement: recorded using up to three portions from esophagus to duodenum (Upper/Middle/Lower third of stomach)
- Center: Cardia/Fundus/Body/Antrum/Pylorus + Lesser curvature/Greater curvature/Anterior wall/Posterior wall

TUMOR CIRCUMFERENCE:
- Describes the circumferential wall involvement of the tumor
- Values: Anterior wall, Posterior wall, Lesser curvature, Greater curvature

TUMOR SIZE:
- Recorded as the largest dimension (cm)

HISTOLOGIC TYPE (WHO 5th edition):
- Tubular adenocarcinoma (well/moderately/poorly differentiated)
- Papillary adenocarcinoma (>50% papillary component required)
- Mucinous adenocarcinoma (>50% extracellular mucin)
- Poorly cohesive carcinoma (PCC): includes signet ring cell (SRC) type and NOS
- Mixed adenocarcinoma (glandular + poorly cohesive components)
- Others: adenocarcinoma with lymphoid stroma, hepatoid, micropapillary, fundic-gland type, undifferentiated

LAUREN CLASSIFICATION:
- Intestinal: WD/MD tubular and papillary adenocarcinoma
- Diffuse: PCC and SRC
- Indeterminate: solid type PD adenocarcinoma (some disagreement exists)
- Mixed: intestinal and diffuse components in similar proportions

DIFFERENTIATION (grading):
- Well differentiated (WD): distinct glandular structure with columnar cells
- Moderately differentiated (MD): small glandular structure with cuboidal/flat cells
- Poorly differentiated (PD): rare luminal structure
- Three-tier system (WD/MD/PD) used; reflects largest tumor area

DEPTH OF INVASION (pT, AJCC 8th edition):
- pT1a: invades lamina propria or muscularis mucosae
- pT1b: invades submucosa (sm1/sm2/sm3)
- pT2: invades proper muscle
- pT3: invades subserosa (omentum/perigastric fat)
- pT4a: invades serosa (visceral peritoneum)
- pT4b: directly invades adjacent structures
- Note: cancer cells within lymphatic/vascular spaces NOT counted for invasion depth

RESECTION MARGIN:
- Proximal margin: distance from tumor to proximal resection margin in cm (null if involved)
- Distal margin: distance from tumor to distal resection margin in cm (null if involved)

REGIONAL LYMPH NODE METASTASIS:
- Minimum 16 regional lymph nodes should be assessed
- Report: metastasis in X out of Y regional lymph nodes
- pN0: no metastasis; pN1: 1-2; pN2: 3-6; pN3a: 7-15; pN3b: >=16
- Micrometastasis (0.2-2mm): counted as positive
- ITC (<0.2mm by IHC only): reported as pN0(i+), excluded from pN stage

LYMPHOVASCULAR INVASION (LVI):
- Includes both lymphatic and vascular invasion
- Reported as: Not identified / Present

PERINEURAL INVASION (PNI):
- Present when cancer cells observed within or around the nerve
- Reported as: Not identified / Present

STAGING (AJCC 8th edition):
- pTNM stage based on pT + pN + pM
- pM0: no distant metastasis (default for resection specimens)
- pM1: distant metastasis present
- "Mx" or "MX" means no distant metastasis confirmed -- treat as "M0"
""".strip()

# Common field definitions
FIELD_DEFINITIONS = """Extract the following fields from the gastric cancer pathology report and return a JSON object:

- TumorLocation (array): location(s) of tumor along the stomach axis.
  Values: "GEJ/Upper third", "Middle third", "Lower third"
  Note: Use "GEJ/Upper third" for tumors in the upper third including GEJ, cardia, and fundus.
        If the report describes a range, list all applicable values separately.
        Do NOT include wall information here.
        Wall information belongs to TumorCircumference field.

- TumorCircumference (array): circumferential wall involvement.
  Values: "Anterior wall", "Posterior wall", "Lesser curvature", "Greater curvature"
  Note: If all four walls are involved, list all four values separately.
        Do NOT use "all four walls".

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
  Note: "Mx" or "MX" means no distant metastasis confirmed -- treat as "M0"

- Staging (string): AJCC 8th edition overall stage.
  Values: "IA", "IB", "IIA", "IIB", "IIIA", "IIIB", "IIIC", "IV"

- MetastaticLymphNode (integer): number of metastatic lymph nodes

- HarvestedLymphNode (integer): total number of harvested lymph nodes

Rules:
- If a field is not mentioned in the report, use null
- Return ONLY a valid JSON object, no explanation"""

# Zero-shot with KSP
ZERO_SHOT_KSP_SYSTEM = (
    "You are an expert pathologist specializing in gastric cancer pathology report analysis.\n\n"
    "The following guidelines are from the Korean Society of Pathologists (KSP) Standardized Pathology Report "
    "for Gastric Cancer, 2nd Edition (2023). Use these as reference when extracting information:\n\n"
    + KSP_GUIDELINE
    + "\n\n---\n\n"
    + FIELD_DEFINITIONS
)

ZERO_SHOT_KSP_USER = "Pathology report:\n{report}\n\nExtract the fields as JSON:"

# Few-shot with KSP
FEW_SHOT_KSP_SYSTEM = (
    "You are an expert pathologist specializing in gastric cancer pathology report analysis.\n\n"
    "The following guidelines are from the Korean Society of Pathologists (KSP) Standardized Pathology Report "
    "for Gastric Cancer, 2nd Edition (2023). Use these as reference when extracting information:\n\n"
    + KSP_GUIDELINE
    + "\n\n---\n\n"
    + FIELD_DEFINITIONS
)

FEW_SHOT_KSP_EXAMPLES = [
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

FEW_SHOT_KSP_USER = "Pathology report:\n{report}\n\nExtract the fields as JSON:"

# CoT with KSP
COT_KSP_SYSTEM = (
    "You are an expert pathologist specializing in gastric cancer pathology report analysis.\n\n"
    "The following guidelines are from the Korean Society of Pathologists (KSP) Standardized Pathology Report "
    "for Gastric Cancer, 2nd Edition (2023). Use these as reference when extracting information:\n\n"
    + KSP_GUIDELINE
    + "\n\n---\n\n"
    + FIELD_DEFINITIONS
    + "\n\nExtract the fields using the following steps:\n"
    "Step 1. Read the report carefully.\n"
    "Step 2. For potentially ambiguous fields (Histologic_type, Lauren_type, Differentiation, T/N/M stage, Staging), "
    "briefly reason based on KSP guidelines above.\n"
    "Step 3. Output the final JSON object.\n\n"
    "Format your response as:\n"
    "<reasoning>\n"
    "[brief reasoning for ambiguous fields only]\n"
    "</reasoning>\n"
    "<json>\n"
    "{JSON object}\n"
    "</json>"
)

COT_KSP_USER = "Pathology report:\n{report}"


def get_messages(prompt_type: str, report: str) -> list:
    if prompt_type == "zero_shot_ksp":
        return [
            {"role": "system", "content": ZERO_SHOT_KSP_SYSTEM},
            {"role": "user",   "content": ZERO_SHOT_KSP_USER.format(report=report)},
        ]
    elif prompt_type == "few_shot_ksp":
        messages = [{"role": "system", "content": FEW_SHOT_KSP_SYSTEM}]
        for ex in FEW_SHOT_KSP_EXAMPLES:
            messages.append({"role": "user",      "content": FEW_SHOT_KSP_USER.format(report=ex["report"])})
            messages.append({"role": "assistant", "content": json.dumps(ex["answer"], ensure_ascii=False)})
        messages.append({"role": "user", "content": FEW_SHOT_KSP_USER.format(report=report)})
        return messages
    elif prompt_type == "cot_ksp":
        return [
            {"role": "system", "content": COT_KSP_SYSTEM},
            {"role": "user",   "content": COT_KSP_USER.format(report=report)},
        ]
    else:
        raise ValueError(f"Unknown prompt_type: {prompt_type}")


PROMPT_TYPES = ["zero_shot_ksp", "few_shot_ksp", "cot_ksp"]
