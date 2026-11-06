# High-Intent Signal Features (Family 3): Client Summary, NBA 3.1

**Audience:** Kerendia brand, analytics, OE and field-operations teams  
**Notebook:** `High_Intent_Signal_Features/25_Features_High_Intent_Signals_NBA31`  
**Based on:** section 3.3 of `52_digital_feature_families_nba30_vs_nba31.md`, the notebook code and its run on 6 November 2026  
**Date:** 6 November 2026

---

## Summary in one page

* **What is new.** NBA 3.0 had **no** high-intent features. NBA 3.1 adds a family for the moments when a doctor shows clear interest in Kerendia: they **ask for a rep** (Request-a-Rep form), they **start prescribing** (New Writer), or they **react to an SMS** (Impiricus).
* **What was built.** **28 features** on **294,726 HCPs x 28 monthly cohorts** (c1 to c28): 18 Request-a-Rep, 5 New Writer, 5 SMS. A **business-rule list** of doctors with an open request is also produced (49 HCPs at the latest cohort end, 17 Sep 2026).
* **Decisions applied.** A request counts as open for at most **90 days**. A **new writer** is the **first month with a Kerendia prescription**.
* **Main open point.** Of the 1,385 Kerendia requests, only **612 link to an HCP in the NBA 3.1 universe**. 722 carry new Bayer IDs (BH_IDs) that are not yet in the BH_ID mapping table. A mapping refresh is needed to recover them.
* **Not built.** Health-system formulary wins (source not found).

---

## 1. Types of high-intent features and the business rationale

| Type | What it captures | Source | Business rationale |
| --- | --- | --- | --- |
| **A. Request-a-Rep (RAR), all requests** | The doctor filled in the form on a Kerendia HCP website ("send me samples", "have a rep contact me", ...) | Snowflake `PHCDW.PHCDW_CDM.RPT_DIGITAL_RAR_TAB` | A doctor asking for contact is the **clearest signal of interest that exists**. It is direct and doctor-initiated, unlike exposure to media. |
| **B. RAR by follow-up type** | Whether Bayer answered the request with a **call, sample, iRep email or HQ email**, and whether the request is still open | Same table, follow-up columns | Only **29.7%** of Kerendia requests were followed by a call. An unanswered request is both an **opportunity** (the doctor is waiting) and a **risk** (interest fades). Separating "asked" from "answered" lets NBA prioritise open requests. |
| **C. New Writer** | The doctor wrote Kerendia for the **first time** recently | HCP x month Kerendia claims (`kerendia_claims_monthly_from_raw_fct_rx`) | The first prescriptions are the moment to **reinforce adoption** (support, samples, patient-access help) so the new writer becomes a repeat writer. |
| **D. Impiricus SMS** | The doctor received and engaged with a Kerendia SMS | MMX table, vendor `IMPIRICUS`, tactic `SMS` | Responding to a text is an active, personal signal of attention. |
| **E. Health-system formulary win** | Kerendia added to a health system's formulary, linked to its affiliated doctors | **Not located** | A formulary win removes an access barrier: a strong trigger to tell affiliated doctors. **Not built** (see section 5). |

Why the business rule as well as features: Request-a-Rep events are rare (about 1,200 doctors against a universe of almost 300,000), so a model alone may not learn them reliably. NBA therefore also **always shows** doctors with an open request in the dropdown list, with the reason "Requested a rep on <date>".

---

## 2. Step-by-step feature creation, with the business rules

### 2.1 Common steps (all types)

| Step | What happens | Business rule |
| --- | --- | --- |
| 1. Configuration | Sources, windows (3 / 6 / 12 months), the 90-day open rule and default values are set in one cell. | All rules in one place, applied the same way at every run. |
| 2. Cohorts | Reads the 28 NBA 3.1 promotional cohorts (`cohorts/promotional/cohorts.parquet`). Every cohort's lookback ends on the **17th** (c1 = 17 Jun 2024, c28 = 17 Sep 2026). | Same time frame as all other NBA 3.1 promotional features. |
| 3. HCP universe | Loads the NBA 3.1 HCP universe (294,726 `PROVIDER_ID`s, placeholder `0` removed). | Features only for doctors the model scores. |
| 4. ID mapping | `BH_ID` and `NPI` mapped to `PROVIDER_ID` with `kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING` (universe only; if one ID points to several `PROVIDER_ID`s, the smallest is kept). Only 10-digit NPIs are used. | One doctor key across NBA 3.1; each event counted once. |
| 5. Data history | `RAR_HISTORY_MONTHS` and `MMX_HISTORY_MONTHS` (0 to 12) record how much history each cohort has. RAR and SMS start in January 2025. | The model can tell "no request" from "no data yet" (2024 cohorts). |

### 2.2 Type A and B: Request-a-Rep

| Step | What happens | Business rule |
| --- | --- | --- |
| A1. Load | Reads Kerendia rows (`BRAND_NAME` contains `KERENDIA`) from Snowflake: request ID, doctor IDs, request date, request type, mastered flag and follow-up dates. | **No personal data is read** (name, email, phone, address). The raw `TRANSACTION_ID` contains the requester's email and name, so it is **hashed (SHA-256) inside Snowflake** before it reaches Databricks. |
| A2. One row per request | Checks that each request ID is unique (1,385 requests). For each follow-up type, keeps the first follow-up dated **on or after** the request. | A follow-up dated before the request is not a response to it. |
| A3. Link to the doctor | `BH_ID` first, then `NPI` as a fallback. Requests that reach no universe HCP are reported. | 530 linked by BH_ID, 82 by NPI, 773 not in the universe (see section 6). |
| A4. Count requests per cohort | Requests in the last 3 / 6 / 12 months before the cohort end; days since the last request. | Window = (cohort end - w months, cohort end]. A request after the cohort end is never used. |
| A5. Follow-up per type | For **call, sample, iRep email, HQ email**: number of requests in 12 months answered by that type, and the share of requests answered. | **Leakage rule:** a follow-up counts only if its date is **on or before the cohort end**. A call made after the cohort end does not mark the request as answered. |
| A6. Open requests | Flag if a request from the **last 90 days** has no follow-up by the cohort end (any type, and separately: no call, no sample). | **Decision:** a request counts as open for at most 90 days. Older unanswered requests are treated as expired. |
| A7. Request type | Flags if a request in 12 months mentions **Samples** or **Contact by Rep**. | What the doctor **asked** for is kept separate from what the rep **did**. |
| A8. Business-rule list | Doctors with an open request and no call at the latest cohort end, with the reason "Requested a rep on <date>". | Always shown in the NBA dropdown. 49 HCPs at 17 Sep 2026. |

Kerendia request types and follow-up (all 1,385 requests, any follow-up date):

| Request type | Requests | Followed by a call | Followed by a sample |
| --- | --- | --- | --- |
| Samples | 581 | 305 | 225 |
| Contact by Rep | 520 | 36 | 15 |
| Empty | 188 | 59 | 31 |
| News & Announcements | 54 | 6 | 1 |
| Other | 42 | 5 | 2 |

Total follow-ups: call 411, sample 274, iRep email 10, HQ email 0 (the HQ columns are empty in the source).

### 2.3 Type C: New Writer

| Step | What happens | Business rule |
| --- | --- | --- |
| C1. Load | Reads the HCP x month Kerendia claims table (from raw FCT_RX), July 2021 (launch) to October 2026. Checks there is one row per HCP and month. | **Not** the LAAD v6 table, as agreed. |
| C2. First month | For each HCP, the first month with a Kerendia prescription (`TRX_KERENDIA_OVERALL > 0`). 84,389 universe HCPs have written Kerendia. | **Decision:** a new writer is the first month with a Kerendia prescription. |
| C3. Complete months only | For each cohort, only months that are **fully before** the cohort end are used. For c28 (ends 17 Sep 2026), the latest month used is August 2026. | The month that holds the cohort end also has claims after the 17th; using it would leak future data. |
| C4. Features | New-writer flags (first month in the last 3 / 6 / 12 complete months), ever-writer flag, months since the first prescription. | |

### 2.4 Type D: Impiricus SMS

| Step | What happens | Business rule |
| --- | --- | --- |
| D1. Load | MMX rows with a Kerendia brand value, vendor `IMPIRICUS`, tactic containing `SMS`; NPI mapped to `PROVIDER_ID`. | Same MMX source and brand rule as the Digital Engagement family. |
| D2. Features | SMS sent (3 / 12 months), engaged flags (3 / 12 months), days since the last SMS. | Same windows as RAR. |

SMS data exists only in Mar, Apr, Jun, Nov and Dec 2025 (248 to 5,046 HCPs a month) and is **zero in 2026**.

### 2.5 Quality checks built in

* **Known-answer self-test** on hand-made cases: window edges (exactly 12 months back is excluded), a call dated after the cohort end (not counted, request still open), a request after the cohort end (ignored), a partial month for New Writer (ignored). **Passed.**
* **Independent cross-checks.** New writers in the last 3 months recomputed with a separate SQL query: **6,135 (c28) and 3,829 (c1), the same as the notebook**. The open-request list (49 HCPs) matches the open-no-call flag total for c28 (49).
* **QC cell** (to run with the output write): fixed schema, row count = universe x cohorts, unique IDs, nested windows, follow-ups never above requests, no RAR before 2025, and a pandas recompute of the RAR counts.

---

## 3. Cross join with the monthly cohorts (HCP x cohort level)

**Done.** Every HCP in the universe is crossed with every cohort, so each HCP has one row per cohort: **294,726 x 28 = 8,252,328 rows**.

* Each event (request, first prescription, SMS) is crossed with the 28 cohorts and kept only for cohorts whose end date is on or after the event. The windows are then measured back from each cohort's end date.
* Results are joined to the full HCP x cohort grid. HCPs with no event get **0** for counts and flags, **999** for days / months since ("never"), and **NULL** for shares (no request, so no share).
* Key: `HCP_COHORT_ID` = `PROVIDER_ID` + `_` + `COHORT`, plus `DATASET` (Training / Testing / Holdout), `PREDICTION_MONTH` and `SVC_DT` (cohort end).

How the signals build up over the cohorts:

| Cohort | Cohort end | RAR history (months) | Requests, last 12M | With call | With sample | HCPs open, no call | New writers, last 3M | Ever writers | HCPs SMS-engaged, 12M |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| c1 | 17 Jun 2024 | 0 | 0 | 0 | 0 | 0 | 3,829 | 38,596 | 0 |
| c8 | 17 Jan 2025 | 0 | 9 | 1 | 0 | 8 | 3,988 | 48,030 | 0 |
| c14 | 17 Jul 2025 | 6 | 110 | 66 | 49 | 24 | 4,190 | 56,407 | 94 |
| c20 | 17 Jan 2026 | 12 | 247 | 150 | 105 | 43 | 5,463 | 66,489 | 141 |
| c24 | 17 May 2026 | 12 | 321 | 187 | 133 | 49 | 5,738 | 74,038 | 103 |
| c28 | 17 Sep 2026 | 12 | 421 | 259 | 167 | 49 | 6,135 | 82,061 | 48 |

Status: the grid is built and checked in the notebook; the **write to the output file and the QC cell have not yet been run** (output folder `kerendia_nba_3_1_volume/notebook_output/high_intent_signals_nba_3_1/`).

---

## 4. Features created, with examples and business meaning

| Type | Feature | Business meaning |
| --- | --- | --- |
| A. RAR all (8) | `RAR_COUNT_3M`, `RAR_COUNT_6M`, `RAR_COUNT_12M` | How often the doctor asked for contact recently. Repeat requests mean strong or unmet interest. |
| | `RAR_LAST_6M_FLAG` | The doctor asked at least once in the last 6 months. |
| | `DAYS_SINCE_LAST_RAR` | How fresh the interest is (999 = no request in 12 months). |
| | `RAR_OPEN_REQUEST_FLAG` | A request from the last 90 days has had **no follow-up of any kind**: the doctor is waiting. |
| | `RAR_TYPE_SAMPLES_FLAG` | The doctor asked for **samples**: ready to try Kerendia with patients. |
| | `RAR_TYPE_CONTACT_BY_REP_FLAG` | The doctor asked to **talk to a rep**: wants information or a conversation. |
| B. RAR + Call (3) | `RAR_CALL_COUNT_12M`, `RAR_CALL_SHARE_12M` | How many requests (and what share) a rep answered with a call. |
| | `RAR_OPEN_NO_CALL_FLAG` | A request from the last 90 days with **no call yet**: the main trigger for the NBA dropdown rule. |
| B. RAR + Samples (3) | `RAR_SAMPLE_COUNT_12M`, `RAR_SAMPLE_SHARE_12M`, `RAR_OPEN_NO_SAMPLE_FLAG` | Requests answered with samples, and requests still waiting for one. |
| B. RAR + iRep (2) | `RAR_IREP_COUNT_12M`, `RAR_IREP_SHARE_12M` | Requests answered by an iRep email (very rare today: 10 in total). |
| B. RAR + HQ (2) | `RAR_HQ_COUNT_12M`, `RAR_HQ_SHARE_12M` | Requests answered by an HQ email (always 0 until the source fills these columns; kept so the schema stays fixed). |
| C. New Writer (5) | `NEW_WRITER_LAST_3M_FLAG`, `_6M_FLAG`, `_12M_FLAG` | The doctor wrote Kerendia for the first time in the last 3 / 6 / 12 complete months: an adoption moment to reinforce. |
| | `KERENDIA_WRITER_EVER_FLAG` | The doctor has ever written Kerendia (since launch). |
| | `MONTHS_SINCE_FIRST_KERENDIA_RX` | How long the doctor has been a Kerendia writer (0 = first month is the latest complete month; 999 = never). |
| D. SMS (5) | `SMS_SENT_3M`, `SMS_SENT_12M` | How many Kerendia SMS the doctor received. |
| | `SMS_ENGAGED_3M_FLAG`, `SMS_ENGAGED_12M_FLAG` | The doctor reacted to an SMS: open to this channel. |
| | `DAYS_SINCE_LAST_SMS` | How recent the SMS contact was. |
| Context | `RAR_HISTORY_MONTHS`, `MMX_HISTORY_MONTHS` | Complete months of source history before the cohort end (0 to 12), so "no data yet" is not read as "no interest". c8 shows 0 because its window holds only 17 days of 2025 data. |

---

## 5. Next steps for features not created (or not yet complete)

| Item | Status | Next step |
| --- | --- | --- |
| **Health-system formulary win** (`FORMULARY_WIN_AFFIL_6M_FLAG`) | Not built: source not found | Digital / OE team to provide the source and format; link health systems to doctors via MDM best affiliation. |
| **722 requests with unmapped BH_IDs** | Features built without them | Refresh `SOURCE_PROVIDER_BHID_NPI_MAPPING` (or provide a newer BH_ID source), then rerun. This would roughly double the requests in the features. |
| **RAR history before 2025** | Not used | `KERENDIA_HCP_RAR_EXTRACTS` holds raw requests from January 2024. Loading it would give RAR history to cohorts c1 to c7 (none today) and c8 (only 17 days today). |
| **SMS for 2026** | Built, but all zero for 2026 | Confirm where 2026 Impiricus data lands; drop or replace the SMS features if the channel has stopped. |
| **HQ email follow-up** | Built, always 0 | Ask the table owner to fill the HQ follow-up columns; review the iRep and HQ features after the first model run. |
| **Open-request list for the NBA dropdown** | Shown in the notebook, not saved | Agree the output format with the NBA front-end and save it at each run. |
| **Output write and QC** | Code ready, not yet run | Run the write and QC cells; then join the features to the NBA 3.1 HCP feature table. |

---

## 6. Client alignment needed

| # | Topic | Question for the client | Current choice |
| --- | --- | --- | --- |
| 1 | Open-request window | Confirmed: a request is open for at most 90 days. | **Decided** (90 days). |
| 2 | New Writer definition | Confirmed: the first month with a Kerendia prescription. Should the prescription measure be **all claims** (incl. rejected / reversed) or **paid / approved only**, or new-to-brand Rx (NBRx)? | **Decided** on first month; uses all claims (`TRX_KERENDIA_OVERALL`). Measure to confirm. |
| 3 | Business rule | Is "open" for the dropdown = **no call** (as in the design), or **no follow-up of any kind** (call, sample, email)? | No call. |
| 4 | "Contact by Rep" requests | Only 36 of 520 (about 7%) were followed by a call. Is the call logged without a link to the request, or are these requests really unanswered? | Ask the table owner. |
| 5 | Request type quality | `REQUEST_TYPE` can hold several values in one text, and `REP_TYPE` sometimes holds request-type text (about 115 rows). Can the owner fix this? | Text search for "samples" / "contact by rep". |
| 6 | Back-loaded history | The RAR table was created on 15 Sep 2026 and the 2025 history loaded in one go. Do the follow-up dates show what was known at the time? | Follow-ups counted only if dated on or before the cohort end. |
| 7 | Requests outside the universe | 44 requests come from mapped doctors who are not in the NBA 3.1 universe. Should they be added, or ignored? | Ignored. |
| 8 | Monthly claims location | The monthly claims table is in `hcp_level_model/dev_pipeline/...`, not `ops_pipeline/...`. Which location is the production source? | `dev_pipeline`. |
| 9 | Personal data | The RAR `TRANSACTION_ID` contains the requester's email and name. Confirm that hashing it inside Snowflake is acceptable. | Hashed (SHA-256). |

---

## 7. Data sources missing or incomplete

| Source | Issue | Impact |
| --- | --- | --- |
| Health-system formulary wins | **Not located** | No formulary-win features. |
| BH_ID mapping for new IDs | 722 Kerendia requests have BH_IDs (BH49... / BH50...) missing from `SOURCE_PROVIDER_BHID_NPI_MAPPING`; the OE BH_ID mapping adds none; only 49 of them have a valid NPI, and those NPIs are not in the mapping either | 56% of requests (773 of 1,385, incl. 44 outside the universe and 7 with no ID) cannot reach an HCP. |
| Impiricus SMS 2026 | No MMX rows after December 2025 | SMS features are zero for 2026 cohorts. |
| RAR HQ email follow-up | `SENT_HQ`, `HQ_EMAIL_SENT_DATE` and related columns are empty | HQ follow-up features are always 0. |
| RAR history before 2025 | `RPT_DIGITAL_RAR_TAB` starts on 1 Jan 2025; earlier history exists only in `KERENDIA_HCP_RAR_EXTRACTS` (not loaded) | Cohorts c1 to c7 have no RAR history; c8 has only 17 days. |
| Other RAR columns | `REQUEST_DETAILS`, `WEBFORM_SOURCE` and `CLICKED_IREP` are empty | No detail on what was asked or how the doctor reached the form. |
