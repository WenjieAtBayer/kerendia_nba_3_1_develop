# Kerendia NBA HCP Universe — Agent Instructions

You are an AI agent tasked with building an **HCP (Healthcare Provider) Universe** for **Kerendia** (finerenone), a drug used to treat **Chronic Kidney Disease (CKD) associated with Type 2 Diabetes (T2D)**. The universe identifies which HCPs should be scored by the Next Best Action (NBA) model.

---

## 1. Business Context

### 1.1 What is Kerendia?

Kerendia (finerenone) is a selective nonsteroidal mineralocorticoid receptor antagonist (MRA) prescribed for patients with CKD associated with T2D. It is marketed by Bayer. The drug launched in the US in July 2021.

### 1.2 What is the HCP Universe?

The HCP Universe is the set of healthcare providers who are eligible to be scored by the NBA model for commercial targeting. The universe must:

* **Maximize Kerendia writer coverage** — capture as many HCPs who have ever prescribed Kerendia ("writers") as possible
* **Stay within a size budget** — the total universe must not exceed **300,000 HCPs** across all criteria
* **Be commercially relevant** — include HCPs who are likely to prescribe Kerendia based on their prescribing behavior, specialty, or commercial engagement

### 1.3 Key Metric: Kerendia Writers

There are **61,583 Kerendia writers** — HCPs with at least one new-to-brand prescription (NBRX > 0) across all claim types (paid, reversed, rejected) over the full history since Kerendia's launch (July 2021). This is the primary metric to optimize for — the universe should capture as many of these 61,583 as possible.

---

## 2. Therapeutic Area: Indication Pools

Kerendia sits at the intersection of multiple disease areas. HCPs who treat these conditions are the target prescriber population:

| Indication | Code in Data | Relevance to Kerendia |
|:-----------|:-------------|:----------------------|
| **Type 2 Diabetes (T2D)** | `INDICATION_GROUP_APP1` contains "T2D" | Primary indication — Kerendia is for CKD in T2D patients |
| **Chronic Kidney Disease (CKD)** | `INDICATION_GROUP_APP1` contains "CKD" | Primary disease area |
| **Heart Failure (HF)** | `INDICATION_GROUP_APP1` contains "HF" | Overlapping patient population, many CKD+HF patients |
| **Type 1 Diabetes (T1D)** | `INDICATION_GROUP_APP1` contains "T1D" | Smaller overlap, some off-label or adjacent prescribers |

**Important:** `INDICATION_GROUP_APP1` uses compound values (e.g., "T2D, CKD"). Use `.contains()` for filtering, NOT exact match (`==`).

---

## 3. Drug Pools

Two drug pools define the prescribing behavior we care about:

| Drug Pool | Products (`PRODUCT_CLASS`) | Why It Matters |
|:----------|:--------------------------|:---------------|
| **SGLT2 / GLP1** | `["SGLT2", "GLP1"]` | Primary co-prescribed drug classes with Kerendia. SGLT2 inhibitors (Jardiance, Farxiga) and GLP1 agonists are standard-of-care for T2D+CKD |
| **ACE / ARB** | `["ACE", "ARB"]` | Foundational CKD therapies. Nearly all CKD patients are on ACE inhibitors or ARBs. Broader pool, captures more HCPs |

**The 4×2 Matrix:** Crossing 4 indications with 2 drug pools gives **8 possible HCP sets**:

| | SGLT2/GLP1 | ACE/ARB |
|:--|:-----------|:--------|
| **T2D** | Set 1 | Set 2 |
| **CKD** | Set 3 | Set 4 |
| **HF** | Set 5 | Set 6 |
| **T1D** | Set 7 | Set 8 |

Each set is built by: filtering claims to the indication×drug pool, aggregating NBRX per HCP, then ranking HCPs by prescribing volume.

---

## 4. Data Sources

All data lives in the Databricks catalog `ph-com-ai-us-prod-catalog-2553213839599380`.

### 4.1 Claims Data (Criterion 1 — Core Prescribers)

**Table:** `ph-com-ai-us-prod-catalog-2553213839599380.pace_ker_in_house_schema.lrx_nbrx`

* ~247M rows total; ~104M in a 24-month lookback window
* **Key columns:**
  * `PROVIDER_ID` — IQVIA provider identifier (7-8 digit string)
  * `INDICATION_GROUP_APP1` — compound indication values (use `.contains()`)
  * `PRODUCT_CLASS` — drug class: "SGLT2", "GLP1", "ACE", "ARB", etc.
  * `NBRX` — new-to-brand prescriptions (decimal type)
  * `WEEK_ENDING_DATE` — DATE type (not string)
  * `SPECIALTY_GROUP` — HCP specialty: "PCP", "NEPH", "CARD", "ENDO", "HOS", "OTHERS", etc.
* **Lookback window:** Use a rolling 24-month window ending at the latest available data (e.g., Oct 2024 – Sep 2026)
* **Unique HCPs in lookback:** ~1.36M

### 4.2 Kerendia Prescription Data (Criterion 2 — Kerendia Writers)

**Source:** Snowflake `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FCT_RX` joined with `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRD`

* Query via `Get_Data_Snowflakes()` function (defined in helper notebook `00_connection`)
* Filter: `PRODUCT_GROUP = 'KERENDIA'`, all claim types (PD=paid, RV=reversed, RJ=rejected)
* Full history since launch (July 2021)
* **NBRX logic:** First-ever claim per patient-product = NBRX=1; gap > 365 days between claims = new NBRX
* Roll up to HCP level: `NBRX_KERENDIA_OVERALL`, `TRX_KERENDIA_OVERALL`
* A pre-computed Delta output exists at: `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/dev_folder_3_1/notebook_output/kerendia_nbrx_from_raw_fct_rx`
* **61,583 HCPs** with NBRX_KERENDIA_OVERALL > 0

### 4.3 Specialty Data (Criterion 3 — Specialists)

* **Nephrologists (NEPH):** From `lrx_nbrx` where `SPECIALTY_GROUP = 'NEPH'` → ~15K unique
* **Cardiologists (CARD):** From `lrx_nbrx` where `SPECIALTY_GROUP = 'CARD'` → ~52K unique
* These are clinically relevant specialties for CKD/HF patients regardless of prescribing volume

### 4.4 Targeting / BPT Data (Criterion 4 — Call Plan HCPs)

**Source:** Snowflake `PHCDW.PHCDW_TARGETING.CP_KER_HCP`

* Query: `SELECT DISTINCT BAYER_ID as BH_ID FROM CP_KER_HCP WHERE FF in ('CR1','CR2','CR4','CR5') AND ((UPPER(PRODUCT_1)='KERENDIA') or (UPPER(PRODUCT_2)='KERENDIA'))`
* Returns BH_IDs that must be mapped to PROVIDER_ID via mapping table
* ~78K HCPs on the targeting/BPT list

### 4.5 Call History Data (Criterion 5 — Called HCPs)

**Source:** Snowflake `CPH_DB_PROD.MODEL_V2.FACT_CALL` joined with `CPH_DB_PROD.MODEL_V2.MAP_CUSTOMER_XREF`

* Query: Filter for `STAT='SUBMITTED_VOD'`, `DETL_PROD='KERENDIA'`, `BH_ID NOT LIKE '%BHO%'`, `CALL_DATE >= '2023-01-01'`
* Returns BH_IDs of HCPs called for Kerendia since 2023
* ~153K called HCPs; ~127K overlap with the universe, ~26K outside

### 4.6 ID Mapping Table

**Table:** `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING`

* Columns: `PROVIDER_ID` (IQVIA), `NPI_NUMBER`, `BH_ID` (Bayer)
* ~1.65M rows
* **Critical:** The universe uses `PROVIDER_ID` (IQVIA, 7-8 digits). Snowflake CRM data uses `BH_ID`. Always map through this table.

### 4.7 NBA 3.0 Baseline Universe

**Delta path:** `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/hcp_level_model/dev_folder_3_1/notebook_output/kerendia_nba_3_hcp_model_base_hcp_universe_for_inference`

* 232,965 HCPs (PULL_DT: 2026_10_09)
* Columns: `PROVIDER_ID`, `KERENDIA_FLAG`, `SGLT2_GLP1_FLAG`, `NEPH_FLAG`, `TARGETING_HCP_FLAG`, `BPT_HCP_FLAG`
* Use as a validation baseline — check what % of this universe your new universe covers

### 4.8 Snowflake Connection

To query Snowflake, use the helper function `Get_Data_Snowflakes(query)` defined in:
`/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection`

This uses key-pair authentication with secrets from scope `US_DSAA_PROD_GROUP_Snowflake_Key_Value_Pair`.

---

## 5. Universe Criteria

The universe is built by **unioning** HCPs from multiple independent criteria:

### C1: Core Prescribers (Claims-Based)

**Objective:** Identify high-volume prescribers of relevant drug classes across relevant indications.

**Method:**
1. For each indication×drug pool combination (up to 8 sets), filter `lrx_nbrx` to the 24-month lookback window
2. Aggregate `sum(NBRX)` per `PROVIDER_ID`
3. Rank HCPs by volume (optional: use cumulative volume-based deciling where each decile ≈ 10% of total NBRX)
4. Select HCPs above a volume threshold (e.g., decile ≥ 2 = top 90% of volume)
5. Union the selected sets to form C1

**Key considerations:**
* **Core sets** are T2D×SGLT2/GLP1 (Set 1) and CKD×SGLT2/GLP1 (Set 3) — these are most aligned with Kerendia's prescriber profile
* Deciling is **optional** — you may use any volume-based threshold that maximizes writer capture within the size budget
* The cutoff directly trades off universe size vs writer capture
* If using deciles, use cumulative volume ascending with tiebreaker: `Window.orderBy(asc("TOTAL_NBRX"), asc("PROVIDER_ID"))`

### C2: Kerendia Writers

**Objective:** Ensure every HCP who has ever written a Kerendia prescription is in the universe.

**Method:** Load the pre-computed Delta at the path in Section 4.2. Select `PROVIDER_ID` where `NBRX_KERENDIA_OVERALL > 0`.

**Count:** 61,583 HCPs. This criterion guarantees 100% writer capture by definition.

### C3: Specialists (Nephrologists + Cardiologists)

**Objective:** Include clinically relevant specialists regardless of their prescribing volume.

**Method:** From `lrx_nbrx`, select distinct `PROVIDER_ID` where `SPECIALTY_GROUP` is "NEPH" or "CARD".

**Rationale:** Nephrologists and cardiologists treat CKD/HF patients and are key influencers even if their individual claim volumes are low.

### C4: Targeting / BPT HCPs

**Objective:** Include HCPs on the commercial targeting or Best Practice Targeting lists.

**Method:** Query Snowflake `CP_KER_HCP` (see Section 4.4), map BH_ID → PROVIDER_ID.

**Rationale:** These are commercially prioritized HCPs who may not appear in claims-based criteria.

### C5: Called HCPs (Optional)

**Objective:** Include HCPs who have been called/detailed for Kerendia by the sales team.

**Method:** Query Snowflake `FACT_CALL` (see Section 4.5) for calls since 2023-01-01, map BH_ID → PROVIDER_ID.

**Rationale:** Maintains continuity between sales outreach and model scoring. Only add if needed to recover commercially engaged HCPs not captured by C1–C4.

---

## 6. Objective & Constraints

### Primary Objective

**Maximize Kerendia writer capture** — of the 61,583 Kerendia writers, maximize the number that fall within the universe.

### Constraints

1. **Universe size ≤ 300,000 HCPs** after applying all criteria (C1 ∪ C2 ∪ C3 ∪ C4 ∪ C5)
2. **C2 is mandatory** — all 61,583 Kerendia writers must be in the universe (100% capture by construction)
3. **C3 is mandatory** — all NEPH and CARD specialists must be included
4. **C1 threshold is the tunable lever** — adjust which sets to include and what volume cutoff to use
5. C4 and C5 are additive — include them if size budget allows

### Validation Metrics

After building the universe, validate against these independent benchmarks:

| Metric | Definition | Baseline Count |
|:-------|:-----------|---------------:|
| **M1** | NBA 3.0 `KERENDIA_FLAG` = 1 (from the baseline universe) | 77,972 |
| **M2** | `lrx_nbrx` Kerendia paid NBRX > 0, 24-month lookback | ~40,112 |
| **M3** | LAAD V6 Kerendia TRX > 0, 24-month lookback | ~67,835 |
| **NBA 3.0 overlap** | % of the 232,965 NBA 3.0 HCPs captured by new universe | target ≥ 90% |

---

## 7. Hotspot Analysis: Finding Missed Writers

After building the universe, **profile the Kerendia writers who are NOT captured by C1 alone** (before adding C2). This reveals where the claims-based approach falls short:

### Questions to Answer

1. **Which sets are they in?** — Are they in D1 (lowest decile) of the core sets? In non-core sets (ACE/ARB, HF, T1D)? Or not in any of the 8 sets at all?
2. **What is their specialty?** — PCP, NEPH, CARD, ENDO, or other?
3. **What is their claim type?** — Are they paid-only writers, or do they have reversed/rejected claims only?
4. **What is their Kerendia volume?** — How many NBRX? Are they single-script writers or repeat prescribers?
5. **Are they in NBA 3.0?** — Did the prior model already include them?
6. **How are they recovered?** — Which criterion (C2, C3, C4, C5) captures them?

### Expected Patterns

* ~64% of missed writers sit in D1 of the core sets (low-volume SGLT2/GLP1 prescribers)
* ~18% are not in any of the 8 decile sets (Kerendia-only prescribers with no SGLT2/GLP1/ACE/ARB claims)
* ~68% are single-script writers (NBRX = 1)
* ~44% have non-paid claims only (reversed/rejected) — invisible to paid-only definitions
* C2 recovers ALL missed writers by definition
* C3 recovers ~3K NEPH/CARD writers who are also outside the decile sets

---

## 8. Technical Notes

### ID Systems

* **PROVIDER_ID** (IQVIA) — 7-8 digit string, used in `lrx_nbrx` and the universe output
* **BH_ID** (Bayer) — format "BH12345678", used in Snowflake CRM tables (FACT_CALL, CP_KER_HCP)
* **NPI_NUMBER** — 10-digit national provider identifier
* Always map between systems using `SOURCE_PROVIDER_BHID_NPI_MAPPING`

### Common Pitfalls

* `INDICATION_GROUP_APP1` has compound values → use `.contains()` not `==`
* `WEEK_ENDING_DATE` in `lrx_nbrx` is DATE type; in LAAD V6 it's STRING (YYYYMMDD)
* `min()`/`sum()` in PySpark are intercepted by PySpark functions → use `builtins.min`/`builtins.sum` for Python-native operations
* Window functions with no partition clause cause a single-partition warning (acceptable for decile calculation)
* Snowflake queries require `Get_Data_Snowflakes()` — do NOT use Databricks tables for CRM/targeting data

### Output Format

The final universe should be a DataFrame (or Delta table) with at minimum:

* `PROVIDER_ID` — unique HCP identifier
* `C1_FLAG` — 1 if HCP entered through Criterion 1
* `C2_FLAG` — 1 if HCP is a Kerendia writer
* `C3_FLAG` — 1 if HCP entered through Specialty
* `C4_FLAG` — 1 if HCP is on Targeting/BPT list
* `C5_FLAG` — 1 if HCP was called for Kerendia (since 2023)
* `SPECIALTY_GROUP` — from lrx_nbrx

---

## 9. Step-by-Step Workflow

1. **Load data:** Read `lrx_nbrx`, filter to 24-month lookback
2. **Build C1:** For each indication×drug pool, aggregate NBRX per HCP, apply volume threshold, union selected sets
3. **Build C2:** Load Kerendia NBRX Delta, filter NBRX > 0
4. **Build C3:** Extract NEPH + CARD from lrx_nbrx
5. **Build C4:** Query Snowflake CP_KER_HCP, map BH_ID → PROVIDER_ID
6. **Build C5 (optional):** Query Snowflake FACT_CALL since 2023, map BH_ID → PROVIDER_ID
7. **Union all:** `universe = C1 ∪ C2 ∪ C3 ∪ C4 ∪ C5`
8. **Check size:** Must be ≤ 300,000. If over, tighten C1 threshold or drop C5
9. **Validate:** Compute overlap with NBA 3.0, M1, M2, M3 metrics
10. **Hotspot analysis:** Profile C2 writers not in C1 — by set membership, specialty, claim type, volume
11. **Report:** Produce a summary with universe size, writer capture %, validation metrics, and hotspot findings

---

## 10. Reference: NBA 3.1 v6 Achieved Results

For calibration, here are the numbers achieved by the NBA 3.1 v6 build:

| Criterion | Count |
|:----------|------:|
| C1 (Core D2+, Set1 ∪ Set3) | 242,868 |
| C2 (Kerendia Writers) | 61,583 |
| C3 (NEPH + CARD) | 66,714 |
| C4 (CP_KER_HCP Targeting) | 78,798 |
| **Total (C1+C2+C3+C4)** | **294,244** |
| NBA 3.0 overlap | 220,017 (94.4%) |
| M1 capture | 71,795 / 77,972 (92.1%) |
| Writer capture (C2) | 61,583 / 61,583 (100%) |

Your build should aim for similar or better results while staying under 300K.
