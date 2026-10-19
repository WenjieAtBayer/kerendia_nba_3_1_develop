# NextGen NBA 3.1 — HCP Universe Selection Analysis

**Date:** October 9, 2026  
**Notebook Reference:** `01_HCP_Universe/01_HCP_Universe_Identification`  
**Status:** Exploratory Analysis — Transitioning from Product-Based to Indication-Based Universe

---

## 1. NBA 3.0 Baseline (Product-Based Approach)

The HCP universe for NBA 3.0 was defined using a **product-based** methodology.  
**Time frame adopted:** 2 years (May '23 to Apr '25)

### 1.1 Selection Criteria & Counts

| # | Criterion | Description | HCP Count | % of Universe |
|---|-----------|-------------|----------:|:-------------:|
| 1 | **SGLT2/GLP1 Prescribers (Decile 2+)** | All HCPs (decile 2 and above) with SGLT2/GLP1 prescriptions in the two years | 184,480 | 83.2% |
| 2 | **Kerendia Writers** | All HCPs prescribing Kerendia in complete history | 49,849 | 22.5% |
| 3 | **NEPH HCPs** | All Nephrologists | 15,209 | 6.9% |
| 4 | **Targeting & BPT HCPs** | All HCPs in BPT or Targeting List | 116,944 | 52.7% |
| | **Total HCP Universe** | Union of all criteria | **221,723** | — |

> *Overall SGLT2/GLP1 prescribing HCPs before decile filter: 648,778*  
> *Percentages represent each group's share of the total universe (221,723)*  
> *Among 117K Targeting and BPT HCPs, 93% were already captured using criteria 1 to 3 (16K explicitly added)*

---

## 2. NBA 3.1 Current Run (Product-Based, Updated Data)

Same methodology as NBA 3.0, run on refreshed data.

### 2.1 Selection Criteria & Counts

| # | Criterion | HCP Count | % of Universe |
|---|-----------|----------:|:-------------:|
| 1 | **SGLT2/GLP1 Prescribers (Decile 2+)** | 193,974 | 83.3% |
| 2 | **Kerendia Writers** (full history) | 77,972 | 33.5% |
| 3 | **NEPH HCPs** | 16,414 | 7.0% |
| 4 | **Targeting & BPT HCPs** | 78,389 | 33.6% |
| | **Total HCP Universe** | **232,965** | — |

> *Overall SGLT2/GLP1 prescribing HCPs before decile filter: 575,742*

### 2.2 NBA 3.0 → 3.1 Comparison

| Criterion | NBA 3.0 | NBA 3.1 | Delta | Notes |
|-----------|--------:|--------:|------:|-------|
| SGLT2/GLP1 (all) | 648,778 | 575,742 | -73,036 | Pool shrank but Decile 2+ grew |
| SGLT2/GLP1 (Decile 2+) | 184,480 | 193,974 | +9,494 | Higher-volume writers grew |
| Kerendia Writers | 49,849 | 77,972 | +28,123 | ~57% growth in Kerendia adoption |
| NEPH HCPs | 15,209 | 16,414 | +1,205 | Stable |
| Targeting & BPT | 116,944 | 78,389 | -38,555 | Call Plan / BPT list updated |
| **Total Universe** | **221,723** | **232,965** | **+11,242** | **+5.1% growth** |

**Key Observations:**
- Kerendia writers nearly doubled (~50K → ~78K), reflecting growing market adoption
- SGLT2/GLP1 Decile 2+ share held steady at ~83% of universe despite the total pool shrinking
- Targeting & BPT list shrank significantly — needs investigation into whether `CP_KER_HCP` source changed
- In NBA 3.1, Targeting and BPT use the identical underlying query, producing the same 78,389 HCPs

---

## 3. Paradigm Shift: Indication-Based Universe

### 3.1 Motivation

The NBA 3.0/3.1 product-based approach only captured HCPs prescribing **SGLT2/GLP1 drugs** — a proxy for treating T2D and CKD. This missed:
- HCPs treating these conditions with **other drug classes** (ACE, ARB, BB, Diuretics, sMRA, etc.)
- HCPs treating **Heart Failure (HF)** — a key Kerendia-adjacent indication
- HCPs treating **Type 1 Diabetes (T1D)** — a newly relevant population

New indication-enriched tables now allow us to **directly identify HCPs by the conditions they treat**, not just the products they prescribe.

### 3.2 Available Data Sources

All tables reside in **`ph-com-ai-us-prod-catalog-2553213839599380.pace_ker_in_house_schema`**

| Table | Rows | Patients | HCPs | Date Range | Grain |
|-------|-----:|:--------:|-----:|:----------:|-------|
| **lrx_nbrx** | 246M | — | 1,653,769 | Jul '21 – Sep '26 | Provider × Week × Product × Indication |
| **pt_lvl_nbrx** | 249M | 117.9M | 1,653,757 | Jul '21 – Sep '26 | Claim-level (NBRx only) |
| **pt_lvl_trx** | 4.8B | 152.1M | 1,972,490 | Jan '21 – Sep '26 | Claim-level (all TRx) |
| **indication_table** | 95.5M | 95.5M | — | — | Patient-level reference (1:1) |

### 3.3 Indication Classification

#### Indication Group Columns

Two indication group columns exist across the prescription tables (`lrx_nbrx`, `pt_lvl_nbrx`):

| Column | # Values | T1D Split? | Recommended? |
|--------|:--------:|:----------:|:------------:|
| `INDICATION_GROUP` | 8 | No — T1D patients lumped into T2D or OTHERS | No |
| `INDICATION_GROUP_APP1` | 16 | **Yes** — T1D separated into own combinations | **Yes** |

**`INDICATION_GROUP_APP1` values (16 combinations):**

| Pure Indications | 2-way Combinations | 3-way Combinations | 4-way |
|:-----------------|:-------------------|:-------------------|:------|
| T1D | T1D + T2D | T1D + T2D + CKD | T1D + T2D + CKD + HF |
| T2D | T1D + CKD | T1D + T2D + HF | |
| CKD | T1D + HF | T1D + CKD + HF | |
| HF | T2D + CKD | T2D + CKD + HF | |
| OTHERS | T2D + HF | | |
| | CKD + HF | | |

> **Recommendation:** Use `INDICATION_GROUP_APP1` — it provides T1D granularity essential for the 4-indication approach.

#### Three Flag Versions: ORIGINAL vs APP1 vs APP2

The `indication_table` contains three different versions of T1D/T2D flags, each using a different **T1D vs T2D disambiguation strategy**. CKD and HF flags are identical across all three versions — only T1D/T2D assignment differs.

| Version | Column Suffix | T1D Patients | T2D Patients | Dual T1D+T2D Handling |
|---------|:-------------|-------------:|-------------:|:----------------------|
| **ORIGINAL** | `_FLAG_ORIGINAL` | 3,619,864 | 68,438,026 | **No disambiguation** — both T1D and T2D can be flagged = 1 simultaneously |
| **APP1** | `_FLAG_APP1` | 2,083,252 | 67,334,183 | **Strict** — force-assigns each dual-flagged patient to either T1D **or** T2D, never both |
| **APP2** | `_FLAG_APP2` | 2,737,593 | 67,511,192 | **Moderate** — more permissive than APP1; re-adds T1D for some patients APP1 had resolved to T2D-only |

Corresponding indication columns: `INDICATION_ORIGINAL`, `INDICATION_APP1`, `INDICATION_APP2`

**How the disambiguation flows (patient counts):**

```
  ORIGINAL (raw flags)          APP1 (strict)              APP2 (moderate)
  ┌───────────────────┐        ┌──────────────────┐       ┌──────────────────┐
  │ T1D+T2D: 1,536,612│───────▶│ Resolved to T2D  │──────▶│ 654K re-added    │
  │ patients (both=1) │        │ only: 882,271    │       │ back as T1D+T2D  │
  │                   │        │                  │       │                  │
  │                   │        │ Resolved to T1D  │       │ 177K re-added    │
  │                   │        │ only: rest       │       │ back as T1D+T2D  │
  └───────────────────┘        └──────────────────┘       └──────────────────┘
```

**Top ORIGINAL → APP1 reclassifications (2.6M patients affected):**

| ORIGINAL Label | APP1 Label | Patients | Change |
|:---------------|:-----------|:--------:|:-------|
| T1D + T2D | T1D | 586,006 | Kept as T1D, dropped T2D |
| T1D + T2D | T2D | 518,993 | Kept as T2D, dropped T1D |
| T1D + T2D + CKD | T2D + CKD | 470,016 | Dropped T1D |
| T1D + T2D + CKD + HF | T2D + CKD + HF | 444,789 | Dropped T1D |
| T1D + T2D + CKD | T1D + CKD | 291,065 | Dropped T2D |
| T1D + T2D + CKD + HF | T1D + CKD + HF | 185,276 | Dropped T2D |
| T1D + T2D + HF | T2D + HF | 102,814 | Dropped T1D |
| T1D + T2D + HF | T1D + HF | 41,496 | Dropped T2D |

**Top APP1 → APP2 relaxations (831K patients affected):**

| APP1 Label | APP2 Label | Patients | Change |
|:-----------|:-----------|:--------:|:-------|
| T2D + CKD + HF | T1D + T2D + CKD + HF | 210,395 | T1D re-added |
| T2D | T1D + T2D | 206,328 | T1D re-added |
| T2D + CKD | T1D + T2D + CKD | 189,614 | T1D re-added |
| T1D | T1D + T2D | 97,385 | T2D re-added |
| T2D + HF | T1D + T2D + HF | 48,004 | T1D re-added |
| T1D + CKD | T1D + T2D + CKD | 43,972 | T2D re-added |
| T1D + CKD + HF | T1D + T2D + CKD + HF | 26,652 | T2D re-added |
| T1D + HF | T1D + T2D + HF | 9,000 | T2D re-added |

> **Note:** The disambiguation likely uses `LATEST_ENDO_DX`, `T1D_DRUG_FLAG`, and `T2D_DRUG_FLAG` columns in the `indication_table`, but the source notebook that builds this table was not found in this workspace — it is likely maintained by the PACE team externally.

### 3.4 Indication Assignment Methods (indication_table)

The `indication_table` columns suggest multiple approaches are used to assign disease flags per patient. **These methods are inferred from column naming patterns** (e.g., `T1D_DX_MIN_DATE` → DX approach, `CKD_LAB_MIN_DATE` → Lab approach). The source notebook for this table was not found in the workspace.

| Approach | Inferred From Column | T1D/T2D | CKD | HF |
|----------|:--------------------|:-------:|:---:|:--:|
| **DX** | `*_DX_MIN_DATE` | ✓ | ✓ | ✓ |
| **Proxy** | `*_PROXY_MIN_DATE` | ✓ | ✓ | ✓ |
| **Lab** | `CKD_LAB_MIN_DATE` | — | ✓ | — |
| **DX + Proxy** | `CKD_DX_PROXY_MIN_DATE` | — | ✓ | — |
| **Drug Flag** | `T1D_DRUG_FLAG`, `T2D_DRUG_FLAG` | ✓ | — | — |
| **Kerendia Proxy** | `HF_KER_PROXY_MIN_DATE` | — | — | ✓ |
| **Combined** | `*_MIN_DATE` | ✓ | ✓ | ✓ |

> **Caveat:** The exact logic behind each approach (DX codes used, proxy rules, lab thresholds) is unknown without the source pipeline. The `*_MIN_DATE` columns represent the earliest date across all approaches for that indication.

**Patient-Level Indication Prevalence (indication_table, 95.5M patients):**

| Indication | ORIGINAL | APP1 | APP2 |
|:-----------|:--------:|:----:|:----:|
| T2D | 68,438,026 (71.6%) | 67,334,183 (70.5%) | 67,511,192 (70.7%) |
| CKD | 41,965,784 (43.9%) | 41,965,784 (43.9%) | 41,965,784 (43.9%) |
| HF | 21,213,328 (22.2%) | 21,213,328 (22.2%) | 21,213,328 (22.2%) |
| T1D | 3,619,864 (3.8%) | 2,083,252 (2.2%) | 2,737,593 (2.9%) |

> CKD and HF counts are identical across all three versions — only T1D/T2D assignment varies.

---

## 4. Indication-Based EDA Results

**Analysis Window:** 2 years (Oct '24 – Sep '26)  
**Source Table:** `lrx_nbrx` using `INDICATION_GROUP_APP1`

### 4.1 HCPs by Indication Group

| Indication Group | Distinct HCPs | Total NBRx |
|:-----------------|:-------------:|-----------:|
| OTHERS | 1,240,418 | 43,710,195 |
| T2D | 945,932 | 30,564,757 |
| T2D + CKD | 601,309 | 8,820,152 |
| CKD | 592,302 | 5,084,919 |
| T2D + CKD + HF | 499,086 | 5,039,783 |
| HF | 482,267 | 3,906,317 |
| T2D + HF | 459,771 | 3,297,644 |
| CKD + HF | 393,347 | 2,399,532 |
| T1D | 184,079 | 458,065 |
| T1D + CKD | 97,326 | 177,527 |
| T1D + CKD + HF | 64,764 | 104,205 |
| T1D + HF | 25,216 | 36,879 |
| T1D + T2D | 14,466 | 21,695 |
| T1D + T2D + CKD | 5,667 | 7,712 |
| T1D + T2D + CKD + HF | 2,339 | 3,023 |
| T1D + T2D + HF | 1,610 | 2,235 |

### 4.2 HCPs Treating Each Target Indication (Any Combination)

| Indication | HCPs | % of All HCPs in Table (1.35M) |
|:-----------|------:|:------------------------------:|
| **T2D** | 1,019,894 | 75.3% |
| **CKD** | 799,068 | 59.0% |
| **HF** | 696,373 | 51.5% |
| **T1D** | 280,902 | 20.8% |
| **Union (any T1D/T2D/CKD/HF)** | **1,078,405** | **79.7%** |
| OTHERS only | 275,042 | 20.3% |

### 4.3 Cross-Indication Overlap Among HCPs

| Overlap | HCP Count |
|:--------|----------:|
| T2D ∩ CKD | 760,527 |
| T2D ∩ HF | 667,553 |
| CKD ∩ HF | 639,342 |
| **T2D ∩ CKD ∩ HF** | **626,632** |

> 626K HCPs treat patients across all three of T2D + CKD + HF — the core Kerendia-relevant population. This represents 58% of all indication-tagged HCPs.

### 4.4 Top Drug Classes by Indication

All counts below use `INDICATION_GROUP_APP1` containing the target indication (i.e., any combination that includes it).

#### T2D — HCPs treating Type 2 Diabetes (1,019,894 total)

| Product Class | HCPs | Total NBRx |
|:--------------|------:|-----------:|
| OTHERS | 792,935 | 11,906,348 |
| BB | 636,037 | 4,798,549 |
| DIURETICS | 599,910 | 4,573,101 |
| ARB | 510,180 | 4,600,873 |
| ACE | 476,577 | 3,005,568 |
| SGLT2 | 452,092 | 5,452,303 |
| GLP1 | 423,012 | 11,013,109 |
| sMRA | 406,922 | 1,730,846 |
| ENTRESTO GENERICS | 101,538 | 267,553 |
| ENTRESTO BRAND | 95,402 | 238,346 |
| **KERENDIA** | **35,798** | **165,152** |

> GLP1 dominates T2D by NBRx volume (11M) despite fewer HCPs than OTHERS/BB. SGLT2 is 6th by HCPs but 2nd by NBRx.

#### CKD — HCPs treating Chronic Kidney Disease (799,068 total)

| Product Class | HCPs | Total NBRx |
|:--------------|------:|-----------:|
| OTHERS | 536,107 | 3,649,164 |
| DIURETICS | 519,141 | 3,357,323 |
| BB | 501,849 | 3,054,186 |
| ARB | 421,848 | 2,660,187 |
| SGLT2 | 367,694 | 2,626,538 |
| ACE | 353,667 | 1,316,686 |
| GLP1 | 317,089 | 3,275,411 |
| sMRA | 303,004 | 1,129,944 |
| ENTRESTO GENERICS | 90,422 | 228,433 |
| ENTRESTO BRAND | 83,123 | 193,513 |
| **KERENDIA** | **32,569** | **140,978** |

> CKD prescribing is more evenly distributed across drug classes than T2D. Diuretics and BB are dominant — these HCP pools were entirely missed by the old SGLT2/GLP1-only approach.

#### HF — HCPs treating Heart Failure (696,373 total)

| Product Class | HCPs | Total NBRx |
|:--------------|------:|-----------:|
| DIURETICS | 479,967 | 2,719,310 |
| BB | 430,402 | 2,343,685 |
| OTHERS | 421,827 | 1,698,413 |
| SGLT2 | 352,337 | 1,956,064 |
| ARB | 342,229 | 1,381,583 |
| sMRA | 311,058 | 1,494,008 |
| GLP1 | 266,972 | 1,430,758 |
| ACE | 252,242 | 592,751 |
| ENTRESTO GENERICS | 153,255 | 589,057 |
| ENTRESTO BRAND | 143,401 | 517,959 |
| **KERENDIA** | **21,071** | **64,274** |

> HF is dominated by Diuretics and BB — classic heart failure drug classes. SGLT2 is already 4th (352K HCPs), showing the overlap between HF and metabolic prescribing. Entresto (brand + generics) together reach ~154K HCPs — a distinctly HF-focused drug class. sMRA writers (311K) represent a Kerendia-adjacent competitive pool.

#### T1D — HCPs treating Type 1 Diabetes (280,902 total)

| Product Class | HCPs | Total NBRx |
|:--------------|------:|-----------:|
| OTHERS | 106,886 | 245,179 |
| BB | 90,926 | 115,719 |
| DIURETICS | 76,017 | 94,964 |
| ARB | 70,967 | 94,879 |
| ACE | 59,750 | 80,848 |
| GLP1 | 40,953 | 104,484 |
| sMRA | 29,850 | 34,851 |
| SGLT2 | 21,909 | 28,459 |
| ENTRESTO GENERICS | 4,253 | 4,516 |
| ENTRESTO BRAND | 3,787 | 3,989 |
| **KERENDIA** | **2,681** | **3,356** |

> T1D is the smallest pool. BB, DIURETICS, and ARB dominate — these are likely managing comorbid hypertension/cardiovascular risk in T1D patients. GLP1 appears for 41K HCPs despite not being a traditional T1D drug, reflecting off-label or dual-diagnosis use. SGLT2 and KERENDIA are minimal.

#### Key Insight Across All Indications

> The old product-based approach (SGLT2 + GLP1 only) captured at most **452K T2D HCPs** and **352K HF HCPs** via those two drug classes. The indication-based approach reveals that **BB, Diuretics, ARB, ACE, and sMRA** each contribute 250K–640K HCPs per indication — large populations entirely invisible to the product-based filter.

### 4.5 Kerendia Writer Indication Profile

**Total Kerendia NBRx writers in 2-year window: 39,704**

| Indication Group | HCPs | NBRx | % of Kerendia Writers |
|:-----------------|-----:|-----:|:---------------------:|
| T2D + CKD | 22,586 | 82,412 | 56.9% |
| T2D + CKD + HF | 16,789 | 43,722 | 42.3% |
| T2D | 13,583 | 30,800 | 34.2% |
| OTHERS | 4,703 | 7,386 | 11.8% |
| T2D + HF | 4,678 | 8,103 | 11.8% |
| CKD | 4,015 | 6,224 | 10.1% |
| CKD + HF | 3,523 | 5,940 | 8.9% |
| HF | 2,836 | 5,607 | 7.1% |
| T1D + CKD | 1,556 | 1,837 | 3.9% |
| T1D + CKD + HF | 717 | 773 | 1.8% |
| T1D | 456 | 520 | 1.1% |
| T1D + HF | 107 | 111 | 0.3% |

> **99.9%** of Kerendia writers (39,657 of 39,704) are captured by the indication-based approach.  
> Only **47** Kerendia writers fall exclusively in OTHERS.

### 4.6 Specialty-Based HCP Analysis

The original notebook only included **Nephrologists (NEPH)** via a complex Provider Dimension → NPI → MDM → Specialty mapping chain. The `lrx_nbrx` table already has a `SPECIALTY_GROUP` column, enabling direct specialty identification — and expanding to additional relevant specialties.

#### All Specialty Groups in `lrx_nbrx`

| Specialty | Code | HCPs | Total NBRx | Kerendia Writers | Kerendia % |
|:----------|:-----|------:|-----------:|-----------------:|:----------:|
| Primary Care Physicians | `PCP` | 721,427 | 77,479,461 | 24,053 | 3.3% |
| Other Specialties | `OTHERS` | 543,876 | 7,879,141 | — | — |
| Cardiologists | `CARD` | 51,622 | 12,279,727 | 5,102 | 9.9% |
| Nephrologists | `NEPH` | 15,035 | 2,087,334 | 7,479 | 49.7% |
| Endocrinologists | `ENDO` | 13,360 | 3,584,796 | 2,593 | 19.4% |
| Hospitalists | `HOSPITALIST` | 7,395 | 147,114 | 1 | 0.0% |
| Hospital-based Specialists | `HOS` | 731 | 177,067 | 386 | 52.8% |

> `HOS` and `HOSPITALIST` have **zero provider overlap** — they are entirely distinct populations. `HOS` (731 HCPs) has the highest Kerendia writing rate (52.8%), suggesting hospital-based subspecialists.

#### Indication Coverage by Specialty

| Specialty | HCPs | % treating T2D | % treating CKD | % treating HF | % treating T1D |
|:----------|------:|:--------------:|:--------------:|:-------------:|:--------------:|
| **NEPH** | 15,035 | 95.2% | 95.3% | 91.0% | 66.3% |
| **CARD** | 51,622 | 94.5% | 92.3% | 92.7% | 50.0% |
| **ENDO** | 13,360 | 96.0% | 91.7% | 87.3% | 81.5% |
| **PCP** | 721,427 | 87.8% | 75.5% | 68.4% | 27.9% |
| **HOSPITALIST** | 7,395 | 72.9% | 61.7% | 60.4% | 14.5% |
| **HOS** | 731 | 99.2% | 98.6% | 97.7% | 64.7% |

**Key observations:**
- **NEPH, CARD, ENDO** are highly concentrated in all 4 indications (87–96%)
- **PCP** is the largest pool by far (721K) with broad but shallower indication coverage
- **ENDO** has the highest T1D involvement (81.5%) — naturally, as endocrinologists manage diabetes
- **CARD** has the highest HF involvement (92.7%) and is 3.4× larger than NEPH
- **HOSPITALIST** has the lowest indication coverage (~60–73%) and almost no Kerendia writing

#### Overlap with Indication-Based Criterion 1

How many of these specialty HCPs are **already captured** by the indication criterion (`INDICATION_GROUP_APP1 != 'OTHERS'`)?

| Specialty | Total HCPs | Already in Indication Set | Net New Adds | % Already Captured |
|:----------|:----------:|:-------------------------:|:------------:|:------------------:|
| **NEPH** | 15,035 | 14,612 | 423 | 97.2% |
| **CARD** | 51,622 | 49,907 | 1,715 | 96.7% |
| **ENDO** | 13,360 | 13,001 | 359 | 97.3% |
| **PCP** | 721,427 | 654,997 | 66,430 | 90.8% |
| **HOSPITALIST** | 7,395 | 6,054 | 1,341 | 81.9% |
| **Combined** | **808,839** | **738,571** | **70,268** | **91.3%** |

> **91.3%** of target specialty HCPs are already in the indication set. The specialty criterion would explicitly add **70,268 net new HCPs** — mostly PCPs (66K) who prescribe only for OTHERS indications but are clinically relevant by virtue of their specialty.

#### Simplification Opportunity

The original notebook derived specialty via a 4-table join chain:
```
STG_CAR_IQV_LAAD_DIM_PRVDR → NPI XREF → MAP_CUSTOMER_XREF → MDM_STG_HCP_PRFL → specialty CSV
```

Since `lrx_nbrx` already has `SPECIALTY_GROUP` at the provider level, the new pipeline can source specialty **directly** — eliminating the complex mapping chain entirely.

---

## 5. Product-Based vs. Indication-Based Comparison

### 5.1 Head-to-Head (Criterion 1 Only)

| Metric | Product-Based (SGLT2/GLP1) | Indication-Based (T1D/T2D/CKD/HF) |
|:-------|---------------------------:|-----------------------------------:|
| Total HCPs in scope | 604,603 | 1,078,405 |
| Overlap | 597,054 | 597,054 |
| Unique to this approach | 7,549 | 481,351 |
| Kerendia writer coverage | — | 99.9% |

```
                Product-Based           Indication-Based
                ┌──────────┐            ┌──────────────────────┐
                │          │            │                      │
                │  7,549   │  597,054   │      481,351         │
                │  (only   │  (overlap) │      (new HCPs       │
                │  SGLT2/  │            │      from ACE, ARB,  │
                │  GLP1)   │            │      BB, Diuretics,  │
                │          │            │      sMRA, etc.)      │
                └──────────┘            └──────────────────────┘
                  604,603                    1,078,405
```

**Key Insight:** The indication-based approach captures **98.8%** of the old SGLT2/GLP1 HCPs while adding **481K new HCPs** who treat T1D/T2D/CKD/HF with non-SGLT2/GLP1 drug classes. The 7,549 SGLT2/GLP1 HCPs not in the indication set are those whose patients have only "OTHERS" indications.

### 5.2 Recommended Table for Universe Building

| Purpose | Recommended Table | Why |
|:--------|:------------------|:----|
| **HCP identification (Criterion 1)** | `lrx_nbrx` | Already at Provider × Indication grain; most efficient for HCP-level aggregation |
| **Decile calculation** | `lrx_nbrx` | Sum NBRX per PROVIDER_ID for TRx-based deciling |
| **Patient-level deep dives** | `pt_lvl_trx` | 4.8B rows with disease flags for granular patient analysis |
| **Indication reference/enrichment** | `indication_table` | Gold-standard patient→indication mapping with diagnosis dates |
| **NBRx-specific analysis** | `pt_lvl_nbrx` | Claim-level new-to-brand data with indication |

---

## 6. Proposed NBA 3.1 Updated HCP Universe

### 6.1 New Selection Criteria

| # | Criterion | Source | Description |
|---|-----------|--------|-------------|
| 1 | **Indication-Based HCPs (Decile 2+)** | `lrx_nbrx` | All HCPs prescribing to T1D/T2D/CKD/HF patients (`INDICATION_GROUP_APP1 != 'OTHERS'`), decile 2 and above by total NBRx |
| 2 | **Kerendia Writers** | `lrx_nbrx` | All HCPs prescribing Kerendia (`PRODUCT_CLASS = 'KERENDIA'`) in complete history |
| 3 | **Specialty HCPs** | `lrx_nbrx` (`SPECIALTY_GROUP`) | All NEPH, CARD, ENDO, PCP, and HOSPITALIST HCPs — expanded from NEPH-only; sourced directly from `lrx_nbrx` instead of the MDM chain |
| 4 | **Targeting & BPT HCPs** | `CP_KER_HCP` | All HCPs in BPT or Targeting List (unchanged) |

### 6.2 Enhanced Output Schema

The new universe output should include **indication-level flags** per HCP:

| Column | Type | Description |
|:-------|:-----|:------------|
| `PROVIDER_ID` | string | Unique HCP identifier |
| `T1D_FLAG` | int | 1 if HCP treats T1D patients |
| `T2D_FLAG` | int | 1 if HCP treats T2D patients |
| `CKD_FLAG` | int | 1 if HCP treats CKD patients |
| `HF_FLAG` | int | 1 if HCP treats HF patients |
| `KERENDIA_FLAG` | int | 1 if HCP prescribes Kerendia |
| `NEPH_FLAG` | int | 1 if HCP is a Nephrologist |
| `CARD_FLAG` | int | 1 if HCP is a Cardiologist |
| `ENDO_FLAG` | int | 1 if HCP is an Endocrinologist |
| `PCP_FLAG` | int | 1 if HCP is a Primary Care Physician |
| `HOSPITALIST_FLAG` | int | 1 if HCP is a Hospitalist |
| `TARGETING_HCP_FLAG` | int | 1 if HCP is in Targeting list |
| `BPT_HCP_FLAG` | int | 1 if HCP is in BPT list |
| `INDICATION_DECILE` | int | NBRx-based decile rank (1–10) |
| `PULL_DT` | date | Data pull date |

### 6.3 Expected Impact

| | NBA 3.0 | NBA 3.1 (Product) | NBA 3.1 (Indication) |
|:--|--------:|------------------:|---------------------:|
| Criterion 1 scope | SGLT2/GLP1 only | SGLT2/GLP1 only | All drug classes for T1D/T2D/CKD/HF |
| Criterion 1 pre-decile | 648,778 | 575,742 | ~1,078,405 |
| Kerendia writer coverage | ✓ | ✓ | ✓ (99.9%) |
| Indications covered | T2D, CKD (implicit) | T2D, CKD (implicit) | **T1D, T2D, CKD, HF (explicit)** |
| Per-HCP indication flags | No | No | **Yes** |

> **Note:** Final universe size will depend on the decile cutoff applied. The indication-based Criterion 1 pool (~1.08M) is ~1.9× larger than the product-based pool (~576K), so the total universe will grow significantly.

---

## 7. v1 vs v2 Universe Overlap Analysis

**Implementation notebook:** `02_HCP_Universe_Identification_v2`  
**Lookback window:** Oct '24 – Sep '26  
**Output path:** `kerendia_nba_3_hcp_universe_v2` (Delta)  
**Date:** October 12, 2026

### 7.1 Headline Comparison

| Metric | Count |
|:-------|------:|
| v1 Universe (product-based) | 232,965 |
| v2 Universe (indication-based) | 1,086,478 |
| Overlap (in both) | 231,511 |
| v1 only (dropped in v2) | 1,454 (0.6% of v1) |
| v2 only (new in v2) | 854,967 (78.7% of v2) |
| v1 retention in v2 | 99.4% |
| v2 growth over v1 | +366.4% |

```
  v1 Universe          v2 Universe
  ┌──────────┐    ┌──────────────────────────────┐
  │  1,454   │    │        854,967               │
  │ (v1-only │    │      (v2-only HCPs,          │
  │  dropped) │    │       78.7% of v2)           │
  ├──────────┼────┤                             │
  │  231,511      │                             │
  │  (overlap,    │                             │
  │   99.4% of v1)│                             │
  └──────────┘    └──────────────────────────────┘
   232,965                    1,086,478
```

**Key takeaway:** v2 retains 99.4% of v1 while growing 4.7×. The 1,454 dropped HCPs are immaterial and well-explained (see Section 7.2).

---

### 7.2 v1-Only HCPs: Why 1,454 Were Dropped

#### v1 Criterion Flags for Dropped HCPs

| v1 Flag | Count |
|:--------|------:|
| NEPH_FLAG | 1,118 |
| KERENDIA_FLAG | 346 |
| SGLT2_GLP1_FLAG | 0 |
| TARGETING_HCP_FLAG | 0 |
| BPT_HCP_FLAG | 0 |

> All 1,454 dropped HCPs qualified via NEPH (1,118) or Kerendia (346) in v1. **Zero** were lost from SGLT2/GLP1, Targeting, or BPT.

#### Root Cause Categorization

| Drop Reason | HCPs | % of 1,454 |
|:------------|-----:|:----------:|
| In lrx_nbrx but outside lookback window | 1,349 | 92.8% |
| Not in lrx_nbrx at all | 84 | 5.8% |
| Only OTHERS indications & no target specialty | 11 | 0.8% |
| Indication HCP but Decile 1 (low volume) | 5 | 0.3% |
| Decile 2+ indication HCP — edge case | 5 | 0.3% |
| **Total** | **1,454** | **100%** |

#### Detailed Findings

- **92.8% (1,349):** HCPs with NEPH or Kerendia activity in v1's data source (`STG_CAR_IQV_LAAD_FCT_RX`) but zero `lrx_nbrx` activity in the current 2-year lookback window. These are dormant HCPs who stopped prescribing — correctly excluded from v2.
- **5.8% (84):** HCPs not found in `lrx_nbrx` at all. These came from v1's MDM specialty chain or the old Snowflake RX table with provider IDs that don't map to the new `lrx_nbrx` source.
- **1.6% (21):** HCPs active in the window but missed by v2: 11 have only OTHERS indications (correctly excluded), 5 are Decile 1 low-volume (correctly filtered), 5 are edge cases with Decile 2+ that should theoretically be in v2.
- **0% lost from SGLT2/GLP1 or Targeting/BPT** — the product-based criterion and targeting list are fully preserved in v2.

> **Conclusion:** The drops are driven entirely by the source table change (v1: `STG_CAR_IQV_LAAD_FCT_RX` + MDM chain → v2: `lrx_nbrx`) and the lookback window. No methodology gaps in v2 are responsible.

---

### 7.3 v2-Only HCPs: 854,967 Net-New HCPs

#### By Specialty

| Specialty | v2-only | % of v2-only | v2 Total | % that are new |
|:----------|--------:|:------------:|:--------:|:-------------:|
| PCP | 540,865 | 63.3% | 722,285 | 74.9% |
| CARD | 28,794 | 3.4% | 51,666 | 55.7% |
| HOSPITALIST | 7,411 | 0.9% | 7,432 | 99.7% |
| ENDO | 3,518 | 0.4% | 13,371 | 26.3% |
| NEPH | 23 | 0.0% | 15,048 | 0.2% |
| (no target spec) | 274,356 | 32.1% | — | — |

> **PCP** is the largest driver (541K new, 75% of all PCPs in v2). **HOSPITALIST** is almost entirely new (99.7%) since v1 only had NEPH. **NEPH** barely changes — v1 already captured nearly all.

#### By Entry Criterion (non-exclusive)

| Criterion | v2-only | % of v2-only |
|:----------|--------:|:------------:|
| Indication HCP (Decile 2+) | 744,572 | 87.1% |
| Specialty HCP | 580,611 | 67.9% |
| Kerendia | 216 | 0.0% |
| Targeting / BPT | 0 | 0.0% |

#### Top Criterion Combinations

| Indication | Specialty | Kerendia | n_hcps | % of v2-only |
|:----------:|:---------:|:--------:|------:|:------------:|
| ✓ | ✓ | ✗ | 470,023 | 55.0% |
| ✓ | ✗ | ✗ | 274,335 | 32.1% |
| ✗ | ✓ | ✗ | 110,393 | 12.9% |
| ✓ | ✓ | ✓ | 194 | 0.0% |
| ✓ | ✗ | ✓ | 20 | 0.0% |
| ✗ | ✓ | ✓ | 1 | 0.0% |
| ✗ | ✗ | ✓ | 1 | 0.0% |

> 55% entered via both Indication AND Specialty criteria. 32% entered via Indication-only (indication-relevant HCPs not in any target specialty — see Section 7.4). 13% entered via Specialty-only (target specialty but Decile 1 or only OTHERS indications).

#### By Indication

| Indication | v2-only | % of v2-only | % new in v2 total |
|:----------|--------:|:------------:|:----------------:|
| T2D | 712,861 | 83.4% | 75.7% |
| CKD | 541,325 | 63.3% | 70.4% |
| HF | 453,072 | 53.0% | 66.8% |
| T1D | 134,502 | 15.7% | 48.1% |
| (no indication) | 110,395 | 12.9% | — |

#### Decile Distribution (Indication HCPs only)

| Decile | v2-only HCPs |
|:------:|------------:|
| 2 | 107,377 |
| 3 | 107,203 |
| 4 | 106,853 |
| 5 | 106,317 |
| 6 | 104,861 |
| 7 | 99,364 |
| 8 | 74,789 |
| 9 | 30,843 |
| 10 | 6,965 |

> Skews heavily toward lower deciles (2–6 each have ~105K), tapering at higher deciles. These are moderate-to-lower-volume prescribers missed by the old product-based SGLT2/GLP1 filter.

### 7.4 Product Group Analysis of v2-only HCPs

#### Overall Product Group Distribution (Top 20)

| Product Group | HCPs | Total NBRx | Kerendia HCPs |
|:-------------|------:|-----------:|--------------:|
| OTHERS | 669,488 | 8,016,155 | 204 |
| BB | 619,593 | 7,673,764 | 189 |
| DIURETICS | 545,972 | 4,463,719 | 193 |
| ARB | 446,792 | 3,570,047 | 198 |
| ACE | 432,665 | 2,570,788 | 170 |
| SPIRONOLACTONE | 356,298 | 3,001,793 | 171 |
| JARDIANCE | 215,771 | 682,532 | 170 |
| OZEMPIC | 145,348 | 445,213 | 97 |
| MOUNJARO | 137,146 | 638,552 | 73 |
| ZEPBOUND | 103,232 | 556,907 | 49 |
| FARXIGA BRAND | 96,283 | 207,483 | 88 |
| FARXIGA GENERIC | 90,620 | 179,738 | 125 |
| WEGOVY | 90,319 | 318,087 | 48 |
| ENTRESTO GENERIC | 83,672 | 209,586 | 104 |
| ENTRESTO BRAND | 76,131 | 174,172 | 67 |
| TRULICITY | 52,199 | 93,448 | 26 |
| RYBELSUS | 31,528 | 49,222 | 22 |
| EPLERENONE | 22,172 | 37,134 | 33 |
| LIRAGLUTIDE | 20,168 | 30,872 | 14 |
| KERENDIA | 216 | 222 | 216 |

> **All 854,967 v2-only HCPs** have lrx_window activity. The top drug groups are cardiovascular/renal: BB (620K), DIURETICS (546K), ARB (447K), ACE (433K), and SPIRONOLACTONE (356K). SGLT2 products (JARDIANCE 216K, FARXIGA 187K) and GLP1 products (OZEMPIC 145K, MOUNJARO 137K, ZEPBOUND 103K) appear mid-range. Only 216 v2-only HCPs prescribe Kerendia directly.

#### Product Group by Criterion Cohort

**Cohort A: Indication + Specialty (470,217 HCPs)** — HCPs qualifying under both criteria

| Product Group | HCPs | % of cohort |
|:-------------|------:|:-----------:|
| OTHERS | 421,788 | 89.7% |
| BB | 388,904 | 82.7% |
| DIURETICS | 376,677 | 80.1% |
| ARB | 337,448 | 71.8% |
| ACE | 321,601 | 68.4% |
| SPIRONOLACTONE | 256,462 | 54.5% |
| JARDIANCE | 193,834 | 41.2% |
| OZEMPIC | 128,743 | 27.4% |
| MOUNJARO | 118,836 | 25.3% |
| FARXIGA BRAND | 89,150 | 19.0% |

> This cohort has the highest SGLT2/GLP1 penetration — 41% prescribe JARDIANCE and 27% prescribe OZEMPIC, indicating these are clinically active HCPs treating the right patient populations with relevant drugs.

**Cohort B: Indication-only (274,355 HCPs)** — No target specialty, entered via indication decile only

| Product Group | HCPs | % of cohort |
|:-------------|------:|:-----------:|
| OTHERS | 201,587 | 73.5% |
| BB | 190,254 | 69.3% |
| DIURETICS | 137,368 | 50.1% |
| ACE | 88,244 | 32.2% |
| SPIRONOLACTONE | 87,727 | 32.0% |
| ARB | 87,349 | 31.8% |
| JARDIANCE | 20,337 | 7.4% |
| MOUNJARO | 17,312 | 6.3% |
| ZEPBOUND | 14,972 | 5.5% |
| OZEMPIC | 14,897 | 5.4% |

> Low SGLT2/GLP1 penetration (5–7%) confirms this is a cardiovascular/renal prescribing cohort with minimal metabolic drug involvement. Their BB/Diuretic/sMRA prescribing is clinically relevant to Kerendia's mechanism but they are not traditional diabetes prescribers.

**Cohort C: Specialty-only (110,394 HCPs)** — Target specialty but Decile 1 or OTHERS-only indications

| Product Group | HCPs | % of cohort |
|:-------------|------:|:-----------:|
| OTHERS | 46,112 | 41.8% |
| BB | 40,435 | 36.6% |
| DIURETICS | 31,927 | 28.9% |
| ACE | 22,820 | 20.7% |
| ARB | 21,995 | 19.9% |
| SPIRONOLACTONE | 12,109 | 11.0% |
| ZEPBOUND | 2,146 | 1.9% |
| OZEMPIC | 1,708 | 1.5% |
| JARDIANCE | 1,600 | 1.4% |
| WEGOVY | 1,358 | 1.2% |

> Very low volume across all product groups — these HCPs have target specialties but minimal indication-relevant prescribing activity. Only 1.4% prescribe JARDIANCE and 1.5% prescribe OZEMPIC.

#### Key Insights

- The v2-only HCPs prescribe primarily **cardiovascular/renal drugs** (BB, DIURETICS, ARB, ACE, sMRA) — classes that were entirely invisible to v1's SGLT2/GLP1-only filter
- **SGLT2/GLP1 penetration varies dramatically by cohort**: 41% in Indication+Specialty vs 6% in Indication-only vs 1.5% in Specialty-only
- **Kerendia overlap is minimal**: only 216 v2-only HCPs prescribe Kerendia (0.025%), confirming these are mostly non-Kerendia prescribers captured by the expanded criteria
- The high SPIRONOLACTONE (356K) and EPLERENONE (22K) usage is notable — these are sMRA drugs that compete with Kerendia, representing a large competitive landscape

---

### 7.5 Deep Dive: 274K No-Specialty Indication HCPs

These HCPs entered v2 via Criterion 1 (Indication Decile 2+) but have no target specialty — their `SPECIALTY_GROUP` in `lrx_nbrx` is `OTHERS` (274,354) or `HOS` (1). They represent 32.1% of all v2-only HCPs.

#### Indication Mix

| Indication | Count | % of 274K |
|:----------|------:|:---------:|
| T2D | 256,102 | 93.3% |
| CKD | 156,726 | 57.1% |
| HF | 113,550 | 41.4% |
| T1D | 29,677 | 10.8% |

Top combinations: T2D-only (87.5K), T2D+CKD+HF (73.4K), T2D+CKD (51.8K) — heavily skewed toward T2D.

#### Decile Distribution

| Decile | HCPs |
|:------:|-----:|
| 2 | 63,650 |
| 3 | 57,810 |
| 4 | 52,297 |
| 5 | 44,771 |
| 6 | 33,336 |
| 7 | 16,938 |
| 8 | 4,490 |
| 9 | 858 |
| 10 | 205 |

> Concentrates in lower deciles — these are moderate-to-low-volume prescribers.

#### Drug Class Activity

| Product Class | HCPs | Total NBRx |
|:-------------|------:|-----------:|
| OTHERS | 201,587 | 1,645,495 |
| BB | 190,254 | 2,161,356 |
| DIURETICS | 137,368 | 682,274 |
| sMRA | 88,623 | 1,334,692 |
| ACE | 88,244 | 274,366 |
| ARB | 87,349 | 258,724 |
| GLP1 | 40,414 | 212,045 |
| SGLT2 | 29,977 | 60,377 |
| KERENDIA | 20 | 20 |

#### Key Characteristics

- **Kerendia adoption:** Only 20 writers (0.01%) — extremely low Kerendia penetration
- **Specialty:** All are `OTHERS` (unmapped specialties — likely psychiatrists, surgeons, urgent care, pain management, OB/GYN, etc.)
- **Prescribing pattern:** BB, DIURETICS, sMRA, ACE, ARB dominate — cardiovascular/renal drugs but not SGLT2/GLP1
- **Entry path:** Criterion 1 (Indication Decile 2+) only — no specialty or Kerendia contribution

#### Assessment

These 274K HCPs are a large but **low-priority expansion cohort**:
- They treat T2D/CKD/HF patients at moderate volumes but have virtually no Kerendia adoption
- They are not specialists in any Kerendia-relevant field
- If the universe needs tightening, this is the first group to consider filtering (e.g., restrict to Decile 4+, or require CKD+T2D co-indication, or exclude HCPs with no SGLT2/GLP1 or Kerendia prescribing history)
- Potential value: they represent future Kerendia expansion targets if their patient panels are clinically appropriate

---

### 7.6 Summary & Recommendations

| Question | Answer |
|:---------|:------|
| Does v2 lose any meaningful v1 HCPs? | No — 99.4% retention, 1,454 drops all explained by source change + dormant HCPs |
| Are Targeting/BPT HCPs fully preserved? | Yes — 0 lost from Targeting/BPT |
| Are SGLT2/GLP1 HCPs fully preserved? | Yes — 0 lost from SGLT2/GLP1 |
| What drives the 4.7× growth? | Indication-based Criterion 1 (745K new) + expanded specialties (581K new, mostly PCP) |
| Are there low-value cohorts in v2? | Yes — 274K no-specialty indication HCPs (0.01% Kerendia, lower deciles). Consider tightening if needed |
| What are the edge cases? | 5 HCPs with Decile 2+ indications that should be in v2 but aren't — investigate individually |

**Recommended next actions:**
- [ ] Decide whether to keep or tighten the 274K no-specialty cohort (e.g., add decile threshold or drug-class filter)
- [ ] Investigate the 5 edge-case HCPs individually
- [ ] Validate downstream model performance with v2 universe
- [ ] Consider adding HOS (731 HCPs, 52.8% Kerendia writers) to Criterion 3

---

## 8. Next Steps

- [x] Confirm lookback window for NBA 3.1 — **Oct '24 – Sep '26**
- [x] Decide on decile methodology — **Combined NBRx decile across all indication HCPs (ntile 10, ascending)**
- [x] Confirm indication column — **`INDICATION_GROUP_APP1`** (16 values, includes T1D)
- [x] Expand Criterion 3 from NEPH-only to NEPH + CARD + ENDO + PCP + HOSPITALIST — **Done**
- [x] Build the updated `02_HCP_Universe_Identification_v2` notebook — **Done**
- [x] Validate new universe against Kerendia writer and Targeting list coverage — **Done** (99.4% retention, 99.9% Kerendia coverage)
- [x] v1 vs v2 overlap analysis — **Done** (Section 7)
- [ ] Decide whether to include `HOS` (731 HCPs, 52.8% Kerendia writers) alongside HOSPITALIST
- [ ] Decide whether to tighten the 274K no-specialty indication HCP cohort
- [ ] Validate downstream model performance with v2 universe

---

*Generated by Genie Code — October 9, 2026. Updated October 12, 2026 with v1 vs v2 overlap analysis.*