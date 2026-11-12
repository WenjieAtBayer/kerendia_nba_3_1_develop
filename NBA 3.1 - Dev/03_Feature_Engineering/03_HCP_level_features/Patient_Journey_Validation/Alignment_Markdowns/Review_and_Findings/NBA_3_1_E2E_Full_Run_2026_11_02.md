# NBA 3.1 patient journey: full HCP universe run, what changed vs 3.0, and what it does to the results

**Run:** 2026-11-02, job `NBA 3.1 Patient Journey (PJ01-PJ06)`, run 1066154679479482. All six journey steps (lab, Dx, Rx, Px / dialysis, diabetes / heart-failure flags, combine) on the **complete 3.1 HCP universe**.
**Settings:** `VALIDATION_MODE = false` (no test-HCP filter); HCP universe = 3.1 `HCP_Universe_without_call_hcps` (Parquet, 294,726 HCPs after dropping `PROVIDER_ID = 0`); output in `query_output/full_2026_11_02/`.
**Compared with:** the 3.0 full outputs in `query_output/` (written 2026-10-27; 3.0 universe of 234,404 HCPs; Jan 2021 - Oct 2026). Comparisons use only the months both runs cover: **Jan 2023 - Sep 2026**.
**Like-for-like check:** the same 3.1 code was also run on the patients of the 10 test HCPs and compared with 3.0 for the same patients (`query_output/validation_2026_10_30/`). Those numbers are shown as "10 HCPs" where they explain a difference better than the full run can (see 4.2).

## 1. In short

* **3.1 full journey:** 148.0M patients, 4.12B patient-months, 3.17B eligible patient-months, 125.1M patients eligible in at least one month.
* **Eligible patients per month are 7-13% higher than in 3.0** (Sep 2026: 77.5M vs 68.3M). Part of this comes from the larger HCP universe (+26% HCPs), so not all of it is caused by the 3.1 logic.
* **Patients are classified more precisely.** 3.1 reads the stage 3a / 3b and stage 5 / ESRD codes that 3.0 could not read. About 1.0M patients are now correctly excluded as stage 5. The new dialysis code list moves patients in both directions (14,561 newly excluded, 44,854 eligible again).
* **The SGLT2 rule issue (section 6, C1) decides more than half of eligibility:** 56% of the eligible months have no known stage and never an SGLT2. With the rule as intended, they would not be eligible. This is already in 3.0 (78% there).
* **Diabetes is not required for eligibility (C9):** 58% of the eligible months belong to patients with no T1D or T2D diagnosis.
* **New in 3.1:** diabetes type (`DM_TYPE`) and heart failure per patient, and a monthly `HF_FLAG` in the eligibility table. They are reported but **do not change eligibility yet** (that needs the 3.1 rules per indication, C3).
* **One baseline question to settle (B1):** the 3.0 full combine table uses far fewer lab stages than the 3.0 lab journey contains. Most of the full-scale difference with 3.0 comes from this, not from 3.1 (section 4.2).
* **Section 8 lists every decision that affects these results.** Please review in particular the ones marked "Our choice, please confirm".

## 2. What changed between 3.0 and 3.1, per step

| Step | What 3.0 did | What 3.1 does | Full universe: 3.1 vs 3.0 |
| --- | --- | --- | --- |
| **Lab** (eGFR / UACR stage) | Lab codes and settings written in the query | Lab codes from the basket file; settings in one place | 64.6M vs 65.6M patients; 1.75B vs 2.21B patient-months (3.0 covers 2 more years). On the 10 HCPs: 30 of 6,171 months differ |
| **Dx** (CKD stage from diagnoses) | Stage taken from the **text** of the diagnosis description. Stage 3a / 3b (N18.30-N18.32) and stage 5 / ESRD codes were not in the list, so they gave "stage 0". Every patient had a row for every month, even before the first diagnosis | Stage taken from the **code**, using the basket file (31 staging codes). Patient starts at the first CKD diagnosis. "No stage known" is now empty instead of 0, so the lab stage can be used for those months | 16.7M vs 16.0M patients (497.7M vs 409.2M rows). Stage 3 and stage 5 now appear (section 5) |
| **Rx** (treatments) | Product list written in the query; fills before the start date not counted | Product list from the basket; a fill started before the start date still counts for the months its days of supply cover (97-day look-back) | 113.3M patients, 2.84B patient-months. On the 10 HCPs: 98.8% of shared months have the same drug classes; nearly all others only gain a class |
| **Px** (first dialysis date) | Dialysis code list written in the query | Code list from the basket: dialysis sessions, monthly ESRD services, home dialysis training and dialysis drugs count; **access procedures** (catheters, fistulas) **no longer count** on their own | 1,537,460 vs 1,489,202 patients with a dialysis date |
| **Diabetes / HF flags** (new) | Only "diabetic yes / no" | Keeps the 3.0 diabetic flag, and adds diabetes type (T2D / T1D, mixed) and heart failure (with HFrEF / HFpEF proxy and first HF date) | 89.0M patients (section 7) |
| **Combine** | Joins the journeys and sets eligibility: stage 2-4 and not on dialysis | Same rules, same output tables; adds `HF_FLAG` and `DM_TYPE` columns to the eligibility table | Sections 3-6 |

## 3. Results

### 3.1 Tables written (`full_2026_11_02/`)

| Table | 3.1 full: rows / patients | 3.0 full: rows / patients |
| --- | --- | --- |
| Lab journey | 1.75B / 64.6M | 2.21B / 65.6M |
| Dx journey | 497.7M / 16.7M | 409.2M / 16.0M |
| Rx journey | 2.84B / 113.3M | – |
| Px (first dialysis date) | 1.54M / 1.54M | 1.49M / 1.49M |
| Diabetes / HF flags (new) | 89.0M / 89.0M | – |
| Treatments, CKD stage, GFR / Dx stage, SGLT2 eligibility (one row per patient-month) | 4.12B / 148.0M each | 4.50B / 156.4M |
| UACR stage (one row per category) | 12.76B / 148.0M | 18.76B / 156.4M |

3.1 covers 46 months (Dec 2022 - Sep 2026; Dec 2022 comes from the Rx look-back). 3.0 covers Jan 2021 - Oct 2026, so 3.0 has more months per patient. "–": no 3.0 full table with the same content.

### 3.2 Eligible patients per month

| Month | 3.0 full | 3.1 full | Change |
| --- | --- | --- | --- |
| 2025-01 | 67,175,092 | 71,808,728 | +6.9% |
| 2025-06 | 68,208,241 | 73,354,730 | +7.5% |
| 2026-01 | 68,982,963 | 75,541,583 | +9.5% |
| 2026-06 | 68,691,552 | 76,587,258 | +11.5% |
| 2026-09 | 68,346,880 | 77,527,752 | +13.4% |

Eligible months by stage label in 3.1: `STAGE_UNKNOWN` 2,093.4M (66%), `STAGE_2` 687.8M, `STAGE_3` 347.1M, `STAGE_4` 37.9M.

### 3.3 Patient-months in both versions (Jan 2023 - Sep 2026)

| | Patient-months | Patients |
| --- | --- | --- |
| 3.0 full | 3,084.9M | 142.2M |
| 3.1 full | 4,069.0M | 147.9M |
| In both | 2,840.9M | – |
| Only in 3.0 | 244.0M (231.4M eligible, 218.4M with no known stage) | – |
| Only in 3.1 | 1,228.0M (609.7M eligible) | – |

The months in only one version are not yet broken down by cause, because the HCP universe changed as well as the logic. On the 10 HCPs, where the universe is the same, almost all months only in 3.0 were Dx months **before the first CKD diagnosis** (3.0 filled every month for every patient). The months only in 3.1 were mostly new Dx patients (codes 3.0 did not read) and Rx look-back months.

## 4. Eligibility differences explained

Of the 2,840.9M patient-months in both versions, **91.5% keep the same eligibility** (10 HCPs: 98.5%).

### 4.1 Eligible in 3.0, not eligible in 3.1: 232.1M months

| Reason in 3.1 | Full: months / patients | 10 HCPs: months / patients | Explanation |
| --- | --- | --- | --- |
| **Stage 1** | 217.3M / 14.6M | 51 / 5 | Mostly a 3.0 baseline effect at full scale (4.2). 202.1M of these months had no stage at all in the 3.0 table; 12.4M had Dx stage 0, which hid the lab stage (3.1 leaves the Dx stage empty, so the lab stage is used) |
| **Stage 5** (end-stage kidney disease) | 14.3M / 0.99M | 1,022 / 127 | ESRD / stage 5 codes now read. In 3.0 these months were stage 0 (7.8M), stage 4 (5.2M), no stage (0.8M) or stage 2-3 (0.5M). Stage 5 is not eligible, so these are corrections |
| **On dialysis** | 0.45M / 14,561 | 791 / 68 | Dialysis found by the 3.1 Px list that 3.0 missed or dated later. On the 10 HCPs, all 68 patients had a **monthly ESRD service** code as first event (CPT 90960 / 90961 / 90962), a code group added in the 3.1 basket (P2) |

### 4.2 Why "stage 1" dominates at full scale (open point B1)

In a fixed 1% sample of patients:

* about 96% of the months that move from eligible (3.0) to stage 1 (3.1) **already have eGFR stage 1 in the 3.0 lab journey output** (`kerendia_nba_3_0_lab_journey_output`);
* but the **3.0 full combine table** shows a stage in only 3.9M of the 22.1M 3.0 lab-journey months (18%).

So the 3.0 production combine did not use most of the 3.0 lab stages; 3.1 does, as the 3.0 code intends. This does not appear on the 10 HCPs, where the 3.0 side was rebuilt from the 3.0 journeys of the same patients (only 51 stage 1 months). **Until we know which lab input the 3.0 Ops combine read, the stage 1 numbers, and most of the stage label changes in section 5, should not be read as 3.1 changes.**

### 4.3 Not eligible in 3.0, eligible in 3.1: 10.0M months

| Reason | Full: months / patients | 10 HCPs: months / patients | Explanation |
| --- | --- | --- | --- |
| Stage 1 in 3.0, stage 2-4 or no stage in 3.1 | 9.25M / – | 17 / 1 | Stage 1 → 2 (5.7M), → 3 (2.0M), → no stage (1.5M), → 4 (0.02M) |
| **No longer counted as on dialysis** | 0.71M / 44,854 | 66 / 7 | The 3.0 dialysis date came from codes that are not in the 3.1 list, such as access procedures (P1) |
| Stage 5 in 3.0, stage 2-4 or no stage in 3.1 | 0.08M / – | 1 / 1 | Small |

## 5. Stage differences explained

The eligibility table shows the stage as `STAGE_2`, `STAGE_3`, `STAGE_4` or `STAGE_UNKNOWN` (stage 1, 5 and no stage are all "unknown"). 521.9M shared months change label:

| Change | Full: months | 10 HCPs: months | Explanation |
| --- | --- | --- | --- |
| Unknown → stage 2 | 229.3M | under 208 (in "other small moves") | Mostly the lab-stage effect of B1 (4.2) |
| Unknown → stage 3 | 222.3M | 13,155 | Stage 3a / 3b codes (N18.30-N18.32) now read (3.0 gave them stage 0), plus the B1 lab effect at full scale |
| Stage 2 → stage 3 | 22.3M | 424 | A later stage 3 diagnosis now read |
| Stage 4 → unknown | 17.8M | 1,717 | Mostly now stage 5 (ESRD code read): shown as "unknown" in the label but not eligible (4.1) |
| Stage 4 → stage 3 | 14.0M | 906 | A stage 3a / 3b diagnosis after the stage 4 one. 3.0 could not read it and carried stage 4 forward; 3.1 uses the **latest** staged diagnosis (X2, to confirm in the Dx review) |
| Stage 2 → unknown | 11.5M | – | Mostly stage 1 or 5 in 3.1 |

Besides these label changes, 156.5M shared months go from Dx "stage 0" to "no Dx stage". By itself this changes nothing, since both mean no known Dx stage. It matters only where the patient has a lab stage, which is now used.

## 6. Issue found (already in 3.0): the SGLT2 rule for unknown stage never applies

The combine step is meant to say: *a patient with no known stage is eligible only if they have ever had an SGLT2*. In the code, that check compares the stage itself with the value "-1" instead of the "stage unknown" marker, so it is never true. Result: **every patient-month with no known stage is eligible**, with or without an SGLT2.

| Jan 2023 - Sep 2026 | 3.0 full | 3.1 full |
| --- | --- | --- |
| Eligible patient-months | 2,956.8M | 3,113.0M |
| of them with no known stage | 2,717.2M (91.9%) | 2,040.7M (65.6%) |
| of them also never on an SGLT2 (would not be eligible if the rule worked) | 2,297.5M (77.7%) | 1,745.6M (56.1%) |

This is not caused by 3.1: it is copied from 3.0 so that the two versions can be compared. 3.1 already reduces the problem, because more patients now have a known stage. The share is the same on the 10 HCPs (56%). **Decision needed (C1):** fix the rule in 3.1 (eligible patient-months would drop by about 56%), or keep the 3.0 behaviour on purpose.

## 7. New diabetes and heart-failure flags

| Flag | Patients |
| --- | --- |
| Patients in the flags table | 88,986,826 |
| Diabetic, 3.0 rule (computed as in 3.0; **not used in eligibility** and not written to the eligibility table, see C2 and C9) | 77,277,926 |
| `DM_TYPE = T2D` (3.1 rule) | 73,589,616 |
| `DM_TYPE = T1D` | 1,949,941 (1,166,304 of them were "diabetic" in 3.0) |
| Both T1D and T2D codes (type set by the most frequent) | 3,626,815 |
| `DM_TYPE = OTHER` (meaning to confirm, C10) | 342,541 |
| `DM_TYPE` empty | 13,104,728 |
| Heart failure | 23,784,227: unknown type 7,840,591, HFpEF proxy 6,176,810, mixed 5,363,067, HFrEF proxy 4,403,759 |
| Monthly HF flag in the eligibility table | 14,726,077 patients, 398.6M months |
| First dialysis date (Px), by first event | 1,537,460: dialysis session 945,304, monthly ESRD service 525,674, dialysis drug 40,339, home training 26,143 |

The 3.1 T2D count is lower than the 3.0 diabetic flag mainly because patients whose only diabetes evidence is an SGLT2 are no longer T2D (SGLT2s are also given for HF and CKD; decision F1). On the 10 HCPs the flags were checked against an independent recount from the raw claims: 0 differences. Fewer patients have monthly HF months than have HF, because the first HF date can be after their last journey month.

## 8. Decisions and open points for the team

Each decision has a status:

* **Open:** not decided yet; the run uses the 3.0 behaviour or a provisional choice.
* **Our choice, please confirm:** we chose an option so the work could continue. Not reviewed by the team yet.
* **Decided:** agreed during the notebook reviews; listed so the team sees its effect here.

Effects are for the full universe unless marked "10 HCPs".

**The five most important, in order:**

1. The SGLT2 rule that never applies (C1): it decides the eligibility of 56% of the eligible months.
2. The Dx end-to-end review with Saurabh (X1): the Dx changes cause most of the real 3.1 differences.
3. The drugs missing from the Rx list, mainly generic dapagliflozin and Kerendia (R1). They matter much more once C1 is fixed, because the SGLT2 flag would then decide eligibility.
4. The dialysis code list, to confirm with Raman (P1-P3).
5. Eligibility rules per indication (C3), and whether eligibility should require diabetes at all (C9).

### 8.1 Decisions from the journey notebooks (PJ01-PJ05)

| # | Notebook | Decision | What this run uses | Status | Effect on the combined journey |
| --- | --- | --- | --- | --- | --- |
| L1 | 01 Lab | **Specialty filter**: lab results count only if ordered by one of the 10 primary-care specialties | Filter kept, as in 3.0 | Open | Biggest single exclusion in the lab data. Removing it adds about 16% more eGFR and 13% more UACR patients (all US), so more patients would get a known lab stage |
| L2 | 01 Lab | **`>60` eGFR results** (827K rows, all US) | Excluded, as in 3.0 | Open | Counting them as "not stage 3+" gives more patients a lab stage |
| L3 | 01 Lab | Where the lab settings live (lab notebook or a shared config) | Lab notebook | Open | None on the results |
| X1 | 02 Dx | **Dx end-to-end review with Saurabh** (the whole new Dx logic) | 3.1 Dx logic | Open | Stage 3 and stage 5 now read; 16.7M Dx patients (3.0: 16.0M); months before the first diagnosis removed |
| X2 | 02 Dx | **Latest staged diagnosis wins** | Latest staged diagnosis | Our choice, please confirm | 14.0M months move from stage 4 to stage 3 and 22.3M from stage 2 to 3 (section 5). Eligibility does not change, because stages 2-4 are all eligible |
| X3 | 02 Dx | ESRD codes (N18.6, I12.0, I13.11, I13.2) count as **stage 5**; Z99.2 (dialysis dependence) counts as stage 0 | As decided | Decided (Dx plan D3, D4), to confirm in X1 | 14.3M months / 0.99M patients no longer eligible (4.1) |
| X4 | 02 Dx | T1D kidney codes (E10.21 / E10.22 / E10.29) count as **CKD with unknown stage** | As decided | Decided (Dx plan D2) | T1D patients with CKD enter the journey. The combine does not check the diabetes type, so T1D patients at stage 2-4 are already eligible (C3) |
| X5 | 02 Dx | Add E09.21 / E09.29 (other diabetes with kidney disease) as unknown stage | Not added | Open | Small: these codes were in 3.0 and are not in the 3.1 basket. With header and ICD-9 codes, they make up 2,612 patient-days lost (all US) |
| X6 | 02 Dx | Dialysis diagnoses (Z99.2, Z49.x) feed the dialysis flag? | No: the dialysis flag comes from procedures only, as in 3.0 | Open (question for Raman) | Patients with a dialysis diagnosis but no dialysis procedure are not flagged as on dialysis |
| R1 | 03 Rx | **Drugs missing from the 3.0 list**: Kerendia, generic dapagliflozin, GLP-1s (Ozempic, Mounjaro, Wegovy, ...), generic Entresto, nebivolol, generic insulin glargine, DPP-IVs | Kept as 3.0 (left out) | Open (Rx Phase B) | **Generic dapagliflozin patients (4.3M, all US) do not get the SGLT2 flag.** No effect on eligibility today because of C1, but there would be one as soon as C1 is fixed. Kerendia use is not visible in the journey |
| R2 | 03 Rx | Fills started up to 97 days before the start date count (look-back); end date = end of the run window | As decided | Decided (Rx plan D4) | Adds the Dec 2022 - Mar 2023 months covered by earlier fills (10 HCPs: +2,273 patient-months) |
| R3 | 03 Rx | Cap on very long days supply (up to 999 days) | No cap, as in 3.0 | Open | Minor (10 HCPs: 4 fills) |
| P1 | 05 Px | **Access procedures** (catheters, fistulas) no longer count as dialysis | Not counted | Decided (Px D1, after a check in the diagnosis claims); confirm with Raman | 44,854 patients eligible again (0.71M months, 4.3) |
| P2 | 05 Px | **Monthly ESRD service codes** count as dialysis (3.0 missed them) | Counted | Decided (Px D1 / D2); confirm the code list with Raman | 525,674 patients have one as their first dialysis event; 14,561 patients no longer eligible, or not eligible earlier (0.45M months, 4.1) |
| P3 | 05 Px | How procedure codes are used in the patient potential | – | Open (question for Raman) | To be confirmed |
| F1 | 04 Flags | An SGLT2 on its own does not make a patient T2D (D1) | As chosen | Our choice, please confirm | **None today.** The combine still uses the 3.0 diabetic flag (C2). 77.3M diabetic patients (3.0 rule) vs 73.6M T2D (3.1 rule) |
| F2 | 04 Flags | Patients coded both T1D and T2D: the type with more claim days wins (D2); insulins as in 3.0 (D3); no ICD-9 codes (D5); additions file kept separate from the Dx basket (D6) | As chosen | Our choice, please confirm | None on eligibility today. Decides `DM_TYPE` for 3.6M mixed patients, which the T1D eligibility rule will use (C3) |
| G1 | All | **Go-live together:** the 3.1 Rx, Px and flags tables go live only with the 3.1 Dx table | Not live yet | Decided (Px D6, Rx D8) | Required: without the 3.1 Dx stage 5, patients whose only "dialysis" was an access procedure would become eligible |

### 8.2 Decisions in the combine notebook (06)

| # | Decision | What this run uses | Status | Effect |
| --- | --- | --- | --- | --- |
| C1 | **SGLT2 rule for unknown stage** (section 6) | Copied from 3.0 as it is (so it never applies), so that the two versions can be compared | **Open, most important** | Fixing it makes 1,745.6M of the 3,113.0M eligible months (56%) not eligible. It also makes R1 (generic dapagliflozin) matter |
| C2 | **Which diabetic flag** goes into the table: the 3.0 rule or the new 3.1 T2D flag | 3.0 rule (`T2D_FLAG_30`) | Our choice, please confirm | None on eligibility (the rule does not use the diabetic flag). 77.3M vs 73.6M diabetic patients |
| C3 | **Eligibility per indication** (T2D + CKD, T1D + CKD, HF) | One CKD-stage rule for everyone, as in 3.0 | Open (needs Medical for T1D) | **32.3M eligible months** have `DM_TYPE = T1D`. 339.1M of the 394.0M HF months (86%) are eligible through the CKD rule alone; HF patients without CKD are eligible today only through C1. Proposal from the Dx plan: separate flags per indication, with T1D switched on only after Medical confirms |
| C4 | **Monthly HF flag**: from the month of the first HF code on, and it never ends | As described | Our choice, please confirm | 14.7M patients, 398.6M months. Output only; it does not change eligibility |
| C5 | Dialysis: only the first dialysis date is carried into the combine (not the new code and group columns); the 3.0 rule "first dialysis before 2017 = on dialysis" is kept | As described | Our choice, please confirm | None: the procedure data starts in 2021, so the 2017 rule never applies |
| C6 | **Output table shape**: `pat_sglt2_filter_m` gets two new columns (`HF_FLAG`, `DM_TYPE`), and the three `cohort_label` copies of 3.0 become one column | As described | Our choice, please confirm | All 3.0 columns are unchanged. The HCP-level notebooks that read these tables still need to be checked for the new columns |
| C7 | Months with only a lab result stay in the journey, now that the Dx journey starts at the first diagnosis | Kept | Our choice, please confirm (Dx plan review point) | Lab-only months keep their lab stage and eligibility |
| C8 | Go-live of the 3.1 combine | Written to `full_2026_11_02/` only; the 3.0 tables are unchanged | Open (after the decisions above and G1) | – |
| C9 | **Should eligibility require diabetes?** | Not required, as in 3.0: the diabetic flag is joined but never used (checked in the 3.0 and 3.1 combine code) | Open | **1,795.9M eligible months (58%), 76.5M patients** have no T1D or T2D diagnosis (`DM_TYPE` empty). If the CKD indication means CKD with T2D, they should not be eligible |
| C10 | Meaning of `DM_TYPE = OTHER` | 342,541 patients; not described in the flags summary | Open | Confirm before `DM_TYPE` is used in an eligibility rule (C3) |

### 8.3 Open points from the full run

| # | Point | Status |
| --- | --- | --- |
| B1 | **Which lab input the 3.0 Ops combine read** in production: it uses about 18% of the 3.0 lab-journey stages (4.2). Needed before the full-scale 3.0 vs 3.1 differences can be fully explained; to check in the 3.0 Ops combine notebook (owner: Wenjie) | Open |
| B2 | The full-run table names still end in `_validation`; rename before go-live (with G1 / C8) | Open |
| B3 | Clean-up: `full_2026_11_02/_stage/` (Snowflake pulls, and the 4.3B-row comparison table `_compare_30_vs_31` used for sections 3-6), and the old test copies of 26 Oct in the `query_output/` root | Open |
| B4 | Volume: 77.5M eligible patients per month, 66% of them with unknown stage. Check that the HCP-level notebooks handle this; fixing C1 roughly halves it | Open |

## 9. How the run was made

* **One job, six tasks:** lab, Dx and Rx in parallel, then Px and the flags (they use the patients of the first three), then combine (`Combine Files/06_patient_journey_combine_3_1`; the 3.0 combine notebook is unchanged). All six succeeded in about 35 minutes: lab 11, Dx 19.5, Rx 18, flags 5.6, Px 1.3, combine 15.
* **Job parameters**, read once in `00_cohort_config`: `VALIDATION_MODE` (`true` = 10 test HCPs, `false` = full HCP universe), `RUN_OUTPUT_DIR` (required for a full run, so a full run can never overwrite the validation tables), `HCP_UNIVERSE_PATH` (Delta or Parquet), `NPI_BHID_MAPPING_PATH` and `RUN_CHECKS` (`false` skips the slow all-US checks). The job defaults are now the full run; the notebooks without parameters reproduce the validation run.
* **HCP universe:** the reader checks whether the folder is Delta or Parquet before reading, and drops `PROVIDER_ID = 0` (a placeholder for "no provider"). The `C1_FLAG`-`C5_FLAG` columns of the 3.1 universe are not used as filters.
* **Staging:** in a full run, the large Snowflake pulls are written once to `RUN_OUTPUT_DIR/_stage/`, so later steps do not pull them again.
* **Two fixes were needed for the full run** (neither shows up in validation mode): the universe reader (it used to try Delta first, which fails on the Parquet universe) and the Rx example query (it needed the test HCPs).
* **Validation run:** the same job with `VALIDATION_MODE = true` on the 10 test HCPs reproduces the 2026-11-02 validation tables exactly.
* **How the comparison numbers were made:** the eligibility of both versions was rebuilt from the patient-month stage tables and the Px tables, with the same rule as the combine (section 6). The 3.1 rebuild matches the written 3.1 eligibility table exactly (3,112,994,738 eligible months in both). On the 10 HCPs the rebuild matches both written eligibility tables (0 differences). The B1 check uses a fixed 1% sample of patients.
