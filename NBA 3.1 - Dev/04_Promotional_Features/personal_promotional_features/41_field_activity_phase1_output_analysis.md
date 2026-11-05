# Field Activity Phase 1: Output Analysis (NBA 3.1)

**Notebook:** `41_field_activity_phase1_core_features`  
**Plan:** `40_field_activity_nba_3_1_readiness_plan.md` (Phase 1, success criteria S1 – S7, gate G1)  
**Runs analysed:** 3 Nov 2026 (re-run) and 4 Nov 2026 (this folder). Both give the same counts (8,182,383 call records, 3,650,456 HCP-cohort rows, 53 features).  
**Date:** 4 Nov 2026

**How to read this file.** Section 1 is the one-page summary. Section 2 explains the background for a first-time reader. Section 3 explains what the notebook does. Section 4 goes through every expectation: why we expected it (from NBA 3.0), whether it is new, what we got, and what to raise with the client. Sections 5 – 8 list the gate status, issues, client questions and next actions.

---

## 1. Summary

| ID | Expectation (readiness plan) | NBA 3.0 or new | Status | One-line result |
| --- | --- | --- | --- | --- |
| S1 | Count all Kerendia doctor calls: about 660K calls / 104K doctors in Year 2 (NBA 3.0 sees 413K / 84K) | Fixes NBA 3.0 | **Met** | 676,136 calls / 104,752 doctors = 606,239 HCP interactions + 69,897 account / office records; exact match with Phase 0 |
| S2 | One count per interaction; BHO and account / office never counted as HCP activity | Fixes NBA 3.0 | **Met** | 0 duplicate calls; Kerendia-only + co-detail = total on every row; core counts use `HCP_INTERACTION` only |
| S3 | No double counting across blocks (samples, iRep, CLM) | New | **Not in Phase 1 scope** | Phase 1 builds no sample, iRep or CLM features; check again in Phases 3 – 4 |
| S4 | Same columns every run, from a config | New | **Mostly met** | 53 columns generated from config, same count in two runs; formal column-by-column comparison not saved yet (V9) |
| S5 | New block improves the model (E2 vs E0) | New | **Not met (not run)** | Only a count comparison with NBA 3.0 exists; the model experiment E2 has not been run |
| S6 | Every feature is explainable to the field | New | **Partly met** | Names map to field signals; organisation counts are large and co-detail includes unbranded content, both need explanation |
| C1 | Interactions by record type (12 – 16 cols) | Replaces NBA 3.0 call counts | **Met (16)** | F2F 96.7%, group 2.9%, remote 0.4% in Year 2; group and remote 98 – 99% zero |
| C2 | Meal (4 – 6) | Kept from NBA 3.0 | **Met (6)** | Meal on 11 – 14% of Kerendia interactions per month |
| C3 | Product detail and priority (8 – 12) | Revised | **Built (12); low signal in training** | Co-detail under 1% before 2026, 30 – 46% in 2026; training cohorts end Apr 2025 |
| C4 | Recency and regularity (3 – 5) | New | **Met (4)** | Sentinel 999 bug fixed; values valid |
| C5 | Rep coverage and continuity (3 – 4) | New | **Met (4)** | Rep change in 6 months 95.5% zero |
| C6 | Account / office engagement (4 – 6) | New (separate from C1) | **Met (5)**, trend to watch | Share falls from 16.1% (Nov 2024) to 8.9% (Oct 2026) |
| C7 | Organisation context, focal doctor excluded (4 – 6) | Revised (replaces NBA 3.0 BHO) | **Partly met (4)** | Built from call links; top-level BHO calls left out (V3 open) |
| C8 | Trend (1 – 2) | New | **Met (2)** | Defaults valid |
| G1 | Gate after Phase 1 | — | **Not met** | 3 of 4 conditions pass; E2 vs E0 not run |

**Bottom line.** The data part of Phase 1 is solid: every Kerendia doctor call is counted once, the classification matches Phase 0 exactly and an independent Snowflake recompute agrees. What is missing is (1) the model experiment that proves value (E2), (2) training cohorts in 2026, without which the co-detail and Lynkuet behaviour is never seen in training, and (3) client answers on organisation calls, unbranded co-detail and the falling account / office share.

---

## 2. Background for a new reader

1. **What NBA does.** The model scores doctors (HCPs) every cycle and suggests to reps whom to visit. One block of its inputs is **field activity**: what reps did with the doctor in the past (calls, meals, products discussed, ...).
2. **What a call is in Veeva.** A rep logs a call on a doctor. A call can discuss several products ("details"), each with a priority (1 = first). Veeva also writes extra records: a copy of the call on the doctor's organisation (BHO child), account / office calls where no doctor was present, and MSL (medical) calls.
3. **What went wrong in NBA 3.0** (readiness plan, section 3):
   * It kept only calls whose product text was exactly `KERENDIA`. Since Jan 2026, reps detail Kerendia together with Lynkuet, so 40 – 46% of calls each month were lost and about 20,000 called doctors looked "never called".
   * It gave every organisation (BHO) call to every doctor of the organisation, about 80 doctors per call, including the visited doctor. One visit was counted many times.
   * It counted account / office records (no doctor present) as doctor calls: about 10 – 12% of calls.
   * Several features were empty or constant (call length 30 on 97% of calls, phone always 0).
4. **What Phase 1 is.** The first set of NBA 3.1 field features (C1 – C8), built only from data that Phase 0 validated: interaction counts, meals, products, recency, reps, account / office, organisation context, trend. Key messages, samples, events and iRep come later (Phases 2 – 4).
5. **How we judge it.** Success criteria S1 – S6 (section 2 of the plan) and gate G1 (section 8 of the plan).

---

## 3. How the notebook works

| Step | Cell | What it does | Output |
| --- | --- | --- | --- |
| Config | 4 | Paths, windows (1, 3, 6, 12 months = 30, 91, 182, 365 days), record-type map, account / office key messages, medical rules, the list of 53 feature columns | 53 columns configured |
| Cohorts | 5 | Reads 26 cohort anchor dates | C01 (2023-03-17) to C26 (2025-04-16) |
| 1a | 6 | Loads submitted calls since 2022 and product detail rows from Snowflake | 9,703,442 call x product rows |
| 1b | 7 | `field_interaction`: one row per call with one class (`HCP_INTERACTION`, `ACCOUNT_OFFICE`, `BHO_CHILD`, `BHO_TOP_LEVEL`, `MEDICAL`) and product flags (Kerendia, co-detail, Kerendia first, meal) | 8,182,383 calls, 0 calls with two doctors |
| 1c | 8 | Class counts, Year 2 reconciliation, record types, monthly shares | see section 4 |
| 1d | 9 | `field_org_link`: links a doctor call to its organisation (BHO child of the call, or the doctor attended a BHO group call) | about 1 organisation per linked call |
| 2a | 10 | Attaches each event to every cohort whose 12-month lookback contains it; leakage check | passed |
| 2b – 2d | 11 – 13 | Builds C1 – C8 per doctor and cohort, fills defaults, enforces the fixed schema | 3,650,456 rows x 53 features |
| G1 checks | 14 – 16 | 22 rule checks, profile by cohort, independent Snowflake recompute for 10 doctors | all pass |
| E0 reference | 17 | Compares NBA 3.1 face-to-face counts with the NBA 3.0 call output | ratio 84 – 88% |
| Co-detail check | 18 | Which products share a call with Kerendia | see C3 |

---

## 4. Expectation by expectation

### S1 — Full coverage of Kerendia doctor calls

* **Why we expect this.** NBA 3.0 filtered on the product text `KERENDIA`, so calls with Kerendia and Lynkuet disappeared. The data review counted about 660K Kerendia doctor calls and 104K doctors in Year 2, against 413K / 84K in NBA 3.0.
* **NBA 3.0 or new.** Fix of an NBA 3.0 problem. The Kerendia rule now comes from the product detail rows (any detail = Kerendia).
* **What we got.**

| Year 2 (Nov 2025 – Oct 2026) | Calls | Doctors |
| --- | --- | --- |
| HCP interactions | 606,239 | 96,610 |
| Account / office records | 69,897 | 27,280 |
| **Total** | **676,136** | **104,752** |
| Review target | about 660K | about 104K |
| NBA 3.0 | 413K | 84K |

  NBA 3.1 sees 64% more Kerendia doctor records and about 20,700 more doctors than NBA 3.0, which matches the "about 20,000 doctors look never called" finding. Kerendia is detailed first on 86 – 93% of 2026 interactions (review: 87 – 92%).
* **Status.** Met.
* **Raise with client.** Confirm that the target is restated as about 606K HCP interactions plus about 70K account / office records (Phase 0 question C1). Reason: the review figure of 660K mixed the two.
* **Suggestions.** Keep the Year 2 reconciliation in the notebook as a standing check.

### S2 — One count per interaction

* **Why we expect this.** NBA 3.0 counted the same visit several times (BHO copies to about 80 colleagues) and counted visits with no doctor present.
* **NBA 3.0 or new.** Fix of an NBA 3.0 problem (design principles 1 and 3).
* **What we got.**
  * Every call ID appears once; no call is attached to two doctors.
  * Rule "Kerendia-only + co-detail = total" holds on all 3.65M rows, so a co-detail call is one interaction, not two.
  * Core counts (C1 – C5, C8) read only `HCP_INTERACTION`. Account / office feeds only C6. BHO records feed only C7. Medical records feed nothing.
* **Status.** Met.
* **Raise with client.** Nothing new.
* **Suggestions.** Add an explicit check that the focal doctor's own calls are not in his organisation counts (see C7).

### S3 — No double counting across blocks

* **Why we expect this.** In NBA 3.0, samples existed in two blocks (call block and market access block).
* **NBA 3.0 or new.** New rule.
* **What we got.** Phase 1 builds no sample, iRep or CLM features (a sample flag exists in `field_interaction` but is not an output).
* **Status.** Not applicable to Phase 1; check in Phases 3 – 4.

### S4 — Stable schema

* **Why we expect this.** NBA 3.0 columns depended on which values existed in the data, so the column list could change between runs.
* **NBA 3.0 or new.** New (principle 10).
* **What we got.** The 53 columns come from one config function; missing values are filled with fixed defaults (0, 999 for "days since", 365 for median gap, 1.0 for the trend ratio). The 3 Nov and 4 Nov runs both produce 57 fields (53 features + 4 keys).
* **Status.** Mostly met. The plan asks for "two runs produce identical columns"; the column count matches but the full list of names was not saved and compared.
* **Suggestions.** Save the column list as JSON at the end of each run and compare with the previous one (action A7 from Phase 0).

### S5 — Model value

* **Why we expect this.** A cleaner block is only worth it if the model is at least as good.
* **NBA 3.0 or new.** New.
* **What we got.** The notebook compares counts with NBA 3.0 (cell 17) but does not train a model. E2 has not been run.

| Cohort | NBA 3.0 F2F 6 months | NBA 3.1 F2F 6 months | Ratio |
| --- | --- | --- | --- |
| C01 (Mar 2023) | 287,017 | 241,924 | 84.3% |
| C10 (Dec 2023) | 304,228 | 268,997 | 88.4% |
| C20 (Oct 2024) | 280,869 | 235,375 | 83.8% |
| C26 (Apr 2025) | 243,406 | 213,094 | 87.5% |

  In the training cohorts NBA 3.1 counts **fewer** face-to-face calls than NBA 3.0. This is expected: these cohorts end before 2026, when the co-detail loss did not exist yet, and the gap (12 – 16%) is close to the account / office share of Kerendia doctor records in the lookback months (about 12 – 20% per month in 2022 – 2025), which NBA 3.0 counted as visits. From 2026 the direction reverses: NBA 3.1 counts more because NBA 3.0 loses the Kerendia + Lynkuet calls.
* **Status.** Not met: E2 not run.
* **Raise with client (modelling team).** Agree the validation metric and split for E0 vs E2.
* **Suggestions.** Run E2 now; it is the last missing G1 condition.

### S6 — Explainable to the field

* **Why we expect this.** NBA 3.0 drivers (for example `BHO_TOTAL_F2F_...` in the millions, call length 30) could not be explained to a rep.
* **NBA 3.0 or new.** New.
* **What we got.** All 53 names map to a field signal. Two features need care: organisation colleague interactions average 16 – 27 in 6 months, about 11 times the doctor's own count, and co-detail before 2026 is mostly "Cardiovascular Unbranded" content.
* **Status.** Partly met.
* **Raise with client (Field Analytics).** Review driver wording for C3 and C7.
* **Suggestions.** Express organisation context as "colleagues visited" or a per-colleague rate rather than a raw total.

### C1 — HCP interactions by record type (16 columns)

* **Why we expect this.** Field Analytics uses face-to-face activity first. NBA 3.0 used record-type patterns that only match the old Veeva names; the new names (from mid-2025) would read 0.
* **NBA 3.0 or new.** Replaces NBA 3.0 call counts; old and new record-type names are both mapped.
* **What we got.**

| Period | F2F | Group | Remote | Other |
| --- | --- | --- | --- | --- |
| 2022 | 463,516 | 8,252 | 17,685 | 1,616 |
| Year 1 | 462,308 | 7,644 | 2,036 | 248 |
| Year 2 | 586,315 (96.7%) | 17,601 (2.9%) | 2,323 (0.4%) | 0 |

  "Other" is 0 in Year 2, so the map covers all current record types. Group calls more than doubled in Year 2. Remote fell sharply after 2022. Group and remote are 0 for 98.3 – 99.9% of doctor-cohort rows.
* **Status.** Met.
* **Raise with client (Field Analytics).** Are group and remote calls worth separate features, or one "non face-to-face" count? Reason: they are rare, and the 1- and 3-month versions are almost always 0.
* **Suggestions.** Keep all columns in the schema; let feature selection decide; consider a merged non-F2F feature.

### C2 — Meal (6 columns)

* **Why we expect this.** Meals are a field-recognised signal kept from NBA 3.0 (PF-4).
* **NBA 3.0 or new.** Kept from NBA 3.0, now on the interaction grain.
* **What we got.** Meal on 11 – 14% of Kerendia interactions per month; average meal interactions in 6 months fell from 0.31 (2023 cohorts) to 0.20 – 0.23 (2024 – 2025 cohorts). Meal in 12 months 82% zero. The Snowflake recompute matches meal counts exactly.
* **Status.** Met.

### C3 — Product detail and priority (12 columns)

* **Why we expect this.** From 2026 reps detail Kerendia together with Lynkuet. A visit where Kerendia is second probably carries less Kerendia message. NBA 3.0 could not see these calls at all.
* **NBA 3.0 or new.** Revised (PN-2). Columns: Kerendia-only, co-detail and Kerendia-first counts (3, 6, 12 months), Kerendia-first share (6, 12 months), and a co-detail period flag (cohort ends on or after 1 Jan 2026).
* **What we got.**

| Year | Kerendia interactions | Co-detail | Share |
| --- | --- | --- | --- |
| 2023 | 529,567 | 920 | 0.17% |
| 2024 | 475,811 | 4,650 | 0.98% |
| 2025 | 483,561 | 4,675 | 0.97% |
| 2026 | 533,256 | 237,038 | 44.45% |

  2024 co-detail partners: Cardiovascular Unbranded 2,842 calls (61%), Adempas 1,424, Nubeqa 244, Mirena 137, Kyleena 136, Skyla 45, Xofigo 6. On 82% of 2024 co-detail calls the other product was detailed first. 2025 includes 276 calls with "Elinzanetant", Lynkuet's generic name. 2026: Lynkuet 233,845 calls. Cross-check against the call header text gave identical counts.

  In the training cohorts co-detail is 99.4 – 99.7% zero, the period flag is 0 for every row, and Kerendia-only / Kerendia-first are almost the same as total interactions.
* **Status.** Built correctly, but no training signal until 2026 cohorts exist.
* **Raise with client.**
  * Field Analytics: should "Cardiovascular Unbranded" (disease-awareness content) count as co-detail? Reason: it is 61% of pre-2026 co-detail; excluding it would reclassify those visits as Kerendia-only.
  * Field Analytics / sales operations: are Nubeqa and women's health products with Kerendia expected (reps covering several portfolios)?
  * Modelling team: can cohorts be extended past January 2026 (Phase 0 question C6)? Reason: without them, the model never trains on the co-detail period it will be used in.
* **Suggestions.** Decide the unbranded rule in config; map Elinzanetant to Lynkuet if a Lynkuet-specific feature is added; document the period flag as "Lynkuet co-promotion period" (Adempas co-detail existed from April 2024).

### C4 — Recency and regularity (4 columns)

* **Why we expect this.** NBA 3.0 had only 90-day and 1-year totals, no recency or regularity.
* **NBA 3.0 or new.** New (PN-3).
* **What we got.** Days since last interaction uses 999 when there is no interaction in 12 months (fixed bug: it used 0 for 1.8M rows). Active months bounded (6 and 12). Median gap uses 365 when fewer than 2 dates.
* **Status.** Met.
* **Suggestions.** Tree models handle the 999 sentinel; for linear models add a "no interaction" flag.

### C5 — Rep coverage and continuity (4 columns)

* **Why we expect this.** Rep changes and multi-rep coverage were requested by Field Analytics and not in NBA 3.0.
* **NBA 3.0 or new.** New (PN-5).
* **What we got.** Average reps in 6 months 0.43 – 0.47 per doctor-cohort (about 1.1 for doctors actually visited). Rep change in 6 months is 95.5% zero.
* **Status.** Met; rep change is a weak signal.
* **Raise with client (Field Analytics).** The 2025 – 2026 field reorganisation (strikers, growth to about 650 – 690 reps) will shift these features in later cohorts. Reason: plan risk table.
* **Suggestions.** Check that the rep ID (`SOURCE_EMP_ID`) is filled on all interactions; consider a relative measure per territory.

### C6 — Account / office engagement (5 columns)

* **Why we expect this.** NBA 3.0 mixed these records into doctor calls; Field Analytics asked to keep them as their own signal (decision D2).
* **NBA 3.0 or new.** New, separate from C1.
* **What we got.** Identified from five key-message codes. Share of Kerendia doctor records:

| Period | Account / office share |
| --- | --- |
| Nov 2024 – Dec 2025 (monthly) | 11.8 – 16.1% |
| Jan – Oct 2026 (monthly) | 8.9 – 11.1% |
| Year 2 total | 10.3% |

  Average account / office records in 6 months 0.28 – 0.39; 78% zero at 12 months. Snowflake recompute matches.
* **Status.** Met, but the steady decline needs explanation.
* **Raise with client (Field Analytics).** Why does the account / office share fall from 16% to 9%: fewer office visits, or reps using the codes less? Are the five codes used consistently (Phase 0 C2)? Reason: plan risk "classification depends on key-message codes".
* **Suggestions.** Keep the monthly share report; recheck after the client answer.

### C7 — Organisation context, focal doctor excluded (4 columns)

* **Why we expect this.** NBA 3.0 spread each BHO call to about 80 doctors including the visited one. NBA 3.1 keeps organisation context but counts only colleagues' activity.
* **NBA 3.0 or new.** Revised (PF-2). Doctors are linked to organisations from call data, not from master-data affiliations.
* **What we got.** About 1 organisation per linked doctor call each year (2022 – 2026); 86.1% of doctor-cohort rows have an organisation link; colleague interactions in 6 months average 16 – 27 (59.7% zero). The planned top-level organisation call feature is not built.
* **Status.** Partly met.
* **Raise with client (CRM team, Phase 0 questions B1 – B6).** Are BHO children always automatic copies? What is a top-level organisation call? Should "doctors of an organisation" follow master data (NBA 3.0) or call data (NBA 3.1)? Reason: decides whether 216,069 top-level records enter C7 and who receives context.
* **Suggestions.** Treat the 7,096 BHO children with an empty parent ID as top-level (the empty text currently looks like a parent); add a test that a doctor's own calls are never in his colleague counts; consider capping or normalising very large organisations.

### C8 — Trend (2 columns)

* **Why we expect this.** Rising or falling contact is a natural rep signal; not in NBA 3.0.
* **NBA 3.0 or new.** New.
* **What we got.** Last 3 months minus prior 3 months (66.9% zero) and their ratio (default 1.0 when both are 0).
* **Status.** Met.

---

## 5. Gate G1

| G1 condition (plan, section 8) | Status | Evidence |
| --- | --- | --- |
| Core block built for all training instances | Pass | 26 cohorts, 3,650,456 rows, 53 features, 0 nulls, 0 duplicate keys |
| Leakage check passed | Pass | All events within the 12 months before the anchor date |
| Account / office and BHO excluded from core counts | Pass | Core events filtered to `HCP_INTERACTION` with Kerendia detail |
| E2 run and compared with E0 | **Fail (not run)** | Only a count comparison exists |

Additional evidence: 22 rule checks pass (nested windows, sub-counts within totals, bounds, sentinels, shares between 0 and 1); 10 doctors recomputed directly in Snowflake match on 4 features, on two runs with different samples.

**G1 is not met** until E2 is run. The readiness plan status paragraph ("G1 passed, 3 Nov 2026") should be corrected.

---

## 6. Issues found

| # | Issue | Effect | Fix |
| --- | --- | --- | --- |
| P1 | E2 not run | S5 and G1 open | Run E0 vs E2 |
| P2 | Training cohorts end Apr 2025 | Co-detail, Lynkuet and 2026 priority patterns never seen in training; drift at inference | Extend cohort anchors (needed for E6) |
| P3 | 14 of 53 features are more than 95% zero in training (group and remote 1 – 12 months, co-detail 3 – 12 months, period flag, meal 1 month, rep change) | Little signal, noise in feature selection | Keep in schema; merge or drop at selection |
| P4 | Kerendia-only and Kerendia-first are almost equal to total before 2026 | Redundant features | Correlation check; recheck on 2026 cohorts |
| P5 | Empty-text parent IDs on 7,096 BHO children | Wrong BHO class | Treat empty as missing in step 1b |
| P6 | Top-level BHO calls not built | C7 incomplete | Wait for V3 |
| P7 | Account / office share falling 16% to 9% | C6 may reflect coding habits | Client question; monthly monitoring |
| P8 | Statements in the notebook results cell: "co-detail 0 for all cohorts" (it is under 1%, not 0), "F2F ~84% of NBA 3.0" (84 – 88%), "account / office monthly range 10.9 – 19.8%" (2022 months only), "intermediate parquet writes removed" (the detail table is still written) | Misleading summary | Correct the cell and the plan status |
| P9 | Column list not saved and compared between runs | S4 / V9 not formally closed | Save and compare a schema JSON |

---

## 7. Questions to send to the client

| # | Question | Team | Blocks |
| --- | --- | --- | --- |
| Q1 | Confirm the Year 2 target as about 606K HCP interactions + about 70K account / office records | Field Analytics | S1 |
| Q2 | Should "Cardiovascular Unbranded" count as co-detail with Kerendia? | Field Analytics | C3 |
| Q3 | Are Nubeqa, Mirena, Kyleena, Skyla co-details with Kerendia expected (multi-portfolio reps)? | Field Analytics, sales operations | C3 |
| Q4 | Why does the account / office share fall from 16% (Nov 2024) to 9% (Oct 2026)? Are the five codes used consistently? | Field Analytics | C6 |
| Q5 | Can training cohorts be extended past January 2026? | Modelling team | C3, E6 |
| Q6 | Validation metric and split for E0 vs E2 | Modelling team | S5, G1 |
| Q7 | BHO questions B1 – B6 (copies, top-level calls, membership definition) | CRM team | C7 |
| Q8 | Keep group and remote as separate features, or merge? | Field Analytics | C1 |
| Q9 | How will the 2025 – 2026 field reorganisation be reflected in rep features? | Field Analytics | C5 |

---

## 8. Next actions

| # | Action | Closes | Owner |
| --- | --- | --- | --- |
| N1 | Run E2 vs E0 with the NBA 3.1 model | S5, G1 | NBA team, modelling team |
| N2 | Extend cohort anchors past Jan 2026 and re-run | P2, E6 | Modelling team |
| N3 | Save and compare the schema between two runs | S4, V9 | NBA team |
| N4 | Treat empty `PAR_CALL_ID` as missing | P5 | NBA team |
| N5 | Add a focal-doctor exclusion test for C7 | S2, C7 | NBA team |
| N6 | Correlation and sparsity review of the 53 features | P3, P4 | NBA team |
| N7 | Correct the results cell and the readiness plan status | P8 | NBA team |
| N8 | Send Q1 – Q9 and update rules (unbranded, Elinzanetant, top-level BHO) | C3, C6, C7 | NBA team |
