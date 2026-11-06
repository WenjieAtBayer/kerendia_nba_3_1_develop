# Field Activity Phase 4 (X1 Samples): Output Analysis (NBA 3.1)

**Notebook:** `44_field_activity_phase4_samples_features`  
**Plan:** `40_field_activity_nba_3_1_readiness_plan.md` (Phase 4: X1; condition V5; experiment E5; design principles 5, 6, 8, 9 and 10; success criterion S3)  
**Background:** `22_samples_reconciliation_call_vs_shipped_dropped_2024_2026.md` (V5, rules R1 – R7), V5 section of `40_field_activity_phase0_output_analysis.md`, `20_field_activity_data_review_2024_2026.md` (section 6.4)  
**Run analysed:** 6 Nov 2026 (settling period removed), serverless (data to 30 Oct 2026)  
**Date:** 6 Nov 2026

**How to read this file.** Section 1 is the summary. Section 2 gives the background for a first-time reader. Section 3 explains what the notebook does. Section 4 goes through every expectation: why we expected it (from NBA 3.0 and V5), whether it is new, what we got, and what to raise with the client. Sections 5 – 8 list the gate, issues, client questions and next actions.

**Years.** Year 1 = Nov 2024 – Oct 2025, Year 2 = Nov 2025 – Oct 2026 (as in Phase 0). **Cohorts.** Unlike notebooks 41 – 43, this notebook uses the NBA 3.1 promotional cohort file (`kerendia_nba_3_1_volume/cohorts/promotional/cohorts.parquet`): 28 cohorts, lookback ends 2024-06-17 (c1) to 2026-09-17 (c28); c1 – c24 training, c25 – c26 testing, c27 – c28 back-testing. Each feature uses the 12 months up to the **sample cutoff** = lookback end (settling rule R7 removed). **Universe.** `kerendia_nba_3_1_volume/HCP_Universe_without_call_hcps/` (294,726 `PROVIDER_ID`s after removing placeholder `0`); every universe HCP has one row per cohort.

---

## 1. Summary

| ID | Expectation (plan / V5) | NBA 3.0 or new | Status | One-line result |
| --- | --- | --- | --- | --- |
| X1-a | One samples source, received = `Delivered` + `AOC Received` | Correction of 3.0 and of the market access table | **Met** | Year 2 received 452,210 units / 20,448 doctors vs `22_` 449,246 / 20,270 (+0.66% / +0.88%); every status mapped |
| X1-b | Status map in config, unmapped status stops the run | New | **Met** | 11 statuses mapped; 0 unmapped; 2023 pending (stale) 8,386 units and Year 2 failed 14,772 units excluded |
| X1-c | Settling rule (R7): only orders up to lookback end − 21 days | New | **Removed** | Settling period removed; SAMPLE_CUTOFF_DATE = LOOKBACK_END_DATE for all cohorts; request feature removed |
| X1-d | Received units and sample calls, 3 / 6 / 12 months, recency | New (NBA 3.0: "call type with sample" only) | **Built** | 19,737 – 21,490 HCPs per cohort with a received sample in 12 months (6.7 – 7.3% of the universe) |
| X1-e | 40 mg flags (6 / 12 months), no 10 / 20 mg split | New | **Built, sparse** | 0 in c1 – c15, 344 HCPs in c16, 1,501 in c24, 2,222 – 2,250 in c27 – c28; 99.5 – 100% zero in training |
| X1-f | Sample requests in the settling period (any status) | New (optional) | **Removed** | Settling period removed; feature no longer in output |
| X1-g | Universe x cohort skeleton, mapped to `PROVIDER_ID` | New (other blocks are BHID-only) | **Met** | 8,252,328 rows = 294,726 x 28; 9 features; 98.10% of received units on universe HCPs |
| X1-h | Comparison with the market access logic | V5 follow-up | **Done** | Market access logic sees 40% of NBA 3.1 units in c1, 99 – 100% in c11 – c14, 40% in c24, 5 – 6% in c27 – c28 |
| G1-type checks | Keys, nulls, invariants, recompute | — | **Pass** | 0 duplicates, 0 nulls, 9 / 9 invariants, 8 / 8 HCPs match in Snowflake (c24, cutoff 2026-05-17) |
| X1 condition / E5 | Plan section 6 (Phase 4) and section 7 | — | **Not met** | Block location with market access owner (Q-S2) and legacy rule (Q-S6) open; E5 not run |

**Bottom line.** The samples block is built once from `FACT_CALL_SAMPLE`, with the agreed status rule and a universe x cohort skeleton (no settling period), and it reconciles with `22_` within 1%. All data checks pass. The run confirms the size of the NBA 3.0 problem: the market access logic sees only 5 – 6% of received units in the back-testing cohorts. Two findings need a client answer before E5: **(1)** before the BRC process (until about April 2024) samples were recorded as `Kerendia 10mg / 20mg` with **no status**, and they are 3 – 56% of received units in c1 – c10 (currently counted as received, Q-S6); **(2)** almost no sample orders exist for the two weeks of the Vault change (28 Jul – 10 Aug 2025), which affects every window that covers them (Q-S7). The 40 mg flag now has signal in 9 training cohorts, but it is above 99.5% zero.

---

## 2. Background for a new reader

1. **Kerendia samples.** Reps order free Kerendia samples for a doctor through a business reply card (BRC) during a call. The order is shipped by the vendor and the doctor acknowledges receipt. Veeva stores one row per sample line (`FACT_CALL_SAMPLE`): product (`Kerendia 10mg / 20mg / 40mg BRC`), quantity (`SMPL_QTY`), order date (`CALL_DATE`) and delivery status (`DLVR_STAT`).
2. **Status.** The status changes as the order moves: in progress, shipped, delivered or AOC received (acknowledgement of content), or rejected / returned / cancelled / lost. Only the **current** status is stored, with no delivery date.
3. **What NBA 3.0 did.** The field block only had "call type with sample". The market access block (`17_promotional_features_samples`) used `ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER`, which V5 showed to be a status-filtered copy of `FACT_CALL_SAMPLE` that misses `aoc_received__c` (used since the Vault change, late July 2025) and counts `Shipped_vod` as received.
4. **Why Phase 4 (X1).** The plan builds samples once, from one source (principle 6, S3), with the agreed rule (received = `Delivered` + `AOC Received`), and a 40 mg flag. The settling rule R7 (21-day cutoff) has been removed: `SAMPLE_CUTOFF_DATE = LOOKBACK_END_DATE`. The block is conditional: it enters the model only through E5.
5. **Why a universe x cohort skeleton.** Notebooks 41 – 43 output only doctors with activity (BHID). Here every universe HCP (`PROVIDER_ID`) gets a row in every cohort with defaults, so the row count is known (universe x 28) and the join to other blocks is one-to-one.

---

## 3. How the notebook works

| Step | Cell | What it does |
| --- | --- | --- |
| Setup | 2 – 4 | Installs the Snowflake connector, defines `Get_Data_Snowflakes`, and holds the config: paths, `SETTLE_DAYS = 0` (no settling period), windows 3 / 6 / 12 months (no 1-month window), products and strengths, `COUNT_LEGACY_DIRECT_SAMPLES`, status map, reference figures from `22_`, and `expected_feature_columns()` (9 columns) |
| Inputs | 5 | Reads the 28 cohorts (adds `SAMPLE_CUTOFF_DATE`), the universe (294,726 `PROVIDER_ID`s after removing placeholder `0`) and the BHID mapping restricted to the universe |
| 1a | 6 | Pulls Kerendia sample lines since 2023-01-01 from Snowflake (277,509 lines), BRC and legacy products, with BHID from `MAP_CUSTOMER_XREF` |
| 1b | 7 | Builds `field_sample_line`: removes exact duplicates, adds strength and the status class; stops if a status is not mapped or a sample line appears twice; writes the table for reuse by notebook 17 |
| 1c | 8 | Validates: units by period and status, by quarter (BRC vs legacy), Year 2 against `22_` (3% tolerance), and the settling pattern in the last 8 weeks |
| 1d | 9 | Maps lines to universe `PROVIDER_ID`s and reports coverage |
| 2a | 10 | Attaches received lines to every cohort whose 12-month window before the sample cutoff contains them; leakage check (no settling period) |
| 2b | 11 | Aggregates the 9 features |
| 2c | 12 | Universe x cohort skeleton, defaults (0, or 999 for days since), fixed schema, write (16 columns: 7 keys + 9 features); cohort diagnostics table (`SMPL_40MG_AVAILABLE`, units by status, legacy units) |
| Checks | 13 – 17 | Duplicates, nulls, 9 invariants; profile by cohort; independent Snowflake recompute for 8 c24 HCPs; comparison with the market access logic; default rate per feature, distribution, Vault-change weeks |
| Results | 18 | Results summary |

**Changes during the run.**

* No code fixes were needed: all cells ran on the first attempt.
* One cell was added after the run (cell 17): default rate per feature by dataset, distribution of units and calls in c24, weekly units around the Vault change, and checks on zero quantities and on `PROVIDER_ID` `0`.
* The results cell (18) was filled with the run figures.

**Outputs** (`kerendia_nba_3_1_volume/notebook_output/field_activity_nba_3_1/`): `field_sample_line.parquet` (277,507 lines), `kerendia_nba_3_1_hcp_model_field_sample_features.parquet` (8,252,328 rows, 16 columns: 7 keys + 9 features), `field_sample_cohort_diagnostics.parquet` (28 rows).

---

## 4. Expectation by expectation

### X1-a — One source, agreed received rule

* **Why we expect this.** V5 (`22_`, R1 – R3) showed that the market access table and the call samples are the same records, and agreed with MV that received = `DELIVERED` / `Delivered_vod` + `aoc_received__c`. Building once from `FACT_CALL_SAMPLE` avoids double counting (S3) and the Year 2 gap.
* **NBA 3.0 or new.** Correction of 3.0 (the field block had no quantities; the market access table used the wrong statuses).
* **What we got.** Units by period and status class (lines with a BHID):

| Period | Received | Pending | Failed | Unknown |
| --- | --- | --- | --- | --- |
| 2023 | 376,798 | 8,386 | 95 | 1,114 |
| Jan – Oct 2024 | 476,262 | 24 | 8,386 | 2,371 |
| Y1 (Nov 2024 – Oct 2025) | 425,450 | 176 | 12,151 | 2,274 |
| Y2 (Nov 2025 – Oct 2026) | 452,210 | 13,511 | 14,772 | 0 |

  Year 2 received (BRC only, as in `22_`): 452,210 units and 20,448 doctors, against 449,246 / 20,270 in `22_` (+0.66% / +0.88%). The small increase is expected: the `22_` cut was 23 Oct 2026, and orders keep settling into a received status.
  Line quality: 277,509 lines pulled, 2 exact duplicates (same sample line twice through the customer cross-reference), 24 lines without a BHID; 0 received lines with zero or empty quantity.
* **Status.** Met.
* **Raise with client.** Q-S2: notebook 17 should read `field_sample_line` (or apply the same status map) so that samples exist once (S3).
* **Suggestions.** Keep the 3% tolerance check against `22_`; replace the reference figures when the market access owner agrees a new baseline.

### X1-b — Status map in config

* **Why we expect this.** NBA 3.0 lost `aoc_received__c` silently when Vault introduced it. The plan keeps the rule in config and makes an unknown status stop the run (principle 10).
* **NBA 3.0 or new.** New.
* **What we got.** `DLVR_STAT` values found and mapped:

| Class | Statuses | Used in features |
| --- | --- | --- |
| RECEIVED | `DELIVERED` (to Jul 2025), `Delivered_vod`, `aoc_received__c` | Yes |
| PENDING | `Shipped_vod`, `In_Progress_vod`, `on_hold__c`, `IN PROCESS` (brochures only) | No |
| FAILED | `rejected__c`, `Returned`, `Cancelled_vod`, `lost_in_transit__c` | No |
| UNKNOWN | empty status on BRC lines (2,274 units in Y1, 0 in Y2) | No |
| RECEIVED (assumption) | empty status on legacy `Kerendia 10mg / 20mg` lines (see X1-g caveat and section 6, P1) | Yes, while `COUNT_LEGACY_DIRECT_SAMPLES = True` |

  0 unmapped statuses. The 8,386 pending units in 2023 are old `In_Progress_vod` / `Shipped_vod` lines that never reached a final status; they are excluded.
* **Status.** Met.
* **Raise with client.** None beyond Q-S6.
* **Suggestions.** Report units by status every month (the cell 8 tables) and recheck the October 2026 status shift in December (R6).

### X1-c — Settling rule (R7) — removed

* **Why it existed.** Orders take two to three weeks to reach their final status and only the current status is stored. At scoring, recent orders are still pending; in history they have all settled. The 21-day cutoff was designed to give training and scoring the same basis.
* **Why it was removed.** The user requested removal of the 21-day settling period. `SAMPLE_CUTOFF_DATE` now equals `LOOKBACK_END_DATE` for all cohorts, and the request feature (`SMPL_REQ_CALLS_LAST_21D`) has been removed from the output.
* **What we got.** Leakage check passed (no received line after the sample cutoff). `SETTLING_PERIOD_UNITS_ANY_STATUS = 0` for all cohorts (no settling window). The 12-month feature window now ends at the cohort lookback end date.
* **Status.** Removed (settling rule R7 no longer applied).
* **Raise with client.** Q-S5: a delivery or status-change date, or weekly status snapshots, would allow receipt-date windows instead of the cutoff.
* **Suggestions.** If pending orders in the last few weeks prove noisy in E5, re-introduce a settling period as a config value.

### X1-d — Received units, sample calls and recency

* **Why we expect this.** The data review (PN-4) and V5 found quantity and number of sample calls a usable signal that NBA 3.0 did not have. The plan asks for units and sample-call counts over 3 / 6 / 12 months and recency (principle 8).
* **NBA 3.0 or new.** New.
* **What we got.** Profile by cohort (universe = 294,726 rows per cohort):

| Cohort | Dataset | Sample cutoff | HCPs received 12M | % of universe | Units 12M | Units 3M | Legacy share of units |
| --- | --- | --- | --- | --- | --- | --- | --- |
| c1 | Training | 2024-06-17 | 21,490 | 7.29 | 466,419 | 148,610 | 56.2% |
| c4 | Training | 2024-09-17 | 21,037 | 7.14 | 498,762 | 128,213 | 34.1% |
| c8 | Training | 2025-01-17 | 20,261 | 6.87 | 532,548 | 114,287 | 11.8% |
| c10 | Training | 2025-03-17 | 19,737 | 6.70 | 548,423 | 126,253 | 2.6% |
| c12 | Training | 2025-05-17 | 18,723 | 6.35 | 529,195 | 142,054 | 0% |
| c15 | Training | 2025-08-17 | 17,760 | 6.03 | 489,296 | 88,627 | 0% |
| c16 | Training | 2025-09-17 | 17,525 | 5.95 | 470,979 | 73,212 | 0% |
| c18 | Training | 2025-11-17 | 15,878 | 5.39 | 396,640 | 45,038 | 0% |
| c20 | Training | 2026-01-17 | 15,130 | 5.13 | 360,787 | 42,297 | 0% |
| c22 | Training | 2026-03-17 | 13,730 | 4.66 | 300,713 | 57,135 | 0% |
| c24 | Training | 2026-05-17 | 14,110 | 4.79 | 291,915 | 105,488 | 0% |
| c25 | Testing | 2026-06-17 | 15,211 | 5.16 | 311,706 | 139,409 | 0% |
| c26 | Testing | 2026-07-17 | 16,148 | 5.48 | 331,586 | 163,727 | 0% |
| c27 | Back-testing | 2026-08-17 | 17,571 | 5.96 | 367,769 | 161,930 | 0% |
| c28 | Back-testing | 2026-09-17 | 18,584 | 6.31 | 401,027 | 161,355 | 0% |

  The fall in c16 – c24 and the rise afterwards follow the real H2 2025 dip and the 2026 recovery in sample volume (`20_`, 6.4; confirmed in `22_`), plus the Vault-change gap (P2). In c24, HCPs with a sample received a median of 13 units in 12 months (90th percentile 45, 99th 120, maximum 389) on a median of 1 sample call (90th percentile 3, 99th 8).
  Default rate (share of rows at 0, or 999 for days since):

| Feature | Training | Testing | Back-testing |
| --- | --- | --- | --- |
| `SMPL_RCVD_UNITS_3M` / `_CALLS_3M` | 96.9 – 99.0% | 96.5 – 97.0% | 96.5% |
| `SMPL_RCVD_UNITS_6M` / `_CALLS_6M` | 95.1 – 98.0% | 95.5 – 96.2% | 94.6 – 95.1% |
| `SMPL_RCVD_UNITS_12M` / `_CALLS_12M`, `SMPL_DAYS_SINCE_LAST_RCVD` | 92.7 – 95.4% | 94.5 – 94.8% | 93.7 – 94.0% |

* **Status.** Built. Sparse by nature: about 5 – 7% of universe HCPs receive samples in a year.
* **Raise with client.** Inform Field Analytics that sample features describe only about 14 – 21K of the 295K universe HCPs per cohort.
* **Suggestions.** Units and calls are zero for exactly the same rows; check their correlation in E5 and keep one per window if they are redundant. Keep `SMPL_DAYS_SINCE_LAST_RCVD`.

### X1-e — 40 mg flags

* **Why we expect this.** V5 (R5) found the 10 / 20 mg mix stable (no information) and 40 mg new from August 2025 and HF-related. The plan asks for a 40 mg flag over 6 / 12 months, with availability kept for checks only.
* **NBA 3.0 or new.** New.
* **What we got.** HCPs with a received 40 mg sample:

| Cohorts | 12 months | 6 months |
| --- | --- | --- |
| c1 – c14 | 0 | 0 |
| c15 | 64 | 64 |
| c16 | 485 | 485 |
| c18 | 716 | 716 |
| c20 | 952 | 952 |
| c22 | 1,233 | 813 |
| c24 | 1,698 | 1,092 |
| c25 – c26 (testing) | 1,946 – 2,181 | 1,233 – 1,410 |
| c27 – c28 (back-testing) | 2,261 – 2,340 | 1,514 – 1,654 |

  The invariant "40 mg flag only after the 40 mg start" passed (0 rows). `SMPL_40MG_AVAILABLE` (0 for c1 – c14, 1 from c15) is in the diagnostics table only, not in the features. Default rate: 99.4 – 100% in training, 99.3 – 99.6% in testing and back-testing.
* **Status.** Built; signal in 10 training cohorts (c15 – c24), meeting the minimum of 6 proposed in the V5 section; very sparse.
* **Raise with client.** Q-S4: is 40 mg sampled mainly for HF patients? It decides whether the flag can be explained to reps as an HF signal.
* **Suggestions.** Keep `SMPL_40MG_RCVD_12M` only if E5 gives it weight and its importance is stable across time folds; the 6-month flag adds little (same as 12 months until c21).

### X1-f — Sample requests in the settling period — removed

* **Why it existed.** The settling cutoff hid the last 21 days. A sample order exists on the call date whatever its later status, so counting requests in that period (any status) gave a recent signal without leakage (V5 section, proposal).
* **Why it was removed.** With the settling period removed (`SAMPLE_CUTOFF_DATE = LOOKBACK_END_DATE`), the settling window is empty and the request feature has no meaning. `INCLUDE_REQUEST_FEATURE = False`.
* **Status.** Removed.

### X1-g — Universe x cohort skeleton

* **Why we expect this.** A known row count and a one-to-one join to the other blocks (`PROVIDER_ID` x cohort).
* **NBA 3.0 or new.** New. Notebooks 41 – 43 output only doctors with activity, keyed on BHID, on the old 26 cohorts.
* **What we got.** 8,252,328 rows = 294,726 x 28; 0 duplicate keys; every cohort has exactly 294,726 rows; 9 features (16 columns: 7 keys + 9 features). The placeholder `PROVIDER_ID` `0` was removed from the universe before building the skeleton. Mapping: 294,577 universe HCPs (99.95%) have a BHID; 38 BHIDs map to more than one universe `PROVIDER_ID` (each receives the samples); no `PROVIDER_ID` has more than one BHID. 98.10% of received units (1,697,875 of 1,730,777 since 2023) and 94.71% of received BHIDs (42,520 of 44,894) fall in the universe.
* **Status.** Met.
* **Raise with client.** None (placeholder `0` removed).
* **Suggestions.** Use the same skeleton, universe and 28-cohort file in notebooks 41 – 43 so all promotional blocks share keys and row counts (section 8, N6).

### X1-h — Comparison with the market access logic

* **Why we expect this.** V5 measured the gap by year; the plan needs it per cohort to show the effect on training and scoring.
* **NBA 3.0 or new.** V5 follow-up.
* **What we got.** Units in the 12-month window before the sample cutoff, market access logic (`DELIVERED`, `Delivered_vod`, `Shipped_vod`, BRC only) vs NBA 3.1:

| Cohorts | Ratio market access / NBA 3.1 | Main reason |
| --- | --- | --- |
| c1 – c10 | 0.40 – 0.97 | Legacy pre-BRC lines not in the market access table |
| c11 – c14 | 0.997 – 1.00 | Both see the same records |
| c15 – c21 | 0.97 – 0.67 | `aoc_received__c` missing from August 2025 |
| c22 – c24 | 0.57 – 0.29 | Same, growing share of the window |
| c25 – c26 (testing) | 0.16 – 0.06 | Same |
| c27 – c28 (back-testing) | 0.055 – 0.07 | Window almost entirely after the Vault change |

  HCPs with a received sample in c27: 17,571 with NBA 3.1, 1,569 with the market access logic.
* **Status.** Done.
* **Raise with client.** Q-S2 (with this table).
* **Suggestions.** Use this table to explain to the market access owner why notebook 17 must change before NBA 3.1 scoring.

---

## 5. Phase 4 condition (X1) and E5

The plan's condition for X1: "V5 done; agree with the market access block owner where the block lives", and the block enters the model through E5 ("E4 + conditional candidates (X1, X2) that passed their condition").

| Part | Status | Evidence |
| --- | --- | --- |
| V5 done | **Pass** | `22_`; this run reconciles with `22_` within 1% |
| Block location agreed with the market access owner | **Open** | Q-S2; `field_sample_line` written for reuse |
| Legacy pre-BRC samples rule | **Open** | Q-S6; 3 – 56% of c1 – c10 units |
| Vault-change gap explained | **Open** | Q-S7 |
| Data checks (keys, nulls, invariants, recompute) | **Pass** | 0 duplicates, 0 nulls, 9 / 9 invariants, 8 / 8 HCPs match (c24, cutoff 2026-05-17) |
| Back-testing targets complete (c27 – c28) | **Open** | Modelling team (C6) |
| E5 run | **Open** | Needs E4 (G2 still open) |

**The X1 condition is not met.** The block is technically ready for E5 with `COUNT_LEGACY_DIRECT_SAMPLES = True`; the decision on Q-S6 should be taken before E5, because it changes the first ten training cohorts.

---

## 6. Issues

| # | Issue | Impact | Proposal |
| --- | --- | --- | --- |
| P1 | Legacy `Kerendia 10mg / 20mg` lines (until April 2024) have no status; counted as received by assumption | 56.2% of c1 received units, 34.1% of c4, 2.6% of c10, 0 from c12; without them c1 – c10 would show an artificial rise in samples | Q-S6; keep the config switch; rerun with `False` as a sensitivity check in E5 |
| P2 | Almost no orders in the weeks of 28 Jul and 4 Aug 2025 (75 and 105 units vs 7 – 11K normally), at the Vault change | The 12-month windows of c15 – c27 miss about two weeks of samples | Q-S7: data missing or a real pause? If missing, ask for a backfill |
| P3 | Sample volume falls in c16 – c24 and rises in testing and back-testing | Training ends at the low point; level shift between training and scoring | Real (H2 2025 dip, 2026 recovery); check feature stability across time folds in E5 |
| P4 | 40 mg flags above 99.5% zero in training | Little room for the model to learn | Keep the 12-month flag only if E5 supports it |
| P5 | Units and calls zero on the same rows | Possible redundancy | Correlation check; keep one per window if redundant |
| P6 | 38 BHIDs map to more than one universe `PROVIDER_ID` | Their samples are counted on each `PROVIDER_ID` (small) | Same rule as the mapping table; review with the universe owner |
| P7 | `PROVIDER_ID` `0` in the universe | No impact (no samples, removed from output) | Resolved: filtered out before building the skeleton |
| P8 | Notebooks 41 – 43 use BHID, activity-only rows and the old 26 cohorts | Blocks cannot be joined one-to-one with this block | Move them to the universe x 28-cohort skeleton (N6) |
| P9 | Notebook 17 still uses the market access table | Samples counted twice and wrong (5 – 6% of units in back-testing) if both blocks are used | Q-S2 |
| P10 | c27 – c28 prediction months are Sep – Oct 2026 | Targets may not be complete for back-testing | Confirm with the modelling team (C6) |

---

## 7. Client questions

| # | Question | Why it matters | Owner |
| --- | --- | --- | --- |
| Q-S2 | Will notebook 17 read `field_sample_line` (or apply the same status map), and when? | Removes double counting (S3) and the Year 2 gap (market access logic sees 5 – 6% of units in c27 – c28) | Market access block owner |
| Q-S4 | Is 40 mg sampled mainly for HF patients? | Explains the 40 mg flag to reps | Kerendia brand team |
| Q-S5 | Can CareTria provide a delivery or status-change date, or can weekly status snapshots be kept? | Would allow receipt-date windows instead of the current cutoff (settling rule removed) | Samples operations, data team |
| Q-S6 | Before the BRC process (to about April 2024), are `Kerendia 10mg / 20mg` sample lines without a status samples the doctor received (direct rep drops)? | 3 – 56% of received units in c1 – c10 | Samples operations, CRM team |
| Q-S7 | Why are there almost no sample orders in the two weeks from 28 Jul 2025 (Vault change)? Missing data or a real pause? | Two weeks missing from the windows of c15 – c27 | CRM team (Vault migration) |
| C6 | Confirm the 28-cohort promotional file and that the c27 – c28 targets are complete | Back-testing | Modelling team |


---

## 8. Next actions

| # | Action | Owner | Status |
| --- | --- | --- | --- |
| N1 | Send Q-S2 (with the X1-h table), Q-S4, Q-S5, Q-S6 and Q-S7 | NBA team | Open |
| N2 | Decide `COUNT_LEGACY_DIRECT_SAMPLES` after Q-S6; rerun the notebook | NBA team | Waiting for client |
| N3 | Agree with the market access owner that notebook 17 reads `field_sample_line` | NBA team, market access block owner | Open |
| N4 | Run E5 (after E4): samples features with and without the legacy lines; check 40 mg weight and stability | NBA team | Open |
| N5 | Correlation check units vs calls; drop redundant columns after E5 | NBA team | Open |
| N6 | Move notebooks 41 – 43 to the same universe, `PROVIDER_ID` x 28-cohort skeleton and cohort file, then join the blocks on `HCP_COHORT_ID` | NBA team | Open (to confirm) |
| N7 | Monthly report of units by status; recheck the October 2026 status shift in December 2026 (R6) | NBA team | Open |
| N8 | Update the readiness plan (X1 status, Q2, risks) with these results | NBA team | Open |
