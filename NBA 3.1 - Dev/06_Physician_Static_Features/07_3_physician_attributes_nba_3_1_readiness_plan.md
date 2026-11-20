# Physician Attributes Features: NBA 3.1 Readiness Plan

**Group:** HCP profile and affiliations for the NBA 3.1 HCP-level model  
**Notebook:** `NBA 3.1 Static Feature Notebooks/07_physician_attributes_features` (run 2026-11-19, 12 of 13 checks passed)  
**Output:** `kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/hcp_features/physician_attributes_features`  
**Builds on:** `07_1_physician_attributes_nba_3_0_profile.md` (what 3.0 had) and `07_2_physician_attributes_data_assessment.md` (what we checked for 3.1)  
**Same keys and cohorts as:** `33_colocation_idn_features` (one row per HCP x cohort, 28 claims cohorts)  
**Status:** draft for discussion  
**Date:** November 19, 2026

---

## The story in one paragraph

In NBA 3.0, this block had one strong feature (the affiliation count, SHAP rank 4) and many weak or broken ones: an age column that was 85% empty, experience values below zero, placeholder dates and constant flags. For 3.1 we kept what worked, dropped what did not, and added what the assessment showed was missing: **who the HCP is affiliated with** (nephrology, cardiology, endocrinology accounts, dialysis centers) and a cleaner profile (degree, gender, cardiorenal secondary specialty). The new nephrology and dialysis features are by far the strongest signals in the block: HCPs with them are four to five times more likely to write. The output is saved and ready for model testing; one open decision remains about small source-data drift in Snowflake.

---

## 1. Where we started: physician attributes in NBA 3.0

* **What it was.** Profile fields from MDM (`MDM_STG_HCP_PRFL`), affiliation flags from `MDM_STG_HCP_ACCT_AFFL` (both Snowflake) and two LAAD provider columns. 25 output columns for 234,405 HCPs.
* **How much it mattered.** 6 of the 10 "HCP Demo" features in the final 752 came from here:

| Feature | SHAP rank (of 752) |
| --- | --- |
| `AFFL_COUNT` | **4** (1.70% of total SHAP) |
| `HCP_EXPERIENCE` | 55 |
| `HCP_AGE` | 263 |
| `DIALYSIS_CENTER_FLAG` | 478 |
| `TEACHING_HOSP_FLAG` | 684 |
| `LONG_TERM_CARE_FACIL_FLAG` | 726 |

* **What was wrong.**
  * **Age was 85% empty** (only 35,211 HCPs had a birth year).
  * **Experience went negative** (min -7): it used the run year minus grad year, and some grad years are in the future.
  * **Placeholder and constant columns:** `GRAD_TRG_START_YEARS` was almost always 56 (a 1970 default date), two flags were constant, `ORG_NM` was filled for 19 HCPs.
  * **Useful fields never reached the model:** gender and education stayed raw text; degree and specialty were pulled but not saved.
  * The affiliation count said *how many* affiliations, not *what kind*.

## 2. What we learned in the 3.1 assessment (07_2)

* **The type of affiliation matters more than the count.** HCPs affiliated with a nephrology account or a dialysis center write far more often than others.
* **Profile fields carry signal once encoded.** NP/PA and female HCPs write less often; a cardiorenal secondary specialty and longer experience go with more writing.
* **Some MDM codes and the BEST_AFFL account add small signals** (self-employed solo practice, inactive status, employment flag, account size) worth testing.
* **Experience must be anchored to the cohort,** not to the run date, to avoid negative values and future information.
* **IDN features belong with colocation,** so they are built in `33_colocation_idn_features`, not here.

The assessment ended with a Build / Test / Skip list (07_2 section 4), which the 3.1 notebook follows exactly.

## 3. What we changed in 3.1

| Topic | NBA 3.0 | NBA 3.1 | Why |
| --- | --- | --- | --- |
| Features | 25 columns, many raw or weak | **22 features: 8 Build + 14 Test** | Only what 07_2 supports |
| Affiliations | `AFFL_COUNT` + 3 flags | Distinct account count, nephrology / cardiology / endocrinology account counts, dialysis, teaching, long-term care, 3 account-type flags | What kind of affiliation, not only how many |
| Profile | Raw degree / gender text, age | `HCP_DEGREE_NP_PA`, `HCP_GENDER_F`, `HCP_SECONDARY_SPEC_CARDIORENAL`; age dropped | Encoded and usable; age too empty |
| Experience | Run year - grad year (negatives possible) | Cohort prediction year - grad year; future grad years set to null | No negatives, no future information |
| MDM codes | Pulled, then dropped | 4 fixed code flags, checked against the MDM reference table | Stable schema |
| Account profile | Not used | BEST_AFFL employment flag (Y / N / NA) and account MD/DO count | New Test features |
| Missing values | Null for no affiliation | Same, kept on purpose; type flags 0 when affiliated but not that type | No-affiliation HCPs behave differently |
| Grain | One row per HCP | One row per HCP x cohort (28 cohorts), same keys as colocation | Plugs straight into the 3.1 model table |
| Writer definition (for checks) | LRx V7 | KER-10 `active_nbrx_writers` (Kerendia metric view) | Shared definition across 3.1 notebooks |

Sources stay the same: PRFL and ACCT_AFFL from Snowflake (ACCT_AFFL has no UC copy; the UC copy of PRFL is a different snapshot), BEST_AFFL and the account profile from UC.

## 4. What the 3.1 run showed

**Coverage.** 283,013 of 294,727 HCPs (96.0%) have at least one affiliation; 294,493 have a profile row. Counts are within 0.41% of 07_2 (the Snowflake tables refresh).

**Signal on KER-10 writers** (cohort c17, baseline 10.56% writers). All 15 features with a clear direction in 07_2 keep it:

| Feature | Status | Writer rate: with vs without | rho |
| --- | --- | --- | --- |
| Nephrology account affiliation (`AFFL_NEPH_ACCT_COUNT` > 0) | Build | **41.1% vs 8.9%** | 0.24 |
| Dialysis center (`DIALYSIS_CENTER_FLAG`) | Build | **45.3% vs 9.8%** | 0.18 |
| Endocrinology account affiliation | Test | 18.9% vs 10.4% | 0.05 |
| Health system / admin-only account | Test | 13.9% / 14.1% vs 10.4% | 0.03 |
| NP / PA (`HCP_DEGREE_NP_PA`) | Build | 8.3% vs 11.9% | -0.06 |
| Female (`HCP_GENDER_F`) | Build | 8.5% vs 13.2% | -0.08 |
| Cardiorenal secondary specialty | Build | 12.6% vs 10.5% | 0.01 |
| Experience, most vs least experienced fifth | Build | 13.1% vs 7.8% | 0.06 |
| Distinct accounts, most vs fewest fifth | Build | 14.4% vs 8.7% | 0.06 |
| Account MD/DO count, largest vs smallest fifth | Test | 9.0% vs 14.0% | -0.06 |

New on the full universe: self-employed solo practice writes at 15.9% vs 10.2% (07_2 compared it among MDs only). Weak: cardiology account affiliation (11.0% vs 10.7%), teaching hospital (11.0% vs 10.5%), resident (11.7% vs 10.5%).

**In plain words:** knowing that an HCP works with nephrology or dialysis accounts is the single most useful thing this block adds. Profile fields help a little; most Test features are weak and need the model to decide.

## 5. Where we are now

The notebook runs 13 automatic checks. They answer six questions. All but one pass.

| # | Question | How we checked | What we found | Result |
| --- | --- | --- | --- | --- |
| 1 | **Are the sources read correctly?** | Decoded the 4 MDM codes behind the code flags with the MDM reference table; checked BEST_AFFL has one main account per HCP | All 4 codes match their flag names; 0 HCPs with more than one main (rank-1) account | Passed |
| 2 | **Does every HCP get the right data, as in 07_2?** | Counted HCPs with each source and 14 key feature counts, and compared with 07_2 | 283,013 HCPs with an affiliation (07_2: 283,022, 9 fewer); BEST_AFFL 282,881 (exact). Of 14 counts, 4 match exactly (the 3 employment flags and account size, all from UC); the largest gap is 0.41% (female HCPs 153,983 vs 154,244). Differences are in Snowflake fields only | Passed (limit 0.5%) |
| 3 | **Does the new code give the same values as the 3.1 draft?** | Compared 18 shared columns for the 294,689 HCPs in both, HCP by HCP | Profile code flags differ for 2 HCPs and experience for 4, so the logic matches. Affiliation columns differ for 265-430 HCPs each, and the distinct account count for **1,509 (0.51%)**, just above the 0.5% limit. Gender differs for 797 | **Failed narrowly** |
| 4 | **Are missing values handled as agreed?** | Checked the 11,714 HCPs with no affiliation and the type flags of affiliated HCPs | No-affiliation HCPs have every affiliation feature empty; affiliated HCPs always have 0 or 1 in the type flags; specialty counts never exceed the distinct account count | Passed |
| 5 | **Does the signal still hold with the new writer definition?** | Recomputed each feature's link to writing on KER-10 writers (c17) and compared the direction with 07_2 | All 15 features with a clear direction in 07_2 kept it. The other 7 (cardiology accounts, 3 code flags, 3 employment flags) had no clear full-universe direction in 07_2, so they were not tested | Passed |
| 6 | **Is the output table correct and stable?** | Counted rows and keys, rebuilt the last two cohorts and compared, checked values across cohorts | 8,252,356 rows = 294,727 HCPs x 28 cohorts, one row per HCP x cohort; the rebuild gives identical rows; only `HCP_EXPERIENCE` changes between cohorts, and it is never negative | Passed |

**Why check 3 failed, and why it is most likely not a bug.** The draft read Snowflake on 2026-11-13; this notebook read it on 2026-11-19. The code flags and experience, which use the same rules, match almost perfectly (2 and 4 HCPs). The differences sit in fields that come from live Snowflake tables (affiliations, and gender from the profile table), and affiliation coverage itself changed by 9 HCPs. That pattern fits a source refresh, not a logic error. It has not been proven, because the raw 11-13 Snowflake read was not kept.

**Verdict: ready for model testing once the team accepts the drift in check 3.** The table is correct, complete as far as the data allows, and shows the expected signal one feature at a time. It does **not** yet show that the features improve the model; that is open point 2 below.

## 6. What is still open

The open points are of three kinds: **work we can do now**, **a team decision**, or **a known limitation** we accept for now and note.

| # | Open point | Kind | Why it is open | What is needed | Suggested default |
| --- | --- | --- | --- | --- | --- |
| 1 | Drift in check 3 | Team decision | The 0.5% limit was set by us, not by the team. The failure is most likely a Snowflake refresh (section 5), but only the team can agree that this level of drift is acceptable | Accept the drift, or raise the limit (for example to 1%) and record why | Accept it, and compare against this run (not the draft) from now on |
| 2 | **Do the features improve the model? (Build and Test)** | Work we can do now | Section 4 checks each feature on its own. Several features overlap (for example the nephrology account count and the dialysis flag, or account counts and colocation practice size), so a feature can look good alone and add nothing in the model. Only a model comparison shows this. It was left out because the agreed scope was "build and check", without model experiments | A proxy-model test, as in the colocation notebook: base model vs base + Build vs base + Build + Test, AUC on the same cohort, also in the new-writer view. Final confirmation in the full 3.1 model | Run the proxy test now; keep a Test feature only if it adds AUC |
| 3 | Affiliations are a current snapshot | Known limitation | Past cohorts use today's affiliations. An HCP who joined a nephrology group last year looks affiliated in 2024 cohorts too, which can make these features look slightly better in training than they will be in scoring | An affiliation history (dated snapshots or start / end dates) | Accept for now and note it; check the start / end date fields when a UC copy exists |
| 4 | Snowflake dependency | Known limitation (data request) | ACCT_AFFL has no UC copy and the UC copy of PRFL is a different snapshot, so the notebook needs the Snowflake connection and its values move between runs (as check 3 shows) | A governed UC copy of both tables, refreshed on a schedule | Request it in `01_data_improvement_requests.md` if it is not already there |
