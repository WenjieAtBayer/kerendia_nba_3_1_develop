# Veeva Link to People — Data Assessment for HCP-Level NBRx Modelling

**Scope.** Veeva Link "Data Science File Set" (Veeva dictionary v2.0), as loaded into our warehouse.
**Profiled.** All 17 tables, 350 columns, every row — not a sample.
**As-of.** `SCIENTIFIC_EXPERT` loaded 2025-06-25; all child tables loaded 2025-03-06; `COMMUNITY_LEADER_FOCUS_AREA` last loaded 2024-08-29.
**Purpose.** Establish what this asset contains, how it links together, and which features it can support for an HCP-month NBRx forecast in Type 1 Diabetes, Type 2 Diabetes and Hypertension.

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

For a US NBRx model, roughly 2.2M experts are in footprint.

### 1.4 Volumetrics

| Table | Rows | Distinct experts | Expert coverage |
|---|---:|---:|---:|
| `FOCUS_AREA` | 182,423,886 | 1,586,906 | 62.7% |
| `PAYMENT` | 108,908,302 | 1,000,117 | 39.5% |
| `CLINICAL_LEADER` | 91,060,114 | 870,837 | 34.4% |
| `DIGITAL_REACH_FOCUS_AREA` | 27,681,001 | 106,471 | 4.2% |
| `SCIENTIFIC_EXPERT_PUBLICATION` | 11,822,427 | 1,246,496 | 49.2% |
| `PUBLICATION` | 6,395,291 | — | — |
| `EVENT_ATTENDEE` | 4,917,373 | 740,879 | 29.3% |
| `COMMUNITY_LEADER_FOCUS_AREA` | 4,579,943 | 756,697 | *(deprecated)* |
| `INDEX` | 3,991,179 | 1,715,109 | 67.7% |
| `ADDRESS` | 2,771,121 | 2,771,121 | 109.4% ⚠ |
| `SCIENTIFIC_EXPERT` | **2,531,920** | 2,531,920 | 100% |
| `SCIENTIFIC_EXPERT_CLINICAL_TRIAL` | 889,413 | 279,438 | 11.0% |
| `ASSOCIATION` | 803,819 | 362,576 | 14.3% |
| `MEDICAL_EVENT` | 677,395 | — | — |
| `COMPANY_SPONSORSHIP` | 543,811 | 192,000 | 7.6% |
| `CLINICAL_TRIAL` | 200,065 | — | — |
| `COMPANY_COLLABORATION` | **0** | 0 | **Empty** |

### 1.5 Four findings that materially affect how this asset can be used

**① There is no history. The warehouse holds current state only.**
`IS_LATEST_FLAG = 'Y'` and `SYS_DELETE_FLAG = 0` for **100% of rows in every table**. No superseded versions are retained. This means **point-in-time reconstruction of any vendor score is impossible** from what we hold today — we cannot know what an expert's decile was in 2023. Features built on dated activity (publications, trials, events, payments) are unaffected and remain fully usable. Scores and deciles can only be used as static attributes, or point-in-time from the date we begin archiving.
*Action: begin archiving every monthly load now. Each month of delay is a month of panel history permanently lost.*

**② Table vintages are inconsistent — up to 10 months apart.**
`SCIENTIFIC_EXPERT` was refreshed 2025-06-25. Every child table was last loaded 2025-03-06. `COMMUNITY_LEADER_FOCUS_AREA` has not been refreshed since 2024-08-29. Joining the June hub to March children means recently added experts have no activity rows and will look inactive rather than new.
*Action: align the load schedule, and until then, restrict analysis to experts present at the oldest relevant vintage.*

**③ `COMPANY_COLLABORATION` is empty.**
The table exists with its full schema and zero rows. This was expected to be a primary source of competitor-relationship signal without the CMS disclosure lag. It is unavailable.
*Action: confirm with Veeva whether this file is in our subscription.*

**④ `COMMUNITY_LEADER_FOCUS_AREA` is confirmed dead.**
Removed from the Veeva specification at revision 1.8, absent from the official ERD, and empirically frozen since August 2024 while every other table has refreshed since. Superseded by `CLINICAL_LEADER`.
*Action: retire from the pipeline; migrate any dependent logic to `CLINICAL_LEADER`.*

---

## 2. ER diagram — how the tables link

![Veeva Link data model v2.0](1793362173998_image.png)

*Keep the image file alongside this document for the diagram to render.*

### 2.1 Structure in words

The model is a **hub and spoke** centred on `SCIENTIFIC_EXPERT`, keyed on `SE_ID`.

- **Nine tables attach directly** to the hub on `SE_ID` alone, in two clusters: scoring and ranking (`FOCUS_AREA`, `CLINICAL_LEADER`, `DIGITAL_REACH_FOCUS_AREA`, `INDEX`) and profile/commercial/identity (`ADDRESS`, `ASSOCIATION`, `PAYMENT`, `COMPANY_SPONSORSHIP`, `COMPANY_COLLABORATION`).
- **Three activity chains require two hops**, through a bridge table to a dimension: events via `EVENT_ATTENDEE` → `MEDICAL_EVENT`; trials via `SCIENTIFIC_EXPERT_CLINICAL_TRIAL` → `CLINICAL_TRIAL`; publications via `SCIENTIFIC_EXPERT_PUBLICATION` → `PUBLICATION`. Neither dimension can be reached directly from the hub.
- **`SCIENTIFIC_EXPERT_CHANGELOG`** is a self-referencing identity table, carrying both `SE_ID` and `MERGED_INTO_SE_ID`.
- **`SCIREACH_MAPPING`** is a value lookup, not an expert child; it decodes `INDEX` rows where `TYPE = 'Scientific Reach'`.

### 2.2 Verified cardinality

| Relationship | Documented | **Measured** | Note |
|---|---|---|---|
| `SCIENTIFIC_EXPERT` → `ADDRESS` | 1:1 | **1:1 confirmed** | `SE_ID` unique across all 2,771,121 rows |
| `SCIENTIFIC_EXPERT` → `FOCUS_AREA` | 1:N | 1:N, avg **115 rows/expert** | Very high fan-out; aggregate before joining |
| `SCIENTIFIC_EXPERT` → `CLINICAL_LEADER` | 1:N | 1:N, avg **105 rows/expert** | Same caution |
| `SCIENTIFIC_EXPERT` → `PAYMENT` | 1:N | 1:N, avg **109 rows/expert**, max 81,080 | Extreme skew |
| `SCIENTIFIC_EXPERT` → `INDEX` | 1:N | 1:N, avg **2.3 of 6 index types** | Most experts have few indices, not all six |
| `SE_ID` ↔ `NPI` | not stated | **1:1 where populated** | 1,568,886 distinct NPIs across 1,568,777 non-null rows |

**⚠ `ADDRESS` has 239,201 more rows than `SCIENTIFIC_EXPERT`.** Since `SE_ID` is unique in `ADDRESS`, these are orphan addresses with no matching expert — most likely a vintage artefact (March children vs June hub). Quantify before any join; they will silently disappear in an inner join and appear as nulls in a left join from the hub.

### 2.3 The external join — NPI to claims

`SCIENTIFIC_EXPERT.NPI` is the bridge to IQVIA LAAD, NPPES and CMS. **It is 38.0% null.** Where populated it is effectively 1:1 with `SE_ID`.

Coverage is not random — it tracks profession and geography:

- US experts: 87.5% of the base; NPI is a US-only identifier, so non-US experts cannot have one.
- `NON_PHYSICIAN_RESEARCHER` is the **largest** expert category at 1,087,042 (42.9%), and most do not hold an NPI or prescribe.
- `VEEVA_ID` is populated at **98.1%** and is the better fallback route into Veeva Network to recover a missing NPI.

**The claims universe must be the spine, not Veeva.** Veeva covers ~1.57M NPIs against a US prescriber universe several times larger. Left-join Veeva onto the claims population, and carry `has_veeva_profile` as an explicit feature.

---

## 3. EDA — columns that matter for feature creation

### 3.1 Expert profile (`SCIENTIFIC_EXPERT`, 2,531,920 rows)

**`EXPERT_TYPE`** — 15 values, 0% null. The single most important segmentation field:

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

**Implication:** fewer than half the Veeva universe can prescribe at all. NPs and PAs (11.1% combined) do prescribe and manage substantial routine T2D and HTN care. Filtering to prescriber-capable types roughly halves the population before any other criterion.
*Note: these are UPPER_SNAKE values; the Veeva specification documents title-case values and does not list `NON_PHYSICIAN_RESEARCHER`. Our ingestion is remapping — worth tracing.*

**`SPECIALTY_1`** — **61.0% null**, 431 distinct values. Far sparser than expected. Top: Internal Medicine (90,418), Family Medicine (85,423), Pediatrics (46,824), Emergency Medicine (40,447), Cardiology (23,967). `SPECIALTY_2` is 92.2% null; `SPECIALTY_3` is 99.1% null.
*Implication: specialty cannot be an inclusion filter. Backfill from NPPES taxonomy (available via the NPI join) and from `ADDRESS.DEPARTMENT`.*

**`DEGREE_1`** — 29.9% null, 890 distinct. MD (692,520), PhD (266,480), DO (73,668), PA-C (62,512), CNP (55,605). Usable as a credential signal.

**`JOB_TITLE`** — 33.6% null, but the top values are *professions* rather than seniority titles: Physician (697,106), Nurse Practitioner (111,791), Physician Assistant (83,273). **A "leadership title" feature will not work on this field** — it largely duplicates `EXPERT_TYPE`.

**`EMERGING_EXPERT`** — 19,255 experts flagged `Y` (0.76%). Small but precisely the cohort worth early engagement.

**Dead fields:** `SLN` and `VERIFIED_PROFILE` are 100% null by design (removed/deprecated in the Veeva spec). `DELETED_DATE` 100% null. All `ORIGINAL_*` name fields ≥99.9% null in an Americas licence.

### 3.2 Disease and drug-class authority

Three scoring tables with **completely different taxonomies**. This distinction drives the whole indication-scoping approach.

| | `CLINICAL_LEADER` | `FOCUS_AREA` | `DIGITAL_REACH_FOCUS_AREA` |
|---|---|---|---|
| Rows | 91,060,114 | 182,423,886 | 27,681,001 |
| Distinct experts | 870,837 (34.4%) | 1,586,906 (62.7%) | 106,471 (4.2%) |
| Distinct `FOCUS_NAME` | **704** | **18,499** | **17,093** |
| Taxonomy style | Curated clinical: diseases and drug classes | MeSH-like research topics | MeSH-like (similar to FOCUS_AREA) |
| Scores | Patient volume | Scientific output | Digital/online influence |
| Decile null rate | **89.1%** ⚠ | 0% | 0% |
| Decile distribution | Spread across 1–10 | Spread across 1–10 | 88% at decile 1 |

**`CLINICAL_LEADER.FOCUS_NAME`** — a clean, usable clinical vocabulary. In-scope entries confirmed present:
- `Essential Hypertension` — 657,328 rows
- `Type 2 Diabetes Mellitus` — 641,764 rows
- plus drug classes such as `Glucocorticoid Receptor Agonist` (725,245), `Nonsteroidal Anti-Inflammatory Drugs (NSAIDs)` (669,955)

**`CLINICAL_LEADER.TYPE`** — `drug_class` 51,650,796 (56.7%) / `disease` 39,409,318 (43.3%). The drug-class rows are the closest thing in this asset to a direct NBRx analogue.

**⚠ `CLINICAL_LEADER.SE_DECILE` is 89.1% null** — only ~9.9M of 91M rows carry a decile. Any feature built on it will be sparse and must handle missingness explicitly.

**`FOCUS_AREA.FOCUS_NAME`** is dominated by generic research concepts — `Quality of Health Care` (1,156,917), `Diagnosis` (1,101,217), `Efficacy / Effectiveness` (992,426), `Adult` (848,990). It is a topic index, not a disease list, and is a poor primary indication filter.

**`DIGITAL_REACH_FOCUS_AREA.FOCUS_NAME`** — 17,093 distinct values, similarly dominated by generic MeSH-like research concepts: `Health Care Quality, Access, and Evaluation` (88,811), `Quality of Health Care` (88,089), `Health Care Evaluation Mechanisms` (86,694), `Health` (85,981), `Diagnosis` (85,347), `Infections (Infectious Diseases)` (83,723), `COVID-19 / SARS-CoV-2` (81,265). The taxonomy overlaps heavily with `FOCUS_AREA` and is equally poor as an indication filter.

**`FOCUS_AREA.FOCUS_TYPE`** — 14 values, multi-valued in places: Diseases (41.8M), Diagnosis and Treatment (40.9M), Biology (29.1M), Real World Data (14.8M), Demographics (11.7M), Other (10.9M), Research (10.1M), Drugs (9.6M), Technology (4.7M), Organization (4.3M), Symptoms (3.4M), Medical Devices and 2 others.

**`DIGITAL_REACH_FOCUS_AREA` has no `FOCUS_TYPE` column** and no `FOCUS_DECILE` — only `SE_DECILE` and `FOCUS_NAME`. This means the category-level filtering available through `FOCUS_AREA.FOCUS_TYPE` (e.g. restricting to `Diseases` or `Drugs`) is not possible in the digital-reach table. The only usable fields for indication scoping are `FOCUS_NAME` keyword matching and `SE_DECILE` ranking.

**Decile direction — now empirically confirmed.** All three decile fields decline monotonically from 1 to 10, i.e. decile 10 is the smallest and most selective group. Combined with the Veeva dictionary stating 10 is highest for `FOCUS_AREA`, **10 = top** holds across all of them:

| Decile | `FOCUS_AREA` | `CLINICAL_LEADER` | `DIGITAL_REACH` |
|---|---:|---:|---:|
| 1 | 78,059,921 | 1,663,379 | 24,369,244 |
| 5 | 10,691,486 | 1,042,115 | 342,029 |
| 10 | 1,072,194 | 195,276 | 128,934 |

**`DIGITAL_REACH_FOCUS_AREA`** covers only **106,471 experts (4.2%)**, and 88% of its rows sit at decile 1. Thin; treat as a niche signal.

#### `FOCUS_AREA` vs `DIGITAL_REACH_FOCUS_AREA` — same schema, different signal

Both tables share the same structure (keyed on `SE_ID`, with `FOCUS_NAME`, `FOCUS_DECILE`, `SE_DECILE`) but score orthogonal dimensions of expert influence:

| Dimension | `FOCUS_AREA` | `DIGITAL_REACH_FOCUS_AREA` |
|---|---|---|
| What it scores | Scientific output (publications, trials, research) | Digital/online influence (web mentions, social media) |
| Rows | 182,423,886 | 27,681,001 |
| Expert coverage | 62.7% (1,586,906) | 4.2% (106,471) |
| Avg rows per expert | 115 | 260 |
| Distinct `FOCUS_NAME` | 18,499 | 17,093 |
| Top `FOCUS_NAME` | Quality of Health Care (1.16M), Diagnosis (1.10M), Efficacy / Effectiveness (992K), Adult (849K), Real World Data (704K) | Health Care Quality, Access, and Evaluation (89K), Quality of Health Care (88K), Health Care Evaluation Mechanisms (87K), Health (86K), Diagnosis (85K), COVID-19 / SARS-CoV-2 (81K) |
| `FOCUS_TYPE` column | Yes — 14 values (Diseases, Drugs, Biology, etc.) | **Not available** |
| `FOCUS_DECILE` column | Yes — 0% null | **Not available** — only `SE_DECILE` |
| Decile completeness | 0% null | 0% null |
| Decile distribution | Spread across 1–10 | 88% concentrated at decile 1 |
| Decile-10-vs-1 pub ratio | 5.5× (10 = top confirmed) | 0.3× (reversed — digital reach ≠ publication volume) |

The reversed decile–publication correlation in `DIGITAL_REACH_FOCUS_AREA` confirms it captures a fundamentally different signal: digitally prominent experts are not necessarily the most published, and vice versa. For an NBRx model, `FOCUS_AREA` is the primary scientific-authority source; `DIGITAL_REACH_FOCUS_AREA` is a Tier 2 enrichment given its 4.2% coverage.

### 3.3 `INDEX` — six pre-computed influence scores

3,991,179 rows across 1,715,109 experts — **an average of 2.3 of the 6 index types per expert**, not all six.

| `TYPE` | Rows | Scale |
|---|---:|---|
| Publication Index | 1,477,549 | 0–10 |
| Scientific Reach | 1,027,597 | **0–4** |
| Event Index | 714,023 | 0–10 |
| Clinical Trial Index | 346,381 | 0–10 |
| Digital Reach | 283,705 | 0–10 |
| Guideline Index | 141,924 | 0–10 |

`UPPER_LIMIT` confirms two scales: 10 (2,963,582 rows) and 4 (1,027,597 — exactly the Scientific Reach count). **Never min-max these together.** Scientific Reach decodes via `SCIREACH_MAPPING` to n/a / local / regional / national / global.

`VALUE` is heavily skewed: 1 (2,740,688), 2 (572,496), 10 (9,968). Treat as ordinal, not continuous.

### 3.4 Clinical trials

**`ROLE`** (889,413 rows) — Investigator 535,122 (60.2%), **Principal Investigator 347,763 (39.1%)**, Sub-Investigator 6,528 (0.7%). The PI share is high enough to support a well-populated PI-specific feature.

**`PHASE`** (200,065 trials) — `None Specified` **134,991 (67.5%)**, Phase II 21,592, Phase I 12,795, Phase III 11,066, Phase IV 8,406, Phase I/II 6,333, Early Phase I 2,603, Phase II/III 2,279.
*Two thirds unphased. These are largely investigator-initiated and observational studies — model `None Specified` as its own category, not as missing.*

**Dates** — `START_DATE` 0.9% null, `END_DATE` 4.1% null. End dates run into 2026, so forward-looking commitment features are supportable. **No condition, sponsor or NCT field**: indication scoping must use `NAME` keyword matching.

### 3.5 Congresses and events

**`EVENT_ATTENDEE.POSITION`** (4,917,373 rows) — 8 clean values:

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

Excellent for feature engineering — podium roles (Speaker, Chairperson, Moderator, Panelist) cover 75% of rows.

**⚠ `TALK_TITLE`** — 18.0% null, 2,780,079 distinct, but the most frequent values are **generic session labels**: `Introduction` (15,034), `Panel Discussion` (11,955), `Session 1` (10,699), `Welcome` (7,027), `Q&A` (5,755), `Closing Remarks` (5,425). Topic matching on this field is viable but needs a stop-list; it is noisier than its distinct count suggests.

**⚠ `MEDICAL_EVENT.EVENT_TYPE` is corrupted.** Expected 3–6 values; found **51**, including bare dates (`2023-09-20`, `2022-09-08`) and French event names (` Digital Réunion Thématique du Cancéropôle Nord-Ouest…`). This is **column shift from the pipe-delimited source**: `AFFILIATION` and event-name fields contain literal `|` characters, and quoting was not honoured on some rows. Legitimate values are Workshop (531,503), Congress (144,767), Board Meeting (543), Webinar (390), Committee Meeting (144).
*Action: raise with data engineering. The affected row count is small (~0.3%) but the same defect may be shifting other fields silently.*

`END_DATE` is 71.6% null — use `START_DATE` for all timing logic.

### 3.6 Publications

**`AUTHORSHIP_POSITION`** (11,822,427 rows) — Coauthor 8,043,106 (68.0%), **Last Author 2,014,941 (17.0%)**, First Author 1,764,380 (14.9%). Senior-authorship weighting is well supported.

**`PUBLICATION_TYPE`** — 98 distinct, **multilingual**: Journal Article (2,720,437), Research Support Non-U.S. Gov't (674,720), 会議録 / Meeting Minutes (629,419), Review (447,699), Research Support N.I.H. Extramural (294,513), Case Reports (258,101), Comment (178,974), 解説 / Commentary (163,789), Editorial (123,093).
*Japanese-language type labels require normalisation before any type-based feature.*

`DATE` is 0% null and well distributed 2020–2024.

### 3.7 Payments (`PAYMENT`, 108,908,302 rows)

The largest table and the richest commercial signal.

**`PROGRAM_YEAR`** — 2013 to **2023 only**. 2023: 13,293,393 · 2022: 12,530,255 · 2021: 11,095,470. **No 2024 or 2025 data**, consistent with the CMS annual disclosure cycle.

**`NATURE_OF_PAYMENT`** — 23 values, 8.2% null:

| Nature | Count | Share |
|---|---:|---:|
| Food and Beverage | 88,824,342 | 81.6% |
| Travel and Lodging | 4,761,716 | 4.4% |
| Compensation for services (incl. faculty/speaker) | 2,302,184 | 2.1% |
| Education | 1,913,356 | 1.8% |
| Consulting Fee | 1,417,646 | 1.3% |
| Gift, Honoraria and 17 others | ~1.5M | 1.4% |

**`TYPE`** — General 100,025,684 (91.8%), Research 8,844,861 (8.1%), Ownership 37,757 (0.03%).

**`COMPANY_NAME`** — 2,776 distinct, normalised and usable directly: AbbVie (6,289,686), Janssen (5,148,158), Pfizer (4,947,268), **Novo Nordisk (4,681,042)**, AstraZeneca (4,385,139), Amgen, GSK, Lilly, MSD, Allergan, Novartis. Diabetes-relevant competitors are well represented.

**`AMOUNT`** — extreme right skew. Modal values are small (USD 25.00 appears 386,983 times; 15.00, 20.00, 10.00 all in the hundreds of thousands) alongside 1500.00 (203,745) and 3000.00 (144,113). Use `log1p`, not winsorising.

**`CLINICAL_TRIAL_ID`** — 98.1% null, but the 9,217 populated distinct values are **NCT identifiers** (`NCT05566639`, `NCT05815498`), *not* Veeva trial UUIDs. This is the only place an NCT number appears anywhere in the file set and can seed a partial Veeva-trial-to-ClinicalTrials.gov crosswalk.

**`CURRENCY`** — 99.97% USD.

### 3.8 Associations and sponsorship

**`ASSOCIATION_TYPE`** (803,819 rows) — 9 values: Scientific Association (253,062), Professional Association (250,892), **Editorial Board (164,773)**, Foundation (55,742), Patient Association (43,686), Regulatory/Health Authority (24,215), Internet Portal (9,264), Industry Association (2,163), Ministry (22).

**`POSITION_TYPE`** — Member (345,824), Board Member (220,757), Editor (172,330), Head of (64,907), Reviewer (1).

**⚠ Two data issues:**
- **`PAST_POSITION` = 'N' for 100% of rows.** No historical positions are retained, so the current-versus-past distinction is unavailable.
- **`JOB_TITLE` is an exact duplicate of `POSITION_TYPE`** — same 5 values, identical counts. One of the two is redundant.
- **`ASSOCIATION_NAME`** top values are committee labels rather than organisations: `Board of Directors` (32,516), `Fellows` (25,197), `Members` (7,408). Society-name matching (ADA, EASD, ISH) will need care — the organisation may sit elsewhere in the string or be absent.

**`COMPANY_SPONSORSHIP`** (543,811 rows, 192,000 experts) — `SCORE` 1–5: 2 (209,077), 1 (189,015), 3 (68,911), 5 (39,564), 4 (37,244). `HAS_SPONSORED_CLINICAL_TRIAL` true for 96%; `HAS_SPONSORED_EVENT` true for only 6.6%.

### 3.9 Affiliation and geography (`ADDRESS`)

**`AFFILIATION`** — 0% null, 522,336 distinct. Top: University of California (19,814), The University of Texas System (11,693), Stanford University (11,000), University of Michigan (8,564), NIH (6,441), Kaiser Permanente. Clean enough to serve as a site key after normalisation.

**`DEPARTMENT`** — 41.5% null, 318,955 distinct. Top values skew academic: Department of Chemistry (18,781), Department of Medicine (16,946), Department of Psychology (13,680) — reflecting the large `NON_PHYSICIAN_RESEARCHER` population.

**`ZIP`** — stored as text with leading zeros intact (`02115` appears 16,556 times). No padding required.

---

## 4. Features that can be created

Features are specified at **NPI-month** grain, keyed on the claims universe with Veeva left-joined.

### 4.1 Build-feasibility summary

| Family | Status | Constraint |
|---|---|---|
| Publication activity | ✅ Full | Dated; 49.2% expert coverage |
| Clinical trial activity | ✅ Full | Dated; 11.0% coverage — sparse but high-signal |
| Congress and events | ✅ Full | Dated; 29.3% coverage; `TALK_TITLE` needs a stop-list |
| Payments / commercial | ✅ Full | Dated; **2023 ceiling**, annual disclosure lag |
| Drug-class authority | ⚠ Partial | `CLINICAL_LEADER` decile 89% null |
| Scientific authority | ⚠ Partial | Static only — no history to reconstruct |
| Associations | ⚠ Partial | `PAST_POSITION` unusable; name matching fragile |
| Network / diffusion | ✅ Full | Self-joins on bridge tables |
| Site / affiliation | ✅ Full | 1:1 address confirmed |
| Digital reach | ⚠ Thin | 4.2% coverage |
| Company collaboration | ❌ Blocked | Table empty |
| Point-in-time vendor scores | ❌ Blocked | No SCD-2 history retained |

### 4.2 Tier 1 — build first

**Dated activity (fully point-in-time safe).** These derive from real event dates and carry no leakage risk.

| Feature | Source | Logic as of month M |
|---|---|---|
| `pub_in_scope_t12` / `_t36` | `SE_PUBLICATION` + `PUBLICATION` | Count of in-scope publications with `DATE` in window |
| `pub_senior_author_t12` | `SE_PUBLICATION` | Restrict to `First Author` / `Last Author` (31.9% of rows) |
| `pub_weighted_authorship` | `SE_PUBLICATION` | Last 1.0, First 1.0, Coauthor 0.3 |
| `pub_velocity_t3`, `pub_acceleration` | `PUBLICATION` | Rate and change in rate |
| `months_since_last_in_scope_pub` | `PUBLICATION` | Recency, 60-month cap |
| `trial_active_in_month` | `SE_CLINICAL_TRIAL` + `CLINICAL_TRIAL` | `START_DATE ≤ M ≤ END_DATE` |
| `trial_pi_active_in_month` | `SE_CLINICAL_TRIAL` | `ROLE = 'Principal Investigator'` |
| `n_trials_in_scope_t36`, `max_phase_in_scope` | `CLINICAL_TRIAL` | Treat `None Specified` as its own category |
| `months_to_next_trial_end` | `CLINICAL_TRIAL` | Capacity-release timing; end dates run to 2026 |
| `competitor_trial_active` | `CLINICAL_TRIAL.NAME` | Competitor-compound keyword match |
| `congress_speaker_t6` | `EVENT_ATTENDEE` | `POSITION` in Speaker/Chairperson/Moderator/Panelist |
| `congress_exposure_decayed` | `EVENT_ATTENDEE` + `MEDICAL_EVENT` | Exponential decay, 6-month half-life |
| `major_congress_in_scope_t6` | `MEDICAL_EVENT.NAME` | ADA, EASD, ATTD, ISH, ESH, AHA, ACC, ESC |
| `talk_topic_in_scope_t12` | `EVENT_ATTENDEE.TALK_TITLE` | Apply the generic-session stop-list first |
| `poster_presenter_t12` | `EVENT_ATTENDEE` | Early-career research output (14.7% of rows) |

**Payments.** Full depth 2013–2023, but every feature must be keyed on **disclosure availability**, not `PAYMENT_DATE`.

| Feature | Logic |
|---|---|
| `brand_payment_amt_t12` | `log1p(SUM(AMOUNT))` where `COMPANY_NAME` = our company |
| `competitor_payment_amt_t12` | Same per named competitor (Novo Nordisk, Lilly, AstraZeneca, Boehringer) |
| `payment_share_of_wallet` | Brand ÷ total payments received |
| `payment_nature_mix` | Share by `NATURE_OF_PAYMENT`; separate Consulting Fee and speaker compensation (3.4% combined) from Food and Beverage (81.6%) |
| `high_value_payment_flag` | Any single `AMOUNT` above an agreed threshold |
| `research_payment_flag` | `TYPE = 'Research'` (8.1%) or `CLINICAL_TRIAL_ID` populated |
| `n_companies_paying_t12` | Distinct `COMPANY_NAME` — industry accessibility |

**Network and diffusion.** Built from bridge-table self-joins; lag all peer outcomes to M-1 and compute site aggregates leave-one-out.

`coauthor_adopter_share` · `coinvestigator_adopter_share` · `co_attendee_adopter_share_t6` · `network_influence_exposure` · `site_adopter_share` (via normalised `AFFILIATION`) · `site_trial_experience_in_scope`

### 4.3 Tier 2 — build with stated caveats

| Feature | Caveat |
|---|---|
| `clinical_leader_decile_t2d` / `_htn` | Use `FOCUS_NAME` in (`Type 2 Diabetes Mellitus`, `Essential Hypertension`). **89% null** — carry an explicit missing indicator |
| `clinical_leader_decile_drug_class` | `TYPE = 'drug_class'`; the closest proxy to NBRx in the asset |
| `index_publication` / `_clinical_trial` / `_guideline` / `_event` | Static attributes only — no history. Guideline Index covers just 141,924 experts |
| `index_scientific_reach` | **0–4 scale**; decode via `SCIREACH_MAPPING`; never scaled with the 0–10 indices |
| `focus_decile_in_scope_max` | `FOCUS_AREA` taxonomy is research topics, not diseases — weak as a primary indication filter |
| `is_editorial_board_member` | `ASSOCIATION_TYPE = 'Editorial Board'` (164,773 rows). `PAST_POSITION` unusable, so currency cannot be established |
| `n_board_or_head_roles` | `POSITION_TYPE` in (`Board Member`, `Head of`) — 285,664 rows |
| `sponsorship_score_competitor` | `SCORE` 1–5; only 7.6% expert coverage |
| `is_emerging_expert` | 19,255 experts — small but precise |
| `expert_type`, `credential_md_phd` | Essential segmentation; `SPECIALTY_1` must be backfilled from NPPES given 61% nulls |
| `primary_affiliation`, `is_academic_medical_center` | 1:1 address confirmed; normalise `AFFILIATION` on `|` and parenthetical acronyms |

### 4.4 Not currently buildable

| Feature | Blocker | Resolution |
|---|---|---|
| `collab_strength_brand` / `_competitor` | `COMPANY_COLLABORATION` empty | Confirm subscription with Veeva |
| Any point-in-time vendor decile or index | No SCD-2 history retained | Begin archiving monthly loads now |
| `veeva_profile_merged_flag` | `SCIENTIFIC_EXPERT_CHANGELOG` not in the warehouse | Request the file; it is a 2-week sliding window, so history is lost until ingested |
| Guideline-committee membership | `ASSOCIATION_NAME` holds committee labels, not consistently organisations | Assess match rate before committing |
| `pct_panel_*`, access and claims features | Outside Veeva | From LAAD, MMIT and patient-level claims |

### 4.5 Recommended sequence

1. **Establish the claims-only baseline.** Lagged NBRx, class volume, patient panel, MMIT access. Every Veeva family must then be judged on incremental lift over this.
2. **Add dated Veeva activity** — publications, trials, events. Point-in-time safe and the largest expected contribution.
3. **Add payments**, keyed strictly on disclosure availability.
4. **Add network and site diffusion** — typically the strongest differentiator over a claims-only model.
5. **Add static vendor scores last**, as level-setting terms, accepting that they cannot be point-in-time until archiving matures.

### 4.6 Open actions

| # | Action | Owner |
|---|---|---|
| 1 | Begin archiving every monthly Veeva load — each month of delay is permanently lost panel history | Data Engineering |
| 2 | Align table load vintages (hub June 2025 vs children March 2025) | Data Engineering |
| 3 | Confirm whether `COMPANY_COLLABORATION` is in our subscription | Vendor Management |
| 4 | Request `SCIENTIFIC_EXPERT_CHANGELOG` and ingest it cumulatively | Data Engineering |
| 5 | Investigate pipe-delimiter column shift evidenced in `MEDICAL_EVENT.EVENT_TYPE` | Data Engineering |
| 6 | Retire `COMMUNITY_LEADER_FOCUS_AREA`; migrate to `CLINICAL_LEADER` | Analytics |
| 7 | Quantify the 239,201 orphan `ADDRESS` rows | Analytics |
| 8 | Trace the `EXPERT_TYPE` remapping against the Veeva specification | Data Engineering |
| 9 | Validate the T1D / T2D / HTN keyword scope against `CLINICAL_LEADER.FOCUS_NAME`, excluding pulmonary, portal, intracranial and ocular hypertension | Analytics |