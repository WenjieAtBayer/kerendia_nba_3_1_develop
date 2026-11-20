# NBA 3.1 Competitor, Comorbidity, Adoption and Market-Event Features, in Simple Words

This is a plain-language companion to `92_competitor_comorbidity_nba31_readiness_plan.md`. It explains what the plan wants, what has to be done, what changes compared with NBA 3.0, and which business rules apply. It also lists the notebooks built from it in `NBA 3.1 - Dev/03_HCP_Level_Features`.

---

## 1. What the plan wants

The NBA model predicts which HCPs will write Kerendia (a new Kerendia prescription, NBRx) in the next month. Kerendia's label now covers more patients than before:

* type 2 diabetes (T2D) with chronic kidney disease (CKD), as before,
* type 1 diabetes (T1D) with CKD (new),
* heart failure (HF) with LVEF >= 40% (new).

The NBA 3.0 features in four families were built only around CKD, mixed all indications together, or looked into the future. The plan rebuilds those four families so that they:

1. describe the patients Kerendia is now approved for,
2. separate brand Farxiga from the new cheap generic,
3. never use data after the cohort date (no leakage),
4. tell the model when the market changed (Farxiga and Entresto generics).

| Family | Question the features answer |
| --- | --- |
| Comorbidity / Dx panel | How many of the HCP's patients fit a Kerendia indication, and how severe is their CKD? |
| Competitor NBRx share | How much does the HCP start patients on SGLT2s, steroidal MRAs and GLP-1s, and in which patient groups? |
| Adoption speed | How quickly does the HCP start a CKD patient on a newer, guideline-backed drug? |
| Market-event labels | How long ago did the market change (Farxiga generic, Entresto generic), and how did the HCP react? |

Out of scope: prior Kerendia writing (files 07-08) and IQVIA channel (files 05-06).

---

## 2. What needs to be done

### 2.1 Before building (data checks, Phase 0)

| # | Check | Status on 2026-11-17 |
| --- | --- | --- |
| V1 | How many SGLT2 / MRA / Entresto NBRx have a usable indication group | Open. The notebook prints the share per drug and month |
| V2 | CKD stage 3 codes N18.30 / N18.31 / N18.32 are in the Dx input | All three codes are present in `dx_input_claims_all_events_features_input` |
| V3 | Medical sign-off on the HF LVEF >= 40% proxy (`I50.3x` and no `I50.2x`) | Open (Medical). Built as specified until then |
| V4 | Which `INDICATION_GROUP` values contain CKD | In LRx V7 (checked on `PERIOD_ID` >= 2025-09-01 only) the values are `CKD`, `T2D + CKD`, `T2D + CKD + HF`, `CKD + HF` (plus `T2D`, `T2D + HF`, `HF`, `OTHERS`). There are no CVD groups in V7 |
| V5 | Farxiga brand vs generic labels | V7 uses `FARXIGA BRAND` and `FARXIGA GENERIC` (not `GENERICS`) |
| V6 | Entresto generic in the inputs | LRx V7 has `ENTRESTO BRAND` and `ENTRESTO GENERIC`. `Rx_01_new` has only `ENTRESTO` (brand), so the adoption features see brand only until the input is re-pulled |
| V7 | GLP-1 products in LRx | Present in V7 (`PERIOD_ID` >= 2025-09-01): Ozempic, Wegovy, Wegovy HD, Rybelsus (semaglutide), Mounjaro, Zepbound (tirzepatide) |
| V8 | Parity with NBA 3.0 | Open |
| V9 | Enough training rows after each event | Open. The event notebook prints rows per cohort before/after each event |
| V10 | Specialty mix of pre-LOE Entresto writers | Open |

### 2.2 Build (Phases 1-4)

| Phase | Notebook in `NBA 3.1 - Dev/03_HCP_Level_Features` | Replaces NBA 3.0 notebook |
| --- | --- | --- |
| 1 Comorbidity | `09_claim_comorbidity` | `09_claim_comorbidity` |
| 2 Competitor | `31_Competitor_drugs_NBRX_share` | `31_Competitor_drugs_NBRX_share` |
| 3 Adoption | `11_adoption_features` | `11_adoption_features_inv_far` |
| 4 Events | `36_market_event_features` | new (no 3.0 notebook) |

Then: experiments E0-E6, gates G0-G3 and the combine notebook `99_Combine_Physician_Data` joining on `HCP_COHORT_ID` (not built here).

---

## 3. What changes compared with NBA 3.0

### 3.1 Changes in every family

| NBA 3.0 | NBA 3.1 |
| --- | --- |
| One row per HCP and month, or one static row per HCP | One row per HCP and cohort (`HCP_COHORT_ID` = `PROVIDER_ID` + `_` + `cohort_id`) |
| Static builds used all data up to the pull date, so training rows saw the future | Every feature uses only data up to the end of the cohort's `lookback_end_date` month |
| 3.0 universe (about 229-234K HCPs) | 3.1 universe without call-only HCPs: 294,727 HCPs (`HCP_Universe_without_call_hcps`) |
| 3.0 volume paths | Read and write only in the 3.1 volume. Inputs: `hcp_level_model/dev_pipeline/query_output`. Outputs: `hcp_level_model/dev_pipeline/notebook_output/hcp_features/<family>` |
| LRx V6 | LRx V7 (`kerendia_laad_based_lrx.kerendia_laad_based_lrx_v7`) |

Cohorts: the 28 claims cohorts (c1-c28, lookback end 2024-05 to 2026-08) in `cohorts/claims`. The plan mentions `cohorts/lrx` for LRx features, but that folder does not exist yet. The LRx notebooks use `cohorts/lrx` when it exists and fall back to the claims cohorts otherwise.

### 3.2 Comorbidity (Phase 1)

| Removed (NBA 3.0, 39 columns) | Why |
| --- | --- |
| Single-month counts and shares | One month is noisy and mostly reflects visit timing |
| Rolling averages over 1/3/6/12 months | Count "patients per active month", not different patients. Windows are one month longer than their name |
| Running totals since 2021 | Grow every run and depend on the data start date |
| 1/3/6-month shares | Redundant; shares could exceed 100% |
| `KD` / `DB-KD` / `CV-KD` groups from `FIN_DIAG_CD` | No HF, no T1D, stage 3 codes missing |

| Added (14 columns) | Meaning |
| --- | --- |
| `NUM_` and `PCT_OF_PATIENTS_IN_HCP_DX_PANEL_WITH_{T2D_CKD, HF_LVEF_GE_40_PROXY, CKD_AND_HF, ANY_KERENDIA_INDICATION}_IN_LAST_365_DAYS_DX` (8) | Patients in the HCP's panel that fit each indication, as a count and as a share of the panel |
| `NUM_OF_PATIENTS_IN_HCP_DX_PANEL_WITH_T1D_CKD_IN_LAST_365_DAYS_DX` (1) | T1D + CKD patients (count only; the share is near 0 for most HCPs) |
| `PCT_OF_PATIENTS_IN_HCP_DX_PANEL_WITH_CKD_STAGE_3_IN_LAST_365_DAYS_DX`, `..._CKD_STAGE_4_...` (2) | Share of the panel in the eGFR range where Kerendia is started |
| `NUM_OF_PATIENTS_IN_HCP_DX_PANEL_WITH_{DIABETIC_CKD, CKD}_IN_LAST_730_DAYS_DX` (2) | Replace the two running totals in the 3.0 model with a fixed 24-month count |
| `LOGRATIO_PATIENTS_ANY_KERENDIA_INDICATION_3M` (1) | Is the HCP's indicated panel growing (last 3 months vs the 9 before)? |

### 3.3 Competitor NBRx share (Phase 2)

| NBA 3.0 | NBA 3.1 |
| --- | --- |
| All indications mixed (most SGLT2 use is T2D, not CKD) | Two scopes: `CKD` (indication group contains CKD) and `ALL` (no filter) |
| Farxiga brand and generic combined | `FARXIGA_BRAND` and `FARXIGA_GENERIC` separately, plus `FARXIGA` combined |
| 12-month window only, plus running total | 3-month and 12-month windows; running total dropped |
| SGLT2s only | Adds steroidal MRA (spironolactone, eplerenone and their brands) and GLP-1 (semaglutide, tirzepatide) |
| Static, joined on NPI and month | Per cohort, `PROVIDER_ID` |

Columns: for each drug D, scope S and window W, `TOTAL_NBRX_{D}_{S}_IN_LAST_{W}_MONTH` and, for SGLT2 drugs, `PERC_{D}_NBRX_SHARE_{S}_IN_LAST_{W}_MONTH` (= drug / all four SGLT2 brands in the same scope and window). Steroidal MRA, Invokana and Steglatro are built as counts in CKD scope. GLP-1 is built as counts and as a share of all GLP-1 + SGLT2 NBRx in the `T2D` and `HF` scopes.

### 3.4 Adoption speed (Phase 3)

| NBA 3.0 | NBA 3.1 |
| --- | --- |
| `TIME_TO_ADOPT_INVOKANA`, `TIME_TO_ADOPT_FARXIGA` (one static row per HCP) | 14 columns per cohort for Invokana, Farxiga, Jardiance, steroidal MRA and Entresto |
| Name suggested "days since launch" | Renamed `MIN_DAYS_TO_PRESCRIBE_{DRUG}_POST_CKD_DIAGNOSIS` |
| - | New `HCP_TIME_TO_ADOPT_{DRUG}` (days from FDA approval to the HCP's first Rx; not for steroidal MRA) |
| - | New `MIN_DAYS_TO_PRESCRIBE_{DRUG}_POST_FIRST_CKD_DIAGNOSIS_ANY_HCP` (CKD date from any provider, so referred patients count) |
| - | New `ENTRESTO_BRAND_ADOPTER_FLAG` (1 = the HCP wrote Entresto before its generic launch, 0 = not) |

### 3.5 Market events (Phase 4, new)

| Column | Meaning |
| --- | --- |
| `DAYS_SINCE_FARXIGA_LOE` | Days from the Farxiga generic launch (2026-04-06) to the cohort cutoff. Negative before the event |
| `DAYS_SINCE_ENTRESTO_LOE` | Days from the Entresto generic launch (2025-07-01, month only in the CI report) to the cohort cutoff |
| `FARXIGA_NBRX_LOGRATIO_POST_PRE_LOE` | Per HCP: Farxiga (brand + generic) NBRx in the 3 months from the launch vs the 3 months before. Empty until the cohort has seen all 3 post months |

Event dates live in a small reference table, so adding an event (Baxfendy, GLP-1 HF guideline, Entresto full generic, a new nsMRA competitor) is a new row, not a code change. Only events with `status = 'build'` become columns.

---

## 4. Business rules applied

### 4.1 General

1. **No future data.** A cohort's features only use claims up to the last day of its `lookback_end_date` month.
2. **Universe.** Every output row is a universe HCP. HCPs without data keep a row with empty or zero features.
3. **Null policy.** Counts (`NUM_*`, `TOTAL_NBRX_*`) are 0 when nothing qualifies. Shares (`PCT_*`, `PERC_*`) are empty when the denominator is 0. `MIN_DAYS_*` and `HCP_TIME_*` are empty when the HCP never prescribed the drug. The model treats empty and 0 differently, so they are not filled.
4. **Windows are calendar months.** "Last 365 days" = the 12 months ending with the lookback-end month; "last 730 days" = 24 months; "last 90 days" / "3M" = 3 months.

### 4.2 Comorbidity

1. **Dx panel** of an HCP = distinct patients with any Dx event-list claim where the HCP is the referring doctor, or the rendering doctor when no referring doctor is given.
2. **Patient flags** come from claims by **any** provider in the window, so a nephrologist gets credit for a T2D diagnosis made by the PCP.
3. **Code groups (ICD-10):**

| Group | Codes |
| --- | --- |
| T2D | `E11*` |
| T1D | `E10*` |
| CKD (not ESRD) | `N18.1`-`N18.5` (incl. `N18.30/31/32`), `N18.9`, `E11.21/22/29`, `E10.21/22/29`, `I12.9`, `I13.0`, `I13.10` |
| ESRD / dialysis (excluded) | `N18.6`, `Z99.2`, `I12.0`, `I13.11`, `I13.2` |
| CKD stage 3 | `N18.3`, `N18.30`, `N18.31`, `N18.32` |
| CKD stage 4 | `N18.4` |
| HF | `I50*` |
| HF LVEF >= 40% proxy | an `I50.3x` code and no `I50.2x` code in the window (needs Medical sign-off) |

4. **Combinations:** T2D + CKD = T2D and CKD and not ESRD. T1D + CKD = T1D and CKD and not ESRD. CKD + HF = CKD and HF and not ESRD. Diabetic CKD = (T2D or T1D) and CKD and not ESRD. Any Kerendia indication = T2D + CKD, or T1D + CKD, or the HF proxy.
5. **Log-ratio:** `ln((n_3M / 3 + 0.5) / ((n_12M - n_3M) / 9 + 0.5))`, where n = panel patients with any Kerendia indication in the window.

### 4.3 Competitor NBRx share

1. Source: LRx V7, `NBRX`, all claim weeks (`PERIOD_TYPE` W and X do not overlap).
2. Month = `trunc(PERIOD_ID, 'month')`.
3. CKD scope = `INDICATION_GROUP` contains `CKD`. T2D scope contains `T2D`. HF scope contains `HF`.
4. SGLT2 denominator = Farxiga (brand + generic) + Jardiance + Invokana + Steglatro in the same scope and window, as in NBA 3.0.
5. Kerendia is the target, so it is never a competitor feature.
6. Reading rule (D8): a high CKD-scoped SGLT2 share is expected to be **positive** for Kerendia (SGLT2 + Kerendia are paired first-line in HF). A model that learns the opposite should be reviewed.

### 4.4 Adoption speed

1. Gap = days from the patient's first CKD Dx (`Dx_03`) to the patient's first Rx of the drug from this HCP. Negative gaps are dropped. The feature is the smallest gap over the HCP's patients.
2. Farxiga: Dx and Rx on or after 2021-04-01 (CKD label). Invokana: on or after 2019-10-01 (before the data start, so no effect). Other groups: full history from 2021-01-02.
3. FDA approval dates for `HCP_TIME_TO_ADOPT_*` (confirm with Medical): Invokana 2013-03-29, Farxiga 2014-01-08, Jardiance 2014-08-01, Entresto 2015-07-07. All are before the data start, so HCPs who wrote the drug before 2021 look like 2021 starters.
4. Entresto brand adopter = first Entresto Rx before 2025-07-01 and on or before the cohort cutoff.
5. Rejected claims are included (as in NBA 3.0).

### 4.5 Market events

1. `DAYS_SINCE_*` = days from the event date to the cohort cutoff (last day of the lookback-end month). Continuous and negative before the event, so the model can learn that a market settles over time. A 0/1 flag is the alternative tested in experiment E4.
2. The Farxiga log-ratio uses `ln((post + 0.5) / (pre + 0.5))` with pre = 2026-01 to 2026-03 and post = 2026-04 to 2026-06. It is only filled for cohorts whose cutoff is on or after 2026-06-30.

---

## 5. Open items that affect the features

* HF LVEF >= 40% proxy needs Medical sign-off (V3).
* `Rx_01_new` has brand Entresto only; generic sacubitril/valsartan must be added to the pull before the adoption features cover generics (V6).
* `cohorts/lrx` does not exist yet; LRx features use the claims cohorts meanwhile.
* Exact Entresto LOE day (only July 2025 is known) and the full-generic date (2027) need Josh (Q6).
* Indication-group coverage in LAAD is weak (V1), so both CKD and ALL scopes are kept and feature selection decides.
