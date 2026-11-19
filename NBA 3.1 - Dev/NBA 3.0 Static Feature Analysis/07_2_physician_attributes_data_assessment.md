# Data Assessment: HCP Physician Attributes (nb 07_phy_static_features), NBA 3.1

## Purpose
Decide which physician-attribute features to build for NBA 3.1, and from which sources. The 3.0 profile is in `07_1_physician_attributes_nba_3_0_profile.md`. This file checks the 3.1 draft output and three related MDM sources against the 3.1 outcome.

## Method (2026-11-18)

**In one sentence:** for each physician feature, we compare how often HCPs with and without it go on to write Kerendia.

**Step by step**

| Step | What we did | Result |
| --- | --- | --- |
| 1. Who | Took the NBA 3.1 HCP universe (`kerendia_nba_3_1_volume/HCP_Universe_without_call_hcps`) | 294,727 HCPs |
| 2. Feature values | Read the features from the output of the 3.1 draft notebook `07_phy_static_features_creation` (`/Users/sehar.aejaz.ext@bayer.com/Extra Notebooks/Feature Creation Static/`), saved at `{VOL_31}/hcp_level_model/dev_pipeline/notebook_output/static_features/07_phy_static_features` on 2026-11-13. It reads the real Snowflake affiliation table `MDM_STG_HCP_ACCT_AFFL`, so the stand-in table used in the 07 recommendations (`whc_data_zone1_prod.mdm_hcp_hco_affl`) is no longer needed | 294,689 HCPs have a row (38 missing) |
| 3. Who wrote Kerendia | Writer = at least 1 Kerendia NBRx in LRx V7 (weekly data) between 2025-10-24 and 2026-10-23 | 28,628 writers (**9.7%**) |
| 4. New writers only | Repeated the check on HCPs with no Kerendia activity in the 3 months before (2025-07-25 to 2025-10-23). This shows whether a feature predicts *new* adoption, not just continued writing | 265,563 HCPs, of whom **5.4%** become writers |
| 5. Inside each specialty | Repeated the check inside PCP, CARD, NEPH and ENDO (notebook 20 grouping: OTHERS, OBGYN and no-specialty HCPs count as PCP), so a feature is not just a stand-in for specialty | PCP 220,477 / CARD 49,398 / NEPH 14,650 / ENDO 10,202 |
| 6. New sources | Linked each HCP's main account (best-affiliation table, rank-1 row) to the MDM account hierarchy and account profile (section 3.3) | 282,881 HCPs linked |

**How to read the results**
* **Yes / no features** (for example NP/PA): writer rate of HCPs with the feature vs without. "7.6% vs 11.0%" means NP/PAs write less often than other HCPs.
* **Number features** (for example years of experience): HCPs are sorted and split into five equal groups, Q1 (lowest) to Q5 (highest), and we compare the writer rate of Q1 with Q5. **rho** is one number for the whole trend (Spearman correlation with being a writer; 0 = no trend).
* **Counts that are mostly 0** (for example number of nephrology accounts): compared as "at least one" vs "none", because five equal groups do not work when most values are 0.
* Each feature is checked on its own, not inside the model.

**Good to know**
* The draft output holds 314,920 HCPs (more than the final universe) and 53 columns: PROVIDER_ID, 51 features and PULL_DT.
* PCP is 1 HCP above notebook 20's 220,476 because I also counted the one HOS-coded HCP as PCP.

**Verdicts:** **Build** = clear signal that holds within specialty and for new writers; **Test** = some signal, offer it to feature selection; **Skip** = no signal, or duplicates another feature; **Later** = needs a source or decision outside this notebook.

## Sources

| Source | What it gives | Checked | Usable? |
| --- | --- | --- | --- |
| `MDM_STG_HCP_PRFL` (UC copy `pace_ker_in_house_schema.mdm_stg_hcp_prfl`, 83 columns) | Degree, gender, secondary specialty, grad / birth year, practice type, MPA, employment | Via the nb 07 3.1 output | Yes |
| `MDM_STG_HCP_ACCT_AFFL` (Snowflake only) | All HCP-account affiliations: specialty, class of trade, description, primary flag | Via the nb 07 3.1 output | Yes |
| `pace_ker_in_house_schema.mdm_stg_acct_hrchy_ker` | Account hierarchy L1 to L4 IDN, Q4 2026 only: 563,271 L1 accounts, one row each | Joined on the BEST_AFFL rank-1 BHO_ID | Yes, for IDN features |
| `pace_ker_in_house_schema.mdm_stg_acct_prfl_ker` | Account profile, 108 columns, 1,116,411 accounts (one row per BHO_ID) | Joined on the BEST_AFFL rank-1 BHO_ID: 279,153 HCPs (94.7%) | Partly: the size columns only |
| `pace_ker_in_house_schema.cust_mdm_best_affl_publish_pd_outp_static` | Best account per HCP (BHO_ID, EMPLOYMENT_FLAG) | 282,881 HCPs (96.0%) have a rank-1 row | Yes, as the bridge |

No UC copy of `MDM_STG_HCP_ACCT_AFFL` exists. A search of `information_schema.tables` for `acct_affl`, `hcp_affl` and `hco_affl` returns 22 tables. The four closest (`whc_data.acct_affl_master`, `whc_data.whc_hcp_affl_master`, `whc_tsd.acct_affl`, `pc_data.hcp_hco_affl`) lack IS_PRIMARY_RELATIONSHIP__V and START_DATE, so none is a copy. The pipeline must keep reading it from Snowflake.

## 1. Readiness of the Inputs

### 1.1 The 3.1 draft already fixes the 3.0 defects

| 3.0 defect (analysis file, 6.3) | 3.1 draft output |
| --- | --- |
| AGE 85% null | HCP_AGE filled for 80.9% (birth year where present, otherwise imputed from GRAD_YEAR); range 20-99 |
| HCP_EXPERIENCE negative (min -7) | Filled for 78.8%; range 0-72. Grad years after the anchor are set to NULL |
| Wall-clock year | The draft's column notes describe an anchor year (grad years after the anchor are NULL). Which date the anchor is was not checked here |
| GENDER raw string | HCP_GENDER_F; U is NULL, not male. Filled for 91.4% (25,240 NULL) |
| GRAD_TRG_START_YEARS placeholder, governance flags, ORG_NM | Not in the 3.1 output |

### 1.2 AFFL_COUNT undercounts, it does not double count
The 07 recommendations assumed AFFL_COUNT counts rows twice. On the real table it is the other way round. AFFL_DISTINCT_ACCT_COUNT (distinct BHO_ID) is never lower than AFFL_COUNT and is higher for 12,204 HCPs. AFFL_COUNT collapses separate accounts that share name, class and description. The two are almost the same ranking (Spearman 0.994).

### 1.3 Coverage gaps
* **11,705 HCPs (4.0%) have NULL affiliation features** (this includes the 38 universe HCPs with no output row). Their writer rate is 5.9%. NULL is informative, so keep it as NULL, not 0.
* **PRIMARY_* features are filled for only 57.0%** (126,586 NULL). The cause was not checked.
* **Peer IDN features** need a BEST_AFFL account that is in the hierarchy: 282,881 HCPs (96.0%). 210,425 (71.4%) sit in a real IDN, after treating "NA" and "Multiple Doctors" as no IDN, across 33,062 IDNs.

## 2. Grouping Levels (affiliation and IDN)

Affiliation information can be summarised at three levels:

| Level | Example feature | Link |
| --- | --- | --- |
| All HCP affiliations | AFFL_NEPH_ACCT_COUNT | ACCT_AFFL on BH_ID |
| Best account | ACCT_MD_DO_COUNT (account size) | BEST_AFFL rank-1 BHO_ID to `mdm_stg_acct_prfl_ker` |
| IDN of the best account | IDN_PEER_KERENDIA_SHARE | BEST_AFFL BHO_ID = `L1_CHILD_BHO_ID`, then L4_IDN_BHO_ID |

The all-affiliations level carries the strongest signal (Section 3.2). The IDN level adds peer adoption, which the HCP's own affiliations cannot show.

## 3. Signal Check

### 3.1 Profile features (PRFL)

| Feature | HCPs flagged / filled | Writer rate | New writers | Within specialty (PCP / CARD / NEPH / ENDO) | Verdict |
| --- | --- | --- | --- | --- | --- |
| HCP_DEGREE_NP_PA | 109,809 | 7.6% vs 11.0% | 4.8% vs 5.8% | 6.5 vs 7.8 / 7.9 vs 9.7 / 25.9 vs 46.8 / 18.0 vs 19.1 | **Build** |
| HCP_GENDER_F (F vs M) | 154,244 F | 7.8% vs 12.3% | 4.7% vs 6.5% | 6.0 vs 9.5 / 8.0 vs 10.1 / 34.8 vs 47.9 / 16.7 vs 25.4 | **Build** |
| HCP_SECONDARY_SPEC_CARDIORENAL | 12,697 | 11.9% vs 9.6% | 8.2% vs 5.3% | 14.0 vs 7.2 (n = 2,555) / 10.9 vs 8.6 (9,759) / NEPH n = 36 / ENDO n = 347 | **Build** |
| HCP_EXPERIENCE (fixed) | 78.8% | Q1 7.2% vs Q5 12.0%, rho 0.058 | Q1 4.6% vs Q5 5.3% | - | **Build** |
| HCP_AGE (imputed) | 80.9% | Q1 7.3% vs Q5 11.7%, rho 0.052 | Q1 4.7% vs Q5 5.1% | Spearman 0.97 with HCP_EXPERIENCE | **Skip** (duplicates EXPERIENCE) |

**PRACTICE_TYPE / MPA / EMPLOYMENT one-hots.** The three "missing" flags are nearly the same column: they agree for 294,345 and 294,015 of 294,455 HCPs. They mostly restate NP/PA: 109,581 of the 123,199 missing HCPs are NP/PA, and 99.8% of NP/PA HCPs are missing. PRACTICE_TYPE_DIRECT_PATIENT_CARE and MPA_OFFICE_BASED_PRACTICE correlate at 0.92. So the codes are compared among MDs only (NP/PA = 0):

| Code (MDs only) | MDs flagged | Writer rate | New writers | Verdict |
| --- | --- | --- | --- | --- |
| PRACTICE_TYPE_MISSING | 13,618 | 9.0% vs 11.1% | 6.3% vs 5.7% | **Skip** (direction flips for new writers) |
| MPA_OFFICE_BASED_PRACTICE | 140,390 | 11.5% vs 9.4% | 5.6% vs 6.2% | **Skip** (flips) |
| PRACTICE_TYPE_DIRECT_PATIENT_CARE | 152,774 | 11.3% vs 9.6% | 5.6% vs 6.6% | **Skip** (flips; 0.92 with OFFICE) |
| EMPLOYMENT_GROUP_PRACTICE | 80,153 | 11.1% vs 10.9% | 5.1% vs 6.2% | **Skip** |
| EMPLOYMENT_SELF_EMPLOYED_SOLO_PRACTICE | 19,874 | 14.7% vs 10.5% | 5.8% vs 5.7% | **Test** (existing writers only) |
| MPA_INACTIVE | 2,579 | 5.5% vs 11.0% | 2.4% vs 5.8% | **Test** (small, consistent) |
| PRACTICE_TYPE_RESIDENT | 4,148 | 9.8% vs 11.0% | 9.1% vs 5.7% | **Test** (small; new-writer lift) |

The other one-hots on the full universe (yes vs no; new writers yes vs no): PRACTICE_TYPE_NOT_CLASSIFIED and MPA_NOT_CLASSIFIED 11.3% vs 9.7% (7.4% vs 5.3%; 8,261 and 8,037 HCPs; their overlap was not computed); EMPLOYMENT_NOT_CLASSIFIED 10.2% vs 9.6% (6.4% vs 5.2%); EMPLOYMENT_OTHER_PATIENT_CARE 13.1% vs 9.7% (5.5% vs 5.4%, 4,318 HCPs); MPA_FULL_TIME_HOSPITAL_STAFF 9.1% vs 9.7%; the non-government and city / county / state hospital codes 9.7% and 9.0% vs 9.7%. None was checked among MDs only. **Skip**, except the NOT_CLASSIFIED codes, which are a weak **Test** (new-writer lift; meaning of the code unknown).

### 3.2 Affiliation features (ACCT_AFFL, via the 3.1 output)

Rates are among the 283,022 HCPs with at least one affiliation.

| Feature | HCPs | Writer rate | New writers | Within specialty (PCP / CARD / NEPH / ENDO) | Verdict |
| --- | --- | --- | --- | --- | --- |
| AFFL_NEPH_ACCT_COUNT > 0 | 15,619 | 39.2% vs 8.2% | 17.0% vs 5.0% | 15.2 vs 7.2 / 11.3 vs 9.0 / 46.9 vs 22.3 / 17.9 vs 18.7 | **Build** (strongest) |
| AFFL_CARD_ACCT_COUNT > 0 | 47,406 | 10.3% vs 9.8% | 7.5% vs 5.0% | 7.4 vs 7.3 / **10.1 vs 5.5** / 42.7 vs 42.3 / 15.6 vs 18.9 | **Build** (signal inside cardiology and for new writers) |
| AFFL_ENDO_ACCT_COUNT > 0 | 10,279 | 17.8% vs 9.6% | 6.9% vs 5.4% | 8.1 vs 7.3 / 10.5 vs 9.1 / 49.6 vs 42.2 / 20.7 vs 14.2 | **Test** |
| DIALYSIS_CENTER_FLAG | 6,919 | 43.3% vs 9.0% | 17.4% vs 5.2% | 16.6 vs 7.2 / 11.0 vs 9.1 / 47.7 vs 38.6 / 20.0 vs 18.7 | **Build** (keep) |
| AFFL_DISTINCT_ACCT_COUNT | 96.0% | Q1 7.9% vs Q5 13.5%, rho 0.064 | Q1 5.4% vs Q5 6.5% | - | **Build**, replaces AFFL_COUNT |
| AFFL_COUNT (3.0 definition) | 96.0% | Q1 8.0% vs Q5 13.3%, rho 0.060 | Q1 5.5% vs Q5 6.4% | Spearman 0.994 with DISTINCT | **Skip** (keep only for a 3.0 comparison run) |
| TEACHING_HOSP_FLAG | 116,568 | 10.3% vs 9.6% | 5.6% vs 5.3% | - | **Test** (weak) |
| LONG_TERM_CARE_FACIL_FLAG | 9,686 | 11.9% vs 9.8% | 6.0% vs 5.4% | - | **Test** (weak) |
| AFFL_HOSPITAL_COUNT > 0 | 166,613 | 10.1% vs 9.5% | 5.4% vs 5.4% | - | **Skip** |
| AFFL_IDN_ACO_FLAG | 65,306 | 10.3% vs 9.7% | 5.2% vs 5.5% | - | **Skip** |
| AFFL_POST_ACUTE_FLAG | 27,585 | 10.0% vs 9.9% | 4.7% vs 5.5% | - | **Skip** |
| PRIMARY_ACCT_HCP_COUNT | 57.0% filled | Q1 10.9% vs Q5 8.8%, rho -0.031 | Q1 5.6% vs Q5 6.0% | - | **Skip** (low fill; ACCT_MD_DO_COUNT is better, 3.3) |
| PRIMARY_AFFL_CLASS_HOSPITALS / MEDICAL_GROUP_OUTPATIENT / OTHER | 22,747 / 136,878 / 8,516 | 8.4 vs 10.0 / 9.8 vs 9.7 / 13.3 vs 9.6 | 5.6 vs 5.5 / 5.4 vs 5.7 / 6.2 vs 5.5 | - | **Skip** |

**HCP_AFFL_DESCRIPTION_* (13 type flags).** Three duplicate existing flags: CMS_TEACHING_HOSPITAL has the same 116,568 HCPs as TEACHING_HOSP_FLAG; NURSING_HOME_OR_LONG_TERM_CARE the same 9,686 as LONG_TERM_CARE_FACIL_FLAG; DIALYSIS_INFUSION_CENTERS (6,771) is near DIALYSIS_CENTER_FLAG (6,919). Drop them.

| Type | HCPs | Writer rate | New writers | Within specialty (PCP / CARD / NEPH / ENDO) | Verdict |
| --- | --- | --- | --- | --- | --- |
| ORGANIZATION_HEALTH_SYSTEM | 27,100 | 12.9% vs 9.5% | 5.9% vs 5.4% | 8.1 vs 7.2 / 10.7 vs 8.9 / 49.9 vs 40.8 / 21.6 vs 18.4 | **Test** |
| ORGANIZATION_ADMIN_ONLY | 20,400 | 13.0% vs 9.6% | 5.7% vs 5.4% | 9.1 vs 7.1 / 9.4 vs 9.0 / 49.4 vs 41.3 / 20.6 vs 18.6 | **Test** |
| ORGANIZATION_ACOS | 43,027 | 8.7% vs 10.1% | 4.8% vs 5.5% | - | **Test** (only negative type with some size) |
| ORGANIZATION_GROUP_PRACTICE | 258,777 | 10.1% vs 7.2% | 5.4% vs 5.4% | - | **Skip** (near-constant, no new-writer signal) |
| ORGANIZATION_HOSPITAL | 82,617 | 10.4% vs 9.6% | 5.5% vs 5.4% | - | **Skip** |
| DEPT_AT_HOSPITAL, GROUP_AT_HOSPITAL, HOSPICE, HOME_HEALTH_CARE_AGENCY, PHS_OUTPATIENT, WALK_IN_CLINIC | 4,360-17,426 each | Within 2.4 points of the baseline | Within 1.1 points of 5.4% | - | **Skip** |

### 3.3 IDN and account features (new sources)

Peer writing = HCPs active on Kerendia in the look-back window (29,164 HCPs), excluding the HCP itself.

| Feature | HCPs | Writer rate | New writers | Check | Verdict |
| --- | --- | --- | --- | --- | --- |
| IDN_PEER_KERENDIA_SHARE | 186,909 (IDN with at least 2 universe HCPs) | Quintiles 5.9 / 6.2 / 7.5 / 9.6 / 16.3%, rho 0.125 | Q1 4.0% vs Q5 7.6% | Share > 10% vs 0-10%: PCP 12.1 vs 4.6, CARD 12.2 vs 7.7, NEPH 53.2 vs 34.1, ENDO 30.6 vs 11.3 | **Build**, in the colocation notebook (see below) |
| IDN_HCP_COUNT | 210,425 | Quintiles 11.9 / 10.0 / 8.0 / 8.0 / 8.8%, rho -0.039 | 6.1% vs 4.9% | - | **Skip** |
| HCP_IN_IDN | 210,425 | 9.3% vs 10.6% | 5.3% vs 5.7% | - | **Test** (weak negative) |
| BEST_AFFL EMPLOYMENT_FLAG | Y 230,078 / N 37,220 / NA 15,583 / missing 11,846 | 10.2 / 7.8 / 10.9 / 4.8% | - | - | **Test** |
| ACCT_MD_DO_COUNT (best account, `COUNT_MD_DO` > 0) | 196,044 | Q1 12.9% vs Q5 8.2%, rho -0.062 | Q1 6.0% vs Q5 5.4% | Smaller accounts write more in every specialty: PCP 11.3 to 5.4, CARD 11.1 to 6.6, NEPH 46.1 to 31.3, ENDO 28.1 to 9.0. Spearman 0.32 with PRIMARY_ACCT_HCP_COUNT, 0.22 with AFFL_DISTINCT_ACCT_COUNT | **Test** |
| ACCT_BED_COUNT (`COUNT_BEDS` > 0) | 83,208 | Q1 6.3% vs Q5 9.1%, rho 0.031 | - | - | **Skip** |
| COUNT_MEDSTAFF, COUNT_ALL_LOCN_MD_DO | 201,087 / 196,117 | rho -0.059 / -0.062 | - | Similar rho and quintiles to COUNT_MD_DO (their correlation with it was not computed) | **Skip** |
| PERCENT_MEDICAID, PERCENT_MEDICARE | 0 HCPs > 0 | - | - | Empty | **Skip** |
| ACCEPT_MEDICAID / ACCEPT_MEDICARE, LAB_SERVICES | 'U' (unknown) is the largest or second-largest value | 8.5-11.0% across Y / N / U (NULL 6.0-7.3%) | - | - | **Skip** |
| TRAINING_FACILITY = Y | 13 | - | - | - | **Skip** |
| VA_DOD_AFFILIATED = Y | 1,138 | 4.1% | - | - | **Skip** (too small) |
| EMR_VENDOR_NAME_1, TRAUMA_CENTER_LEVEL | 77,816 / 46,404 filled | Epic 7.2%, any trauma level 4.0-8.5% vs NULL 10.4% / 10.1% | - | Both mark hospital-based accounts | **Skip** (restate the hospital setting) |

**Zero peer share is its own group.** Bands of IDN_PEER_KERENDIA_SHARE: 0 (21,263 HCPs) 7.6%; 0-5% (40,850) 4.8%; 5-10% (78,811) 8.1%; 10-20% (37,546) 12.4%; > 20% (8,439) 28.4%. HCPs whose peers have share 0 write more than the 0-5% band. This is the likely reason quintile 1 sat above quintile 2 in the 07 recommendations (in this run quintile 1 is 5.9% and quintile 2 6.2%). Add an IDN_PEER_SHARE_ZERO flag, or leave share = 0 as a separate value for the tree model. A further 23,516 HCPs are the only universe HCP in their IDN, so their share is NULL.

**Ownership.** IDN_PEER_KERENDIA_SHARE is also in `33_2_colocation_idn_data_assessment.md`. As agreed, it is built in the colocation notebook, not here. Here peer writing is any Kerendia activity in the look-back window. The 07 recommendations reported rho 0.088, also with a look-back peer definition. I did not trace the difference from the 0.125 here, so the colocation notebook should fix one definition and recompute.

## 4. Candidate Features for NBA 3.1

| Feature | Source | Verdict | Note |
| --- | --- | --- | --- |
| HCP_DEGREE_NP_PA | PRFL | Build | Already in the 3.1 draft |
| HCP_GENDER_F | PRFL | Build | Already in the draft |
| HCP_SECONDARY_SPEC_CARDIORENAL | PRFL | Build | Already in the draft |
| HCP_EXPERIENCE (anchored) | PRFL | Build | Already in the draft |
| AFFL_NEPH_ACCT_COUNT | ACCT_AFFL | Build | Already in the draft |
| AFFL_CARD_ACCT_COUNT | ACCT_AFFL | Build | Already in the draft |
| AFFL_DISTINCT_ACCT_COUNT | ACCT_AFFL | Build | Replaces AFFL_COUNT |
| DIALYSIS_CENTER_FLAG | ACCT_AFFL | Build | Keep |
| AFFL_ENDO_ACCT_COUNT | ACCT_AFFL | Test | |
| TEACHING_HOSP_FLAG, LONG_TERM_CARE_FACIL_FLAG | ACCT_AFFL | Test | Weak |
| HCP_AFFL_DESCRIPTION_HEALTH_SYSTEM / ADMIN_ONLY / ACOS | ACCT_AFFL | Test | Drop the other 10 type flags |
| HCP_EMPLOYMENT_SELF_EMPLOYED_SOLO_PRACTICE, HCP_MPA_INACTIVE, HCP_PRACTICE_TYPE_RESIDENT, PRACTICE_TYPE_NOT_CLASSIFIED | PRFL | Test | Drop the other practice / MPA / employment one-hots |
| HCP_IN_IDN | Hierarchy | Test | |
| BEST_AFFL EMPLOYMENT_FLAG | BEST_AFFL | Test | One-hot Y / N / NA |
| ACCT_MD_DO_COUNT | Account profile | Test | New; needs adding to nb 07 |
| IDN_PEER_KERENDIA_SHARE (+ zero flag) | Hierarchy + LRx | Build (colocation nb) | Defer to the colocation notebook |
| HCP_AGE, AFFL_COUNT, AFFL_HOSPITAL_COUNT, AFFL_IDN_ACO_FLAG, AFFL_POST_ACUTE_FLAG, PRIMARY_ACCT_HCP_COUNT, PRIMARY_AFFL_CLASS_*, IDN_HCP_COUNT, other account-profile columns | - | Skip | See Section 3 |
| External: CMS Doctors and Clinicians (grad year, group size), NPPES taxonomy, Open Payments | External | Later | Listed in the 07 recommendations (7.4); not checked here |

## 5. Data Issues
1. **ACCT_AFFL is Snowflake-only.** It has no UC copy, so the 3.1 pipeline keeps the Snowflake read. It is a current snapshot (START_DATE = load date, END_DATE empty, per the 07 recommendations), so training cohorts get today's affiliations. That is a leakage risk for a back-dated training window.
2. **The hierarchy is also a snapshot** (Q4 2026 only), and the account profile has one row per account (no history checked). Same caveat for the IDN and account features.
3. **Gender U is NULL** (25,240 HCPs). Fine for LightGBM, but document it.
4. **The 3.1 draft output covers 314,920 HCPs**, more than the final universe (294,727). 38 universe HCPs are missing from it, so rerun nb 07 on the final universe.
5. **Too many sparse one-hots.** 30 of the 51 draft features are practice-type (4), MPA (6), employment (7) or description (13) one-hots. Sections 3.1 and 3.2 keep 6 as Test, plus the two NOT_CLASSIFIED codes as weak Test.

## 6. Recommended Order
1. Rerun nb 07 on the final 3.1 universe. Replace AFFL_COUNT with AFFL_DISTINCT_ACCT_COUNT, drop HCP_AGE and the Skip one-hots.
2. Keep the Build features already in the draft (NP_PA, GENDER_F, SECONDARY_SPEC, EXPERIENCE, AFFL_NEPH, AFFL_CARD, DIALYSIS).
3. Add ACCT_MD_DO_COUNT and BEST_AFFL EMPLOYMENT_FLAG (two joins on the BEST_AFFL BHO_ID).
4. Hand IDN_PEER_KERENDIA_SHARE plus the zero flag to the colocation notebook, with the peer definition from 3.3.
5. Offer the Test features to feature selection.
6. External sources (Later).

## Summary
The 3.1 nb 07 draft already fixes the 3.0 defects (null AGE, negative EXPERIENCE, wall-clock year, raw gender) and is built from the real ACCT_AFFL, so no proxy is needed. The strongest new signals are affiliation with a nephrology account (39.2% vs 8.2%; new writers 17.0% vs 5.0%), dialysis affiliation, cardiology accounts inside cardiology, and HCP traits (NP/PA and gender, both lower in every specialty; cardiorenal secondary specialty). AFFL_COUNT undercounts accounts rather than double counting them, and the distinct count replaces it. Most practice-type and affiliation-type one-hots add nothing once NP/PA and specialty are known. Of the new sources, IDN peer adoption is the strongest (rho 0.125; HCPs whose IDN peer share is above 10% write most in every specialty) and goes to the colocation notebook. Account size is a modest Test candidate, and the rest of the account profile is empty or restates the hospital setting.
