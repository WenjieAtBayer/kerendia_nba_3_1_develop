# Kerendia NBA 3.1 (v6) — HCP Universe Identification

**Date:** October 16, 2026
**Status:** In Development
**Key Change from v5:** C2 (Kerendia writers) now uses **raw STG_CAR_IQV_LAAD_FCT_RX NBRX** (all claim types, full history) computed from `Kerendia_NBRX_From_Raw_FCT_RX` notebook.

---

## 1. Approach: Claims-Based Universe for NBA 3.1

### 1.1 Background: NBA 3.0 Universe

NBA 3.0 identifies HCPs through 4 criteria, all sourced from IQVIA LAAD claims via Snowflake (`STG_CAR_IQV_LAAD_FCT_RX`):

| Criterion | Definition | NBA 3.0 Count |
|:----------|:-----------|---------------:|
| C1: SGLT2/GLP1 prescribers | HCPs (D2+) prescribing SGLT2/GLP1 in the 2-year lookback | 193,974 |
| C2: Kerendia writers | HCPs with paid Kerendia TRx claims (full history, `CLAIM_TYPE='PD'`) | 77,972 |
| C3: Nephrologists | All Nephrologists from targeting list | 16,414 |
| C4: Targeting / BPT | HCPs on latest BPT or Call Plan targeting list | 78,798 |
| **Total Universe** | | **232,965** |

### 1.2 NBA 3.1 Universe (v6 Results)

NBA 3.1 expands to 4 indications, 2 drug pools, broader Kerendia writer definition, and adds Cardiologists:

| Criterion | Definition | NBA 3.1 Count |
|:----------|:-----------|---------------:|
| C1: Core prescribers (D2+) | Set 1 (T2D×SGLT2/GLP1) ∪ Set 3 (CKD×SGLT2/GLP1), decile ≥ 2 | 242,868 |
| C2: Kerendia writers | STG_CAR_IQV_LAAD_FCT_RX NBRX > 0, all claim types (PD+RV+RJ), full history | 61,583 |
| C3: Specialists | NEPH (15,048) + CARD (51,666) | 66,714 |
| C4: Targeting / BPT | `CP_KER_HCP` (FF in CR1/CR2/CR4/CR5, Product = KERENDIA) | 78,798 |
| **Total Universe (C1+C2+C3+C4)** | | **294,244** |

| | NBA 3.0 | NBA 3.1 (v6) | Change |
|:--|---:|---:|:--|
| **Total HCPs** | 232,965 | **294,244** | +61,279 (+26%) |
| **NBA 3.0 overlap** | 232,965 (100%) | **220,017 (94.4%)** | 12,948 NBA30-only not yet captured |
| **Kerendia Flag Writers (M1 - From NBA 3.0)** | 77,972 | **71,309 captured (91.5%)** | 6,663 missed (mostly pre-Oct’24 writers) |
| **Kerendia Writers (C2 - From NBA 3.1)** | 58,212 (94.5%) | **61,583 (100%)** |  3,371 are new to NBA 3.1 |

**NBA 3.0 vs NBA 3.1 Core Overlap with Kerendia Writers (61,583):**

| Metric | NBA 3.0 C1 (193,974) | NBA 3.1 C1 (242,868) |
|:-------|----------------------:|----------------------:|
| Overlap with Kerendia Writers | 43,610 | 49,520 |
| % of Writers captured | 70.8% | 80.4% |

> NBA 3.1's expanded C1 captures **5,910 more** Kerendia writers than NBA 3.0's C1 (80.4% vs 70.8%). The remaining ~12K writers are recovered by the explicit C2 criterion.

> **NBA 3.1 is 26% larger than NBA 3.0** while covering 94.4% of the prior universe. The remaining 5.6% (12.9K) are primarily HCPs who entered NBA 3.0 through legacy criteria no longer active.

### 1.3 What Changes in NBA 3.1 (v6)

NBA 3.1 expands the claims-based approach with **indication-specific deciling** to capture a broader, more relevant HCP population.

| Dimension | NBA 3.0 | NBA 3.1 (v6) |
|:----------|:--------|:--------|
| **Decile source** | SGLT2/GLP1 only (single pool) | 4 indications × 2 drug pools = **8 decile sets** |
| **Indications** | Not used for deciling | T2D, CKD, HF, T1D (from `INDICATION_GROUP_APP1`) |
| **Drug pools** | SGLT2 + GLP1 | SGLT2/GLP1 **and** ACE/ARB |
| **Decile metric** | TRx-based | **NBRx-based** (`sum(NBRX)` per HCP) |
| **C2: Kerendia writers** | Paid TRx claims, full history | **STG_CAR_IQV_LAAD_FCT_RX NBRX > 0** (all claim types, full history) |
| **C3: Specialty** | Nephrologists only | **Nephrologists + Cardiologists** |
| **Source table** | `STG_CAR_IQV_LAAD_FCT_RX` (Snowflake) | Deciling: `lrx_nbrx`; C2: `STG_CAR_IQV_LAAD_FCT_RX` (Snowflake) |
| **Lookback** | 2-year rolling | 2-year rolling; Analysis on Oct '24 – Sep '26 (24 months) |

### 1.4 Data Summary

| Parameter | Value |
|:----------|:------|
| **Decile source** | `pace_ker_in_house_schema.lrx_nbrx` (103.9M rows in lookback) |
| Decile metric | `sum(NBRX)` per PROVIDER_ID |
| Decile method | Cumulative volume-based (each decile ≈ 10% of total NBRX) |
| Unique HCPs in lookback | 1,357,359 |
| **C2 source** | `Kerendia_NBRX_From_Raw_FCT_RX` → Snowflake `STG_CAR_IQV_LAAD_FCT_RX` × `DIM_PRD` |
| C2 scope | `PRODUCT_GROUP='KERENDIA'`, all claim types (PD+RV+RJ), full history (Jul 2021–Sep 2026) |
| C2 NBRX logic | First-ever claim per patient-product = NBRX; gap > 365 days = NBRX |
| **C2 Kerendia writers (NBRX > 0)** | **61,583** |

**Kerendia Writer Breakdown from STG_CAR_IQV_LAAD_FCT_RX:**

| Metric | Count |
|:-------|------:|
| NBRX > 0 (all claims) | **61,583** |
| NBRX > 0 (paid only) | 43,114 |
| TRX > 0 (all claims) | 91,751 |
| TRX > 0 (paid only) | 79,342 |

### 1.5 The 8 Decile Sets: HCP Counts & Kerendia Writer Capture

| Set | Ind × Pool | Total HCPs | D2+ HCPs | Kerendia Writer Capture (%) | D2+ Kerendia Writer Capture (%) |
|:---:|:-----------|----------:|---------:|:---------------------------:|:-------------------------------:|
| 1 | T2D × SGLT2/GLP1 | 553,251 | 210,872 | 94.4% | 70.7% |
| 2 | T2D × ACE/ARB | 603,913 | 281,207 | 94.2% | **80.2%** |
| 3 | CKD × SGLT2/GLP1 | 449,230 | 205,248 | 92.3% | 76.5% |
| 4 | CKD × ACE/ARB | 494,874 | 253,771 | 91.5% | **78.2%** |
| 5 | HF × SGLT2/GLP1 | 430,659 | 228,342 | 89.3% | 72.8% |
| 6 | HF × ACE/ARB | 409,457 | 242,195 | 83.4% | 67.7% |
| 7 | T1D × SGLT2/GLP1 | 56,350 | 42,885 | 23.4% | 19.0% |
| 8 | T1D × ACE/ARB | 114,916 | 97,185 | 37.8% | 33.1% |

> **Total Kerendia Writers (C2): 61,583.** No single set exceeds 80% capture at D2+. **Combination logic is essential.** T1D sets capture only 19–33% of writers. 2,174 writers (3.5%) are NOT in any of the 8 decile sets.

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

### 2.3 Optimal Combination Logic

Starting from the Core D2+ (Set 1 ∪ Set 3), we add sets one at a time in order of best writer-recovery-per-HCP ratio:

| Step | Action | Universe | Ker Writers | % Captured | Marginal HCPs | Marginal Writers |
|:----:|:-------|--------:|-----------:|:----------:|--------------:|-----------------:|
| 0 | Core D2+ (Set 1 ∪ Set 3) | 242,868 | 49,520 | 80.4% | — | — |
| 1 | + Set 4: CKD×ACE/ARB | 308,048 | 53,291 | 86.5% | 65,180 | 3,771 |
| 2 | + Set 5: HF×SGLT2/GLP1 | 331,575 | 54,181 | 88.0% | 23,527 | 890 |
| 3 | + Set 2: T2D×ACE/ARB | 353,226 | 54,878 | 89.1% | 21,651 | 697 |
| 4–6 | + T1D sets + HF×ACE/ARB | 390,549 | 55,538 | 90.2% | 37,323 | 660 |

> **After Core + Set 4, each additional set adds diminishing Kerendia writers** (890 → 697 → 660). The remaining 9.8% gap (6,045 writers) needs an explicit Kerendia writer criterion (C2).

**Why not use the full 390K instead of 242K?**

The full 8-set union (390K) was considered but not adopted as the core for three reasons:

| | Core (Set1 ∪ Set3) | Full 8-Set Union | Difference |
|:--|---:|---:|:--|
| HCPs | 242,868 | 390,549 | +148K HCPs (+61%) |
| Kerendia writers captured | 49,520 | 55,538 | +6,018 writers (+12%) |
| Writer capture % | 80.4% | 90.2% | +9.8pp |
| Writer density | 20.4% | 14.2% | **-6.2pp** (dilution) |

1. **Diminishing returns:** The extra 148K HCPs only add 6K writers — a writer density of just **4.1%** in the marginal HCPs (vs 20% in the core). Most of the 148K are non-Kerendia prescribers.
2. **Criterion2 makes it redundant:** Since C2 (61,583 writers) is added as a separate criterion anyway, those 6K writers are already captured. The full union adds 148K non-writer HCPs for no Kerendia benefit.
3. **Universe bloat:** Stacking C2 + C3 on top of the 390K union would push the total to ~430K+ (vs 291K with the core), **nearly 2× NBA 3.0**, without proportional commercial value.

The core (Set1 ∪ Set3) keeps C1 focused on the **highest-relevance HCPs** (T2D + CKD × SGLT2/GLP1) while C2 and C3 handle targeted additions.

### 2.4 Profile of 12,063 Writers Missed by Core D2+

Of the 61,583 C2 writers, **12,063 (19.6%)** are not in Core D2+. Here is who they are:

**Claim type:**

| Type | Count | % |
|:-----|------:|:---:|
| Paid NBRX (PD) | 6,798 | 56.4% |
| Non-paid NBRX only (RV/RJ) | 5,265 | 43.6% |

> Nearly half the missed writers have **non-paid claims only** — these were invisible in paid-only definition and would never appear in `lrx_nbrx`.

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

## 3. Combined NBA 3.1 Universe (Core + Criterion 2 + Criterion 3)

**Criterion definitions:**
* **C1 (Core):** Set 1 (T2D×SGLT2/GLP1) ∪ Set 3 (CKD×SGLT2/GLP1) at decile cutoff
* **C2 (Kerendia Writers):** STG_CAR_IQV_LAAD_FCT_RX NBRX > 0, all claim types, full history → **61,583 HCPs**
* **C3 (Specialty):** NEPH (15,048) ∪ CARD (51,666) = **66,714 HCPs**
* **C4 (Targeting/BPT):** `CP_KER_HCP` (FF in CR1/CR2/CR4/CR5, Product = KERENDIA) = **78,798 HCPs**

Kerendia writers who are NEPH: 9,074 | CARD: 6,604

### 3.1 Incremental Buildup + Validation Metrics

**Validation Metrics (independent of C2):**
* **M1:** NBA 3.0 `KERENDIA_FLAG` = **77,972** (pre-baked flag from prior pipeline output)
* **M2:** `lrx_nbrx` paid NBRX > 0, 24-mo lookback = **40,122** (v5 baseline)
* **M3:** LAAD V6 `TRX > 0`, 24-month lookback = **67,835**
* **M4:** Raw STG_CAR_IQV_LAAD_FCT_RX paid TRX, 24-mo lookback = **67,796**
| Metric | D2+ |
|:-------|----:|
| C1 Core | 242,868 |
| +C2 Kerendia Writers | 254,931 |
| +C3 NEPH | 259,452 |
| +C3 CARD | 291,357 |
| +C4 Targeting/BPT = **Total** | **294,244** |
| %NBA30 | **94.4%** |
| M1: NBA 3.0 FLAG (77,972) | 71,795 (92.1%) |
| M2: lrx_nbrx NBRX (40,112) | 40,040 (99.8%) |
| M3: LAAD V6 TRX (67,835) | 63,207 (93.2%) |
| M4: STG_CAR_IQV_LAAD_FCT_RX TRX (79,342) | 72,966 (92.0%) |

> **D2+ combined (294K) covers 94.4% of NBA 3.0.** C4 adds 2,888 incremental HCPs (mostly Targeting/BPT PCPs in D1). All validation metrics exceed 92% at D2+.

### 3.2 Kerendia Writer Coverage — Validation Metrics

| Metric | Source | Baseline | Captured at D2+ | % | Missed |
|:-------|:-------|----------:|----------------:|:---:|-------:|
| **M1** | NBA 3.0 KERENDIA_FLAG | 77,972 | 71,309 | **91.5%** | 6,663 |
| **M2** | lrx_nbrx paid NBRX>0 (24-mo) | 40,122 | 39,857 | **99.3%** | 265 |
| **M3** | LAAD V6 TRX>0 (24-mo) | 67,835 | 62,745 | **92.5%** | 5,090 |
| **M4** | STG_CAR_IQV_LAAD_FCT_RX paid TRX (24-mo) | 67,796 | 62,722 | **92.5%** | 5,074 |

**v5 → v6 improvement:**
* **M1:** 87.2% → **91.5%** (+4.3pp) — 3,353 more NBA 3.0 Kerendia writers captured
* **M3/M4:** 91.5% → **92.5%** (+1.0pp) — modest improvement from broader C2
* **NBA30 overlap:** 91.7% → **93.2%** (+1.5pp) — 3,470 fewer NBA30-only HCPs

---

## 4. Next Steps

### 4.1 Kerendia Call Table Overlap Analysis

**Source:** `CPH_DB_PROD.MODEL_V2.FACT_CALL` × `MAP_CUSTOMER_XREF` (Snowflake)
**ID Mapping:** `kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING` (PROVIDER_ID ↔ BH_ID)
**Filters:** `STAT = 'SUBMITTED_VOD'`, `DETL_PROD = 'KERENDIA'`, `BH_ID NOT LIKE '%BHO%'`

| Metric | All-Time | Since 2023 |
|:-------|--------:|-----------:|
| Called HCPs | 177,855 | 152,852 |
| Overlap with universe (294K) | 139,521 (47.9%) | 126,725 (43.5%) |
| In universe, NOT called | 151,835 (52.1%) | 164,631 (56.5%) |
| Called, NOT in universe | 38,338 | 26,131 |

> ~48% of the universe has been called for Kerendia. Over half has never been contacted.

**Profile of 26,131 called-but-outside HCPs (since 2023):**

| Dimension | Finding |
|:----------|:--------|
| **ID mapping** | 21,174 with PROVIDER_ID; 4,957 unmappable |
| **Specialty** | 94.6% PCPs (20,027); ENDO 525; NEPH 190; CARD 183 |
| **C2 writer?** | **0** — none are Kerendia writers |
| **In NBA 3.0?** | 2,933 (13.9%) |
| **In lrx_nbrx (24-mo)?** | 18,884 (89.2%) have claims |
| **In D1 of core sets?** | 13,554 (64.0%) — low-volume SGLT2/GLP1 prescribers |
| **Not in any decile** | 7,624 (36.0%) |

> These are predominantly **low-volume PCPs in D1** — commercially active (89% have claims, recently called) but prescribing too little SGLT2/GLP1 to cross the D2 cutoff. A **Call History criterion (C5)** would capture ~21K recently-called HCPs not reachable through claims-based criteria.

### 4.2 Add HCPs Reached via Other Promotional Channels

Expand the universe to include HCPs who have responded positively to:
* **Speaker Programs** — HCPs who attended or spoke at Kerendia-related events
* **Deep Engagement Programs** — HCPs engaged through peer-to-peer or medical education
* **Digital / Non-Personal Promotion** — HCPs with meaningful engagement via email, digital media, or remote interactions

These HCPs represent an invested audience with prior brand exposure and should be retained regardless of their claims-based decile position.

---

*Generated by Genie Code — October 16, 2026*