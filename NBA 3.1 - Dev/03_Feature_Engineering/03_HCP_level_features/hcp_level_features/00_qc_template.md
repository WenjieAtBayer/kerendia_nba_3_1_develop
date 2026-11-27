# QC <NN>: <claim type> features, NBA 3.1

**QC status:** <NOT STARTED / IN PROGRESS / DONE>, <date> (claim type <n> of 2; next: <next>)  
**Verdict:** <PASS / PASS with actions / FAIL>. <one line: what was proven, what is open>  
**QC run:** <date>, <compute>, on the output written <PULL_DT>. Notebook re-run during QC: <yes / no>.

How to use: fill sections 1 and 2 first, record numbers in section 3, then sections 4 to 10. A check is closed only with evidence (number + query / cell). Do not re-run the feature notebook unless agreed: it overwrites the outputs. Rule source = `60_ftp_copay_nba_3_1_readiness_plan.md` ("readiness"). `<V31>` = `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume`.

## 1. What is under QC

| Item | Value |
| --- | --- |
| Notebook | <path> (<n> cells) |
| Rule file | `60_ftp_copay_nba_3_1_readiness_plan.md` (sections 2, 4, 6, 8, 9) |
| Source table | <UC table, program groups> |
| Universe | <path>: <n> HCPs |
| Cohorts | <path>: family, offset, c1 to c28, split |
| Mapping | <path> (PROVIDER_ID -> NPI_NUMBER / BH_ID) |
| Output | <path>: rows x feature columns |
| Expected grain | One row per `PROVIDER_ID` x `COHORT` = universe x 28 |
| NBA 3.0 counterpart | <3.0 notebook / output> |
| NBA 3.0 final model | 752 features: `/Users/sehar.aejaz.ext@bayer.com/Extra Notebooks/Final NBA 3.0 Modeling Features.xlsx` |

## 2. QC checklist

Status: `PASS` / `FAIL` / `OPEN` / `N/A`. Evidence goes in section 3.

| # | Check | How | Pass when | Status |
| --- | --- | --- | --- | --- |
| Q1 | HCP universe | Distinct `PROVIDER_ID` in output vs universe; rows per cohort; duplicate keys; `left_anti` output vs universe; placeholder IDs (`'0'`, null) | Output = universe x 28, 0 duplicates, 0 outside | |
| Q2 | Right cohorts | File = `<V31>/cohorts/claims/cohorts.parquet`; `metadata.json` family `claims`, offset 0; output `COHORT` / `DATASET` / `PREDICTION_MONTH` / `SVC_DT` = file | 0 mismatches, no promotional dates | |
| Q3 | Windows and point-in-time | Window end E = last day of lookback end month; claim counted only if `RX_FILL_DATE <= E` and `INSERT_TS < PREDICTION_MONTH`; edge fills (last day in, 1st of next month out, late-loaded out) | No claim after E or loaded late contributes | |
| Q4 | Data sources vs readiness | Section 5: tables, paths, rows, date ranges, freshness, link coverage; no write to the 3.0 volume | Same sources, differences explained | |
| Q5 | All features made | Section 6: plan families (C1 to C6, X1 to X8) vs output columns and types | 0 missing without a reason, 0 unexpected | |
| Q6 | Business rules | Section 4: readiness rule vs notebook | Each rule matches, or the difference is documented and agreed | |
| Q7 | Fill rate | Section 7: per feature % null, % zero, % non-zero, sentinel %, min / max; all, train, test, holdout, c28 | No unexpected nulls; flags for constant, > 99.5% zero, train-vs-holdout change > 5 points | |
| Q8 | NBA 3.0 752 coverage | Every 3.0 feature of this claim type in the 752 (SHAP rank, %) mapped in section 8 | 0 skipped without a written reason | |
| Q9 | Preserved vs new | Section 8: each 3.1 feature labelled preserved / replaced / new; each dropped 3.0 feature has a reason | All labelled | |
| Q10 | HCP trace | Section 9: >= 5 HCP x cohort cases recomputed from the source table independently of the notebook, value printed at each step | Output = recompute for every value | |
| Q11 | Invariants | Independent recount: nested windows, new-Rx <= fills, flag vs counts, cap / band, sentinel, ranges, zero when inactive | 0 violations (or explained) | |
| Q12 | NBA 3.0 output comparison | Closest 3.0 output vs 3.1 c28 on common HCPs: HCPs > 0, totals, Spearman | Differences explained | |
| Q13 | Reproducibility and docs | Output from the full run (row count, `PULL_DT`), QC log written, notebook header / decision log / readiness match the run; stale outputs in the folder | No stale text that changes meaning | |
| Q14 | Program groups (O5) and data drift (owner: NBA team) | Distinct `GRP_NUM` in the source table vs the config group list (new / missing groups); per `DATASET`: active HCPs and 12M fills per cohort, % change of test and holdout vs training; QC log O3 / O5 rows | Groups = config (0 new, 0 missing); every drift change > 20% vs training is explained and signed off by the NBA team | |

## 3. Evidence log

| # | Result (numbers) | Where (query / cell) | Notes |
| --- | --- | --- | --- |
| Q1 | | | |
| ... | | | |

## 4. Business rules (readiness vs notebook)

| Rule | Readiness says (section) | Notebook does (cell / decision) | Match |
| --- | --- | --- | --- |
| | | | |

## 5. Data sources (readiness vs notebook)

| Source | Readiness says | Notebook uses | Rows / dates found | Match |
| --- | --- | --- | --- | --- |
| | | | | |

## 6. Features made (plan vs output)

| Plan family | Expected (readiness) | Output columns | Status |
| --- | --- | --- | --- |
| | | | |

## 7. Fill rate

% over all output rows (universe x 28) unless stated. Non-zero excludes sentinel values.

| Feature | % null | % zero | % non-zero | % sentinel | min / max | % non-zero train / test / holdout / c28 | Flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | |

## 8. NBA 3.0 vs NBA 3.1 feature map

| NBA 3.0 feature | In 752? (SHAP rank, % SHAP) | NBA 3.1 feature | Status (preserved / replaced / dropped / new) | Reason |
| --- | --- | --- | --- | --- |
| | | | | |

## 9. HCP trace (step-by-step recompute)

Cases: high volume; window edge (fill on the last day in, on the 1st of next month out); loaded after the prediction month; no fills; type-specific case (e.g. refill / high dose / copay outlier); one training cohort.

| Step | What |
| --- | --- |
| 1 | `PROVIDER_ID` in universe -> NPIs in mapping |
| 2 | Raw rows in source for those NPIs (all dates) |
| 3 | After source filters (NPI not null, fill >= data start, program groups) |
| 4 | Fill <= E |
| 5 | Loaded before `PREDICTION_MONTH` |
| 6 | Inside each window (1 / 3 / 6 / 12M) |
| 7 | Derived values (counts, cap / band, recency, shares) |
| 8 | Output value; match step 7 = step 8 |

## 10. Findings and actions

| # | Finding | Severity (blocker / fix / doc / note) | Action / owner | Status |
| --- | --- | --- | --- | --- |
| F1 | | | | |

## 11. Sign-off

| Item | Value |
| --- | --- |
| Checks passed | <n> / 14 |
| QC by / date | |
| O5 and drift review (NBA team) / date | |
| Reviewed by / date | |
| Next | |
