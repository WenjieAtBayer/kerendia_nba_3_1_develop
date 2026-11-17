# Veeva Link to People — Data Assessment v2 (with HCP Universe and Call Plan Segment Overlap)

**Scope.** Veeva Link "Data Science File Set" (Veeva dictionary v2.0), as loaded into Snowflake (`CPH_DB_PROD.ANALYTICS_V2.ANLT_VEEVA_LINK_*`).
**Profiled.** All 17 tables, 350 columns, every row — not a sample.
**As-of.** `SCIENTIFIC_EXPERT` loaded 2025-06-25; all child tables loaded 2025-03-06; `COMMUNITY_LEADER_FOCUS_AREA` last loaded 2024-08-29.
**Purpose.** Document what data the asset contains, which tables are present, what information each holds, and how it overlaps with (a) the NBA 3.1 HCP Universe and (b) the Kerendia call-plan segments A, B, C, D (and E), and (c) what model features it supports.
**What changed from v1.** Added the time-dependent vs time-agnostic classification (Section 3), the HCP Universe overlap (Section 5), the call-plan segment overlap (Section 6), the decile distribution with segments across deciles (Section 7) and downstream activity by decile and segment, including clinical trials (Section 8). Section 9 gives a short overview of the features this data supports; the full feature design lives in `veeva_link_feature_engineering_plan.md`. Each section ends with a short summary. Deciles are shown as 1–10 only, with no High/Medium/Low grouping.

---

## 1. Sources of Veeva Link to People Data

### 1.1 What the asset is

Veeva Link is a curated expert database. Veeva employs analysts and automated pipelines to track scientific and clinical activity for individual healthcare professionals, assembling a profile per person from published literature, trial registries, congress programmes, professional bodies, and public payment disclosures.

It is **not** a prescriber database and not a claims asset. It describes *influence and activity*, not *prescribing*. The link to prescribing behaviour is made externally, through NPI.

### 1.2 Upstream sources behind each table

| Veeva table | Underlying source | Refresh |
|---|---|---|
| `SCIENTIFIC_EXPERT`, `ADDRESS` | Veeva OpenData / Network master, provider registries, institutional websites | Continuous curation |
| `PUBLICATION`, `SCIENTIFIC_EXPERT_PUBLICATION` | PubMed/MEDLINE and equivalent bibliographic indices, incl. non-English sources | Continuous |
| `CLINICAL_TRIAL`, `SCIENTIFIC_EXPERT_CLINICAL_TRIAL` | Public trial registries (ClinicalTrials.gov and international equivalents) | Continuous |
| `MEDICAL_EVENT`, `EVENT_ATTENDEE` | Congress and conference programmes, session agendas, speaker lists | Event-driven |
| `ASSOCIATION` | Society membership rosters, editorial mastheads, committee listings | Periodic |
| `PAYMENT` | **CMS Open Payments** (US Sunshine Act) and international transparency registers | Annual disclosure |
| `FOCUS_AREA`, `DIGITAL_REACH_FOCUS_AREA`, `CLINICAL_LEADER`, `INDEX` | Veeva proprietary scoring models computed over the above | Recomputed each load |
| `COMPANY_SPONSORSHIP`, `COMPANY_COLLABORATION` | Derived from trial sponsorship, event sponsorship and collaboration signals | Recomputed each load |

### 1.3 Licence footprint

Our licence covers **the Americas only** — 13 countries. Distribution of experts by country:

| Country | Experts | Share |
|---|---:|---:|
| US | 2,215,203 | 87.5% |
| Brazil | 104,617 | 4.1% |
| Canada | 89,316 | 3.5% |
| Mexico | 42,183 | 1.7% |
| Argentina | 37,048 | 1.5% |
| Chile, Colombia, Peru, Ecuador, Guatemala, Panama, El Salvador, Dominica | 43,553 | 1.7% |

Roughly 2.2M experts are US, and 1,594,381 US expert rows carry an NPI (1,567,252 distinct NPIs).

### 1.4 Table inventory and volumetrics

| Table | Rows | Distinct experts | Expert coverage | Present in warehouse |
|---|---:|---:|---:|---|
| `FOCUS_AREA` | 182,423,886 | 1,586,906 | 62.7% | Yes |
| `PAYMENT` | 108,908,302 | 1,000,117 | 39.5% | Yes |
| `CLINICAL_LEADER` | 91,060,114 | 870,837 | 34.4% | Yes |
| `DIGITAL_REACH_FOCUS_AREA` | 27,681,001 | 106,471 | 4.2% | Yes |
| `SCIENTIFIC_EXPERT_PUBLICATION` | 11,822,427 | 1,246,496 | 49.2% | Yes |
| `PUBLICATION` | 6,395,291 | — | — | Yes |
| `EVENT_ATTENDEE` | 4,917,373 | 740,879 | 29.3% | Yes |
| `COMMUNITY_LEADER_FOCUS_AREA` | 4,579,943 | 756,697 | *(deprecated)* | Yes (frozen) |
| `INDEX` | 3,991,179 | 1,715,109 | 67.7% | Yes |
| `ADDRESS` | 2,771,121 | 2,771,121 | 109.4% ⚠ | Yes |
| `SCIENTIFIC_EXPERT` | **2,531,920** | 2,531,920 | 100% | Yes |
| `SCIENTIFIC_EXPERT_CLINICAL_TRIAL` | 889,413 | 279,438 | 11.0% | Yes |
| `ASSOCIATION` | 803,819 | 362,576 | 14.3% | Yes |
| `MEDICAL_EVENT` | 677,395 | — | — | Yes |
| `COMPANY_SPONSORSHIP` | 543,811 | 192,000 | 7.6% | Yes |
| `CLINICAL_TRIAL` | 200,065 | — | — | Yes |
| `COMPANY_COLLABORATION` | **0** | 0 | **Empty** | Yes (empty) |
| `SCIENTIFIC_EXPERT_CHANGELOG` | — | — | — | **No** |
| `SCIREACH_MAPPING` | — | — | — | **No** (5-value lookup) |

### 1.5 Four findings that materially affect how this asset can be used

**① There is no history. The warehouse holds current state only.**
`IS_LATEST_FLAG = 'Y'` and `SYS_DELETE_FLAG = 0` for **100% of rows in every table**. No superseded versions are retained, so **point-in-time reconstruction of any vendor score is impossible** — we cannot know what an expert's decile was in 2023. Dated activity (publications, trials, events, payments) is unaffected.
*Action: begin archiving every monthly load now.*

**② Table vintages are inconsistent — up to 10 months apart.**
`SCIENTIFIC_EXPERT` was refreshed 2025-06-25. Every child table was last loaded 2025-03-06. `COMMUNITY_LEADER_FOCUS_AREA` has not been refreshed since 2024-08-29. Recently added experts have no activity rows and look inactive rather than new.
*Action: align the load schedule.*

**③ `COMPANY_COLLABORATION` is empty.**
The table exists with its full schema and zero rows.
*Action: confirm with Veeva whether this file is in our subscription.*

**④ `COMMUNITY_LEADER_FOCUS_AREA` is confirmed dead.**
Removed from the Veeva specification at revision 1.8, absent from the official ERD, and frozen since August 2024. Superseded by `CLINICAL_LEADER`.

### 1.6 Query traps

- **SCD-2 filter:** every query needs `IS_LATEST_FLAG = 'Y' AND COALESCE(SYS_DELETE_FLAG, 0) = 0`. `SCIENTIFIC_EXPERT` uses `COALESCE(ISDELETED, 0) = 0` instead.
- **`SYS_TENANT`:** person tables use country codes (`US`, `CA`, `BR`); dimension tables (`PUBLICATION`, `CLINICAL_TRIAL`, `MEDICAL_EVENT`) use `XX`. A blanket `SYS_TENANT = 'US'` filter silently drops every dimension row.
- **`REGEXP_LIKE` through the Spark Snowflake connector** returns 0 rows on free-text columns. Use it only on `FOCUS_NAME`; use `ILIKE` on `TITLE` / `NAME`.

> **Summary.** Veeva Link is a curated database of about 2.5M healthcare experts across the Americas (2.2M in the US), built from publications, trial registries, congress programmes, society rosters and CMS Open Payments. It tells us how influential and active an HCP is, not what they prescribe. The data is a current snapshot with no history, and the activity tables are a few months older than the expert list.

---

## 2. How the tables link

### Join keys at a glance

`SCIENTIFIC_EXPERT` is the centre table. Only the linking columns are listed.

| Table | Linking columns | Joins to |
|---|---|---|
| **`SCIENTIFIC_EXPERT`** (centre) | `SE_ID`, `NPI`, `BH_ID`, `VEEVA_ID` | `SE_ID` to every Veeva table below; `NPI` / `BH_ID` to our HCP Universe and call plan |
| `ADDRESS` | `SE_ID` | `SCIENTIFIC_EXPERT` |
| `ASSOCIATION` | `SE_ID` | `SCIENTIFIC_EXPERT` |
| `FOCUS_AREA` | `SE_ID` | `SCIENTIFIC_EXPERT` |
| `CLINICAL_LEADER` | `SE_ID` | `SCIENTIFIC_EXPERT` |
| `DIGITAL_REACH_FOCUS_AREA` | `SE_ID` | `SCIENTIFIC_EXPERT` |
| `INDEX` | `SE_ID` | `SCIENTIFIC_EXPERT` |
| `PAYMENT` | `SE_ID`, `CLINICAL_TRIAL_ID` | `SCIENTIFIC_EXPERT`; `CLINICAL_TRIAL_ID` is 98.1% null |
| `COMPANY_SPONSORSHIP` | `SE_ID` | `SCIENTIFIC_EXPERT` |
| `SCIENTIFIC_EXPERT_PUBLICATION` | `SE_ID`, `PUBLICATION_ID` | `SCIENTIFIC_EXPERT` and `PUBLICATION` |
| `PUBLICATION` | `PUBLICATION_ID` | `SCIENTIFIC_EXPERT_PUBLICATION` |
| `SCIENTIFIC_EXPERT_CLINICAL_TRIAL` | `SE_ID`, `CLINICAL_TRIAL_ID` | `SCIENTIFIC_EXPERT` and `CLINICAL_TRIAL` |
| `CLINICAL_TRIAL` | `CLINICAL_TRIAL_ID` | `SCIENTIFIC_EXPERT_CLINICAL_TRIAL` |
| `EVENT_ATTENDEE` | `SE_ID`, `MEDICAL_EVENT_ID` | `SCIENTIFIC_EXPERT` and `MEDICAL_EVENT` |
| `MEDICAL_EVENT` | `MEDICAL_EVENT_ID` | `EVENT_ATTENDEE` |

*`COMPANY_COLLABORATION` (empty) and `COMMUNITY_LEADER_FOCUS_AREA` (deprecated) also carry `SE_ID`. `PUBLICATION`, `CLINICAL_TRIAL` and `MEDICAL_EVENT` have no `SE_ID`, so they are always reached through their link table.*

### 2.1 How to explain it in one minute

1. **One expert, one profile.** Everything hangs off a single expert record (`SCIENTIFIC_EXPERT`). Every table about the expert carries the same expert key, `SE_ID`.
2. **Four groups of information.** Each group answers one question about the expert: *who they are*, *how Veeva ranks them*, *what they do*, and *who pays them*.
3. **Activity takes two steps.** One paper has many authors, one trial many investigators, one congress many speakers. So a link table records the expert's role (first author, PI, speaker), and the paper, trial or event itself is stored once in its own table.
4. **How it connects to us.** Our HCP Universe joins to Veeva on NPI (77.7% match). The call-plan segment joins to the HCP Universe on BH_ID.

| Group | Tables | Question it answers | One row is | Has an event date? |
|---|---|---|---|---|
| Expert profile | `SCIENTIFIC_EXPERT` | Who is this person (type, specialty, NPI)? | One expert | No |
| 1. Who they are | `ADDRESS`, `ASSOCIATION` | Where do they work, which bodies do they sit on? | One affiliation / one role | No |
| 2. How Veeva ranks them | `CLINICAL_LEADER`, `FOCUS_AREA`, `DIGITAL_REACH_FOCUS_AREA`, `INDEX` | How influential are they, by disease or topic? | One expert x one disease or topic (with a decile) | No (current score only) |
| 3. What they do | `PUBLICATION`, `CLINICAL_TRIAL`, `MEDICAL_EVENT` (plus their link tables) | What have they published, run or presented? | One paper / trial / event | Yes |
| 4. Industry ties | `PAYMENT`, `COMPANY_SPONSORSHIP` | Which companies pay or sponsor them? | One payment / one company link | `PAYMENT` yes (program year) |

*Not covered above: `COMPANY_COLLABORATION` (empty), `COMMUNITY_LEADER_FOCUS_AREA` (deprecated), and `SCIENTIFIC_EXPERT_CHANGELOG` and `SCIREACH_MAPPING` (part of the Veeva model but not in our warehouse).*

### 2.2 Structure in words

The model is a **hub and spoke** centred on `SCIENTIFIC_EXPERT`, keyed on `SE_ID`.

- **Nine tables attach directly** to the hub on `SE_ID`, in two clusters: scoring and ranking (`FOCUS_AREA`, `CLINICAL_LEADER`, `DIGITAL_REACH_FOCUS_AREA`, `INDEX`) and profile/commercial/identity (`ADDRESS`, `ASSOCIATION`, `PAYMENT`, `COMPANY_SPONSORSHIP`, `COMPANY_COLLABORATION`).
- **Three activity chains require two hops** through a bridge table to a dimension: events (`EVENT_ATTENDEE` → `MEDICAL_EVENT`), trials (`SCIENTIFIC_EXPERT_CLINICAL_TRIAL` → `CLINICAL_TRIAL`), publications (`SCIENTIFIC_EXPERT_PUBLICATION` → `PUBLICATION`).
- **`SCIENTIFIC_EXPERT_CHANGELOG`** is a self-referencing identity table (`SE_ID`, `MERGED_INTO_SE_ID`).
- **`SCIREACH_MAPPING`** decodes `INDEX` rows where `TYPE = 'Scientific Reach'`.

### 2.3 Verified cardinality

| Relationship | Documented | **Measured** | Note |
|---|---|---|---|
| `SCIENTIFIC_EXPERT` → `ADDRESS` | 1:1 | **1:1 confirmed** | `SE_ID` unique across all 2,771,121 rows |
| `SCIENTIFIC_EXPERT` → `FOCUS_AREA` | 1:N | 1:N, avg **115 rows/expert** | Very high fan-out |
| `SCIENTIFIC_EXPERT` → `CLINICAL_LEADER` | 1:N | 1:N, avg **105 rows/expert** | |
| `SCIENTIFIC_EXPERT` → `PAYMENT` | 1:N | 1:N, avg **109 rows/expert**, max 81,080 | Extreme skew |
| `SCIENTIFIC_EXPERT` → `INDEX` | 1:N | 1:N, avg **2.3 of 6 index types** | |
| `SE_ID` ↔ `NPI` | not stated | **near 1:1 where populated** | 1,568,886 distinct NPIs across 1,568,777 non-null rows |

**⚠ `ADDRESS` has 239,201 more rows than `SCIENTIFIC_EXPERT`** — orphan addresses, most likely a vintage artefact (March children vs June hub).

### 2.4 The external join — NPI

`SCIENTIFIC_EXPERT.NPI` is the bridge to IQVIA, NPPES and CMS. **It is 38.0% null.** NPI is a US-only identifier, and `NON_PHYSICIAN_RESEARCHER` (42.9% of experts) mostly do not hold one. `VEEVA_ID` (98.1% populated) is the fallback route into Veeva Network.

> **Summary.** Every table hangs off one expert record, keyed on `SE_ID`. Profile, scores and payments join to it directly; publications, trials and events go through a link table that records the expert's role (author, investigator, speaker). Veeva connects to our own data through NPI.

---

## 3. Time-dependent vs time-agnostic tables

**⚠ Snapshot constraint.** The warehouse holds **current state only**. The data represents a rolling ~5-year window from the export date; there is no panel of historical loads.

**Time-dependent tables** carry a date recording *when the underlying event occurred*, so activity can be placed in time within the snapshot.
**Time-agnostic tables** carry only system-load timestamps (`SYS_SRC_MODIFIED_DT`, `LOAD_ID`). They reflect Veeva's *current assessment* at the latest load.

| Table | Type | Date column | Historical view possible? |
|---|---|---|---|
| `PUBLICATION` | **Time-dependent** | `DATE` (0% null, 2020–2024) | Yes — by publication date |
| `CLINICAL_TRIAL` | **Time-dependent** | `START_DATE` (0.9% null), `END_DATE` (4.1% null, runs to 2026) | Yes — by trial start/end |
| `MEDICAL_EVENT` | **Time-dependent** | `START_DATE` (0% null), `END_DATE` (71.6% null) | Yes — by event start only |
| `PAYMENT` | **Time-dependent** | `PROGRAM_YEAR` (2013–2023), `PAYMENT_DATE` | Yes — annual, 6–18 month disclosure lag |
| `SCIENTIFIC_EXPERT` | Time-agnostic | None | No — current profile |
| `ADDRESS` | Time-agnostic | None | No — current affiliation |
| `ASSOCIATION` | Time-agnostic | None | No — `PAST_POSITION` is 'N' for 100% of rows |
| `COMPANY_SPONSORSHIP` | Time-agnostic | None | No — current sponsorship |
| `FOCUS_AREA` | Time-agnostic | None | No — recomputed each load |
| `CLINICAL_LEADER` | Time-agnostic | None | No — recomputed each load |
| `DIGITAL_REACH_FOCUS_AREA` | Time-agnostic | None | No — recomputed each load |
| `INDEX` | Time-agnostic | None | No — six pre-computed scores |

**Bridge tables** (`SCIENTIFIC_EXPERT_PUBLICATION`, `SCIENTIFIC_EXPERT_CLINICAL_TRIAL`, `EVENT_ATTENDEE`) have no event date themselves, but they link to time-dependent dimensions, so the joined result is dated.

> **Summary.** Publications, trials, events and payments carry real dates, so we can see when activity happened. Veeva's scores and profile fields carry no date: they are today's view and cannot be rolled back to an earlier month.

---

## 4. Column-level EDA

### 4.1 Expert profile (`SCIENTIFIC_EXPERT`, 2,531,920 rows)

**`EXPERT_TYPE`** — 15 values, 0% null:

| Value | Count | Share |
|---|---:|---:|
| NON_PHYSICIAN_RESEARCHER | 1,087,042 | 42.9% |
| PHYSICIAN | 943,351 | 37.3% |
| NURSE_PRACTITIONER | 191,250 | 7.6% |
| PHYSICIAN_ASSISTANT | 88,732 | 3.5% |
| MENTAL_HEALTH_THERAPIST | 67,508 | 2.7% |
| NURSE | 60,374 | 2.4% |
| PHARMACIST | 35,541 | 1.4% |
| OPTOMETRIST / PHYSICAL_THERAPIST / DIETICIAN / TECHNICIAN and 5 others | 58,122 | 2.3% |

Fewer than half the Veeva universe can prescribe. *These are UPPER_SNAKE values; the Veeva specification documents title-case values and does not list `NON_PHYSICIAN_RESEARCHER`, so our ingestion is remapping.*

**`SPECIALTY_1`** — **61.0% null**, 431 distinct. Top: Internal Medicine (90,418), Family Medicine (85,423), Pediatrics (46,824), Emergency Medicine (40,447), Cardiology (23,967). `SPECIALTY_2` 92.2% null; `SPECIALTY_3` 99.1% null.

**`DEGREE_1`** — 29.9% null, 890 distinct. MD (692,520), PhD (266,480), DO (73,668), PA-C (62,512), CNP (55,605).

**`JOB_TITLE`** — 33.6% null; top values are professions (Physician 697,106, Nurse Practitioner 111,791, Physician Assistant 83,273), not seniority titles. Largely duplicates `EXPERT_TYPE`.

**`EMERGING_EXPERT`** — 19,255 experts flagged `Y` (0.76%).

**Empty fields:** `SLN` and `VERIFIED_PROFILE` 100% null by design; `DELETED_DATE` 100% null; `ORIGINAL_*` name fields ≥99.9% null.

### 4.2 Scoring tables — disease and drug-class authority

| | `CLINICAL_LEADER` | `FOCUS_AREA` | `DIGITAL_REACH_FOCUS_AREA` |
|---|---|---|---|
| Rows | 91,060,114 | 182,423,886 | 27,681,001 |
| Distinct experts | 870,837 (34.4%) | 1,586,906 (62.7%) | 106,471 (4.2%) |
| Distinct `FOCUS_NAME` | **704** | **18,499** | **17,093** |
| Taxonomy style | Curated clinical: diseases and drug classes | MeSH-like research topics | MeSH-like |
| What it scores | Patient volume | Scientific output | Digital/online influence |
| Decile columns | `SE_DECILE` | `FOCUS_DECILE`, `SE_DECILE` | `SE_DECILE` only |
| Decile null rate | **89.1%** ⚠ | 0% | 0% |
| `FOCUS_TYPE` column | No (`TYPE` = disease / drug_class) | Yes — 14 values | **No** |

**`CLINICAL_LEADER`** — clean clinical vocabulary: `Essential Hypertension` (657,328 rows), `Type 2 Diabetes Mellitus` (641,764), plus drug classes. `TYPE`: `drug_class` 51,650,796 (56.7%) / `disease` 39,409,318 (43.3%). Only ~9.9M of 91M rows carry a decile.

**`FOCUS_AREA`** — dominated by generic research concepts (`Quality of Health Care` 1,156,917, `Diagnosis` 1,101,217, `Efficacy / Effectiveness` 992,426, `Adult` 848,990). `FOCUS_TYPE`: Diseases (41.8M), Diagnosis and Treatment (40.9M), Biology (29.1M), Real World Data (14.8M), Demographics (11.7M), Other (10.9M), Research (10.1M), Drugs (9.6M) and others.

**`DIGITAL_REACH_FOCUS_AREA`** — similar generic topics (`Health Care Quality, Access, and Evaluation` 88,811, `Quality of Health Care` 88,089, `COVID-19 / SARS-CoV-2` 81,265). 88% of rows sit at decile 1.

**Decile direction — 10 = top** for all three tables (row counts decline monotonically from 1 to 10):

| Decile | `FOCUS_AREA` | `CLINICAL_LEADER` | `DIGITAL_REACH` |
|---|---:|---:|---:|
| 1 | 78,059,921 | 1,663,379 | 24,369,244 |
| 5 | 10,691,486 | 1,042,115 | 342,029 |
| 10 | 1,072,194 | 195,276 | 128,934 |

**`FOCUS_AREA` vs `DIGITAL_REACH_FOCUS_AREA`.** Both rate each expert topic by topic, using a similar MeSH-like topic list. They differ in the activity the rating is based on:

- **`FOCUS_AREA`** rates **scientific output**: how much the expert publishes, runs trials and presents on a topic. It shows *who is producing research* on a subject.
- **`DIGITAL_REACH_FOCUS_AREA`** rates **online influence** on a topic: the reach of the expert's digital presence. It shows *who is being heard online* about a subject. The exact channels measured are not documented in the dictionary; confirm with Veeva.

| | `FOCUS_AREA` | `DIGITAL_REACH_FOCUS_AREA` |
|---|---|---|
| What it measures | Scientific output by topic | Online influence by topic |
| Rows | 182,423,886 | 27,681,001 |
| Experts covered | 1,586,906 (62.7%) | 106,471 (4.2%) |
| Distinct topics | 18,499 | 17,093 |
| Decile columns | `FOCUS_DECILE` and `SE_DECILE` | `SE_DECILE` only |
| Topic grouping (`FOCUS_TYPE`) | Yes, 14 groups | No |
| Decile spread | Spread across 1–10, weighted to the low end | 88% of rows at decile 1, so close to on/off |
| HCP Universe HCPs with a Kerendia-relevant decile (Section 5.3) | 29,033 (12.7%) | 4,710 (2.1%) |

Digital reach covers a much smaller, more visible group of experts, and within it almost everyone sits at decile 1, so in practice it mainly indicates whether an expert has any digital presence on a topic. Both differ from `CLINICAL_LEADER`, which ranks experts by patient volume on a curated disease and drug-class list.

### 4.3 `INDEX` — six pre-computed influence scores

3,991,179 rows across 1,715,109 experts (avg 2.3 of 6 types per expert).

| `TYPE` | Rows | Scale |
|---|---:|---|
| Publication Index | 1,477,549 | 0–10 |
| Scientific Reach | 1,027,597 | **0–4** |
| Event Index | 714,023 | 0–10 |
| Clinical Trial Index | 346,381 | 0–10 |
| Digital Reach | 283,705 | 0–10 |
| Guideline Index | 141,924 | 0–10 |

`UPPER_LIMIT` confirms two scales (10 and 4). Scientific Reach decodes to n/a / local / regional / national / global. `VALUE` is heavily skewed: 1 (2,740,688), 2 (572,496), 10 (9,968).

### 4.4 Clinical trials

**`ROLE`** (889,413 rows) — Investigator 535,122 (60.2%), **Principal Investigator 347,763 (39.1%)**, Sub-Investigator 6,528 (0.7%).

**`PHASE`** (200,065 trials) — `None Specified` **134,991 (67.5%)**, Phase II 21,592, Phase I 12,795, Phase III 11,066, Phase IV 8,406, Phase I/II 6,333, Early Phase I 2,603, Phase II/III 2,279. The unphased two thirds are largely investigator-initiated and observational studies.

**Dates** — `START_DATE` 0.9% null, `END_DATE` 4.1% null, end dates run into 2026. **No condition, sponsor or NCT field**: indication can only be identified from `NAME`.

### 4.5 Congresses and events

**`EVENT_ATTENDEE.POSITION`** (4,917,373 rows):

| Position | Count | Share |
|---|---:|---:|
| Speaker | 2,602,211 | 52.9% |
| Poster Presenter | 721,927 | 14.7% |
| Chairperson | 509,376 | 10.4% |
| Organizer | 478,255 | 9.7% |
| Panelist | 467,038 | 9.5% |
| Moderator | 114,206 | 2.3% |
| Award Winner | 23,918 | 0.5% |
| Participant | 442 | 0.01% |

**`TALK_TITLE`** — 18.0% null, 2,780,079 distinct, but top values are generic session labels (`Introduction` 15,034, `Panel Discussion` 11,955, `Session 1` 10,699, `Welcome` 7,027).

**⚠ `MEDICAL_EVENT.EVENT_TYPE` is corrupted** — 51 values instead of 3–6, including bare dates and French event names. Column shift from the pipe-delimited source (~0.3% of rows). Legitimate values: Workshop (531,503), Congress (144,767), Board Meeting (543), Webinar (390), Committee Meeting (144). `END_DATE` 71.6% null.

### 4.6 Publications

**`AUTHORSHIP_POSITION`** (11,822,427 rows) — Coauthor 8,043,106 (68.0%), **Last Author 2,014,941 (17.0%)**, First Author 1,764,380 (14.9%).

**`PUBLICATION_TYPE`** — 98 distinct, **multilingual**: Journal Article (2,720,437), Research Support Non-U.S. Gov't (674,720), 会議録 / Meeting Minutes (629,419), Review (447,699), Case Reports (258,101), 解説 / Commentary (163,789), Editorial (123,093). `DATE` is 0% null, 2020–2024.

### 4.7 Payments (`PAYMENT`, 108,908,302 rows)

**`PROGRAM_YEAR`** — 2013 to **2023 only** (2023: 13,293,393 · 2022: 12,530,255 · 2021: 11,095,470). No 2024/2025 data (CMS annual cycle).

**`NATURE_OF_PAYMENT`** — 23 values, 8.2% null: Food and Beverage 88,824,342 (81.6%), Travel and Lodging 4,761,716 (4.4%), Compensation for services incl. faculty/speaker 2,302,184 (2.1%), Education 1,913,356 (1.8%), Consulting Fee 1,417,646 (1.3%), others ~1.5M (1.4%).

**`TYPE`** — General 100,025,684 (91.8%), Research 8,844,861 (8.1%), Ownership 37,757 (0.03%).

**`COMPANY_NAME`** — 2,776 distinct, normalised: AbbVie (6,289,686), Janssen (5,148,158), Pfizer (4,947,268), Novo Nordisk (4,681,042), AstraZeneca (4,385,139), Amgen, GSK, Lilly, MSD, Novartis.

**`AMOUNT`** — extreme right skew (USD 25.00 appears 386,983 times; 1500.00 203,745; 3000.00 144,113). **`CLINICAL_TRIAL_ID`** — 98.1% null; the 9,217 populated values are NCT identifiers, the only NCT numbers in the file set. **`CURRENCY`** — 99.97% USD.

### 4.8 Associations and sponsorship

**`ASSOCIATION_TYPE`** (803,819 rows) — Scientific Association (253,062), Professional Association (250,892), Editorial Board (164,773), Foundation (55,742), Patient Association (43,686), Regulatory/Health Authority (24,215), Internet Portal (9,264), Industry Association (2,163), Ministry (22).

**`POSITION_TYPE`** — Member (345,824), Board Member (220,757), Editor (172,330), Head of (64,907), Reviewer (1).

**⚠ Data issues:** `PAST_POSITION` = 'N' for 100% of rows; `JOB_TITLE` is an exact duplicate of `POSITION_TYPE`; `ASSOCIATION_NAME` top values are committee labels (`Board of Directors` 32,516, `Fellows` 25,197) rather than organisations.

**`COMPANY_SPONSORSHIP`** (543,811 rows, 192,000 experts) — `SCORE` 1–5: 2 (209,077), 1 (189,015), 3 (68,911), 5 (39,564), 4 (37,244). `HAS_SPONSORED_CLINICAL_TRIAL` true for 96%; `HAS_SPONSORED_EVENT` true for 6.6%.

### 4.9 Affiliation and geography (`ADDRESS`)

**`AFFILIATION`** — 0% null, 522,336 distinct (University of California 19,814, The University of Texas System 11,693, Stanford University 11,000). **`DEPARTMENT`** — 41.5% null, academic skew. **`ZIP`** — text with leading zeros intact.

> **Summary.** The activity tables are clean and detailed: authorship position, PI role, trial phase, speaker role, payment type and paying company are all usable. The scores are thinner: `CLINICAL_LEADER` has a decile on only about one row in ten, and digital reach covers just 4% of experts. A few fields have quality issues (event type, association history) and are flagged.

---

## 5. Overlap with the NBA 3.1 HCP Universe

### 5.1 Method

- **HCP Universe:** `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/HCP_Universe_without_call_hcps` (criteria C1–C4), 294,727 IQVIA `PROVIDER_ID`s.
- **Crosswalk:** `kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING` (`PROVIDER_ID` → `NPI_NUMBER`, `BH_ID`). Each provider maps to at most one NPI and one BH_ID.
- **Veeva side:** `SCIENTIFIC_EXPERT`, `SYS_TENANT = 'US'`, `ISDELETED = 0`, NPI not null. Matched on NPI.

### 5.2 Funnel

| Step | HCPs | % of universe |
|---|---:|---:|
| HCP Universe | 294,727 | 100% |
| With a valid NPI in the crosswalk | 294,553 | 99.9% |
| With a BH_ID in the crosswalk | 294,578 | 99.9% |
| **Matched to a Veeva profile** | **228,932** | **77.7%** |
| Not in Veeva | 65,795 | 22.3% |

The 228,932 matched providers correspond to 228,930 distinct `SE_ID`s (two providers share an SE_ID). They represent 14.4% of the 1,594,381 US Veeva experts with an NPI.

### 5.3 Scoring-table coverage within the overlap

**In scope = any focus name relevant to Kerendia.** That covers the indications (T2D, T1D, CKD, heart failure, hypertension), Kerendia and the MRA class, the main competitor and co-therapy classes (SGLT2 inhibitors, GLP-1 / incretins, DPP-4 inhibitors, other T2D drugs, ACE inhibitors / ARBs) and hyperkalemia. All deciles 1–10 count, with no threshold. US experts only, latest rows only.

- `CLINICAL_LEADER`: max `SE_DECILE` over the 17 focus names below, **both `TYPE = 'disease'` and `TYPE = 'drug_class'`**.
- `FOCUS_AREA`: max `FOCUS_DECILE` over the 147 focus names below, all `FOCUS_TYPE`s.
- `DIGITAL_REACH_FOCUS_AREA`: max `SE_DECILE` over the 135 focus names below.
- **Best decile** = the highest of the three.

#### Focus names used — `CLINICAL_LEADER` (17)

| `TYPE` | Theme | `FOCUS_NAME` | HCPs in overlap with a decile |
|---|---|---|---:|
| disease | Hypertension | Essential Hypertension | 53,032 |
| disease | Hypertension | Hypertensive Crisis | 7,740 |
| disease | T2D | Type 2 Diabetes Mellitus | 46,817 |
| disease | T1D | Type 1 Diabetes Mellitus | 13,340 |
| disease | CKD | Chronic Kidney Disease (CKD) | 22,551 |
| disease | Heart failure | Heart Failure | 26,213 |
| disease | Heart failure | Cardiomyopathy (CM) | 11,802 |
| disease | Heart failure | Cardiomyopathies | 0 |
| drug_class | Kerendia / MRA | Mineralocorticoid Receptor Antagonist | 28,107 |
| drug_class | Kerendia / MRA | Aldosterone Receptor Antagonist | 6,856 |
| drug_class | Kerendia / MRA | Potassium Sparing Diuretic | 24,940 |
| drug_class | SGLT2 inhibitors | SGLT2 Inhibitors | 39,167 |
| drug_class | GLP-1 / incretin | Glucagon Receptor Agonist | 33,029 |
| drug_class | DPP-4 inhibitors | DPP4 Inhibitors | 30,435 |
| drug_class | ACE inhibitors / ARBs | Angiotensin-Converting Enzyme (ACE) Inhibitors | 61,250 |
| drug_class | ACE inhibitors / ARBs | Angiotensin Receptor Antagonist | 36,356 |
| drug_class | Hyperkalemia | Potassium Binder | 4,797 |

*`CLINICAL_LEADER` has no finerenone or diabetic-kidney-disease value. "Glucagon Receptor Agonist" is Veeva's class label and is taken as the GLP-1 class. Excluded as not Kerendia-relevant: obesity, AF, CAD, AKI, pulmonary hypertension, kidney cancer, other kidney diseases, statins, CCBs, diuretics, insulin.*

#### Focus names used — `FOCUS_AREA` (147) and `DIGITAL_REACH_FOCUS_AREA` (135)

The two tables share the same topic list. `FOCUS_TYPE` of the 147 `FOCUS_AREA` names: Drugs 92, Diseases 39, Diagnosis and Treatment 9, Biology 7 (`DIGITAL_REACH_FOCUS_AREA` has no `FOCUS_TYPE`). Names marked * appear only in `FOCUS_AREA`; names marked † only in `DIGITAL_REACH_FOCUS_AREA`.

| Theme | Focus names |
|---|---|
| Kerendia / MRA (10) | Mineralocorticoid Receptor Antagonists (Aldosterone Antagonists); Steroidal Mineralocorticoid Receptor Antagonists; Spironolactone; Non-Steroidal Mineralocorticoid Receptor Antagonists; Eplerenone; Finerenone (KERENDIA®); Hydrochlorothiazide/Spironolactone*; Hydrochlorothiazide / Spironolactone; Balcinrenone/Dapagliflozin; Balcinrenone / Dapagliflozin* |
| SGLT2 inhibitors (31) | SGLT2 Inhibitors; Empagliflozin (JARDIANCE®); Canagliflozin (INVOKANA®); Sodium-Glucose Cotransporter-2 (SGLT2); SGLT1 Inhibitors; Sotagliflozin (ZYNQUISTA® / INPEFA®); Ertugliflozin (STEGLATRO®); Dapagliflozin/Metformin (XIGDUO® / EBYMECT®)*; Canagliflozin/Metformin (INVOKAMET® / VOKANAMET®); Empagliflozin/Metformin (SYNJARDY®); Bexagliflozin (BRENZAVVY®); Luseogliflozin (LUSEFI®); Empagliflozin/Linagliptin (GLYXAMBI®); Tofogliflozin (DEBERZA® / APLEWAY®)*; Ipragliflozin (SUGLAT®); Empagliflozin / Metformin (SYNJARDY®); Dapagliflozin/Saxagliptin (QTERN®); Dapagliflozin / Metformin (XIGDUO® / EBYMECT®); Empagliflozin/BI690517; Ertugliflozin/Sitagliptin (STEGLUJAN®)*; Canagliflozin / Metformin (INVOKAMET® / VOKANAMET®); Ertugliflozin/Metformin (SEGLUROMET®)*; Empagliflozin / Linagliptin (GLYXAMBI®); Ertugliflozin / Sitagliptin (STEGLUJAN®); Dapagliflozin / Saxagliptin (QTERN®); Empagliflozin / BI690517*; Zibotentan/Dapagliflozin; Ertugliflozin / Metformin (SEGLUROMET®)*; Empagliflozin/Linagliptin/Metformin (TRIJARDY®)*; Empagliflozin / Linagliptin / Metformin (TRIJARDY®)†; Zibotentan / Dapagliflozin† |
| GLP-1 / incretin (29) | Incretin Mimetics; Incretin; Glucagon-Like Peptide 1 (GLP-1); Glucagon-Like Peptide 1 (GLP-1) Receptor Agonists; Glucagon-Like Peptide-1 Receptor (GLP1R); Liraglutide (VICTOZA® / SAXENDA®); Semaglutide; Dual-GLP-1RA/GIPR Agonists; Tirzepatide (MOUNJARO® / ZEPBOUND®); Injectable Semaglutide for T2D (OZEMPIC®); Exenatide; Dulaglutide (TRULICITY®); Exenatide Once-Weekly (BYDUREON®); Injectable Semaglutide for Obesity (WEGOVY®); Triple GLP-1R/GIPR/GCGR Agonists; Oral Semaglutide (RYBELSUS®); Dual GLP-1RA/GCGR Agonists; Exenatide Twice-Daily (BYETTA®); Insulin Degludec/Liraglutide (XULTOPHY®); Semaglutide (OZEMPIC® / RYBELSUS® / WEGOVY®); Compounded Glucagon-Like Peptide 1 (GLP-1) Receptor Agonists; Dual-GLP-1RA/GIPR Antagonists; Insulin Degludec / Liraglutide (XULTOPHY®); Fixed-Dose Semaglutide/Cagrilintide (CagriSema); Ultra-Long-Acting Glucagon-Like Peptide 1 (GLP-1) Receptor Agonists; Insulin Icodec/Semaglutide (IcoSema); Fixed-Dose Semaglutide / Cagrilintide (CagriSema); Insulin Icodec / Semaglutide (IcoSema); Dual GLP-1RA/Amylin Agonists |
| DPP-4 inhibitors (19) | DPP4 Inhibitors; Sitagliptin; Saxagliptin; Linagliptin; Alogliptin (NESINA® / VIPIDIA®); Sitagliptin/Metformin; Vildagliptin; Saxagliptin/Metformin; Sitagliptin / Metformin; Vildagliptin/Metformin*; Saxagliptin / Metformin; Vildagliptin / Metformin; Linagliptin/Metformin*; Alogliptin/Pioglitazone (OSENI® / INCRESYNC®); Linagliptin / Metformin; Retagliptin*; Alogliptin/Metformin (KAZANO® / VIPDOMET®)*; Alogliptin / Pioglitazone (OSENI® / INCRESYNC®)†; Alogliptin / Metformin (KAZANO® / VIPDOMET®)† |
| Other T2D drugs (8) | Antidiabetic Drugs; Metformin; Pioglitazone/Metformin*; Glyburide/Metformin; Pioglitazone / Metformin; Glipizide/Metformin*; Glyburide / Metformin; Glipizide / Metformin |
| ACE inhibitors / ARBs (2) | Angiotensin-Converting Enzyme (ACE) Inhibitors; Angiotensin II Receptor Blockers (ARBs) |
| Hyperkalemia (1) | Hyperkalemia |
| Hypertension (8) | Hypertension (High Blood Pressure); Antihypertensive Agents; Treatment-Resistant Hypertension (RHTN); Essential Hypertension; Hypertensive Crisis; Hypertensive Heart Failure (HHF); Uncontrolled/Resistant Hypertension with HFpEF; Uncontrolled/Resistant Hypertension with CKD Stage 3/4* |
| CKD (20) | Kidney Diseases (Nephrology); Renal Insufficiency; Chronic Kidney Disease (CKD); Kidney Failure; Glomerular Filtration Rate; End Stage Renal Disease (ESRD); Estimated Glomerular Filtration Rate (eGFR); Proteinuria; Chronic Kidney Disease (CKD) and Atherosclerotic Cardiovascular Disease (ASCVD); Diabetic Kidney Disease; Albuminuria; Anemia in Chronic Kidney Disease (CKD); Reduction of Proteinuria; Cardio-Renal Syndrome; Microalbuminuria; Macroalbuminuria (High Level Albuminuria); Stage 3 Chronic Kidney Disease (CKD); Cardiorenal Protection (Cardiorenal Benefit); Stage 4 Chronic Kidney Disease (CKD); Chronic Kidney Diseases of Uncertain Etiology |
| Heart failure (17) | Heart Failure; Cardiomyopathy (CM); Ejection Fraction (EF); Chronic Heart Failure; Ventricular Dysfunction; Congestive Heart Failure; Left Ventricular Dysfunction; Heart Failure with reduced Ejection Fraction (HFrEF, Systolic HF); Heart Failure with preserved Ejection Fraction (HFpEF, Diastolic HF); New York Heart Association (NYHA) Classification of Heart Failure; Acute Heart Failure; Right Ventricular Dysfunction; Acute Decompensated Heart Failure (ADHF); Cardiomyopathies; Heart Failure and Systemic Inflammation; Subclinical Heart Failure; Heart Failure with Mid-Range Ejection Fraction (HFmEF) |
| T2D (1) | Type 2 Diabetes Mellitus |
| T1D (1) | Type 1 Diabetes Mellitus |
| Diabetes (general) (2) | Diabetes Mellitus; Diabetes Complications |
| Cardiometabolic (2) | Cardiometabolic; Cardiometabolic Risk Factors |

*Excluded on purpose: pulmonary, intracranial, portal and pregnancy-related hypertension; gestational, paediatric and experimental diabetes; diabetic eye, nerve and vessel complications; kidney cancer, transplant, acute kidney injury and other non-CKD kidney diseases; hypertrophic cardiomyopathy; GLP-2; COVID / ACE2 topics; general RAAS topics (`Renin-Angiotensin-Aldosterone System (RAAS) Inhibitors`, `Renin-Angiotensin System`) and ARNIs, so the theme is strictly ACE inhibitors and ARBs.*

#### Coverage within the overlap (228,932 HCPs)

| Source | HCPs with an in-scope decile | % of overlap |
|---|---:|---:|
| `CLINICAL_LEADER` (any type) | 134,930 | 58.9% |
|  – `TYPE = 'disease'` | 84,378 | 36.9% |
|  – `TYPE = 'drug_class'` | 110,110 | 48.1% |
| `FOCUS_AREA` | 29,033 | 12.7% |
| `DIGITAL_REACH_FOCUS_AREA` | 4,710 | 2.1% |
| **Any table (best decile)** | **147,489** | **64.4%** |
| No in-scope decile | 81,443 | 35.6% |

50,552 HCPs are scored in `CLINICAL_LEADER` on a drug class only, with no disease decile.

**Coverage by theme (HCPs with a decile on at least one focus name in the theme)**

| Theme | `CLINICAL_LEADER` | `FOCUS_AREA` | `DIGITAL_REACH` | Any table | % of overlap |
|---|---:|---:|---:|---:|---:|
| ACE inhibitors / ARBs | 75,528 | 2,852 | 1,611 | 78,883 | 34.5% |
| Hypertension | 55,884 | 13,687 | 3,326 | 68,116 | 29.8% |
| T2D | 46,817 | 6,593 | 1,206 | 52,315 | 22.9% |
| Kerendia / MRA | 48,562 | 1,405 | 874 | 50,031 | 21.9% |
| SGLT2 inhibitors | 39,167 | 3,268 | 1,961 | 42,701 | 18.7% |
| Heart failure | 27,853 | 16,054 | 3,708 | 38,325 | 16.7% |
| GLP-1 / incretin | 33,029 | 3,144 | 1,425 | 36,118 | 15.8% |
| CKD | 22,551 | 14,036 | 2,885 | 34,154 | 14.9% |
| DPP-4 inhibitors | 30,435 | 723 | 185 | 31,152 | 13.6% |
| Diabetes (general) | 0 | 14,701 | 3,004 | 16,012 | 7.0% |
| T1D | 13,340 | 1,942 | 471 | 14,605 | 6.4% |
| Other T2D drugs | 0 | 6,693 | 2,526 | 8,340 | 3.6% |
| Hyperkalemia | 4,797 | 993 | 624 | 6,122 | 2.7% |
| Cardiometabolic | 0 | 1,970 | 842 | 2,469 | 1.1% |

**Change from the earlier definition.** The KOL EDA notebook definition gave 79,578 HCPs (34.8%) with any decile: `CLINICAL_LEADER` 65,909, `FOCUS_AREA` 20,953, `DIGITAL_REACH` 3,981. It was narrower for two reasons: (1) it used `TYPE = 'disease'` only and a short curated list, which did not pick up `CLINICAL_LEADER`'s CKD value `Chronic Kidney Disease (CKD)`; (2) Snowflake `REGEXP_LIKE` matches the whole string, so an indication regex without leading and trailing `.*` matches only focus names that equal a keyword exactly. The new lists use `.*pattern.*` and then curate the matches by hand. Sections 6–10 use the new definition.

> **Summary.** 77.7% of our HCP Universe (228,932 of 294,727 HCPs) has a Veeva profile, matched on NPI. Counting every Kerendia-relevant disease and drug class, 64.4% of those matched HCPs also have a Veeva influence decile, mostly from `CLINICAL_LEADER`. The most common are ACE inhibitors / ARBs, hypertension, T2D and the MRA class.

---

## 6. Overlap with Kerendia call-plan segments

### 6.1 Segment source

The segment table is the one used for criterion C4 in HCP Universe creation: Snowflake `PHCDW.PHCDW_TARGETING.CP_KER_HCP`, filtered to `FF IN ('CR1','CR2','CR4','CR5')` and `PRODUCT_1` or `PRODUCT_2` = KERENDIA. The segment is `NOTE_2`, joined on `BAYER_ID` = `BH_ID`. The current call plan runs **2026-10-01 to 2026-12-31**, and each BH_ID has exactly one segment.

### 6.2 HCP Universe → Veeva coverage by segment

| Segment | HCP Universe | In Veeva | Veeva coverage | Not in Veeva |
|---|---:|---:|---:|---:|
| A | 11,367 | 10,401 | 91.5% | 966 |
| B | 21,257 | 18,556 | 87.3% | 2,701 |
| C | 17,073 | 13,434 | 78.7% | 3,639 |
| D | 19,429 | 15,460 | 79.6% | 3,969 |
| E | 9,687 | 7,698 | 79.5% | 1,989 |
| **A–E (targets)** | **78,813** | **65,549** | **83.2%** | **13,264** |
| Non-target | 215,914 | 163,383 | 75.7% | 52,531 |
| **Total** | **294,727** | **228,932** | **77.7%** | **65,795** |

High-potential segments (A, B) have the best Veeva coverage.

### 6.3 Scoring-table coverage by segment (in-Veeva HCPs)

| Segment | In Veeva | `CLINICAL_LEADER` | `FOCUS_AREA` | `DIGITAL_REACH` | Any decile |
|---|---:|---:|---:|---:|---:|
| A | 10,401 | 9,382 (90.2%) | 2,238 (21.5%) | 329 (3.2%) | 9,622 (92.5%) |
| B | 18,556 | 15,319 (82.6%) | 2,945 (15.9%) | 405 (2.2%) | 15,871 (85.5%) |
| C | 13,434 | 9,201 (68.5%) | 2,304 (17.2%) | 368 (2.7%) | 9,901 (73.7%) |
| D | 15,460 | 10,334 (66.8%) | 3,352 (21.7%) | 600 (3.9%) | 11,457 (74.1%) |
| E | 7,698 | 4,416 (57.4%) | 1,091 (14.2%) | 192 (2.5%) | 4,944 (64.2%) |
| Non-target | 163,383 | 86,278 (52.8%) | 17,103 (10.5%) | 2,816 (1.7%) | 95,694 (58.6%) |
| **Total** | **228,932** | **134,930 (58.9%)** | **29,033 (12.7%)** | **4,710 (2.1%)** | **147,489 (64.4%)** |

*Deciles use the Kerendia-relevant focus names in Section 5.3.*

### 6.4 Profile of in-Veeva HCPs by segment

| Segment | Physician | Nurse Practitioner | Physician Assistant | Other | `SPECIALTY_1` null | Top Veeva specialties | Emerging experts |
|---|---:|---:|---:|---:|---:|---|---:|
| A | 80.7% | 12.5% | 4.4% | 2.5% | 19.3% | Nephrology, Internal Med, Family Med, Endocrinology | 57 |
| B | 73.8% | 16.4% | 5.7% | 4.1% | 26.0% | Internal Med, Family Med, Cardiology, Endocrinology | 72 |
| C | 68.1% | 18.6% | 6.7% | 6.6% | 31.5% | Nephrology, Family Med, Internal Med, Cardiology | 82 |
| D | 66.2% | 19.2% | 7.0% | 7.5% | 33.4% | Cardiology, Internal Med, Family Med, Interventional Cardiology | 105 |
| E | 62.9% | 20.7% | 7.8% | 8.7% | 36.8% | Family Med, Internal Med, Cardiology, Interventional Cardiology | 38 |
| Non-target | 62.0% | 21.2% | 7.9% | 8.8% | 37.6% | Family Med, Internal Med, Cardiology, Interventional Cardiology | 669 |

> **Summary.** Call-plan targets are better covered than the rest of the universe: 83.2% of segments A–E are in Veeva, rising to 91.5% for segment A. The high-potential segments A and B are also the most likely to carry a Kerendia-relevant Veeva decile (86–93% vs 59% for Non-target HCPs).

---

## 7. Decile distribution

All tables in this section cover the 228,932 HCP Universe providers matched to Veeva.

**What a decile means here.** Veeva ranks each expert against other experts *within each disease or topic* and assigns a decile from 1 to 10, where **10 is the highest rank** (most influential) and 1 the lowest. The groups are not equal in size: most experts sit at the low deciles. Because an expert gets a separate decile for every disease or topic, we keep only the focus names relevant to Kerendia (**in-scope**, full list in Section 5.3): T2D, T1D, CKD, heart failure and hypertension, Kerendia and the MRA class, SGLT2 inhibitors, GLP-1 / incretins, DPP-4 inhibitors, ACE inhibitors / ARBs and hyperkalemia, covering both diseases and drug classes. For each HCP we then take the highest decile across these focus names and across the three scoring tables; this is the **best decile**. HCPs with no decile on any in-scope focus name are shown as **Unscored**.

### 7.1 Decile distribution by scoring table

| Decile | Best decile | `CLINICAL_LEADER` | `FOCUS_AREA` | `DIGITAL_REACH` |
|---|---:|---:|---:|---:|
| 1 | 14,767 | 12,053 | 8,153 | 3,022 |
| 2 | 15,019 | 13,492 | 4,896 | 316 |
| 3 | 16,107 | 14,785 | 3,762 | 232 |
| 4 | 16,510 | 15,375 | 3,008 | 205 |
| 5 | 16,120 | 14,996 | 2,498 | 183 |
| 6 | 16,312 | 15,219 | 2,038 | 152 |
| 7 | 15,578 | 14,445 | 1,775 | 138 |
| 8 | 14,596 | 13,684 | 1,255 | 164 |
| 9 | 13,351 | 12,365 | 1,097 | 155 |
| 10 | 9,129 | 8,516 | 551 | 143 |
| Unscored | 81,443 | 94,002 | 199,899 | 224,222 |
| **Total** | **228,932** | **228,932** | **228,932** | **228,932** |

The best decile is driven mainly by `CLINICAL_LEADER`, which sets it for 88.6% of scored HCPs. Because the best decile is the maximum over many focus names, the distribution is fairly even across deciles 1–9 (13–17K HCPs each), with 9,129 HCPs at decile 10. `FOCUS_AREA` is concentrated at the low deciles (551 HCPs at decile 10), and `DIGITAL_REACH` sits at decile 1 for 64.2% of its scored HCPs.

### 7.2 Segments across deciles — HCP counts (best decile)

| Segment | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | Unscored | Total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 234 | 273 | 389 | 508 | 821 | 1,022 | 1,215 | 1,487 | 1,792 | 1,881 | 779 | 10,401 |
| B | 730 | 859 | 1,116 | 1,253 | 1,380 | 1,633 | 2,025 | 2,272 | 2,515 | 2,088 | 2,685 | 18,556 |
| C | 725 | 777 | 930 | 1,067 | 1,201 | 1,287 | 1,174 | 1,163 | 1,018 | 559 | 3,533 | 13,434 |
| D | 897 | 1,057 | 1,205 | 1,340 | 1,322 | 1,349 | 1,291 | 1,143 | 1,114 | 739 | 4,003 | 15,460 |
| E | 512 | 516 | 576 | 563 | 536 | 583 | 562 | 435 | 388 | 273 | 2,754 | 7,698 |
| Non-target | 11,669 | 11,537 | 11,891 | 11,779 | 10,860 | 10,438 | 9,311 | 8,096 | 6,524 | 3,589 | 67,689 | 163,383 |
| **Total** | **14,767** | **15,019** | **16,107** | **16,510** | **16,120** | **16,312** | **15,578** | **14,596** | **13,351** | **9,129** | **81,443** | **228,932** |

### 7.3 How each segment spreads across deciles (row %, scored HCPs only)

| Segment | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | Scored HCPs | Mean decile | Median |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 2.4 | 2.8 | 4.0 | 5.3 | 8.5 | 10.6 | 12.6 | 15.5 | 18.6 | 19.5 | 9,622 | 7.23 | 8 |
| B | 4.6 | 5.4 | 7.0 | 7.9 | 8.7 | 10.3 | 12.8 | 14.3 | 15.8 | 13.2 | 15,871 | 6.51 | 7 |
| C | 7.3 | 7.8 | 9.4 | 10.8 | 12.1 | 13.0 | 11.9 | 11.7 | 10.3 | 5.6 | 9,901 | 5.59 | 6 |
| D | 7.8 | 9.2 | 10.5 | 11.7 | 11.5 | 11.8 | 11.3 | 10.0 | 9.7 | 6.5 | 11,457 | 5.44 | 5 |
| E | 10.4 | 10.4 | 11.7 | 11.4 | 10.8 | 11.8 | 11.4 | 8.8 | 7.8 | 5.5 | 4,944 | 5.12 | 5 |
| Non-target | 12.2 | 12.1 | 12.4 | 12.3 | 11.3 | 10.9 | 9.7 | 8.5 | 6.8 | 3.8 | 95,694 | 4.80 | 5 |
| **Total** | **10.0** | **10.2** | **10.9** | **11.2** | **10.9** | **11.1** | **10.6** | **9.9** | **9.1** | **6.2** | **147,489** | **5.25** | **5** |

Including unscored HCPs as a column (row % of all in-Veeva HCPs), the unscored share is A 7.5%, B 14.5%, C 26.3%, D 25.9%, E 35.8%, Non-target 41.4%.

### 7.4 Segment mix within each decile (column %)

| Segment | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | Unscored |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 1.6 | 1.8 | 2.4 | 3.1 | 5.1 | 6.3 | 7.8 | 10.2 | 13.4 | 20.6 | 1.0 |
| B | 4.9 | 5.7 | 6.9 | 7.6 | 8.6 | 10.0 | 13.0 | 15.6 | 18.8 | 22.9 | 3.3 |
| C | 4.9 | 5.2 | 5.8 | 6.5 | 7.5 | 7.9 | 7.5 | 8.0 | 7.6 | 6.1 | 4.3 |
| D | 6.1 | 7.0 | 7.5 | 8.1 | 8.2 | 8.3 | 8.3 | 7.8 | 8.3 | 8.1 | 4.9 |
| E | 3.5 | 3.4 | 3.6 | 3.4 | 3.3 | 3.6 | 3.6 | 3.0 | 2.9 | 3.0 | 3.4 |
| Non-target | 79.0 | 76.8 | 73.8 | 71.3 | 67.4 | 64.0 | 59.8 | 55.5 | 48.9 | 39.3 | 83.1 |

**Reading this:** Veeva deciles and call-plan segments agree clearly. A and B (high potential) make up 7–8% of deciles 1–2 but 32% of decile 9 and 44% of decile 10. C, D and E stay roughly flat across deciles (C 5–8%, D 6–8%, E about 3%). Even so, Non-target HCPs are 49% of decile 9 and 39% of decile 10: Veeva-ranked authorities in Kerendia-relevant diseases and drug classes who are in the HCP Universe but not on the call plan.

> **Summary.** Veeva's rankings broadly agree with our call plan: segments A and B are over-represented at the top deciles. But Veeva also identifies 18,209 highly ranked HCPs (deciles 8–10) who are in our universe and not on the call plan, 10,113 of them at deciles 9–10.

---

## 8. Downstream activity by decile and segment

Activity is counted per HCP across **all topics** over the full snapshot (publications 2020–2024, trials to 2026, events, payments 2013–2023). It is not restricted to the in-scope focus names. The medians are 0 for publications, trials and events in every group, so active % and mean are shown instead.

### 8.1 By best decile

| Decile | HCPs | Pubs active % | Pubs mean | Senior-author active % | Trials active % | Trials mean | PI active % | Events active % | Events mean | Podium active % | Paid % | Median total paid (payees, USD) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 14,767 | 24.6 | 0.88 | 11.9 | 5.8 | 0.11 | 2.4 | 14.5 | 0.42 | 10.0 | 75.3 | 1,035 |
| 2 | 15,019 | 21.6 | 0.92 | 12.6 | 5.1 | 0.11 | 2.3 | 14.1 | 0.42 | 9.4 | 78.7 | 1,200 |
| 3 | 16,107 | 20.6 | 1.18 | 13.1 | 5.7 | 0.14 | 2.8 | 14.6 | 0.58 | 10.9 | 81.3 | 1,364 |
| 4 | 16,510 | 19.3 | 1.26 | 12.7 | 6.8 | 0.17 | 3.5 | 14.5 | 0.57 | 11.2 | 84.2 | 1,583 |
| 5 | 16,120 | 18.8 | 1.64 | 12.5 | 8.3 | 0.27 | 4.7 | 14.1 | 0.74 | 11.4 | 86.7 | 1,922 |
| 6 | 16,312 | 18.9 | 2.01 | 12.6 | 9.6 | 0.29 | 5.6 | 14.7 | 0.88 | 12.4 | 88.8 | 2,342 |
| 7 | 15,578 | 18.6 | 2.36 | 12.4 | 11.2 | 0.40 | 6.7 | 14.5 | 1.02 | 12.3 | 89.9 | 2,907 |
| 8 | 14,596 | 17.8 | 2.97 | 12.1 | 11.9 | 0.52 | 7.9 | 14.7 | 1.28 | 12.8 | 91.9 | 3,695 |
| 9 | 13,351 | 18.9 | 4.54 | 12.5 | 14.5 | 0.80 | 10.7 | 14.8 | 1.67 | 13.3 | 93.6 | 5,365 |
| 10 | 9,129 | 19.5 | 8.31 | 12.6 | 16.1 | 1.09 | 11.5 | 15.5 | 2.80 | 14.0 | 94.4 | 8,510 |
| Unscored | 81,443 | 8.9 | 0.20 | 3.9 | 1.9 | 0.03 | 0.7 | 6.7 | 0.15 | 4.4 | 63.8 | 608 |
| **All** | **228,932** | **16.0** | **1.57** | **9.4** | **6.5** | **0.24** | **3.8** | **11.8** | **0.67** | **9.1** | **78.2** | **1,504** |

Totals across the overlap: 358,601 publications, 54,673 clinical trials (26,006 as PI), 152,510 medical events, 38,305,022 payment records.

**Gradient:** from decile 1 to decile 10, the share running trials rises from 5.8% to 16.1%, PI involvement 4.8× (2.4% → 11.5%) and mean trials 9.9× (0.11 → 1.09). The share receiving payments rises from 75.3% to 94.4% and median total payments from USD 1,035 to 8,510. Mean publications (0.88 → 8.31) and mean events (0.42 → 2.80) also rise, but the **share** of HCPs who publish (17.8–24.6%) or attend events (14.1–15.5%) is flat across scored deciles: the rise in means comes from a smaller group of very prolific HCPs at the top deciles.

### 8.2 By call-plan segment

| Segment | HCPs | Pubs active % | Pubs mean | Senior-author active % | Trials active % | Trials mean | PI active % | Events active % | Events mean | Podium active % | Paid % | Payment records mean | Median total paid (payees, USD) | Paying companies mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 10,401 | 19.1 | 1.56 | 11.1 | 10.8 | 0.45 | 6.9 | 14.8 | 0.75 | 11.1 | 91.2 | 451.5 | 5,886 | 27.8 |
| B | 18,556 | 17.0 | 1.35 | 9.6 | 7.7 | 0.27 | 4.5 | 12.1 | 0.62 | 9.1 | 87.0 | 270.3 | 2,922 | 20.8 |
| C | 13,434 | 18.4 | 1.99 | 11.4 | 8.0 | 0.31 | 4.6 | 14.2 | 0.79 | 10.5 | 82.1 | 251.7 | 2,756 | 19.7 |
| D | 15,460 | 24.2 | 2.53 | 14.6 | 10.1 | 0.35 | 5.9 | 17.7 | 1.04 | 13.7 | 83.1 | 199.9 | 2,622 | 17.7 |
| E | 7,698 | 17.9 | 1.82 | 10.7 | 7.2 | 0.29 | 4.6 | 13.7 | 0.92 | 10.4 | 81.7 | 236.3 | 2,532 | 19.1 |
| Non-target | 163,383 | 14.6 | 1.45 | 8.6 | 5.6 | 0.20 | 3.2 | 10.7 | 0.61 | 8.3 | 75.4 | 124.3 | 1,054 | 12.6 |

**Reading this:** Segment A leads on clinical trials (10.8% active, 6.9% PI) and industry payments (median USD 5,886, 27.8 paying companies on average). Segment D (lower-potential non-writers, cardiology-heavy) is the most academically active: highest publication (24.2%) and event (17.7%) participation. Non-target HCPs are the least active on every channel.

### 8.3 Clinical trials — segment × decile

**% of HCPs with any clinical trial**

| Segment | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | Unscored | All |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 3.4 | 4.8 | 4.1 | 6.3 | 6.5 | 8.3 | 9.9 | 12.6 | 15.7 | 16.5 | 2.1 | 10.8 |
| B | 4.0 | 3.5 | 4.3 | 5.1 | 7.2 | 8.1 | 10.3 | 9.4 | 11.6 | 12.9 | 1.8 | 7.7 |
| C | 5.5 | 3.0 | 4.4 | 5.7 | 7.3 | 10.4 | 12.3 | 12.7 | 19.5 | 22.7 | 1.8 | 8.0 |
| D | 5.6 | 6.7 | 7.2 | 9.9 | 12.1 | 15.3 | 16.0 | 17.3 | 20.6 | 20.8 | 1.7 | 10.1 |
| E | 5.5 | 5.4 | 7.6 | 7.5 | 9.3 | 12.5 | 13.7 | 13.8 | 17.3 | 13.2 | 1.9 | 7.2 |
| Non-target | 6.0 | 5.2 | 5.8 | 6.7 | 8.1 | 9.0 | 10.7 | 11.5 | 13.2 | 15.9 | 1.9 | 5.6 |

**% of HCPs who are Principal Investigator on any trial**

| Segment | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | Unscored | All |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 0.9 | 1.8 | 2.3 | 3.0 | 3.0 | 3.9 | 5.3 | 8.1 | 11.9 | 11.9 | 0.0 | 6.9 |
| B | 1.5 | 1.4 | 1.9 | 2.2 | 3.3 | 4.6 | 5.7 | 5.7 | 8.1 | 8.6 | 0.5 | 4.5 |
| C | 2.5 | 0.9 | 1.6 | 1.9 | 3.7 | 5.0 | 7.2 | 8.6 | 14.1 | 15.9 | 0.8 | 4.6 |
| D | 2.1 | 2.6 | 3.2 | 4.4 | 6.9 | 8.2 | 9.4 | 12.1 | 14.7 | 15.6 | 0.6 | 5.9 |
| E | 3.1 | 2.1 | 3.5 | 5.3 | 5.2 | 8.7 | 9.6 | 9.4 | 13.7 | 11.4 | 0.7 | 4.6 |
| Non-target | 2.4 | 2.5 | 2.9 | 3.6 | 4.8 | 5.5 | 6.5 | 7.8 | 9.9 | 11.5 | 0.7 | 3.2 |

**Mean clinical trials per HCP**

| Segment | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | Unscored |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 0.08 | 0.09 | 0.09 | 0.13 | 0.15 | 0.19 | 0.27 | 0.46 | 0.74 | 0.98 | 0.02 |
| B | 0.12 | 0.07 | 0.07 | 0.10 | 0.18 | 0.20 | 0.34 | 0.32 | 0.46 | 0.66 | 0.03 |
| C | 0.10 | 0.05 | 0.09 | 0.13 | 0.15 | 0.28 | 0.38 | 0.53 | 1.16 | 1.66 | 0.03 |
| D | 0.09 | 0.13 | 0.14 | 0.19 | 0.32 | 0.40 | 0.49 | 0.74 | 1.07 | 1.40 | 0.02 |
| E | 0.14 | 0.10 | 0.20 | 0.20 | 0.30 | 0.47 | 0.70 | 0.43 | 1.09 | 1.16 | 0.04 |
| Non-target | 0.11 | 0.12 | 0.14 | 0.18 | 0.29 | 0.29 | 0.40 | 0.56 | 0.83 | 1.25 | 0.03 |

*The smallest segment × decile cell is 234 HCPs (segment A, decile 1); decile 10 cells range from 273 (E) to 3,589 (Non-target).*

Within every segment, trial and PI involvement rise broadly with decile, so the Veeva decile adds separation that the call-plan segment alone does not give. In segment A, 3.4% of decile-1 HCPs run trials against 16.5% at decile 10.

### 8.4 Publications and events — segment × decile (% active)

**% with any publication**

| Segment | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | Unscored | All |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 26.1 | 23.1 | 22.1 | 21.9 | 18.6 | 19.6 | 18.9 | 19.2 | 18.4 | 20.5 | 9.9 | 19.1 |
| B | 26.6 | 23.1 | 20.8 | 19.1 | 17.1 | 19.5 | 19.1 | 15.4 | 17.1 | 14.8 | 9.5 | 17.0 |
| C | 24.6 | 20.3 | 22.3 | 21.2 | 20.4 | 20.6 | 19.3 | 19.0 | 22.9 | 26.5 | 10.3 | 18.4 |
| D | 33.7 | 29.8 | 29.2 | 28.9 | 27.5 | 29.4 | 28.7 | 25.6 | 29.0 | 25.2 | 11.3 | 24.2 |
| E | 25.0 | 28.7 | 28.1 | 22.4 | 23.9 | 21.4 | 18.0 | 19.8 | 20.4 | 17.6 | 9.0 | 17.9 |
| Non-target | 23.8 | 20.4 | 19.2 | 17.9 | 17.5 | 17.1 | 17.0 | 16.8 | 17.3 | 19.5 | 8.6 | 14.6 |

**% with any medical event**

| Segment | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | Unscored | All |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 17.9 | 18.3 | 18.5 | 15.4 | 12.9 | 15.5 | 14.0 | 15.7 | 14.3 | 15.3 | 10.8 | 14.8 |
| B | 16.0 | 14.0 | 13.1 | 13.6 | 12.2 | 13.9 | 13.1 | 13.1 | 12.0 | 11.9 | 6.7 | 12.1 |
| C | 15.9 | 14.8 | 15.4 | 15.7 | 16.3 | 15.7 | 15.0 | 16.8 | 18.2 | 20.6 | 8.5 | 14.2 |
| D | 20.4 | 19.5 | 19.8 | 20.2 | 20.3 | 22.8 | 22.0 | 20.8 | 22.0 | 18.1 | 9.1 | 17.7 |
| E | 15.0 | 21.7 | 19.3 | 18.7 | 16.6 | 17.2 | 16.0 | 14.9 | 18.0 | 15.4 | 7.1 | 13.7 |
| Non-target | 13.8 | 13.1 | 13.9 | 13.6 | 13.2 | 13.4 | 13.7 | 13.8 | 14.1 | 16.4 | 6.4 | 10.7 |

The share of HCPs who publish or attend events does not rise with decile. In segments A, B, D and E the share who publish is higher at decile 1 than at decile 10. The deciles come mainly from `CLINICAL_LEADER` (patient volume, now including drug classes), so they track clinical-trial involvement and industry payments rather than scientific output. The largest contrast on every channel is scored vs unscored HCPs.

> **Summary.** Higher-decile HCPs run more trials, are more often principal investigators and receive more industry payments, so the deciles reflect real clinical activity. The share who publish or speak at congresses is about the same at every decile; the gap there is between scored and unscored HCPs. Within every call-plan segment the decile still separates HCPs by trial involvement, which means Veeva adds information the call plan does not already carry.

---

## 9. From data to features — how Veeva Link helps the model

The NBA 3.1 model predicts HCP-level NBRx from claims, which tell us *what an HCP prescribes*. Veeva Link adds *how engaged and influential the HCP is*, a signal claims do not contain. Features are joined onto the claims HCP Universe on NPI, so every HCP keeps a row whether or not Veeva covers them.

### 9.1 Feature families

| Feature family | Built from | Examples | Why it helps the model |
|---|---|---|---|
| Coverage flags | `SCIENTIFIC_EXPERT`, scoring tables | Has a Veeva profile; has an in-scope decile | Being tracked and ranked by Veeva marks a more engaged HCP; keeps "unscored" separate from "low" |
| Influence rankings | `CLINICAL_LEADER`, `FOCUS_AREA`, `DIGITAL_REACH_FOCUS_AREA`, `INDEX` | Best in-scope decile, decile per indication, publication / trial / event index | Ranks HCPs by disease authority and separates HCPs within the same segment (Section 8.3) |
| Clinical-trial experience | `SCIENTIFIC_EXPERT_CLINICAL_TRIAL`, `CLINICAL_TRIAL` | Any trial, PI role, highest phase, trials naming finerenone, MRAs or SGLT2 inhibitors | Hands-on experience with Kerendia's class and competitors is a likely driver of adoption (to be tested in the model) |
| Scientific and congress activity | `SCIENTIFIC_EXPERT_PUBLICATION`, `PUBLICATION`, `EVENT_ATTENDEE`, `MEDICAL_EVENT` | Publication count, senior authorship, speaker roles, months since last activity | Captures peer influence and thought leadership |
| Industry relationships | `PAYMENT`, `COMPANY_SPONSORSHIP` | Total paid, number of paying companies, Bayer and competitor payments, speaker and consulting fees | Openness to industry engagement and existing competitor ties |
| Profile | `SCIENTIFIC_EXPERT`, `ADDRESS`, `ASSOCIATION` | Expert type, specialty, academic affiliation, society and editorial roles | Context on practice setting and seniority |

### 9.2 How this helps the model and the NBA

1. **A new dimension.** Influence and engagement are not visible in claims, so they can explain NBRx differences that prescribing history alone cannot.
2. **Finer targeting within segments.** HCPs in the same call-plan segment differ widely by decile and trial involvement (Section 8.3).
3. **New opportunities.** 18,209 Non-target HCPs rank at deciles 8–10 (10,113 at deciles 9–10) and can be reviewed for targeting.
4. **Better actions.** Activity type points to the right channel: congress speakers to peer-to-peer and speaker programmes, trial investigators to clinical-evidence messaging.

### 9.3 Cautions

- **Snapshot only.** Scores and profile fields reflect today's view. Using them to explain past months risks look-ahead bias, so dated activity features (trials, publications, events, payments) are the safest. Archiving each monthly load would remove this limit.
- **Missing is not zero.** 22.3% of the universe has no Veeva match and 35.6% of matched HCPs have no in-scope decile. These should be treated as their own category.
- **Skewed activity.** Most HCPs have no publications, trials or events (median 0), so flags, logs or bins work better than raw counts.

The full feature list, logic and data-quality controls are in `veeva_link_feature_engineering_plan.md`.

> **Summary.** Claims tell us what an HCP prescribes; Veeva tells us how influential and engaged they are. Adding Veeva features (rankings, trial experience, congress and publication activity, industry ties) gives the model a signal it does not have today, sharpens targeting within each call-plan segment and highlights influential HCPs outside the call plan.

---

## 10. Summary of findings

1. **Coverage:** 77.7% of the HCP Universe (228,932 of 294,727) has a Veeva profile, rising to 83.2% for call-plan targets A–E and 91.5% for segment A.
2. **Scoring coverage:** 64.4% of matched HCPs have a Kerendia-relevant decile (diseases and drug classes, Section 5.3), and `CLINICAL_LEADER` supplies most of it (58.9% vs 12.7% `FOCUS_AREA` and 2.1% `DIGITAL_REACH`).
3. **Segments align with deciles:** A and B have the highest mean decile (7.23, 6.51) and lowest unscored share (7.5%, 14.5%). They make up 32% of decile 9 and 44% of decile 10, against 7–8% of deciles 1–2.
4. **Untargeted authorities exist:** 18,209 Non-target HCPs sit at deciles 8–10 (8,096 + 6,524 + 3,589), 10,113 of them at deciles 9–10.
5. **Clinical activity rises with decile:** trial and PI involvement increase from decile 1 to 10, both overall and within each segment, and industry payments rise with decile overall; the share who publish or attend events is flat across scored deciles. Unscored HCPs are far less active: 8.9% publish (vs 17.8–24.6% across scored deciles), 1.9% run trials (vs 5.1–16.1%) and 6.7% attend events (vs 14.1–15.5%).
6. **Segment-specific activity:** A leads on trials and industry payments; D leads on publications and congress participation.

## 11. Open data issues

| # | Issue | Owner |
|---|---|---|
| 1 | No SCD-2 history retained — begin archiving every monthly load | Data Engineering |
| 2 | Table vintages misaligned (hub June 2025 vs children March 2025) | Data Engineering |
| 3 | `COMPANY_COLLABORATION` empty — confirm subscription | Vendor Management |
| 4 | `SCIENTIFIC_EXPERT_CHANGELOG` and `SCIREACH_MAPPING` not in the warehouse | Data Engineering |
| 5 | Pipe-delimiter column shift in `MEDICAL_EVENT.EVENT_TYPE` | Data Engineering |
| 6 | Retire `COMMUNITY_LEADER_FOCUS_AREA` | Analytics |
| 7 | 239,201 orphan `ADDRESS` rows | Analytics |
| 8 | `EXPERT_TYPE` values remapped vs the Veeva specification | Data Engineering |
| 9 | 65,795 HCP Universe providers (22.3%) have no Veeva match — try `VEEVA_ID` / Veeva Network NPI recovery | Analytics |
