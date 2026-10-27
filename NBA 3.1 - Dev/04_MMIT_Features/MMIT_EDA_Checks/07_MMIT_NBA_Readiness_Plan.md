# MMIT to NBA 3.1: Data Science Readiness Plan

**Purpose:** Replace the DRG formulary features in the current NBA 3.0 model with MMIT-based market access features for NBA 3.1, building on EDA Checks 00-06.
**Baseline model:** MLflow run `f583bcbc9d56477fae983d44c16f8c70` ("LightGBM with Tweedie - Best Model - Trained on Complete Data", 752 features, Tweedie objective).

---

## 1. What the DRG features contributed in the current model

From `Shap_Importances.csv` on the baseline run:

| Group | Features | Share of total mean abs SHAP | Best rank |
|---|---|---|---|
| `PCT_PLANS_*` (DRG formulary, verified in Section 1.1) | 44 | **4.7%** | 25 |
| of which Kerendia | 18 | 2.8% | 25 (`PCT_PLANS_KERENDIA_COVERED_LOOKBACK`), 28 (`..._UNRESTRICTED`) |
| of which Jardiance | 13 | 0.95% | 152 |
| of which Farxiga | 13 | 0.93% | 189 |
| LAAD reject / pay-type features (kept, not DRG) | ~15 | ~2.5% | 11 (`RUNNING_TOTAL_HCP_RX_REJECTED_KERENDIA_CLAIMS`) |

Readings:
* Formulary access was a supporting signal (about 5% of SHAP), consistent with EDA Check 5 (best univariate AUC around 0.58). The goal is to recover and modestly improve this share, not to make access a top driver.
* LAAD reject and pay-type features already carry part of the access signal and stay in the model. MMIT features must be tested for **incremental** value on top of them.

### 1.1 How `PCT_PLANS_*` was built in NBA 3.0 (verified)

Source notebooks: `NBA 3.0 Dev/08_HCP_Level_Model/03_Feature_Engineering/02_Other_Features - DRG, Claim-related/` `2.1_DRG_Features_Kerendia`, `2.2_DRG_Features_Farxiga`, `2.3_DRG_Features_Jardiance` (same logic, one drug per notebook).

| Step | Logic |
|---|---|
| 1. Plan universe per HCP | **All paid LAAD Rx claims** of the HCP (`STG_CAR_IQV_LAAD_FCT_RX` inner join `STG_CAR_IQV_LAAD_DIM_PRD` on NDC with **no product filter**, `claim_type = 'PD'`). Not limited to Kerendia, and not limited to SGLT2: every product in the LAAD subscription contributes its `PAYER_PLAN_ID`. |
| 2. HCP filter | Restricted to the NBA HCP universe (`kerendia_nba_3_hcp_model_base_hcp_universe_v5`, 221,723 HCPs). |
| 3. Unit | **Distinct `PAYER_PLAN_ID` per HCP x month** (one vote per plan, not weighted by claim count or lives). |
| 4. Payer to formulary | `PAYER_PLAN_ID` -> DRG plan via the MASA mapping file `MASA_MA_Kerendia_IQVIA_Access_Mapping_at_Plan_Level_01_28_25.xlsb` (4,335 rows); DRG status from `CPH_DB_PROD.ANALYTICS_V2.ANLT_DRG_FRMLRY_HIST` by `Data_Month`. Inner join, so plans without a DRG mapping are dropped from both numerator and denominator. |
| 5. Status flags per plan-month | Two DRG taxonomies, one flag each (max over the DRG plans mapped to the payer plan, so flags are not mutually exclusive): `PHARMACY_ST_CRITERIA` -> `unrestricted`, `covered_pa_wo_st`, `covered_st_or_pa_st`, `not_covered_st`, `unspecified`; `DUAL_COVERAGE_NOMENCLATURE` -> `preferred`, `covered`, `not_preferred`, `not_covered`, `specialty`. |
| 6. Current-month feature | `pct_plans_<drug>_<flag>` = sum of flag over the HCP's plans in month / distinct plans in month. |
| 7. `_LOOKBACK` feature | 12-row rolling window per HCP: sum of flags over the last 12 months / sum of monthly plan counts over the same 12 months. |
| 8. Grain | Skeleton HCP x 47 months, then joined to the 26 cohorts (C01 = 2023-02 ...) by `SVC_DT_M = LOOKBACK_END_DATE` month. Null when the HCP has no mapped plan in the month. |

Static vs dynamic parts (verified Oct 23 2026):
* **Static:** only the crosswalk `PAYER_PLAN_ID -> DRG_PLAN_ID` from the MASA file (Jan 2025). Its `KERENDIA ACCESS (FINGERTIP)` column (Bayer's own label, e.g. `PREFERRED, PRIOR AUTH (APR)`) is **not used** by the NBA 3.0 notebooks.
* **Dynamic:** the status itself comes from `ANLT_DRG_FRMLRY_HIST` for each month. On mapped DRG plans, Kerendia status changed month over month in 7.8% of plan-months in 2022, 2.5% in 2023, 1.4% in 2024 and 1.5% in 2025; 26% of plans differ between 202301 and 202511.
* Residual staleness from the static crosswalk: payer plans created or re-pointed after Jan 2025 are unmapped (3.5% DRG-only vs 12% MMIT-only paid claims in the overlap), and pre-2025 months use the 2025 plan mapping.
* Bayer HPM (`Bayer_ChronicKidneyDisease_HPM_Pharm`, MMIT derived field, monthly from 202601) uses the same Bayer taxonomy as the FINGERTIP label (both have the `APR` code), but it is recomputed every month per formulary.

Implications for MMIT:
* The DRG features describe the **access landscape of the HCP's whole book of business**, evaluated for each drug, not the plans on which Kerendia was actually dispensed. This is why they exist for non-writers.
* EDA Checks 1-6 were built on **Kerendia claims and a claim-weighted winning formulary**. That is a different (complementary) feature. Parity features must reproduce steps 1-7 with MMIT instead of DRG.
* LAAD reject features stay separate; the DRG features used paid claims only.

---

## 2. What a data scientist needs to understand about MMIT before modeling

### 2.1 Grain, keys and time
| Topic | What to know | Source |
|---|---|---|
| Natural key | `FormularyId x MedId x TherapeuticClass x Period x feed_date`. Class rows are identical for target drugs, so filter to CKD class. | Check 2 |
| Indication | PA / ST / UDF differ by indication. Always filter `IndicationName = 'Chronic Kidney Disease'`. | Check 2 |
| Three time fields | `Period` (monthly snapshot month), `feed_date` (weekly delivery), `ProcessingDate` (MMIT processing). Decide which is the "as-of" date for point-in-time joins. | Bronze |
| Weekly vs monthly | Status is monthly per `Period`, but the weekly feeds revise it. `silver_status_changes` catches intra-month changes the monthly snapshot misses. | Check 6 |
| Point-in-time rule | For a feature as of month t, use only feeds with `feed_date` before the end of t. Never use a later feed's restatement of month t (leakage). | To implement |

### 2.2 History and coverage limits
* Full feed only from **202510** (Check 1). 202509 is missing; 202506-202508 are a 31-drug pilot without Kerendia.
* Bayer HPM (derived fields) only from **202601**. L3M change features complete from 202601, L6M from 202604.
* Inside the window, 10.5% of Kerendia claims are unmatched (6.5% no payer, 4.1% no Kerendia row; the latter jumps to ~7% from 202603 when the formulary count drops from 2,133 to 2,036).
* MMIT alone is short, but **DRG (202107-202511) + MMIT (from 202510) together cover the full training window**, with a 2-month overlap (202510-202511) for calibration. See Section 4.

### 2.3 Semantics to align with the client
* Which source defines "Preferred": MMIT rollup or Bayer HPM (they disagree on 119 formularies).
* Meaning of HPM `APR`.
* Whether the Farxiga deterioration (202604-202607) is the generic dapagliflozin event, and whether to treat it as a market event feature.
* HPM value-to-group mapping bug (73% "Other" at claim level). Fix before any HPM conclusion.

### 2.4 Missingness is structural
* No PA / ST row usually means "not restricted" when status is unrestricted. Encode as `No_PA` / `No_Step`; otherwise `Unknown`.
* 30-40% of `(PA/ST)` formularies have no structured PA/ST row. Use `RestrictionDetail` text as fallback, or an explicit `Unknown` level.

### 2.5 Population: the EDA covers Kerendia writers, the model needs the full book of business
* All EDA so far is on **HCPs with at least one Kerendia claim** (59K HCPs), using the plans of Kerendia claims. The NBA universe is **221,723 HCPs**, and the DRG features were built on **all paid LAAD claims** of each HCP (Section 1.1).
* The MMIT replacement must therefore be built on the HCP's whole plan mix:
  1. **Primary:** all paid LAAD claims -> `PAYER_PLAN_ID` per HCP x month -> `bronze_iqvia_bridge` -> formulary -> Kerendia / Jardiance / Farxiga status, **weighted by patients** (each LAAD patient seen by the HCP in the month counts once, split equally across that patient's plans). Patient weighting replaces the NBA 3.0 distinct-plan count (Section 3.1).
  2. **Variants to test:** NBA 3.0 distinct-plan count (parity reference); claim-weighted; plans restricted to the relevant patient basket (CKD / T2D / SGLT2 / ACE-ARB patients) instead of all products; Kerendia-claim plans only (the EDA version).
  3. **Geographic fallback** for HCPs with no mapped plan: lives-weighted access in the HCP's ZIP / CBSA / state from `bronze_zip_code`, `bronze_cbsas`, `bronze_states`, with `access_source = plans / geo / none`.
* Re-run the coverage, unmatched-rate and lift checks (Checks 1, 3, 5) on this all-claims plan universe. All-product plans include many payers not seen on Kerendia claims, so the payer match rate and the payer-to-formulary rule (winning plan by lives vs all formularies of the payer) need to be re-checked.

---

## 3. Feature design (Gold layer, HCP x month)

Keep a **plan-month access table** at `FormularyId x MedId x month` (point-in-time), then aggregate to HCP x month through claim, panel and geography weights. This keeps one source of truth and lets the same access table serve NBA, OE and BI.

| Priority | Family | Example features | Source | Notes |
|---|---|---|---|---|
| P0 | **DRG parity** | `PCT_PLANS_<DRUG>_{UNRESTRICTED, COVERED_PA_WO_ST, COVERED_ST_OR_PA_ST, NOT_COVERED_ST, UNSPECIFIED, PREFERRED, COVERED, NOT_PREFERRED, NOT_COVERED, SPECIALTY}` + `_LOOKBACK` for Kerendia / Jardiance / Farxiga | All paid LAAD claims -> bridge -> bronze_statuses + bronze_restrictions | Patient-weighted (Section 3.1); NBA 3.0 distinct-plan version kept as the parity reference. 12-month lookback as Section 1.1. Status mapping below |
| P1 | Restriction type | `share_has_PA`, `share_has_ST`, `share_has_QL`, `share_any_restriction`, `share_step_requires_sglt2`, `share_ckd_pa_ars_R` | restrictions, st, pa_v2 | Inverse signal; strongest in Check 5 |
| P1 | Plan mix | `share_commercial`, `share_medicare`, `share_medicaid`, top PBM shares | silver_plan_dim | `share_commercial` most stable positive signal |
| P1 | Relative access | `kerendia_minus_jardiance_rank`, `share_kerendia_worse_than_sglt2` | statuses | Kerendia is add-on to SGLT2; relative access matters |
| P2 | Bayer HPM | `hpm_group`, `hpm_is_preferred` | derived_fields | After mapping fix; from 202601 only |
| P2 | Momentum / events | `kerendia_improved_l3m`, `kerendia_worsened_l3m`, `farxiga_worsened_l3m`, `months_since_status_change`, `tier_changed_l3m` | silver_status_changes | Sparse; use L3M / L6M |
| P2 | PA burden | criteria count, age / duration / lab (eGFR, UACR) requirements | pa_v2, pa_udf | Links to Quest lab features already in the model |
| P3 | Geography | lives-weighted access in ZIP / CBSA | zip_code, cbsas, states | Fallback for non-writers |
| P3 | Medical benefit | Medical coverage flags | Medical, MedicalPA | Low relevance for oral Kerendia; deprioritize |

DRG to MMIT status mapping for P0 (to validate in the parity check):

| DRG flag | MMIT derivation |
|---|---|
| `preferred` / `covered` / `not_covered` / `specialty` | `UniversalStatusRollup` tier prefix (Preferred, Covered, Not Covered, Specialty); decide how `Not Listed` is treated |
| `not_preferred` | No direct rollup value; derive from `RawStatus` tier (e.g. non-preferred brand tier) |
| `unrestricted` | Rollup without `(PA/ST)` and no PA / ST row in `bronze_restrictions` (QL-only counts as unrestricted, as in DRG) |
| `covered_pa_wo_st` | PA restriction present, no ST |
| `covered_st_or_pa_st` | ST present (with or without PA) |
| `not_covered_st` | Rollup `Not Covered` |
| `unspecified` | `(PA/ST)` rollup with no structured restriction code |

The P1-P3 features should also be computed on the all-claims plan universe (primary) and, where useful, on the Kerendia-claim plans (secondary).

### 3.1 Weighting unit: plans, claims or patients (evaluated Oct 2026)

Market Access reads MMIT on a **patient** basis. None of the current metrics use patients:

| Where | Unit used today |
|---|---|
| NBA 3.0 `PCT_PLANS_*` (Section 1.1) | Distinct `PAYER_PLAN_ID` per HCP x month: every plan counts once, whether it covers 1 or 300 of the HCP's patients |
| EDA Checks 1-6, client walkthrough (`share_*`, `kerendia_<category>` counters) | Kerendia claims |
| DRG-MMIT overlap agreement (4.2a) | All paid LAAD claims |

**Test.** For DRG Kerendia status in feature months 202503-202505, the same four shares were built three ways on all paid LAAD claims: distinct plans (NBA 3.0), claims, and patients (each patient counts once per HCP-month, split across that patient's plans). Population: 433K HCPs per month with a paid Kerendia / Jardiance / Farxiga claim in H1 2025 (a proxy for the 221,723-HCP universe). Outcome: next-month Kerendia NBRx (first Kerendia claim since 2023-01; rate 1.29%). AUC within terciles of HCP patient volume removes the size effect.

| Share | Correlation, plan vs patient | Correlation, claim vs patient | AUC within volume terciles (avg distance from 0.5): plan / claim / patient | Month-over-month change within HCP (pp): plan / claim / patient |
|---|---|---|---|---|
| Unrestricted | 0.84 | 0.98 | 0.035 / **0.056** / 0.054 | 8.9 / 8.6 / **8.0** |
| PA or ST | 0.84 | 0.98 | 0.038 / **0.052** / 0.049 | 9.7 / 9.3 / **8.7** |
| Preferred | 0.85 | 0.98 | 0.027 / 0.045 / **0.048** | 10.7 / 10.7 / **9.9** |
| Not covered | 0.86 | 0.97 | **0.024** / 0.017 / 0.015 | 3.2 / 2.8 / **2.6** |

Readings:
* Patient and claim weighting are almost the same feature (r 0.97-0.98, mean gap about 2.5 pp). The distinct-plan count is a different feature (r about 0.84, mean gap about 8 pp), because it gives a plan with one patient the same weight as a plan with hundreds.
* Weighting by patients or claims carries about 1.5x the signal of the plan count for unrestricted, PA / ST and preferred, within volume terciles. Not covered is the only share where the plan count is slightly better, and all three are weak there.
* Patient weighting is the most stable. True DRG status changes in only about 1.5% of plans per month, so most month-over-month movement is patient-mix noise. Patients reduce it by 7-10% vs plans and 3-7% vs claims, because patients with many refills do not dominate.
* Patient weighting also matches how Market Access and the brand team read access ("x% of this HCP's patients have unrestricted Kerendia access").

**Decision.** Use **patient weighting** as the primary unit for all share features (P0 and P1), in both the DRG history and MMIT. Keep the NBA 3.0 distinct-plan version only as the parity reference in ablation M2. Implementation:
* Patient = LAAD `PATIENT_ID` with at least one paid claim with the HCP in the month. Weight 1 per patient per HCP-month, split equally across the patient's plans in that month.
* `_LOOKBACK`: patient-months over 12 months (sum of monthly patient weights), so the denominator is the same as for the current-month share.
* The Kerendia-claim EDA features (`share_*`) move to Kerendia patients in the same way.
* Limits: univariate, 3 months, DRG status, proxy HCP universe. Confirm in ablation M2 (plan vs patient) on the 221,723-HCP universe.

Interaction candidates for the learner (or explicit): restriction share x `RUNNING_TOTAL_HCP_RX_REJECTED_KERENDIA_CLAIMS`; access x F2F calls (does a rep visit offset a restriction?). The second one is the key NBA question: does access change which action is best.

---

## 4. Stitching DRG and MMIT into one access history

DRG data runs through **202511** (verified in 4.3) and MMIT was purchased from Jan 2026 (the MMIT historical uploads in the volume start at 202510 for the full feed). Combining them gives a continuous history from 2023, with MMIT as the go-forward source.

### 4.1 Linkage design

| Layer | DRG (2023 - 202509 in the unified table) | MMIT (202510 onward) |
|---|---|---|
| Common key | IQVIA LAAD `PAYER_PLAN_ID` | IQVIA LAAD `PAYER_PLAN_ID` (`IMSPayerPlanId`) |
| Payer to formulary | MASA file `MASA_MA_Kerendia_IQVIA_Access_Mapping_at_Plan_Level_01_28_25.xlsb` -> `DRG_PLAN_ID` (static, Jan 2025) | `bronze_iqvia_bridge` -> `OrgId` -> `FormularyId` (refreshed weekly; winning formulary by lives) |
| Status source | `ANLT_DRG_FRMLRY_HIST` (`PHARMACY_ST_CRITERIA`, `DUAL_COVERAGE_NOMENCLATURE`, `CHANNEL`, `PLAN_TYPE`) | `bronze_statuses` (`UniversalStatusRollup`, `RawStatus`) + `bronze_restrictions` (PA / ST / QL) |

Build one **unified plan-month access table** at `PAYER_PLAN_ID x month x drug`, with harmonized columns `h_tier` (Preferred / Covered / Non_Preferred / Not_Covered / Specialty / Not_Listed) and `h_restriction` (Unrestricted / PA_wo_ST / ST_or_PA_ST / Not_Covered / Unspecified), plus `access_source` (DRG / MMIT). All HCP features (Section 1.1 logic) are then computed once from this table, so the feature code does not change at the switch.

### 4.2 Switch rule and calibration
* **Overlap 202510-202511:** compare DRG and MMIT on the same payer plan and month (claim-weighted agreement matrices for tier and restriction). This is the evidence that the two series can be joined. Results in 4.2a.
* **Switch month (decided, 4.2a):** DRG through 202509, MMIT from 202510. DRG has no data after 202511, so a 202601 switch is not possible.
* **Crosswalk:** systematic off-diagonal cells in the overlap (e.g. MMIT `Covered` where DRG says `Non-Preferred`) become explicit mapping rules. Remaining differences are absorbed by an `access_source` flag.
* **Artificial changes:** change and momentum features must not fire because of the source switch. Compare the month-over-month change rate at 202509 -> 202510 with the within-source rates; if it spikes, compute changes within source only and set the switch-month change to missing.
* **Plan-universe drift:** the MASA file is static (Jan 2025) and the MMIT bridge is refreshed weekly, so the set of mapped plans (the denominator of `PCT_PLANS_*`) can step-change at the switch. Measure the share of paid claims mapped in DRG only / MMIT only / both, and test a common-universe denominator (plans mapped in both) as a variant.

### 4.2a Overlap results (run Oct 23 2026)

**Setup.** DRG month = file date minus 1 month (latest file per month; e.g. `formularies_20251124` -> 202510), joined to IQVIA payer plans via the MASA file (3,680 payer plans -> 1,300 DRG plans, 1:1). MMIT = `bronze_statuses` CKD class, latest feed, winning formulary by lives per IMS payer plan, plus `bronze_restrictions` PA / ST / QL. Overlap months **202510-202511**. Weights = all paid LAAD claims per payer plan x month (about 148M claims over the 2 months). Aligning DRG one month later instead lowered agreement (59.0% vs 60.1%), which supports the file-date month rule.

**Coverage of all paid LAAD claims (Kerendia status available):**

| Segment | 202510 | 202511 |
|---|---|---|
| Both DRG and MMIT | 75.2% | 75.1% |
| MMIT only | 11.8% | 12.0% |
| DRG only | 3.5% | 3.5% |
| Neither | 9.5% | 9.5% |

MMIT maps about 87% of paid claims vs about 79% for DRG, so `PCT_PLANS_*` denominators grow at the switch. Test the common-universe denominator variant.

**Claim-weighted agreement on the same payer plan and month:**

| Definition | Kerendia | Jardiance | Farxiga | Join-ready? |
|---|---|---|---|---|
| Covered vs not covered | 96.2 | 100.0 | 97.7 | Yes |
| Tier, 3 levels (Preferred / Covered or Non-Preferred / Not Covered) | 89.5 | 95.3 | 92.1 | Yes |
| Tier number (Tier 1-5; on the 77% of Kerendia claims where both report a number) | 91.3 | 91.9 | 91.3 | Yes |
| Unrestricted (covered, no PA, no ST) | 93.2 | 92.3 | 91.2 | Yes |
| Any PA or ST | 90.7 | 92.4 | 89.3 | Yes |
| QL | 95.7 | 95.0 | 92.5 | Yes |
| PA only | 91.0 | 98.5 | 97.7 | Yes |
| DRG 5-level tier (`DUAL_COVERAGE_NOMENCLATURE`) vs MMIT rollup | **60.1** | 94.3 | 80.9 | No |
| DRG restriction (`PHARMACY_ST_CRITERIA`) vs MMIT PA / ST split | **66.8** | 90.6 | 88.6 | No |
| ST only (claim-weighted ST rate: DRG vs MMIT) | **60.4** (4.9% vs 44.2%) | 91.4 | 87.2 | No |

**Why Kerendia's detailed definitions disagree (definitional, not noise):**
* **Tier labels:** 29% of paired claims are DRG `Non-Preferred` (Tier 3 / 4) and MMIT `Covered (PA/ST)` with `RawStatus` Tier 3 / 4. MMIT's rollup has no Non-Preferred level, but the tier numbers agree (Tier 3 = 50.9% on the diagonal, Tier 4 = 16.2%).
* **Step therapy:** 35% of paired claims are DRG `PA QL` (no ST) and MMIT has an ST code, mostly MMIT `Preferred (PA/ST)` Tier 3. MMIT likely codes the label prerequisite (for example ACEi / ARB background therapy) as a step, while DRG records it as PA. To confirm with MMIT / Bayer Market Access.
* **By payer type (Kerendia):** Medicare Part D PA agreement 99.2%, FFS Medicaid 98.8%, Commercial 80.2%. Commercial drives most of the gap.

**Decisions:**
1. The two series can be joined for: covered / not covered, 3-level tier, tier number, unrestricted, any PA-or-ST, PA only, QL. The top two DRG features in the baseline (`PCT_PLANS_KERENDIA_COVERED_LOOKBACK`, rank 25; `PCT_PLANS_KERENDIA_UNRESTRICTED`, rank 28) fall in this group.
2. Do **not** stitch `NOT_PREFERRED`, `COVERED_PA_WO_ST` or `COVERED_ST_OR_PA_ST` as defined in NBA 3.0. Replace them with tier-number shares (`PCT_PLANS_<DRUG>_TIER_1_2`, `_TIER_3`, `_TIER_4_PLUS`) and `PCT_PLANS_<DRUG>_PA_OR_ST`. Keep the MMIT ST split as an MMIT-only (Tier B) feature.
3. Switch at **202510** (MMIT from 202510, DRG through 202509), because MMIT covers more claims. Keep `access_source` and test the common-universe denominator.

### 4.3 Feature continuity: which features can be built from DRG and continued with MMIT

**Verified in `DRG_MMIT_History_Linkage_Checks` (Oct 23 2026):** `ANLT_DRG_FRMLRY_HIST` has 46 columns. Beyond the 7 used in NBA 3.0 it has `TIER_STATUS` (Tier 1-6 / Not Covered), `RESTRICTIONS` (PA / ST / QL combinations, e.g. `PA QL`, `ST QL`), `FORMULARY_STATUS` (tier + restrictions), `PHARMACY_LIVES` (80-92% filled), `REASON_CODE`, `PARENT_ID/NAME` and `PROVIDER_ID/NAME` (controller / payer org), `MEDICAL_ST_CRITERIA` (all Not Covered for Kerendia). No step-product or PA-criteria detail.

DRG coverage: 202107-202511 (50 months). **The last month is 202511, not 202512.** In 2025, the `DATA_MONTH` labels 05, 07 and 09 are missing, and 06, 08 and 10 each hold two snapshot files (e.g. 10/2025 holds `formularies_20251027` and `formularies_20251124`), so some files are mislabelled to the previous month. 12/2024 has about 5x the normal rows. Rule adopted: month = file date minus 1 month, keeping the latest file per month (supported by the overlap check in 4.2a). Overlap with MMIT: **202510-202511**.

| Family | Feature | From DRG (history) | From MMIT (go-forward) | Continuous series? |
|---|---|---|---|---|
| P0 | Coverage and tier shares (`COVERED`, `NOT_COVERED`, `PREFERRED` 3-level, `TIER_1_2` / `TIER_3` / `TIER_4_PLUS`) | Yes (`DUAL_COVERAGE_NOMENCLATURE`, `TIER_STATUS`) | Yes (rollup, `RawStatus` tier number) | **Yes** (89-96% agreement, 4.2a) |
| P0 | `UNRESTRICTED`, `PA_OR_ST`, `QL` shares | Yes (`RESTRICTIONS`) | Yes (PA / ST / QL codes) | **Yes** (91-96%) |
| P0 | NBA 3.0 `NOT_PREFERRED`, `COVERED_PA_WO_ST`, `COVERED_ST_OR_PA_ST` as defined | Yes | Different definitions | **No** for Kerendia (60-67%); replace as in 4.2a |
| P0 | `_LOOKBACK` (12-month) | Yes | Yes, on the unified table | **Yes** |
| P1 | `has_PA`, `has_ST` | Yes, coarse (from `PHARMACY_ST_CRITERIA`) | Yes, exact | **Yes** (at DRG granularity) |
| P1 | `has_QL`, `any_restriction` incl. QL | Yes (`RESTRICTIONS`) | Yes | **Yes** |
| P1 | Plan mix (commercial / Medicare / Medicaid, PBM) | Yes, and source-independent: LAAD / MASA `METHOD_OF_PAYMENT`, `PBM_NAME` | Yes | **Yes**: build from LAAD so it never breaks |
| P1 | Relative access (Kerendia vs Jardiance / Farxiga) | Yes | Yes | **Yes** |
| P1 | `step_requires_sglt2`, PA ARS rating | No (not in known DRG fields) | Yes (`bronze_st`, `bronze_pa_v2`) | MMIT-only |
| P2 | Status momentum (`improved` / `worsened_l3m`, `months_since_change`) | Yes, within DRG | Yes, within MMIT | **Yes**, with the switch-month guard |
| P2 | Competitor events (`farxiga_worsened_l3m`) | Yes | Yes | **Yes** |
| P2 | Raw tier and tier change | Yes (`TIER_STATUS`) | Yes (`RawStatus`, mapping to tiers needed) | **Yes** |
| P2 | Bayer HPM group | No | Yes, from 202601 | MMIT-only |
| P2 | PA burden (criteria, eGFR / UACR, age, duration) | No | Yes (`bronze_pa_v2`, `bronze_pa_udf`) | MMIT-only |
| P3 | Lives-weighted access | Yes, national (`PHARMACY_LIVES`, no geography) | Yes (`bronze_states`, `bronze_zip_code`) | **Yes** nationally; geography is MMIT-only |
| P3 | Medical benefit | No | Yes | MMIT-only |

### 4.4 How to use the two feature tiers in NBA 3.1
* **Tier A (continuous):** P0, coarse PA / ST, plan mix, relative access, momentum and competitor events. Built on the unified table from 2023 onward, so the model keeps its full training history (the 26 cohorts and beyond). These replace the DRG features one-for-one.
* **Tier B (MMIT-only):** MMIT ST split, step product, PA burden, HPM, medical, geography. About 12 months of history exist now (202510-202609) and it grows every week. Do not add them as all-missing before 2026 in a single model, because LightGBM would learn "missing = earlier cohorts" and confound them with time. Instead:
  1. Train the main model on Tier A over the full history.
  2. Measure the value of Tier B with a second-stage model on the residuals, or a model trained on recent months only, evaluated on later held-out months.
  3. Move a Tier B feature into the main model once its MMIT history covers the training window used for retraining.
* Fallbacks if the overlap shows the sources cannot be joined: (a) request an MMIT historical backfill before 202510; (b) retrain on MMIT months only; (c) carry 202510 status back with an imputed flag for slow-moving shares only.

---

## 5. Validation plan

1. **Linkage and parity check:** notebook `DRG_MMIT_History_Linkage_Checks` (same folder). Sections: DRG schema and month range; claim-weighted coverage of paid LAAD claims by DRG / MMIT / both; harmonized taxonomy; overlap-month (202510-202511) agreement matrices; change rate across the switch; HCP x month `PCT_PLANS_*` parity (correlation, mean, MAE). Pass criteria to agree with the team, e.g. claim-weighted tier agreement of 90% or more and HCP-level correlation of 0.9 or more for the P0 features.
2. **Ablation on the baseline setup** (same target, Tweedie, hyperparameters, time split):
   * M0: baseline with DRG (reference)
   * M1: baseline minus all `PCT_PLANS_*` (cost of dropping DRG)
   * M2: M1 + MMIT parity (P0), patient-weighted; M2b: same with the NBA 3.0 distinct-plan count
   * M3: M2 + P1 / P2 families
   * Metrics: Tweedie deviance, Gini / lift at top deciles, calibration, SHAP share of access group.
3. **Out-of-time** stability by month, especially across the 202601 plan-year reset and the 202607 Farxiga event.
4. **Volume control:** report importance within NBRx and volume strata (Checks 5.5 and 5.6 showed pooled AUC is inflated by volume).
5. **NBA impact:** check whether MMIT features change the recommended action, not only NBRx accuracy (e.g., uplift of F2F by access segment).

---

## 6. Using the weekly cadence

* **Modeling:** stay monthly (matches the model grain), but build features from weekly feeds point-in-time.
* **Scoring:** refresh access features weekly between monthly retrains, so NBA recommendations react to formulary wins and losses (e.g., trigger a rep message when an HCP's top plans improve).
* **Event feed:** publish weekly Kerendia / competitor status changes as a triggers table for NBA and OE.
* **Data quality monitors** on each weekly load: CONTROL.txt row-count reconciliation, Kerendia formulary count drift (the 202603 drop), status distribution drift, unmatched-payer rate, per-table coverage (prevent a repeat of the 2026-03-19 partial load).

---

## 7. Work plan

| Phase | Weeks | Deliverables |
|---|---|---|
| 0. Fix and align | 1-2 | Finish `DRG_MMIT_History_Linkage_Checks` (switch month decided: 202510); confirm crosswalk; HPM mapping fix; `bronze_plan_details` explicit schema; client decisions (Preferred source, APR, Farxiga) |
| 1. Access foundation | 2-4 | Unified DRG + MMIT plan-month access table at `PAYER_PLAN_ID x month x drug` (harmonized, point-in-time, `access_source` flag); payer bridge QA (placeholder IDs); weekly DQ checks |
| 2. HCP features | 4-6 | P0 parity on all paid LAAD claims (patient-weighted, plus distinct-plan reference; 12-month lookback) for Kerendia / Jardiance / Farxiga; P1 features; geo fallback; coverage for the 221,723-HCP universe |
| 3. Modeling | 6-8 | Ablations M0-M3; out-of-time tests; SHAP review |
| 4. Productionize | 8-10 | Add MMIT features to NBA 3.1 feature pipeline and weekly scoring refresh; monitoring |

---

## 8. Open questions
* ~~Last month of DRG data~~ Resolved: 202511 (overlap 202510-202511).
* ~~Full DRG column list~~ Resolved: tier (`TIER_STATUS`), QL (`RESTRICTIONS`) and lives (`PHARMACY_LIVES`) exist; no step-product or PA-criteria detail (4.3).
* Why MMIT codes ST for 35% of Kerendia claims where DRG records `PA QL` (label prerequisite coded as a step?). To confirm with MMIT / Bayer Market Access.
* Is the MASA payer-plan mapping file maintained after Jan 2025? If not, plans added in 2025 are missing from DRG history.
* Can MMIT deliver historical monthly snapshots before 202510 (only needed if the overlap check fails)?
* Whether the NBA 3.1 HCP universe stays at the v5 definition (221,723 HCPs).
* Whether to keep "all LAAD products" as the plan universe, or restrict it to the CKD / T2D / CV patient basket (test both).
* Reason for the 202603 formulary drop.
