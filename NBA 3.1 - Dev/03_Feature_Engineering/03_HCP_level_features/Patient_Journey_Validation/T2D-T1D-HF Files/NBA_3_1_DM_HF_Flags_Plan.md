# NBA 3.1 – Diabetes type and heart failure flags (PJ04): analysis and plan

**Status (2026-10-30):** built and run in `04_patient_journey_dm_hf_flags`, Steps 0–5. Decisions D1–D6 taken (section 6) and open for team review. Step 5 (write) is switched off (`WRITE_OUTPUT = False`); PJ06 keeps reading the 3.0 T2D table.  
**Folder:** `Patient_Journey_Validation/T2D-T1D-HF Files/`  
**Old notebook:** `04_patient_journey_t2d_flag` (3.0, logic unchanged; only its `%run` path was updated after the folder move)  
**New notebook:** `04_patient_journey_dm_hf_flags`  
**Code lists:** `Final Product Basket/Kerendia_Dx_Final.csv` (read only, columns `DM_TYPE`, `HF_TYPE`) + `Final Product Basket/Kerendia_Dx_Flag_Additions.csv` (new, 116 codes)  
**Approach:** same as the Lab, Dx, Rx and Px notebooks: rerun the 3.0 logic as the baseline, then add one step at a time and measure each change.  
**Scope:** patient-level flags. Monthly flags and eligibility per indication are built in PJ06 (section 7).

---

## 0. Implementation results

Run 2026-10-30, all US patients and validation patients (4,238 patients of the lab, Dx and Rx validation tables). Claims up to `date_end` = 2026-09-30.

| Step | Check | Result |
| --- | --- | --- |
| 0 | 3.0 T2D rule rerun as one Snowflake query vs the table written by the old notebook | Identical: 77,186,262 patients, 0 only in the rerun, 0 only in the table. 2,024 diabetes-drug NDCs from 70 products |
| 1 | Basket codes vs a word search of the diagnosis dimension (ICD-10) | T2D 124 word match / 86 basket / 38 added; T1D 120 / 52 / 68; HF 35 / 26 / 10. 0 codes not covered. I50.1 is in the basket but not in the HF word match. With the additions, T2D codes equal the 3.0 list (assert in the cell) |
| 2 | Settings and building blocks | Config check passed; basket read from `../../Final Product Basket` |
| 3 | All-US counts (aggregated in Snowflake) | Section 5 |
| 4 | Validation patients; Snowflake flags vs an independent pandas recount from the raw claim rows | 0 differences for `DM_TYPE`, `HF_TYPE`, `HF_FIRST_DATE`; 0 duplicate patients |
| 5 | Write | Switched off |

---

## 1. Old notebook: what it does

`04_patient_journey_t2d_flag` writes `kerendia_nba_3_1_t2d_patient_validation`: one row per patient, `DIABETIC_FLAG` = 1.

| Part | Rule |
| --- | --- |
| Dx | Any claim with a code whose description contains `TYPE 2 DIABETES` (word match on `STG_IQVIA_LAAD_DIM_DIAGNOSIS`), rendering provider present, any date |
| Dx sources | `PHCDW_DISCOVERY.STG_IQV_LAAD_DX` (latest version of each claim, until 2018-05-31) + `PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FACT_DX` (from 2021-01-02) |
| Rx | Any claim of an NDC whose product is in `kerendia_pcp.diabetes_product` with `LOGIC = 1`, or `LOGIC = 2` and not an injection (`diabetes_product_injection_mapping`) |
| Result | Dx OR Rx |

PJ06 joins this table as `DIABETIC_FLAG` (one row per patient).

---

## 2. Findings on the 3.0 logic

1. **No T1D.** T1D is not identified. A T1D patient with a single T2D claim, or with any drug from the 3.0 list, is counted as T2D: 1,165,299 of the 3.0 T2D patients have more T1D than T2D claim days.
2. **No HF.** There is no heart failure flag.
3. **SGLT2 alone.** 2,480,584 of the 3.0 T2D patients have no T1D/T2D code and their only 3.0 diabetes drug is an SGLT2 on its own (Farxiga, Jardiance, Invokana, Steglatro); 1,095,883 of them have an HF code.
4. **No end date.** The 3.0 flag uses all claims; 7,555 patients have T2D codes only after `date_end`.
5. **Codes by word match, not by list.** The 3.0 word match finds 124 T2D codes; the basket has 86 of them. The 38 others are E11 parent codes, retinopathy eye-side codes (e.g. E11.3393, 447,260 patients) and O24.1x (pre-existing T2D in pregnancy).
6. **ICD-9.** The word match does not find ICD-9 codes (their description says `TYPE II`). Patients with ICD-9 codes only: T2D 4,347,621, T1D 1,140,938, HF 3,127,750.
7. **Dx gap.** No Dx claims from 2018-06 to 2020-12 (history table ends 2018-05-31, LAAD fact starts 2021-01-02).
8. **Performance.** The old notebook pulls every (patient, NDC) pair into Spark to filter the drugs; the new notebook filters the NDC list in Snowflake.

---

## 3. New logic

One Snowflake query (`build_flags_query`), one row per patient with any flag. Claims up to `date_end`, rendering provider present.

| Column | Rule |
| --- | --- |
| `T2D_FLAG_30` | The 3.0 `DIABETIC_FLAG` (any T2D code at any date, or a 3.0 diabetes drug), kept for PJ06 |
| `T2D_DX_DAYS`, `T1D_DX_DAYS` | Distinct service dates with a T2D / T1D code |
| `DM_TYPE` | `T1D` if T1D days > T2D days; `T2D` if T2D days >= T1D days (> 0). No T1D/T2D code: `T2D` if a 3.0 diabetes drug other than an SGLT2 alone (D1), else `OTHER` if an other-diabetes code (E08/E09/E13), else empty |
| `T2D_FLAG`, `T1D_FLAG` | `DM_TYPE` = T2D / T1D |
| `DM_MIXED` | 1 when both T1D and T2D codes are present |
| `RX_T2D` | Any 3.0 diabetes drug |
| `RX_T2D_NON_SGLT2` | Any 3.0 diabetes drug other than an SGLT2 alone |
| `HF_FLAG` | Any HF code |
| `HF_TYPE` | `MIXED` (combined code, or both HFrEF and HFpEF codes), `HFREF_PROXY` (systolic, I50.2x), `HFPEF_PROXY` (diastolic, I50.3x), else `UNKNOWN` |
| `HF_FIRST_DATE` | First HF claim |

Output: `kerendia_nba_3_1_dm_hf_flags_validation` (`ops_pipeline/query_output/`), not written.

---

## 4. Code lists

| Flag | Basket (`Kerendia_Dx_Final.csv`) | Additions (`Kerendia_Dx_Flag_Additions.csv`) | Total |
| --- | --- | --- | --- |
| T2D | 86 | 38 (E11 parents, retinopathy eye-side codes, O24.1x) | 124 |
| T1D | 52 | 68 (E10 parents, eye-side codes, O24.0x) | 120 |
| HF | 26 | 10 (I50, I50.2, I50.3, I50.4, I50.8, I50.81 parents, I50.83, I97.13x) | 36 |
| OTHER diabetes | 101 | 0 | 101 |

The additions file has the same columns as `Kerendia_Dx_Final.csv`. It is separate because the Dx journey (PJ02) checks that its basket codes equal the original DX Event List (D6).

---

## 5. Numbers

**All US patients**

| Measure | Patients |
| --- | --- |
| Patients with any flag code or 3.0 diabetes drug | 88,896,145 |
| T2D flag 3.0 | 77,186,262 |
| T2D code, any date (basket + additions) | 54,315,151 |
| T2D code from the basket only | 54,253,172 |
| 3.0 diabetes drug | 51,780,610 |
| `DM_TYPE` = T2D | 73,532,765 |
| of them by Rx only (no T1D/T2D code) | 20,196,245 |
| SGLT2 alone and no T1D/T2D code (T2D in 3.0, not T2D now, D1) | 2,480,584 (1,095,883 with HF) |
| `DM_TYPE` = T1D | 1,949,479 |
| of them T2D in 3.0 | 1,165,299 |
| of them only through added codes | 19,751 |
| `DM_TYPE` = OTHER | 342,430 |
| `DM_MIXED` = 1 | 3,625,338 (966,140 T1D; 143,765 ties set to T2D) |
| T2D in 3.0, no `DM_TYPE` now | 2,479,429 |
| `HF_FLAG` = 1 | 23,763,719 (5,065 only through added codes) |

**3.0 T2D vs 3.1 T2D:** 77,186,262 → 73,532,765 (−3,653,497) = 2,471,874 SGLT2 alone without a flag + 8,710 SGLT2 alone with an other-diabetes code (now OTHER) + 1,165,299 now T1D + 7,555 T2D codes only after `date_end` + 59 now OTHER.

**HF by type and diabetes type**

| `HF_TYPE` | T2D | T1D | OTHER | No diabetes | Total |
| --- | --- | --- | --- | --- | --- |
| HFPEF_PROXY | 3,117,540 | 42,284 | 14,719 | 2,996,035 | 6,170,578 |
| HFREF_PROXY | 2,034,796 | 31,245 | 10,387 | 2,324,418 | 4,400,846 |
| MIXED | 3,064,987 | 39,503 | 13,648 | 2,239,110 | 5,357,248 |
| UNKNOWN | 3,638,127 | 58,017 | 19,877 | 4,119,026 | 7,835,047 |
| Total | 11,855,450 | 171,049 | 58,631 | 11,678,589 | 23,763,719 |

**Validation patients (4,238)**

| Measure | Patients |
| --- | --- |
| T2D flag 3.0 | 2,490 |
| `T2D_FLAG` | 2,339 |
| `T1D_FLAG` | 39 (36 T2D in 3.0) |
| `DM_MIXED` | 205 |
| `HF_FLAG` | 1,309 (MIXED 424, HFPEF_PROXY 420, UNKNOWN 315, HFREF_PROXY 150) |

---

## 6. Decisions (2026-10-30)

Taken on the user's instruction to apply the recommended option for each question and document it for team review.

| # | Question | Decision | Effect |
| --- | --- | --- | --- |
| D1 | No T1D/T2D code, only 3.0 diabetes drug is an SGLT2 alone | Not T2D. Kept in `T2D_FLAG_30`; visible as `RX_T2D` = 1, `RX_T2D_NON_SGLT2` = 0 | −2,480,584 T2D |
| D2 | Both T1D and T2D codes | More claim days wins, tie goes to T2D, `DM_MIXED` = 1 | 966,140 T1D, 143,765 ties |
| D3 | Insulins in the 3.0 drug list (e.g. Tresiba, Fiasp, Afrezza) | Kept as in 3.0; they count only when there is no T1D/T2D code | None |
| D4 | CKD / eGFR eligibility for T1D | Not decided in PJ04; belongs to PJ06. Proposal: same CKD stage rule as T2D | None in PJ04 |
| D5 | ICD-9 codes | Not used, as in 3.0 | 4,347,621 T2D, 1,140,938 T1D, 3,127,750 HF ICD-9-only patients out |
| D6 | Additions file | Kept separate; merge into `Kerendia_Dx_Final.csv` with Saurabh once Dx 3.1 is live | None |

---

## 7. Next steps

1. Team review of D1–D6.
2. Switch on the write (Step 5) together with the 3.1 Dx table (same go-live rule as Rx and Px).
3. PJ06 update (on hold until all journeys go live): read `kerendia_nba_3_1_dm_hf_flags_validation` instead of the 3.0 table (`DIABETIC_FLAG` = `T2D_FLAG_30` for parity, or `T2D_FLAG` for 3.1); monthly HF flag `month >= HF_FIRST_DATE`; eligibility per indication (T2D + CKD, T1D + CKD, HF); dialysis exclusion unchanged.

---

## 8. Files

| File | Change |
| --- | --- |
| `T2D-T1D-HF Files/04_patient_journey_dm_hf_flags` | New notebook |
| `T2D-T1D-HF Files/04_patient_journey_t2d_flag` | Moved; `%run "../../00_cohort_config"` |
| `T2D-T1D-HF Files/NBA_3_1_DM_HF_Flags_Plan.md` | This file |
| `T2D-T1D-HF Files/NBA_3_1_DM_HF_Flags_Client_Summary.md` | Client summary |
| `Final Product Basket/Kerendia_Dx_Flag_Additions.csv` | New, 116 codes |
| `Final Product Basket/Kerendia_Dx_Final.csv` | Not changed |
