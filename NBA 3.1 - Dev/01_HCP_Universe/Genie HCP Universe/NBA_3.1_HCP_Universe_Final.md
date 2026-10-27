# Kerendia NBA 3.1 — HCP Universe (Final)

**Date:** October 19, 2026
**Status:** Complete
**Built by:** Genie Code

---

## 1. Universe Summary

| | Count |
|:--|------:|
| **Total Universe** | **294,505** |
| Budget limit | 300,000 |
| **Budget check** | **PASS ✅** |
| Kerendia writer capture | 61,583 / 61,583 (**100.0%**) |
| NBA 3.0 overlap | 220,031 / 232,965 (**94.4%**) |

---

## 2. Criteria Breakdown

| Criterion | Definition | Count |
|:----------|:-----------|------:|
| **C1: Core Prescribers** | Set1 (T2D×SGLT2/GLP1) ∪ Set3 (CKD×SGLT2/GLP1) at D2+ | 242,976 |
| **C2: Kerendia Writers** | NBRX > 0, all claim types (PD+RV+RJ), full history since Jul 2021 | 61,583 |
| **C3: Specialists** | Nephrologists (15,063) + Cardiologists (51,717) | 66,780 |
| **C4: Targeting/BPT** | CP_KER_HCP (FF in CR1/CR2/CR4/CR5, Product = KERENDIA) | 78,798 |

### Incremental Buildup

| Step | Total | Incremental |
|:-----|------:|------------:|
| C1 Core (Set1 ∪ Set3, D2+) | 242,976 | — |
| + C2 Kerendia Writers | 255,052 | +12,076 |
| + C3 NEPH | 259,596 | +4,544 |
| + C3 CARD | 291,630 | +32,034 |
| + C4 Targeting/BPT | 294,505 | +2,875 |

---

## 3. Data Sources

| Source | Table / Path | Window |
|:-------|:-------------|:-------|
| Claims (C1) | `pace_ker_in_house_schema.lrx_nbrx` | Oct 2024 – Sep 2026 (24 mo) |
| Kerendia Writers (C2) | `/Volumes/.../kerendia_nbrx_from_raw_fct_rx` (Delta) | Full history (Jul 2021+) |
| Specialists (C3) | `lrx_nbrx` SPECIALTY_GROUP | 24-mo lookback |
| Targeting (C4) | Snowflake `PHCDW.PHCDW_TARGETING.CP_KER_HCP` | Current list |
| Call History (C5) | Snowflake `CPH_DB_PROD.MODEL_V2.FACT_CALL` | Since Jan 2023 |
| NBA 3.0 Baseline | `/Volumes/.../kerendia_nba_3_hcp_model_base_hcp_universe_for_inference` | PULL_DT: 2026_10_09 |

### Source Counts

| Parameter | Value |
|:----------|:------|
| `lrx_nbrx` full table | 248,320,834 rows |
| `lrx_nbrx` 24-mo lookback | 104,871,069 rows |
| Unique HCPs in lookback | 1,361,189 |
| NBA 3.0 baseline | 232,965 HCPs |
| ID mapping table | 1,650,983 rows |

---

## 4. C1 Decile Analysis: The 8-Set Matrix

### HCP Counts by Set and Decile Cutoff

| Set | Ind × Pool | Total | D2+ | D3+ | D4+ |
|:---:|:-----------|------:|----:|----:|----:|
| 1 | T2D × SGLT2/GLP1 | 555,175 | 211,132 | 146,433 | 106,998 |
| 2 | T2D × ACE/ARB | 605,968 | 281,567 | 196,031 | 143,516 |
| 3 | CKD × SGLT2/GLP1 | 451,058 | 205,459 | 136,669 | 95,575 |
| 4 | CKD × ACE/ARB | 496,725 | 254,305 | 173,498 | 123,764 |
| 5 | HF × SGLT2/GLP1 | 432,481 | 228,937 | 156,175 | 109,955 |
| 6 | HF × ACE/ARB | 411,128 | 242,821 | 163,360 | 115,228 |
| 7 | T1D × SGLT2/GLP1 | 56,821 | 43,214 | 29,607 | 17,698 |
| 8 | T1D × ACE/ARB | 115,665 | 97,786 | 79,907 | 62,028 |

### Why Core = Set1 ∪ Set3 at D2+

* T2D and CKD are Kerendia's primary indications
* SGLT2/GLP1 is the drug pool most aligned with the Kerendia prescriber profile
* D2+ captures 80.4% of Kerendia writers in ~243K HCPs
* Additional sets yield diminishing returns (148K more HCPs for only 6K more writers)

### Greedy Set Addition (from Core D2+)

| Step | Action | Universe | Ker Writers | % Captured | Marginal HCPs | Marginal Writers |
|:----:|:-------|--------:|-----------:|:----------:|--------------:|-----------------:|
| 0 | Core (Set1 ∪ Set3) | 242,976 | 49,507 | 80.4% | — | — |
| 1 | + Set4 CKD×ACE/ARB | 308,480 | 53,315 | 86.6% | +65,504 | +3,808 |
| 2 | + Set5 HF×SGLT2/GLP1 | 332,091 | 54,199 | 88.0% | +23,611 | +884 |
| 3 | + Set2 T2D×ACE/ARB | 353,729 | 54,894 | 89.1% | +21,638 | +695 |
| 4–6 | + T1D + HF×ACE/ARB | 391,181 | 55,551 | 90.2% | +37,452 | +657 |

> After Core + Set4, each set adds < 900 writers for 20K+ HCPs. C2 recovers the remaining 9.8% explicitly.

---

## 5. Validation Metrics

### NBA 3.0 Overlap

| | Count |
|:--|------:|
| Universe | 294,505 |
| NBA 3.0 | 232,965 |
| **Overlap** | **220,031 (94.4% of NBA 3.0)** |
| Universe-only | 74,474 |
| NBA30-only | 12,934 |

### Kerendia Writer Coverage (Independent Metrics)

| Metric | Source | Baseline | Captured | % | Missed |
|:-------|:-------|:---------|:---------|:---:|-------:|
| **M1** | NBA 3.0 KERENDIA_FLAG | 77,972 | 71,790 | **92.1%** | 6,182 |
| **M2** | LAAD V6 NBRX>0 (24-mo) | 40,512 | 40,382 | **99.7%** | 130 |
| **M3** | LAAD V6 TRX>0 (24-mo) | 68,416 | 63,647 | **93.0%** | 4,769 |
| **M4** | FCT_RX paid TRX (24-mo) | 68,375 | 63,619 | **93.0%** | 4,756 |
| **C2** | FCT_RX NBRX overall | 61,583 | 61,583 | **100.0%** | 0 |

> All metrics exceed 92%. M2 near-perfect (99.7%) because C1+C2 covers nearly all in-table paid NBRX writers.

---

## 6. Hotspot Analysis: Writers Missed by C1

Of the 61,583 C2 writers, **12,076 (19.6%)** are not in C1 Core (D2+).

### Specialty Profile of Missed Writers

| Specialty | Count | % |
|:----------|------:|:---:|
| PCP | 7,708 | 63.8% |
| NEPH | 1,578 | 13.1% |
| CARD | 1,378 | 11.4% |
| NULL (no lrx_nbrx record) | 952 | 7.9% |
| OTHERS | 168 | 1.4% |
| ENDO | 151 | 1.3% |
| HOS | 137 | 1.1% |

### Kerendia NBRX Volume of Missed Writers

| NBRX Bucket | Count | % |
|:------------|------:|:---:|
| 1 (single script) | 8,212 | 68.0% |
| 2–3 | 2,334 | 19.3% |
| 4–5 | 639 | 5.3% |
| 6–10 | 498 | 4.1% |
| 11+ | 393 | 3.3% |

> Avg NBRX: 2.4 | Median: 1 | Avg TRX: 14.4

### Recovery Paths

* **C2 recovers all 12,076** by definition (explicit Kerendia writer criterion)
* **C3 recovers 2,956** (NEPH + CARD specialists who are also writers)
* **C4 recovers 3,977** (targeting list overlap)

---

## 7. Call History Overlap (C5 Exploration)

**Source:** `CPH_DB_PROD.MODEL_V2.FACT_CALL` via Python Snowflake connector
**Filters:** `STAT='Submitted_vod'`, `DETL_PROD LIKE '%KERENDIA%'`, `BAYER_CUST_ID NOT LIKE '%BHO%'`, `CALL_DATE >= '2023-01-01'`

| Metric | Count |
|:-------|------:|
| Called HCPs since 2023 | 160,929 |
| In universe | 136,191 (84.6%) |
| **Outside universe** | **24,738 (15.4%)** |

### Profile of 24,738 Called-but-Outside HCPs

| Specialty | Count |
|:----------|------:|
| PCP | 20,823 (84.2%) |
| NULL | 2,640 (10.7%) |
| OTHERS | 761 (3.1%) |
| ENDO | 473 (1.9%) |
| HOSPITALIST | 41 (0.2%) |

> These are predominantly **low-volume PCPs** — commercially active (recently called) but prescribing too little SGLT2/GLP1 to cross the D2 cutoff. A C5 criterion would capture ~24.7K additional HCPs.

---

## 8. Universe Output Schema

| Column | Description |
|:-------|:------------|
| `PROVIDER_ID` | IQVIA provider identifier (7-8 digit string) |
| `C1_FLAG` | 1 if HCP entered through Core Prescribers (D2+) |
| `C2_FLAG` | 1 if HCP is a Kerendia writer |
| `C3_FLAG` | 1 if HCP entered through Specialty (NEPH/CARD) |
| `C4_FLAG` | 1 if HCP is on Targeting/BPT list |
| `SPECIALTY_GROUP` | PCP, NEPH, CARD, ENDO, HOS, OTHERS, HOSPITALIST |

### Flag Distribution

| Flag | Count | % of Universe |
|:-----|------:|--------------:|
| C1_FLAG = 1 | 242,976 | 82.5% |
| C2_FLAG = 1 | 61,583 | 20.9% |
| C3_FLAG = 1 | 66,780 | 22.7% |
| C4_FLAG = 1 | 78,798 | 26.8% |

---

## 9. Notebook Artifacts

| File | Purpose |
|:-----|:--------|
| `00_Approach.md` | Methodology and strategy documentation |
| `01_Data_Exploration` | Source data loading, schema, distributions |
| `02_Universe_Construction` | C1–C4 build, decile computation, universe assembly |
| `03_Validation_Hotspot` | NBA 3.0 overlap, M1–M4 metrics, hotspot, greedy addition, C5 call history |
| `NBA_3.1_HCP_Universe_Final.md` | This document |

---

*Generated by Genie Code — October 19, 2026*
