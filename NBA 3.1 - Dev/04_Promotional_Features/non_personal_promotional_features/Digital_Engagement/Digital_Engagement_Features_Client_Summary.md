# Digital Engagement Features (HCP Paid Media): NBA 3.0 vs NBA 3.1

**Audience:** Kerendia brand, analytics and OE teams  
**Scope:** Family 1, HCP paid media (banner ads, 3rd-party emails, custom placements on medical sites and apps)  
**Notebook:** `Digital_Engagement/24_Features_Digital_NBA31` (rewrite of NBA 3.0 `03_HCP_Level_Features/24_Features_Digital`)  
**Based on:** section 3.1 of `52_digital_feature_families_nba30_vs_nba31.md` and the NBA 3.1 notebook code  
**Date:** 6 November 2026

> HQ email, iRep email, calls, samples, CLM / clickstream, Request-a-Rep and DTC (patient) media are **not** in this family. Each has its own feature notebook.

---

## Summary in one page

* **The problem.** In NBA 3.0, digital barely helped the model. The best HCP digital feature was only **rank 68 of 752**, and no feature named a media partner (Doximity, Medscape, Epocrates, ...).
* **Why.** (1) A strict brand filter dropped most of the data from some vendors (up to **88.5%** for Doceree). (2) The "best" banner feature mostly marked the date ("after April 2025"), not a real media effect. (3) One programmatic vendor, PulsePoint, makes up **93.7%** of all exposure, so totals hid the placements doctors respond to. (4) The columns were built from whatever values existed on the day of the run, so the feature list changed between runs.
* **What NBA 3.1 does.** It keeps all Kerendia data and maps every vendor and placement with a **fixed dictionary** (38 placements, 18 vendors). It builds a **fixed list of 144 features**: totals, channels, placements, response rates, recency, breadth, trend and indication (HF / CKD). It also uses the NBA 3.1 HCP universe and the 28 monthly cohorts.
* **What this gives the business.** The model can now tell "a doctor who was shown a lot" from "a doctor who responds", see which partner and placement each doctor responds to, and get the same columns at every run.

---

## 1. NBA 3.0 compared with NBA 3.1

### 1.1 What was happening in NBA 3.0

The NBA 3.0 notebook read the marketing-mix (MMX) table, kept only rows whose brand was **exactly** `KERENDIA`, and turned the data into columns with three **dynamic pivots** (by channel, by vendor, by tactic). Each pivot was crossed with 4 measures, 1 / 3 / 6 month windows and "running" (all-time) totals. The result was **684 columns**. The model kept only 9 of them, mostly banner, HQ email and iRep email.

Where the digital features ranked in NBA 3.0 (out of 752 features; rank 1 = most useful):

| Rank | NBA 3.0 feature | Comment |
| --- | --- | --- |
| 68 | `DIGITAL_BANNER_TACTIC_EXPOSURE_IN_LAST_3_MONTH` | Best HCP digital feature |
| 151 / 200 / 644 | `DIGITAL_RUNNING_BANNER_EXPOSURE`, `DIGITAL_BANNER_EXPOSURE_IN_LAST_3_MONTH`, `..._1_MONTH` | More banner variants |
| 688 / 695 / 698 | HQ email exposure / light engagement (from MMX) | Duplicates the HQ email family |
| 738 / 743 | iRep email exposure (from MMX) | Duplicates the personal block |

### 1.2 What the data showed (the four findings behind the change)

**Finding A: the brand filter threw away data.** Kerendia rows carry brand values by indication (`KERENDIA HF`, `KERENDIA_CKD`, `KERENDIA UACR`, ...). NBA 3.0 kept only the exact value `KERENDIA`.

| Vendor | Exposure, all Kerendia brand values | Exposure kept by NBA 3.0 | Share dropped |
| --- | --- | --- | --- |
| Doceree | 854,996 | 98,527 | **88.5%** |
| ReachMD | 46,329 | 6,240 | **86.5%** |
| PeerDirect | 502,571 | 164,369 | **67.3%** |
| Doximity | 1,452,826 | 1,450,873 | 0.1% |

**Finding B: the rank-68 banner feature marked the date, not a media effect.** Banner exposure is zero until April 2025 (when Doceree, OpenEvidence and PeerDirect banners started). With the NBA 3.0 filter it then switches on and off from month to month (for example 32,892 in Jul 2025, 0 in Dec 2025, 3,559 in Mar 2026). The model could learn "after April 2025", not "banners work".

**Finding C: one vendor dominated the totals.** PulsePoint (programmatic display) has **98.5%** of banner exposure and **93.7%** of all paid-media exposure, but doctors rarely react to it:

| Vendor / channel | Exposure | Engagement | Engagement per exposure |
| --- | --- | --- | --- |
| PulsePoint banner | 109,297,058 | 83,898 | 0.08% |
| Medscape 3rd-party email | 754,668 | 337,909 | 44.8% |
| Epocrates custom | 182,828 | 83,553 | 45.7% |
| Doximity custom | 1,452,826 | 154,700 | 10.6% |

So a plain "total exposure" mostly measured PulsePoint and hid the smaller placements with much higher response.

**Finding D: the vendor list kept changing.** Paid-media vendors active per month: 4 (Jan 2025), 8 (Apr 2025), 14 (Dec 2025), 6 (Oct 2026). With dynamic pivots, every change added or removed columns, so the model did not get the same inputs at each run.

### 1.3 What changed in NBA 3.1

| Topic | NBA 3.0 | NBA 3.1 |
| --- | --- | --- |
| Brand filter | Brand exactly `KERENDIA` | Every brand value that contains `KERENDIA`; the indication (HF / CKD) becomes a feature dimension |
| Scope | Calls and samples removed, but HQ email and iRep email kept as channels | Paid media only (banner, 3rd-party email, custom). HQ email, iRep email, calls and samples moved to their own families |
| Mapping of vendors / tactics | Exact tactic names; renamed tactics fell into `OTHER_TACTIC` | Fixed **placement dictionary** (44 rules, 38 placements, 18 vendors), case- and spacing-insensitive, with an unmapped report at every run |
| Feature list | 3 dynamic pivots, 684 columns that change between runs | **Fixed list of 144 features** generated from configuration |
| Running (all-time) totals | Yes | Removed |
| Doctor key | `NPI_NUMBER` | `PROVIDER_ID` of the NBA 3.1 HCP universe (294,726 HCPs) |
| Time grain | One inference cohort | 28 monthly cohorts (c1 to c28: training, testing, holdout) |
| Windows | Calendar months, including the unfinished current month | 1 / 3 / 6 / 12 months ending exactly on each cohort's lookback end date |
| NPI quality | `PDRP` / `'NULL'` values counted as doctors | Only valid 10-digit NPIs |
| Quality checks | None built in | Dictionary self-test, unmapped alert, data-end check, leakage check, schema and invariant QC, independent recompute |

---

## 2. Step-by-step feature creation

| Step | What happens | Why |
| --- | --- | --- |
| **1. Configuration** | Sets sources, output paths and rules: windows 1 / 3 / 6 / 12 months, digital data from 1 Jan 2025, recency default 999 days, trend needs at least 6 months of history, unmapped alert above 1%. | All rules sit in one place and are applied the same way every run. |
| **2. Cohorts** | Reads the 28 NBA 3.1 promotional cohorts. Every cohort's lookback ends on the **17th** of the month (e.g. c28 ends 17 Sep 2026). | Same time frame as the other NBA 3.1 promotional features. |
| **3. Cohort-aligned months** | Each event date is put in a "cohort month" that runs from the 18th of one month to the 17th of the next. A 3-month window is then exactly the 3 cohort months up to the lookback end. A self-test checks the edge dates (17th vs 18th). | Windows end exactly on the cohort end date: nothing after it is used (no leakage), and nothing is cut off. |
| **4. Digital history per cohort** | Counts how many complete months of digital data each cohort has (`DIGITAL_HISTORY_MONTHS`, 0 to 12). MMX paid media starts in Jan 2025, so c1 to c8 have 0 and c9 onward have 1 to 12. | The model can tell "no exposure" from "no data yet". |
| **5. HCP universe and ID mapping** | Loads the NBA 3.1 HCP universe (placeholder ID `0` removed) and maps NPI to `PROVIDER_ID` with `kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING`. Only 10-digit NPIs are kept. If an NPI maps to more than one `PROVIDER_ID`, the smallest is kept (11 such NPIs). | One doctor key across all NBA 3.1 features, and each exposure counted once. |
| **6. Placement dictionary** | 44 fixed rules map each raw (channel, vendor, tactic) value to a clean channel, vendor and placement. Exclusion rules take out calls, samples, HQ email and iRep email. Matching ignores case and extra spaces. A 12-case self-test covers the NBA 3.0 failures (spelling, case, empty or renamed tactic, new vendor). | Vendors and tactics are spelled differently over time; the dictionary keeps them stable. |
| **7. Load MMX and report unmapped rows** | Loads all MMX rows with a Kerendia brand value from 2025 on, applies the dictionary, and writes an **unmapped report** at every run (alert if more than 1% of rows or exposure is unmapped). Checks that paid-media data reaches every cohort end. | New vendors or tactics are caught instead of silently lost. Latest run: **0.0% unmapped**; data to 29 Oct 2026 (3rd-party email, custom) and 30 Oct 2026 (banner). |
| **8. Indication tag** | Tags each row HF, CKD, BOTH or GENERAL from the brand value (e.g. `KERENDIA HF`, `KERENDIA_CKD`, `UACR`, `FINEARTS`, `FINEONE`). | Shows whether a doctor saw heart-failure or kidney messaging. |
| **9. Monthly stage table** | Builds one row per HCP x cohort month with fixed columns: totals with and without PulsePoint, each channel, each placement, each vendor, each indication, and the last exposure / engagement date. It checks that the channels add up to the total. | A fixed intermediate table; no dynamic pivot. |
| **10. Feature specification** | Generates the fixed list of 144 features and a **feature manifest** (name, family, type, window, description, dictionary version). | Same columns at every run, with documentation of each one. |
| **11. Feature build** | For each HCP x cohort, sums the 12 cohort months up to the lookback end, then derives rates, recency, breadth and trend. A leakage check makes sure no event after the cohort end is used. | Features show exactly what was known on the cohort end date. |
| **12. Full grid and defaults** | Every HCP in the universe gets a row for every cohort (294,726 x 28). HCPs without paid media get 0 for counts, 999 for "days since", NULL for rates (no exposure, so no rate) and NULL for trend when there are fewer than 6 months of history. | One row per HCP x cohort, as the model expects. |
| **13. QC** | Checks the schema against the fixed list, the row count, that IDs are unique, that windows are nested (1M <= 3M <= 6M <= 12M), that channels add up to the total, and recomputes sample values directly from raw MMX. | Catches errors before the features reach the model. |
| **14. Per-cohort summary** | Number of HCPs exposed, total exposure and engagement per cohort. | Quick view of how digital coverage builds up over time. |

**Outputs** (folder `kerendia_nba_3_1_volume/notebook_output/digital_engagement_nba_3_1/`): the feature file `kerendia_nba_3_1_hcp_model_digital_paid_media_features.parquet`, the placement dictionary, the unmapped report (appended each run), the feature manifest and the expected schema.

---

## 3. Types of digital engagement features created

There are **144 features** in 8 groups, plus 8 identifier / context columns (`HCP_COHORT_ID`, `PROVIDER_ID`, `COHORT`, `DATASET`, `PREDICTION_MONTH`, `SVC_DT`, `DIGITAL_HISTORY_MONTHS`, `PULL_DT`).

| Group | Features | Count | Examples |
| --- | --- | --- | --- |
| **P1 Totals** | Exposure and engagement over 1 / 3 / 6 / 12 months, for all paid media and for all paid media **without PulsePoint** (XPP) | 16 | `DIGITAL_TOTAL_EXPOSURE_3M`, `DIGITAL_TOTAL_XPP_ENGAGEMENT_6M` |
| **P2 Channels** | Exposure and engagement over 1 / 3 / 6 / 12 months for banner, 3rd-party email and custom placements | 24 | `DIGITAL_CH_3P_EMAIL_ENGAGEMENT_3M`, `DIGITAL_CH_CUSTOM_EXPOSURE_12M` |
| **P3 Vendor x placement** | For each of the 38 placements: exposure in the last 3 months and engagement in the last 6 months | 76 | `DIGITAL_PLC_DOXIMITY_DOCSPOT_EXPOSURE_3M`, `DIGITAL_PLC_EPOCRATES_MONOGRAPH_ENGAGEMENT_6M` |
| **P4 Engagement rates** | Engagement / exposure: all paid media (3 / 6 / 12 months), without PulsePoint (6M), and per channel (6M). NULL if no exposure; can be above 1 because one exposure can lead to several engagements | 7 | `DIGITAL_ENGAGEMENT_RATE_6M`, `DIGITAL_XPP_ENGAGEMENT_RATE_6M` |
| **P5 Recency** | Days from the cohort end to the last exposure, last engagement, last 3rd-party email engagement and last custom-placement engagement (999 if none in 12 months) | 4 | `DIGITAL_DAYS_SINCE_LAST_ENGAGEMENT` |
| **P6 Breadth** | Number of vendors (3M, 12M), number of placements (3M) and number of active months (6M, 12M) | 5 | `DIGITAL_N_VENDORS_12M`, `DIGITAL_N_ACTIVE_MONTHS_6M` |
| **P7 Trend** | Last 3 months compared with the 3 months before, as (last - prior) / (last + prior), from -1 to +1, for exposure, engagement and exposure without PulsePoint. NULL with fewer than 6 months of history | 3 | `DIGITAL_EXPOSURE_3M_VS_PRIOR_3M` |
| **IND Indication** | Paid media tagged HF, CKD or BOTH: exposure over 3 and 6 months, engagement over 6 months | 9 | `DIGITAL_IND_HF_EXPOSURE_3M`, `DIGITAL_IND_CKD_ENGAGEMENT_6M` |
| **Total** | | **144** | |

**Placements covered by the dictionary (38)**

| Channel | Placements |
| --- | --- |
| Banner (13) | PulsePoint programmatic display, Medscape, Doceree EHR, PeerDirect, OpenEvidence direct, Biopharm, Haymarket, ReachMD, ConnectiveRx, Nativo, HealthCast, MJH, LinkedIn |
| 3rd-party email (7) | Medscape email alert, PeerDirect MDFI, PeerDirect MD Minute, Haymarket, Biopharm, MJH, HealthCast |
| Custom: medical sites and apps (18) | Doximity DocNews, DocPoint, DocSpot, Announcement, FormularyOne; Medscape Brand Alert, Education (ReCAP, Fast Five Quiz, BrandSpot, XCOD), Offsite media; Epocrates Monograph, DocAlert, Search suggestion; Prescriber Point Monograph; PeerDirect web; Impiricus SMS; ReachMD; MDCalc; Haymarket; MJH |

---

## 4. Changes in preprocessing

| Preprocessing step | NBA 3.0 | NBA 3.1 | Effect |
| --- | --- | --- | --- |
| Brand filter | `= 'KERENDIA'` | `LIKE '%KERENDIA%'` (all brand values) | Recovers up to 88.5% of the data for Doceree, 86.5% for ReachMD and 67.3% for PeerDirect |
| Text cleaning | Exact match on raw names | Upper case, trimmed, repeated spaces collapsed before matching | Spelling and case variants (e.g. `Programatic_DISPLAY`) map to one placement |
| Vendor / tactic mapping | Raw values pivoted as they came | Fixed dictionary; first matching rule wins; unknown values go to an unmapped report | Stable columns; new vendors are flagged, not lost |
| Channel scope | HQ email, iRep email inside the digital block | Excluded by dictionary rules | No duplicates with the HQ email and personal-block features |
| NPI cleaning | Placeholder values (`PDRP`, `'NULL'`) counted as doctors | Only 10-digit NPIs | No fake "doctors" |
| Doctor key | NPI | NPI mapped to `PROVIDER_ID` (NBA 3.1 universe only); duplicates go to the smallest `PROVIDER_ID` | Joins directly with all NBA 3.1 features; no double counting |
| Indication | Not used | HF / CKD / BOTH / GENERAL from the brand value | New indication features |
| Time window | Calendar month, including the unfinished current month | Cohort months ending on the 17th (the cohort end day) | Windows match the cohort exactly; no information after the cohort end |
| History | Not tracked | `DIGITAL_HISTORY_MONTHS` per cohort; trend NULL when below 6 months | "No data yet" is not confused with "not exposed" |
| Missing values | Mixed | Counts 0, days since 999, rates NULL, trend NULL when history is too short | Consistent defaults across the block |
| Running totals | Included | Removed | Avoids features that just grow with time |

---

## 5. Business explanation of the features

| Feature group | Business question it answers | How the NBA model can use it |
| --- | --- | --- |
| **Totals (P1)** | How much Kerendia digital media has this doctor seen, and how often did they react? The "without PulsePoint" version shows the targeted, higher-response media. | Separates doctors reached by the broad programmatic campaign from those reached by targeted partners. |
| **Channels (P2)** | Does this doctor see Kerendia mainly through banners, 3rd-party emails or medical apps and sites? | Shows the channel mix for each doctor, so the next action can favour the channel that already works for them. |
| **Vendor x placement (P3)** | Which partner and which spot reaches this doctor (e.g. Doximity DocSpot, Epocrates Monograph, Medscape Brand Alert)? | OE's own model found its strongest digital signals at this level. It lets the model learn which placements are linked to prescribing. |
| **Engagement rates (P4)** | When this doctor is shown Kerendia content, how often do they react? | Tells "shown a lot" apart from "responds". A high rate marks a digitally responsive doctor; high exposure with a near-zero rate suggests the message is not landing. |
| **Recency (P5)** | How long ago did this doctor last see or react to Kerendia digital content? | Recent engagement is a sign of current interest and a good moment for a follow-up action. A long gap can mean the doctor has gone cold. |
| **Breadth (P6)** | Through how many partners, placements and months does this doctor meet Kerendia? | Separates a one-off contact from steady, multi-channel presence. |
| **Trend (P7)** | Is digital activity for this doctor going up or down? | A rising trend shows growing attention; a falling one can signal fatigue or the end of a campaign. |
| **Indication (IND)** | Is this doctor seeing heart-failure (HF) or kidney (CKD) messaging, or both? | Links the media to the doctor's specialty and patient mix, so the next action fits the right indication. |
| **Context: `DIGITAL_HISTORY_MONTHS`** | How much digital history exists for this cohort? | Stops the model reading "no digital data yet" (2024 cohorts) as "not exposed". |

---

## 6. Caveats and next steps

* **Short history.** MMX paid media starts in January 2025: cohorts c1 to c8 have no digital data, and 12-month windows are only complete from c20 (lookback end 17 Jan 2026) onward.
* **Sparse placements.** Several placements (e.g. LinkedIn, Nativo, HealthCast, Impiricus SMS, which has no rows after December 2025) are small or stopped. They stay in the fixed list so the schema does not change; review their usefulness after the first model run.
* **Vendor codes to confirm.** ConnectiveRx, Nativo and HealthCast vendor codes are marked "to confirm" in the dictionary.
* **Status.** Steps 1 to 7 (configuration, cohorts, universe, dictionary, MMX load and unmapped report) have been run and checked. Steps 8 to 14 (indication tag, stage table, feature build, QC and summary) are written but not yet run, so feature-level counts are not included in this document.
