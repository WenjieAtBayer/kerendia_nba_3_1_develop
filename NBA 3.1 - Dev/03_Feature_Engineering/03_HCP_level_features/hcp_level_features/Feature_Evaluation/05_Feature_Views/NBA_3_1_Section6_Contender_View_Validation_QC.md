# NBA 3.1: validation of section 6 (contender view readiness) against the HCP monthly feature notebooks

**Status:** DONE, 2026-11-27  
**Verdict:** Of the 10 in-scope section 6 rows, 8 are confirmed (V1, V2, V3, V6, V7, V8, V10, F9). **V9** is only partly confirmed (T1D and CKD sit on different claim rows, so it is not a single-filter pilot), and **F10** is only partly confirmed (trend columns exist only in NB01). V4 / V5 are out of scope (not LAAD). Blockers confirmed: no `CLAIM_TYPE` (V1 paid-only, V2 RV), stale `pj_pat_sglt2_filter_m` (V6), no HCP column on any patient-state table (bridge, V3 / V6 / V7 / V8).  
**Rule source:** [`NBA_3_1_LAAD_Feature_Views_Readiness_Plan.md`](NBA_3_1_LAAD_Feature_Views_Readiness_Plan.md) ("readiness"), section 6 and 6.1-6.3, with sections 4, 5.1, 5.3 and 5.4 where a view depends on them. Section 7 (work plan) is out of scope: no feature was built.  
**Method:** read-only. Evidence = (a) the five per-notebook QC files (all DONE 2026-11-27) and (b) fresh spot-check queries run 2026-11-27 on run `full_2026_11_16` in `ph-com-ai-us-prod-catalog-2553213839599380.kerendia_nba_3_1` (`<S>`). No notebook or table was changed.

Verdict scale: **Confirmed** = the data agrees with the readiness status and blocker; **Partly confirmed** = status holds only in part, or a condition the readiness does not mention was found; **Not confirmed** = the data contradicts the readiness; **N/A** = out of scope.

## 1. Notebooks and outputs checked

| # | Notebook | Output table (`<S>.`) | Key | Columns | Per-notebook QC |
| --- | --- | --- | --- | --- | --- |
| NB01 | `01 Rx Claims Files/01_claim_rx_monthly_cohort` | `full_2026_11_16_hcp_claim_rx_monthly_cohort` | `NPI_NUMBER` | 4,681 | `01 Rx Claims Files/01_rx_claims_features_qc.md` |
| NB02 | `02 Lab Claims Files/02_claim_lab_monthly_cohort` | `full_2026_11_16_hcp_claim_lab_monthly_cohort` | `NPI_NUMBER` | 152 | `02 Lab Claims Files/02_lab_claims_features_qc.md` |
| NB03 | `03 Diagnosis Claims Files/03_claim_diagnosis_monthly_cohort` | `full_2026_11_16_hcp_claim_diagnosis_monthly_cohort` | `NPI_NUMBER` | 122 | `03 Diagnosis Claims Files/03_dx_claims_features_qc.md` |
| NB05 | `05 Rx NPS Claims Files/05_claim_rx_nps_monthly_cohort` | `full_2026_11_16_hcp_claim_rx_nps_monthly_cohort` | `PROVIDER_ID` | 172 | `05 Rx NPS Claims Files/05_rx_nps_claims_features_qc.md` |
| NB06 | `06 Eligible HCP Claims Files/06_claim_eligible_hcp` | `full_2026_11_16_hcp_claim_eligible_patient_cohort` | `NPI_NUMBER` | 226 | `06 Eligible HCP Claims Files/06_eligible_hcp_claims_features_qc.md` |

NB01 and NB03 also write a `..._hcp_provider_...` copy keyed by `PROVIDER_ID` (checked); provider copies of NB02 / NB06 were not checked here. Column counts for eligible / HF / stage / rejected columns below are by name pattern.

## 2. View-to-notebook coverage

Column counts are by name pattern on the output schema (spot check 2026-11-27).

| View | NB01 Rx | NB02 Lab | NB03 Dx | NB05 Rx NPS | NB06 Eligible | Track C view built? |
| --- | --- | --- | --- | --- | --- | --- |
| V1 Kerendia writing | 234 Kerendia claim columns | - | - | 9 Kerendia patient-start columns | - | No (Track R = register) |
| V2 Claim type | 162 rejected columns; 0 paid / reversed | - | - | - | - | No |
| V3 SGLT2 add-on pool | SGLT2 claim counts only | - | - | SGLT2 start columns | - | No |
| V6 Eligible panel | - | 24 eligible columns | - | - | 140 eligible columns | No |
| V7 CKD stage mix | - | 45 stage columns (by test) | 108 stage columns (coded Dx stage) | - | 63 stage columns (PJ06 Dx-first label) | No |
| V8 HF | - | - | - | - | 80 HF columns (16 HFpEF proxy) | No |
| V9 T1D + CKD | - | - | T1D codes counted as stage 0 | - | 16 T1D columns | No |
| V10 Lab monitoring | - | 66 test columns (GFR / UACR / K / HbA1c) | - | - | - | No |
| F9 Completeness | - | - | - | - | - | No |
| F10 Trends | 12 `RATIO_..._IN_PRIOR_3_LAST_3_MONTH` | 0 | 0 | 0 | 0 | No |

## 3. Validation per contender view

### V1 Kerendia writing: readiness status "Needs prep"

Readiness: NBRx, TRx, running totals, time since first Kerendia Rx; NB01 / NB05 output, Track R (register); NBRx is stateful, keep in notebooks; paid-only filter needs `CLAIM_TYPE`.

| Claim | Evidence | Result |
| --- | --- | --- |
| Kerendia counts and running totals exist in NB01 | 234 Kerendia columns (windows 1 / 3 / 6 / 12, `RUNNING_`, `PCT_`, rejected, days supply, payer, patient attributes); 6-case trace 0 mismatches (01 QC Q10) | Yes |
| NBRx (first claim per patient) stays in notebooks | NB05 computes `TOTAL_PATIENTS_START_KERENDIA_*` and `RUNNING_TOTAL_PATIENTS_START_KERENDIA` in the notebook; 95 count features recomputed with 0 differences (05 QC) | Yes |
| Paid-only filter needs `CLAIM_TYPE` | `full_2026_11_16_pull_rx_hcp` has 16 columns, `REJECTION_FLAG` but no `CLAIM_TYPE` / `CLAIM_STATUS`. Today rejected claims are counted: 134,454 of 395,486 Kerendia starts (34.0%) have only rejected claims on the start day (05 QC F1) | Yes, and the effect is large for Kerendia |
| Time since first Kerendia Rx | No column with `SINCE` / `RECEN` / `FIRST` / `DAYS_SINCE` in NB01 or NB05 | Not built (name check only) |
| Entity `NPI_NUMBER` for registration (5.1) | NB01 keyed by `NPI_NUMBER`; NB05 keyed by `PROVIDER_ID` only (05 QC F3) | NB05 needs an `NPI_NUMBER` column before Track R |
| Track R full width | NB01 = 4,681 columns (readiness 1 / 7 says 4,677) | Readiness count out of date |

**Verdict: Confirmed** ("Needs prep"). Extra prep found: NB05 key, time-since-first not built, 34% rejected-only Kerendia starts.

#### V1 addendum: Kerendia timing features in the adoption notebook (`03_HCP_Level_Features/11_adoption_features`)

Checked 2026-11-27 by reading cells 1, 3, 8, 11 and 13 (cell 13 first part only), a text search of all 13 cells, and the `RX01_DRUG_GROUPS` and Kerendia lines of the shared `hcp_features_config.py` (read-only; the notebook was not run).

**What the notebook builds** (15 columns per `PROVIDER_ID` x claims cohort, cells 1, 3, 8, 13):

| # | Feature | Definition | Drug groups |
| --- | --- | --- | --- |
| 1 | `MIN_DAYS_TO_PRESCRIBE_{DRUG}_POST_CKD_DIAGNOSIS` | Min over the HCP's patients of days from the patient's first CKD Dx by this HCP to the patient's first Rx of the drug from this HCP (NBA 3.0 `TIME_TO_ADOPT_{DRUG}` renamed) | 5 groups |
| 2 | `HCP_TIME_TO_ADOPT_{DRUG}` | Days from FDA approval to the HCP's **first Rx** of the drug (any patient) | Invokana, Farxiga, Jardiance, Entresto |
| 3 | `MIN_DAYS_TO_PRESCRIBE_{DRUG}_POST_FIRST_CKD_DIAGNOSIS_ANY_HCP` | Same as #1, from the patient's first CKD Dx by any provider | 5 groups |
| 4 | `ENTRESTO_BRAND_ADOPTER_FLAG` | First brand Entresto Rx before LOE (2025-07-01) and on or before the cutoff | Entresto |

`{DRUG}` = `RX01_DRUG_GROUPS` in the config: `INVOKANA`, `FARXIGA`, `JARDIANCE`, `STEROIDAL_MRA` (spironolactone + eplerenone), `ENTRESTO`. Point-in-time: each cohort uses claims up to the end of its `lookback_end_date` month; empty when there is no qualifying Rx by the cutoff; rejected claims included.

**Kerendia:** not covered. Kerendia is not a drug group in the notebook or in `RX01_DRUG_GROUPS`, and `APPROVAL_DATES` has no Kerendia date. A text search of all 13 cells finds "Kerendia" only in the Phase 0 validation note (Kerendia writer specialty mix, cell 2) and in the volume path check (cell 3). So the notebook has no time-since-first Kerendia Rx, no Kerendia adoption speed, and no most-recent Kerendia Rx (NBA 3.0 `KERENDIA_RX_TIME_MIN`, SHAP rank 3 in the 752).

**Fit with V1:** feature #2 is exactly the "time since first Rx" pattern V1 asks for, so adding a `KERENDIA` group (with the Kerendia product name(s) used in `Rx_01_new`, not checked here) and a Kerendia approval date would give `HCP_TIME_TO_ADOPT_KERENDIA` (and #1 / #3 Kerendia variants) with the same point-in-time logic. Differences from the section 5.1 Track R rules: output is a Delta path under `kerendia_nba_3_1_volume/.../hcp_features/adoption_features`, not a UC table; key `PROVIDER_ID` (no `NPI_NUMBER`); Rx source `Rx_01_new`, not `full_2026_11_16_pull_rx_hcp`.

**Lead not checked:** `hcp_features_config.py` refers to a `10_kerendia_prior_writing` notebook with claim types PD / RJ / RV ("approved = paid + reversed"). It may hold Kerendia writing features (and a claim-type split relevant to V1 paid-only and V2); it was not read in this QC.

**Addendum verdict: V1 Confirmed.** The time-since-first feature pattern is built in the Adoption Features notebook (`HCP_TIME_TO_ADOPT_{DRUG}` = days from approval to the HCP's first Rx, point-in-time per cohort) for the competitors Invokana, Farxiga, Jardiance and Entresto. The only remaining V1 item is the Kerendia variant: add a `KERENDIA` drug group and a Kerendia approval date to `11_adoption_features` / `hcp_features_config.py` to get `HCP_TIME_TO_ADOPT_KERENDIA` (plus the two `MIN_DAYS_TO_PRESCRIBE_KERENDIA_*` columns). Finding S6 is narrowed to this.

### V2 Claim type: "Blocked (RV) / Ready (RJ)"

| Claim | Evidence | Result |
| --- | --- | --- |
| RJ can start via `REJECTION_FLAG` | `REJECTION_FLAG` decimal(1,0), 0 / 1 only, 307,579,439 of 3,275,477,893 rows rejected (01 QC Q4); NB01 already has 162 rejected columns (`TOTAL_REJECTED_RX_CLAIMS_*`, `RUNNING_TOTAL_REJECTED_*`) | Yes |
| RV blocked until PJ03 adds `CLAIM_TYPE` | No `CLAIM_TYPE` / `CLAIM_STATUS` in the pull; 0 paid / reversed columns in NB01, NB02, NB03 and NB05 (NB06 not checked by this pattern) | Yes |
| Rejection rate computed after the join | Not built (no rate column in NB01) | Section 7 work |

**Verdict: Confirmed.**

### V3 SGLT2 add-on pool: "Needs prep"

| Claim | Evidence | Result |
| --- | --- | --- |
| Needs patient-level state per month (on SGLT2, no Kerendia) | No such table: `pj_pat_sglt2_filter_m` has `ELIGIBLE_PATIENT_FLAG`, stage, `HF_FLAG`, `DM_TYPE` only; no SGLT2 / Kerendia status column. NB01 and NB05 count SGLT2 claims and starts per HCP, not patients on SGLT2 without Kerendia | Yes |
| Needs the HCP-patient bridge (6.1) | No patient-state table has an HCP column (section 4 below) | Yes |

**Verdict: Confirmed.**

### V4 Calls, V5 Practice: "Out of scope"

Not LAAD; none of the five notebooks covers them. **N/A.**

### V6 Eligible panel: "Blocked"

| Claim | Evidence | Result |
| --- | --- | --- |
| `pj_pat_sglt2_filter_m` built before the C1 fix, only `ELIGIBLE_PATIENT_FLAG` | Columns: `PATIENT_ID`, `SVC_DT_M`, `ELIGIBLE_PATIENT_FLAG`, `GFR_UACR_DX_STAGE`, `GFR_DX_STAGE`, `UACR_STAGE`, `HF_FLAG`, `DM_TYPE`, `PULL_DT`: no per-indication flags. Mean flag 0.7697 (06 QC), matching the readiness 77% | Yes |
| Eligible features downstream are affected | NB06: 140 eligible columns read this table (06 QC F1, blocker). NB02: 24 `ELIGIBLE_PATIENTS` columns read it (02 QC F1, blocker). Both compute correctly from the table (traces 0 mismatches), so the issue is the input | Yes, wider than V6: existing NB02 / NB06 features are affected too |
| Fix = PJ06 re-run with C1 | Readiness 8 Q8: C11 (variant B) implemented in PJ06, not yet run; next full run writes it | Open |

**Verdict: Confirmed.** Until the PJ06 re-run, the 164 eligible columns in NB02 + NB06 should not be used in feature selection.

### V7 CKD stage mix: "Needs prep"

| Claim | Evidence | Result |
| --- | --- | --- |
| `CKD_SUBSTAGE` has only 3a / 3b / ESRD; stage 2 and 4 from `DX_STAGE` (section 4) | Dx pull `CKD_SUBSTAGE`: 3a 24,512,925, 3b 20,661,766, ESRD 102,803,207, null otherwise. `DX_STAGE` 0-5 (0 = 265,726,135; 2 = 9,452,467; 4 = 16,730,920) | Yes |
| `pj_pat_new_ckd_stage` has no HCP column | Columns `PATIENT_ID`, `SVC_DT_M`, `NEW_CKD_STAGE`, `PULL_DT` | Yes |
| Current features do not follow the 6.2 rule | NB03 counts the coded `DX_STAGE` per claim, no 3a / 3b; its patient-stage columns use the Dx-first `NEW_CKD_STAGE` (03 QC, F5). NB02 counts tests by eGFR stage 1-5 / UACR A1-A3, no 3a / 3b, no damage rule (02 QC). NB06 counts the PJ06 Dx-first `GFR_DX_STAGE`, stage 3 not split (06 QC F7) | Yes: V7 is new Track C work |

**Verdict: Confirmed.**

### V8 HF: "Needs prep"

| Claim | Evidence | Result |
| --- | --- | --- |
| Source `pj_dm_hf_flags` + bridge | Patient-level table: `HF_FLAG`, `HF_TYPE`, `HF_FIRST_DATE`, DM flags; no HCP column | Yes |
| HFpEF-proxy adequacy open | NB06 already counts HF patients by `HF_TYPE` (HFPEF_PROXY / HFREF_PROXY / MIXED / UNKNOWN), 80 HF columns, 0 mismatches (06 QC); 12M HFpEF-proxy non-zero on 91.05% of rows. Adequacy of the proxy not tested | Yes |

**Verdict: Confirmed.** NB06 HF columns can serve as a Track R stand-in, but they also sit on the eligible spine (stale input, V6).

### V9 T1D + CKD: "Ready for pilot"

| Claim | Evidence | Result |
| --- | --- | --- |
| Source `pull_dx_step4` with `DM_TYPE`, `DX_STAGE` | Both columns present; `DM_TYPE` T1D on 1,393,020 rows | Yes |
| Can be expressed as an event-level filter | T1D rows never carry a CKD stage: `CKD_SUBSTAGE` null on all T1D rows (spot check) and all T1D rows are `DX_STAGE` 0 (03 QC). A single-row filter `DM_TYPE = 'T1D' AND DX_STAGE > 0` returns 0 rows; the view needs a patient-level join of E10 claims with N18 claims | **No**: needs patient-level prep |
| Volume | Patients with an E10 and an N18 claim in the same month: 10,709 (Mar 2026) .. 9,949 (Sep 2026), about 10k per month | Enough data for a pilot |
| Little history since Sep 2026 approval | The E10 + N18 population was about 10k per month in every month checked (Mar-Sep 2026); so "little history" probably refers to Kerendia use in T1D since the approval, which was not checked | Not checked |

**Verdict: Partly confirmed.** Data is there, but "Ready for pilot" needs a patient-level E10 x N18 step (or the bridge), not a `filter_condition` on one claim table.

### V10 Lab monitoring: "Ready after dedup check"

| Claim | Evidence | Result |
| --- | --- | --- |
| Test types UACR, GFR, POTASSIUM, HBA1C present | GFR 174,588,290 rows (198,843 NPIs); POTASSIUM 61,583,584 (162,988); HBA1C 38,370,788 (144,807); UACR 32,918,919 (151,202) | Yes |
| Confirm S3 dedup | 0 exact duplicate rows over all 11 pull columns (spot check). 02 QC reports 8,641 duplicate pull rows under its own key definition (not re-checked here) | Exact dedup applied; key-level duplicates remain open (02 QC) |
| K / HbA1c LabCorp only (L-A) | Not checked (no lab-vendor column in the pull) | Not checked |
| Existing coverage | NB02: test counts by stage plus 48 K > 5.0 / HbA1c >= 9 flag columns (02 QC, X18); K tested 12M holdout +27.0% vs training (02 QC F4) | Partly built in NB02 |

**Verdict: Confirmed** ("Ready after dedup check"): the exact-duplicate part passes; the 02 QC key-level duplicates and the K volume step should be closed before the pilot.

### F9 Completeness: "Needs prep"

Latest-month volume vs the median of the 3 months before (5.4 rule: >= 95%), rows per service month:

| Month | Rx | Rx ratio | Dx | Dx ratio | Lab | Lab ratio |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-07 | 79,144,402 | 1.040 | 11,538,262 | 1.026 | 12,285,908 | 1.599 |
| 2026-08 (last feature month) | 76,788,269 | 0.998 | 10,920,704 | 0.971 | 11,807,606 | 1.074 |
| 2026-09 (lag month, pull end) | 75,126,377 | 0.977 | 10,763,192 | 0.957 | 11,530,696 | 0.977 |

No output has a completeness column. All sources pass the 95% rule for Aug and Sep 2026 (Dx Sep closest at 95.7%). The Lab jump in Jun-Jul 2026 (ratio 1.599 in Jul) matches the 02 QC F4 step. The thin Oct 2026 month in readiness 5.4 is outside the pulls (they end 2026-09-30).

**Verdict: Confirmed** (not built; no window shift needed for this run).

### F10 Trends: "Ready with V2 / V10"

| Claim | Evidence | Result |
| --- | --- | --- |
| 3 months vs previous 3 on a month-bucket view | Only NB01 has trend columns: 12 `RATIO_RX_CLAIMS_<category>_IN_PRIOR_3_LAST_3_MONTH`, treatment categories only (01 QC). None in NB02, NB03, NB05, NB06 | Partly built in Track R |
| Ready together with V2 / V10 | V2 and V10 month-bucket sources are not built (section 7), and the `RollingWindow` + `delay` method has not been tested (readiness 5.2 / 9) | Depends on section 7 |

**Verdict: Partly confirmed.** Rx category trends exist; no rejected (V2) or lab (V10) trends yet.

## 4. Sections 6.1 to 6.3

| Item | Readiness says | Evidence | Result |
| --- | --- | --- | --- |
| 6.1 HCP-patient bridge needed by V3, V6, V7, V8 | No HCP column on patient-state tables | `pj_pat_new_ckd_stage`, `pj_pat_sglt2_filter_m`, `pj_dm_hf_flags`, `pj_px` all keyed by `PATIENT_ID` only (column lists checked). `pj_px.FIRST_DIALYSIS_DATE` is STRING, as section 4 says. NB06 already builds an Rx-only NPI x patient x month grain (06 QC F8); Dx / Lab-only patients are missing | Confirmed; bridge size not measured |
| 6.2 CKD stage: lab first, Dx fallback | Investigation numbers (full tables + 5% sample) | Not re-run. Consistent facts: `CKD_SUBSTAGE` values as section 4; NB03 uses the coded stage per claim, not the carried `DX_STAGE_UPDATED` (03 QC) | Reported, not re-run |
| 6.3 Eligibility test: stored 77% vs current code 18.5% | Stored table written by an earlier code version | Stored side confirmed (mean flag 0.7697, 06 QC). The 18.5% and the variant A / B numbers were not re-run (5% patient sample rebuild) | Partly re-checked |

## 5. Cross-cutting findings

| # | Finding | Views | Severity | Action / owner |
| --- | --- | --- | --- | --- |
| S1 | No `CLAIM_TYPE` / `CLAIM_STATUS` in the Rx pull; rejected claims are counted everywhere (34.0% of Kerendia starts in NB05, 3.37% of eligible patient-months in NB06) | V1, V2 | blocker (RV, paid-only) | PJ03 Step 4d to add `CLAIM_TYPE`; NBA team to decide paid-only for starts / PJ03 owner |
| S2 | `pj_pat_sglt2_filter_m` is the pre-C1 version (77%); 164 eligible columns in NB02 (24) and NB06 (140) depend on it | V6 (and existing features) | blocker | Run PJ06 with C1 / C11, then NB02 and NB06 / pipeline owner |
| S3 | No patient-state table has an HCP column | V3, V6, V7, V8 | blocker for Track C | Bridge (6.1); NB06 Rx-only grain as a start / section 7 |
| S4 | T1D and CKD stage never on the same Dx row | V9 | fix (design) | Build V9 from a patient-level E10 x N18 join, not a single `filter_condition` / section 7 |
| S5 | NB05 output keyed by `PROVIDER_ID` only (readiness 5.1 asks for `NPI_NUMBER`) | V1 (Track R) | fix | Add `NPI_NUMBER` before registering / NB05 owner |
| S6 | Time-since-first pattern exists in `11_adoption_features` (competitors only); no Kerendia group yet, so no time-since-first Kerendia Rx | V1 | note | Add a `KERENDIA` group and approval date to the adoption notebook / feature-engineering owner |
| S7 | Readiness counts out of date: NB01 = 4,681 columns (readiness 4,677) | V1 Track R | doc | Update readiness sections 1 and 7 / Wenjie |
| S8 | Lab key-level duplicates (8,641, 02 QC) and K / HbA1c volume step in mid-2026 | V10, F9 | fix (check) | Close before the V10 pilot / NB02 owner |

## 6. Not re-verified in this QC

* Readiness 6.2 and 6.3 sample numbers (agreement rates, variant A / B counts, 18.5%).
* K / HbA1c LabCorp-only (L-A): no vendor column in the lab pull.
* Kerendia use in T1D since the Sep 2026 approval (V9 "little history").
* HFpEF proxy adequacy (V8), bridge size (6.1), Feature Views behaviour (month-bucket windows, `ApproxCountDistinct`, `RollingWindow` + `delay`).
* Column counts in section 2 are by name pattern; the time-since check (V1) is a name check only.
* Numbers marked "QC" come from the per-notebook QC files and were not re-run here.
