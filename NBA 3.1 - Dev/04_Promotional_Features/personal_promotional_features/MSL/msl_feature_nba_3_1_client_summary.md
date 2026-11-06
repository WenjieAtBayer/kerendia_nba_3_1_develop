# Field Activity Phase 3, MD-1: MSL Flag Output Analysis (NBA 3.1)

**Notebook:** `45_field_actovity_phase_3_MSL_features`  
**Plan:** `40_field_activity_nba_3_1_readiness_plan.md` (Phase 3: MD-1; condition V10; gate G2)  
**Phase 0 reference:** `40_field_activity_phase0_output_analysis.md` (V10, C11; scope decision 5 Nov 2026)  
**Phase 3 reference:** `43_field_activity_phase3_events_irep_msl` (step 3, same medical rule), `43_field_activity_phase3_output_analysis.md` (MD-1)  
**Run analysed:** 5 Nov 2026, serverless  
**Date:** 5 Nov 2026

**How to read this file.** Section 1 is the summary. Section 2 gives the background for a first-time reader. Section 3 explains what the notebook does. Section 4 goes through every expectation: why we expected it, whether it is new, what we got, and what to raise with the client. Sections 5 – 8 list the gate, issues, client questions and next actions. Section 9 relates the results to V10 / C11 in the Phase 0 output analysis.

**Years.** Year 1 = Nov 2024 – Oct 2025, Year 2 = Nov 2025 – Oct 2026 (as in Phase 0). **Cohorts.** The 28 promotional cohorts (`cohorts/promotional/cohorts.parquet`, offset 17): c1 – c24 Training (lookback end 2024-06-17 to 2026-05-17), c25 – c26 Testing (2026-06-17, 2026-07-17), c27 – c28 Holdout / Backtesting (2026-08-17, 2026-09-17). Each flag uses the 6 or 12 months up to `LOOKBACK_END_DATE`. **Grain.** One row per `PROVIDER_ID` x `COHORT_ID` on the HCP universe `HCP_Universe_without_call_hcps/` (not BHID as in notebook 43).

---

## 1. Summary

| ID | Expectation | NBA 3.0 or new | Status | One-line result |
| --- | --- | --- | --- | --- |
| M-0 | Inputs, universe and mapping | New (3.1 universe) | **Met, with a coverage note** | 294,726 universe HCPs (placeholder `PROVIDER_ID` '0' removed), 99.95% with a BHID; only 62.9% of Finerenone MSL doctors (BHIDs) fall in the universe |
| M-1 | Medical records reconcile with notebook 43 | New | **Met** | Finerenone Y1 10,462 / 6,409 doctors (+0.0%), Y2 11,187 / 6,971 (+0.1%) |
| M-2 | Product mix and record types as in V10 | New | **Met** | Y2 product mix identical to the 5 Nov check; all Y2 Finerenone records have a medical type; 25 `Event_vod` records from 2023 and 2025 do not |
| M-3 | MD-1 flag profile by cohort | New | **Built** | 12M flag on 2,662 – 4,334 HCPs in training, 4,230 / 4,258 in testing, 4,342 / 4,356 in holdout; 98.5 – 99.1% zero |
| M-4 | Scope diagnostics for C11 | New | **Built** | `ALL_VS_FIN_RATIO` 1.07 – 1.16 (training), 1.17 (testing), 1.18 / 1.20 (holdout); extra HCPs grow from 233 to 891 |
| Checks | Keys, nulls, invariants, leakage, recompute | — | **Pass** | 8,252,328 rows = 294,726 x 28; 0 duplicates, 0 nulls, 3 / 3 invariants, 28 / 28 cohorts consistent, 12 / 12 HCPs match in Snowflake |
| G2 (MD-1 part) | "V10 done and MSL flag built" | — | **Pass (scope to confirm, C11)** | E4 not run |

**Bottom line.** The stand-alone MD-1 block is built on the NBA 3.1 universe and the 28 promotional cohorts, and every check passes. At BHID level it reproduces notebook 43 exactly in Year 1 and within 0.1% in Year 2. On the universe the flag is sparse but stable: about 4,100 – 4,360 HCPs per cohort from c14 onward, 98.5% zero, with the same level in training, testing and holdout. The universe already removes most non-Kerendia MSL doctors, so `ALL_MEDICAL` would add only 7 – 20% more HCPs here, but that extra part grows almost fourfold over the cohorts (233 to 891) while the Finerenone flag grows by a third; this supports keeping `MSL_SCOPE = "FINERENONE"`. The main point to raise is coverage: 37% of Finerenone MSL doctors are not in the universe.

---

## 2. Background for a new reader

1. **MSL interactions.** Medical science liaisons (medical staff, not sales) meet doctors. Their visits are scientific exchange, not promotion, and must never be counted as rep calls. Compliance confirmed on 30 Oct 2026 that a **flag** "had a medical interaction in the window" may be used (MD-1); nothing more detailed.
2. **What NBA 3.0 did.** Nothing explicit. MSL records were left out of call features only because their product text (`Finerenone [...]`) did not equal `KERENDIA` (V10).
3. **Scope decision.** On 5 Nov 2026 the scope was set to Finerenone only, without Asundexian or other medical products (V10 / C11 of the Phase 0 output analysis): non-Finerenone MSL doctors are almost all outside Kerendia rep coverage, grow over the cohorts, and fall outside the Kerendia-related compliance approval. C11 asks the client to confirm.
4. **Why a separate notebook.** Notebook 43 built MD-1 on BHID and the older 26 cohorts (C01 – C26). Notebook 45 builds the same flag on the NBA 3.1 universe (`PROVIDER_ID`) and the 28 promotional cohorts, the same set-up as notebook 44 (samples), so it joins to the other 3.1 field blocks on `HCP_COHORT_ID`.

---

## 3. How the notebook works

| Step | Cell | What it does |
| --- | --- | --- |
| Setup | 2 – 4 | Installs the Snowflake connector, defines `Get_Data_Snowflakes`, and holds the config: windows 6 / 12 months (182 / 365 days), medical rule, `MSL_SCOPE = "FINERENONE"`, `REQUIRE_MEDICAL_REC_TYPE = False`, reference figures from notebook 43, and `expected_feature_columns()` (2 columns) |
| Inputs | 5 | Reads the 28 promotional cohorts, the HCP universe and the BHID to `PROVIDER_ID` mapping (universe only) |
| 1a | 6 | Builds `field_msl_record` from `FACT_CALL` since 2023-06-01: submitted calls on non-BHO IDs that are medical (record type pattern or `Finerenone` text), with product group and `IN_SCOPE` |
| 1b | 7 | Reconciles with notebook 43 by year (BHID level); Year 2 product mix and Finerenone record types |
| 1c | 8 | Maps records to `PROVIDER_ID`, universe only |
| 1d | 9 | Coverage diagnostics (where BHIDs are lost) and Finerenone records without a medical record type |
| 2a | 10 | Attaches in-scope records to every cohort with `CALL_DATE` in (`LOOKBACK_END_DATE` − 365 days, `LOOKBACK_END_DATE`]; leakage and scope checks |
| 2b | 11 | Builds `FLD_MSL_INTERACTION_6M` and `FLD_MSL_INTERACTION_12M` (max of 0 / 1) |
| 2c | 12 | Universe x cohort skeleton, defaults 0, fixed schema, write; scope diagnostics table (not features) |
| Checks | 13 – 15 | Keys / nulls / invariants and consistency with the diagnostics; profile by cohort and dataset; independent Snowflake recompute for 12 HCPs in c24 |
| Results | 16 | Results summary |

**Changes during the run.**

* **No code fixes were needed.** All cells ran on the first attempt.
* **Cell added (step 1d).** Step 1a reported 25 Finerenone records without a medical record type, and step 1c showed that only 62.9% of in-scope BHIDs reach the universe. Step 1d was added to explain both (M-0 and M-2 in section 4). It does not change the features.
* **`PROVIDER_ID` '0' removed (6 Nov 2026, user request).** The universe contains a placeholder `PROVIDER_ID` '0' (1 BHID mapped to it, no MSL records, flags 0 in all 28 cohorts). Its 28 rows were removed from the feature output (8,252,356 to 8,252,328 rows). The diagnostics table is cohort-level and was not affected (the ID had no medical records). The notebook now excludes it in the inputs cell (`EXCLUDE_PROVIDER_IDS = ["0"]`) and checks that it is absent from the output, so a re-run gives the same result.

**Outputs** (`kerendia_nba_3_1_volume/notebook_output/field_activity_nba_3_1/`): `kerendia_nba_3_1_hcp_model_field_msl_features.parquet` (features), `field_msl_record.parquet` (intermediate), `field_msl_cohort_diagnostics.parquet` (scope diagnostics).

---

## 4. Expectation by expectation

### M-0 — Inputs, universe and mapping

* **Why we expect this.** The block must have one row per universe HCP and cohort, and MSL records must reach the right `PROVIDER_ID`. Notebook 44 uses the same universe, mapping and cohorts and reported 294,727 HCPs (including '0'), 99.95% mapped.
* **NBA 3.0 or new.** New (NBA 3.1 universe and promotional cohorts).
* **What we got.**

| Item | Value |
| --- | --- |
| Cohorts | 28 (Training c1 – c24, Testing c25 – c26, Holdout c27 – c28) |
| Universe `PROVIDER_ID`s | 294,726 (raw file 294,727; placeholder '0' removed) |
| With a BHID in the mapping | 294,577 (99.95%) |
| BHIDs on > 1 `PROVIDER_ID` | 38 (each gets the flag) |
| `PROVIDER_ID`s with > 1 BHID | 0 |

  Coverage of the MSL records:

| | In-scope BHIDs | In the mapping | In the universe | Mapped, outside universe | Not in the mapping |
| --- | --- | --- | --- | --- | --- |
| All periods (since Jun 2023) | 16,085 | 12,105 (75.3%) | 10,117 (62.9%) | 1,988 | 3,980 |
| Year 2 | 6,971 | 5,080 (72.9%) | 4,365 (62.6%) | 715 | 1,891 |

  In records: 21,082 of 30,948 in-scope records (68.1%) are on universe HCPs.
* **Status.** Met; the numbers match notebook 44. Coverage note: about a quarter of Finerenone MSL doctors have no `PROVIDER_ID` in the mapping, and about a tenth are mapped but not in the universe.
* **Raise with client.** Nothing for the client; raise internally with the universe and mapping owners: should the universe include doctors the MSLs see (this universe excludes call-only HCPs, criterion C5), and why are 3,980 MSL BHIDs missing from `SOURCE_PROVIDER_BHID_NPI_MAPPING`?
* **Suggestions.** Check the 3,980 unmapped BHIDs (for example non-prescribers, pharmacists or new BHIDs) before the model run. Ask the universe owner to drop `PROVIDER_ID` '0' at source; it is removed here and should also be removed from notebook 44's output.

### M-1 — Reconciliation with notebook 43

* **Why we expect this.** Notebook 45 uses the same medical rule as notebook 43 step 3 and the same Snowflake source, so the BHID-level counts must match (V10, plan).
* **NBA 3.0 or new.** New.
* **What we got.**

| Period | All medical records | Doctors | Finerenone records | Doctors | Notebook 43 (Finerenone) | Difference |
| --- | --- | --- | --- | --- | --- | --- |
| Jun – Dec 2023 | 11,145 | 6,579 | 4,081 | 2,868 | — | — |
| Jan – Oct 2024 | 11,807 | 7,475 | 5,218 | 3,918 | 5,218 / 3,918 | 0 |
| Y1 | 22,715 | 12,883 | 10,462 | 6,409 | 10,462 / 6,409 | +0.0% / +0.0% |
| Y2 | 30,165 | 18,118 | 11,187 | 6,971 | 11,180 / 6,964 | +0.1% / +0.1% |

  The 2023 row starts at `DATA_START` (2023-06-01), which is all the c1 lookback needs. The Year 2 difference (7 records, 7 doctors) is late MSL entries since the notebook 43 run on 4 Nov.
* **Status.** Met.
* **Raise with client.** Nothing.
* **Suggestions.** Keep the reconciliation in every run with the 3% tolerance.

### M-2 — Product mix and record types

* **Why we expect this.** The scope decision (V10, 5 Nov) rests on the product mix of medical records; the medical rule must cover the record types in the data (C3).
* **NBA 3.0 or new.** New.
* **What we got.** Year 2 medical records by product group:

| Product group | Records | Doctors |
| --- | --- | --- |
| Finerenone | 11,187 | 6,971 |
| Other (oncology, haematology, PAH, women's health, radiology) | 7,542 | 4,741 |
| Asundexian | 6,452 | 4,137 |
| Elinzanetant | 4,918 | 2,961 |
| Empty | 66 | 55 |

  Identical to the 5 Nov Snowflake check. Year 2 Finerenone records by record type: `Face2Face Interaction Med` 6,586, `Non Face2Face Interaction Med` 1,737, `Group Interaction Med` 1,444, `Remote Interaction Med` 786, `Event Call Report` 347, `Remote Group Interaction Med` 287; all have a medical type.
  Over the full period, 25 Finerenone records have the type `Event_vod`, which the medical pattern does not match (11 in 2023, 14 in 2025; one doctor each). They enter MD-1 through the product text while `REQUIRE_MEDICAL_REC_TYPE = False`.
* **Status.** Met.
* **Raise with client.** C3: confirm the full list of medical record types, including whether `Event_vod` records with Finerenone product text are MSL events.
* **Suggestions.** Keep `REQUIRE_MEDICAL_REC_TYPE = False` until C3 is answered; switching it on would remove these 25 records.

### M-3 — MD-1 flag profile by cohort

* **Why we expect this.** The plan expects a sparse but usable flag: notebook 43 had 3,838 – 5,636 doctors per cohort with the 12-month flag (87 – 93% zero, on its BHID x cohort rows). On the universe grain, zero rates are higher because every universe HCP has a row.
* **NBA 3.0 or new.** New.
* **What we got.**

| Set | HCPs with 12M flag | Zero rate 12M | HCPs with 6M flag | Zero rate 6M |
| --- | --- | --- | --- | --- |
| Training c1 – c24 | 2,662 – 4,334 | 98.53 – 99.10% | 1,262 – 2,634 | 99.11 – 99.57% |
| Testing c25 / c26 | 4,230 / 4,258 | 98.56 / 98.56% | 2,291 / 2,507 | 99.22 / 99.15% |
| Holdout c27 / c28 | 4,342 / 4,356 | 98.53 / 98.52% | 2,546 / 2,702 | 99.14 / 99.08% |

  The 12-month flag rises from about 2,700 HCPs (c1 – c4) to about 4,100 (c14) and then stays at 4,095 – 4,356 to c28. Compared with the BHID-level check of 5 Nov (6,417 Finerenone doctors in c24, 6,915 in c28), the universe keeps 63 – 67% of the flagged doctors, in line with M-0.
* **Status.** Built. The flag means the same in training, testing and holdout from c14 onward; the early training cohorts (c1 – c10) have about a third fewer flagged HCPs.
* **Raise with client.** Nothing new.
* **Suggestions.** Use the 12M flag as the main feature; the 6M flag is sparser (above 99% zero in every cohort) and should be kept only if E4 gives it weight.

### M-4 — Scope diagnostics for C11

* **Why we expect this.** The 5 Nov BHID-level check found that `ALL_MEDICAL` roughly doubles the flagged doctors (ratio 1.82 – 2.38 in training, 2.38 – 2.42 in testing, 2.45 – 2.50 in holdout) with very few Kerendia doctors. The diagnostics table repeats this on the universe, so C11 can be answered with the model's own population.
* **NBA 3.0 or new.** New (diagnostics only, not features).
* **What we got.** Universe HCPs with a medical record in the 12-month window:

| Set | Finerenone HCPs | Non-Finerenone-only HCPs | Asundexian-only HCPs | `ALL_VS_FIN_RATIO` |
| --- | --- | --- | --- | --- |
| Training c1 – c24 | 2,662 – 4,334 | 233 – 676 | 8 – 125 | 1.07 – 1.16 |
| Testing c25 / c26 | 4,230 / 4,258 | 708 / 743 | 83 / 86 | 1.17 / 1.17 |
| Holdout c27 / c28 | 4,342 / 4,356 | 798 / 891 | 110 / 124 | 1.18 / 1.20 |

  * The universe removes most non-Kerendia MSL doctors: the ratio is 1.07 – 1.20 here, against 1.82 – 2.50 at BHID level.
  * The extra part still grows: non-Finerenone-only HCPs go from 233 (c7, c8) to 891 (c28), almost four times, while Finerenone HCPs go from 3,283 to 4,356 (+33%). The ratio rises steadily from 1.07 (c6 – c10) to 1.20 (c28).
  * Asundexian-only HCPs: 125 in c1, falling to 8 – 11 in c6 – c10, then rising to 70 in c24 and 124 in c28.
* **Status.** Built. The universe-level evidence points the same way as the 5 Nov check, with a smaller effect.
* **Raise with client.** C11 (unchanged): confirm the flag counts only Finerenone visits. Add the universe figures: `ALL_MEDICAL` would add 7 – 20% more HCPs, and that addition grows over the cohorts.
* **Suggestions.** Keep `MSL_SCOPE = "FINERENONE"`, without Asundexian. Keep the diagnostics table in every run so C11 can be revisited with current data.

---

## 5. Gate G2 (MD-1 part)

The plan's gate G2 includes "V10 done and MSL flag built" and "E3 and E4 run".

| Part | Status | Evidence |
| --- | --- | --- |
| V10 done and MSL flag built | **Pass** (scope to confirm, C11) | Reconciles with notebook 43 (Y1 exact, Y2 +0.1%); flag built on the universe x 28 cohorts |
| Keys and nulls | **Pass** | 8,252,328 rows = 294,726 x 28; 0 duplicate `HCP_COHORT_ID`; 0 nulls in both features; every cohort has 294,726 rows; no `PROVIDER_ID` '0' |
| Invariants | **Pass** | 3 / 3: 6M ≤ 12M, both flags in (0, 1); 0 failing rows |
| Consistency | **Pass** | 12M flagged HCPs equal `HCPS_FINERENONE_12M` of the diagnostics in 28 / 28 cohorts |
| Leakage and scope | **Pass** | All attached records within (`LOOKBACK_END_DATE` − 365 days, `LOOKBACK_END_DATE`]; no out-of-scope or non-Finerenone record in MD-1; no BHO IDs |
| Independent Snowflake recompute | **Pass** | 12 / 12 HCPs match in c24 (end 2026-05-17): 8 flagged (6 with both flags, 2 with the 12M flag only) and 4 unflagged |
| E4 run (with and without MD-1) | **Open** | Not run |

**The MD-1 part of G2 is met.** G2 as a whole stays open for the reasons in `43_field_activity_phase3_output_analysis.md` (event states, template groups, E3 / E4).

---

## 6. Issues

| # | Issue | Impact | Proposal |
| --- | --- | --- | --- |
| P1 | 37% of Finerenone MSL doctors (BHIDs) are not in the universe: 3,980 not in the mapping, 1,988 mapped outside the universe | MSL contact on these doctors is lost; the flag covers 62.9% of MSL doctors | Check the unmapped BHIDs and whether call-only HCPs (C5) should be in the universe |
| P2 | Flag is sparse on the universe grain (98.5 – 99.1% zero for 12M, above 99% for 6M) | Weak feature; 6M adds little | Keep 12M; drop 6M unless E4 gives it weight |
| P3 | Early training cohorts (c1 – c10) have fewer flagged HCPs (2,662 – 3,568) than later ones (about 4,100 – 4,360) | The flag rate changes inside training | Watch in E4; consider the flag's effect by cohort |
| P4 | 25 Finerenone records with type `Event_vod` and no medical type | Enter MD-1 through the product text | C3; keep `REQUIRE_MEDICAL_REC_TYPE = False` until answered |
| P5 | `PROVIDER_ID` '0' in the universe | **Resolved here** (6 Nov): removed from the MD-1 output; still in the universe file and in notebook 44's output | Ask the universe owner to drop it at source; apply the same exclusion in notebook 44 |
| P6 | 38 BHIDs map to more than one `PROVIDER_ID` | The flag is copied to each | Same rule as notebook 44; confirm with the mapping owner |

---

## 7. Client questions

| # | Question | Why it matters | Owner |
| --- | --- | --- | --- |
| C11 | MSL flag scope: confirm Finerenone interactions only (recommended), not any medical interaction | MD-1 definition; on the universe `ALL_MEDICAL` adds 7 – 20% more HCPs (233 – 891 per cohort), a part that grows almost fourfold over the cohorts | Medical affairs, compliance |
| C3 | Full list of medical record types; are `Event_vod` records with Finerenone product text MSL events? | The pattern covers the types seen; 25 `Event_vod` records enter only through product text | CRM team, medical affairs |
| — | Confirm MD-1 stays out of rep-facing driver text | Compliance approved a flag for the model, not as a reason shown to reps | Compliance |

---

## 8. Next actions

| # | Action | Owner | Status |
| --- | --- | --- | --- |
| N1 | Send C11 (with the universe diagnostics) and C3 (with the `Event_vod` records) | NBA team | Open |
| N2 | Run E4 with and without MD-1 (12M flag; 6M optional) | NBA team | Open |
| N3 | Check the 3,980 unmapped MSL BHIDs and the universe definition for MSL-only doctors (P1) | NBA team, universe owner | Open |
| N4 | Keep MD-1 out of rep-facing driver text unless compliance agrees | NBA team | Open |
| N5 | Join the MD-1 output with the other 3.1 field blocks on `HCP_COHORT_ID` | NBA team | Open |
| N6 | After C3: decide on `REQUIRE_MEDICAL_REC_TYPE` and re-run | NBA team | Waiting for client |
| N7 | Update V10 / C11 in `40_field_activity_phase0_output_analysis.md` and the readiness plan Phase 3 status with these results | NBA team | Open |

---

## 9. Relation to V10 / C11 in the Phase 0 output analysis

* **V10 rules applied unchanged.** Medical records are matched by the V2 / V10 pattern (record type contains `Interaction Med` / `Interaction_Med`, starts with `BPH_MED_` or `Event Call Report`, or product text contains `Finerenone`); the flag uses Finerenone records only (`MSL_SCOPE = "FINERENONE"`), no Asundexian, flags only, no settling rule.
* **V10 figures reproduced.** The Year 2 product mix equals the 5 Nov check (Finerenone 11,187, Asundexian 6,452, Elinzanetant 4,918, other 7,542, empty 66), and Finerenone Year 1 / Year 2 match notebook 43 (M-1 in section 4).
* **C11 evidence extended to the universe.** V10 showed at BHID level that `ALL_MEDICAL` roughly doubles the flagged doctors (ratio 1.82 – 2.50) with few Kerendia doctors. On the universe the ratio is 1.07 – 1.20, because the universe already excludes most non-cardiorenal doctors; the trend is the same (rising from c6 – c10 to c28). Both levels support Finerenone only.
* **Asundexian decision unchanged.** Asundexian-only HCPs in the universe are few (8 – 125 per cohort) but rising since c10 (124 in c28); the V10 reasons for not adding Asundexian (pre-launch product, drift, compliance scope) still apply.
* **New point for V10.** Universe coverage of MSL doctors (62.9%) was not part of V10; it should be added there as a caveat for MD-1.
* **C3 detail.** The 25 `Event_vod` records with Finerenone text are the only Finerenone records outside the medical record-type pattern; V10's note that "none exist today" for non-medical Finerenone records holds for rep calls (V2), but not for these event records.