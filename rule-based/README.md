# Rule-Based Extraction System

This folder contains MySQL SQL queries for extracting 16 standardized clinical variables from gastric cancer surgical pathology reports stored in the hospital CDW (Clinical Data Warehouse).

---

## Overview

The rule-based system extracts structured clinical information from semi-structured pathology report text using pattern matching, string functions, and regular expressions in MySQL. Each SQL file targets one or more related clinical variables.

The pathology reports follow a semi-structured format with numbered item labels (e.g., `1) gross type: ...`, `2) size: ...`), which allows reliable label-based extraction followed by value parsing after colons or semicolons.

---

## Source Table

All queries read from a table named `pathology_report`, which represents the pathology report table in the hospital CDW. The table name has been anonymized from the original internal schema for public release. The key column is `병리진단`, which contains the full free-text pathology report.

---

## SQL Files

| File | Extracted Variables | Notes |
|---|---|---|
| `histologic_type.sql` | Histologic type | Handles three report format versions (VER1/VER2/VER3); normalizes abbreviations (TA, MuA, PCC, SRC, etc.) |
| `differentiation.sql` | Differentiation grade | Handles mixed differentiation (e.g., "poorly to moderately"); resolves majority component by percentage when available |
| `lauren_type.sql` | Lauren classification | Extracts Intestinal / Diffuse / Mixed from both standard and early gastric cancer report formats |
| `invasion.sql` | Lymphovascular invasion, Perineural invasion | Binary present/absent classification; handles both fields in a single query |
| `lymph_node.sql` | Metastatic lymph node count, Harvested lymph node count | Parses `X/Y` format across up to 13 lymph node stations; sums metastatic (numerator) and harvested (denominator) counts |
| `margin.sql` | Proximal resection margin, Distal resection margin | Extracts margin distance (cm) or positive/negative status; handles clear resection margin phrases |
| `tumor_site.sql` | Tumor location, Tumor circumference | Extracts anatomical site (cardia, fundus, upper/mid/lower body, pylorus, antrum) and wall involvement (anterior, posterior, greater/lesser curvature) |
| `tumor_size.sql` | Tumor size | Extracts major × minor dimensions in cm; handles mm-to-cm conversion |
| `staging.sql` | T stage, N stage, M stage, Staging (AJCC 8th) | Two-step extraction: (1) parse raw pTNM string from report, (2) classify into standardized T/N/M categories and derive AJCC 8th edition overall stage |

---

## Query Design

- Queries use **nested subqueries** (or CTEs via `WITH`) to progressively parse and normalize raw text.
- Multi-step queries (e.g., `histologic_type.sql`, `staging.sql`) are combined into a single file using CTEs to avoid intermediate table dependencies.
- The source table is referred to as `pathology_report` throughout the queries. This is an anonymized placeholder for the internal CDW table name.
- Korean column names (`원무접수ID`, `환자번호`, `검사시행일`, `병리진단`) reflect the original CDW schema and are preserved as-is for reproducibility.
- Patient identifiers (`원무접수ID`, `환자번호`) are present in the query output but were de-identified before use in this study.

---

## Notes

- These queries are written for **MySQL 8.0+** and use MySQL-specific functions (`REGEXP_REPLACE`, `REGEXP_SUBSTR`, `REGEXP_INSTR`, `SUBSTR`, `INSTR`, etc.).
- The queries are designed for the specific pathology report format used at Chungnam National University Hospital (2013–2022) and may require adaptation for other institutions or report formats.
- Report format variation across the study period is handled within each query (e.g., VER1/VER2/VER3 branching in `histologic_type.sql`).
