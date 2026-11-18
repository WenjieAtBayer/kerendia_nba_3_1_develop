# Census / SDoH Data Assessment (NBA 3.1)

## Purpose
NBA 3.0 describes the area around each HCP with 22 ZIP-level ACS columns from one static CSV (`SDoH Walgreens v2.csv`, notebook 08). All 22 made the 752, but each one is weak on its own. For NBA 3.1 we want to know (1) whether the current file and join are sound, (2) which other sources can describe the HCP's area better (newer or wider ACS data, population weights, territory / county roll-ups, metro status, rurality), and (3) which census features actually separate Kerendia writers from non-writers on the 3.1 universe. This document lists those sources, what each one holds, how well it covers the 3.1 universe, and which features it could support. It is a data assessment that feeds the readiness plan. Nothing here has been built in a pipeline notebook yet.

## Method (2026-11-18)
* Population: NBA 3.1 universe `HCP_Universe_without_call_hcps` (294,727 PROVIDER_IDs). 294,578 (99.9%) map to a BH_ID through `kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING`.
* HCP ZIP: `HCP_ZIP` from the HCP's BRAND_RANK = 1 row in `pace_ker_in_house_schema.cust_mdm_best_affl_publish_pd_outp_static` (Kerendia BEST_AFFL, Q4-2026), cut to 5 digits and zero-padded. **282,881 HCPs (96.0%) have a ZIP**; 11,846 have none.
* Outcome for the signal checks: Kerendia writer in LRx V7 (`PERIOD_TYPE = 'W'`, NBRX > 0, 2025-10-24 to 2026-10-23). Baseline **9.7% (28,628 HCPs)**. Same outcome as the colocation assessment.
* "New-writer view": only HCPs with **no** Kerendia LRx row in the 3 months before the outcome window (2025-07-25 to 2025-10-23). 265,563 HCPs, baseline **5.4%**. It shows whether a feature predicts new adoption, not just continued writing.
* Specialty group for the within-specialty checks: BEST_AFFL `HCP_SPECIALTY` mapped with `KERENDIA SPECIALTY MAPPINGS HF AND CKD Q2 2026.csv`. 3.1 counts and writer rates: PCP 188,267 (7.6%), CARD 49,398 (9.1%), NEPH 14,650 (42.3%), ENDO 10,202 (18.7%), OTHERS 18,890 (6.0%), no BEST_AFFL row 11,846 (4.8%). The 07 recommendations show PCP 220,476 because notebook 20 remaps OTHERS, OBGYN and no-specialty HCPs to PCP: 188,267 + 18,890 + 1,473 + 11,846 = 220,476 exactly. CARD, NEPH and ENDO match.
* Quintiles: HCPs with a non-null value are sorted by the feature and cut into 5 equal groups (Q1 lowest, Q5 highest). rho = Spearman correlation with the writer flag on the same HCPs.
* Census values are static, so there is no feature window and no leakage risk from the census data itself. The only time-dependent input is the HCP's ZIP (a Q4-2026 snapshot applied to past months).
* These are one-feature-at-a-time checks, not model lift.
* Verdicts used below: **Build** = passes all three gates in section 1, add to the pipeline. **Test** = passes creation and value but overlaps an existing feature, so keep it only if it adds model lift when both are in the model. **Skip** = fails at least one gate. **Later** = needs data that is not in the workspace.

## 1. Sources Found

**Usable for a census feature?** "Yes" only if all three hold: (1) **can be created**, meaning the source joins to the HCP ZIP (or territory / county) one-to-one with enough coverage; (2) **not redundant**, meaning it does not repeat a feature already in the model or another source in this table; (3) **adds value**, meaning the signal check in section 3 shows a clear gap between Q1 and Q5 (or yes vs no) that also holds in the new-writer view. "No" if any one fails or has not been shown. The PROVIDER_ID to BH_ID to ZIP mapping is a common step for every source and is not counted as a linkage.

| # | Source | Grain / key | What it holds | Coverage on the 3.1 universe | Status | Usable for census feature? |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `kerendia_nba_3_volume/.../input_files/SDoH Walgreens v2.csv` | ZIPCODE (41,011) with ZCTA (32,441) | 22 ACS % / income columns | 282,857 of 282,881 HCP ZIPs match on ZIPCODE (99.99%); 281,978 HCPs (95.7% of universe) get a value | **In use** (nb 08, all 22 in the 752) | **Yes** (keep, but join on ZIPCODE, not ZCTA, and drop POSTHS_ED). Strongest columns: WHITE, LT_HS, HISPANIC (rho 0.058-0.075). Vintage now identified through source 2 |
| 2 | `whc_data_zone1_prod.dem_zip_sdoh_acs20` (UC) | ZIPCODE (41,011) with ZCTA | 325 columns: the same 22 ACS columns plus population, age bands, Medicare / Medicaid, disability, language, nativity, veterans, housing | Same ZIPs as source 1 (41,011 of 41,011) | **Not used.** It is the source of the Walgreens file: all 22 columns are identical for 100% of ZIPs. AHRQ SDOH Database 2020 ZIP file = ACS 2016-2020 5-year estimates | **Yes** (replace the CSV with this table; add population as a weight and the columns marked Build / Test in section 3.4). All 296 extra numeric columns screened: 12 reach abs(rho) >= 0.06; of the 15 strongest, 10 restate an existing column (rho 0.69-0.99) and 3 are Test |
| 3 | `zip_terr_Q2_2026.csv` (CR1 rows) | ZIP -> GEO_NUM (territory), COUNTY_NAME, STATE | Territory and county per ZIP | 282,872 HCPs (96.0%) get a territory; 329 territories (median 64 ZIPs), 3,231 counties | Used by nb 08 (3.1 draft) and nb 20 | **Yes** (territory / county roll-ups). Created: one CR1 row per ZIP. Value: TERR_SDOH_LT_HS rho 0.084 and COUNTY_SDOH_LT_HS 0.083, the strongest census features found. Not redundant: rho 0.50 between ZIP and territory deprivation |
| 4 | `whc_data_zone1_prod.vms_laad_dim_geo` (UC) | ZIP_CODE (99,999, no duplicates) | CBSA code and name, state | All 282,881 HCP ZIPs match; 269,732 have a CBSA | **Not used** | **Yes** (NO_CBSA_FLAG). Created: direct ZIP join. Value: HCPs outside any CBSA write at 7.3% vs 10.0% (new-writer 3.9% vs 5.5%). Not redundant with nb 35: rho -0.35 with county metro share, and the gap holds inside each metro-share band (section 3.6) |
| 5 | `whc_data_zone1_prod.dem_zip_ruca_code` (UC) | ZIP_CODE (3,221 distinct in 8,642 rows) | RUCA code and description | Only 15,710 universe HCPs (5.3%) match | Not used. nb 35 already reads `ruca2010revised.xlsx` and builds county-level `COUNTY_PCT_POP_METRO` / `COUNTY_PCT_POP_RURAL` | **No.** Partial ZIP list, and rurality is owned by nb 35 |
| 6 | `whc_vms_pj_v3.sdoh_walgreens`, `kerendia_oe_journey.hcp_model_sdoh_features_for_inference` | ZIPCODE, 41,011 rows, 24 columns | Copies of the Walgreens table in other projects | Same as source 1 | Not used by NBA | **No.** Exact duplicates of source 1: all 22 columns identical for 100% of the 41,011 ZIPs in both tables |
| 7 | `kerendia_bps_x.intermediate_sdoh_features` (79,017 rows, 26 cols), `kerendia_bps_x.sdoh_features_cr4_cr5` (215 rows, TERR_ID + ZCTA) | ZIPCODE / ZCTA; territory | The Walgreens columns per ZIP x TERR_ID (max 2 rows per ZIP), and 215 territory-level rows | Same 41,011 ZIPs | Not used by NBA | **No.** Same values as source 1 except that NULLs are stored as 0 (all 41,319 differing cells are Walgreens NULL -> 0; no other differences). Filling NULL with 0 is wrong for % columns, so do not use it. The territory table only covers CR4/CR5 territories (215), not CR1 |
| 8 | `junyingz.zipcodes_geo_us` (UC, personal schema) | ZIPCODE (25,711 rows) | State, county, latitude, longitude | 282,671 of 282,881 HCP ZIPs (99.9%) match | Not used | **No.** Personal schema with no owner process; county is already in source 3 and source 4 matches all ZIPs |
| 9 | `kerendia_laad_based_lrx.kerendia_laad_based_lrx_v7` | PROVIDER_ID x week | Kerendia NBRx | All writers | **In use** for the outcome | Outcome only. Not a census source |

### 1.1 Explanation: What We Are Trying to Achieve

**The idea.** A census feature answers one question: *what kind of area does this HCP practise in?* The area tells us about the patient pool the HCP sees (income, insurance, education, ethnicity, age) and therefore how likely CKD / HF patients with access to a branded drug are to come through the door. Census features never say anything about the HCP personally; they describe the place.

**Every census feature needs two inputs:**
1. **A location for the HCP**: a ZIP (from BEST_AFFL), and from it a territory and county (source 3) or CBSA (source 4).
2. **An area measure**: a value from the ACS table for that ZIP, or an average of ZIP values over the territory / county.

**Worked example.** Dr A practises in ZIP 30301, which sits in territory T-101 with 4 other ZIPs.

| Measure | ZIP 30301 | Territory T-101 (mean of 5 ZIPs) | Feature value for Dr A |
| --- | --- | --- | --- |
| % adults without high school (LT_HS) | 18% | 12% | ACS_PCT_LT_HS_ZC = 18; TERR_SDOH_LT_HS = 12 |
| Deprivation index (section 3.2) | +1.2 | +0.2 | SDOH_DEPRIVATION_INDEX = 1.2; TERR_DEPRIVATION_MEAN = 0.2 |

Illustrative numbers only. The ZIP value describes Dr A's own neighbourhood; the territory value describes the wider market Dr A's rep covers.

### 1.2 Explanation: How the Signal Check Works

The signal check asks: *do HCPs in one kind of area go on to write Kerendia more often than HCPs in another?*

1. **Take the HCPs**: all 294,727 HCPs in the NBA 3.1 universe.
2. **Give each a value**: the HCP's ZIP (or territory / county) value for the measure.
3. **Sort and split**: sort HCPs by the value and cut into 5 equal groups, Q1 (lowest) to Q5 (highest).
4. **Look forward (outcome window, 2025-10-24 to 2026-10-23)**: the share of each group that wrote Kerendia (NBRx > 0). Overall 9.7%.
5. **Compare** Q1 with Q5, and repeat on new writers only (5.4% baseline) and inside each specialty.

**Three views are used:**
* **Q1 vs Q5 and rho (3.1-3.4)**: how far apart the extremes are, and the Spearman correlation across all HCPs.
* **Within specialty (3.5)**: census measures can simply track where nephrologists or endocrinologists practise. Repeating the check inside PCP / CARD / NEPH / ENDO shows whether the area effect survives once specialty is fixed.
* **New-writer view**: repeats every check on HCPs with no Kerendia activity in the 3 months before the outcome window, so the feature is judged on new adoption.

### 1.3 Explanation by Source

**Source 1: SDoH Walgreens v2.csv (current file)**
* *What it is:* 22 ZIP-level ACS columns (race / ethnicity, education, poverty by race, unemployment, per capita income, uninsured, transport).
* *Role:* the only census input of NBA 3.0.
* *Join check (section 2):* the file has a ZIPCODE column (41,011 postal ZIPs) and a ZCTA column (32,441 census areas). 8,583 file rows have ZIPCODE different from ZCTA. Joining the HCP ZIP to **ZIPCODE** matches 282,857 HCPs; joining to **ZCTA**, as the 3.1 draft notebook (`08_census_features_creation`) does, matches only 278,414. **4,443 HCPs (1.5% of the universe) are lost** by the ZCTA join.
* *Signal:* modest. The best single columns separate Q1 and Q5 by about 5 points (WHITE 13.4% vs 7.2%, LT_HS 8.0% vs 13.3%, HISPANIC 8.3% vs 13.5%), and the gaps hold for new writers. Degree columns and HS_GRADUATE are flat.
* *Decision:* **Yes, keep**, with the ZIPCODE join and POSTHS_ED dropped (flagged for removal in the 08 recommendations).

**Source 2: dem_zip_sdoh_acs20 (UC)**
* *What it is:* a 325-column ZIP table in `whc_data_zone1_prod` with the same 41,011 ZIPs. The column names (`ACS_*_ZC`, `POINT_ZIP`, `TERRITORY`) follow the AHRQ SDOH Database layout, and the table name ends in `acs20`. [AHRQ's SDOH documentation](https://www.ahrq.gov/sites/default/files/wysiwyg/sdoh/SDOH-Data-Sources-Documentation-v1-Final.pdf) states that the 2020 ZIP file uses the ACS 2016-2020 5-year estimates and that ZIP files carry a `POINT_ZIP` variable. Both match this table.
* *Key finding:* all 22 Walgreens columns are **identical for 100% of the 41,011 ZIPs**. The "Walgreens v2" CSV is an extract of this table, so the vintage question in the 08 recommendations is answered: the data is ACS 2016-2020.
* *Role:* drop-in replacement for the CSV (same key, same values), with 300 extra columns available, including the population counts the 08 recommendations said were missing.
* *Signal of the extra columns (section 3.4):* all 296 extra numeric columns were screened. 12 reach abs(rho) >= 0.06, 62 fall between 0.04 and 0.06, and 222 are below 0.04. The strongest is % White non-Hispanic (-0.085), a sharper version of the existing WHITE column (-0.075). Age 65+, age 80+, disability and Medicare-only are flat (abs(rho) <= 0.018).
* *Decision:* **Yes.** Read it from UC instead of the CSV, use population as a weight, swap WHITE for WHITE_NONHISP, and model-test MEDICAID_ANY, MARRIED_SP_AB_F, 1UP_PERS_1ROOM and SELF_MDCR_ABOVE35. It is not a newer vintage, so it does not solve the refresh.

**Source 3: zip_terr (territory and county)**
* *What it is:* the Kerendia zip-to-territory alignment (Q2 2026), with county and state per ZIP. CR1 rows give one territory per ZIP.
* *Role:* roll ZIP values up to the territory (329 territories) and county (3,231 counties).
* *Signal:* the best census features found are roll-ups: TERR_SDOH_LT_HS (Q1 7.0% vs Q5 14.0%, rho 0.084) and COUNTY_SDOH_LT_HS (6.8% vs 14.2%, rho 0.083). They beat the ZIP-level LT_HS (0.062) because averaging over many ZIPs removes small-area noise. Territory and ZIP deprivation correlate at only 0.50, so the roll-up adds information rather than repeating it.
* *Decision:* **Yes** for TERR / COUNTY versions of LT_HS, WHITE, HISPANIC and the deprivation mean. **No** for SDOH_DEPRIVATION_VS_TERR (rho 0.020).

**Source 4: vms_laad_dim_geo (CBSA)**
* *What it is:* LAAD's geography dimension: ZIP to CBSA (metro / micropolitan area).
* *Signal:* 13,149 HCPs in a ZIP with no CBSA write at 7.3% vs 10.0% for the rest (new-writer 3.9% vs 5.5%). CBSA size (universe HCPs per CBSA) is weak (rho 0.026).
* *Overlap with nb 35:* I rebuilt nb 35's county metro share (population-weighted share of RUCA 1-3 tracts in `ruca2010revised.xlsx`), joined on the zip_terr county (nb 35 itself joins on the MDM address county). It matched 271,300 HCPs. Correlation with NO_CBSA is -0.35, and NO_CBSA HCPs write less inside every metro-share band (section 3.6).
* *Decision:* **Build** NO_CBSA_FLAG. **Skip** CBSA_HCP_COUNT.

**Source 5: dem_zip_ruca_code**
* *Why No:* only 3,221 ZIPs; 15,710 universe HCPs match. nb 35 reads the full RUCA file and owns rurality.

**Sources 6-8: copies and personal tables**
* *Why No:* the two source 6 tables are exact copies of the Walgreens file. Source 7 holds the same values but replaces NULL with 0, and its territory table covers CR4/CR5 only. Source 8 sits in a personal schema and adds nothing over sources 3 and 4.

## 2. How Each HCP Gets an Area

| Step | HCPs | % of universe |
| --- | --- | --- |
| NBA 3.1 universe | 294,727 | 100% |
| Mapped to BH_ID | 294,578 | 99.9% |
| With a BEST_AFFL rank-1 ZIP | 282,881 | 96.0% |
| ZIP found in the file on **ZIPCODE** | 282,857 | 96.0% |
| ZIP found in the file on **ZCTA** (3.1 draft join) | 278,414 | 94.5% |
| **Lost by the ZCTA join** | **4,443** | **1.5%** |
| With a non-null ACS value (LT_HS) after the ZIPCODE join | 281,978 | 95.7% |
| With a CR1 territory (zip_terr Q2 2026) | 282,872 | 96.0% |
| With a CBSA (vms_laad_dim_geo) | 269,732 | 91.5% |
| No ZIP at all | 11,846 | 4.0% |

Observations:
* The 11,846 HCPs without a ZIP are the same HCPs without a BEST_AFFL rank-1 row. 11,695 of them have a BH_ID, but none of those BH_IDs has any BEST_AFFL row at any brand rank, so there is no fallback ZIP in this source. They write at 4.8%, half the baseline, so "no area data" is itself informative. Tree models can use the NULL directly; an explicit `SDOH_MISSING_FLAG` should be 1 for them, not NULL.
* 903 HCPs have a ZIP but no LT_HS value: 24 HCPs have a ZIP that is not in the file, and the other 879 sit in 34 ZIPs whose source value is null. 864 of the 879 are in ZIPs with zero or missing population, 169 in point ZIPs (single large facilities) and 104 in US territories (categories overlap). These are true gaps in the ACS, not join failures.
* BEST_AFFL HCP_ZIP is already 5 digits for all but one HCP, so the 3.0 leading-zero defect (12,705 HCPs lost in 3.0, see the 08 analysis) does not occur with this ZIP source. The 3.1 nb 08 draft also pads the ZIP to 5 digits before the join, and the 3.1 nb 20 contains no zfill, lpad or lstrip step on the ZIP (searched the notebook source), so the defect does not come back in 3.1.
* ZCTA values are shared: 41,011 file ZIPs map to 32,441 distinct ZCTAs, and 8,583 rows have a ZCTA code different from their ZIPCODE. ZIPs carry the values of their ZCTA, which is correct, but they must not be double counted in territory or county averages. The roll-ups in section 3.3 keep one row per ZCTA.

## 3. Signal Check

### 3.1 Existing ACS columns (ZIP level, source 1 / 2, ZIPCODE join)

| Column | Fill (universe) | Q1 writer rate | Q5 writer rate | New-writer Q1 | New-writer Q5 | rho |
| --- | --- | --- | --- | --- | --- | --- |
| ACS_PCT_WHITE_ZC | 95.7% | 13.4% | 7.2% | 6.9% | 4.0% | -0.075 |
| ACS_PCT_LT_HS_ZC | 95.7% | 8.0% | 13.3% | 4.8% | 7.0% | 0.062 |
| ACS_PCT_HISPANIC_ZC | 95.7% | 8.3% | 13.5% | 4.6% | 7.1% | 0.058 |
| ACS_PCT_OTHER_RACE_ZC | 95.7% | 8.2% | 13.1% | 4.6% | 6.9% | 0.056 |
| ACS_PCT_UNINSURED_ZC | 95.5% | 7.6% | 12.0% | 4.4% | 6.6% | 0.050 |
| ACS_PCT_UNINSURED_BELOW64_ZC | 95.5% | 7.6% | 11.7% | 4.4% | 6.4% | 0.049 |
| ACS_PCT_UNEMPLOY_ZC | 95.5% | 8.3% | 11.7% | 4.8% | 6.5% | 0.044 |
| ACS_PCT_BLACK_ZC | 95.7% | 8.0% | 11.8% | 4.3% | 6.5% | 0.040 |
| ACS_PER_CAPITA_INC_ZC | 95.6% | 12.2% | 8.9% | 6.7% | 5.1% | -0.039 |
| ACS_PCT_POV_WHITE_ZC | 95.3% | 8.5% | 11.2% | 4.6% | 6.3% | 0.036 |
| ACS_PCT_POSTHS_ED_ZC | 95.7% | 11.9% | 8.8% | 6.3% | 5.2% | -0.036 |
| ACS_PCT_TRANSPORT_ZC | 95.5% | 8.7% | 11.3% | 5.2% | 5.8% | 0.031 |
| ACS_PCT_GRADUATE_DGR_ZC | 95.7% | 11.1% | 8.9% | 5.9% | 5.3% | -0.026 |
| ACS_PCT_BACHELOR_DGR_ZC | 95.7% | 10.9% | 9.1% | 5.9% | 5.4% | -0.025 |
| ACS_PCT_POV_HISPANIC_ZC | 94.8% | 8.2% | 10.6% | 4.5% | 6.0% | 0.024 |
| ACS_PCT_POV_ASIAN_ZC | 92.1% | 8.7% | 10.6% | 4.8% | 6.0% | 0.022 |
| ACS_PCT_ASIAN_ZC | 95.7% | 9.6% | 11.6% | 5.3% | 6.2% | 0.021 |
| ACS_PCT_POV_BLACK_ZC | 93.6% | 8.5% | 10.0% | 4.7% | 5.8% | 0.016 |
| ACS_PCT_PUBL_TRANSIT_ZC | 95.5% | 9.5% | 10.7% | 5.1% | 5.9% | 0.015 |
| ACS_PCT_COLLEGE_ASSOCIATE_DGR_ZC | 95.7% | 10.2% | 9.0% | 5.8% | 4.9% | -0.014 |
| ACS_PCT_EDUC_ZC | 95.5% | 10.7% | 9.7% | 5.7% | 5.6% | -0.011 |
| ACS_PCT_HS_GRADUATE_ZC | 95.7% | 9.2% | 9.3% | 5.4% | 5.0% | 0.002 |

**How to read it:**
* **Race / ethnicity, low education and uninsured share carry the signal.** HCPs in the most diverse, least-educated, most-uninsured fifth of ZIPs write at about 12-13.5%, against 7-8% in the opposite fifth. The direction holds for new writers (about 6.5-7% vs 4-5%).
* **Degree columns are weak or flat** (BACHELOR, GRADUATE, ASSOCIATE, EDUC, HS_GRADUATE: |rho| <= 0.026).
* These ranks agree with the 08 recommendations, which used a different ZIP source (nb 20 / LAAD). The result does not depend on the ZIP source.

### 3.2 ZIP-level composites (from the existing 22 columns)

| Candidate | Q1 vs Q5 | New-writer Q1 vs Q5 | rho | Verdict |
| --- | --- | --- | --- | --- |
| ACS_PCT_NON_WHITE_ZC (100 - WHITE) | 7.2% vs 13.4% | 4.0% vs 6.9% | 0.075 | **Skip.** Exact mirror of WHITE; keep one of the two |
| SDOH_DEPRIVATION_INDEX (mean z of LT_HS, UNEMPLOY, UNINSURED_BELOW64, TRANSPORT, -PER_CAPITA_INC) | 8.2% vs 13.0% | 4.8% vs 7.0% | 0.058 | **Test.** rho 0.89 with LT_HS and -0.91 with PER_CAPITA_INC; no stronger than LT_HS alone |
| ACS_PCT_BACHELOR_PLUS_ZC | 11.0% vs 8.9% | 5.9% vs 5.3% | -0.026 | **Skip.** Same as GRADUATE alone |
| SDOH_POVERTY_DISPARITY | 10.0% vs 9.3% | 5.4% vs 5.2% | -0.007 | **Skip.** No signal |

### 3.3 Territory and county roll-ups (source 3)

**How it is calculated:**
1. Give every ZIP in the file the deprivation index from 3.2.
2. Map each ZIP to its CR1 territory and county with zip_terr Q2 2026. Keep one row per ZCTA so shared ZCTAs are not counted twice.
3. Average each measure over all ZIPs in the territory (or county), unweighted. Every HCP gets the value of its own ZIP's territory (county).
4. `COUNTY_DEP_POPW` repeats step 3 weighted by `ACS_TOT_POP_WT_ZC` from source 2.

| Candidate | Fill | Q1 vs Q5 | New-writer Q1 vs Q5 | rho | Verdict |
| --- | --- | --- | --- | --- | --- |
| TERR_SDOH_LT_HS | 96.0% | 7.0% vs 14.0% | 4.0% vs 7.3% | 0.084 | **Build.** Strongest census feature |
| COUNTY_SDOH_LT_HS | 95.9% | 6.8% vs 14.2% | 3.9% vs 7.3% | 0.083 | **Build** (or the territory version; test both) |
| TERR_SDOH_WHITE | 96.0% | 14.1% vs 6.8% | 7.5% vs 3.9% | -0.079 | **Build** |
| COUNTY_SDOH_WHITE | 95.9% | 13.5% vs 7.2% | 7.0% vs 4.1% | -0.075 | **Test** |
| COUNTY_DEP_POPW (population-weighted) | 95.9% | 7.2% vs 13.8% | 4.2% vs 7.4% | 0.076 | **Build** in place of the unweighted county mean |
| COUNTY_DEPRIVATION_MEAN (unweighted) | 95.9% | 7.8% vs 13.1% | 4.5% vs 6.9% | 0.064 | **Skip** if the weighted version is built (rho 0.93 between them) |
| TERR_SDOH_HISPANIC | 96.0% | 8.3% vs 14.2% | 4.6% vs 7.4% | 0.060 | **Test** |
| TERR_DEPRIVATION_MEAN | 96.0% | 8.6% vs 13.4% | 4.8% vs 7.0% | 0.059 | **Test** |
| SDOH_DEPRIVATION_VS_TERR (ZIP minus territory) | 95.5% | 9.5% vs 11.3% | 5.3% vs 6.0% | 0.020 | **Skip** |

Correlation between levels (Spearman): ZIP deprivation vs territory 0.50, vs county 0.54; territory vs county 0.70. The roll-ups are related to the ZIP value but not copies of it.

### 3.4 New columns from dem_zip_sdoh_acs20 (source 2)

| Column | Fill | Q1 vs Q5 | New-writer Q1 vs Q5 | rho | Verdict |
| --- | --- | --- | --- | --- | --- |
| ACS_PCT_ENGL_NOT_WELL_ZC | 95.7% | 8.1% vs 13.7% | 4.5% vs 7.1% | 0.061 | **Skip.** rho 0.78 with HISPANIC and 0.83 with FOREIGN_BORN; HISPANIC is already in the model |
| ACS_PCT_FOREIGN_BORN_ZC | 95.0% | 8.8% vs 13.3% | 4.7% vs 6.9% | 0.051 | **Skip.** rho 0.69 with HISPANIC |
| ACS_PCT_MEDICAID_ANY_ZC | 95.5% | 8.6% vs 12.4% | 5.0% vs 6.5% | 0.046 | **Test.** rho 0.46 with UNINSURED and 0.26 with HISPANIC, so it is partly new payer-mix information |
| ACS_TOT_POP_WT_ZC (population) | 95.9% | 7.9% vs 12.3% | 4.7% vs 6.4% | 0.044 | **Build** as a weight for the roll-ups; test as a feature (log scale) |
| ACS_PCT_VET_ZC | 95.7% | 12.2% vs 8.7% | 6.7% vs 4.7% | -0.039 | **Test** |
| ACS_PCT_HH_ALONE_ABOVE65_ZC | 95.3% | 11.0% vs 9.4% | 5.9% vs 5.3% | -0.019 | **Skip** |
| ACS_PCT_AGE_ABOVE65_ZC | 95.7% | 11.0% vs 9.0% | 6.2% vs 5.0% | -0.018 | **Skip.** Older ZIPs do not write more |
| ACS_PCT_AGE_ABOVE80_ZC | 95.7% | 10.1% vs 9.4% | 5.7% vs 5.2% | -0.011 | **Skip** |
| ACS_PCT_MEDICARE_ONLY_ZC | 95.5% | 9.5% vs 10.3% | 5.3% vs 5.6% | 0.010 | **Skip** |
| ACS_PCT_DISABLE_ZC | 95.5% | 9.5% vs 10.0% | 5.3% vs 5.5% | 0.003 | **Skip** |

**Full screen of all 296 extra numeric columns** (rho with the writer flag, ZIPCODE join): 12 columns reach abs(rho) >= 0.06, 62 fall between 0.04 and 0.06, and 222 are below 0.04. The 15 strongest:

"Closest existing column" = the highest Spearman correlation (HCP level) with any of the 22 current columns or with population.

| Column | Fill | rho with writer | Closest existing column (rho) | Verdict |
| --- | --- | --- | --- | --- |
| ACS_PCT_WHITE_NONHISP_ZC | 95.7% | -0.085 | WHITE (0.92) | **Build** in place of ACS_PCT_WHITE_ZC (-0.075) |
| ACS_PCT_HOUSEHOLDER_WHITE_ZC | 95.3% | -0.080 | WHITE (0.98) | **Skip** (copy of WHITE) |
| ACS_PCT_MARRIED_SP_AB_F_ZC | 95.6% | 0.074 | LT_HS (0.61) | **Test** |
| ACS_PCT_WHITE_COMB_ZC | 95.7% | -0.072 | WHITE (0.99) | **Skip** (copy of WHITE) |
| ACS_PCT_1UP_PERS_1ROOM_ZC | 95.3% | 0.065 | HISPANIC (0.61) | **Test** |
| ACS_TOT_GRANDCHILDREN_GP_ZC | 95.9% | 0.064 | Population (0.69) | **Skip** (a raw count that grows with population) |
| ACS_PCT_MARRIED_SP_AB_M_ZC | 95.7% | 0.063 | LT_HS (0.58) | **Skip** (same measure as the F version, which is stronger) |
| ACS_PCT_HH_KID_1PRNT_ZC | 95.3% | 0.062 | LT_HS (0.74) | **Skip** |
| ACS_PCT_SPANISH_ZC | 95.7% | 0.061 | HISPANIC (0.96) | **Skip** (copy of HISPANIC) |
| ACS_PCT_ENGL_NOT_WELL_ZC | 95.7% | 0.061 | HISPANIC (0.78) | **Skip** |
| ACS_PCT_HH_LIMIT_ENGLISH_ZC | 95.3% | 0.061 | HISPANIC (0.74) | **Skip** |
| ACS_PCT_SELF_MDCR_ABOVE35_ZC | 95.5% | -0.060 | WHITE (0.63) | **Test** |
| ACS_PCT_ENGLISH_ZC | 95.7% | -0.059 | HISPANIC (0.82) | **Skip** |
| ACS_PCT_HOUSEHOLDER_OTHER_ZC | 95.3% | 0.058 | OTHER_RACE (0.95) | **Skip** (copy of OTHER_RACE) |
| ACS_PCT_ENGL_WELL_ZC | 95.7% | 0.058 | HISPANIC (0.76) | **Skip** |

Rule used: closest correlation >= 0.70 means Skip; 0.58-0.63 means Test. Of the 15 strongest extra columns, 10 restate an existing column (0.69-0.99). Three overlap only moderately (MARRIED_SP_AB_F, 1UP_PERS_1ROOM, SELF_MDCR_ABOVE35) and go to the model test. MARRIED_SP_AB_M (0.58) is skipped only because it measures the same thing as MARRIED_SP_AB_F, which is stronger. WHITE_NONHISP replaces WHITE.

### 3.6 Metro status: NO_CBSA vs nb 35 county metro share

County metro share = population-weighted share of RUCA 1-3 tracts (nb 35 logic, `ruca2010revised.xlsx`). Writer rate by band:

| County metro share | In a CBSA: HCPs | In a CBSA: writer rate | No CBSA: HCPs | No CBSA: writer rate |
| --- | --- | --- | --- | --- |
| 0% | 14,899 | 9.4% | 7,560 | 6.6% |
| >0-50% | 10,966 | 9.1% | 3,793 | 7.8% |
| 50-<100% | 71,454 | 10.8% | 986 | 8.5% |
| 100% | 161,415 | 9.7% | 227 | 6.6% |

Inside every band, HCPs whose own ZIP has no CBSA write 1.3-3.1 points less. The ZIP-level CBSA flag carries information that the county-level metro share does not.

### 3.5 Within-specialty check (writer rate Q1 -> Q5)

| Feature | PCP | CARD | NEPH | ENDO |
| --- | --- | --- | --- | --- |
| ACS_PCT_WHITE_ZC | 11.4% -> 5.4% | 10.1% -> 8.3% | 41.3% -> 43.3% | 20.6% -> 16.4% |
| ACS_PCT_LT_HS_ZC | 5.0% -> 12.0% | 8.5% -> 10.5% | 39.5% -> 44.2% | 16.0% -> 20.9% |
| SDOH_DEPRIVATION_INDEX | 5.0% -> 11.4% | 8.8% -> 10.8% | 39.9% -> 44.2% | 14.9% -> 22.2% |
| ACS_PCT_HISPANIC_ZC | 6.4% -> 11.6% | 9.1% -> 10.0% | 38.4% -> 46.8% | 14.7% -> 23.9% |
| ACS_PCT_UNINSURED_ZC | 5.1% -> 9.9% | 7.7% -> 10.0% | 37.4% -> 46.7% | 12.2% -> 22.7% |

* **The area effect is not just specialty.** In PCP (the largest group) the writer rate more than doubles from Q1 to Q5 for every measure.
* **It is weakest in cardiology** (about 2 points) and flips sign for WHITE inside nephrology (41.3% -> 43.3%), where nearly half of all HCPs write anyway.
* HISPANIC and UNINSURED are the most consistent across all four groups.

## 4. Candidate Features for the Readiness Plan

| Feature | Source | Logic | Evidence | Readiness |
| --- | --- | --- | --- | --- |
| 21 ACS columns (all except POSTHS_ED) | 2 (or 1) | ZIP value, join on **ZIPCODE** | Section 3.1; 4,443 more HCPs than the ZCTA join | **Build.** Fix the join, read from UC |
| SDOH_MISSING_FLAG | 2 | 1 if the HCP has no ZIP or the ZIP has no ACS value | 11,846 HCPs without a ZIP write at 4.8% | **Build** (1 for no-ZIP HCPs too) |
| TERR_SDOH_LT_HS, TERR_SDOH_WHITE | 2 + 3 | Unweighted mean over CR1 territory ZIPs, one row per ZCTA | rho 0.084 / -0.079 | **Build** |
| COUNTY_DEP_POPW (and COUNTY_SDOH_LT_HS) | 2 + 3 | Population-weighted county mean | rho 0.076 / 0.083 | **Build** one county measure; test the other |
| ACS_TOT_POP_WT_ZC / LOG_POP | 2 | ZIP population | rho 0.044; needed as a weight | **Build** as weight, **Test** as feature |
| ACS_PCT_WHITE_NONHISP_ZC (replaces ACS_PCT_WHITE_ZC) | 2 | ZIP value | rho -0.085 vs -0.075 for WHITE | **Build** |
| ACS_PCT_MEDICAID_ANY_ZC | 2 | ZIP value | rho 0.046; 0.46 with UNINSURED | **Test** |
| ACS_PCT_MARRIED_SP_AB_F_ZC, ACS_PCT_1UP_PERS_1ROOM_ZC, ACS_PCT_SELF_MDCR_ABOVE35_ZC | 2 | ZIP value | rho 0.074 / 0.065 / -0.060; closest existing column 0.61 / 0.61 / 0.63 | **Test** |
| ACS_PCT_ENGL_NOT_WELL_ZC, ACS_PCT_FOREIGN_BORN_ZC and the other language / household columns | 2 | ZIP value | rho 0.69-0.83 with HISPANIC | **Skip** |
| SDOH_DEPRIVATION_INDEX, TERR_DEPRIVATION_MEAN | 1/2 + 3 | Mean z-score | rho 0.058 / 0.059; no better than LT_HS | **Test** (optional compact summary) |
| NO_CBSA_FLAG | 4 | 1 if the ZIP has no CBSA | 7.3% vs 10.0%; new-writer 3.9% vs 5.5%; holds inside every nb 35 metro band | **Build** |
| SDOH_DEPRIVATION_VS_TERR, POVERTY_DISPARITY, BACHELOR_PLUS, NON_WHITE | 1 + 3 | As in the 08 recommendations | rho 0.020, -0.007, -0.026, mirror of WHITE | **Skip** |
| CDC PLACES diabetes / heart disease prevalence, SVI / ADI, HRSA AHRF specialist supply | External | See the 08 recommendations section 6 | Not in the catalog: an `information_schema.tables` search for names containing places, svi, ahrf, area_deprivation, _adi_, cdc, acs2 or acs_2 (non-radiology schemas) returns only the two `dem_zip_sdoh_acs20` tables and two unrelated `kerendia_rb` pipeline objects | **Later.** Needs a new feed. PLACES has no CKD measure: [CDC lists it as discontinued in the 2024 release](https://www.cdc.gov/places/current-release-notes/) |
| ACS 2020-2024 refresh | External | Same columns, newer vintage | The current data is ACS 2016-2020. The [2020-2024 ACS 5-year estimates were released on January 29, 2026](https://www.census.gov/programs-surveys/acs/news/data-releases/2024/release.html) | **Later.** AHRQ-format files for the newer years must be sourced (AHRQ or a rebuild from Census tables) |

## 5. Data Issues to Resolve Before Build
1. **ZCTA join in the 3.1 draft.** `08_census_features_creation` states "Join key = `ZCTA` padded to 5 digits; one row kept per ZCTA", so the 8,583 file rows whose ZIPCODE differs from ZCTA are never matched by postal ZIP. Switch to ZIPCODE: +4,443 HCPs, and each ZIP gets its own row's values (which are already the ZCTA values).
2. **Vintage.** The CSV equals `dem_zip_sdoh_acs20`, the AHRQ SDOH 2020 ZIP file, which uses the ACS 2016-2020 5-year estimates. The data is 6 years older than the 2020-2024 release.
3. **Shared ZCTAs in roll-ups.** The file has 41,011 ZIPs but only 32,441 distinct ZCTAs, so many ZIPs share a ZCTA (8,583 rows have ZIPCODE different from ZCTA). Average over distinct ZCTAs, not ZIPs, or one area is counted several times.
4. **Unweighted averages.** The CSV has no population column. Source 2 has one; use it for county (and territory) means.
5. **ZIP snapshot.** The HCP ZIP comes from the current BEST_AFFL table, but it is applied to past training months. Compared with the quarterly copies in `kerendia_cp` (rank-1 rows, HCPs present in both): Q2-2026 has the same ZIP for 91.17% (6,959 of 78,771 differ), Q3-2026 for 92.58% (6,267 of 84,464 differ), Q4-2026 for 99.82% (167 of 91,239 differ). About 8% of HCPs change ZIP within two quarters. Use the snapshot that matches each training cohort's date. The quarterly copies cover only 78-91K HCPs, so for the rest the current ZIP is the only option.
6. **Territory alignment.** TERR_* features change when territories are realigned. Freeze the zip_terr file used (Q2 2026 here) so training and inference use the same mapping.
7. **No-ZIP HCPs.** 11,846 universe HCPs (4.0%) have no BEST_AFFL row at any brand rank, and nb 20 reads the same table, so it is not a fallback. Set SDOH_MISSING_FLAG = 1 for them. The 3.1 nb 08 draft leaves it NULL for the 14,354 no-ZIP HCPs in its 314,920 universe (314,920 - 300,566 with a ZIP).

## 6. Recommended Order
1. **Fix the join and the source**: read `dem_zip_sdoh_acs20` from UC, join on ZIPCODE, drop POSTHS_ED, set SDOH_MISSING_FLAG for all HCPs. No new data.
2. **Territory / county roll-ups**: TERR_SDOH_LT_HS, TERR_SDOH_WHITE and one population-weighted county measure. Strongest census signal found.
3. **acs20 additions**: population as the roll-up weight, WHITE_NONHISP in place of WHITE, NO_CBSA_FLAG.
4. **Model test** of the Test features (MEDICAID_ANY, MARRIED_SP_AB_F, 1UP_PERS_1ROOM, SELF_MDCR_ABOVE35, deprivation index, TERR_SDOH_HISPANIC, TERR_DEPRIVATION_MEAN, COUNTY_SDOH_WHITE, LOG_POP): keep each only if it adds lift with its overlapping feature already in the model.
5. **External feeds** (ACS refresh, CDC PLACES, SVI / ADI, HRSA) as a later phase.

## Summary
The census inputs are in better shape than expected. The "Walgreens" CSV is an exact extract of a UC table (`dem_zip_sdoh_acs20`) that also holds population and 300 more columns, so the file can be replaced without a new feed. One join defect needs fixing in the 3.1 draft (ZCTA instead of ZIPCODE, 4,443 HCPs lost). The signal is modest at ZIP level (best of the current 22 columns rho -0.075; best acs20 column, WHITE_NONHISP, -0.085) but clearer when ZIP values are rolled up to the territory or county (rho 0.08, Q5 writer rate about twice Q1), and it holds for new writers and inside PCP. Composite indices add little over the best single columns. Of the 296 extra acs20 columns, the strongest mostly restate existing race / language columns; WHITE_NONHISP replaces WHITE and three moderately overlapping columns go to a model test. The ZIP-level CBSA flag adds information beyond nb 35's county metro share. Disease prevalence and the 2020-2024 ACS vintage need external data.
