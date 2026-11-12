# Veeva Link — Feature Engineering Plan for HCP-Level NBRx Model

**Companion to:** `veeva_link_to_people_data_assessment.md`
**Target model:** HCP-month NBRx forecast (T1D, T2D, Hypertension)
**Feature grain:** NPI × month, matching the existing Kerendia NBA 3.x pipeline
**Date:** November 2026

---

## 0. Architecture Decisions

### 0.1 Spine and join strategy

The **claims universe is the spine**, not Veeva. Veeva covers ~1.57M US NPIs against a prescriber universe several times larger.

```
Claims HCP Universe (NPI × month)
  └── LEFT JOIN SCIENTIFIC_EXPERT ON NPI
        └── LEFT JOIN child tables ON SE_ID
```

**`has_veeva_profile`** (binary) is itself a feature — experts tracked by Veeva are likely higher-influence HCPs.

### 0.2 NPI join constraints

- NPI fill rate: **62%** overall, **84%** for PHYSICIANs
- NPI is effectively 1:1 with SE_ID where populated (1,568,886 distinct NPIs)
- `VEEVA_ID` (98.1% populated) is the fallback route for NPI recovery via Veeva Network
- Non-US experts (12.5%) will never have NPI — filter to `SYS_TENANT = 'US'`

### 0.3 SCD-2 filtering

Every Snowflake query must apply:
```sql
WHERE IS_LATEST_FLAG = 'Y' AND COALESCE(SYS_DELETE_FLAG, 0) = 0
```
Exception: `SCIENTIFIC_EXPERT` uses `COALESCE(ISDELETED, 0) = 0` instead of `SYS_DELETE_FLAG`.

### 0.4 SYS_TENANT trap

Person tables use country codes (`US`, `CA`, `BR`); reference/dimension tables use `XX` (global). A blanket `SYS_TENANT = 'US'` filter will **silently drop all PUBLICATION, CLINICAL_TRIAL, and MEDICAL_EVENT rows**.

### 0.5 Time-dependent vs time-agnostic tables

**⚠ SNAPSHOT CONSTRAINT:** The warehouse holds **current state only** — no SCD-2 history is retained. `SCIENTIFIC_EXPERT` was refreshed 2025-06-25; all child tables were last loaded 2025-03-06. The data represents a rolling 5-year window from the export date. There is no panel of historical months to window against.

**Consequence for feature engineering:** Time-dependent tables (those with event dates) still distinguish *what kind* of date information is available, but we **cannot compute rolling-window features relative to each model month M**. Instead, all features are **total aggregates over the full snapshot window**. The event dates remain useful for simple recency features (e.g. months since last publication) and for scoping within the snapshot (e.g. excluding very old events), but not for true point-in-time reconstruction.

**Time-dependent tables** carry a date column recording *when the underlying event occurred*. Within the snapshot, these dates can be used for recency and sub-window aggregation.

**Time-agnostic tables** carry no event date — only system-load timestamps (`SYS_SRC_MODIFIED_DT`, `LOAD_ID`). They reflect the vendor's *current assessment* at the time of the latest Snowflake load.

| Table | Type | Date Column | Temporal Window Possible? | Leakage Risk |
|-------|------|-------------|--------------------------|-------------|
| `PUBLICATION` | **Time-dependent** | `DATE` (0% null) | Yes — publication date | LOW |
| `CLINICAL_TRIAL` | **Time-dependent** | `START_DATE` (0.9% null), `END_DATE` (4.1% null) | Yes — trial start/end dates | LOW |
| `MEDICAL_EVENT` | **Time-dependent** | `START_DATE` (0% null), `END_DATE` (71.6% null) | Yes — event start date only | LOW |
| `PAYMENT` | **Time-dependent** | `PROGRAM_YEAR`, `PAYMENT_DATE` | Yes — program year (annual, 6–18 month lag) | LOW |
| `SCIENTIFIC_EXPERT` | Time-agnostic | None (only `SYS_SRC_MODIFIED_DT`) | No — current profile snapshot | MEDIUM |
| `ADDRESS` | Time-agnostic | None | No — current affiliation snapshot | MEDIUM |
| `ASSOCIATION` | Time-agnostic | None (`PAST_POSITION` flag only) | No — but PAST_POSITION = Y/N gives a coarse before/after | MEDIUM |
| `COMPANY_SPONSORSHIP` | Time-agnostic | None | No — current sponsorship snapshot | MEDIUM |
| `FOCUS_AREA` | Time-agnostic | None | No — Veeva recomputes scores each load | HIGH |
| `CLINICAL_LEADER` | Time-agnostic | None | No — same as FOCUS_AREA | HIGH |
| `DIGITAL_REACH_FOCUS_AREA` | Time-agnostic | None | No — same as FOCUS_AREA | HIGH |
| `INDEX` | Time-agnostic | None | No — six pre-computed influence scores | HIGH |

**Bridge tables** (`SE_PUBLICATION`, `SE_CLINICAL_TRIAL`, `EVENT_ATTENDEE`) are themselves time-agnostic (no event date), but they link to time-dependent dimension tables, so the joined result *is* temporal.

**Practical implication:**
- **Activity features (Category A)** can be windowed to any month M — they are the safest features
- **Profile features (Category B)** are stable enough that the snapshot is usable, but cannot be reconstructed for a past month
- **Scoring features (Category C)** reflect *today's* vendor assessment — using them for a model trained on historical months introduces look-ahead bias unless we begin archiving monthly loads

### 0.6 Leakage risk tiers (summary)

| Tier | Risk | Description | Tables |
|------|------|-------------|--------|
| **T1** | LOW | Event-dated activity — temporal filtering possible | PUBLICATION, CLINICAL_TRIAL, MEDICAL_EVENT, PAYMENT |
| **T2** | MEDIUM | Profile attributes — stable but could reflect future state | SCIENTIFIC_EXPERT, ADDRESS, ASSOCIATION, COMPANY_SPONSORSHIP |
| **T3** | HIGH | Vendor scores — snapshot only, no history retained | FOCUS_AREA, CLINICAL_LEADER, DIGITAL_REACH_FOCUS_AREA, INDEX |


### 0.7 HCP Universe Overlap & Decile-Based Profiling

The KOL EDA notebook (Section 6) profiles the **full HCP Universe overlap** against Veeva, segmenting all matched HCPs into High / Medium / Low influence tiers based on their best decile across the three scoring tables.

#### HCP Universe → Veeva overlap

The NBA 3.x HCP Universe (294,727 IQVIA PROVIDER_IDs) was mapped to Veeva SCIENTIFIC_EXPERT via the NPI crosswalk table `SOURCE_PROVIDER_BHID_NPI_MAPPING`:

| Step | Count | Coverage |
|------|------:|----------|
| HCP Universe (total) | 294,727 | — |
| Providers with valid NPI (via crosswalk) | 294,553 | 99.9% |
| Matched to Veeva SE_ID | **228,930** | **77.7%** |
| Veeva US experts with NPI | 1,594,381 | 14.4% hit rate |

**Key finding:** 77.7% of the HCP Universe has a Veeva profile. The remaining 22.3% (65,797 HCPs) have no Veeva coverage — these are likely lower-volume prescribers outside Veeva's KOL tracking threshold.

#### Segmentation rules

For each of the 228,930 matched HCPs, the **maximum decile** is computed across three in-scope scoring tables:

- **FOCUS_AREA** → `FOCUS_DECILE` (scientific output; 9.2% of overlap has a score)
- **CLINICAL_LEADER** → `SE_DECILE` (patient volume; 28.8% scored)
- **DIGITAL_REACH_FOCUS_AREA** → `SE_DECILE` (digital influence; 1.7% scored)

All three tables are filtered to US, in-scope indications (T2D, CKD, T1D, HF) before computing the max.

| Segment | Rule | HCPs | % of Overlap |
|---------|------|-----:|-------------:|
| **High** | Max decile ≥ 7 in any table | 15,658 | 6.8% |
| **Medium** | Max decile 4–6 (not High) | 25,892 | 11.3% |
| **Low** | Max decile 1–3, or no score in any table | 187,380 | 81.9% |

**Scoring coverage:** Only 34.8% of the overlap (79,578 HCPs) have a decile in *any* table. The remaining 65.2% (149,352) land in Low by default — they are in Veeva but have no in-scope influence score. CLINICAL_LEADER is the dominant scoring source (28.8% coverage), followed by FOCUS_AREA (9.2%) and DIGITAL_REACH (1.7%).

#### Segment profiles

| Attribute | High (15,658) | Medium (25,892) | Low (187,380) |
|-----------|:---:|:---:|:---:|
| Mean max decile | 7.9 | 4.9 | 1.9 (scored only) |
| Scored in FOCUS_AREA | 4,406 (28.1%) | 6,122 (23.6%) | 10,425 (5.6%) |
| Scored in CLINICAL_LEADER | 14,060 (89.8%) | 22,817 (88.1%) | 29,032 (15.5%) |
| Scored in DIGITAL_REACH | 1,277 (8.2%) | 1,238 (4.8%) | 1,466 (0.8%) |
| Top specialties | Cardiology, Internal Med, Family Med, Endocrinology, Nephrology | Cardiology, Internal Med, Family Med, Endocrinology, Nephrology | Internal Med, Family Med, Cardiology |
| Emerging Expert rate | ~2–3% | ~1% | <0.5% |

#### Downstream activity metrics by segment

**Publications:**

| Segment | HCPs | Total Pubs | Active (%) | Mean | Median | Max |
|---------|-----:|----------:|----------:|-----:|-------:|----:|
| High | 15,658 | 158,233 | 4,910 (31.4%) | 10.1 | 0 | 910 |
| Medium | 25,892 | 92,388 | 6,984 (27.0%) | 3.6 | 0 | 417 |
| Low | 187,380 | 107,980 | 24,635 (13.1%) | 0.6 | 0 | 324 |

**Clinical Trials:**

| Segment | HCPs | Total Trials | Active (%) | Mean | Median | Max |
|---------|-----:|------------:|----------:|-----:|-------:|----:|
| High | 15,658 | 21,531 | 3,649 (23.3%) | 1.4 | 0 | 76 |
| Medium | 25,892 | 15,524 | 3,979 (15.4%) | 0.6 | 0 | 54 |
| Low | 187,380 | 17,618 | 7,346 (3.9%) | 0.1 | 0 | 57 |

**Medical Events:**

| Segment | HCPs | Total Events | Active (%) | Mean | Median | Max |
|---------|-----:|------------:|----------:|-----:|-------:|----:|
| High | 15,658 | 55,641 | 4,023 (25.7%) | 3.6 | 0 | 283 |
| Medium | 25,892 | 39,511 | 5,496 (21.2%) | 1.5 | 0 | 287 |
| Low | 187,380 | 57,357 | 17,441 (9.3%) | 0.3 | 0 | 319 |

#### Activity gradient (High ÷ Low mean per HCP)

| Metric | High mean | Low mean | Gradient |
|--------|----------:|---------:|---------:|
| Publications | 10.1 | 0.6 | **17.5×** |
| Clinical Trials | 1.4 | 0.1 | **14.6×** |
| Medical Events | 3.6 | 0.3 | **11.6×** |

**Key findings:**
1. **The decile segmentation produces a strong, monotonic activity gradient** — High-tier HCPs are 12–18× more active than Low-tier across all three channels, validating the scoring tables as meaningful influence proxies.
2. **The Low segment is massive (82%) but not inert** — 24,635 Low-tier HCPs still have publications (13.1% active), suggesting latent scientific engagement below the Veeva scoring threshold.
3. **Median is 0 across all segments** — even High-tier KOLs have a skewed distribution, reinforcing the need for log-transform or percentile binning (Section 0.7, Key finding on skewness).
4. **Medium tier (11.3%) is the emerging KOL cohort** — 27% publish, 15.4% run trials, 21.2% attend events. These HCPs are potential future High-tier KOLs.
5. **CLINICAL_LEADER dominates the scoring** — 89.8% of High-tier and 88.1% of Medium-tier are scored via CLINICAL_LEADER (patient volume), versus only 28.1% / 23.6% from FOCUS_AREA (scientific output). The segments primarily reflect clinical practice volume, not research prominence.

**Implication for features:** The `veeva_segment` (High/Medium/Low) is itself a strong candidate feature. Per-segment activity metrics (e.g., `veeva_pubs_mean_segment`, `veeva_segment_rank`) could capture relative positioning within tier. The 65.2% unscored-but-matched HCPs represent a distinct "Veeva-profiled but unranked" cohort that may benefit from separate treatment.

---

## 1. Category A — Activity Features (Snapshot Aggregates)

These features are computed as **totals over the full snapshot window** (~5-year rolling window from export date). Event dates are used for recency and sub-window scoping within the snapshot, not for point-in-time reconstruction.

### 1.1 Publication Features

**Source:** `SE_PUBLICATION` (bridge) → `PUBLICATION` (dimension)
**Join:** SE_ID → SE_PUBLICATION.SE_ID + PUBLICATION_ID → PUBLICATION.PUBLICATION_ID
**Coverage:** 49.2% of experts (1,246,496)
**Date column:** `PUBLICATION.DATE` (0% null, range 2020–2024)

| Feature | Logic | Notes |
|---------|-------|-------|
| `veeva_n_pubs_total` | COUNT DISTINCT PUBLICATION_ID | Total publications in snapshot |
| `veeva_n_pubs_in_scope` | Same, but TITLE matches indication + drug class + competitor keywords (Section 7) | In-scope publication count (broad cardiorenal landscape) |
| `veeva_pubs_per_year` | n_pubs_total / years spanned in DATE | Average annual publication rate |
| `veeva_senior_author_ratio` | Share of pubs as First Author or Last Author | Seniority signal; AUTHORSHIP_POSITION is clean (14.9% First, 17.0% Last) |
| `veeva_first_author_count` | COUNT where AUTHORSHIP_POSITION = 'First Author' | First-author leadership |
| `veeva_months_since_last_pub` | Months between MAX(DATE) and snapshot date | Recency — uses date within snapshot |
| `veeva_n_co_authors` | COUNT DISTINCT co-author SE_IDs on in-scope pubs | Network size / collaboration breadth |
| `veeva_journal_article_ratio` | Share of pubs with PUBLICATION_TYPE = 'Journal Article' | Quality indicator (vs abstracts, case reports) |

**DQ controls:**
- DATE is 0% null, well distributed 2020–2024
- PUBLICATION_TYPE has multilingual labels (Japanese 会議録, 解説) — normalise before type-based features
- Orphan rate SE_PUBLICATION → PUBLICATION is near-zero (5 rows)

### 1.2 Clinical Trial Features

**Source:** `SE_CLINICAL_TRIAL` (bridge) → `CLINICAL_TRIAL` (dimension)
**Join:** SE_ID → SE_CLINICAL_TRIAL.SE_ID + CLINICAL_TRIAL_ID → CLINICAL_TRIAL.CLINICAL_TRIAL_ID
**Coverage:** 11.0% of experts (279,438)
**Date columns:** `START_DATE` (0.9% null), `END_DATE` (4.1% null)

| Feature | Logic | Notes |
|---------|-------|-------|
| `veeva_n_trials_in_scope` | COUNT DISTINCT CLINICAL_TRIAL_ID where NAME matches indication regex | Total in-scope trials in snapshot |
| `veeva_n_trials_active` | Trials where END_DATE is null OR END_DATE > snapshot date | Currently ongoing trials at time of export |
| `veeva_pi_role_flag` | Any row with ROLE = 'Principal Investigator' on in-scope trial | Trial leadership; PI = 39.1% of rows |
| `veeva_max_phase_in_scope` | Highest PHASE ordinal on in-scope trials | Level of evidence generated |
| `veeva_finerenone_trial_flag` | Any trial NAME mentioning 'finerenone' or 'Kerendia' or FIDELIO/FIGARO/FIDELITY/FINE-HEART | Direct product experience |
| `veeva_mra_trial_flag` | Any trial NAME mentioning MRA class drugs (spironolactone, eplerenone, mineralocorticoid) | Drug-class experience |
| `veeva_sglt2i_trial_flag` | Any trial NAME mentioning SGLT2i drugs (empagliflozin, dapagliflozin, canagliflozin, sotagliflozin, gliflozin) | Competitor drug experience |
| `veeva_cardiorenal_trial_count` | COUNT DISTINCT trials matching full drug class + indication + landmark trial keywords | Total cardiorenal competitive landscape trials |

**DQ controls:**
- No NCT field — indication scoping via NAME keyword matching only
- PHASE: 67.5% is 'None Specified' (investigator-initiated/observational) — model as own category
- START_DATE 0.9% null, END_DATE 4.1% null
- Orphan rate SE_CLINICAL_TRIAL → CLINICAL_TRIAL is near-zero (438 rows)

### 1.3 Congress / Event Features

**Source:** `EVENT_ATTENDEE` (bridge) → `MEDICAL_EVENT` (dimension)
**Join:** SE_ID → EVENT_ATTENDEE.SE_ID + MEDICAL_EVENT_ID → MEDICAL_EVENT.MEDICAL_EVENT_ID
**Coverage:** 29.3% of experts (740,879)
**Date column:** `MEDICAL_EVENT.START_DATE` (0% null; END_DATE 71.6% null — use START only)

| Feature | Logic | Notes |
|---------|-------|-------|
| `veeva_n_events_total` | COUNT DISTINCT MEDICAL_EVENT_ID | Total events attended in snapshot |
| `veeva_n_events_in_scope` | Same, but MEDICAL_EVENT.NAME matches indication regex | In-scope event count |
| `veeva_speaker_flag` | Any POSITION IN ('Speaker', 'Chairperson', 'Moderator') at in-scope event | Thought leader indicator |
| `veeva_podium_role_count` | COUNT of Speaker + Chairperson + Moderator + Panelist roles | Podium roles cover 75% of rows |
| `veeva_poster_count` | COUNT where POSITION = 'Poster Presenter' | Active researcher indicator |

**DQ controls:**
- END_DATE is 71.6% null — use START_DATE for all timing
- EVENT_TYPE is corrupted (~0.3% column-shifted rows from pipe-delimited source)
- TALK_TITLE is noisy — needs stop-list for generic labels ('Introduction', 'Panel Discussion', 'Q&A')
- Orphan rate EVENT_ATTENDEE → MEDICAL_EVENT is low (4,513 rows, 0.09%)

### 1.4 Payment Features (CMS Open Payments)

**Source:** `PAYMENT` (direct child of SCIENTIFIC_EXPERT)
**Join:** SE_ID → PAYMENT.SE_ID
**Coverage:** 39.5% of experts (1,000,117)
**Date column:** `PROGRAM_YEAR` (2013–2023; no 2024/2025 data due to CMS annual cycle)

| Feature | Logic | Notes |
|---------|-------|-------|
| `veeva_total_payment_amt` | SUM(AMOUNT) across all PROGRAM_YEARs in snapshot | Total industry payment volume |
| `veeva_consulting_fee_amt` | SUM(AMOUNT) where NATURE_OF_PAYMENT = 'Consulting Fee' | Advisory engagement signal |
| `veeva_speaker_payment_amt` | SUM(AMOUNT) where NATURE_OF_PAYMENT LIKE '%speaker%' | Speaker bureau involvement |
| `veeva_n_paying_companies` | COUNT DISTINCT COMPANY_NAME | Breadth of industry relationships |
| `veeva_bayer_payment_flag` | Any payment from COMPANY_NAME ILIKE 'bayer%' | Prior Bayer relationship |
| `veeva_competitor_payment_flag` | Payment from Novo Nordisk, Lilly, AstraZeneca, etc. | Competitor engagement |
| `veeva_research_payment_flag` | Any payment with TYPE = 'Research' | Research-oriented HCP |
| `veeva_latest_program_year` | MAX(PROGRAM_YEAR) | Recency of payment activity |

**DQ controls:**
- PROGRAM_YEAR runs 2013–2023 only; **no 2024 or 2025 data** (CMS annual cycle, 6–18 month lag)
- Food and Beverage is 81.6% of rows — consider excluding for a "meaningful payment" variant
- NATURE_OF_PAYMENT is 8.2% null
- Key on PROGRAM_YEAR publication date, NOT PAYMENT_DATE — slight temporal ambiguity

---

## 2. Category B — Profile, Commercial & Identity Features (Tier 2: MEDIUM leakage)

Stable attributes that change slowly. Safe for modelling if the HCP universe vintage is controlled.

### 2.1 Expert Profile Features

**Source:** `SCIENTIFIC_EXPERT` (hub table)

| Feature | Logic | Notes |
|---------|-------|-------|
| `veeva_has_profile` | Binary: NPI exists in SCIENTIFIC_EXPERT | Distinguishes KOLs from ordinary prescribers |
| `veeva_expert_type` | EXPERT_TYPE (15 categories) | Segment by prescribing capability; encode as categorical |
| `veeva_is_physician` | EXPERT_TYPE IN ('PHYSICIAN', 'NURSE_PRACTITIONER', 'PHYSICIAN_ASSISTANT') | Prescriber-capable flag |
| `veeva_specialty_match` | SPECIALTY_1 IN ('Internal Medicine', 'Endocrinology', 'Nephrology', 'Cardiology', 'Family Medicine') | Kerendia-relevant specialty; **61% null — backfill from NPPES** |
| `veeva_emerging_expert` | EMERGING_EXPERT = 'Y' | Only 0.76% flagged but high-value cohort |
| `veeva_has_degree_md` | DEGREE_1 = 'MD' | Credential signal (29.9% null) |

### 2.2 Geographic & Institutional Features

**Source:** `ADDRESS` (1:1 child of SCIENTIFIC_EXPERT)

| Feature | Logic | Notes |
|---------|-------|-------|
| `veeva_state` | STATE (2-letter code) | Geographic segmentation |
| `veeva_academic_affiliation` | AFFILIATION contains university/medical school keywords | Academic vs community flag |
| `veeva_has_department` | DEPARTMENT IS NOT NULL | Institutional depth indicator |

**DQ controls:**
- ZIP loses leading zeros — always `LPAD(ZIP::VARCHAR, 5, '0')`
- AFFILIATION may contain literal `|` pipe characters (8,414 rows) — possible column-shift
- ADDRESS has 239K more rows than SE (orphans from vintage mismatch)

### 2.3 Association & Professional Role Features

**Source:** `ASSOCIATION` (1:N child, 14.3% coverage)

| Feature | Logic | Notes |
|---------|-------|-------|
| `veeva_n_editorial_boards` | COUNT where ASSOCIATION_TYPE = 'Editorial Board' AND PAST_POSITION = 'N' | Institutional influence |
| `veeva_n_society_roles` | COUNT DISTINCT ASSOCIATION rows, current only | Professional society engagement |
| `veeva_n_leadership_roles` | COUNT where POSITION contains 'President', 'Chair', 'Director' | Leadership indicator |
| `veeva_kidney_society_flag` | ASSOCIATION at ASN, NKF, ISN, or kidney-related societies | Kerendia-relevant society membership |

### 2.4 Industry Relationship Features

**Source:** `COMPANY_SPONSORSHIP` (7.6% coverage), `COMPANY_COLLABORATION` (EMPTY — 0 rows)

| Feature | Logic | Notes |
|---------|-------|-------|
| `veeva_n_sponsors` | COUNT DISTINCT COMPANY_NAME from COMPANY_SPONSORSHIP | Breadth of industry relationships |
| `veeva_bayer_sponsor_flag` | Any COMPANY_NAME ILIKE 'bayer%' | Prior Bayer sponsorship |
| `veeva_has_trial_sponsorship` | HAS_SPONSORED_TRIAL = 'Y' or HAS_SPONSORED_EVENT = 'Y' | Active sponsorship indicator |

**Note:** `COMPANY_COLLABORATION` is **empty (0 rows)** — no features possible. Confirm with Veeva if this is in our subscription.

---

## 3. Category C — Scoring & Ranking Features (Tier 3: HIGH leakage)

**⚠ CRITICAL WARNING:** These are snapshot-only scores. The warehouse holds current state only — no superseded versions are retained. **Point-in-time reconstruction is impossible.** These can only be used as static attributes or become temporal once we begin archiving monthly loads.

### 3.1 Disease Authority Scores

**Source:** `CLINICAL_LEADER` (34.4% coverage, curated clinical vocabulary)

| Feature | Logic | Notes |
|---------|-------|-------|
| `veeva_cl_decile_t2d` | SE_DECILE where FOCUS_NAME = 'Type 2 Diabetes Mellitus' | Patient volume ranking for T2D; **89.1% null** |
| `veeva_cl_decile_htn` | SE_DECILE where FOCUS_NAME = 'Essential Hypertension' | Patient volume ranking for HTN |
| `veeva_cl_decile_ckd` | SE_DECILE for CKD-related FOCUS_NAME | Patient volume ranking for CKD |
| `veeva_cl_max_decile_in_scope` | MAX(SE_DECILE) across all in-scope FOCUS_NAME | Best ranking across target indications |
| `veeva_cl_n_focus_areas` | COUNT DISTINCT FOCUS_NAME in CLINICAL_LEADER | Breadth of clinical activity |

**DQ controls:**
- SE_DECILE is **89.1% null** — only ~9.9M of 91M rows carry a decile
- 10 = TOP confirmed empirically
- TYPE: drug_class (56.7%) vs disease (43.3%) — filter by TYPE when appropriate

### 3.2 Scientific Output Scores

**Source:** `FOCUS_AREA` (62.7% coverage, MeSH-like taxonomy)

| Feature | Logic | Notes |
|---------|-------|-------|
| `veeva_fa_decile_max_in_scope` | MAX(FOCUS_DECILE) across FOCUS_NAME matching indication regex | Best scientific output ranking |
| `veeva_fa_n_focus_areas_in_scope` | COUNT DISTINCT FOCUS_NAME matching indication regex | Breadth of in-scope research |
| `veeva_fa_top_decile_any` | MAX(FOCUS_DECILE) across ALL FOCUS_NAME | Overall scientific prominence |

**DQ controls:**
- FOCUS_DECILE is 0% null and 10 = TOP
- 18,499 distinct FOCUS_NAME — too many to enumerate; use regex matching
- FOCUS_TYPE (14 values) can pre-filter: 'Diseases' (41.8M) narrows the taxonomy

### 3.3 Digital Influence Scores

**Source:** `DIGITAL_REACH_FOCUS_AREA` (4.2% coverage only)

| Feature | Logic | Notes |
|---------|-------|-------|
| `veeva_digital_reach_decile` | MAX(SE_DECILE) across in-scope FOCUS_NAME | Online influence ranking |
| `veeva_has_digital_reach` | Binary: expert exists in DIGITAL_REACH_FOCUS_AREA | Thin coverage makes this binary valuable on its own |

**DQ controls:**
- Only 106,471 experts covered (4.2%) — treat as enrichment, not primary
- 88% sit at decile 1 — decile is nearly binary (1 vs rest)
- **No FOCUS_TYPE or FOCUS_DECILE** — only SE_DECILE and FOCUS_NAME available

### 3.4 Index Scores

**Source:** `INDEX` (67.7% coverage, 6 types)

| Feature | Logic | Notes |
|---------|-------|-------|
| `veeva_publication_index` | VALUE where TYPE = 'Publication Index' | Scale 0–10, ordinal |
| `veeva_clinical_trial_index` | VALUE where TYPE = 'Clinical Trial Index' | Scale 0–10 |
| `veeva_event_index` | VALUE where TYPE = 'Event Index' | Scale 0–10 |
| `veeva_guideline_index` | VALUE where TYPE = 'Guideline Index' | Scale 0–10; guideline authorship |
| `veeva_digital_reach_index` | VALUE where TYPE = 'Digital Reach' | Scale 0–10 |
| `veeva_scientific_reach` | VALUE where TYPE = 'Scientific Reach' | Scale 0–4; map via SCIREACH_MAPPING (0=n/a, 1=local, 2=regional, 3=national, 4=global) |
| `veeva_n_index_types` | COUNT DISTINCT TYPE per expert | Avg is 2.3 of 6; breadth indicator |

**DQ controls:**
- **Never min-max Scientific Reach (0–4) together with others (0–10)**
- VALUE is heavily skewed: 1 (2.74M), 2 (572K), 10 (10K) — treat as ordinal
- SCIREACH_MAPPING table is missing from warehouse — hardcode the 0–4 lookup

---

## 4. Composite / Derived Features

These combine signals from multiple table categories.

| Feature | Logic | Tables Used | Risk |
|---------|-------|-------------|------|
| `veeva_kol_composite_score` | Weighted sum of publication_index + event_index + clinical_trial_index + n_pubs_5y + pi_role_flag | INDEX + SE_PUBLICATION + SE_CLINICAL_TRIAL | Mixed |
| `veeva_research_vs_clinical` | Ratio of n_pubs / cl_max_decile — distinguishes researchers from practitioners | PUBLICATION + CLINICAL_LEADER | Mixed |
| `veeva_industry_engagement_score` | n_paying_companies + n_sponsors + consulting_fee_flag | PAYMENT + COMPANY_SPONSORSHIP | T1 |
| `veeva_network_centrality` | n_co_authors + n_events + n_society_roles | SE_PUBLICATION + EVENT_ATTENDEE + ASSOCIATION | T1–T2 |

---

## 5. Tables NOT Producing Features

| Table | Reason |
|-------|--------|
| `COMPANY_COLLABORATION` | Empty (0 rows) |
| `COMMUNITY_LEADER_FOCUS_AREA` | Deprecated at Veeva spec v1.8, frozen since Aug 2024, superseded by CLINICAL_LEADER |
| `SCIENTIFIC_EXPERT_CHANGELOG` | Missing from warehouse — cannot track merged SE_IDs |
| `SCIREACH_MAPPING` | Missing from warehouse — hardcode the 5-value lookup instead |

---

## 6. Implementation Plan

### Phase 1: Foundation (Week 1)
- [ ] Build the NPI → SE_ID mapping table with SCD-2 filtering
- [ ] Implement `has_veeva_profile` and expert profile features (Section 2.1)
- [ ] Implement ADDRESS features (Section 2.2)
- [ ] Define and test indication regex patterns for T1D, T2D, HTN, CKD
- [ ] **Validate:** left-join Veeva onto claims universe, confirm coverage rates

### Phase 2: Activity Features (Weeks 2–3)
- [ ] Publication features (Section 1.1) — requires 2-hop join through bridge
- [ ] Clinical trial features (Section 1.2) — requires NAME regex for indication scoping
- [ ] Event features (Section 1.3) — apply stop-list for TALK_TITLE, use START_DATE only
- [ ] Payment features (Section 1.4) — key on PROGRAM_YEAR, handle 6–18 month lag
- [ ] **Validate:** spot-check 10 known KOLs against Veeva web profiles

### Phase 3: Scoring & Ranking Features (Week 3)
- [ ] CLINICAL_LEADER deciles (Section 3.1) — handle 89.1% null SE_DECILE
- [ ] FOCUS_AREA deciles (Section 3.2) — pre-filter by FOCUS_TYPE = 'Diseases'
- [ ] INDEX scores (Section 3.4) — pivot 6 types into 6 columns, separate Scientific Reach
- [ ] DIGITAL_REACH features (Section 3.3) — binary + max decile only (4.2% coverage)
- [ ] **Validate:** confirm decile direction (10 = top) on the output

### Phase 4: Association, Sponsorship & Composites (Week 4)
- [ ] Association features (Section 2.3)
- [ ] Company sponsorship features (Section 2.4)
- [ ] Composite features (Section 4)
- [ ] **Validate:** full feature matrix completeness check, null rate analysis

### Phase 5: Integration & QC (Week 5)
- [ ] Join all Veeva features into the existing NBA pipeline feature matrix
- [ ] Feature importance baseline: compare Veeva features vs claims-only model
- [ ] Correlation analysis: identify redundancy within Veeva feature groups
- [ ] Document final feature dictionary with business descriptions

---

## 7. Indication Scoping Patterns

Used for filtering FOCUS_NAME, PUBLICATION.TITLE, CLINICAL_TRIAL.NAME, and MEDICAL_EVENT.NAME.

**⚠ CRITICAL:** `REGEXP_LIKE` fails silently through the Spark Snowflake connector on free-text columns (returns 0 rows). Use `REGEXP_LIKE` **only** on controlled-vocabulary columns (`FOCUS_NAME`) inside subqueries. For `TITLE`, `NAME`, and other free-text VARCHAR columns, use `ILIKE` / `LIKE`-based matching (see Section 0.7, Technical learnings #1).

### REGEXP_LIKE patterns (for FOCUS_NAME only):

```sql
-- Type 1 Diabetes
REGEXP_LIKE(col, 'type.?1.?diabet|\bT1D\b|\bIDDM\b|juvenile.?diabet|insulin.?dependent', 'i')
  AND NOT REGEXP_LIKE(col, 'type.?2|\bT2D\b|\bNIDDM\b|gestational', 'i')

-- Type 2 Diabetes  
REGEXP_LIKE(col, 'type.?2.?diabet|\bT2D\b|\bNIDDM\b|non.?insulin|metformin|GLP.?1|SGLT2|DPP.?4|sulfonylurea|finerenone|kerendia', 'i')
  AND NOT REGEXP_LIKE(col, 'type.?1.?diabet|\bT1D\b|\bIDDM\b|juvenile', 'i')

-- Hypertension
REGEXP_LIKE(col, 'hypertens|\bHTN\b|blood.?pressure|antihypertens|ACE.?inhib|ARB\b|calcium.?channel|diuretic|MRA\b|mineralocorticoid', 'i')

-- CKD (Kerendia-specific)
REGEXP_LIKE(col, 'chronic.?kidney|\bCKD\b|nephro|renal.?insufficiency|kidney.?disease|dialysis|\beGFR\b|albuminuria|UACR|finerenone|kerendia', 'i')
```

### ILIKE patterns (for TITLE, NAME — free-text columns)

```sql
-- T2D (PUBLICATION.TITLE or CLINICAL_TRIAL.NAME)
LOWER(col) LIKE '%type 2 diabet%' OR LOWER(col) LIKE '% t2d %' OR LOWER(col) LIKE '%t2dm%'
OR LOWER(col) LIKE '%metformin%' OR LOWER(col) LIKE '%sglt2%' OR LOWER(col) LIKE '%glp-1%'
OR LOWER(col) LIKE '%dpp-4%' OR LOWER(col) LIKE '%sulfonylurea%'

-- CKD
LOWER(col) LIKE '%chronic kidney%' OR LOWER(col) LIKE '% ckd %' OR LOWER(col) LIKE '%nephro%'
OR LOWER(col) LIKE '%kidney disease%' OR LOWER(col) LIKE '%dialysis%' OR LOWER(col) LIKE '%egfr%'
OR LOWER(col) LIKE '%albuminuria%' OR LOWER(col) LIKE '%uacr%' OR LOWER(col) LIKE '%finerenone%'

-- T1D
LOWER(col) LIKE '%type 1 diabet%' OR LOWER(col) LIKE '% t1d %' OR LOWER(col) LIKE '%t1dm%'
OR LOWER(col) LIKE '%insulin-dependent diabet%' OR LOWER(col) LIKE '%juvenile diabet%'

-- HF (Heart Failure)
LOWER(col) LIKE '%heart failure%' OR LOWER(col) LIKE '%hfref%' OR LOWER(col) LIKE '%hfpef%'
OR LOWER(col) LIKE '%cardiomyopathy%' OR LOWER(col) LIKE '%ventricular dysfunction%'
```

### Drug class and competitor keywords (for PUBLICATION.TITLE, CLINICAL_TRIAL.NAME)

The indication patterns above capture disease-level terms. For publications and clinical trials, we also need **drug class, brand/generic name, and landmark trial** keywords to find KOLs working in the competitive landscape, not just those who mention finerenone directly.

```sql
-- Kerendia / finerenone (direct product)
LOWER(col) LIKE '%finerenone%' OR LOWER(col) LIKE '%kerendia%'
OR LOWER(col) LIKE '%fidelio%' OR LOWER(col) LIKE '%figaro%'
OR LOWER(col) LIKE '%fidelity%' OR LOWER(col) LIKE '%fine-heart%'

-- MRAs (mineralocorticoid receptor antagonists — drug class)
OR LOWER(col) LIKE '%mineralocorticoid%' OR LOWER(col) LIKE '%spironolactone%'
OR LOWER(col) LIKE '%eplerenone%' OR LOWER(col) LIKE '%esaxerenone%'
OR LOWER(col) LIKE '%nonsteroidal mra%' OR LOWER(col) LIKE '%non-steroidal mra%'

-- SGLT2 inhibitors (key cardiorenal competitors)
OR LOWER(col) LIKE '%empagliflozin%' OR LOWER(col) LIKE '%jardiance%'
OR LOWER(col) LIKE '%dapagliflozin%' OR LOWER(col) LIKE '%farxiga%' OR LOWER(col) LIKE '%forxiga%'
OR LOWER(col) LIKE '%canagliflozin%' OR LOWER(col) LIKE '%invokana%'
OR LOWER(col) LIKE '%sotagliflozin%' OR LOWER(col) LIKE '%ertugliflozin%'
OR LOWER(col) LIKE '%sglt2 inhibit%' OR LOWER(col) LIKE '%sglt-2 inhibit%'
OR LOWER(col) LIKE '%gliflozin%'

-- GLP-1 receptor agonists (overlapping T2D + CV)
OR LOWER(col) LIKE '%semaglutide%' OR LOWER(col) LIKE '%ozempic%' OR LOWER(col) LIKE '%wegovy%'
OR LOWER(col) LIKE '%liraglutide%' OR LOWER(col) LIKE '%victoza%'
OR LOWER(col) LIKE '%dulaglutide%' OR LOWER(col) LIKE '%trulicity%'
OR LOWER(col) LIKE '%tirzepatide%' OR LOWER(col) LIKE '%mounjaro%'
OR LOWER(col) LIKE '%exenatide%' OR LOWER(col) LIKE '%orforglipron%'
OR LOWER(col) LIKE '%glp-1 receptor%'

-- RAAS pathway (standard CKD background therapy)
OR LOWER(col) LIKE '%renin-angiotensin%' OR LOWER(col) LIKE '%raas%'
OR LOWER(col) LIKE '%ace inhibit%' OR LOWER(col) LIKE '%angiotensin receptor%'

-- Endothelin receptor antagonists (emerging CKD)
OR LOWER(col) LIKE '%atrasentan%' OR LOWER(col) LIKE '%zibotentan%'
OR LOWER(col) LIKE '%endothelin%'

-- CKD/cardiorenal therapeutic area terms
OR LOWER(col) LIKE '%cardiorenal%' OR LOWER(col) LIKE '%cardio-renal%'
OR LOWER(col) LIKE '%cardio-kidney%' OR LOWER(col) LIKE '%cardiokidney%'
OR LOWER(col) LIKE '%diabetic kidney%' OR LOWER(col) LIKE '%diabetic nephro%'
OR LOWER(col) LIKE '% dkd %' OR LOWER(col) LIKE '%proteinuria%'

-- Landmark cardiorenal trial names
OR LOWER(col) LIKE '%credence%' OR LOWER(col) LIKE '%dapa-ckd%'
OR LOWER(col) LIKE '%empa-kidney%' OR LOWER(col) LIKE '%emperor%'
OR LOWER(col) LIKE '%dapa-hf%' OR LOWER(col) LIKE '%deliver %'
OR LOWER(col) LIKE '%flow trial%' OR LOWER(col) LIKE '%scored trial%'
```

**Note:** These drug/trial keywords should be combined with the indication patterns using `OR` to form a comprehensive “cardiorenal competitive landscape” filter. This dramatically expands KOL coverage beyond the 118 HCPs found with finerenone-only keywords.

---

## 8. Feature Naming Convention

All Veeva Link features are prefixed `veeva_` to distinguish from claims-based features in the combined model.

```
veeva_{table_group}_{metric}_{window}
```

Examples:
- `veeva_n_pubs_in_scope_5y` — publication count, in-scope, 5-year window
- `veeva_cl_decile_t2d` — clinical leader decile for T2D
- `veeva_speaker_flag_3y` — speaker role at events, 3-year window
- `veeva_publication_index` — INDEX table score (snapshot)

---

## 9. Summary: Feature Count by Category

| Category | Source Tables | Features | Type | Coverage |
|----------|--------------|----------|------|----------|
| A1. Publications | SE_PUBLICATION + PUBLICATION | 8 | Snapshot aggregate (dates used for recency) | 49.2% |
| A2. Clinical Trials | SE_CLINICAL_TRIAL + CLINICAL_TRIAL | 8 | Snapshot aggregate (dates used for active flag) | 11.0% |
| A3. Events | EVENT_ATTENDEE + MEDICAL_EVENT | 5 | Snapshot aggregate | 29.3% |
| A4. Payments | PAYMENT | 8 | Snapshot aggregate (PROGRAM_YEAR for recency) | 39.5% |
| B1. Expert Profile | SCIENTIFIC_EXPERT | 6 | Snapshot attribute | 100% (of joined) |
| B2. Geography | ADDRESS | 3 | Snapshot attribute | ~100% |
| B3. Associations | ASSOCIATION | 4 | Snapshot attribute | 14.3% |
| B4. Sponsorship | COMPANY_SPONSORSHIP | 3 | Snapshot attribute | 7.6% |
| C1. Disease Authority | CLINICAL_LEADER | 5 | Snapshot score | 34.4% |
| C2. Scientific Output | FOCUS_AREA | 3 | Snapshot score | 62.7% |
| C3. Digital Influence | DIGITAL_REACH_FOCUS_AREA | 2 | Snapshot score | 4.2% |
| C4. Index Scores | INDEX | 7 | Snapshot score | 67.7% |
| D. Composites | Multiple | 4 | Mixed | Varies |
| **Total** | **13 tables** | **66 features** | | |

---

## 10. Open Items & Pre-Requisites

1. **Begin archiving monthly Snowflake loads immediately** — each month of delay is a month of score history permanently lost (affects all Tier 3 features)
2. **Confirm COMPANY_COLLABORATION subscription** with Veeva — currently empty, blocks competitor-relationship features
3. **Align table load schedules** — SE was loaded June 2025, children March 2025 (3-month gap creates orphan artifacts)
4. **Backfill SPECIALTY from NPPES** — Veeva SPECIALTY_1 is 61% null; NPPES taxonomy via NPI join fills the gap
5. **Hardcode SCIREACH_MAPPING** — table is missing from warehouse; the 5-value lookup (0=n/a, 1=local, 2=regional, 3=national, 4=global) is stable
6. **Build EVENT_TYPE stop-list** — ~0.3% of MEDICAL_EVENT rows have pipe-delimiter corruption
7. **Normalise PUBLICATION_TYPE** — 81 distinct values including Japanese labels (会議録, 解説, 原著論文, 総説) need mapping to English equivalents
8. **Log-transform or bin activity counts** — publication, trial, and event counts are heavily right-skewed (median=0, max=1,165); raw counts will dominate tree-based models
9. **T1D event features may be unreliable** — only 58 in-scope events across 64 KOLs; consider dropping T1D from event-based features or using an all-indication aggregate only
10. **Validate DATE column type** — PUBLICATION.DATE and MEDICAL_EVENT.START_DATE are VARCHAR, not DATE; all temporal operations need `TRY_TO_DATE()` cast