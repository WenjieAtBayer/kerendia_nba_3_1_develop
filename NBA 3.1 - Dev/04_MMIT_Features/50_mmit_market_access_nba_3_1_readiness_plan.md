# Market Access in NBA 3.1: Readiness Plan

**Group:** Market access features (formulary tier, restriction, plan mix, access momentum)  
**Purpose:** one plan for how market access features go into NBA 3.1: what we build, from which data, in which order, how we test it, and when it is ready  
**Builds on:** EDA Checks 00-06, `DRG_MMIT_History_Linkage_Checks`, `MMIT_Access_Features_Client_Walkthrough.md`, the Market Access team briefing (`10_...`) and questionnaire, the Silver table update of Nov 24 2026, and the working-level detail in `07_MMIT_NBA_Readiness_Plan.md`  
**Status:** draft for review with the NBA and Market Access teams  
**Date:** November 25, 2026

---

## 1. In short

* **Today market access adds modest value to NBA 3.0.** The model keeps 44 DRG formulary features out of 752. Together they contribute about 5% of SHAP. The best feature (`PCT_PLANS_KERENDIA_COVERED_LOOKBACK`) ranks 25th; most features rank below 150. LAAD reject and pay-type features carry another roughly 2.5% of the access signal independently.
* **DRG ends in November 2025 and the data has limitations.** The DRG source (`ANLT_DRG_FRMLRY_HIST`) stops at month 202511. The IQVIA-to-DRG plan mapping (MASA file, January 2025) is static: plans created after that date drop out. Each plan counts once regardless of how many patients it covers.
* **What we propose for NBA 3.1:** four feature families: (1) **DRG parity** features (tier, restriction, unrestricted, QL) on the harmonised definitions where DRG and MMIT agree 89-96%; (2) **MMIT-enhanced** features (step detail, PA criteria, Bayer HPM) available from Oct 2025 / Jan 2026; (3) **access momentum** (improved / worsened); (4) **geographic fallback** for HCPs without mapped plans. All families are **patient-weighted** and use the **Bayer Payer Spine** for the IQVIA-to-formulary mapping. DRG provides history to September 2025; MMIT takes over from October 2025.
* **Key change from NBA 3.0:** replace the plan-count unit with a **patient** unit (each LAAD patient counts once per HCP per month). Patient weighting carries about 1.5x the signal of the plan count and is more stable, and it matches how Market Access reads MMIT.

---

## 2. What we learned (the evidence behind this plan)

| Topic | Finding | Consequence for NBA 3.1 | Source |
| --- | --- | --- | --- |
| NBA 3.0 model | 44 DRG features kept; about 5% SHAP; best rank 25; Jardiance/Farxiga ranks 152+ | Access is a supporting signal; goal is to recover and modestly improve, not to make it a top driver | SHAP file on baseline run |
| DRG ends Nov 2025 | Last month in `ANLT_DRG_FRMLRY_HIST` is 202511; DRG month labels inconsistent in 2025 (re-derived from file date minus 1 month) | Must stitch DRG history with MMIT; switch at 202510 | `DRG_MMIT_History_Linkage_Checks` section 1 |
| DRG vs MMIT agreement | Covered/not 96%, 3-level tier 90%, unrestricted 93%, PA-or-ST 91%, QL 96%; but DRG 5-level tier 60%, PA/ST split 67% for Kerendia | Build on the harmonised definitions that agree well; replace Non-Preferred and PA-vs-ST with tier numbers and PA-or-ST | Overlap check (Oct-Nov 2025), `07_...` section 4.2a |
| Non-Preferred gap | 29% of Kerendia claims: DRG Non-Preferred (Tier 3/4) = MMIT Covered (PA/ST) Tier 3/4 | Use tier numbers instead of DRG's Non-Preferred | Same |
| Step therapy gap | MMIT 44% ST vs DRG 5%; likely label prerequisite (ACEi/ARB) coded as step | Keep MMIT ST as MMIT-only; merge PA+ST for the stitched series | Same; question A2 for Market Access |
| MASA plan mapping | Static Jan 2025 snapshot; 12% of paid claims map only through MMIT, 3.5% only through DRG | Replace with Bayer Payer Spine (refreshed; Kerendia-specific rules) | Market Access feedback |
| Patient weighting | Patient and claim weighting nearly identical (r 0.98); both carry about 1.5x signal of plan count; patient most stable (MoM noise 7-10% lower) | Patient-weighted shares primary; plan count kept only as parity reference | Weighting test (DRG, Mar-May 2025) |
| MMIT match rate | 89.5% of Kerendia claims matched in window; 10.5% unmatched (6.5% no payer, 4.1% no drug row) | Expect some missingness; build a geographic fallback | EDA Check 1 |
| Best EDA features | `share_commercial` AUC 0.579, `share_step_requires_sglt2` 0.575, `share_any_restriction` 0.431 (inverse) | Moderate univariate signal, consistent with DRG SHAP | EDA Check 5 |
| Kerendia access improving | About 2:1 improvements vs deteriorations since Oct 2025; Farxiga deteriorated sharply Apr-Jul 2026 | Momentum features; Farxiga deterioration may be generic dapagliflozin (question C1) | EDA Check 6 |
| Bayer HPM | Monthly from Jan 2026; 73% "Other" at claim level (mapping bug); disagrees with MMIT rollup on 119 formularies on "Preferred" | Fix mapping before using; HPM enters family 2 | EDA Check 4 |
| Silver plan_dim rebuild | Nov 24 2026: now Galaxy-sourced, 9,539 current OrgIds (up 12%), full SCD2 history, new StateId/Zip columns; 678 OrgIds changed FormularyId over time | Use SCD2 point-in-time joins (`valid_from / valid_to`), not `is_current = true` | Silver update analysis |
| Payer Spine | Market Access says MMIT's IQVIA bridge does not match Bayer's payer mastering; use Galaxy Payer Spine IQVIA Bridge + Payer Hierarchy; interim tables expected this week; Kerendia-specific business rules (patient assistance, copay card plans) | Replace MMIT bridge and MASA file; apply same rules as Galaxy AI / Athena | Market Access feedback, support team |

---

## 3. Decisions taken

| # | Decision | Effect on the plan |
| --- | --- | --- |
| D1 | **Patient-weighted shares** replace the NBA 3.0 distinct-plan count | Every share feature uses patients as the unit (section 3.1); plan count kept only in experiment M2b |
| D2 | **Bayer Payer Spine** replaces MMIT's IQVIA bridge and the MASA file | Interim spine tables this week; re-run all checks on spine; build so the enterprise solution can replace it later |
| D3 | **Switch month 202510:** DRG through 202509, MMIT from 202510 | MMIT covers more claims; DRG's last month is 202511 |
| D4 | **Harmonised definitions** for the stitched series: covered/not, 3-level tier, tier number, unrestricted, PA-or-ST, QL | Drop NBA 3.0's Non-Preferred, Covered (PA) without ST, Covered ST or PA/ST |
| D5 | **SCD2 point-in-time joins** on `silver_plan_dim` | 678 OrgIds changed FormularyId; using `is_current` gives the wrong formulary for historical months |
| D6 | **CKD therapeutic class** for MMIT PA/ST detail | Heart failure indication scope to be confirmed with Market Access (question C3) |

### 3.1 Patient weighting

Patient = every LAAD `PATIENT_ID` with at least one paid claim with the HCP in the month. Weight: 1 per patient per HCP-month, split equally across the patient's plans in that month. `_LOOKBACK`: patient-months over 12 months. Tested on DRG Kerendia status (Mar-May 2025, 433K HCPs, next-month NBRx).

Still open from Market Access: whether "patient" is close to their definition or they prefer lives / Kerendia-eligible patients (question D1 in the questionnaire).

---

## 4. Target design: the four feature families

All families share three rules: **NPI** as HCP key (from LAAD `PROVIDER_ID`, joined to the NBA HCP key in the combine step); windows that end at the last **complete** month before the anchor date (current month and 12-month lookback); and a **patient-weighted** share from the HCP's full book of business (all paid LAAD claims, no product filter).

| # | Family | What it describes | Main sources | Grain | Example features | Approx. candidates | Detail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **DRG parity** | Harmonised tier and restriction shares, continuous from 2023 | DRG `ANLT_DRG_FRMLRY_HIST` (to 202509) + MMIT `bronze_statuses` / `bronze_restrictions` (from 202510), via Payer Spine | NPI × month × drug | `PCT_PAT_KERENDIA_UNRESTRICTED`, `..._COVERED`, `..._TIER_1_2`, `..._PA_OR_ST`, `..._QL`, `..._LOOKBACK` | 60-80 | Section 4.1 |
| 2 | **MMIT-enhanced** (new) | Detail only MMIT provides: step product, PA criteria, Bayer HPM, MMIT ST split | MMIT `bronze_restrictions`, `bronze_pa_v2`, `bronze_derived_fields` | NPI × month | `PCT_PAT_KERENDIA_STEP_REQUIRES_SGLT2`, `PCT_PAT_KERENDIA_PA_EGFR_REQ`, `PCT_PAT_KERENDIA_HPM_PREFERRED_UNRESTRICTED`, `PCT_PAT_KERENDIA_MMIT_HAS_ST` | 20-30 | Section 4.2 |
| 3 | **Access momentum** | Status changes in the last 3 and 6 months | `silver_status_changes`, `silver_restriction_changes` | NPI × month | `KERENDIA_ACCESS_IMPROVED_L3M`, `KERENDIA_NET_CHANGE_L6M`, `FARXIGA_ACCESS_WORSENED_L3M` | 12-18 | Section 4.3 |
| 4 | **Geographic fallback** | Lives-weighted access in the HCP's area, for HCPs without mapped plans | MMIT `bronze_states`, `bronze_cbsas`, `bronze_zip_code`, `silver_plan_dim` (StateId, Zip) | NPI × month | `GEO_KERENDIA_UNRESTRICTED_ZIP`, `GEO_KERENDIA_UNRESTRICTED_STATE`, `ACCESS_SOURCE` (plans / geo / none) | 8-12 | Section 4.4 |
| all | **Relative access** | Kerendia vs competitor, computed on all families | Derived from family 1 | NPI × month | `KERENDIA_VS_JARDIANCE_ACCESS_ADVANTAGE`, `KERENDIA_VS_FARXIGA_UNRESTRICTED_DIFF` | 6-10 | |

Expected result: about 40 to 70 market access features kept after selection.

### 4.1 DRG parity (family 1)

These features replicate and improve the NBA 3.0 `PCT_PLANS_*` block. For each of Kerendia, Jardiance and Farxiga:

| Feature | DRG source | MMIT source | Agreement | Notes |
| --- | --- | --- | --- | --- |
| `PCT_PAT_<DRUG>_COVERED` | `DUAL_COVERAGE_NOMENCLATURE` != Not Covered | `UniversalStatusRollup` != Not Covered / Not Listed | 96-100% | |
| `PCT_PAT_<DRUG>_UNRESTRICTED` | No PA, no ST in `RESTRICTIONS` | No PA, no ST in `bronze_restrictions` | 91-93% | |
| `PCT_PAT_<DRUG>_PA_OR_ST` | PA or ST in `RESTRICTIONS` | PA or ST in `bronze_restrictions` | 89-92% | Replaces separate PA and ST |
| `PCT_PAT_<DRUG>_QL` | QL in `RESTRICTIONS` | QL in `bronze_restrictions` | 93-96% | |
| `PCT_PAT_<DRUG>_PREFERRED` | `DUAL_COVERAGE_NOMENCLATURE` = Preferred | `UniversalStatusRollup` starts with Preferred | 90-95% (3-level) | |
| `PCT_PAT_<DRUG>_TIER_1_2` / `_TIER_3` / `_TIER_4_PLUS` | `TIER_STATUS` | `RawStatus` tier number | 91% | Replaces Non-Preferred |
| `..._LOOKBACK` | 12-month rolling | Same | | |

### 4.2 MMIT-enhanced (family 2)

Available from October 2025 (or January 2026 for HPM). No DRG history; tested in experiment M3 for incremental value.

| Feature | Source | Available from |
| --- | --- | --- |
| `PCT_PAT_KERENDIA_STEP_REQUIRES_SGLT2` | `bronze_st` step product | 202510 |
| `PCT_PAT_KERENDIA_PA_EGFR_REQ` / `_UACR_REQ` | `bronze_pa_v2` CKD indication | 202510 |
| `PA_ARS_RATING_MEAN` | `bronze_pa_v2` ARS | 202510 |
| `PCT_PAT_KERENDIA_MMIT_HAS_ST` | `bronze_restrictions` ST code | 202510 |
| `PCT_PAT_KERENDIA_HPM_<GROUP>` | `bronze_derived_fields` Bayer HPM | 202601 |

### 4.3 Access momentum (family 3)

Computed within each source (DRG or MMIT) to avoid false changes at the switch month. Uses `silver_status_changes` and `silver_restriction_changes` (now Galaxy-sourced, 62 weekly snapshots to Nov 19 2026).

### 4.4 Geographic fallback (family 4)

For the roughly 10% of HCPs whose LAAD payer plans do not map to a formulary, use lives-weighted access at the HCP's ZIP, CBSA or state from MMIT geography tables. `silver_plan_dim` now carries `StateId` and `Zip` (since the Nov 24 Silver rebuild). An `ACCESS_SOURCE` flag (plans / geo / none) is included as a feature.

---

## 5. Data readiness

| Data | Location | Coverage / key | Status | Gap / action | Owner |
| --- | --- | --- | --- | --- | --- |
| DRG formulary history | `CPH_DB_PROD.ANALYTICS_V2.ANLT_DRG_FRMLRY_HIST` (Snowflake) | 202107-202511; plan_id; file-derived month | **Ready** | Month labels fixed (file date minus 1); dedup by latest file per month | NBA team |
| MMIT statuses + restrictions | `market_access.bronze_statuses`, `bronze_restrictions` (Databricks) | 202510-202611 (55 feed dates in UC; 66 in Galaxy) | **Ready** | CKD therapeutic class; latest feed per formulary-drug-month | NBA team |
| MMIT PA / ST detail | `market_access.bronze_pa_v2`, `bronze_st` | 202510+ | **Ready** | CKD indication; ARS, step product | NBA team |
| Bayer HPM | `market_access.bronze_derived_fields` | 202601+ (46 feed dates) | **Partial** | 73% "Other" mapping bug at claim level; fix mapping before use; confirm Preferred source (question A1) | NBA team, Market Access |
| MMIT bridge (interim cross-check) | `market_access.bronze_iqvia_bridge` | 202510+; OrgId → IMSPayerPlanId | **Replaced** | Use Payer Spine instead; keep bridge only as cross-check | NBA team |
| **Bayer Payer Spine** | Galaxy Payer Spine IQVIA Bridge + Payer Hierarchy (interim tables) | Expected this week | **Incoming** | Receive tables; map keys (B7); apply Kerendia business rules (B8); check if spine covers DRG history (B10) | Payer data support, NBA team |
| MASA mapping (DRG history) | `/Volumes/.../kerendia_nba_3_volume/patinet_level_features/notebook_output/MASA_MA_Kerendia_IQVIA_Access_Mapping_at_Plan_Level_01_28_25.xlsb` | Jan 2025 snapshot; 3,680 plans → 1,300 DRG plans | **Ready (fallback)** | Use Payer Spine if it covers DRG (B10); MASA stays as the fallback | NBA team |
| Silver tables (SCD2 dims + changes) | `market_access.silver_plan_dim`, `silver_drug_dim`, `silver_status_changes`, `silver_restriction_changes`, `silver_pa_changes` | Rebuilt Nov 24 2026 from Galaxy; 62 weeks; plan_dim: 9,539 OrgIds with SCD2 | **Ready** | Use point-in-time joins on plan_dim; 678 OrgIds changed FormularyId | NBA team |
| MMIT geography (lives) | `market_access.bronze_states`, `bronze_cbsas`, `bronze_zip_code` | 202510+ | **Ready** | HCP ZIP/CBSA from MDM best affiliation | NBA team |
| LAAD claims (plan universe) | `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FCT_RX` + `_DIM_PRD` (Snowflake) | All products, paid claims, 2021+ | **Ready** | No product filter; patient-weighted | NBA team |
| NBA HCP universe | `kerendia_nba_3_hcp_model_base_hcp_universe_v5` or v6 | 221,723 HCPs (v5) | **To confirm** | Whether NBA 3.1 stays at v5 or moves to v6 | NBA team |
| Market Access questionnaire | `kerendia_nba_3_1.market_access` volume | 26 questions (8 must-answer) | **Sent** | Answers expected before the meeting; 4 must-answer questions (A1, A2, A3, D1) block feature definitions | Market Access |

---

## 6. Work plan

Each phase ends with a gate (section 8). Phase 2 does not depend on phase 1 and can start in parallel.

| Phase | Content | Main tasks | Experiments | Depends on |
| --- | --- | --- | --- | --- |
| **0. Spine and alignment** | Replace the payer mapping; harmonise DRG and MMIT | Receive Payer Spine; map spine keys to MMIT and DRG; apply Kerendia business rules; re-run match rate and DRG-MMIT agreement on spine; fix HPM mapping bug; answer questionnaire must-answer questions (A1-A3, D1) | — | Spine tables; Market Access answers |
| **1. Access foundation** | Build the unified plan-month access table | Unified DRG + MMIT table at `PAYER_PLAN_ID × month × drug` with harmonised status, patient-weighted, `access_source` flag, SCD2 plan_dim; payer bridge QA; switch-month change-rate check | M1 | Phase 0 |
| **2. MMIT-enhanced + momentum** | Families 2 and 3 | Step product, PA criteria, Bayer HPM; momentum features from Silver change tables; guard at switch month | M3 | Silver tables (ready); HPM mapping fix |
| **3. HCP features + fallback** | Families 1 and 4; relative access | Patient-weighted P0 parity for Kerendia / Jardiance / Farxiga on all paid LAAD claims; 12-month lookback; geographic fallback; relative access; coverage check on the 221,723-HCP universe | M2, M2b | Phase 1 |
| **4. Modeling and freeze** | Ablations and selection | Run experiments M0 to M4; out-of-time tests; SHAP review; freeze the feature list; confirm access is incremental over LAAD reject features; document | — | Phases 1-3 |
| **5. Productionise** | Weekly refresh | Add MMIT features to the NBA 3.1 feature pipeline; weekly scoring refresh; data quality monitors (CONTROL.txt reconciliation, formulary count drift, status distribution drift, unmatched-payer rate) | — | Phase 4 |

---

## 7. Experiments and readiness gates

All experiments use the NBA 3.1 HCP-level model, target and validation split; only the market access block changes.

| Exp. | Market access block | Question |
| --- | --- | --- |
| M0 | No market access features (LAAD reject features only) | How much does access add on top of reject features? |
| M1 | NBA 3.0 DRG block (44 features, plan-count weighted) | Parity baseline |
| M2 | Family 1 (DRG parity), patient-weighted, on spine | Does the harmonised + patient-weighted block recover NBA 3.0 value? |
| M2b | Same as M2 but plan-count weighted | Is patient weighting better? |
| M3 | M2 + family 2 (MMIT-enhanced) | Do step, PA criteria and HPM add incremental value? |
| M4 | M3 + family 3 (momentum) + family 4 (geo fallback) + relative access | Full access block |

**Measures:** NBA 3.1 validation metric; SHAP share of the access families; rank of the best access feature; number of access features kept; stability of importance across time folds.

| Gate | Ready when |
| --- | --- |
| **G0 (spine)** | Payer Spine received and mapped; match rate and DRG-MMIT agreement re-run on spine; must-answer questionnaire questions (A1-A3, D1) answered; HPM mapping bug fixed |
| **G1 (foundation)** | Unified plan-month access table built; switch-month change rate checked; E(M1) run as parity |
| **G2 (features)** | All four families built for all training instances; patient weighting applied; leakage check passed (anchor-date compliance); coverage on the 221K-HCP universe measured |
| **G3 (freeze)** | Experiments M0-M4 compared; out-of-time test passed; SHAP review done; final access block documented; feature list frozen in config; inference run reproduces training columns |

---

## 8. Risks

| Risk | Effect | Mitigation |
| --- | --- | --- |
| Payer Spine delayed or keys don't match | Cannot build production features | MMIT bridge + MASA as interim fallback; feature code is mapping-agnostic |
| DRG and MMIT disagree more on the spine | Harmonised definitions lose validity | Re-run overlap check on spine at G0; adjust if agreement drops below 85% |
| Patient weighting worse on the full universe | Wasted development time | M2 vs M2b comparison; revert to plan count if patient is worse |
| HPM mapping bug not fixable | No HPM features | HPM enters only in M3; model works without it |
| MMIT-enhanced features short history (Oct 2025+) | Lookback features incomplete for early cohorts | Mark as missing for months before 202510; test with and without in M3 |
| Momentum features fire at the switch month | False access changes | Compute within each source; set the switch-month change to missing |
| Kerendia business rules differ from Galaxy AI / Athena | Numbers don't reconcile with Market Access reports | Get rules in writing (B8) and apply them; validate a sample |
| Access remains weak in NBA | Little model gain | Accept a small block; value can come from triggers (access improved → rep message) |
| Galaxy Silver tables fail on serverless | Silver not refreshed | Known issue (Nov 24); run on classic cluster or escalate |

---

## 9. Roles

| Area | NBA team | Market Access | Payer data support |
| --- | --- | --- | --- |
| Payer Spine integration | Builds and validates | Reviews mapping and business rules | Provides tables and refreshes |
| Harmonised definitions (tier, restriction) | Proposes and implements | Confirms (A1-A3) | |
| HPM mapping fix | Implements | Confirms HPM/APR meaning (A4) | |
| Feature building (all families) | Owns | Reviews feature list | |
| Patient definition | Proposes | Confirms (D1) | |
| Kerendia business rules | Applies | Provides written rules (B8) | Advises |
| Experiments and freeze | Owns | Reviews SHAP and results | |
| Weekly refresh and monitoring | Owns | Alerted on formulary count / status drift | |

---

## 10. Open questions

The full questionnaire (26 questions, `NBA_3_1_Market_Access_Questionnaire.xlsx`) is with the Market Access team. The 8 must-answer questions that block this plan:

| # | Question | Blocks |
| --- | --- | --- |
| A1 | Which source defines "Preferred" for Kerendia: MMIT rollup or Bayer HPM? | Preferred feature in family 1 |
| A2 | Is MMIT coding the label prerequisite as a step? Which definition reflects the real barrier? | Whether PA and ST stay separate or merge |
| A3 | Is the tier number the right common language for Non-Preferred? | Tier features in family 1 |
| B7 | Payer Spine keys and how they link to MMIT and DRG | Phase 0 |
| B8 | Kerendia business rules (patient assistance, copay card plans) | Phase 0 |
| B10 | Can the spine cover DRG history? | Whether DRG history uses spine or MASA |
| C1 | Is the Farxiga deterioration linked to generic dapagliflozin? | Competitor access feature |
| D1 | Is our patient definition close to Market Access's? | Core unit for all features |

---

## 11. Next actions

| # | Action | Owner |
| --- | --- | --- |
| 1 | Receive Payer Spine tables and map keys to MMIT and DRG | Payer data support, NBA team |
| 2 | Collect Market Access questionnaire answers (must-answer first) | Market Access |
| 3 | Re-run match rate and DRG-MMIT agreement on the Payer Spine | NBA team |
| 4 | Fix HPM mapping bug (73% "Other") | NBA team |
| 5 | Build unified DRG + MMIT plan-month access table (Phase 1) | NBA team |
| 6 | Build patient-weighted HCP features for Kerendia / Jardiance / Farxiga (Phase 3) | NBA team |
| 7 | Run experiments M0 and M1 (baseline and parity) | NBA team |
| 8 | Review this plan with the NBA and Market Access teams | NBA team |

---

## Appendix: where the detail is

| Topic | Document |
| --- | --- |
| Working-level technical plan (DRG logic, stitching design, overlap results, feature continuity table) | `MMIT_EDA_Checks/07_MMIT_NBA_Readiness_Plan.md` |
| How MMIT is joined to claims, step by step | `MMIT_Access_Features_Client_Walkthrough.md` |
| MMIT EDA checks (coverage, HPM, signal, status changes) | `MMIT_EDA_Checks/00_MMIT_Claim_Level_EDA_Client_Summary.md` and files 01-06 |
| DRG vs MMIT overlap comparison | `MMIT_EDA_Checks/DRG_MMIT_History_Linkage_Checks` |
| Market Access team briefing (plain-language) | `10_market_access_team_briefing_nba_3_1.md` |
| Market Access questionnaire | `kerendia_nba_3_1.market_access` volume: `NBA_3_1_Market_Access_Questionnaire.xlsx` |
| Silver table update analysis (Nov 24 2026) | This conversation thread |
| MMIT ingestion skill (Bronze/Silver architecture) | `.assistant/skills/mmit-ingestion/SKILL.md` |
