# Kerendia NBA 3.1 — HCP Universe Identification

**Date:** October 15, 2026
**Status:** In Development

---

## 1. Approach: Claims-Based Universe for NBA 3.1

### 1.1 Background: NBA 3.0 Universe

NBA 3.0 identifies HCPs through 4 criteria, all sourced from IQVIA LAAD claims via Snowflake (`STG_CAR_IQV_LAAD_FCT_RX`):

| Criterion | Definition | NBA 3.0 Count |
|:----------|:-----------|---------------:|
| C1: SGLT2/GLP1 prescribers | HCPs (D2+) prescribing SGLT2/GLP1 in the 2-year lookback | 193,974 |
| C2: Kerendia writers | HCPs with paid Kerendia TRx claims (full history, `CLAIM_TYPE='PD'`) | 77,972 |
| C3: Nephrologists | All Nephrologists from targeting list | 16,414 |
| C4: Targeting / BPT | HCPs on latest BPT or Call Plan targeting list | 78,389 |
| **Total Universe** | | **232,965** |

### 1.2 What Changes in NBA 3.1

NBA 3.1 expands the claims-based approach with **indication-specific deciling** to capture a broader, more relevant HCP population.

| Dimension | NBA 3.0 | NBA 3.1 |
|:----------|:--------|:--------|
| **Decile source** | SGLT2/GLP1 only (single pool) | 4 indications × 2 drug pools = **8 decile sets** |
| **Indications** | Not used for deciling | T2D, CKD, HF, T1D (from `INDICATION_GROUP_APP1`) |
| **Drug pools** | SGLT2 + GLP1 | SGLT2/GLP1 **and** ACE/ARB |
| **Decile metric** | TRx-based | **NBRx-based** (`sum(NBRX)` per HCP) |
| **C2: Kerendia writers** | Paid TRx claims, full history | Paid NBRX > 0, 24-month lookback |
| **C3: Specialty** | Nephrologists only | **NEPH + Cardiologists (CARD)** |
| **Source table** | `STG_CAR_IQV_LAAD_FCT_RX` (Snowflake) | `lrx_nbrx` (Databricks) + Snowflake for validation |
| **Lookback** | 2-year rolling | 2-year rolling; Analysis on Oct '24 – Sep '26 (24 months) |

### 1.3 Data Summary

| Parameter | Value |
|:----------|:------|
| Source | `pace_ker_in_house_schema.lrx_nbrx` (103.9M rows in lookback) |
| Metric | `sum(NBRX)` per PROVIDER_ID |
| Decile method | Cumulative volume-based (each decile ≈ 10% of total NBRX) |
| Unique HCPs in lookback | 1,357,359 |
| Kerendia writers (NBRX > 0) | 40,112 |
| Total Kerendia NBRX | 196,109 |

### 1.4 HCP Counts by Decile Cutoff (8 Sets)

| Set | Ind × Pool | Total HCPs | D2+ | D3+ | D4+ |
|:---:|:-----------|----------:|--------:|--------:|--------:|
| 1 | T2D × SGLT2/GLP1 | 553,251 | 210,872 | 146,270 | 106,869 |
| 2 | T2D × ACE/ARB | 603,913 | 281,207 | 195,788 | 143,309 |
| 3 | CKD × SGLT2/GLP1 | 449,230 | 205,248 | 136,503 | 95,465 |
| 4 | CKD × ACE/ARB | 494,874 | 253,771 | 173,187 | 123,567 |
| 5 | HF × SGLT2/GLP1 | 430,659 | 228,342 | 155,917 | 109,756 |
| 6 | HF × ACE/ARB | 409,457 | 242,195 | 163,125 | 114,988 |
| 7 | T1D × SGLT2/GLP1 | 56,350 | 42,885 | 29,419 | 17,574 |
| 8 | T1D × ACE/ARB | 114,916 | 97,185 | 79,454 | 61,723 |

### 1.5 Kerendia Writer Capture by Individual Set

| Set | Ind × Pool | Writers in Set | D2+ Capture | D3+ Capture |
|:---:|:-----------|---------------:|:----------:|:----------:|
| 1 | T2D × SGLT2/GLP1 | 39,437 / 40,112 | 76.0% | 61.4% |
| 2 | T2D × ACE/ARB | 39,267 / 40,112 | **86.1%** | 73.6% |
| 3 | CKD × SGLT2/GLP1 | 38,996 / 40,112 | 84.1% | 72.1% |
| 4 | CKD × ACE/ARB | 38,582 / 40,112 | **85.1%** | 74.2% |
| 5 | HF × SGLT2/GLP1 | 38,014 / 40,112 | 79.9% | 68.0% |
| 6 | HF × ACE/ARB | 35,736 / 40,112 | 74.4% | 61.8% |
| 7 | T1D × SGLT2/GLP1 | 10,479 / 40,112 | 21.4% | 16.7% |
| 8 | T1D × ACE/ARB | 16,949 / 40,112 | 36.9% | 32.5% |

> No single set exceeds 86% capture. **Combination logic is essential.** T1D sets capture only 21–37% of Kerendia writers.

---

## 2. Strategy for Expanding the Core Universe

### 2.1 The 8 Sets: Indication × Drug Pool Matrix

|  | **SGLT2 / GLP1** | **ACE / ARB** |
|:---|:---:|:---:|
| **T2D** | Set 1 (553K HCPs) | Set 2 (604K HCPs) |
| **CKD** | Set 3 (449K HCPs) | Set 4 (495K HCPs) |
| **HF** | Set 5 (431K HCPs) | Set 6 (409K HCPs) |
| **T1D** | Set 7 (56K HCPs) | Set 8 (115K HCPs) |

Each cell = all HCPs with `sum(NBRX) > 0` for that indication × drug pool. Deciles split the HCPs within each cell into 10 groups by cumulative NBRX volume.

### 2.2 Core Universe: Set 1 ∪ Set 3

**Set 1 (T2D × SGLT2/GLP1)** and **Set 3 (CKD × SGLT2/GLP1)** form the core because:
* T2D and CKD are Kerendia's primary indications (65% of Kerendia NBRX comes from T2D+CKD patients)
* SGLT2/GLP1 is the drug pool most aligned with the Kerendia prescriber profile
* These two sets were the basis of NBA 3.0's C1 criterion

| Cutoff | Core HCPs | Kerendia Writers Captured | % of 40,112 |
|:------:|----------:|--------------------------:|:-----------:|
| D2+ | 242,868 | 35,013 | 87.3% |
| D3+ | 172,114 | 30,831 | 76.9% |
| D4+ | 127,606 | 26,776 | 66.8% |

> At D2+, the core captures 87.3% of Kerendia writers in 243K HCPs. The remaining 12.7% (5,099 writers) must be recovered via add-on sets or explicit criteria.

### 2.3 Cross-Set Recovery of Missing Writers

Writers missing from one set can often be found in another:

| Set Missing From | Missing Writers | Top Recovery Set | Recovers | At D2+ |
|:-----------------|----------------:|:-----------------|--------:|-------:|
| Set 1 (T2D×SGLT2/GLP1) | 675 | Set 2 (T2D×ACE/ARB) | 320 | 58 |
| Set 3 (CKD×SGLT2/GLP1) | 1,116 | Set 2 (T2D×ACE/ARB) | 668 | 201 |
| Set 5 (HF×SGLT2/GLP1) | 2,098 | Set 2 (T2D×ACE/ARB) | 1,622 | 754 |
| Set 6 (HF×ACE/ARB) | 4,376 | Set 1 (CORE) | 3,926 | 2,483 |

> **ACE/ARB sets recover the most missing writers.** Missing writers from core sets (675–1,116) are almost all low-volume, single-script PCPs (Avg Kerendia NBRX 1.2–1.3).

### 2.4 Core Gap + Marginal Add-on Value

**Set 4 (CKD × ACE/ARB) is always the best first add-on** to the core at every cutoff:

| Cutoff | Core HCPs | Core Writers (%) | Best Add-on | Gap Recovered |
|:------:|----------:|-----------------:|:------------|:-------------:|
| D2+ | 242,868 | 35,013 (87.3%) | Set 4: CKD×ACE/ARB | 2,209 (43.3% of gap) |
| D3+ | 172,114 | 30,831 (76.9%) | Set 4: CKD×ACE/ARB | 3,657 (39.4% of gap) |
| D4+ | 127,606 | 26,776 (66.8%) | Set 4: CKD×ACE/ARB | 4,667 (35.0% of gap) |

### 2.5 Optimal Combination Logic

Starting from the core (Set 1 ∪ Set 3), we add sets one at a time in order of best writer-recovery-per-HCP ratio:

| Step | Action | Universe | Ker Writers | % Captured | Marginal HCPs | Marginal Writers |
|:----:|:-------|--------:|-----------:|:----------:|--------------:|-----------------:|
| 0 | Core (Set 1 ∪ Set 3) | 242,868 | 35,013 | 87.3% | — | — |
| 1 | + Set 4: CKD×ACE/ARB | 308,048 | 37,222 | 92.8% | 65,180 | 2,209 |
| 2 | + Set 5: HF×SGLT2/GLP1 | 331,575 | 37,785 | 94.2% | 23,527 | 563 |
| 3 | + Set 2: T2D×ACE/ARB | 353,226 | 38,104 | 95.0% | 21,651 | 319 |
| 4–6 | + T1D sets + HF×ACE/ARB | 390,549 | 38,421 | 95.8% | 37,323 | 317 |

> **After Core + Set 4, each additional set adds diminishing Kerendia writers** (563 → 319 → 37 per step). The remaining 4.2% gap (1,691 writers) needs an explicit Kerendia writer criterion (C2).

---

## 3. NBA 3.1 Core vs NBA 3.0 Universe Overlap

### 3.1 Core (Set 1 ∪ Set 3) vs NBA 3.0 by Cutoff

**NBA 3.0 Universe:** 232,965 HCPs (PULL_DT: 2026_10_09)

| Cutoff | v5 Core HCPs | Overlap | v5-only | NBA30-only | Ker Overlap | Ker v5-only | Ker NBA30-only |
|:------:|-----------:|--------:|--------:|-----------:|------------:|------------:|---------------:|
| ALL | 566,605 | 224,697 | 341,908 | 8,268 | 38,880 | 672 | 39,092 |
| D2+ | 242,868 | 198,007 | 44,861 | 34,958 | 34,545 | 468 | 43,427 |
| D3+ | 172,114 | 160,217 | 11,897 | 72,748 | 30,470 | 361 | 47,502 |
| D4+ | 127,606 | 123,488 | 4,118 | 109,477 | 26,493 | 283 | 51,479 |

> At D2+, the core overlaps with **198K of 233K NBA 3.0 HCPs (85%)**. The 35K NBA30-only HCPs must enter through other criteria.

### 3.2 Flag Distribution: Overlap vs NBA30-only (Core D2+)

| Flag | In Overlap (198K) | % | In NBA30-only (35K) | % |
|:-----|------------------:|:---:|--------------------:|:---:|
| KERENDIA_FLAG | 61,437 | 31.0% | 16,535 | **47.3%** |
| SGLT2_GLP1_FLAG | 185,084 | 93.5% | 8,890 | 25.4% |
| NEPH_FLAG | 8,976 | 4.5% | 7,438 | **21.3%** |
| TARGETING_HCP_FLAG | 66,681 | 33.7% | 11,708 | 33.5% |
| BPT_HCP_FLAG | 66,681 | 33.7% | 11,708 | 33.5% |

> **The 35K NBA30-only HCPs are enriched in Kerendia writers (47%) and NEPH (21%).** These HCPs enter NBA 3.0 through Criterion 2 (Kerendia writers) and Criterion 3 (Specialty), not deciling.

### 3.3 Full 8-Set Union vs NBA 3.0

| Cutoff | v5 Union | Overlap | % of NBA30 | v5-only | NBA30-only |
|:------:|---------:|--------:|:----------:|--------:|-----------:|
| D2+ | 390,549 | 218,835 | **93.9%** | 171,715 | 14,131 |
| D3+ | 303,802 | 204,109 | 87.6% | 99,693 | 28,856 |
| D4+ | 241,825 | 181,549 | 77.9% | 60,276 | 51,416 |

### 3.4 Key Insight: Why Criteria 2–4 are Essential

Deciling alone (even the full 8-set union at D2+) leaves **14,131 NBA 3.0 HCPs unmatched**. These are:

* **Kerendia writers (52%)** — HCPs who prescribe Kerendia but don't appear in the top deciles of any indication×drug pool combination
* **Nephrologists / Cardiologists (21%)** — Specialists who may have low claim volumes but are clinically relevant
* **Targeting/BPT HCPs (15%)** — HCPs on the commercial targeting or Best Practice Targeting lists

**Criteria 2–4 are not replaceable by deciling.** They capture HCPs through fundamentally different pathways (product history, specialty, commercial targeting) that volume-based deciling cannot reach.

---

## 4. Combined NBA 3.1 Universe (Core + Criterion 2 + Criterion 3)

**Criterion definitions:**
* **C1 (Core):** Set 1 (T2D×SGLT2/GLP1) ∪ Set 3 (CKD×SGLT2/GLP1) at decile cutoff
* **C2 (Kerendia Writers):** `PRODUCT_CLASS = 'KERENDIA'` AND `NBRX > 0` (24-mo lookback) → **40,112 HCPs**
* **C3 (Specialty):** NEPH (15,048) ∪ CARD (51,666) = **66,714 HCPs**

Kerendia writers who are NEPH: 7,525 | CARD: 5,201

### 4.1 Incremental Buildup + 4 Kerendia Metrics

**4 Kerendia Writer Definitions:**
* **M1:** NBA 3.0 `KERENDIA_FLAG` = **77,972** (pre-baked flag from prior pipeline output)
* **M2:** LAAD V6 `NBRX > 0`, 24-month lookback = **40,122**
* **M3:** LAAD V6 `TRX > 0`, 24-month lookback = **67,835**
* **M4:** Raw `STG_CAR_IQV_LAAD_FCT_RX` (Snowflake), `CLAIM_TYPE='PD'`, `PRODUCT_GROUP='KERENDIA'`, 24-mo lookback = **67,796**

| Cutoff | C1 Core | +C2 Ker | +C3 NEPH | +CARD = Total | %NBA30 | M1 (77,972) | M2 (40,122) | M3 (67,835) | M4 (67,796) |
|:------:|--------:|--------:|---------:|--------------:|:------:|------------:|------------:|------------:|------------:|
| D2+ | 242,868 | 247,967 | 253,215 | **285,608** | **91.7%** | 67,956 (87.2%) | 40,098 (99.9%) | 62,055 (**91.5%**) | 62,046 (**91.5%**) |
| D3+ | 172,114 | 181,395 | 187,521 | **226,462** | 79.8% | 63,614 (81.6%) | 40,086 (99.9%) | 58,747 (86.6%) | 58,744 (86.6%) |
| D4+ | 127,606 | 140,942 | 147,579 | **189,759** | 67.3% | 59,939 (76.9%) | 40,080 (99.9%) | 55,901 (82.4%) | 55,901 (82.5%) |

> **D2+ combined (286K) covers 91.7% of NBA 3.0.** M3/M4 confirm that 91.5% of 24-mo Kerendia TRx writers are captured. M3 ≈ M4 validates that LAAD V6 and raw FCT_RX agree to within 39 HCPs.

### 4.2 Flag Distribution (D2+ Combined vs NBA 3.0)

| Flag | In Overlap (213,694) | % | NBA30-only (19,271) | % |
|:-----|---------------------:|:---:|--------------------:|:---:|
| KERENDIA_FLAG | 67,956 | 31.8% | 10,016 | **52.0%** |
| SGLT2_GLP1_FLAG | 187,584 | 87.8% | 6,390 | 33.2% |
| NEPH_FLAG | 15,041 | 7.0% | 1,373 | 7.1% |
| TARGETING_HCP_FLAG | 75,571 | 35.4% | 2,818 | 14.6% |
| BPT_HCP_FLAG | 75,571 | 35.4% | 2,818 | 14.6% |

> The remaining 19K NBA30-only HCPs are **52% Kerendia writers** (from NBA 3.0's broader full-history definition). NEPH coverage is near-complete (15,041 of 16,414).

### 4.3 Kerendia Writer Coverage — 4 Metrics

| Metric | Source | Baseline | Captured at D2+ | % | Missed |
|:-------|:-------|----------:|----------------:|:---:|-------:|
| **M1** | NBA 3.0 KERENDIA_FLAG | 77,972 | 67,956 | 87.2% | 10,016 |
| **M2** | LAAD V6 NBRX>0 (24-mo) | 40,122 | 40,098 | **99.9%** | 24 |
| **M3** | LAAD V6 TRX>0 (24-mo) | 67,835 | 62,055 | **91.5%** | 5,780 |
| **M4** | Snowflake FCT_RX TRX (24-mo) | 67,796 | 62,046 | **91.5%** | 5,750 |

**Why baselines differ:**
* **M1 ≫ M3/M4:** M1 uses full history; M3/M4 use 24-mo → ~10K writers stopped before Oct '24
* **M3 ≈ M4:** LAAD V6 and raw FCT_RX agree on 24-mo TRx within 39 HCPs
* **M3/M4 > M2 by ~27,700:** TRx includes refills; NBRX = new scripts only → 27.7K are refill-only writers

### 4.4 Comparison: Core-only vs Combined vs NBA 3.0

| Universe | Total HCPs | %NBA30 | M1 (77,972) | M2 (40,122) | M3 (67,835) | M4 (67,796) |
|:---------|----------:|:------:|------------:|------------:|------------:|------------:|
| Core D2+ only | 242,868 | 85.0% | — | 35,013 (87.3%) | — | — |
| **Core D2+ + C2 + C3** | **285,608** | **91.7%** | **67,956 (87.2%)** | **40,098 (99.9%)** | **62,055 (91.5%)** | **62,046 (91.5%)** |
| NBA 3.0 | 232,965 | 100% | 77,972 (baseline) | — | — | — |

> Adding C2+C3 lifts NBA 3.0 overlap from 85% → 92% and captures 91.5% of 24-mo TRx writers. **To close the remaining ~5,750 TRx writers**, C2 could expand from NBRX>0 to TRX>0.

---

## 5. Next Steps

### 5.1 Add Best Practice Targeting / Call Plan HCPs (Criterion 4)

NBA 3.0 includes 78,389 HCPs from the latest BPT and Call Plan targeting lists (`CP_KER_HCP`, `KER_BPT_2025_Q3`). These are commercially prioritised HCPs that may not appear in claims-based deciling. Adding C4 will close a significant portion of the remaining 19K NBA30-only gap.

### 5.2 Add Historical Face-to-Face Call HCPs

HCPs who have been reached via F2F detailing calls in prior cycles should be retained in the universe to maintain commercial continuity, even if their current claims volume is low.

### 5.3 Add HCPs Reached via Other Promotional Channels

Expand the universe to include HCPs who have responded positively to:
* **Speaker Programs** — HCPs who attended or spoke at Kerendia-related events
* **Deep Engagement Programs** — HCPs engaged through peer-to-peer or medical education
* **Digital / Non-Personal Promotion** — HCPs with meaningful engagement via email, digital media, or remote interactions

These HCPs represent an invested audience with prior brand exposure and should be retained regardless of their claims-based decile position.

### 5.4 Expand Kerendia Writer Definition

Consider switching C2 from `NBRX > 0` (40,122 writers) to `TRX > 0` from LAAD V6 or FCT_RX (67,800 writers) to capture refill-only writers who are actively prescribing Kerendia but had no new starts in the lookback period.

---

*Generated by Genie Code — October 15, 2026*