# Census (SDoH) Features: NBA 3.1 Readiness Plan

**Group:** area context (census / SDoH) for the NBA 3.1 HCP-level model  
**Notebook:** `NBA 3.1 Static Feature Notebooks/08_census_features` (run 2026-11-19, 15 of 15 checks passed)  
**Output:** `kerendia_nba_3_1_volume/hcp_level_model/dev_pipeline/notebook_output/hcp_features/census_features`  
**Builds on:** `08_1_census_nba_3_0_profile.md` (what 3.0 had) and `08_2_census_data_assessment.md` (what we checked for 3.1)  
**Same keys and cohorts as:** `33_colocation_idn_features` (one row per HCP x cohort, 28 claims cohorts)  
**Status:** draft for discussion  
**Date:** November 19, 2026

---

## The story in one paragraph

In NBA 3.0, census features were 22 ZIP-level percentages from a CSV, and almost 1 in 10 HCPs got no values, partly because of a join bug. For 3.1 we checked the data, found what was weak, and rebuilt the block: the same census data now read from Unity Catalog, joined correctly, with a cleaner column set and new **area** features (territory and county averages) that are among the strongest signals in the block. Coverage rose from 91% to 96% of HCPs, every feature keeps the direction we saw in the assessment when we switch to the new KER-10 writer definition, and the output is saved and ready for model testing.

---

## 1. Where we started: census in NBA 3.0

* **What it was.** 22 ZIP-level ACS columns (race, education, poverty, transport, income, insurance) from `SDoH Walgreens v2.csv`, one row per ZIP. The table had no HCP key; HCPs got values through the geo notebook's ZIP in the combine step.
* **How much it mattered.** All 22 columns made the final 752 features. The best was `ACS_PCT_HISPANIC_ZC` (SHAP rank 26); most ranked between 66 and 410. Useful context, not a top driver.
* **What was wrong.**
  * Only **91.2%** of the 234,405 HCPs got values. 12,705 HCPs (5.4%) were lost because the geo notebook stripped leading zeros from ZIPs (New England, NJ, Puerto Rico), and 7,977 had no ZIP at all.
  * Those missing HCPs are not random: they cluster in specific regions.
  * `ACS_PCT_POSTHS_ED_ZC` is just the sum of three other columns.
  * No area-level view: every feature describes one ZIP only.

## 2. What we learned in the 3.1 assessment (08_2)

* **The data is fine.** The CSV is an exact copy of the UC table `dem_zip_sdoh_acs20` (ACS 2016-2020), so we can read UC directly.
* **The 3.1 draft had a new join bug.** It joined on ZCTA instead of ZIPCODE, losing 4,443 HCPs.
* **Area averages add a stronger view.** Territory and county averages (rho about 0.08) were stronger than the same measure at ZIP level (for example, % without high school: 0.084 for the territory vs 0.062 for the ZIP). Only `ACS_PCT_WHITE_NONHISP_ZC` (-0.085) matched them at ZIP level.
* **A better race column exists.** `ACS_PCT_WHITE_NONHISP_ZC` is a stronger signal than `ACS_PCT_WHITE_ZC`.
* **Missing data is informative.** HCPs without census values write less often, so "missing" should be kept as a signal, not filled.

The assessment ended with a Build / Test / Skip list (08_2 section 4), which the 3.1 notebook follows exactly.

## 3. What we changed in 3.1

| Topic | NBA 3.0 | NBA 3.1 | Why |
| --- | --- | --- | --- |
| Source | `SDoH Walgreens v2.csv` | UC table `dem_zip_sdoh_acs20` | Same values (0 differing cells across 41,011 ZIPs); governed source |
| HCP ZIP | Geo notebook ZIP (leading zeros stripped) | BEST_AFFL rank-1 `HCP_ZIP`, zero-padded | Removes the leading-zero loss |
| Join | ZIP (broken by the zeros); ZCTA in the 3.1 draft | **ZIPCODE** | Recovers 4,443 HCPs vs the draft |
| ZIP columns | 22 | 21: POSTHS_ED dropped, WHITE replaced by WHITE_NONHISP | Redundant / weaker columns out |
| Area features | None | Territory (`TERR_SDOH_LT_HS`, `TERR_SDOH_WHITE`) and county (`COUNTY_DEP_POPW`) averages | Stronger than the same measures at ZIP level in 08_2 |
| Missing values | Silent nulls | `SDOH_MISSING_FLAG` and `NO_CBSA_FLAG` (not in a metro area) | Missing is informative |
| Grain | One row per ZIP | One row per HCP x cohort (28 cohorts), same keys as colocation | Plugs straight into the 3.1 model table |
| Writer definition (for checks) | LRx V7 | KER-10 `active_nbrx_writers` (Kerendia metric view) | Shared definition across 3.1 notebooks |

The final block has **36 features: 26 Build and 10 Test.** Test features (deprivation index, Medicaid, marital status, crowding, Medicare, extra territory / county measures, log population) are built and saved but still need to prove their value in the model.

## 4. What the 3.1 run showed

**Coverage.** 281,978 of 294,727 HCPs (95.7%) have census values, up from 91.2% in 3.0. Every coverage number matches 08_2 exactly.

**Signal on KER-10 writers** (cohort c17, baseline 10.56% writers). All 36 features keep the direction seen in 08_2, slightly stronger:

| Feature | Writer rate: lowest vs highest fifth | rho (3.1, KER-10) | rho (08_2, LRx V7) |
| --- | --- | --- | --- |
| `TERR_SDOH_LT_HS` (territory, % without high school) | 7.6% vs 15.2% | 0.087 | 0.084 |
| `COUNTY_SDOH_LT_HS` (Test) | 7.3% vs 15.4% | 0.086 | 0.083 |
| `TERR_SDOH_WHITE` | 15.4% vs 7.4% | -0.082 | -0.079 |
| `COUNTY_DEP_POPW` (county deprivation) | 7.8% vs 15.1% | 0.078 | 0.076 |
| `ACS_PCT_WHITE_NONHISP_ZC` | 15.7% vs 7.7% | -0.089 | -0.085 |
| `ACS_PCT_LT_HS_ZC` | 8.7% vs 14.5% | 0.065 | 0.062 |

Missing flags: HCPs with missing census data write at 5.8% vs 10.8%; HCPs outside a metro area at 7.8% vs 10.9%.

**In plain words:** HCPs in less-educated, more diverse, more deprived areas are about twice as likely to write. The signal is modest per feature, but consistent and stable across writer definitions.

## 5. Where we are now

The notebook runs 15 automatic checks. They answer five questions. Each one must pass before the output can be used.

| # | Question | How we checked | What we found | Result |
| --- | --- | --- | --- | --- |
| 1 | **Is the new source the same data as 3.0?** | Compared the UC table with the 3.0 CSV, value by value, for 21 columns and 41,011 ZIPs | 0 differing values | Passed |
| 2 | **Does every HCP get the right ZIP and census row?** | Rebuilt the HCP to ZIP to census chain and compared each count with 08_2 | HCPs with a ZIP 282,881; matched to census 282,857; with census values 281,978; with a territory 282,872; outside a metro area 13,149. **All equal to 08_2.** The old ZCTA join would have matched only 278,414, so the fix recovers 4,443 HCPs | Passed |
| 3 | **Are missing and odd values handled as agreed?** | Checked the 11,846 HCPs with no ZIP, the two flags and all percent columns | No-ZIP HCPs have every census feature empty and `SDOH_MISSING_FLAG = 1`; flags are only 0 or 1; all 29 percent columns are between 0 and 100 | Passed |
| 4 | **Does the signal still hold with the new writer definition?** | Recomputed each feature's link to writing on KER-10 writers (c17) and compared the direction with 08_2 | All 26 features with a clear direction in 08_2 kept it. The other 10 are very weak in 08_2 (\|rho\| below 0.03), so they were not tested, but they also kept their sign | Passed |
| 5 | **Is the output table correct and stable?** | Counted rows and keys, rebuilt the last two cohorts and compared, checked values across cohorts | 8,252,356 rows = 294,727 HCPs x 28 cohorts, one row per HCP x cohort; the rebuild gives identical rows; each HCP has the same values in every cohort (census is static) | Passed |

Note on check 5: the first run showed differences on the rebuild. They were only in the last decimal places of recomputed averages (floating-point noise). The check now compares values rounded to 9 decimals, and the rebuild is identical.

**Verdict: ready for model testing.** This means the table is correct, complete as far as the data allows, and shows the expected signal one feature at a time. It does **not** yet show that the features improve the model; that is open point 1 below.

## 6. What is still open

The open points are of three kinds: **work we can do now**, **a team decision**, or **a known limitation** we accept for now and note.

| # | Open point | Kind | Why it is open | What is needed | Suggested default |
| --- | --- | --- | --- | --- | --- |
| 1 | **Do the features improve the model? (Build and Test)** | Work we can do now | Section 4 checks each feature on its own. Census features overlap with each other and with geography features from other notebooks, so a feature can look good alone and add nothing in the model. Only a model comparison shows this. It was left out of this notebook because the agreed scope was "build and check", without model experiments | A proxy-model test, as in the colocation notebook: base model vs base + Build vs base + Build + Test, AUC on the same cohort, also in the new-writer view. Final confirmation in the full 3.1 model | Run the proxy test now; keep a Test feature only if it adds AUC |
| 2 | HCP ZIP is a current snapshot | Known limitation | Census values do not change, but 7-9% of HCPs changed BEST_AFFL ZIP between the Q2 and Q3 2026 snapshots. Past cohorts use today's ZIP, so a few HCPs get the area they are in now, not the one they were in then | A ZIP history (quarterly BEST_AFFL snapshots) | Accept for now and note it; the size of the effect was not measured |
| 3 | Territory file frozen at Q2 2026 | Team decision | Territories are redrawn over time. A fixed file keeps training and scoring consistent, but it will age | Decide when, and by whom, the file is refreshed (for example at each model retrain) | Keep Q2 2026 until the next retrain |
| 4 | Census data is ACS 2016-2020 | Team decision | The notebook uses the 2020 file (`dem_zip_sdoh_acs20`); whether a newer release exists in UC was not checked. Area profiles change slowly, so the gain is unknown | Decide whether to request a newer AHRQ / ACS release in `01_data_improvement_requests.md` | Add as a low-priority request |
