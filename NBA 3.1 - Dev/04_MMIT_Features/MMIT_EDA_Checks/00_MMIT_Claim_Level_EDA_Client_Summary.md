# MMIT Market Access EDA: Kerendia Claim-Level Findings

**Audience:** Bayer Kerendia NBA 3.x stakeholders
**Scope:** Kerendia (MedId 607231) IQVIA LAAD claims, Sep 2024 to Aug 2026, joined to MMIT formulary data
**Objective:** Check how reliable the current MMIT access features are, and find new access signals that can drive HCP next-best-action recommendations.

---

## 1. Executive summary

| # | Finding | Implication |
|---|---|---|
| 1 | **53.2% of Kerendia claims do not match MMIT. 90% of these unmatched claims come from months before Oct 2025, when MMIT has no full feed.** Inside the covered window (Oct 2025 to Aug 2026), the unmatched rate is only **10.5%**. | The unmatched rate is mainly a data-history gap, not a join defect. MMIT features are reliable only from 202510 onward. |
| 2 | Kerendia rows repeat across 3 therapeutic classes, but **status is identical across classes (0 conflicts)**. | The current deduplication is safe. Filtering to the CKD class cuts the rows scanned by about 3x. |
| 3 | **83% of matched claims have restriction detail and about 51% have structured PA/ST detail.** Bayer HPM covers 100% of claims from Jan 2026. | Enough coverage to build the new restriction and HPM features. Missing values follow a pattern (an unrestricted drug has no PA/ST row), so they can be encoded explicitly. |
| 4 | **72% of claims on "Preferred" formularies carry a quantity limit only.** PA or step therapy is almost absent. | Splitting the combined "PA/ST" label into separate PA, ST and QL flags removes noise from the current access buckets. |
| 5 | Bayer's CKD HPM status **never contradicts** the MMIT rollup. It adds the type of restriction (PA to label, step, PA+, APR). | HPM is a low-risk enrichment of the current feature, not a replacement. |
| 6 | Kerendia access is **improving** (about 2 improvements for every deterioration). **Farxiga deteriorated on about 1 in 3 Kerendia claims in Jul to Aug 2026.** | Competitor access events matter as signals, and rolling 3-month windows are needed. |
| 7 | **Restriction features are the most discriminating access signals, but in the inverse direction** (AUC 0.38 to 0.45 within Medium/High restriction HCPs). `share_commercial` is the strongest positive predictor (AUC 0.57 in High). `share_step_requires_sglt2` (pooled AUC 0.575) loses most signal within terciles, inflated by HCP volume. Current coarse access buckets remain close to random (AUC 0.47 to 0.55). | Include the separate PA / ST / QL flags as inverse-signal features alongside `share_commercial`. Control for HCP volume: the tercile NBRx rates (3% Low to 26% High) are confounded with it. |

---

## 2. Data used

### 2.1 Claims (Snowflake, through `Get_Data_Snowflakes`)

| Table | Role |
|---|---|
| `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FCT_RX` | Kerendia prescription claims: CLAIM_ID, PROVIDER_ID, PATIENT_ID, SVC_DT, PAYER_PLAN_ID |
| `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_DIM_PRD` | NDC to product (PRODUCT_GROUP = 'KERENDIA') |

Population: **2,585,752 Kerendia claims**, 202409 to 202608, one row per CLAIM_ID.

### 2.2 MMIT market access (`ph-com-ai-us-prod-catalog-2553213839599380`.market_access)

| Table | Role in this analysis |
|---|---|
| `bronze_iqvia_bridge` | IQVIA PAYER_PLAN_ID to MMIT OrgId |
| `silver_plan_dim` (current rows) | Plan to FormularyId, plus Channel, PlanType, PBM, BenefitDesign. Used instead of `bronze_plan_details`, which stops at 202602. |
| `bronze_states` | Lives per OrgId and month. Used to choose the **winning plan** (the one with the most lives) per payer and month. |
| `bronze_statuses` | Formulary status for Kerendia and its SGLT2 competitors (Jardiance, Farxiga, Invokana, Steglatro) |
| `bronze_restrictions` | PA / ST / QL restriction codes |
| `bronze_pa_v2` | Structured CKD prior authorization, including the appropriate/restrictive (ARS) rating |
| `bronze_st` | CKD step therapy, including the required step products |
| `bronze_pa_udf` | PA criteria detail (coverage check) |
| `bronze_derived_fields` | Bayer-specific `Bayer_ChronicKidneyDisease_HPM_Pharm` status |

### 2.3 Join path (same as the production feature logic)

Claim (PAYER_PLAN_ID, claim month) -> `bronze_iqvia_bridge` (OrgId) -> `silver_plan_dim` (FormularyId) -> the winning plan by lives in `bronze_states` -> drug status in `bronze_statuses`. The winning **OrgId and FormularyId** are kept so that every new feature table joins on `FormularyId + Period`. The claim row count was checked before and after the join (**PASS**, no fan-out).

---

## 3. Analyses performed

| Check | Question | Grain |
|---|---|---|
| 1. Unmatched rate | Why do 53% of claims have no MMIT match? | Claim x month |
| 2. Therapeutic class dedup | Do the repeated class rows disagree? | Formulary x drug x period |
| 3. Feature-table coverage | How often do the PA / ST / UDF / HPM / restriction tables have a row for the claim's formulary? | Formulary and claim-weighted |
| 4. Bayer HPM vs current access | Is Bayer HPM consistent with `kerendia_access`, and does it add information? | Formulary and claim-weighted |
| 5. Status change rate | Do formulary changes happen often enough to support momentum features? | Formulary x month, claim exposure |
| 6. Univariate lift | Do the candidate features predict next-month Kerendia NBRx? | HCP x month (289K rows) |
| 7. Stratified AUC by restricted-claim tercile | Does feature signal change for HCPs with High / Medium / Low restricted-claim volume? | HCP x month, within terciles (59K HCPs) |

---

## 4. Key results

### 4.1 MMIT matching is limited by history, not by the join

| Window | Claims | Unmatched | Unmatched % |
|---|---|---|---|
| 202409 - 202509 (no full MMIT feed) | 1,233,639 | 1,233,639 | 100.0% |
| 202510 - 202608 (MMIT covered) | 1,352,113 | 142,496 | **10.5%** |
| **Total** | **2,585,752** | **1,376,135** | **53.2%** |

* Full MMIT status loads start in **202510**. 202506 to 202508 hold a 31-drug pilot without Kerendia, and 202509 is missing.
* Inside the covered window, the unmatched claims split into **No payer match (6.5%)** and **No Kerendia status row on the formulary (4.1%)**.
* The "no status row" share rises from 0% to about **7% from 202603**, when the number of Kerendia formularies drops from 2,133 to 2,036. Ask MMIT to check whether formularies were dropped from the feed.
* About 33% of the unmatched in-window claims come from 5 payer IDs (for example 0002870169, 8888880001, 7000010001). Some of these look like placeholder IDs (8888880001, 4444449999), which should be reviewed with IQVIA.

### 4.2 Data structure is sound

* Kerendia repeats across the CKD, CHF and Cardiovascular Agents classes. **0 of about 98K keys conflict**, so the current dedup returns correct values.
* Jardiance has two MedIds, which disagree on only **0.06%** of formulary-periods. Using the CKD listing (582254) alone is sufficient.
* The PA, ST and UDF tables **do differ by indication** (CKD vs heart failure), so always filter to `IndicationName = 'Chronic Kidney Disease'`.

### 4.3 Feature tables have enough coverage

Claim-weighted coverage (1,209,617 matched claims, 202510-202608):

| Source | Coverage of matched claims |
|---|---|
| bronze_restrictions (PA / ST / QL codes) | **83.4%** |
| Bayer CKD HPM (derived fields) | 72.4% overall, **100% from 202601** |
| bronze_pa_v2 / bronze_pa_udf (CKD PA) | 50.7% |
| bronze_st (CKD step therapy) | 46.4% |

* Missing values follow a pattern. PA/ST rows exist only when the drug is restricted, so for unrestricted formularies a missing value means "no PA/step".
* 30-40% of formularies labeled "(PA/ST)" have no structured PA/ST row. These need an explicit `Unknown` level, or text parsing of the restriction detail.
* For claims on **Preferred** formularies (348,802), **71.6% have a restriction row, almost all of them quantity limits only** (PA 0.2%, ST ~0%).

### 4.4 Bayer HPM refines the current access label

* Formulary level (202608): Not Covered maps 1:1 to `Medical Exception`, and Not Listed maps 1:1 to `Unknown`. No HPM value contradicts the restricted/unrestricted split.
* Within `Covered_with_PA_ST` (67% of formularies), HPM separates **PA to Label (481)**, **Step (401)**, **PA Unspecified (343)**, **APR (148)** and **PA+ (11)**.
* **119 formularies are "Covered" in MMIT but "Preferred - Unrestricted" in Bayer HPM.** Bayer's view is more favorable on these plans. Agree with the client which source defines "Preferred".
* Claim level (876,043 claims, 202601-202608): most volume is in `Covered_with_PA_ST`, refined into PA to Label (8.8%), APR (4.5%), PA Unspecified (2.0%) and Step (1.7%).
* **Caveat:** 73% of claims fall into an "Other" HPM group in the claim-level mapping, even though the formulary-level values map cleanly. The value-to-group string mapping must be fixed before the HPM features are final. Until then, the HPM lift results in 4.6 understate the HPM signal.

### 4.5 Access momentum and competitor events

| Drug | Formularies with at least 1 status change (11 months) |
|---|---|
| Kerendia | 9.2% |
| Jardiance | 9.3% |
| **Farxiga** | **32.5%** |
| Invokana | 5.8% |
| Steglatro | 4.5% |

* Kerendia: **152 improvements vs 80 deteriorations**. Changes peak at the January plan-year reset (202601-202602).
* **Farxiga deteriorated sharply from 202604 to 202607** (304 formularies in 202607 alone). This is consistent with generic dapagliflozin entering the market (to be confirmed). At claim level, **33% of Kerendia claims in 202607-202608 sit on a formulary where Farxiga worsened in the last 3 months**.
* Kerendia's own change exposure is sparse (0.7-2.9% of claims per month). Rolling L3M/L6M windows are required, because single-month flags are mostly zero.

### 4.6 Predictive signal on next-month NBRx (HCP x month)

Base: 289,232 HCP-months, 202510-202607. Next-month NBRx rate: **17.65%**. HCPs stratified into terciles by restricted-claim count (PA / ST / QL on the winning formulary): Low (0-2 restricted claims, 23,604 HCPs), Medium (3-8, 16,154), High (9+, 19,634).

**Stratified AUC (restriction tercile):**

| Feature | AUC overall | AUC Low | AUC Medium | AUC High | Read |
|---|---|---|---|---|---|
| share_any_restriction | 0.431 | 0.451 | **0.378** | 0.391 | Strongest by distance from 0.5, inverse: more restrictions predict fewer new patients |
| share_has_QL | 0.450 | 0.458 | **0.392** | 0.412 | QL-specific inverse signal, concentrated in Medium tercile |
| share_commercial | **0.579** | 0.508 | 0.530 | **0.567** | Most robust positive predictor; strengthens in High tercile |
| share_kerendia_Covered | 0.551 | 0.513 | 0.544 | 0.566 | Current feature, strengthens in High |
| share_has_PA | 0.497 | 0.472 | **0.420** | 0.442 | Inverse, moderate in Medium/High |
| share_has_ST | 0.530 | 0.482 | **0.445** | 0.476 | Inverse, moderate in Medium/High |
| share_step_requires_sglt2 | 0.575 | 0.480 | 0.466 | 0.528 | Loses most signal within terciles; pooled AUC inflated by volume |
| share_ckd_pa_ars_R | 0.541 | 0.484 | 0.450 | 0.486 | Inverse, moderate in Medium/High |
| HPM groups | 0.507-0.512 | 0.505-0.529 | 0.504-0.516 | 0.506-0.509 | Flat across terciles |
| Current coarse buckets | 0.47-0.55 | 0.47-0.51 | 0.42-0.54 | 0.43-0.57 | Wide range; some worsen in Medium |

Tercile NBRx rates: Low **3.07%**, Medium **6.06%**, High **26.27%**. The High tercile rate is driven partly by HCP volume (median 27 total claims vs 2 in Low).

* **Restriction features are the most discriminating access signals**, but they work in the inverse direction. `share_any_restriction` (AUC 0.38 in Medium) and `share_has_QL` (AUC 0.39 in Medium) carry the strongest separation (distance of AUC from 0.5). This makes clinical sense: more restrictions mean more barriers to new prescribing. The model should include these and let the learner use their inverse signal.
* **`share_commercial` is the most stable positive predictor** (AUC 0.51 to 0.57 across terciles). It strengthens in the High restriction tercile, suggesting that commercial vs Medicare channel mix determines whether a PA or step is successfully navigated.
* **`share_step_requires_sglt2` loses most of its within-tercile signal** (0.47-0.53 vs 0.575 pooled). Its pooled AUC was inflated by correlation with HCP volume. It retains moderate signal only in the High tercile.
* **PA and ST type flags add moderate inverse discrimination inside the Medium and High terciles** (`share_has_PA` 0.42-0.44, `share_has_ST` 0.44-0.48). Knowing the specific restriction type helps the model within HCPs who already face restrictions.
* **HPM features are flat across terciles** (AUC 0.50-0.53), adding little within any restriction stratum. This may improve once the HPM value-to-group mapping is fixed (see Check 4).
* Access is a **supporting** signal. Best univariate AUC is about 0.58; it must be combined with Rx, promotional and HCP features in the multivariate model.

---

## 5. Recommendations

**Data and pipeline**
1. Use MMIT features only for `claim_month >= 202510`. Flag earlier months (`mmit_available = 0`), or carry 202510 values back with an `mmit_status_imputed` flag.
2. Ask MMIT to backfill 202509 and pre-202510 loads, and to explain the drop in formularies in 202603.
3. Replace `bronze_plan_details` with `silver_plan_dim` for plan attributes.
4. Filter statuses to the CKD class, and filter PA/ST/UDF to the CKD indication.
5. Review the payer IDs that look like placeholders (8888880001, 4444449999) with IQVIA.

**New features to add (priority)**

| Priority | Feature | Source |
|---|---|---|
| High | `has_PA` / `has_ST` / `has_QL` (separate flags), `any_restriction` | bronze_restrictions (inverse signal; strongest by distance from 0.5 in the stratified check) |
| High | `step_requires_sglt2` (moderate within High tercile), `ckd_pa_ars_restrictive` | bronze_st, bronze_pa_v2 |
| High | `plan_channel`, `pbm_name` (top PBMs + Other) | silver_plan_dim |
| High | `bayer_ckd_hpm_group` + `hpm_is_preferred`, after the mapping fix | bronze_derived_fields |
| Medium | `kerendia_status_improved/worsened_l3m`, `farxiga/jardiance_worsened_l3m` | bronze_statuses / silver_status_changes |
| Medium | `kerendia_tier` from RawStatus, `kerendia_vs_sglt2_relative_access` | bronze_statuses |

**Open decisions for the client**
* Which source defines "Preferred": MMIT rollup or Bayer HPM? They disagree on 119 formularies.
* Meaning of the HPM code `APR`.
* Confirm that the Farxiga deterioration is driven by the generic and decide whether it should be treated as a market event.

---

## 6. Supporting detail

* `01_Unmatched_Rate_by_Claim_Month.md`: monthly unmatched breakdown and top payers
* `02_TherapeuticClass_Dedup.md`: class duplication and Jardiance dual MedId
* `03_Feature_Table_Coverage.md`: coverage by period and status
* `04_Bayer_HPM_vs_Kerendia_Access.md`: HPM cross-tabs
* `05_Univariate_Lift_on_NBRx.md`: full lift and AUC table
* `06_Status_Change_Rate.md`: monthly change counts and claim exposure
* Notebook `MMIT_EDA_Claim_Level_Checks`: reproducible code for all claim-level checks
