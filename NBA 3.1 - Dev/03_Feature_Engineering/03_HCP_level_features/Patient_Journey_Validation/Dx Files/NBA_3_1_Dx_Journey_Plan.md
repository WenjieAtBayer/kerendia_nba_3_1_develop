# NBA 3.1 – Dx patient journey (PJ02): analysis and plan

**Status (2026-10-29):** Phase A Steps 0-5 built and run in `02_patient_journey_dx`; Step 6 (write) is switched off until review (`WRITE_OUTPUT = False`). Results summary in section 0 below. Open: questions I1–I4 (section 6.3), needed for Phases B–D only.  
**Old notebook:** `Patient_Journey_Validation/(Clone) 02_patient_journey_dx` (kept unchanged as the 3.0 baseline)  
**New notebook:** `Patient_Journey_Validation/02_patient_journey_dx`  
**Current Dx basket:** `Final Product Basket/Kerendia NBA 3.1 - DX Event List.csv` (kept unchanged)  
**New Dx basket:** `Final Product Basket/Kerendia_Dx_Final.csv` (240 rows = 368 codes; 31 staging codes)  
**Proposals used:** `NBA_3_1_Patient_Journey_Changes_Proposals.md`, section 1.1 (D1–D5) and section 6 (P1, P4–P6, P13–P15)  
**Approach:** same as the lab notebook: keep the 3.0 query as the baseline, add one step at a time, and compare each step row by row with the one before.

---

## 0. Implementation results (2026-10-29, for review)

| Step | Check | Result |
| --- | --- | --- |
| 0 | 3.0 query + 3.0 processing vs the table last written by the old notebook | Identical: 37,582 patient-months, 817 patients, 0 differences |
| 2a | Basket vs original Dx Event List | Same 368 codes, same patient counts and flags |
| 2 | Basket query vs 3.0, all US 2025-01 to 2026-09 (patient-days) | Same 70.9M; different 79.4M (all upward: 0→5 52.2M, 0→3 26.8M); gained 37.1M; lost 2,612 (E09.21/E09.29, header codes, ICD-9) |
| 2 | Validation HCPs | Patients 817 → 1,163; patients reaching stage 3: 0 → 690, stage 5: 0 → 326 (matches the proposals doc) |
| 3 | Config query vs Step 2 | Identical rows (368.3M all US; 70,892 validation); 29% fewer rows from Snowflake |
| 4 | Output columns + dropped-rows report | Identical rows; report: before start 27.2%, no provider 12.1%, not in HCP universe 24.9%, kept 35.7% |
| 5 | 3.1 processing vs 3.0 processing (same input) | 33,102 same stage; 5,873 months 0 → null; 14,523 months before first Dx removed; 0 stage changes |

**For review:** (1) add E09.21 / E09.29 to the basket as stage 0? (2) keep "latest staged month wins" (906 validation months 4 → 3)? (3) confirm PJ06 keeps lab-only months now that the Dx journey starts at the first CKD Dx; (4) switch on the write (Step 6).

---

## 1. Current notebook: what it does

| Cell | What it does |
| --- | --- |
| 1–2 | Header (out of date: lists `IQV_LAAD_DX_VW`, `DIM_PRODUCT` and dates 2016/2017, which the query does not use) |
| 3–5 | `00_connection`, `00_config` (`analysis_start_month`, `current_month`, `hcp_universe_path`), `00_cohort_config` |
| 6 | **3.0 Dx query** from Snowflake, HCP universe join on `PROVIDER_ID`, `SVC_DT >= DATA_START_DATE`, 10 validation HCPs |
| 7–10 | QC cells, all commented out (compare with an old dev parquet) |
| 12 | Monthly patient journey: patients × all cohort-months grid, max stage per month, stage 0 → null, forward fill, null → 0, cohort label |
| 13–16 | Rename, drop, print shape, cast `DATE` |
| 17 | Compare with production `df_dx_combine` |
| 18 | Write `kerendia_nba_3_1_dx_journey_validation` |

Output columns: `PATIENT_ID, DATE, DX_STAGE (array of the month's stages), DX_STAGE_UPDATED, cohort_label`.

### 1.1 The 3.0 query in short

1. Reads all of `STG_CAR_IQV_LAAD_FACT_DX`.
2. Left-joins patient demographics (`DIM_PTNT_DMGRPHC`) and the provider table (`DIM_PRVDR`) on `COALESCE(REFERRING, RENDERING)`.
3. Inner-joins `STG_IQVIA_LAAD_DIM_DIAGNOSIS`, filtered to a typed list of **163 codes**.
4. Sets the stage from the **description text**: `CATEGORY = 'CHRONIC KIDNEY DISEASE, STAGE 1'` → 1, ... `LIKE '%STAGE 5%'` → 5, else 0.
5. Filters months with `YEAR*100 + MONTH` between `analysis_start_month` and `current_month`, and keeps rows with a provider.

---

## 2. Bottlenecks found

### 2.1 Query (cell 6)

| # | Hardcoded / issue | Effect | Fix goes in |
| --- | --- | --- | --- |
| Q1 | **163-code list typed in the SQL** | Adding or removing a code means editing the SQL | Basket |
| Q2 | **Codes that cannot match in Dx data (131 of 163):** 32 ICD-9 codes (retired in 2015, e.g. `585.3`, `403.90`, `V42.0`) and 99 dialysis / kidney-transplant **procedure** codes reformatted with a dot as if they were diagnoses: CPT `909.xx` (90918–90999), HCPCS `G03.xx` / `G90.xx`, ICD-10-PCS `5A1.D00Z`, `3E1.M39Z`, `0TY0.0Z0`, ICD-9 procedure `399.5`, `549.8`, `556.9`, and `800`–`889` (most likely dialysis revenue codes 0800–0889) | They can only match by accident. The intent (capture dialysis and transplant) belongs in the Px basket, not here | Basket; move the intent to Px (PJ05) |
| Q3 | **Stage from description text**, not from the code | `N18.30/31/32` (stage 3 unspecified / 3a / 3b, about 9.6M patients in the basket counts) are not in the list, so stage 3 comes only from the old header code `N18.3` (2.6K patients). Stage-5 codes (`N18.5`, `N18.6`, `I12.0`, `I13.11`, `I13.2`) are not in the list. **For the 10 validation HCPs, 3.0 has 0 stage-3 and 0 stage-5 Dx patients** (proposals doc) | Basket (stage per code) |
| Q4 | Header codes (`N18`, `I12`, `I13`, `E11.2`…) and non-basket codes (`E09.21`, `E09.29`, `N25.81`, `Z94.0`) | Small volume; not in the 3.1 basket. To be measured in Step 2 | Basket |
| Q5 | **Descriptions in the basket are cut at 100 characters** (e.g. `I12.9` ends in "OR UNSPECIF") | Any text match on descriptions is fragile; codes must be the key | Basket |
| Q6 | **Date filter** `EXTRACT(YEAR)*100 + EXTRACT(MONTH) >= '{analysis_start_month}'` | Calculated on every row, so Snowflake cannot use the date to skip data; compares a number with a string. A second date filter (`DATA_START_DATE`) is applied later in Spark | Config |
| Q7 | **Unused join:** patient demographics (birth year, gender) are joined but never used; `PRIMARY_SPECIALTY_DESC` selected but not used | Extra cost on the largest table | Code |
| Q8 | **Table and column names** in the SQL (`FACT_DX`, `DIM_DIAGNOSIS`, `DIM_PRVDR`) | A rename breaks the query | Config |
| Q9 | **Provider rule** `COALESCE(REFERRING, RENDERING)` typed twice | The patient is attributed to the referring doctor first; choice not visible | Config |
| Q10 | **`DIAGNOSIS_CODE` not in the output** | No QC by code; cannot check which code set the stage | Code |
| Q11 | **No dropped-rows report** | Losses (no provider, outside HCP universe, codes not found) are silent | Code |

### 2.2 Processing (cell 12) and other cells

| # | Issue | Effect | Fix |
| --- | --- | --- | --- |
| C1 | **Dense grid:** every patient × every month from the global first to the global last month (`crossJoin`) | Fine for 10 HCPs, very large for all US. Rows exist before the patient's first diagnosis | Start each patient at the first Dx month (as the lab notebook does) |
| C2 | **Stage 0 means two things:** "CKD, stage unknown" and "before any diagnosis" (nulls filled with 0) | Downstream cannot tell "known CKD, no stage" from "no CKD yet". In PJ06 the 0 also hides the lab stage (section 8) | **Decided (N1):** `DX_STAGE_UPDATED` = null when no stage is known; new column `DX_CKD_FLAG` = 1 from the first CKD Dx month. No change needed in PJ06 |
| C3 | Grid ends at the max service date, not at `date_end` | End month depends on the data, not the run settings | Use `date_end` |
| C4 | Self-join to add `DX_STAGE_UPDATED` | Extra join with no need | One window column |
| C5 | `DX_STAGE` kept as an **array** in the output | Hard to use; not documented | Replace with `DX_STAGE_MONTH` (max of the month) or drop. Check PJ06 first |
| C6 | Cell 14 prints "# Unique HCPs" but counts patients | Misleading label | Fix label |
| C7 | Cells 7–10 commented-out QC on an old parquet | Dead code | Remove in the new notebook |
| C8 | Cell 17 reads production `df_dx_combine`; the lab notebook's equivalent table disappeared in the refresh | Cell can fail | Skip with a message if the table is missing |
| C9 | Header out of date | Confusing | Rewrite |

---

## 3. Current Dx basket (`Kerendia NBA 3.1 - DX Event List.csv`)

* **240 rows**, columns: `DIAGNOSIS_CODE, DIAGNOSIS_DESCRIPTION, patients_total, is_defining, club_members, n_members, in_752_features, is_clubbed, club_reason`.
* Covers many conditions, not only CKD: T2D (E11.x), T1D (E10.x), other diabetes (E08/E09/E13), heart failure (I50.x, I11.0, I13.x, I09.81), CKD (N18.x, I12.x, I13.x, E1x.2x), dialysis / transplant (Z99.2, Z49.x, Z48.22), anaemia (D63.1, D64.x), PVD / atherosclerosis (I70.x, I73.x), cardiomyopathy (I42.x), secondary / resistant hypertension (I15.x, I1A.0), insulin and drug use (Z79.x, Z96.41, Z46.81, T38.3x), pregnancy diabetes (O24.x), proteinuria (R80.9).
* **5 clubbed rows** with made-up codes (`E11.3x_CLUBBED`, `E10.3x_CLUBBED`, `E08.3x_CLUBBED`, `E13.3x_CLUBBED`, `I70.3xx_CLUBBED`). The real member codes are in `club_members`, so they must be expanded before matching.
* `is_defining` values mix `YES`, `no` and `NO`.
* No stage, condition or role columns, so the notebook cannot use it directly.
* **All 28 codes of the proposed `DX_STAGE_BY_CODE` dictionary are in the basket.** The 4 codes proposed for removal (`E09.21`, `E09.29`, `N25.81`, `Z94.0`) are not.

---

## 4. New basket design (`Kerendia_Dx_Final.csv`)

One row per real ICD-10 code (clubbed rows expanded), same idea as `Kerendia_Lab_Final.csv`.

| Column | Values | Purpose |
| --- | --- | --- |
| `DIAGNOSIS_CODE` | e.g. `N18.31` | Match key (exact code) |
| `DIAGNOSIS_DESCRIPTION` | From the current basket | Reference only, never used to match |
| `CONDITION` | `CKD`, `T2D`, `T1D`, `OTHER_DM`, `HF`, `DIALYSIS`, `TRANSPLANT`, `ANEMIA_CKD`, `PVD`, `CARDIOMYOPATHY`, `HTN_SECONDARY`, `DM_TREATMENT`, `PROTEINURIA`, `OTHER` | Groups codes for the journey and for new flags |
| `ACTIVE_STAGING` | `Y` / `N` | `Y` = used by PJ02 (the CKD subset, decision D1) |
| `CKD_STAGE` | `1`–`5`, `0` = CKD stage unknown, empty = not CKD | Replaces the description-text `CASE` |
| `CKD_SUBSTAGE` | `3a`, `3b`, `ESRD`, empty | For the stage 3a/3b and ESRD features (H2, D3) |
| `DM_TYPE` | `T2D` (E11), `T1D` (E10), `OTHER` (E08, E09, E13), empty | Diabetes type on every diabetes code, including the kidney ones (Phase A, D2). Feeds the T2D / T1D flags (Phase B) |
| `HF_TYPE` | `HFPEF_PROXY` (I50.30–I50.33), `HFREF_PROXY` (I50.20–I50.23), `COMBINED` (I50.40–I50.43), `UNKNOWN` (I50.9, I50.1, I50.8x, I11.0, I13.0, I13.2, I09.81), empty | Heart-failure type proxy for the LVEF ≥ 40% indication (Phase C). Claims do not carry the LVEF value |
| `FLAG` | `DIALYSIS`, `TRANSPLANT`, `HF`, `T2D`, ... or empty | Feeds the planned patient flags (P1, P4–P6, P13–P15) |
| `IS_DEFINING` | `Y` / `N` (cleaned) | From the current basket |
| `CLUB_ID` | e.g. `E11.3x` or empty | Keeps the link to the original clubbed row |
| `PATIENTS_TOTAL` | From the current basket | Reference |
| `NOTE` | Free text | Why a code has this stage or role |

Proposed `CKD_STAGE` values (proposals section 1.1):

| Stage | Codes |
| --- | --- |
| 1 | N18.1 |
| 2 | N18.2 |
| 3 | N18.3, N18.30, N18.31 (3a), N18.32 (3b) |
| 4 | N18.4 |
| 5 | N18.5, N18.6 (ESRD), I12.0, I13.11, I13.2 |
| 0 (CKD, stage unknown) | N18.9, I12.9, I13.0, I13.10, E11.21, E11.22, E11.29, **E10.21, E10.22, E10.29** (decision D2), E08.21, E08.22, E08.29, E13.21, E13.22, E13.29, E09.22, D63.1, Z99.2 (`FLAG = DIALYSIS`, decision D4) |
| Not staged, flag only | Z49.01, Z49.02, Z49.31, Z49.32 (`FLAG = DIALYSIS`); Z48.22 (`FLAG = TRANSPLANT`) (decision D5a); R80.9 (`FLAG = PROTEINURIA`); I15.1, I70.1 (kidney / CV comorbidity flag) (decision D5b) |
| Not staged (`ACTIVE_STAGING = N`) | All other codes: T2D, T1D and other diabetes without kidney involvement, HF without CKD, PVD, ... (decision D1). They keep `DM_TYPE` / `HF_TYPE` / `FLAG` for Phases B–C |

---

## 5. Build plan (new notebook `02_patient_journey_dx`)

Each step adds cells and a comparison with the previous step; the 3.0 query is never changed.

| Step | What | Comparison / check | Expected result |
| --- | --- | --- | --- |
| 0 | Copy the old notebook to the new path; rewrite the header; remove dead QC cells; keep cell 6 as "3.0 baseline" | Same output as the old notebook (10 HCPs) | Identical |
| 1 | Markdown inventory of hardcoded parts (section 2 above) | Review only | – |
| 2 | **Basket:** read `Kerendia_Dx_Final.csv`, checks (duplicate codes, valid stages, clubbed members expanded, every `ACTIVE_STAGING = Y` row has a stage), build the query from the basket; stage from `CKD_STAGE` by code; keep `DIAGNOSIS_CODE` | Part A all US (patient × day): same / different stage / lost / gained, by code. Part B 10 HCPs month by month + stage crosstab | Stage 3 and 5 appear (proposals: 0 → 690 and 0 → 326 patients for the 10 HCPs); dead codes lose nothing; count of patients who enter only through E10.21/22/29 (D2) |
| 3 | **Config:** `DX_CONFIG` (start/end dates applied in the SQL on `SERVICE_DATE`, source/dimension table and column names, provider rule); checks that tables and columns exist; remove the unused demographics join | Part A identical to Step 2; rows pulled before/after | Same output, less data pulled |
| 4 | **Code rules and report:** dropped-rows report (no provider, provider not in HCP universe, code not in basket, outside dates), output columns follow the basket (`DIAGNOSIS_CODE`, `CKD_SUBSTAGE`) | Part A identical to Step 3; report totals | Losses visible |
| 5 | **Processing (section 2):** per-patient month range (first CKD Dx month → `date_end`, N2), one window for forward fill, `DX_STAGE_UPDATED` null when no stage is known plus `DX_CKD_FLAG` (N1), replace the `DX_STAGE` array | Patient-months and stage counts vs Step 4 processing, 10 HCPs; simulate the PJ06 `COALESCE` and count patient-months where the lab stage now shows instead of 0 | Fewer rows (no pre-diagnosis months); staged values unchanged; lab stage no longer hidden |
| 6 | Switch section 2 to the Step 5 output (after review), write `kerendia_nba_3_1_dx_journey_validation` | Write succeeds; schema check against what PJ06 reads | – |
| 7 | Downstream (separate tasks): PJ06 re-run; HCP `Dx_03` with the same basket; Phase B (PJ04 `T2D_FLAG` / `T1D_FLAG` from `DM_TYPE`, P1); Phase C (`HF_FLAG` + `HF_TYPE`, P4) and dialysis / transplant flags (P5–P6); Phase D (PJ06 eligibility per indication) | Stage counts before/after in PJ06 and NB03; eligible patients per indication before/after | – |

---

## 6. Decisions

### 6.1 Decisions on the Dx journey

| # | Decision | Default (proposals) | Alternative |
| --- | --- | --- | --- |
| D1 | PJ02 uses only the CKD subset of the basket | **Decided 2026-10-29: yes.** Only codes with a CKD stage (0–5) have `ACTIVE_STAGING = Y`. PJ02 stays a CKD journey: patients with only diabetes or only heart failure get no Dx journey rows, `DX_CKD_FLAG` means real CKD, and each patient's months start at the first kidney diagnosis. All other codes stay in the basket for the flags of Phases B–C | Use the full basket (rejected: millions of non-CKD patients would enter the journey with `DX_CKD_FLAG = 1`) |
| D2 | T1D kidney codes E10.21/22/29 | **Decided 2026-10-29: include as stage 0** (CKD, stage unknown), the same as E11.21/22/29, with `DM_TYPE = T1D`. Reason: Kerendia is moving to new indications (T1D and HF), so CKD in T1D is in scope. Built in Phase A | Exclude, as in 3.0 (rejected) |
| D3 | ESRD codes | **Decided 2026-10-29: stage 5**, with `CKD_SUBSTAGE = ESRD` for N18.6 (empty for I12.0, I13.11, I13.2, which mean "stage 5 or ESRD"). Reason: downstream code only knows stages 1–5 (section 8) | Separate value 6 (rejected: makes ESRD patients eligible in PJ06, lost in NB03/NB04) |
| D4 | Z99.2 (dialysis dependence) | **Decided 2026-10-29: stage 0 (as 3.0)** and `FLAG = DIALYSIS`. Reason: stage 0 never overrides a real stage, and dialysis patients are already excluded from eligibility by the Px `DIALYSIS_FLAG`; Z99.2 / Z49.x can add to that flag in Step 7 | Stage 5 (rejected) |
| D5a | Z49.01, Z49.02, Z49.31, Z49.32, Z48.22 | **Decided 2026-10-29: not staged.** Z49.01 / Z49.02 (dialysis catheter fitting) and Z49.31 / Z49.32 (dialysis adequacy testing) → `FLAG = DIALYSIS`, together with Z99.2. Z48.22 (kidney transplant aftercare) → `FLAG = TRANSPLANT` (transplant recipients were excluded from the Kerendia trials) | Add to staging (rejected) |
| D5b | R80.9, I15.1, I70.1 | **Decided 2026-10-29: not staged.** Kept for flags: R80.9 (proteinuria) → `PROTEINURIA`; I15.1 (hypertension due to kidney disorder), I70.1 (renal artery atherosclerosis) → kidney / CV comorbidity. Patients with only these codes do not enter the CKD journey | Add to staging (rejected) |
| N1 | Meaning of 0 vs null in the monthly output (C2) | **Decided 2026-10-29: fix in PJ02.** `DX_STAGE_UPDATED` = null when no stage is known (instead of 0), so the PJ06 `COALESCE` falls back to the lab stage; new column `DX_CKD_FLAG` = 1 keeps the "known CKD" information. PJ06 unchanged. Built in Step 5 | Treat 0 as null in PJ06 (not chosen: changes a downstream notebook) |
| N2 | Per-patient month range instead of the global grid (C1) | **Decided 2026-10-29: yes.** Each patient from the first CKD Dx month to `date_end`. Built in Step 5 | Keep the grid (rejected) |
| N3 | Provider rule `COALESCE(REFERRING, RENDERING)` | **Decided 2026-10-29: keep** (same as 3.0 and `Dx_03`). The rule moves into `DX_CONFIG` (Step 3), so it is written once and visible | Rendering first (rejected) |
| N4 | Basket file name and location | **Decided 2026-10-29:** `Final Product Basket/Kerendia_Dx_Final.csv`. The current `Kerendia NBA 3.1 - DX Event List.csv` stays unchanged | Other name (rejected) |

### 6.2 New indications (T1D and HF): 4-phase plan

**Decided 2026-10-29.** Today the PJ06 eligibility rule uses only the CKD stage, SGLT2 use and the Px dialysis flag; it never checks diabetes type or heart failure. To support CKD in T2D, CKD in T1D and heart failure, eligibility becomes indication-specific, built in four phases (each one measured on its own):

| Phase | Notebook | What changes | When |
| --- | --- | --- | --- |
| A | PJ02 + basket | E10.21/22/29 become stage 0 (D2). New basket columns `DM_TYPE` and `HF_TYPE` (section 4). Staging logic otherwise unchanged | Now (Steps 2–6) |
| B | PJ04 (diabetes flag) | Replace the T2D-only `DIABETIC_FLAG` with `T2D_FLAG` and `T1D_FLAG` from `DM_TYPE` (plus Rx where useful), with a rule for mixed E10 / E11 coding (question I2) | Step 7, after PJ02 is validated |
| C | New HF flag (P4) | `HF_FLAG` and `HF_TYPE` proxy for the LVEF ≥ 40% indication | Step 7 |
| D | PJ06 eligibility | Separate `ELIGIBLE_CKD_T2D`, `ELIGIBLE_CKD_T1D`, `ELIGIBLE_HF` and `ELIGIBLE_ANY` instead of one stage-based rule | Step 7, after B and C |

Alignment with the other decisions:
* **D1 stays:** PJ02 remains a CKD journey. HF patients without CKD are covered by the HF flag (Phase C), not by CKD journey rows.
* **Codes in both groups:** I13.0 and I13.2 (hypertensive heart and kidney disease with heart failure) keep their CKD stage (0 and 5) and also get `HF_TYPE = UNKNOWN`.
* **Until Phase D:** T1D patients with CKD stage 2–4 are already counted as eligible by the current PJ06 rule, because it does not check diabetes type. This fits a T1D indication, but they cannot be reported separately before Phases B and D.

### 6.3 Open questions for the new indications

Final alignment from the user is pending. The **provisional choice** is used to start work and can be changed later; none of them affects Phase A except I3.

| # | Question | Why it matters | Options | Needed for | Provisional choice (2026-10-29) |
| --- | --- | --- | --- | --- | --- |
| I1 | **T1D label status:** is the T1D indication approved or expected, and does it use the same eGFR / UACR limits as T2D (start at eGFR ≥ 25)? | Decides whether CKD-T1D is treated like CKD-T2D in eligibility | Same rule as T2D / own rule / flag only until approved. To confirm with Medical | Phase D | Build `ELIGIBLE_CKD_T1D` with the **same stage rule as T2D**, but include it in `ELIGIBLE_ANY` only when a config switch (`T1D_INDICATION_ACTIVE`) is on. Default off until Medical confirms |
| I2 | **Mixed coding:** many patients have both E10 and E11 codes. Which type do they get? | Decides `T1D_FLAG` vs `T2D_FLAG` | (a) most frequent type wins; (b) T1D only if no oral diabetes drugs in Rx; (c) separate `MIXED` value | Phase B | **(a) + (c):** primary type = the type with more claims (tie → T2D), plus `DM_TYPE_MIXED = 1` when both types are coded. Keeps the claim counts so the rule can be changed later (e.g. to (b)) without re-querying |
| I3 | **Scope now:** Phase A in this notebook, Phases B–D as separate tasks after PJ02 is validated? | Keeps each change measurable | Proposed: yes (as in Step 7) / all phases together | Planning | **Yes:** Phase A now (Steps 0–6), Phases B–D in Step 7 |
| I4 | **HF depth:** is a patient-level `HF_FLAG` enough, or is a monthly HF journey (like the CKD one) needed? | Decides whether HF needs its own journey notebook | Patient-level flag + `HF_TYPE` / monthly HF journey | Phase C | **Patient-level with a first date:** `HF_FIRST_DATE` and `HF_TYPE` (most specific type seen). The monthly flag is `DATE >= HF_FIRST_DATE`, the same pattern PJ06 uses for `FIRST_DIALYSIS_DATE`. A full monthly HF journey only if the model needs HF type changes over time |

---

## 7. Notes

* The path given for the Dx basket pointed to the Lab list; the Dx list is `Kerendia NBA 3.1 - DX Event List.csv`.
* `patients_total` in the current basket has no stated window; it is kept as reference only.
* **Compute (2026-10-29):** use the same compute as the lab notebook (user decision). The notebook does not record which compute it ran on. The lab notebook last ran on 2026-10-29 (`00_connection` at 09:28), and the compute used in this session the same day (`1029-091520-d9wzoe57-v2n`) is not in the workspace cluster list, so it is most likely **serverless** (not confirmed). The only classic cluster is `Ananya Cluster` (`0421-124602-2q61io6s`, terminated, DBR 14.3). Serverless is the default for the new notebook; if `00_connection` fails there, switch to `Ananya Cluster`.
* The 3.0 Dx query also feeds the HCP-level `Dx_03` input (NB03). Changing PJ02 alone makes PJ02 and NB03 disagree until `Dx_03` gets the same basket (Step 7).

---

## 8. Downstream use of the Dx stage (checked 2026-10-29, by reading the code)

| Where | Code | How stage 5 is used | What a value 6 would do |
| --- | --- | --- | --- |
| PJ06 `06_patient_journey_combine`, cell 7 | `GFR_DX_STAGE = COALESCE(DX_STAGE_UPDATED, GFR_STAGE)`; `GFR_UACR_DX_STAGE = COALESCE(DX, GFR, UACR)` | Dx stage wins over the lab stage whenever it is not null | 6 passes through into the combined stage |
| PJ06, cell 14 `pat_new_ckd_stage` | `NEW_CKD_STAGE` = stage when it changes month to month | Any value | 6 is written as a new stage |
| PJ06, cell 18 `pat_sglt2_filter_m` (eligibility) | `STAGE_ELIGIBLE`: null/0 → −1 (unknown); **1 or 5 → 0 (not eligible)**; otherwise → 1 (eligible). `DIALYSIS_FLAG = 1` (from Px) → not eligible. Labels: only `STAGE_2/3/4`, everything else `STAGE_UNKNOWN` | Stage 5 = not eligible for Kerendia | **6 → eligible** (falls into "otherwise"), unless the Px dialysis flag catches it. Wrong |
| NB03 `03_claim_diagnosis_monthly_cohort` | Reads `Dx_03` (own query, same 3.0 code list): `DX_STAGE` 1–5 → `STAGE_1`…`STAGE_5`, else `STAGE_UNSPECIFIED`. Reads `pat_new_ckd_stage`: 1–5 → `NEW_TO_STAGE_1`…`_5`, else `NO_NEW_STAGE` | Features `TOTAL_DX_CLAIMS_STAGE_5_*`, `TOTAL_DX_CLAIMS_WITH_PATIENT_NEW_TO_STAGE_5_*` | 6 → `STAGE_UNSPECIFIED` / `NO_NEW_STAGE` (silently lost) |
| NB04 `04_claims_monthly_cohort` | `gfr_label`: 1–5 → `GFR_STAGE_1`…`_5`, else `GFR_STAGE_UNKNOWN` | Features `TOTAL_RX_CLAIMS_PATIENT_WITH_GFR_STAGE_5_*`, `..._DX_GFR_STAGE_5_*` | 6 → `GFR_STAGE_UNKNOWN` (silently lost) |

**Conclusion for D3:** ESRD = stage 5. Every consumer handles 1–5 only; a value 6 would make ESRD patients **eligible** in PJ06 and drop them into "unknown" in NB03/NB04 features. ESRD is kept separately through `CKD_SUBSTAGE = ESRD` (and the Px `DIALYSIS_FLAG` that already exists).

**Side effects of adding stage-5 codes (Step 2):**
* Stage-5 patients become **not eligible** in PJ06 (as intended by the eligibility rule).
* NB03 builds its pivot columns from the values present in `Dx_03`. `Dx_03` uses the same 3.0 code list with no stage-5 codes, so `STAGE_5` columns are probably empty or missing today; once `Dx_03` gets the basket (Step 7), the NB03 schema may gain `STAGE_5` columns. To be checked with data.

**Related finding for N1/N2 (important):** in 3.0, every Dx patient has a row for every month (global grid) with nulls filled as 0. Because PJ06 uses `COALESCE(DX_STAGE_UPDATED, GFR_STAGE)`, a Dx value of **0 is not null, so it hides the lab stage**. A patient with only N18.9 (stage unknown) and a lab eGFR of stage 3 ends up with `GFR_DX_STAGE = 0` (unknown, so "stage unknown" in eligibility). **Fix decided (N1, 2026-10-29):** PJ02 outputs null instead of 0 when no stage is known, plus `DX_CKD_FLAG`. In PJ06, null Dx + null lab still gives "unknown" (−1) in the eligibility rule, the same as 0 today, so only the hidden-lab cases change. To be measured in Step 5.
