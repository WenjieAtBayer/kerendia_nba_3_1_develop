# Veeva Link Key People: Phase 3 Working Plan (business use in the NBA)

**Parent plan:** `50_veeva_link_nba_3_1_readiness_plan.md`, section 5, Phase 3 (B1 to B4), gate G3 (business lists and action hints part), decisions D2, D3, D7, questions Q1, Q2, Q9  
**Builds on:** Phase 0 (`51_`, `52_` to `57_`), Phase 1 (`70_`, `71_`, `72_`), Phase 2 (`80_`: `81_` score history, `82_veeva_link_t3_features` T3 + cross features, `82_veeva_colocation_idn_signal_test_ker_10`, `83_veeva_link_t3_tests` R4 and interim R2)  
**Goal:** four reviewed, reproducible business outputs (two HCP lists, one action-hint table, one review pack), offline and not rep-facing until licence and compliance answers (X3) are in  
**Status:** B0 to B4 built and checked (2026-11-23, `91_` run `20261123T103200`, `92_` run `20261123T103700`, `93_` run `20261123T103851`); waiting on B3 review feedback and X3 / Q9 (section 10)  
**Date:** November 23, 2026

---

## 1. Why Phase 3 can start before G2 closes

* D2 / P2-D3: T3 scores are business rules and segmentation only until E6 and R2 say otherwise. Phase 3 is exactly that use, so it does not depend on the blocked model experiments (`84_`, E5 to E7).
* Phase 2 evidence supports business-rule use (`80_` sections 10.4 to 10.6):

| Evidence | Result | Meaning for Phase 3 |
| --- | --- | --- |
| R4, Non-target segment | KER-10 writer rate 0.11% / 0.29% / 0.52% at best decile 1-3 / 4-7 / 8-10 (4.73x) | Decile orders untargeted HCPs, but absolute rates are low: B1 is a review list, not a "will write" list |
| R4, segment B | 3.29% / 3.93% / 5.67% (1.72x) | Decile adds inside B: useful priority within B in B1 / B4 |
| R4, segments A, C, D | ratios 1.10, 1.07, 0.80 | Little or reversed: do not use decile to re-rank A / C / D |
| R2 (interim), best decile | rho 0.435 with market TRx; 2.22x within market-volume deciles | Not a copy of volume; ok as a list criterion |
| R2 (interim), CL MRA / SGLT2 class | no writer signal within claims bands (1.00x, 1.03x) | Fine as a **messaging** hint (B2), not as a writer predictor |
| R5 re-run on KER-10 | 18,254 non-writing experts in 2,454 IDNs with peer writer share <= 5% (10,450 Non-target) | B4 base numbers on the KER-10 rule (replace the LRx V7 numbers in `50_` 5.2) |

## 2. New facts that shape Phase 3

| Fact | Effect |
| --- | --- |
| Veeva scores and activity end 2025-03-06; at list date (2026-11) data age is about 20 months | Every list carries `veeva_data_cutoff` and `veeva_data_age_months`; experts new since 2025-03 are missing (risk P3-R1) |
| Snapshot T3 = as-of T3 for every cohort from 2025-03 on (`82_` L2) | Lists use the snapshot version; no version choice needed |
| Stale latest rows (`81_`): snapshot keeps 2,119 FA and 1,969 DR experts whose last load is older than 2025-03-06 | Keep them (vendor never deleted them) but flag `veeva_score_from_stale_load` so reviewers can drop them |
| 50_ numbers are from assessment v2 (18,209 / 10,113) and the LRx V7 writer rule | Phase 3 recomputes them at the list date with KER-10 and documents the gap |
| Call plan = `cp_ker_hcp_2026q4` (`NOTE_2`, FF CR1 / CR2 / CR4 / CR5, Kerendia) | Same segment rule as R4 and `60_` |

## 3. Decisions for Phase 3

| # | Decision | Detail |
| --- | --- | --- |
| P3-D1 | **Offline only until X3** | All outputs are files for brand, sales operations, Field Analytics and Medical Affairs. Nothing goes to the NBA dropdown or reps until Q1 (licence) is answered; payment-based content waits for Q2 |
| P3-D2 | **List date and writer rule** | List date = latest NBA 3.1 cohort C22 (`2026-10_offset7`, cut-off 2026-11-06). Writer = KER-10 `active_nbrx_writers` > 0 in the 12 months to the last KER-10 week (2026-10-16 today); new-writer view as Q11 |
| P3-D3 | **Expert / authority** | Best in-scope decile 8 to 10 (snapshot T3), the same rule as P2-D6. Top tier = 9 to 10 |
| P3-D4 | **Indication split** | Per HCP: indications where the CL disease decile is 8 to 10 (CKD, HF, T2D, T1D, HTN), plus class authority (MRA, SGLT2). An HCP can carry more than one; lists show all, counts are not summed across indications |
| P3-D5 | **Hints are rules, not scores** | B2 hints are deterministic rules on T1 / T2 / T3 columns, one primary hint per HCP by a fixed priority, other hints as secondary. No model output |
| P3-D6 | **Payments** | No payment feature in any hint or list column shown to the field (Q2, D3). Payments may be used only for internal sizing tables |
| P3-D7 | **Language** | "Influence" / "authority", not "KOL" (principle 9); the NBA output is the "NBA dropdown list" |
| P3-D8 | **Reproducible** | Every list is a parquet table with `run_ts`, input run ids (`82_` run, `61_`/`82_` KER-10 run, segment table) and a check table; Excel / CSV exports are made from it, never edited by hand |

## 4. Output layout

`OUT = /Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/veeva_link_to_people/`

| Path | Content | Written by |
| --- | --- | --- |
| `business/b1_untargeted_authority/run=<ts>/` | One row per Non-target NPI at decile 8 to 10: keys, specialty, state, decile, tier, indications, writer status, market volume band, stale-load flag | B1 |
| `business/b1_untargeted_authority/run=<ts>/summary` | Counts by specialty x indication x tier x writer status | B1 |
| `business/b2_action_hints/run=<ts>/` | One row per NPI with any hint: primary hint, secondary hints, rule evidence columns | B2 |
| `business/b4_low_adoption_idn_experts/run=<ts>/` | One row per non-writing expert in a low-adoption IDN: IDN, specialty, segment, IDN writer share, IDN size | B4 |
| `business/b4_low_adoption_idn_experts/run=<ts>/by_idn` | One row per IDN: experts, writers, writer share, segment mix | B4 |
| `business/review_pack/run=<ts>/` | Review samples and feedback template for B3 | B3 |
| `business/checks/run=<ts>/` | Checks M1 to M8 (section 5.2) | all |

## 5. Tasks, notebooks and checks

| Order | ID | Notebook | Work | Done when (check) |
| --- | --- | --- | --- | --- |
| Day 1 | B0 | `91_veeva_link_business_lists` (section 0) | Build the list base at C22: HCP Universe NPI spine, snapshot T3 (`82_`), T1 / T2 (`71_` C22 partition), segment, specialty (HCP Universe; Veeva specialty only if missing), state, KER-10 writer status, market TRx band (R4 rule), L1 / L4 keys and IDN writer share (`82_veeva_colocation_idn_signal_test_ker_10` logic) | One row per NPI (294,542); M1, M2 pass |
| Day 1 | B1 | `91_` (section 1) | Non-target x decile 8 to 10; tier 9 to 10; indications (P3-D4); writer / non-writer; priority inside the list = tier, then non-writer, then market volume band (R2: decile adds beyond volume) | M3: counts within 1% of `80_` 1.1 (18,208 / 10,113) or gap explained; summary by specialty x indication written |
| Day 2 | B4 | `91_` (section 4) | Non-writing experts (KER-10 look-back) in IDNs with peer writer share <= 5% (self excluded), by IDN, specialty, segment; IDN table with size and writer share | M4: reproduces the KER-10 run (18,254 experts / 2,454 IDNs at the `61_` windows) before moving the window to C22 |
| Days 2 to 3 | B2 | `92_veeva_link_action_hints` | Rule table (section 6) on T1 / T2 / T3 columns; one primary hint per HCP by priority; secondary hints; coverage per hint and per segment; overlap matrix between hints | M5: every hint traces to columns in `71_` / `82_` schema locks; M6: no payment column used; coverage table written |
| Day 3 | B2.1 | `92_` | Sense check of hints vs outcome at C2 (forward 12 months, KER-10): writer and new-writer rate per primary hint, inside segment; not a selection criterion, only to catch a hint that points at the wrong HCPs | Table written; any hint with a lower rate than its segment average is flagged for review |
| Day 4 | B3 | `93_veeva_link_review_pack` | Review pack for Field Analytics and Medical Affairs: per list / hint, 10 to 20 sampled HCPs with their Veeva evidence (trials, podium events, decile themes), same template style as `72_` spot check; feedback columns (agree / disagree / reason) | Pack exported; review meeting booked; feedback re-imported and logged |
| Day 5 | G3-B | `90_` (this file) | Write the outcome: lists and hints accepted / changed / dropped; copy to `50_` Phase 3 and gate G3 | Section 9 checklist complete except external answers |

### 5.1 Inputs

| # | Input | State (2026-11-23) |
| --- | --- | --- |
| J1 | T3 snapshot and cross features (`82_`, run `20261123T093214`) | Ready |
| J2 | T1 / T2 at C22 (`71_`, run `20261123T085209`) | Ready |
| J3 | KER-10 writers (`mv_kerendia_nbrx`) | Ready (I6); last week 2026-10-16 |
| J4 | Segments `cp_ker_hcp_2026q4`, L1 / L4 keys (I7) | Ready |
| J5 | HCP Universe specialty and state | To confirm column names in the HCP Universe table |
| J6 | Licence and compliance answers (Q1, Q2 / X3) | **Open**; gates rep-facing use only |
| J7 | Reviewers named (Q9): brand, sales operations, Field Analytics, Medical Affairs | **Open** |

### 5.2 Checks

| # | Check | Pass rule |
| --- | --- | --- |
| M1 | One row per NPI in the list base | rows = distinct NPIs = 294,542 |
| M2 | Coverage reproduces Phase 0 | SCORED 147,487 / unscored / not in Veeva as `57_` |
| M3 | B1 counts | Non-target 8-10 and 9-10 within 1% of 18,208 / 10,113 (snapshot, C22 segments) |
| M4 | B4 reproduces the KER-10 run | 18,254 experts, 2,454 IDNs, 10,450 Non-target at the `61_` windows |
| M5 | Hint traceability | Every rule column exists in `schema_lock/columns.json`, `t3_columns.json` or `cross_columns.json` |
| M6 | Compliance guard | No `veeva_pay_*` column in B1 / B2 / B4 field-facing exports |
| M7 | No HCP outside the universe or outside Veeva in hint rows | All hint rows have `veeva_coverage_status` = `SCORED` or `IN_VEEVA_UNSCORED` |
| M8 | Independent recount | 100 random B1 / B4 rows recounted from raw T3 and KER-10 with a separate query; 0 mismatches |

## 6. B2 action-hint rules (first version, to review in B3)

Priority = order in the table; the first rule that fires is the primary hint.

| Priority | Hint (NBA reason / channel) | Rule (columns) | Why |
| --- | --- | --- | --- |
| 1 | Peer-to-peer / speaker programme invitation | `veeva_event_podium_flag_3y` = 1 and `veeva_event_n_inscope_3y` > 0 | `50_` B2; podium = peer influence |
| 2 | Clinical-evidence messaging (trial investigator) | `veeva_trial_n_inscope_5y` > 0 (PI if `veeva_trial_pi_flag_5y` = 1), or `veeva_trial_finerenone_flag_5y` / `veeva_trial_mra_flag_5y` = 1 | `50_` B2; trials rise with decile (assessment 8.1) |
| 3 | Cardiorenal class messaging | `veeva_cl_decile_mra_class` or `veeva_cl_decile_sglt2_class` 8 to 10 | `50_` B2; R2: class deciles track volume, not writing, so messaging only |
| 4 | Disease-specific messaging (CKD / HF / T2D) | CL disease decile 8 to 10 for that indication (P3-D4) | Indication view (D5) |
| 5 | Scientific content (digital) | `veeva_dr_any_inscope` = 1 or `veeva_pub_n_inscope_5y` > 0 | Digital reach and publishing activity |

Not used as hints: payments (P3-D6), INDEX scales and Scientific Reach (R2: no writer signal within claims bands; may be shown as context only).

## 7. Order of work

1. B0 base and M1 / M2 (day 1).
2. B1 and B4 in `91_` (days 1 to 2); M3 / M4 first, then move B4 to the C22 window.
3. B2 rules and coverage in `92_` (days 2 to 3), B2.1 sense check.
4. B3 review pack (day 4); meeting with Field Analytics and Medical Affairs.
5. Write outcomes here and in `50_` (day 5).

## 8. Risks for Phase 3

| # | Risk | Mitigation |
| --- | --- | --- |
| P3-R1 | Data age about 20 months; new experts missing, retired experts still listed | Show data cut-off and age on every list; stale-load flag; refresh (X2) before any repeat |
| P3-R2 | Lists read as "will write" lists | State the R4 rates in the cover note (Non-target 8-10: 0.52% writer rate); position as target-list review input |
| P3-R3 | Licence / compliance does not allow commercial use | P3-D1: offline only; Medical Affairs-only fallback for B1 / B4 |
| P3-R4 | Hints overlap with internal speaker / MSL data (personal block) | B3 reviewers check against Bayer speaker lists; Veeva hints describe external activity only (D3) |
| P3-R5 | Old call plan / affiliation snapshot | Same Q4-2026 snapshot as colocation; re-run with the next call plan |
| P3-R6 | Segment D reversal (R4) | Do not use decile to prioritise inside D |

## 9. Phase 3 checklist (G3, business part)

* [x] B0 list base at C22; M1, M2 pass (`91_` run `20261123T103200`)
* [x] B1 untargeted-authority list and summary; M3, M8 pass (`91_`)
* [x] B4 low-adoption IDN expert list; M4, M8 pass (`91_`)
* [x] B2 action hints and coverage; M5 to M7 pass; B2.1 sense check (`92_` run `20261123T103700`)
* [ ] B3 review pack built (`93_` run `20261123T103851`, 150 rows, P1 / P2 / M6 pass); **not yet sent**; feedback not logged
* [ ] Outcomes copied to `50_` Phase 3 and G3
* [ ] External: X3 (Q1, Q2) answered before any rep-facing use; Q9 reviewers named

## 10. Run log

### 10.1 B0, B1, B4: `91_veeva_link_business_lists`, run `20261123T103200` (M1 to M4, M6, M8 pass)

* B0: 294,542 NPIs at C22; coverage SCORED 147,487 / IN_VEEVA_UNSCORED 81,441 / NOT_IN_VEEVA 65,614 (= Phase 0). KER-10 last week 2026-10-16; 12-month window 2025-10-18 to 2026-10-16: 31,425 writers. Experts (decile 8-10) 37,075; 1,508 with a score from a stale load. Specialty filled 99.8% (BEST_AFFL, LRx V7 fallback). Data age 19.3 months.
* B1: 18,208 Non-target HCPs at decile 8-10 (top tier 9-10: 10,113; = `80_` 1.1). Non-writers in the last 12 months: 17,900; writers 308. Top specialties FM 6,338, IM 3,618, CD 2,311, END 1,210, GP 793, NEP 690. CL indication (HCP can carry several): HTN 3,294, MRA class 2,822, T2D 1,568, HF 1,473, SGLT2 class 915, T1D 530, CKD 348; 9,693 have no CL disease / class decile >= 8 (their best decile comes from other CL themes or FA / DR). 46 with stale-load scores.
* B4: M4 reproduces the KER-10 run exactly (18,254 experts / 2,454 IDNs / 10,450 Non-target). At the list date (13-week look-back 2026-07-18 to 2026-10-16): 13,499 experts in 2,296 IDNs; Non-target 7,986, B 2,561, D 1,148, A 756, C 624, E 424. Largest IDNs: Cleveland Clinic (393), Trinity (366), Piedmont (335), Ascension (319), Advocate (270). Top specialties FM, CD, IM, END, NEP.
* M8: 100-row recount of B1 (raw T3 + metric view) and B4 (IDN peers) with 0 mismatches. The B4 recount re-uses the same in-memory provider table, so it checks the grouping logic, not the source joins.

### 10.2 B2, B2.1: `92_veeva_link_action_hints`, run `20261123T103700` (M5, M6, M7 pass)

32,133 NPIs (10.9%) have at least one hint (32,015 scored, 118 in Veeva unscored).

| Hint | Rule fires | Primary | Writer rate at C2 (forward 12M, all segments) |
| --- | --- | --- | --- |
| P2P_SPEAKER | 4,921 | 4,921 | 18.88% |
| CLINICAL_EVIDENCE | 4,810 | 3,333 | 22.71% |
| CARDIORENAL_CLASS | 10,173 | 9,456 | 26.46% |
| DISEASE_CKD | 2,060 | 1,743 | 59.72% |
| DISEASE_HF | 3,954 | 2,835 | 8.54% |
| DISEASE_T2D | 4,881 | 2,465 | 21.18% |
| SCIENTIFIC_CONTENT | 12,784 | 7,380 | 10.03% |
| (no hint) | | 262,409 | 7.55% |

* Largest overlaps: P2P_SPEAKER and SCIENTIFIC_CONTENT 3,573; CLINICAL_EVIDENCE and SCIENTIFIC_CONTENT 2,434; CARDIORENAL_CLASS and DISEASE_T2D 1,580.
* Hints are identical at C2 and C22 for all NPIs (T1 and T3 do not change after the 2025-03-06 cut-off).
* B2.1 flags (segment x primary hint, >= 100 HCPs, writer rate below the segment average), 20 cells: `DISEASE_HF` in A, B, D, E and Non-target; `P2P_SPEAKER` and `SCIENTIFIC_CONTENT` in A, B, D, E and Non-target (`SCIENTIFIC_CONTENT` also in C); in segment D also `CARDIORENAL_CLASS` and `CLINICAL_EVIDENCE` (5 of 7 hints; `DISEASE_CKD` and `DISEASE_T2D` not flagged); in segment E also `CARDIORENAL_CLASS` and `CLINICAL_EVIDENCE` (segment rate 0.14%, hint cells 0%).
* Reading for B3: `DISEASE_HF` points at HCPs who write less than their segment (same as R2: no writer signal for CL HF); keep it as a messaging hint only if reviewers agree, otherwise drop. In segment D, do not use hints for prioritisation (R4 reversal, P3-R6).

### 10.3 B3: `93_veeva_link_review_pack`, run `20261123T103851` (P1, P2, M6 pass)

150 rows: 15 per group for B1 top tier, B1 tier 8, B4 and each of the 7 primary hints, with Veeva evidence and empty `REVIEW_AGREE` / `REVIEW_REASON` / `REVIEWER` columns; cover note with the data age, the R4 rate caveat and review questions. Output: `business/review_pack/run=20261123T103851/{pack, pack_csv, cover}`. Some B1 sample rows have no hint and `IDN_NAME` = 'NA' (no IDN); reviewers see Veeva decile and indication only for them.

Next: name reviewers (Q9), send the pack, log feedback, then decide which hints stay (G3). No rep-facing use until X3 (Q1, Q2).
