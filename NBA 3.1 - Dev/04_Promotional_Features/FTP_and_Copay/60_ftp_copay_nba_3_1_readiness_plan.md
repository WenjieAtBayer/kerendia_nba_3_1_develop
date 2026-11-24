# FTP and Copay: NBA 3.1 Readiness Plan

**Group:** Market access promotional features (Free Trial Program, copay card)  
**Purpose:** a step-by-step plan to turn the FTP and copay Unity Catalog claims tables into a clean, validated and tested feature block for NBA 3.1  
**Builds on:** `NBA 3.1 FTP and COPAY Assessment.md` (UC tables assessment, 18 Nov 2026), `NBA 3.0 FTP and COPAY Assesment.md` (3.0 logic, features and model usage, 18 Nov 2026), `ftp_drift_analysis_and_strategy.md`, `copay_drift_analysis_and_strategy.md` (30 Oct 2026 source-drift analysis, superseded on the source choice by D1), `ftp_decisions_and_findings.md` (30 Oct 2026 notebook run and design decisions)  
**NBA 3.1 notebooks concerned:** `04_Promotional_Features/FTP_and_Copay/19_ftp_features` and `22_copay_features` (both to be re-pointed to the UC claims tables); coordination with the market access block (`17_promotional_features_samples`)  
**Status:** draft for discussion  
**Date:** November 23, 2026

## 1. Scope

| In scope | Out of scope (owned elsewhere or pending) |
| --- | --- |
| **FTP fills** (7 `WF` program groups) from `market_access.kerendia_ftp_claims`, as HCP-level features per 3.1 cohort | **BRIDGE program** (`SALE_TYP = 'BRIDGE'`, bridge-to-insurance): a distinct market access program, excluded by the 30 Oct decision; would need its own feature block if ever requested |
| **Copay fills** (3 `DF` program groups) from `market_access.kerendia_copay_claims`, same treatment | **BlinkRx / consumer enrollment data** (`TRMN_CSMR_PROF_MDM`): consumer-level, no prescriber identifier, inaccessible with the current role; belongs to the DTC / consumer block, not HCP features |
| **Program-use features**: has-any flag, fills, new-Rx fills, recency, and the copay affordability signal (average copay before the card) | **Payer / formulary features** beyond a candidate payer-mix (Phase 2, behind V7): the payer spine work lives with the market access team |
| **Point-in-time correctness**: fill date as feature date, load time respected, recent unsettled days trimmed | **Samples shipped / dropped**: market access block; this plan only ensures no double counting (V8) |
| **Refresh / drift monitoring** of the two UC tables as a feature dependency | Changing the copay source system, the program groups or the `stg_gtn_copay` feed |

## 2. Goal and how we will judge success

**Goal.** Replace the NBA 3.0 FTP / copay block — which counted records (not claims) by the date the prescription was written, let training see pickups that had not happened yet at the cohort date, and ended up with 4 weak FTP features and no copay feature in the final 752-feature model — with a block that is **claim-level, point-in-time correct, covers the whole 3.1 universe, and is honestly evaluated**: only 1.9 – 2.7% of the universe has any FTP or copay fill in a 12-month window, so whether these features earn a place in the model is an open question this plan answers with experiments, not assumptions.

**Success criteria** (to agree with the modelling team):

| # | Criterion | How it is measured |
| --- | --- | --- |
| S1 | **Point-in-time correct** | Features use the fill date (`RX_FILL_DATE`), only claims loaded by the cutoff (`INSERT_TS`), with the last unsettled days trimmed (D4); the written date is never the feature date |
| S2 | **One count per claim** | Each original claim (`ORGN_CLM_AUTH_NUM`) counts once; reversal netting and de-duplication are inherited from the UC build and re-verified per run (V2) |
| S3 | **Full universe, no conflation** | Every HCP x cohort row exists; a `has any` flag separates "no program activity" from "low activity"; 0 always means "no fill", never "not in the data" |
| S4 | **Reconciles with the assessment** | c28 12-month lookback: 3,951 FTP HCPs / 9,279 fills, 4,992 copay HCPs / 32,057 fills, 1,054 HCPs with both; universe link 99.4 – 99.6% |
| S5 | **Stable schema** | Same column list every run, generated from a config (programs, windows, caps); two runs produce identical columns |
| S6 | **Model value measured, not assumed** | Keep / drop decided by E1 – E5 against the E0 baseline; a negative result is recorded and the block is dropped or slimmed without argument |
| S7 | **No double counting across blocks** | FTP / copay counted here only; samples stay in the market access block; the sales-aligned FTP aggregates are a cross-check, never a second feature source (V8) |

## 3. Starting point (NBA 3.0)

| What NBA 3.0 does | Problem | Where it is explained |
| --- | --- | --- |
| Uses the **written** date (`RX_DT`) as the feature date | Training sees pickups that had not happened yet at the cohort date (look-ahead); recent months are undercounted at inference — copay records reach the view a median 82 days after their written month | 3.0 assessment 1j / 2i |
| Counts **records**, not claims | Duplicate rows of the same claim are counted twice: 1.2% of kept FTP rows, 6.3% of kept copay rows | 3.0 assessment 1d / 2d |
| Reversal removal by net `DAY_SUPPLY = 0` | Works, but the second copy of a kept claim stays | 3.0 assessment 1e |
| Only 4 FTP features in the final 752 (SHAP ranks 500 – 661, together 0.09% of total mean absolute SHAP) | FTP has almost no effect on the 3.0 model | 3.0 assessment 1e |
| **No copay feature in the 752** at all | Copay has no effect on the 3.0 model | 3.0 assessment 2f |
| 0 means both "no FTP" and "not in the FTP data" | The two meanings cannot be told apart | 3.0 assessment 1j / 2g |
| Copay `PCT_*` features empty in 94.5% of rows; the 1-month percentage is always 1 | No information | 3.0 assessment 2g |
| `PTNT_COPAY`, `PATOOP`, `GRP_NUM` loaded but never used | The affordability signal is discarded | 3.0 assessment 2b / 2j |
| Non-zero FTP for at most 0.9% of the 3.0 universe | The block is nearly all zeros | 3.0 assessment, one-line summary |

The 30 Oct 2026 draft (`19_ftp_features` run, `ftp_decisions_and_findings.md`) moved FTP to the sales-aligned table `ANLT_BASE_FACT_SALES_ALIGNED` (`SALE_TYP = 'FTP'`, pre-aggregated `FTP_TRX / FTP_NRX / FTP_UNIT`). That run is a useful cross-check baseline, but the primary source decision changes with D1 below.

## 4. Design principles for NBA 3.1

1. **Claim grain, from one place.** The UC tables already give one row per original claim: reversals netted out, duplicates resolved, money clawbacks netted and flagged, dates typed, prescriber matched to MDM. Features count claims; they never re-derive these rules.
2. **Fill date is the event.** The feature date is `RX_FILL_DATE` (pickup), not the written date. The written date is usable only for the written-to-fill lag candidate (Phase 2), never as a feature date.
3. **Point-in-time discipline.** A claim is known to a cohort only if `INSERT_TS` <= cutoff (95.1% of FTP and 96.9% of copay fills load within 14 days of the fill). The last unsettled days before each cutoff are trimmed (D4), so training mimics inference.
4. **Zero means zero.** Output covers every universe HCP x cohort; a `has any` flag separates "no activity" from "low activity"; missing combinations are filled with 0 from a config, never by accident.
5. **Money only netted.** Features use the `NET_*` columns (clawbacks netted). `IS_BENEFIT_CLAWED_BACK` / `IS_ZERO_NET_BENEFIT` are QC flags only — there is no clawback date, so as features they would leak (Q6 asks for the date).
6. **Skew handled by design.** 67% of FTP HCPs have a single fill; copay medians are 4 with a tail past 300. Count features ship with a cap / log / band variant (D5), and recency uses a sentinel, not 0.
7. **One join, cross-checked.** The universe links through `PROVIDER_ID` -> NPI -> `PRSC_NPI` (the 3.1 `00_cohort_config` mapping); `BH_ID` gives the same result (6 FTP / 15 copay disagreements in 106K fills) and is monitored, not used.
8. **No double counting.** FTP and copay are counted here only. Samples stay with the market access block; `ANLT_BASE_FACT_SALES_ALIGNED` FTP aggregates are a reconciliation source, not a feature source.
9. **Windows aligned to the anchor.** Same lookback logic as the rest of 3.1: windows of 1, 3, 6 and 12 months ending at the cohort lookback end (D3 confirms the final list), plus recency in days.
10. **Fixed schema.** Column list generated from a config of programs, windows, caps and flags; runs are reproducible.
11. **Snapshots, not restatements, for history.** The claims tables are overwritten weekly and `NET_*` money is netted with clawbacks known **at rebuild time**, so historical money values can change between rebuilds (D9). Counts are stable; money features accept this caveat until a clawback date exists.
12. **Language.** In documents and Veeva-facing text, use "NBA suggestion" / "NBA list", not "alert".

## 5. Target data model

```
UC claims tables (market_access, weekly overwrite, built from stg_gtn_copay)
  kerendia_ftp_claims    (7 WF program groups, ~106K claims)
  kerendia_copay_claims  (3 DF program groups, ~106K claims)
        |
        |-- point-in-time filter: RX_FILL_DATE <= lookback end, INSERT_TS <= cutoff, fill date >= window start
        |-- join: universe PROVIDER_ID -> NPI_NUMBER -> PRSC_NPI   (BH_ID cross-check)
        v
  ftp_copay_fill_events  (intermediate, one row per claim per program; program, dates, IS_NEW_RX, NET_* money)
        |
        |-- aggregate per HCP x cohort x window (1/3/6/12 months, capped/log/banded)
        v
  HCP x cohort feature rows (every universe HCP, zeros and has-any flags filled)
```

| Item | Grain | Key columns |
| --- | --- | --- |
| `ftp_copay_fill_events` (intermediate, proposal) | claim x program | `ORGN_CLM_AUTH_NUM`, `PROGRAM`, `PRSC_NPI`, `BH_ID`, `RX_FILL_DATE`, `RX_WRITTEN_DATE`, `INSERT_TS`, `IS_NEW_RX`, `FILL_NUMBER`, `DAY_SUPPLY_NUM`, `NDC_NUM`, `NET_PTNT_BNFT`, `NET_PTNT_COPAY`, `MMBR_ID` |
| Feature output | HCP x cohort | `PROVIDER_ID`, cohort, `FTP_*` / `CPY_*` features (C1 – C6), `PULL_DT` |
| Config | run parameters | programs, windows, caps, sentinel days, trim days, fill / zero rules |

QC inputs already built into the weekly refresh (fail on duplicates, non-positive supply, unparsed dates, rows outside the program groups, source older than 21 days, row drop > 5%): reused, not re-implemented.

## 6. Work plan

Each phase ends with a gate (section 8).

### Phase 0: Foundations and validation (blocking)

| ID | Task | Detail | Depends on / owner |
| --- | --- | --- | --- |
| V1 | Source decision and ownership | Confirm the UC claims tables as the single feature source for both programs (D1); confirm who owns the weekly refresh and its QC alerts; record the refresh dependency for the 3.1 runbook | NBA team, market access / data team |
| V2 | Point-in-time reproduction | Rebuild the 3.0 selection from the UC tables at the 3.0 load cut-off (2026-10-20): 105,361 FTP and 103,983 copay claims kept — the assessment already matches these; formalise as an automated check run each refresh | NBA team |
| V3 | Fill-date impact and trim window | Quantify fills / HCPs per month by fill date vs written date (copay roughly triples HCPs with a fill in a month); measure the `INSERT_TS` lag distribution per program; choose the trim window (0 / 14 / 21 days, D4) so the last weeks before a cutoff are not undercounted | NBA team |
| V4 | Universe link | Join both tables to the 3.1 universe through `PROVIDER_ID` -> NPI; re-check the `BH_ID` agreement (6 / 15 disagreements) and the mapping coverage (294,578 of 294,727 providers found) each run; fills with no `PRSC_NPI` (47 / 43) excluded and counted | NBA team |
| V5 | Leakage audit | Verify no feature uses information not knowable at the cutoff: fill <= cutoff and `INSERT_TS` <= cutoff; written date never a feature date; clawback / zero-benefit flags excluded; `MDM_SPECIALTY` excluded (current snapshot, not as of the cohort); `RX_FILL_DATE >= RX_WRITTEN_DATE` holds (0 violations) | NBA team |
| V6 | Skew and coverage profile | Per cohort: share of universe with any fill (expect 1.9 – 2.7%), fill-count percentiles, max (FTP 156, copay 308); pick the cap / log / band treatment (D5) and the recency sentinel | NBA team |
| V7 | Payer code meanings | `OTHR_CVRG_CD` (FTP mostly `00`, copay `08`/`03`) and copay primary-payer BIN (`CO_B_PRMY_OTHR_PYR_ID_BIN`) mapped to readable payer categories with the market access / data team — only then can the Phase 2 payer-mix candidate be built | Market access / data team |
| V8 | Block coordination | Confirm no overlap with the samples block and the sales-aligned FTP aggregates; restate the 30 Oct decisions that still stand (BRIDGE excluded; all FTP channels included; no PDRP filter beyond the universe) | NBA team |
| V9 | Fixed schema and config | Program list, windows, caps, flags, sentinel and trim days in a config; two runs produce identical columns | NBA team |
| V10 | History explanations | FTP volume drop through 2023 (from ~14K per quarter to ~2K) and the copay 2024-Q1 dip (2,828 fills): causes, so drift can be explained rather than just observed (Q4, Q5) | Market access team |

### Phase 1: Core features (high confidence)

Built per program from `ftp_copay_fill_events`, windows of 1, 3, 6 and 12 months ending at the lookback end. Names are illustrative; prefixes `FTP_` and `CPY_`.

| ID | Feature family | Example names | Approx. count | Origin |
| --- | --- | --- | --- | --- |
| C1 | Has any program fill | `FTP_HAS_ANY_12M`, `CPY_HAS_ANY_12M` | 2 | Assessment 1j (new in 3.1) |
| C2 | Fills per window | `FTP_FILLS_3M`, `CPY_FILLS_12M` (+ capped / banded variants, D5) | 8 – 12 | FTP: same as 3.0 but by fill date, one per claim; copay: new in 3.1 |
| C3 | New-Rx fills per window | `FTP_NEWRX_FILLS_6M`, `CPY_NEWRX_FILLS_3M` (`IS_NEW_RX`) | 8 | Assessment 1j; resolves the deferred 30 Oct `FTP_NRX` idea |
| C4 | Recency | `FTP_DAYS_SINCE_LAST_FILL`, `CPY_DAYS_SINCE_LAST_FILL` (sentinel for never) | 2 | Assessment 1j |
| C5 | Affordability (copay only) | `CPY_AVG_COPAY_BEFORE_CARD_12M`, `CPY_COPAY_GT300_SHARE_12M` (`NET_PTNT_COPAY`, USD 30 – 700) | 2 – 3 | Assessment 1j; the one signal no other 3.1 source has |
| C6 | Program overlap | `FTP_CPY_BOTH_12M` (~1,000 – 1,400 HCPs per cohort) | 1 – 2 | Assessment 1e (small overlap) |

Candidate set: about 25 – 30 columns. **Dropped from 3.0:** the `PCT_*` ratio features (empty in 94.5% of rows, 1-month ratio always 1) and the all-time running total (restated weekly; replaced by fixed windows).

**Notebook:** rework `19_ftp_features` and `22_copay_features` to read the UC tables through the shared intermediate, or merge into one `23_ftp_copay_features` notebook (D6). Either way the 3.0 written-date / record-grain logic does not carry over.

### Phase 2: Extended candidates (gated on model value)

Every family below was seen in the data and deliberately deprioritised (assessment 1j); each is added one at a time behind E8, after its validation passes.

| ID | Family | Columns it would use | Gate |
| --- | --- | --- | --- |
| X1 | Persistence / refills | `RX_NUM`, `FILL_NUMBER` (fills per prescription, refill share) | E8 + V5 (no leakage) |
| X2 | Strength / dose mix | `NDC_NUM` (10 / 20 / 40 mg; 20 mg = 21% FTP, 41% copay) | E8 |
| X3 | Patient-days on therapy | `DAY_SUPPLY_NUM` (copay 90-day share 11.6%) | E8 |
| X4 | Patient mix | `PAT_AGE`, `PAT_GNDR` (shares, not identities) | E8 + privacy check |
| X5 | Payer mix | `OTHR_CVRG_CD`, copay BIN | V7 first |
| X6 | Written-to-fill lag | `RX_WRITTEN_DATE` vs `RX_FILL_DATE` | E8; never a feature date |
| X7 | Pharmacy breadth | `PHMCY_NABP` (distinct pharmacies per HCP) | E8 |
| X8 | Trend | window vs prior window | E8 |

### Phase 3: Operations and monitoring

| ID | Task | Detail |
| --- | --- | --- |
| O1 | Refresh dependency | Feature runs require `REFRESH_TS` within 7 days and pass the built-in QC; fail loudly when the source is stale (> 21 days) or the row drop exceeds 5% |
| O2 | Snapshot retention | Monthly raw snapshots exist only from 2026-11 (one partition); agree retention and who keeps them, so past numbers stay traceable (Q7) |
| O3 | Drift report | Per cohort: FTP flat at ~2,000 – 2,400 fills per quarter vs copay growing to ~8,500; training (c1 – c24) sees a different program mix than holdout (c27 – c28) — reported with the block, so a model value change over time is explainable |
| O4 | Backfill behaviour | Recent months keep filling after a rebuild (copay written-month counts grew ~10% after the run); the trim window (D4) absorbs this at the cutoff; documented in the runbook |
| O5 | Program changes | A new `GRP_NUM` group fails the refresh QC until added; the config owns the group lists, and a change needs an explicit owner and a note in the block documentation (Q8) |

## 7. Experiments

All experiments run on the 3.1 cohort structure (training c1 – c24, testing c25 – c26, holdout c27 – c28) against the same validation metric.

| ID | Question | Design |
| --- | --- | --- |
| E0 | Baseline | 3.1 model without any FTP / copay feature |
| E1 | Does the block help? | E0 + full Phase 1 core block |
| E2 | Is it just the flag? | E0 + C1 has-any flags only — given 1.9 – 2.7% coverage, the flags may carry most of the signal |
| E3 | Skew treatment | Raw counts vs capped / log / banded variants (D5) |
| E4 | New starts vs all fills | C3 new-Rx fills vs C2 all fills; FTP is 63% new, copay 31% — the two carry different information |
| E5 | Affordability | E1 with and without C5 (`NET_PTNT_COPAY` features, copay only) |
| E6 | Negative control: 3.0 logic | Core block recomputed on the written date — quantifies how much the 3.0 look-ahead inflated / distorted the signal; expected to degrade holdout performance |
| E7 | Trim window | Cutoff trims of 0 / 14 / 21 days (D4) — the holdout cohorts are the test of whether training and inference see the same settled data |
| E8 | Extended families | Each Phase 2 family added one at a time to the E1 winner |

## 8. Gates

| Gate | Passes when |
| --- | --- |
| G0 (after Phase 0) | V1 – V5 pass: source confirmed and owned, 3.0 reproduction automated, trim window chosen, universe link stable, leakage audit clean |
| G1 (after Phase 1 build) | Fixed schema from config; zero nulls / duplicate keys; per-cohort coverage matches the assessment (S4 numbers; c28: 3,951 FTP / 4,992 copay HCPs, 1,054 both); invariant checks (windows non-decreasing, sentinel used for never, caps respected) |
| G2 (after experiments) | E1 – E5 (and E6 – E8 as needed) give a keep / slim / drop decision recorded with numbers; if dropped, the finding and the data stay documented for NBA 3.2 |
| G3 (before production) | O1 – O5 in the runbook: refresh dependency, drift report, backfill and program-change handling; feature block runs unattended on the 3.1 schedule |

## 9. Decisions and open questions

### Decisions to take

| ID | Decision | Recommendation |
| --- | --- | --- |
| D1 | Feature source | The UC claims tables (`kerendia_ftp_claims` / `kerendia_copay_claims`), not the 30 Oct options: the sales-aligned table is pre-aggregated (no claim detail, no copay claims) and the consumer MDM table has no prescriber; use sales-aligned FTP aggregates only as the V2 / V8 cross-check |
| D2 | Feature date | Fill date (`RX_FILL_DATE`); written date only for the X6 lag candidate |
| D3 | Windows | 1 / 3 / 6 / 12 months (pipeline standard), not the assessment's minimal 3 / 12 — the 1-month window feeds the NBA weekly / monthly rhythm |
| D4 | Point-in-time trim | Trim the last 14 days before each cutoff (95% of fills load within 14 days); confirm with E7 |
| D5 | Skew treatment | Ship counts capped (e.g. at p99: FTP 23, copay 45) plus a banded variant; final choice from E3 |
| D6 | Notebook layout | One combined `23_ftp_copay_features` notebook over the shared intermediate (one point-in-time rule, one join, one config); keep `19_` / `22_` names in history. Column naming keeps `FTP_` / `CPY_` prefixes; do not reuse `TOTAL_RX_FTP_IN_LAST_*` to avoid a silent meaning change |
| D7 | Backlog order for Phase 2 | Persistence (X1) and trend (X8) first, then dose / patient-days (X2 / X3); payer mix (X5) only after V7 |
| D8 | BRIDGE | Stays excluded (30 Oct decision): mixing it would change what the features mean; revisit only if the business asks for bridge tracking |
| D9 | Restated money | Accept that `NET_*` values are netted at rebuild time for C5 (affordability), and note the caveat in the block documentation; counts are unaffected. Remove the caveat if a clawback date ever arrives (Q6) |

### Open questions

| ID | Question | Status / owner |
| --- | --- | --- |
| Q1 | How much signal can a 1.9 – 2.7%-coverage block add? | The central question; answered by E1 / E2, not by assumption |
| Q2 | What do `OTHR_CVRG_CD` values and copay BINs mean in payer terms? | Open (V7); market access / data team |
| Q3 | What drives copay growth (HCPs 3.2K -> 5.0K, fills doubled across cohorts)? | Open (V10); market access team |
| Q4 | Why did FTP volume fall through 2023 and stabilise at ~2,000 – 2,400 fills per quarter? | Open (V10); market access team |
| Q5 | What caused the 2024-Q1 copay dip (2,828 fills)? | Open (V10); market access team |
| Q6 | Can a clawback date be sourced, so clawback flags / netted money become point-in-time correct? | Open; propose to the data team as a data improvement request |
| Q7 | Snapshot retention and ownership (only the 2026-11 partition exists today) | Open (O2); market access team |
| Q8 | Who owns the weekly refresh QC alerts and adding new program groups? Is the 5% row-drop threshold right for a ~106K-row table? | Open (V1 / O5); market access team |
| Q9 | Should FTP and copay features be surfaced as NBA business-rule dropdowns (e.g. "copay-active HCPs") even if model value is low? | Open; NBA / brand team |

## 10. Risks

| Risk | Effect | Mitigation |
| --- | --- | --- |
| Low coverage (97% of the universe always zero) | Block adds little; features risk being noise | E2 tests flag-only value; drop without argument if G2 says so; has-any flags are nearly free |
| Program mix drift (copay growing, FTP flat) | Training cohorts see a different mix than holdout; importance shifts over time | O3 drift report per cohort; banding instead of raw counts; time-fold stability checks in E1 |
| Late backfill (median 5 days, p95 14) | Last weeks before a cutoff undercounted, differently at training and inference | D4 trim window; E7; O4 runbook note |
| Weekly overwrite with restated `NET_*` money | Historical affordability values change between rebuilds; a past run cannot be reproduced exactly | D9 caveat; monthly snapshots (O2) as the traceable record |
| New program groups appear | Refresh QC fails (rows outside the known groups) until someone adds them; feature runs block | O5: group lists in the config, named owner, change note |
| NPI / BH_ID link disagreement (6 / 15 fills) or mapping gaps | A handful of fills land on the wrong HCP or drop out | V4 monitors both keys every run; disagreement counted, not silently fixed |
| Patient-level columns in the source (PII) | Privacy exposure if patient rows or identities leak into features | Aggregate shares only (X4); no patient IDs in any output; review with compliance before X4 ships |
| 3.0 habits carry over (written date, record grain, running totals) | Silent reintroduction of leakage or restated values | G1 invariants + V5 audit; the 3.0 notebooks are re-pointed, not reused (D6) |

## 11. References

* `NBA 3.1 FTP and COPAY Assessment.md` — UC tables assessment: build rules, coverage per cohort, distributions, column-by-column review, feature ideas (18 Nov 2026)
* `NBA 3.0 FTP and COPAY Assesment.md` — 3.0 logic, features, model usage and known issues (18 Nov 2026)
* `ftp_drift_analysis_and_strategy.md`, `copay_drift_analysis_and_strategy.md` — 30 Oct 2026 source drift analysis (sales-aligned / consumer MDM options; superseded by D1, kept for the access issue and column maps)
* `ftp_decisions_and_findings.md` — 30 Oct 2026 `19_ftp_features` run findings and design decisions (BRIDGE, channels, PDRP, NRX)
* `../personal_promotional_features/40_field_activity_nba_3_1_readiness_plan.md` — structure this plan mirrors; samples business rule (received = Delivered + AOC Received)
* `../non_personal_promotional_features/50_digital_nba_3_1_readiness_plan.md` — digital block plan
* UC tables: `ph-com-ai-us-prod-catalog-2553213839599380.market_access.kerendia_ftp_claims`, `...kerendia_copay_claims` (+ `..._snapshot`); build notebooks `/Users/wenjie.chen@bayer.com/kerendia_data_needs/Copay_FTP/` (`00_common`, `02_refresh_copay_ftp`)
* Source: `PHCDW.PHCDW_STG_COMMON.STG_GTN_COPAY` (`SRC_SYS_CD = 'PRM'`, weekly Sunday load)
* 3.1 inputs: `kerendia_nba_3_1.input_hcp_universe` (294,727 providers), `kerendia_nba_3_1.input_claims_cohorts` (c1 – c28), provider -> NPI / Bayer ID mapping (`00_cohort_config` default `NPI_BHID_MAPPING_PATH`)
