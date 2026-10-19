# Kerendia NBA 3.1 — HCP Universe Construction

**Date:** October 19, 2026  
**Author:** Genie Code  
**Objective:** Build an HCP Universe (≤ 300K) that maximizes Kerendia writer coverage for NBA model scoring.

---

## 1. Business Context

Kerendia (finerenone) treats CKD associated with T2D. The HCP Universe identifies which providers are eligible for NBA model scoring. Three goals:

1. **Maximize writer capture** — cover as many of the 61,583 Kerendia writers as possible
2. **Stay within budget** — total universe ≤ 300,000 HCPs
3. **Be commercially relevant** — include HCPs who prescribe, treat, or are engaged with Kerendia

---

## 2. Data Sources

All data lives in catalog `ph-com-ai-us-prod-catalog-2553213839599380`.

| Source | Table / Path | Key Columns | Rows |
|:-------|:-------------|:------------|-----:|
| **Claims (C1)** | `pace_ker_in_house_schema.lrx_nbrx` | PROVIDER_ID, INDICATION_GROUP_APP1, PRODUCT_CLASS, NBRX, WEEK_ENDING_DATE, SPECIALTY_GROUP | ~247M (104M in 24-mo lookback) |
| **Kerendia Writers (C2)** | `/Volumes/.../kerendia_nbrx_from_raw_fct_rx` (Delta) | PROVIDER_ID, NBRX_KERENDIA_OVERALL, TRX_KERENDIA_OVERALL | 91,751 HCPs |
| **ID Mapping** | `kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING` | PROVIDER_ID, NPI_NUMBER, BH_ID | ~1.65M |
| **NBA 3.0 Baseline** | `/Volumes/.../kerendia_nba_3_hcp_model_base_hcp_universe_for_inference` (Delta) | PROVIDER_ID, KERENDIA_FLAG, SGLT2_GLP1_FLAG, NEPH_FLAG, TARGETING_HCP_FLAG | 232,965 HCPs |
| **Targeting (C4)** | Snowflake `PHCDW.PHCDW_TARGETING.CP_KER_HCP` | BH_ID (mapped to PROVIDER_ID) | ~78K HCPs |
| **Validation (M3)** | `kerendia_laad_based_lrx.kerendia_laad_based_lrx_v6` | PROVIDER_ID, PRODUCT_GROUP, NBRX, TRX, WEEK_ENDING_DATE | - |

---

## 3. Universe Criteria

The universe is built by **unioning** HCPs from 4 mandatory criteria (+ 1 optional):

### C1: Core Prescribers (Claims-Based)

Identify high-volume prescribers across indication × drug pool combinations:

* **4 Indications:** T2D, CKD, HF, T1D (from `INDICATION_GROUP_APP1`, use `.contains()`)
* **2 Drug Pools:** SGLT2/GLP1, ACE/ARB (from `PRODUCT_CLASS`)
* **8 Sets** from the 4×2 matrix
* **Method:** For each set, aggregate `sum(NBRX)` per HCP over 24-month lookback, assign cumulative volume-based deciles (1–10), select HCPs at D2+ (top 90% of volume)
* **Core Sets:** Set 1 (T2D×SGLT2/GLP1) ∪ Set 3 (CKD×SGLT2/GLP1) — most aligned with Kerendia's profile

### C2: Kerendia Writers (Mandatory)

All HCPs with at least one Kerendia NBRX (all claim types: PD+RV+RJ, full history since July 2021).

* **Count:** 61,583 HCPs — guarantees 100% writer capture
* **Source:** Pre-computed Delta from `Kerendia_NBRX_From_Raw_FCT_RX` notebook

### C3: Specialists (Mandatory)

Clinically relevant specialists regardless of prescribing volume:

* **NEPH:** ~15K nephrologists
* **CARD:** ~52K cardiologists
* **Total:** ~67K unique specialists

### C4: Targeting / BPT (Additive)

HCPs on the commercial targeting list from Snowflake `CP_KER_HCP`.

* **Count:** ~78K HCPs
* Requires BH_ID → PROVIDER_ID mapping

### C5: Called HCPs (Optional)

HCPs called/detailed for Kerendia since 2023. Only add if size budget allows.

---

## 4. Approach: Indication × Drug Pool Deciling

### 4.1 The 8-Set Matrix

|  | SGLT2/GLP1 | ACE/ARB |
|:---|:---:|:---:|
| **T2D** | Set 1 | Set 2 |
| **CKD** | Set 3 | Set 4 |
| **HF** | Set 5 | Set 6 |
| **T1D** | Set 7 | Set 8 |

### 4.2 Cumulative Volume-Based Deciling

For each set:
1. Filter `lrx_nbrx` to the lookback window + indication + drug pool
2. Aggregate `sum(NBRX)` per `PROVIDER_ID`
3. Order by ascending NBRX (with PROVIDER_ID tiebreaker)
4. Compute cumulative NBRX; assign decile = `min(floor(cum_nbrx / (total_nbrx/10)) + 1, 10)`
5. D1 = lowest-volume 10% of prescriptions, D10 = highest-volume 10%

### 4.3 Core Selection Strategy

Use Set 1 ∪ Set 3 at D2+ as the core:
* T2D and CKD are Kerendia's primary indications
* SGLT2/GLP1 is the most aligned drug pool
* D2+ captures ~80% of Kerendia writers in ~243K HCPs
* Additional sets add diminishing returns (148K HCPs for only 6K more writers)

---

## 5. Validation Metrics

| Metric | Definition | Baseline |
|:-------|:-----------|:--------|
| **M1** | NBA 3.0 KERENDIA_FLAG = 1 | 77,972 |
| **M2** | `lrx_nbrx` paid NBRX > 0 (24-mo lookback) | ~40,122 |
| **M3** | LAAD V6 TRX > 0 (24-mo lookback) | ~67,835 |
| **M4** | STG_CAR_IQV_LAAD_FCT_RX paid TRX (24-mo, Snowflake) | ~67,796 |
| **NBA 3.0 overlap** | % of 232,965 NBA 3.0 HCPs in new universe | target ≥ 90% |

---

## 6. Hotspot Analysis

After building the universe, profile Kerendia writers NOT captured by C1 alone:

1. **Set membership** — D1 of core sets vs. non-core sets vs. not in any set
2. **Specialty** — PCP, NEPH, CARD, ENDO, etc.
3. **Claim type** — paid vs. non-paid (RV/RJ) only
4. **Kerendia volume** — single-script vs. repeat writers
5. **Recovery path** — which criterion (C2, C3, C4) captures them

---

## 7. Actual Results (This Build)

| Criterion | Count |
|:----------|------:|
| C1 (Core D2+, Set1 ∪ Set3) | 242,976 |
| C2 (Kerendia Writers) | 61,583 |
| C3 (NEPH + CARD) | 66,780 |
| C4 (Targeting/BPT) | 78,798 |
| **Total (C1+C2+C3+C4)** | **294,505** |
| NBA 3.0 overlap | 220,031 (94.4%) |
| Budget check | **PASS** (≤ 300K) |

**Incremental Buildup:**

| Step | Total | Incremental |
|:-----|------:|:----------:|
| C1 Core (Set1∪Set3, D2+) | 242,976 | — |
| + C2 Kerendia Writers | 255,052 | +12,076 |
| + C3 NEPH | 259,596 | +4,544 |
| + C3 CARD | 291,630 | +32,034 |
| + C4 Targeting/BPT | 294,505 | +2,875 |

**Validation Metrics:**

| Metric | Baseline | Captured | % |
|:-------|:---------|:---------|:---|
| M1: NBA 3.0 KERENDIA_FLAG | 77,972 | 71,790 | 92.1% |
| M2: LAAD V6 NBRX>0 | 40,512 | 40,382 | 99.7% |
| M3: LAAD V6 TRX>0 | 68,416 | 63,647 | 93.0% |
| M4: FCT_RX paid TRX | 68,375 | 63,619 | 93.0% |
| C2: FCT_RX NBRX overall | 61,583 | 61,583 | **100.0%** |

**Hotspot: 12,076 writers missed by C1 core:**
* 64% PCP, 13% NEPH, 11% CARD
* 68% are single-script writers (NBRX = 1)
* All recovered by C2 criterion

---

## 8. Notebook Structure

| Notebook | Purpose |
|:---------|:--------|
| `01_Data_Exploration` | Load lrx_nbrx, explore schema, distributions, specialty/indication/product summaries |
| `02_Universe_Construction` | Build C1 (8 decile sets), C2 (Kerendia writers), C3 (specialists), C4 (targeting); combine into final universe |
| `03_Validation_Hotspot` | Validate against NBA 3.0, compute M1–M4 metrics, profile missed writers, call history overlap |

---

*Generated by Genie Code — October 19, 2026*
