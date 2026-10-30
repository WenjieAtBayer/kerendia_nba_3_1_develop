Hi Team,

 

Sharing the EOD updates from the Argentina Team for October 30th, 2026.

 

1. New diabetes type and heart failure flags (PJ04)

Goal. NBA 3.1 adds T1D and HF to T2D + CKD, but the 3.0 notebook could only say "this patient is diabetic" (T2D yes/no). It could not tell T1D from T2D and had no heart failure.

What we did.

New notebook 04_patient_journey_dm_hf_flags, in the new folder Patient_Journey_Validation/T2D-T1D-HF Files/ next to the old 04_patient_journey_t2d_flag (logic unchanged, only its config path fixed after the move).
Per patient it keeps the 3.0 flag (T2D_FLAG_30, so PJ06 does not break) and adds DM_TYPE (T2D / T1D / OTHER), T2D_FLAG, T1D_FLAG, DM_MIXED (coded both ways), HF_FLAG, HF_TYPE (HFrEF / HFpEF proxy from the code, mixed or unknown) and HF_FIRST_DATE.
Codes come from the Dx basket plus a new file, Final Product Basket/Kerendia_Dx_Flag_Additions.csv (116 codes the basket is missing: 38 T2D, 68 T1D, 10 HF). The Dx basket itself is untouched.
Checks: the 3.0 rule rerun gives exactly the same 77,186,262 patients as the 3.0 table; with the additions, the T2D codes are exactly the 3.0 list; for the validation patients, an independent recount gives 0 differences.
Results (all US)

T2D: 77.2M (3.0) to 73.5M (3.1). 2.5M patients whose only sign of diabetes is an SGLT2 on its own leave (decision D1), and 1.2M patients mostly coded as T1D move to T1D.
T1D: 1.9M patients (new). 3.6M patients have both T1D and T2D codes.
HF: 23.8M patients (new), 11.7M of them without diabetes. By type: 6.2M HFpEF proxy, 4.4M HFrEF proxy, 5.4M mixed, 7.8M unspecified.
Validation HCPs (4,238 patients): T2D 2,490 to 2,339, T1D 39, HF 1,309.
Decisions taken (for team review): D1 an SGLT2 alone, with no diabetes diagnosis, no longer makes a patient T2D; D2 patients coded both ways get the type with more claim days (tie: T2D); D3 insulins count as in 3.0; D4 the CKD rule for T1D is set in PJ06 (proposal: same as T2D); D5 no ICD-9 codes, as in 3.0; D6 the additions file stays separate until the Dx journey goes live.
Docs: NBA_3_1_DM_HF_Flags_Plan.md (facts) and NBA_3_1_DM_HF_Flags_Client_Summary.md (plain-language summary) in T2D-T1D-HF Files/.

 

2. End-to-end run of the patient journeys (started)

Goal. Run all 3.1 journeys (Lab, Dx, Rx, Px, PJ04) and then PJ06 with the 10 validation HCPs, to check the whole chain works from start to end.

What we did.

New output folder query_output/validation_2026_10_30/. The write cells of Lab, Dx, Rx, Px and PJ04 now write there (switched on). The current *_validation tables that PJ06 and the HCP notebooks read are not touched.
Lab: the monthly processing now uses the 3.1 query (Step 4) instead of the 3.0 query (new cell, LAB_INPUT = "step4").
First issue found by the run: Lab and Dx read their basket files from Wenjie's old kerendia_nba_3_1_develop_sm repo, which no longer exists. Both now read them from our repo. Lab Steps 1-2 then ran fine (225 patients, 6,139 patient-months, same as before).
The run was stopped because it was too slow. Reason: these are validation notebooks. They rerun every query version (3.0, Step 2, 3, 4), compare them on all US data, pull all US rows into Spark before keeping the 10 HCPs, and the 3.0 Rx cells copy the full Rx fact table. Only the final query and the write are needed for this run.
PJ06 (old file) was moved to Patient_Journey_Validation/Combine Files/. Its config path (../00_cohort_config) still points to the old location and needs fixing before it runs.

 

3. FTP & Copay feature notebooks (NBA 3.1)

Goal. Migrate FTP and Copay notebooks to new Galaxy team data sources.

FTP — done.
New source: CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_SALES_ALIGNED (SALE_TYP = 'FTP'). Reversal handling and NPI-to-BHID mapping both eliminated — new table pre-computes FTP_TRX and carries BAYER_HCP_ID directly. Notebook validated end-to-end: 268K raw rows → 4,556 HCPs, cohort I01 (lookback 2025-10-17 to 2026-10-17), all checks passed, written to Delta.

Copay — blocked.
New source (TRMN_CSMR_PROF_MDM) is a consumer profile / MDM table with no HCP identifier and no Rx/claim columns. Also inaccessible with current role (0 rows returned). Schema mismatch sent to team; work paused pending response.

Deliverables (FTP_and_Copay/): ftp_drift_analysis_and_strategy.md, copay_drift_analysis_and_strategy.md, ftp_decisions_and_findings.md, 19_ftp_features (revamped + validated), 22_copay_features (shell with old logic as reference).


Next steps

Make the journeys fast: a RUN_CHECKS switch in each notebook (False = skip the comparison and all-US cells), the 10-HCP filter applied inside the Snowflake query, and PJ04 / Px written only for the validation patients in this run.
Run Lab, Dx, Rx, Px and PJ04 into the dated folder, then build the PJ06 3.1 copy in Combine Files/ (reads the dated folder, 3.0 diabetic flag = T2D_FLAG_30, monthly dialysis flag from FIRST_DIALYSIS_DATE) and compare its output with the current PJ06 output for the same 10 HCPs.
Write a markdown with the findings of the full run.
Commit and push everything together (PJ04 notebook, additions file, PJ04 docs, path fixes, run changes, PJ06 copy, findings). Nothing from today is committed yet.
Open for review: decisions D1-D6 (PJ04); lab specialty filter and >60 eGFR; Px questions for Raman.