---
name: promotional-features-qc-eda
description: >
  Validation skill for promotional feature outputs in Kerendia NBA 3.x.
  Independently recomputes values from raw Snowflake/Delta sources for
  per-channel HCP samples and compares against production parquets.
  Enforces 4-outcome model: PASSED / FAILED / NOT_VALIDATED / INCOMPLETE.
  Zero checks is NEVER a pass.
---

# Promotional Features QC — Independent Recomputation Validation (v2)

## Core Rules

### 4-Outcome Model (Mandatory)

| Status | Condition | Meaning |
| --- | --- | --- |
| PASSED | checks > 0 AND mismatches = 0 | Real validation |
| FAILED | mismatches > 0 | Discrepancies found |
| NOT_VALIDATED | checks = 0, no error | Sample had no events in this channel |
| INCOMPLETE | Query error (permission/schema) | Cannot be validated until access granted |

Zero checks is NEVER a pass. The headline MUST say:
`Validated: X/9. Not validated: Y. Blocked: Z.` No checkmark unless X=9.

### Per-Channel Sampling (Mandatory)

For each channel independently: load production output, filter to C01 cohort,
find HCPs with >=1 non-zero feature, sample 2-4 with seed=42.
Different channels WILL have different sampled HCPs. This is correct.

## Data Provenance — Correct Column Names (verified Oct 2026)

| Channel | Source | Key Columns | Filter | Schema |
| --- | --- | --- | --- | --- |
| Calls | PHCDW.PHCDW_CDM.FACT_CALL | BAYER_HCP_ID, CALL_DT, CALL_CHNL_NM, CALL_TYP_NM, CALL_PRPS_NM, CALL_DURATION | UPPER(PROD_NM)='KERENDIA' | default |
| iRep | PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_IREP | ACCT_IDNTFR AS BHID, EMAIL_SENT_DT, EMAIL_CLCKD_FLG, EMAIL_OPND_FLG, EMAIL_STATUS, APPRVD_DOC_NM | acct_idntfr NOT LIKE 'BHO%' AND Email_Status='Delivered' | PHCDW_SANDBOX |
| ClickStream | CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CLKSTRM + FACT_CALL | join on CALL_ID | depends on FACT_CALL | default |
| HQ Emails | PHCDW.PHCDW_CDM.HCP_EMAIL_LIST | BH_ID AS BHID, EVENTDATE, EVENTTYPE | UPPER(EMAILPRODUCTTYPE) LIKE '%KERENDIA%' | default |
| Speaker | CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM | BAYER_HCP_ID, EVNT_START_DATE, EVNT_FMT, EVNT_TYP, EVNT_TPIC_NM | UPPER(ATND)='ATTENDED' AND UPPER(PROD_BRAND_NM)='KERENDIA' | default |
| Samples | CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER | BHID, SMPLE_CALL_DT, SMPLE_CALL_NM, UPPER(SMPLE_NM), SMPLE_QTY, SAMPLE_FLAG | none | default |
| FTP | PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_VOUCHER_FTP | PRSC_NPI, RX_FILL_DT (MM/dd/yyyy), CLAIM_COUNT_NBR, ORGN_CLM_AUTH_NUM | USE_SLS='Y' | PHCDW_SANDBOX |
| Digital | PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB | NPI-keyed | none | sfOptionscdpread (PHCDW_DSAA) |
| DTC | Delta volume (DirectBuys + Social) | DMA_Code, DATA_MONTH | none | N/A |

## Snowflake Access (Oct 2026)

| Schema | Status | Channels |
| --- | --- | --- |
| PHCDW_SANDBOX | Accessible | FTP, iRep |
| CPH_DB_PROD.ANALYTICS_V2 | Accessible | Speaker, Samples |
| PHCDW_CDM (FACT_CALL) | BLOCKED | Calls, ClickStream |
| PHCDW_CDM (HCP_EMAIL_LIST) | BLOCKED | HQ Emails |
| PHCDW_DSAA (MMX) | Not attempted | Digital |

Blocked channels MUST report INCOMPLETE, never PASSED.

## Tolerance

| Type | Method |
| --- | --- |
| Binary flag sums | Exact integer |
| Quantity sums | Exact integer |
| Count features | Exact integer |
| Duration sums | abs < 1e-4 |
| DTC vendor spend | abs < 0.01 |
  Validation skill for promotional feature engineering outputs in the Kerendia NBA 3.x
  pipeline. Read this skill when the user wants to spot-check that feature values generated
  by the 9 promotional feature notebooks are correct by independently recomputing them from
  raw source data for a sample of HCPs. Covers all 9 channels: Calls, iRep, ClickStream
  (personal) and Digital, HQ Emails, Speaker Programs, Samples, FTP, DTC (non-personal).
  Includes step-by-step cell-by-cell intermediate display, side-by-side manual-vs-production
  comparison, tolerance strategy per feature type, and a known-discrepancy self-test.
---

# Promotional Features QC & EDA — Independent Recomputation Validation

This skill generates a QC notebook that independently recomputes promotional feature values
from raw source data for a small sample of HCPs, then compares them step-by-step against
the production notebooks’ output parquet files. It validates that the pipeline code computes
what it claims to compute.

**Companion skills:**
- [personal-promotional-features](../personal-promotional-features/SKILL.md) — Calls, iRep, ClickStream
- [non-personal-promotional-features](../non-personal-promotional-features/SKILL.md) — Digital, HQ Emails, Speaker, Samples, FTP, DTC

---

## When to Read This Skill

Read this skill when the user wants to:
- Validate feature outputs after running any of the 9 promotional notebooks
- Spot-check whether specific feature values are correct for particular HCPs
- Debug a suspected feature computation bug
- Verify a pipeline modification didn’t break existing features
- Independently audit the feature pipeline before a model training run

---

## Architecture

One notebook is reproducible from this skill:

| Notebook | Template File | Cells | Purpose |
| --- | --- | --- | --- |
| `promotional_features_qc` | [promotional-features-qc-template.md](promotional-features-qc-template.md) | ~98 | Independent recomputation + step-by-step comparison |

The notebook has 14 sections:

| Section | Cells | Channels Covered |
| --- | --- | --- |
| A. Setup & Config | ~5 | (shared) |
| B. HCP Sampling | ~4 | (shared) |
| C. Shared Resources | ~3 | (shared) |
| D. Calls QC | ~9 | F2F Sales Rep Calls |
| E. iRep QC | ~8 | iRep Emails |
| F. ClickStream QC | ~10 | ClickStream/CLM |
| G. HQ Emails QC | ~8 | HQ Emails |
| H. Speaker Programs QC | ~8 | Speaker Programs |
| I. Samples QC | ~8 | Samples |
| J. FTP QC | ~10 | Free Trial Program |
| K. Digital QC | ~12 | Digital Engagement |
| L. DTC QC | ~8 | DTC Direct Buy + Meta/IG |
| M. Known-Discrepancy Self-Test | ~3 | (validation) |
| N. Summary | ~2 | (all channels) |

---

## Key Design Decisions

### Step-by-Step Cell-by-Cell Walkthrough

Unlike the rx-feature-qc-eda skill (which computes and compares in bulk), this QC notebook
shows **one logical step per cell** with intermediate `display()` output at every stage.
This lets the user eyeball each step’s intermediate result against the production notebook’s
output at the same step. For example, for a lag feature:

1. Cell: Load raw source data for this HCP → `display()`
2. Cell: Apply filters → `display()`
3. Cell: Compute aggregates → `display()`
4. Cell: Apply spine fill → `display()`
5. Cell: Compute rolling lag → `display()`
6. Cell: Show final + compare against production → `display()`

### Generic HCP Parameterization

The notebook is parameterized by a single variable at the top:

```python
pinned_hcps = None        # None = random sample (seed=42), or list of IDs
SEED = 42                 # Reproducible sampling seed
N_SAMPLE = 4              # Number of HCPs to sample (3-4 default)
```

To test different HCPs, change `pinned_hcps` — no skill regeneration needed.

---

## Sampling Strategy

The QC samples 3–4 HCPs using **activity-based stratified sampling**:

1. Load all 9 production output files
2. Count features with non-zero values per HCP across all channels
3. Rank HCPs by total non-zero feature count, divide into tertiles (active / moderate / sparse)
4. Sample 1–2 from each tertile (total 3–4 HCPs)
5. Display the sample upfront with event/claim counts per HCP per channel

**Why activity-based:** Promotional data is extremely sparse (67–99% zeros). Sampling only
active HCPs would miss the zero-fill behavior; sampling only sparse HCPs would miss bugs
in aggregation logic. Stratified sampling covers both ends.

**ID type note:** Most channels use BHID, but Digital uses NPI and DTC uses DMA. The
sampling cell maps between them:
- BHID → NPI via the NPI-BHID crosswalk (for Digital validation)
- BHID → ZIP → DMA via the DMA-ZIP mapping (for DTC validation)

---

## What the QC Does NOT Treat as Mismatches

* **Cross-channel cohort coverage differences.** Not every HCP appears in all 26 cohorts
  across all channels. The lookback-window filter (`MONTH_ID BETWEEN
  LOOKBACK_START_DATE AND LOOKBACK_END_DATE`) naturally excludes HCPs with no activity
  in older cohort windows. This is correct pipeline behavior, not a bug.
* **Digital column count drift.** The Digital channel's exact column count varies as the
  MMX source gains new CHANNEL/TACTIC_NAME values over time (baseline 665 → 896 as of
  Oct 2026). Validate structurally (`DIGITAL_` prefix, 3 window variants) instead of
  by exact count.
* **Zero-feature rows.** HCPs appearing in one channel's output but with all-zero
  features (due to the fill-spine step) are expected, not mismatches.

---

## Snowflake Access Requirements

The QC notebook queries 8 of 9 channels from Snowflake. Some Snowflake objects have
fragile permission chains. Known access issues (as of Oct 2026):

* `PHCDW.PHCDW_CDM.FACT_CALL` — role `BAY_CPH_CDP_PROD_CR_US_EAST_1_MVXPF_MVXPF`
  lacks `SELECT` privilege. Calls and ClickStream QC are blocked.
* `PHCDW.PHCDW_CDM.HCP_EMAIL_LIST` — view chain depends on
  `CPH_DB_PROD.MODEL.S_EXTA_IMCM_PH_CAMPAIGN` which is not authorized. HQ Emails QC
  is blocked.

Channels with confirmed Snowflake access: **FTP** (`PHCDW_SANDBOX`), **Speaker**
(`CPH_DB_PROD.ANALYTICS_V2`), **Samples** (`CPH_DB_PROD.ANALYTICS_V2`), **iRep**
(`PHCDW_SANDBOX`). If a channel fails, the QC cell catches the error and reports it
without blocking the rest.

---

## Data Provenance

The QC reads from the **same raw sources** as the production notebooks — it does NOT
read from production output and re-derive. This ensures the QC is truly independent.

| Channel | Source Type | Source System | Key Columns (actual Snowflake names) | Auth |
| --- | --- | --- | --- | --- |
| Calls | Snowflake | `PHCDW.PHCDW_CDM.FACT_CALL` + `XREF_CALL` | `BAYER_HCP_ID`, `CALL_DT`, `CALL_CHNL_NM`, `CALL_TYP_NM`, `CALL_PRPS_NM`, `CALL_DURATION` | `Get_Data_Snowflakes()` |
| iRep | Snowflake | `PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_IREP` | `ACCT_IDNTFR` (aliased to BHID), `EMAIL_SENT_DT`, `APPRVD_DOC_NM`, `EMAIL_STATUS`, `EMAIL_CLCKD_FLG` | `Get_Data_Snowflakes(Schema='PHCDW_SANDBOX')` |
| ClickStream | Snowflake | `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CLKSTRM` + `FACT_CALL` | inner join on `CALL_ID` | `Get_Data_Snowflakes()` |
| HQ Emails | Snowflake | `PHCDW.PHCDW_CDM.HCP_EMAIL_LIST` | `BH_ID` (aliased to BHID), `EVENTDATE`, `EVENTTYPE`, `EMAILPRODUCTTYPE` | `Get_Data_Snowflakes()` |
| Speaker | Snowflake | `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_EVNT_PRSNL_PROM` | `BAYER_HCP_ID`, `EVNT_START_DATE`, `EVNT_FMT`, `EVNT_TYP`, `EVNT_TPIC_NM` | `Get_Data_Snowflakes()` |
| Samples | Snowflake | `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER` | `BHID`, `SMPLE_CALL_DT`, `SMPLE_CALL_NM`, `UPPER(SMPLE_NM)`, `SMPLE_QTY`, `SAMPLE_FLAG` | `Get_Data_Snowflakes()` |
| FTP | Snowflake | `PHCDW.PHCDW_SANDBOX.VIEW_RB_KERENDIA_VOUCHER_FTP` | `PRSC_NPI`, `RX_FILL_DT` (MM/dd/yyyy), `CLAIM_COUNT_NBR`, `ORGN_CLM_AUTH_NUM` | `Get_Data_Snowflakes(Schema='PHCDW_SANDBOX')` |
| Digital | Snowflake | `PHCDW.PHCDW_CDM.MMX_FNL_COMBINED_AGGR_TAB` | `sfOptionscdpread` (different warehouse) |
| DTC | Delta volume | Consolidated Delta tables (DirectBuys + Social) | `spark.read.format("delta")` |

The QC notebook requires Snowflake access for 8 of 9 channels. It defines
`Get_Data_Snowflakes()` and `sfOptionscdpread` inline (see Section A of the template).

---

## Floating-Point Tolerance Strategy

| Feature Type | Comparison | Rationale |
| --- | --- | --- |
| Binary flag sums (Calls, iRep, HQ Emails, Speaker, Samples flags) | Exact integer equality | SUM of 0/1 → always integer |
| Quantity sums (Samples QTY) | Exact integer equality | SUM of integer SMPLE_QTY |
| Count features (FTP TOTAL_RX_FTP) | Exact integer equality | COUNT(1) → always integer |
| Running total (FTP) | Exact integer equality | Cumulative integer count |
| Cross-product features (Calls) | Exact integer equality | `least()` on binary → 0/1, summed |
| DTC impressions/clicks | Exact integer equality | SUM of integer counts |
| Duration sums (ClickStream) | abs(m − n) < 1e-4 | SUM of float durations |
| Duration averages (ClickStream) | abs(m − n) < 1e-4 | AVG → float division |
| Digital engagement metrics | abs(m − n) < 1e-4 | SUM of floats through monthly windows |

Tolerance 1e-4: loose enough to absorb distributed float arithmetic differences, tight
enough that real bugs produce deltas orders of magnitude larger.

---

## Per-Channel Recomputation Sequences

Each channel follows the same pattern: load raw → filter → create flags → cross-join cohort
→ aggregate → fill spine → compute lags → filter to anchor date → compare vs production.

### D. Calls (9 cells)
1. Load raw from FACT_CALL + XREF, filter KERENDIA/SUBMITTED_VOD, filter sampled BHIDs
2. Create 15 binary flags (4 channel + 5 call_type + 5 purpose + 1 duration)
3. Create 20 cross-product features via `least(channel, call_type)`
4. Cross-join with cohort dates, filter lookback window
5. GroupBy aggregate (SUM per HCP_COHORT_ID × MONTH_ID)
6. step2_fill_missing_dates (daily spine)
7. step3_lag_date (6 windows: 30–180 days)
8. Filter to LOOKBACK_END_DATE, show final manual values
9. Load production parquet, compare all 212 features

### E. iRep (8 cells)
1. Load from VIEW_RB_KERENDIA_IREP, filter Delivered + date, sampled BHIDs
2. Create 14 binary flags (3 delivery + 11 doc-name categories with exact `.isin()` lists)
3. Cross-join cohort, filter lookback, create HCP_COHORT_ID
4. GroupBy aggregate → 14 TOTAL_ features
5. step2_fill_missing_dates
6. step3_lag_date (6 windows) → 84 lag features
7. Filter, show final manual values
8. Load production, compare 86 columns

### F. ClickStream (10 cells)
1. Load ANLT_BASE_FACT_CLKSTRM, filter KERENDIA
2. Dedup per CALL_ID (`row_number()` by USAGE_DUR DESC, PRESN_DUR DESC)
3. Load calls, inner join on CALL_ID (SUBMITTED_VOD), show silent-drop count
4. Filter to sampled BHIDs, display raw events
5. Cross-join cohort, filter lookback
6. GroupBy aggregate (SUM + AVG of durations) → 4 base features
7. step2_fill_missing_dates
8. step3_lag_date (6 windows) → 24 lag features
9. Add CLICKSTREAM_ prefix, show final
10. Load production, compare 26 columns

### G. HQ Emails (8 cells)
1. Load from HCP_EMAIL_LIST, filter KERENDIA, sampled BHIDs
2. Create 5 event-type flags (Bounce, Click, Open, Sent, Unsubscribe)
3. Cross-join cohort, filter lookback
4. GroupBy aggregate → 5 TOTAL_ features
5. step2_fill_missing_dates
6. step3_lag_date (6 windows) → 30 lag features
7. Filter, show final
8. Load production, compare 32 columns

### H. Speaker Programs (8 cells)
1. Load from ANLT_BASE_FACT_EVNT_PRSNL_PROM, filter KERENDIA/ATTENDED, sampled BHIDs
2. Create 11 flags (5 format + 2 type + 4 topic, exact `.isin()` values)
3. Cross-join cohort, filter lookback
4. GroupBy aggregate → 11 TOTAL_ features
5. step2_fill_missing_dates
6. step3_lag_date (6 windows) → 66 lag features
7. Filter, show final
8. Load production, compare 68 columns

### I. Samples (8 cells)
1. Load from ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER (BHID direct), sampled BHIDs
2. Create 20 dual FLAG+QTY features (7 name×2 + 2 status×2 + 1 overall×2), exclude brochures
3. Cross-join cohort, filter lookback
4. GroupBy aggregate → 20 TOTAL_ features
5. step2_fill_missing_dates
6. step3_lag_date (6 windows) → 120 lag features
7. Filter, show final
8. Load production, compare 122 columns

### J. FTP (10 cells)
1. Load from VIEW_RB_KERENDIA_VOUCHER_FTP (correct aliases: PRSC_NPI→PROVIDER_ID, etc.)
2. Parse date `MM/dd/yyyy HH:mm:ss`, cast DAY_SUPPLY/ROW_COUNT to int
3. Reversal handling: group by ORGN_CLM_AUTH_NUM, anti-join net-zero/negative groups
4. Show post-reversal data, display before/after counts
5. NPI→BHID mapping, show join result
6. GroupBy aggregate (COUNT(1)) → TOTAL_RX_FTP
7. Cross-join cohort, filter lookback
8. step2_fill_missing_dates + step3_lag_date (6 windows) + RUNNING_TOTAL
9. Filter, show final manual values
10. Load production, compare 9 columns

### K. Digital (12 cells)
1. Load from MMX_FNL_COMBINED_AGGR_TAB via sfOptionscdpread, filter KERENDIA, exclude CALLS/SAMPLES
2. Filter to sampled NPIs, display raw data
3. Pivot 1 (by CHANNEL), prefix CH_, filter None from values
4. Pivot 2 (by SRC_SYS_CD), prefix SRC_
5. Pivot 3 (by TACTIC_NAME), prefix TAC_
6. Join 3 pivots on [NPI_NUMBER, SVC_DT_M], sanitize column names
7. step2_fill_missing (monthly spine, DATE cast for sequence)
8. step3_lag (monthly, windows [1,3,6])
9. Drop zero-variance (stddev > 0)
10. Add DIGITAL_ prefix via .toDF()
11. Show final manual values
12. Load production, compare ~665 columns

### L. DTC (8 cells)
1. Map sampled HCPs to DMA codes (BHID → ZIP_CODE_GEO → DMA_Code), show chain
2. Load Direct Buy Delta, filter to sampled DMAs
3. Pivot by vendor, sanitize + DTC_PROMOTION_ prefix
4. Load Social Delta, pivot by vendor
5. Merge Direct Buy + Social on [DMA_Code, DATA_MONTH]
6. Show final manual values at DMA level
7. Load production, compare 10 features per DMA×month
8. Trace one HCP’s full join path: HCP → ZIP → DMA → DTC values

---

## DTC Geographic Grain Handling

DTC is the only channel at DMA (geographic) level, not HCP level.

**Resolution path for QC:** sampled BHID → HCP universe (has ZIP_CODE_GEO) → DMA-ZIP
mapping parquet → DMA_Code.

The DMA-ZIP mapping is at:
```
/Volumes/.../hcp_level_features/notebook_output/DTC/DMA Zip Mapping.parquet
```

**Comparison grain:** DTC features are compared at DMA×month level (not HCP level). This
is legitimate — all HCPs in the same DMA share identical DTC values by design.

**Trace cell:** The template includes an explicit cell (L8) that walks one sampled HCP
through the full chain: `BHID → ZIP_CODE_GEO → DMA_Code → DTC feature values`. This makes
the geographic fan-out visible.

---

## Known-Discrepancy Self-Test

The QC notebook includes a self-test (Section M) that:
1. Takes one HCP_COHORT_ID from the Calls channel sample
2. Creates a copy of the production output with one feature value corrupted (+999)
3. Re-runs the comparison against the corrupted output
4. Confirms the mismatch is detected with the correct delta (999)

This prevents the “QC silently stopped working” failure mode — a QC that only reports
“all passed” is indistinguishable from one that checks nothing.

---

## What the QC Can Catch

- Wrong flag definition (e.g., wrong `.isin()` values for iRep doc categories)
- Wrong aggregation function (e.g., SUM vs COUNT, SUM vs AVG)
- Wrong lookback window filter bounds
- Wrong lag window sizes or window frame boundaries
- Wrong cross-product formula (e.g., `greatest` instead of `least` for Calls)
- Missing reversal removal (FTP)
- Wrong NPI→BHID mapping or missing join
- DMA join path errors
- Digital pivot NULL contamination
- Digital zero-variance column pruning differences
- Missing brochure exclusion (Samples)
- Wrong date parsing (FTP `MM/dd/yyyy HH:mm:ss`)
- ClickStream dedup logic errors (wrong ORDER BY in row_number)
- Speaker topic case-sensitivity bugs

## What the QC Cannot Catch

- **Bugs in Snowflake source views** — data quality issues upstream of the views/tables
- **Dynamic pivot value differences** — if the set of CHANNEL/TACTIC_NAME values in the
  source changed between the production run and the QC run, column sets will differ
- **Semantic correctness** — whether `least(F2F, DETAIL_WITH_SAMPLE)` is the right formula
  for a cross-product is a design question, not a code bug
- **Issues outside the 3–4 HCP sample** — edge cases not represented in the sample
- **Upstream data extraction bugs** — Snowflake → view creation pipeline issues
- **Topic/doc-name categorization completeness** — the ~50% uncategorized iRep/Speaker
  values are a known limitation, not a bug in the categorized ones

---

## Production Output Paths

All outputs read from:
```
/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_volume/
  hcp_level_model/dev_folder/notebook_output/
```

| Channel | File Name | Key Columns |
| --- | --- | --- |
| Calls | `kerendia_nba_3_hcp_model_call_features.parquet` | HCP_COHORT_ID |
| iRep | `kerendia_nba_3_hcp_model_irep_features.parquet` | HCP_COHORT_ID |
| ClickStream | `kerendia_nba_3_hcp_model_clickstream_features.parquet` | HCP_COHORT_ID |
| HQ Emails | `kerendia_nba_3_hcp_model_hq_email_features.parquet` | HCP_COHORT_ID |
| Speaker | `kerendia_nba_3_hcp_model_speaker_program.parquet` | HCP_COHORT_ID |
| Samples | `kerendia_nba_3_hcp_model_samples_features.parquet` | HCP_COHORT_ID |
| FTP | `kerendia_nba_3_hcp_model_ftp_features.parquet` | HCP_COHORT_ID |
| Digital | `kerendia_nba_3_0_hcp_model_paid_search_features.parquet` | NPI_NUMBER, SVC_DT_M |
| DTC + Meta/IG | `kerendia_nba_3_hcp_model_DTC_PROMOTION.parquet` | DMA_Code, DATA_MONTH |

---

## How to Use This Skill

1. Read this SKILL.md for the architecture, provenance, tolerance, and limitations.
2. Open [promotional-features-qc-template.md](promotional-features-qc-template.md) for the
   cell-by-cell blueprint.
3. Create a new notebook named `promotional_features_qc`.
4. Follow the template section by section. Each section header maps to a cell.
5. Run the notebook. Review intermediate outputs at each step.
6. Check the Summary section (N) for total pass/fail counts and any mismatches.
7. To test different HCPs, change `pinned_hcps` at the top — no regeneration needed.
