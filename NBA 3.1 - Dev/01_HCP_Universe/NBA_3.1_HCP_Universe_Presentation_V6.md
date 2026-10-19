# Kerendia NBA 3.1 (v6) — HCP Universe Identification

**Date:** October 16, 2026
**Status:** In Development
**Key Change from v5:** C2 (Kerendia writers) now uses **raw FCT_RX NBRX** (all claim types, full history) computed from `Kerendia_NBRX_From_Raw_FCT_RX` notebook.

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

### 1.2 What Changes in NBA 3.1 (v6)

NBA 3.1 expands the claims-based approach with **indication-specific deciling** to capture a broader, more relevant HCP population.

| Dimension | NBA 3.0 | NBA 3.1 (v6) |
|:----------|:--------|:--------|
| **Decile source** | SGLT2/GLP1 only (single pool) | 4 indications × 2 drug pools = **8 decile sets** |
| **Indications** | Not used for deciling | T2D, CKD, HF, T1D (from `INDICATION_GROUP_APP1`) |
| **Drug pools** | SGLT2 + GLP1 | SGLT2/GLP1 **and** ACE/ARB |
| **Decile metric** | TRx-based | **NBRx-based** (`sum(NBRX)` per HCP) |
| **C2: Kerendia writers** | Paid TRx claims, full history | **FCT_RX NBRX > 0** (all claim types, full history) |
| **C3: Specialty** | Nephrologists only | **NEPH + Cardiologists (CARD)** |
| **Source table** | `STG_CAR_IQV_LAAD_FCT_RX` (Snowflake) | Deciling: `lrx_nbrx`; C2: `STG_CAR_IQV_LAAD_FCT_RX` (Snowflake) |
| **Lookback** | 2-year rolling | 2-year rolling; Analysis on Oct '24 – Sep '26 (24 months) |

### 1.3 Data Summary

| Parameter | Value |
|:----------|:------|
| **Decile source** | `pace_ker_in_house_schema.lrx_nbrx` (103.9M rows in lookback) |
| Decile metric | `sum(NBRX)` per PROVIDER_ID |
| Decile method | Cumulative volume-based (each decile ≈ 10% of total NBRX) |
| Unique HCPs in lookback | 1,357,359 |
| **C2 source** | `Kerendia_NBRX_From_Raw_FCT_RX` → Snowflake `STG_CAR_IQV_LAAD_FCT_RX` × `DIM_PRD` |
| C2 scope | `PRODUCT_GROUP='KERENDIA'`, all claim types (PD+RV+RJ), full history (Jul 2021–Sep 2026) |
| C2 NBRX logic | First-ever claim per patient-product = NBRX; gap > 365 days = NBRX |
| **C2 Kerendia writers (NBRX > 0)** | **61,583** (v5 was 40,112) |

**Kerendia Writer Breakdown from FCT_RX:**

| Metric | Count |
|:-------|------:|
| NBRX > 0 (all claims) | **61,583** |
| NBRX > 0 (paid only) | 43,114 |
| TRX > 0 (all claims) | 91,751 |
| TRX > 0 (paid only) | 79,342 |

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
| 1 | T2D × SGLT2/GLP1 | 58,141 / 61,583 | 70.7% | 57.1% |
| 2 | T2D × ACE/ARB | 57,992 / 61,583 | **80.2%** | 67.7% |
| 3 | CKD × SGLT2/GLP1 | 56,837 / 61,583 | 76.5% | 64.2% |
| 4 | CKD × ACE/ARB | 56,372 / 61,583 | **78.2%** | 66.6% |
| 5 | HF × SGLT2/GLP1 | 54,999 / 61,583 | 72.8% | 61.1% |
| 6 | HF × ACE/ARB | 51,389 / 61,583 | 67.7% | 55.1% |
| 7 | T1D × SGLT2/GLP1 | 14,394 / 61,583 | 19.0% | 14.7% |
| 8 | T1D × ACE/ARB | 23,303 / 61,583 | 33.1% | 28.9% |

> No single set exceeds 80% capture. **Combination logic is essential.** T1D sets capture only 19–33% of Kerendia writers. 2,174 writers (3.5%) are NOT in any of the 8 decile sets.

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

| Cutoff | Core HCPs | Kerendia Writers Captured | % of 61,583 |
|:------:|----------:|--------------------------:|:-----------:|
| D2+ | 242,868 | 49,520 | 80.4% |
| D3+ | 172,114 | 42,882 | 69.6% |
| D4+ | 127,606 | 36,744 | 59.7% |

> At D2+, the core captures 80.4% of Kerendia writers in 243K HCPs. The remaining 19.6% (12,063 writers) must be recovered via add-on sets or explicit criteria.

### 2.3 Cross-Set Recovery of Missing Writers

Writers missing from one set can often be found in another:

| Set Missing From | Missing Writers | Top Recovery Set | Recovers |
|:-----------------|----------------:|:-----------------|--------:|
| Set 1 (T2D×SGLT2/GLP1) | 3,442 | Set 2 (T2D×ACE/ARB) | 1,026 |
| Set 3 (CKD×SGLT2/GLP1) | 4,746 | Set 4 (CKD×ACE/ARB) | 805 |
| Set 5 (HF×SGLT2/GLP1) | 6,584 | Set 6 (HF×ACE/ARB) | 541 |
| Set 6 (HF×ACE/ARB) | 10,194 | Set 1 (CORE) | 3,926 |

> **ACE/ARB sets recover the most missing writers.** With the larger C2 (61.6K), more writers fall outside the decile sets, making the explicit C2 criterion even more critical.

### 2.4 Core Gap + Marginal Add-on Value

**Set 6 (HF × ACE/ARB) and Set 4 (CKD × ACE/ARB)** are the best first add-ons:

| Cutoff | Core HCPs | Core Writers (%) | Best Add-on | Gap Recovered |
|:------:|----------:|-----------------:|:------------|:-------------:|
| D2+ | 242,868 | 49,520 (80.4%) | Set 6: HF×ACE/ARB | 3,809 (31.6% of gap) |
| D3+ | 172,114 | 42,882 (69.6%) | Set 4: CKD×ACE/ARB | 5,614 (30.0% of gap) |
| D4+ | 127,606 | 36,744 (59.7%) | Set 4: CKD×ACE/ARB | 6,786 (27.3% of gap) |

### 2.5 Optimal Combination Logic

Starting from the core (Set 1 ∪ Set 3), we add sets one at a time in order of best writer-recovery-per-HCP ratio:

| Step | Action | Universe | Ker Writers | % Captured | Marginal HCPs | Marginal Writers |
|:----:|:-------|--------:|-----------:|:----------:|--------------:|-----------------:|
| 0 | Core (Set 1 ∪ Set 3) | 242,868 | 49,520 | 80.4% | — | — |
| 1 | + Set 4: CKD×ACE/ARB | 308,048 | 53,291 | 86.5% | 65,180 | 3,771 |
| 2 | + Set 5: HF×SGLT2/GLP1 | 331,575 | 54,181 | 88.0% | 23,527 | 890 |
| 3 | + Set 2: T2D×ACE/ARB | 353,226 | 54,878 | 89.1% | 21,651 | 697 |
| 4–6 | + T1D sets + HF×ACE/ARB | 390,549 | 55,538 | 90.2% | 37,323 | 660 |

> **After Core + Set 4, each additional set adds diminishing Kerendia writers** (890 → 697 → 660). The remaining 9.8% gap (6,045 writers) needs an explicit Kerendia writer criterion (C2).

**Why not use the full 390K union as C1?**

The full 8-set union (390K) was considered but not adopted as the core for three reasons:

| | Core (Set1 ∪ Set3) | Full 8-Set Union | Difference |
|:--|---:|---:|:--|
| HCPs | 242,868 | 390,549 | +148K HCPs (+61%) |
| Kerendia writers captured | 49,520 | 55,538 | +6,018 writers (+12%) |
| Writer capture % | 80.4% | 90.2% | +9.8pp |
| Writer density | 20.4% | 14.2% | **-6.2pp** (dilution) |

1. **Diminishing returns:** The extra 148K HCPs only add 6K writers — a writer density of just **4.1%** in the marginal HCPs (vs 20% in the core). Most of the 148K are non-Kerendia prescribers.
2. **C2 makes it redundant:** Since C2 (61,583 writers) is added as a separate criterion anyway, those 6K writers are already captured. The full union adds 148K non-writer HCPs for no Kerendia benefit.
3. **Universe bloat:** Stacking C2 + C3 on top of the 390K union would push the total to ~430K+ (vs 291K with the core), **nearly 2× NBA 3.0**, without proportional commercial value.

The core (Set1 ∪ Set3) keeps C1 focused on the **highest-relevance HCPs** (T2D + CKD × SGLT2/GLP1) while C2 and C3 handle targeted additions.

### 2.6 Profile of 12,063 Writers Missed by Core D2+

Of the 61,583 C2 writers, **12,063 (19.6%)** are not in Core D2+. Here is who they are:

**Claim type:**

| Type | Count | % |
|:-----|------:|:---:|
| Paid NBRX (PD) | 6,798 | 56.4% |
| Non-paid NBRX only (RV/RJ) | 5,265 | 43.6% |

> Nearly half the missed writers have **non-paid claims only** — these were invisible in v5's paid-only definition and would never appear in `lrx_nbrx`.

**Kerendia volume (NBRX):**

| NBRX Bucket | HCPs | % |
|:------------|-----:|:---:|
| 1 (single script) | 8,214 | 68.1% |
| 2–3 | 2,329 | 19.3% |
| 4–5 | 635 | 5.3% |
| 6–10 | 500 | 4.1% |
| 11+ | 385 | 3.2% |

> **68% are single-script writers** (Avg NBRX 2.4, Median 1). Low volume but confirmed Kerendia prescribers. Average TRX = 14.2 (Median 4), suggesting these HCPs have refill activity even with few new starts.

**Specialty:**

| Specialty | HCPs | % |
|:----------|-----:|:---:|
| PCP | 7,710 | 63.9% |
| NEPH | 1,565 | 13.0% |
| CARD | 1,371 | 11.4% |
| NULL (no lrx_nbrx record) | 957 | 7.9% |
| ENDO | 152 | 1.3% |
| HOS | 138 | 1.1% |
| OTHERS | 166 | 1.4% |

> **PCPs dominate (64%)**. Notably, 1,565 NEPH and 1,371 CARD will be recovered by Criterion 3 (Specialty). The 957 NULL-specialty writers have no `lrx_nbrx` record at all.

**Where they sit in the decile sets:**

| Segment | Count | % | Description |
|:--------|------:|:---:|:------------|
| **D1 of Set1 or Set3** | 8,852 | 73.4% | In core sets but below the D2 cutoff (lowest volume prescribers) |
| In other sets (not core) | 1,037 | 8.6% | Appear in ACE/ARB or HF sets but not T2D/CKD × SGLT2/GLP1 |
| **NOT in any of 8 sets** | 2,174 | 18.0% | No SGLT2/GLP1 or ACE/ARB claims for any indication — Kerendia-only prescribers |

**Recovery strategies by segment:**

| Segment | Size | Recovery Path |
|:--------|-----:|:--------------|
| D1 of core sets | 8,852 | **C2 captures them** (explicit Kerendia writer criterion) |
| In other sets | 1,037 | **C2 captures them** (also partially recoverable via Set4/Set6 if core expands) |
| Not in any set, NEPH/CARD | 2,936 | **C2 + C3 captures them** (Kerendia writers + Specialty) |
| Not in any set, PCP/other | 1,238 | **C2 captures them** (only reachable via the explicit writer rule) |

> **All 12,063 missed writers are captured by C2.** This validates the v6 design: the core handles high-volume prescribers via deciling, while C2 handles the long tail of low-volume and non-paid Kerendia writers that deciling cannot reach.

---

## 3. NBA 3.1 Core vs NBA 3.0 Universe Overlap

### 3.1 Core (Set 1 ∪ Set 3) vs NBA 3.0 by Cutoff

**NBA 3.0 Universe:** 232,965 HCPs (PULL_DT: 2026_10_09)

| Cutoff | v6 Core HCPs | Overlap | v6-only | NBA30-only | Ker Overlap | Ker v6-only | Ker NBA30-only |
|:------:|-----------:|--------:|--------:|-----------:|------------:|------------:|---------------:|
| ALL | 566,605 | 224,697 | 341,908 | 8,268 | 51,089 | 7,283 | 26,883 |
| D2+ | 242,868 | 198,007 | 44,861 | 34,958 | 44,346 | 5,174 | 33,626 |
| D3+ | 172,114 | 160,217 | 11,897 | 72,748 | 38,828 | 4,054 | 39,144 |
| D4+ | 127,606 | 123,488 | 4,118 | 109,477 | 33,516 | 3,228 | 44,456 |

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

| Cutoff | v6 Union | Overlap | % of NBA30 | v6-only | NBA30-only |
|:------:|---------:|--------:|:----------:|--------:|-----------:|
| D2+ | 390,549 | 218,834 | **93.9%** | 171,715 | 14,131 |
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
* **C2 (Kerendia Writers):** FCT_RX NBRX > 0, all claim types, full history → **61,583 HCPs**
* **C3 (Specialty):** NEPH (15,048) ∪ CARD (51,666) = **66,714 HCPs**

Kerendia writers who are NEPH: 9,074 | CARD: 6,604

### 4.1 Incremental Buildup + Validation Metrics

**Validation Metrics (independent of C2):**
* **M1:** NBA 3.0 `KERENDIA_FLAG` = **77,972** (pre-baked flag from prior pipeline output)
* **M2:** `lrx_nbrx` paid NBRX > 0, 24-mo lookback = **40,122** (v5 baseline)
* **M3:** LAAD V6 `TRX > 0`, 24-month lookback = **67,835**
* **M4:** Raw FCT_RX paid TRX, 24-mo lookback = **67,796**
* **C2:** FCT_RX NBRX > 0, all claims, full history = **61,583** (what we use)

| Cutoff | C1 Core | +C2 Ker | +C3 NEPH | +CARD = Total | %NBA30 | M1 (77,972) | M2 (40,122) | M3 (67,835) | M4 (67,796) | C2 (61,583) |
|:------:|--------:|--------:|---------:|--------------:|:------:|------------:|------------:|------------:|------------:|------------:|
| D2+ | 242,868 | 254,931 | 259,452 | **291,357** | **93.2%** | 71,309 (91.5%) | 39,857 (99.3%) | 62,745 (92.5%) | 62,722 (92.5%) | 61,583 (**100%**) |
| D3+ | 172,114 | 190,815 | 195,947 | **234,130** | 81.9% | 68,107 (87.3%) | 39,709 (99.0%) | 59,961 (88.4%) | 59,939 (88.4%) | 61,583 (100%) |
| D4+ | 127,606 | 152,445 | 157,909 | **199,111** | 70.1% | 65,540 (84.1%) | 39,604 (98.7%) | 57,666 (85.0%) | 57,643 (85.0%) | 61,583 (100%) |

> **D2+ combined (291K) covers 93.2% of NBA 3.0** (vs 91.7% in v5). C2 is 100% captured by definition. M1/M3/M4 all exceed 91% at D2+.

### 4.2 Flag Distribution (D2+ Combined vs NBA 3.0)

| Flag | In Overlap (217,164) | % | NBA30-only (15,801) | % |
|:-----|---------------------:|:---:|--------------------:|:---:|
| KERENDIA_FLAG | 71,309 | 32.8% | 6,663 | **42.2%** |
| SGLT2_GLP1_FLAG | 187,735 | 86.4% | 6,239 | 39.5% |
| NEPH_FLAG | 15,146 | 7.0% | 1,268 | 8.0% |
| TARGETING_HCP_FLAG | 75,540 | 34.8% | 2,849 | 18.0% |
| BPT_HCP_FLAG | 75,540 | 34.8% | 2,849 | 18.0% |

> The remaining **15.8K NBA30-only HCPs** (down from 19.3K in v5) are still enriched in Kerendia writers (42%) but the gap has narrowed significantly. NEPH coverage is near-complete (15,146 of 16,414).

### 4.3 Kerendia Writer Coverage — Validation Metrics

| Metric | Source | Baseline | Captured at D2+ | % | Missed |
|:-------|:-------|----------:|----------------:|:---:|-------:|
| **M1** | NBA 3.0 KERENDIA_FLAG | 77,972 | 71,309 | **91.5%** | 6,663 |
| **M2** | lrx_nbrx paid NBRX>0 (24-mo) | 40,122 | 39,857 | **99.3%** | 265 |
| **M3** | LAAD V6 TRX>0 (24-mo) | 67,835 | 62,745 | **92.5%** | 5,090 |
| **M4** | FCT_RX paid TRX (24-mo) | 67,796 | 62,722 | **92.5%** | 5,074 |
| **C2** | FCT_RX NBRX>0 (all claims, full hist) | 61,583 | 61,583 | **100%** | 0 |

**v5 → v6 improvement:**
* **M1:** 87.2% → **91.5%** (+4.3pp) — 3,353 more NBA 3.0 Kerendia writers captured
* **M3/M4:** 91.5% → **92.5%** (+1.0pp) — modest improvement from broader C2
* **NBA30 overlap:** 91.7% → **93.2%** (+1.5pp) — 3,470 fewer NBA30-only HCPs

### 4.4 Comparison: Core-only vs Combined vs NBA 3.0

| Universe | Total HCPs | %NBA30 | M1 (77,972) | M2 (40,122) | M3 (67,835) | M4 (67,796) | C2 (61,583) |
|:---------|----------:|:------:|------------:|------------:|------------:|------------:|------------:|
| Core D2+ only | 242,868 | 85.0% | — | 49,520 (80.4%) | — | — | — |
| **Core D2+ + C2 + C3** | **291,357** | **93.2%** | **71,309 (91.5%)** | **39,857 (99.3%)** | **62,745 (92.5%)** | **62,722 (92.5%)** | **61,583 (100%)** |
| NBA 3.0 | 232,965 | 100% | 77,972 (baseline) | — | — | — | — |

> Adding C2+C3 lifts NBA 3.0 overlap from 85% → 93%. All validation metrics exceed 91% at D2+. **C2 expansion from 40K → 62K closes most of the Kerendia writer gap.**

---

## 5. Next Steps

### 5.1 Add Best Practice Targeting / Call Plan HCPs (Criterion 4)

NBA 3.0 includes 78,389 HCPs from the latest BPT and Call Plan targeting lists (`CP_KER_HCP`, `KER_BPT_2025_Q3`). These are commercially prioritised HCPs that may not appear in claims-based deciling. Adding C4 will close a significant portion of the remaining 15.8K NBA30-only gap.

### 5.2 Add Historical Face-to-Face Call HCPs

HCPs who have been reached via F2F detailing calls in prior cycles should be retained in the universe to maintain commercial continuity, even if their current claims volume is low.

### 5.3 Add HCPs Reached via Other Promotional Channels

Expand the universe to include HCPs who have responded positively to:
* **Speaker Programs** — HCPs who attended or spoke at Kerendia-related events
* **Deep Engagement Programs** — HCPs engaged through peer-to-peer or medical education
* **Digital / Non-Personal Promotion** — HCPs with meaningful engagement via email, digital media, or remote interactions

These HCPs represent an invested audience with prior brand exposure and should be retained regardless of their claims-based decile position.

---

*Generated by Genie Code — October 16, 2026*