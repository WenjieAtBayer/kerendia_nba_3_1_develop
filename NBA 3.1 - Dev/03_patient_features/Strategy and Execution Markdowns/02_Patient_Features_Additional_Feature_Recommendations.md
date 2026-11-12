# NBA 3.1 Patient Features: Changes and Additions

This file lists the patient-feature changes for NBA 3.1: which NBA 3.0 features to remove or rebuild (section 1), and which new features to add (section 2). How the NBA 3.0 features are built, plus the full list of patient features in the final 752-feature model, is in the companion file `NBA_3_1_Patient_Features_Analysis.md`. References written as "Analysis 1.x" point to sections in that file.

SHAP ranks and shares come from `Final NBA 3.0 Modeling Features.xlsx` (752 features, mean absolute SHAP). Lift and fill rates come from the v3.1 quick-win output `notebook_output/patient_v31_quick_win_features` (cohort I01). Lift = writer rate in the top 20% of the feature / writer rate in the bottom 20%, computed inside 3 panel-size groups. Above 1.5 is a useful signal, and about 1.0 means no signal.

---

## 1. Features to remove or change in NBA 3.1

| # | Feature group | Action | Reason |
| --- | --- | --- | --- |
| 1 | `total_events`, `unique_events`, `total_events_time_N_days` without a type suffix | Drop | Exact duplicates of the type-suffixed versions. Zero mismatches confirmed |
| 2 | First occurrence for long-established drugs (metformin, lisinopril, spironolactone, etc.) | Drop, or cap at 365 days | Measures distance from the data start, not clinical signal. 34 of 243 Rx events have >50% of HCPs within 60 days of the data start (lisinopril 76%, metformin 70%). Keep only for newer drugs (Kerendia, Mounjaro, Inpefa) |
| 3 | The three counts per event (claims per month, events per day window, unique patients per window) | Keep unique patients and event counts, plus one 3- or 6-month change | Near-duplicates. Unique patients is the most meaningful |
| 4 | Change in frequency (absolute difference) | Replace with a log-ratio | The absolute difference grows with HCP volume, so it mostly repeats volume instead of momentum |
| 5 | Split product and diagnosis names (metformin ER (F)/(G)/(Z), insulin pen variants, unspecified-stage CKD codes) | Roll up to drug class or ICD-10 group | One signal is spread across several columns, which dilutes it |

### 1.1 Duplicates (#1)

The recency helper writes `TOTAL_EVENTS`, `UNIQUE_EVENTS` and `{TOTAL,UNIQUE}_EVENTS_TIME_{N}_DAYS` once with no source suffix, and again with the source suffix (`_RX`, `_DX`, `_PX`, `_LAB_DATA`). Because each recency notebook processes one source, the two versions are identical (zero mismatches). This removes 56 columns across the four recency outputs. None of the unsuffixed columns is in the final 752.

### 1.2 First occurrence for long-established drugs (#2)

What the feature measures: days from the HCP's first claim for the drug to the lookback end (Analysis 1.2). The Rx history starts on 2021-01-02. For drugs that HCPs were already prescribing before then, the first claim the data can see is near the data start (left-censored). In that case the value says when the data begins, not when the HCP adopted the drug.

| Check | Result |
| --- | --- |
| Events where >50% of HCPs have their first claim within 60 days of the data start (censored) | 34 of 243 |
| Most censored | lisinopril 76%, amlodipine 76%, losartan 73%, HCTZ 72%, metoprolol succinate 71%, bystolic 71%, furosemide 70%, metformin 70%, metoprolol tartrate 69%, carvedilol 69%, spironolactone 64% |
| Not censored (real adoption signal) | Kerendia 0%, Mounjaro 0%, Inpefa 0%, Entresto 24%, Ozempic 35%, Farxiga 35%, Jardiance 49% |
| Median Spearman correlation with HCP volume | censored events 0.48, uncensored 0.22 |

In the final 752, 8 first-occurrence features hold 1.5% of SHAP. The top ones are `SYNJARDY_XR_RX_FIRST_OCCURRENCE` (rank 34), `TELMISARTAN_HCTZ_RX_FIRST_OCCURRENCE` (56), `ECHO_TESTS_PX_FIRST_OCCURRENCE` (92), `AMILORIDE_HCL_RX_FIRST_OCCURRENCE` (139) and `GFR_LAB_DATA_FIRST_OCCURRENCE` (142). Telmisartan-HCTZ and amiloride are long-established generics. Censored features like these survive selection because they act as a stand-in for HCP size or specialty, which the model already gets from the volume features. They do not carry adoption timing.

**Decision**: drop first-occurrence features for the 34 censored events. Keep them for drugs launched within the data window (Kerendia, Mounjaro, Inpefa, and other recent brands where the share near the data start is low). For the rest, replace the value with `min(days since first claim, 365)` plus a flag `FIRST_CLAIM_BEFORE_WINDOW`. Check whether telmisartan-HCTZ and amiloride are in the 34-event list before training.

### 1.3 Three counts per event (#3)

Each event gets three counts that describe almost the same thing:

| Count | Feature (section in the analysis file) | Unit | In the final 752 | SHAP share |
| --- | --- | --- | --- | --- |
| Claims per calendar month window | `FREQ_*_IN_LAST_{1,2,3,6,12}_MONTH_*` (Analysis 1.6) | Claim lines | 35 | 2.7% |
| Events per day window | `TOTAL_EVENTS_TIME_{N}_DAYS_*` (Analysis 1.4) | Patient-days | 3 | 0.2% |
| Unique patients per day window | `NUM_OF_PATIENTS_THE_HCP_*_IN_LAST_{N}_DAYS_*` (Analysis 1.8) | Distinct patients | 22 | 3.4% |

The claim counts are close to each other across windows (median correlation of 1M vs 3M: Rx 0.96, Dx 0.82, Px 0.90; 3M vs 12M: Rx 0.96, Dx 0.82, Px 0.92), and claim counts follow the same patients as the unique-patient counts. Unique patients is the easiest to interpret ("how many patients does this HCP treat with X") and has the highest SHAP share per feature.

**Decision**: keep `NUM_OF_PATIENTS_*` (90/180/360 d) and the event counts `TOTAL_EVENTS_TIME_*` (by source), plus one 3M or 6M change per event (log-ratio, 1.4). Drop the matching `FREQ_*` claim counts for an event once its unique-patient version exists. Watch: the top patient-pipeline frequency feature, `FREQ_ALBUMIN__URINE_EG_MICROALBUMIN_QUANTITATIVE_IN_LAST_12_MONTH_PX` (rank 20), must keep a unique-patient equivalent (`NUM_OF_PATIENTS_THE_HCP_DID_PROCEDURE_ALBUMIN_URINE_..._IN_LAST_360_DAYS_PX`) before its FREQ version is dropped.

### 1.4 Change in frequency: absolute difference vs log-ratio (#4)

Today the change is the monthly claim rate in the last N months minus the monthly rate in the previous 12 - N months (Analysis 1.7). Correlation of |change| with 12-month volume (median over events):

| Change definition | Rx | Dx | Px |
| --- | --- | --- | --- |
| Current absolute difference, 1M | 0.59 | 0.74 | 0.68 |
| Current absolute difference, 3M | 0.54 | 0.68 | 0.64 |
| Proposed log-ratio, 3M: `ln((f3/3 + 0.5) / ((f12 - f3)/9 + 0.5))` | -0.07 | 0.21 | 0.06 |

The current change feature mostly repeats HCP size: a large HCP moving from 40 to 44 claims per month gets +4, while a small HCP doubling from 2 to 4 gets +2. The log-ratio measures the relative trend separately from size. The 0.5 added to both sides keeps it defined when a period has zero claims.

In the final 752, 33 change features hold 1.5% of SHAP, and 19 of them are 1M or 2M windows.

**Decision**: replace `CHANGE_IN_FREQ_*` with `LOGRATIO_FREQ_* = ln((f_N/N + 0.5) / ((f12 - f_N)/(12 - N) + 0.5))`, only for N = 3 and 6.

### 1.5 Split product and diagnosis names (#5)

* Rx: 36 product stems have more than one variant (79 columns). Examples: metformin (ER F/G/Z, HCL), diltiazem (HCL/SR/XR), glipizide (IR/ER/XL), Levemir (vial/FlexPen/FlexTouch), Fiasp (3), metoprolol (tartrate/succinate/HCTZ). Variants are not duplicates: the median correlation of "HCP ever prescribed" between variants is only 0.34. Splitting them divides one HCP's volume across several sparse columns. The 752 already contains split names, for example `FREQ_DILTIAZEM_HCL_*`, `FREQ_DILTIAZEM_SR_*` and `CHANGE_IN_FREQ_*_DILT_XR_*`.
* Dx: 10 separate CKD stage codes (1, 2, 3, 3a, 3b, 3-unspecified, 4, 5, unspecified, plus hypertensive CKD variants), 28 heart failure codes and 46 T1D codes.

**Decision**: roll up to the product group or class in the new basket. Merge formulation and pen/vial variants into one molecule. Keep fixed-dose combinations with HCTZ separate (different clinical meaning). For Dx, group into CKD 1-2, CKD 3 (3/3a/3b/unspecified), CKD 4, CKD 5/ESRD and CKD unspecified. CKD 1-4 is the label group (eGFR >= 25). Group HF into the types in 2.3.

### 1.6 Where each change is implemented

| Change | Notebook (under `03_Feature_Engineering/01_Patient_Features` unless noted) | What to change |
| --- | --- | --- |
| Duplicates (#1) | `01_rx_features_rec_&_first_occ` and the dx/px/lab recency notebooks | After the recency helper returns, drop the unsuffixed totals before saving |
| First occurrence (#2) | Same notebooks | Keep the list of 34 censored events in `00_config` and drop those columns. For the other established events, add `min(days, 365)` and `FIRST_CLAIM_BEFORE_WINDOW` |
| Three counts (#3) and log-ratio (#4) | `01_rx_frequency_features` and the dx/px/lab frequency notebooks | Generate unique patients only for 90/180/360 d. Drop `FREQ_*` where a unique-patient version exists. Compute `LOGRATIO_FREQ_*` for 3/6M |
| Roll-ups (#5) | Product basket mapping v4 and the Dx event list | Map variants to one `PRODUCT_GROUP`. Map CKD/HF codes to the groups in 1.5 |

---

## 2. Features to add in NBA 3.1

| # | Feature | Source | Hypothesis | Value | Effort |
| --- | --- | --- | --- | --- | --- |
| 1 | Untreated eligible pool | Dx + Rx + Lab | Direct measure of the HCP's addressable pool of Kerendia starts | High | Medium (patient-level join across Dx, Rx and Lab) |
| 2 | 90-day trigger events | Dx (new DKD), Rx (new SGLT2), Lab/Px (new albuminuria test) | Kerendia often starts right after these events. 12-month counts miss the timing | High | Quick win |
| 3 | HF with LVEF >= 40% | Dx + Px (echo) + Rx (loop diuretic, no MRA) | Supports the 2025 HF indication. The current Dx list is mostly systolic or unspecified HF | High for 3.1 | Upstream (Dx grouping) |
| 4 | Potassium barrier | Dx + Rx + Lab | Hyperkalemia is the top safety concern that limits Kerendia use. Nothing captures it today | Medium | Upstream (new codes and a new lab test type) |
| 5 | MRA switch candidates | Rx + Dx | Shows comfort with the MRA class and identifies potential switches to Kerendia | Medium | Quick win |

Source tells which LAAD files a feature needs. Features that combine several sources are built at patient level and end in `_PATIENT`. Single-source features end in `_RX`, `_DX` or `_LAB_DATA`.

### 2.0 Patient-level building blocks (shared by all new features)

Every new feature is built in two steps. First, a patient-level status table is built per cohort from claims by **any** provider, because a patient's diagnoses and therapies do not depend on who coded them. Then the flags are rolled up to each HCP's panel (the distinct patients with any paid Rx, Dx, lab or albuminuria-test claim from the HCP in the lookback). Source: `Extra Notebooks/29_patient_features_v31_quick_wins`, cells B1-C2.

| Building block | Source | Definition |
| --- | --- | --- |
| T2D | Dx | Any ICD-10 `E11*` in the lookback |
| DKD code | Dx | `E11.21`, `E11.22`, `E11.29` |
| CKD (non-ESRD) | Dx | `N18.1-N18.5`, `N18.9`, `I12.9`, `I13.0`, `I13.10`, `E11.21/22/29`, `E08.21` |
| ESRD / dialysis | Dx | `N18.6`, `I12.0`, `I13.11`, `I13.2`, `Z99.2`, `Z49*` |
| Albuminuria Dx | Dx | `R80*` |
| **Diabetic CKD (DKD)** | Dx | T2D and (CKD or DKD code) and not ESRD |
| Rx classes | Rx | From product mapping v4. ACE/ARB = `ACE INHIBITORS AND COMBOS`, `ANGIOTENSIN II RECEPTOR ANTAGONISTS AND COMBOS`. SGLT2 = the 10 `00_config` groups plus `INPEFA`, `BEXAGLIFLOZIN`, `GLYXAMBI`, `SEGLUROMET`. Steroidal MRA = `MINERALOCORTICOID RECEPTOR ANTAGONISTS`. Kerendia = `KERENDIA` |
| Days supply | Rx | Paid claims only. A missing value, or one above 180, is set to 30 (one monthly fill). Fill end = SVC_DT + DAYS_SUPPLY - 1 |
| On ACE/ARB, on SGLT2 | Rx | Paid claim in the last 180 days of the lookback (`ON_THERAPY_RECENT_DAYS`) |
| Never on Kerendia | Rx | No paid Kerendia fill for the patient, from any prescriber, in the full history up to `LOOKBACK_END_DATE` |
| Latest UACR / eGFR | Lab | The patient's most recent result in the lookback. Plausibility filters: eGFR 1-200, UACR 0-20,000 |
| Albuminuria | Lab + Dx | Latest UACR >= 30, or an `R80*` Dx |
| Albuminuria test | Lab + Px | A UACR lab result or CPT 82043 (urine albumin, quantitative) |
| MRA current / stopped | Rx | Current: last fill end >= lookback end - 30 days. Stopped: last fill end + 60 days < lookback end |

Patient counts for cohort I01: 87.3M panel patients, 6.2M with diabetic CKD, 9.4M with a UACR result, 36.0M with an eGFR result.

**Null policy**: `NUM_*` and `TOTAL_*` are 0 when no patient qualifies. `PCT_*` and `RATIO_*` stay null when the denominator is 0, the same as the existing recency features. LightGBM handles nulls natively. Do not fill them with 0.

Feature naming: when a row below lists a stem, there are two features, `NUM_OF_PATIENTS_{stem}` and `PCT_OF_PATIENTS_{stem}` (= NUM / panel size). "Non-zero" = share of HCPs with a non-null, non-zero value. Medians are over non-null values.

### 2.1 Untreated eligible pool (#1): Dx + Rx + Lab

**Business meaning**: the patients this HCP already treats who meet the Kerendia label profile (type 2 diabetes with CKD, already on the standard kidney-protecting therapy) but have never received Kerendia. This is the pool the HCP could start on Kerendia without finding new patients.

**Definition**: patients with T2D + CKD (Dx), on ACE/ARB (Rx), never on Kerendia (Rx). Variants add latest UACR >= 30 and eGFR >= 25 (Lab), which are the label thresholds. The % version has a 2.52 median lift.

| Stem / feature | Sources | Non-zero | Median NUM / PCT |
| --- | --- | --- | --- |
| `IN_HCP_PANEL_WITH_DIABETIC_CKD_IN_LAST_365_DAYS_PATIENT` | Dx | 98.3% | 38 / 0.066 |
| `IN_HCP_PANEL_WITH_T2D_CKD_ON_ACE_ARB_NEVER_ON_KERENDIA_IN_LAST_365_DAYS_PATIENT` | Dx + Rx | 96.5% | 17 / 0.029 |
| `IN_HCP_PANEL_WITH_T2D_CKD_ON_ACE_ARB_NEVER_ON_KERENDIA_AND_UACR_GE_30_IN_LAST_365_DAYS_PATIENT` | Dx + Rx + Lab | 60.1% | 1 / 0.002 |
| `IN_HCP_PANEL_WITH_T2D_CKD_ON_ACE_ARB_NEVER_ON_KERENDIA_AND_UACR_GE_30_AND_EGFR_GE_25_IN_LAST_365_DAYS_PATIENT` | Dx + Rx + Lab | 57.2% | 1 / 0.001 |
| `IN_HCP_PANEL_ELIGIBLE_FOR_KERENDIA_IN_LAST_365_DAYS_PATIENT` (DKD and on ACE/ARB or Kerendia) | Dx + Rx | 96.8% | 18 / 0.031 |
| `IN_HCP_PANEL_ELIGIBLE_AND_ON_KERENDIA_IN_LAST_365_DAYS_PATIENT` | Dx + Rx | 48.4% | 0 / 0 |
| `PCT_OF_DIABETIC_CKD_PATIENTS_IN_HCP_PANEL_UNTREATED_ELIGIBLE_IN_LAST_365_DAYS_PATIENT` (untreated eligible / DKD) | Dx + Rx | 96.5% | median 0.45 |
| `RATIO_KERENDIA_TREATED_TO_ELIGIBLE_PATIENTS_IN_HCP_PANEL_IN_LAST_365_DAYS_PATIENT` (eligible on Kerendia / eligible) | Dx + Rx | 48.4% | median 0.005 |

The UACR and eGFR variants are sparse (57-60% non-zero) because NBA 3.0 lab data covers only primary-care orderers. They fill in once the lab specialty filter is removed.

**New split by background therapy (reviewer request, not built yet)**. The current pool requires ACE/ARB but does not look at SGLT2 or GLP-1 use, so it mixes patients at different steps of the treatment pathway. Add two features:

| New stem | Sources | Definition | Business meaning |
| --- | --- | --- | --- |
| `IN_HCP_PANEL_WITH_T2D_CKD_ON_ACE_ARB_ONLY_NEVER_ON_KERENDIA_IN_LAST_365_DAYS_PATIENT` | Dx + Rx | DKD, on ACE/ARB, no SGLT2 and no GLP-1 claim in the last 180 days, never on Kerendia | Patients on first-line kidney protection only. The HCP is likely to add an SGLT2 first and Kerendia later |
| `IN_HCP_PANEL_WITH_T2D_CKD_ON_SGLT2_OR_GLP1_ONLY_NEVER_ON_KERENDIA_IN_LAST_365_DAYS_PATIENT` | Dx + Rx | DKD, on SGLT2 or GLP-1 in the last 180 days, no ACE/ARB, never on Kerendia | Patients treated with cardio-renal diabetes drugs but without RAAS blockade. Shows HCPs who manage the diabetes side of DKD |

Both need a GLP-1 class in the building blocks (GLP-1 RA product groups from mapping v4, for example Ozempic, Rybelsus, Trulicity, Victoza and Mounjaro; confirm the class name). Build them in cell D3 next to the existing pool, as NUM and PCT of panel.

### 2.2 90-day trigger events (#2): Dx, Rx, Lab/Px

**Business meaning**: trigger events are new clinical moments when a doctor is most likely to add a new therapy. Each one counts patients whose event happened in the last 90 days with no matching event in the 365 days before.

| Trigger | Source | Patient-level definition | % of HCPs with >= 1 | Lift (% version) |
| --- | --- | --- | --- | --- |
| Newly diagnosed diabetic CKD | Dx | First E11.21/E11.22/E11.29 for the patient falls in the last 90 days (no earlier DKD code in history) | 31% | 1.30 |
| New SGLT2 start | Rx | Paid SGLT2 claim in the last 90 days and no SGLT2 claim in the prior 365 days | 74% | 2.21 |
| New albuminuria test | Lab + Px | UACR lab or CPT 82043/82044 in the last 90 days and none in the prior 365 days | 62% | 1.36 |

| Stem | Source | Non-zero | Median NUM / PCT |
| --- | --- | --- | --- |
| `THE_HCP_NEWLY_DIAGNOSED_WITH_DIABETIC_CKD_IN_LAST_90_DAYS_DX` | Dx | 30.9% | 0 / 0 |
| `THE_HCP_STARTED_ON_SGLT2_IN_LAST_90_DAYS_RX` | Rx | 74.0% | 2 / 0.004 |
| `THE_HCP_ORDERED_NEW_ALBUMINURIA_TEST_IN_LAST_90_DAYS_LAB_DATA` | Lab + Px | 62.1% | 2 / 0.007 |

Each trigger has a NUM and a PCT version, 6 features in total, in notebook cell D2. The trigger is credited to the HCP on the claim with the event date. The washout check is done at patient level, across all providers.

Why 90 days: the target is a 30-day NBRx window, and guidelines put the MRA add-on decision at the visit after the DKD diagnosis, UACR result or SGLT2 start, usually within one quarter. The 365-day washout separates a real new event from a continuing patient. Parameters: `TRIGGER_WINDOW_DAYS=90`, `NEW_EVENT_WASHOUT_DAYS=365`.

NBA 3.0 already has `TOTAL_PATIENTS_START_*` features (14 in the 752, claim-based), which count patient starts on a drug class. The new triggers differ because they also cover diagnoses and lab tests, and use a fixed 365-day washout.

### 2.3 HF with LVEF >= 40% (#3): Dx + Px + Rx

**What LVEF is**: left ventricular ejection fraction is the share of blood the heart's main pumping chamber pushes out with each beat, measured by echocardiogram. Normal is about 50-70%. Heart failure is split by LVEF:

| HF type | LVEF | Usual ICD-10 proxy |
| --- | --- | --- |
| HFrEF (reduced) | <= 40% | I50.2x systolic |
| HFmrEF (mildly reduced) | 41-49% | No specific code |
| HFpEF (preserved) | >= 50% | I50.3x diastolic |
| Combined | Mixed | I50.4x combined systolic and diastolic |
| Unspecified | Unknown | I50.9 |

**Business meaning**: Kerendia's heart failure indication (2025, FINEARTS-HF trial) is for HF with mildly reduced or preserved ejection fraction (LVEF >= 40%). HCPs with many such patients are a new target group. Claims data has no LVEF value, so diagnosis codes are the proxy: diastolic HF (I50.3x) is close to HFpEF, and systolic HF (I50.2x) is HFrEF.

The NBA 3.0 Dx list already includes these codes, so no new Dx codes are needed, only a grouping. HCP prevalence: chronic diastolic 27.3%, unspecified diastolic 17.5%, acute-on-chronic diastolic 17.3%, acute diastolic 9.3%. Combined systolic + diastolic is 3.9-13.4%. Echo tests (87%) and natriuretic peptide (79%) are in the Px list. In the final 752, the only HF feature that involves diastolic HF is `FREQ_ACUTE_ON_CHRONIC_COMBINED_SYSTOLIC_CONGESTIVE_AND_DIASTOLIC_CONGESTIVE_HEART_FAILURE_IN_LAST_12_MONTH_DX` (rank 136). No pure diastolic (I50.3x) code survived, because the signal is split across 28 HF columns (see 1.5). The other HF features in the 752 are systolic or unspecified.

**Proposed features (patient level, then rolled up to the HCP)**:

| Feature | Sources | Definition |
| --- | --- | --- |
| `HFPEF_PROXY` | Dx | Any I50.3x in 365 d and no I50.2x / I50.4x |
| `HFPEF_PROXY_WITH_ECHO` | Dx + Px | HFPEF_PROXY plus an echo test within 365 d (confirms the HF work-up) |
| `HFPEF_PROXY_ON_LOOP_DIURETIC_NO_MRA` | Dx + Rx | HFPEF_PROXY, on a loop diuretic (furosemide, bumetanide, torsemide) in the last 180 d, no steroidal MRA or Kerendia. These are symptomatic patients not yet on an MRA, the closest match to the FINEARTS-HF population |

Each as NUM and PCT of panel, plus an "and never on Kerendia" version of `HFPEF_PROXY`. A combined-HF (I50.4x) variant can be tested separately, because combined codes include both reduced and preserved EF patients.

Effort: medium (Dx flags only, plus the existing Rx and Px data). Needs medical sign-off that I50.3x-only is an acceptable proxy for LVEF >= 40%.

### 2.4 Potassium barrier (#4): Dx + Rx + Lab

**Business meaning**: Kerendia must not be started when serum potassium is above 5.0 mEq/L, and potassium is monitored after starting. High potassium (hyperkalemia) is the most common reason doctors do not start an MRA, or stop it. HCPs with many hyperkalemic CKD patients are less likely to start Kerendia, unless they also use potassium binders, which let patients stay on RAAS or MRA therapy.

Missing today: there is no hyperkalemia Dx (E87.5), no potassium binder product (Lokelma, Veltassa) and no potassium lab in the NBA 3.0 data. No feature in the final 752 mentions potassium or hyperkalemia. Only general metabolic panels (BMP 92%, CMP 77%) appear in Px.

**Upstream changes needed**: add E87.5 to the Dx event list, add Lokelma and Veltassa to the product basket, and add potassium (LOINC 2823-3 / 6298-4) to the lab test types in `01_Input_data_creation`.

| Proposed feature | Sources | Definition |
| --- | --- | --- |
| % of DKD patients with hyperkalemia | Dx + Lab | E87.5 Dx or latest K+ > 5.0 mEq/L in the lookback |
| % of DKD patients on a potassium binder | Dx + Rx | Paid Lokelma or Veltassa claim in the last 180 d |

### 2.5 MRA switch candidates (#5): Rx + Dx

**Business meaning**: steroidal MRAs (spironolactone, eplerenone) are used for resistant hypertension and HFrEF. In T2D + CKD, Kerendia is the evidence-based MRA (FIDELIO/FIGARO trials), and steroidal MRAs carry more hyperkalemia risk and side effects (such as gynecomastia). An HCP with T2D + CKD patients on spironolactone is comfortable with the MRA class and has natural switch candidates.

**Do we already use it?** Partly. The final 752 has 17 MRA features (1.4% of SHAP combined). All are HCP-level claim-based features, not patient-pipeline features:

| Feature in the 752 | What it counts | SHAP rank |
| --- | --- | --- |
| `TOTAL_HCP_TRX_CLAIMS_ADD_ON_TO_MINERALOCORTICOID_RECEPTOR_ANTAGONISTS_IN_LAST_6_MONTH` | Add-on claims to an MRA | 82 |
| `PCT_TOTAL_RX_CLAIMS_MRA_30_DAYS_SUPPLY_IN_LAST_12_MONTH` | MRA claims by days supply | 120 |
| `RUNNING_TOTAL_RX_CLAIMS_SPIRONOLACTONE_MRA_90_DAYS_SUPPLY` | Spironolactone claims by days supply | 171 |
| `TOTAL_RX_CLAIMS_PATIENT_WITH_DX_GFR_STAGE_UNKNOWN_WITH_MRA_IN_LAST_{3,6}_MONTH`, `..._UACR_STAGE_UNKNOWN_WITH_MRA_IN_LAST_3_MONTH` | MRA claims for patients with a CKD/UACR-stage Dx | 195, 542, 592 |
| `TOTAL_PATIENTS_START_SPIRONOLACTONE_MRA_IN_LAST_{3,12}_MONTH` | New spironolactone patients | 340, 499 |
| 10 more spironolactone/MRA claim splits (payer, age, refill, new Rx) | Claim volume by segment | 368-666 |

So general MRA volume, MRA starts and MRA use in CKD-stage patients are already covered. Not covered: patients with **T2D + CKD** who are **currently** on a steroidal MRA (switch candidates), and patients who **stopped** an MRA. Check whether the generic `*_MRA_*` groups also include Kerendia. If they do, they mix steroidal and non-steroidal MRA.

**Built features (cell D4, 9 features).** Attribution: patients for whom this HCP wrote spironolactone or eplerenone in the lookback.

| Stem / feature | Sources | Non-zero | Median NUM / PCT | Lift |
| --- | --- | --- | --- | --- |
| `THE_HCP_PRESCRIBED_WITH_STEROIDAL_MRA_IN_LAST_365_DAYS_RX` | Rx | 94.3% | 13 / 0.022 | 0.98 (no signal) |
| `THE_HCP_PRESCRIBED_WITH_STEROIDAL_MRA_CURRENTLY_ON_MRA_WITH_T2D_CKD_RX` | Rx + Dx | 51.3% | 1 / 0.001 | 1.49 |
| `THE_HCP_PRESCRIBED_WITH_STEROIDAL_MRA_THAT_STOPPED_MRA_IN_LAST_365_DAYS_RX` | Rx | 84.5% | 3 / 0.005 | - |
| `THE_HCP_PRESCRIBED_WITH_STEROIDAL_MRA_THAT_STOPPED_MRA_WITH_T2D_CKD_IN_LAST_365_DAYS_RX` | Rx + Dx | 31.9% | 0 / 0 | - |
| `PCT_OF_STEROIDAL_MRA_PATIENTS_THE_HCP_PRESCRIBED_THAT_STOPPED_MRA_IN_LAST_365_DAYS_RX` (stopped / MRA patients) | Rx | 84.5% | median 0.25 | 1.17 |

**Decision**: keep only the T2D + CKD switch-candidate and stopped-MRA versions. Drop general MRA use (`THE_HCP_PRESCRIBED_WITH_STEROIDAL_MRA_IN_LAST_365_DAYS_RX`): it has no signal and repeats the MRA volume features already in the 752.
