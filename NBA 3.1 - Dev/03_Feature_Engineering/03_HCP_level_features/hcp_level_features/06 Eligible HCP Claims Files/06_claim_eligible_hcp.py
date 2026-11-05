# Databricks notebook source
# DBTITLE 1,Title
# MAGIC %md
# MAGIC # Eligible Patient Features (Rx x Patient Eligibility) — All Cohorts
# MAGIC
# MAGIC Cohort-based refactor of `06_claim_eligible_hcp` (NBA 3.0, Wenjie Chen). Sections 1–3 walk through every table the original uses; sections 4–6 rebuild the same features per cohort (windows of 1, 3, 6, 12 months ending at each cutoff, `RUNNING_`, `PCT_`, `DIALYSIS_FLAG`), write one row per NPI per `COHORT_ID` to `claim_eligible_patient_cohort` and `provider_claim_eligible_patient_cohort`, and validate against the original.
# MAGIC
# MAGIC Source: `/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/06_claim_eligible_hcp`. The original wrote `notebook_output/kerendia_nba_3_0_claim_eligible_patient`; this notebook never writes to a 3.0 table.

# COMMAND ----------

# DBTITLE 1,What this notebook does
# MAGIC %md
# MAGIC ## What this notebook does, in plain words
# MAGIC
# MAGIC For every HCP it counts **how many of the patients it wrote an Rx claim for were eligible for Kerendia** in that month, using the patient journey eligibility table (`pat_sglt2_filter_m`, built by `06_patient_journey_combine`).
# MAGIC
# MAGIC | Feature | Question it answers | Column |
# MAGIC | --- | --- | --- |
# MAGIC | Total | How many eligible patients did the HCP see (Rx claim) in the window? | `TOTAL_ELIGIBLE_PATIENTS_...` (also the `PCT_` denominator) |
# MAGIC | By GFR / Dx stage | ... split by the patient's CKD stage that month | `TOTAL_ELIGIBLE_PATIENTS_GFR_DX_STAGE_{2,3,4,UNKNOWN}_...` |
# MAGIC | By UACR stage | ... split by the patient's UACR stage that month | `TOTAL_ELIGIBLE_PATIENTS_UACR_STAGE_{2,3,UNKNOWN}_...` |
# MAGIC | Shares | Stage count / total in the same window | `PCT_...` |
# MAGIC | Dialysis | Did any patient of the HCP's Rx claims in the cohort month already have dialysis? | `DIALYSIS_FLAG` (0/1) |
# MAGIC | Diabetes type (new 2026-11-06) | How many of the HCP's Rx patients (all / eligible) are T2D, T1D, other or no diabetes? | `TOTAL_RX_PATIENTS_DM_TYPE_{T2D,T1D,OTHER,NONE}_...`, `TOTAL_ELIGIBLE_PATIENTS_DM_TYPE_..._...` |
# MAGIC | HF and HF type (new 2026-11-06) | ... how many have heart failure that month, by HF type (HFpEF / HFrEF proxy from the HF codes, mixed, unknown)? | `TOTAL_RX_PATIENTS_HF_...`, `_HF_TYPE_{HFPEF_PROXY,HFREF_PROXY,MIXED,UNKNOWN}_...` (and `TOTAL_ELIGIBLE_PATIENTS_...`) |
# MAGIC | Shares (new) | Count / all Rx patient-months (`TOTAL_RX_PATIENTS_...`) or / eligible patient-months | `PCT_RX_PATIENTS_...`, `PCT_ELIGIBLE_PATIENTS_...` |
# MAGIC
# MAGIC **Eligible patient-month** (set by the patient journey, not here): GFR / Dx stage 2–4 and not on dialysis, or stage unknown and SGLT2 use. Open patient-journey decisions C1 (SGLT2 rule) and C9 (diabetes requirement) change `ELIGIBLE_PATIENT_FLAG` only; this notebook needs a re-run, no code change.
# MAGIC
# MAGIC **Counting rule:** one count per (HCP, patient, month), as the original. A window adds up the monthly counts of the last N months, so a patient seen in 3 different months counts 3 times in `_IN_LAST_3_MONTH` (decision D1). Note: the 3.0 original stored the **mean of N+1 monthly counts** in its `_IN_LAST_N_MONTH` columns (found in the 2026-11-03 parity run); the refactor keeps the sum, like NB01-NB05, so the offset-0 parity differs on the window columns only.
# MAGIC
# MAGIC **Decisions applied (2026-11-03):**
# MAGIC * D1 (confirmed 2026-11-03): window = sum of the monthly patient counts of the last N months (3.0 used the mean of N+1 months; not kept).
# MAGIC * D2: `DIALYSIS_FLAG` = the cohort month only (as 3.0's monthly flag), not windowed.
# MAGIC * D3 (done 2026-11-06, team feedback): diabetes-type and HF-type split of all and eligible Rx patients, windows 1 / 3 / 6 / 12 months, 148 columns (section 4b). Source: PJ04 `kerendia_nba_3_1_dm_hf_flags_validation` (`DM_TYPE`, `HF_TYPE`, `HF_FIRST_DATE`) in the patient-journey run folder; HF in a month = month on or after the month of `HF_FIRST_DATE` (same rule as the monthly `HF_FLAG` of PJ06). Kerendia's indications are CKD with T2D and HF with LVEF >= 40% (HFpEF proxy).
# MAGIC
# MAGIC **How to read this notebook:** section 1 shows each input table; section 2 the patient-month table the original counts; section 3 the original output. Everything is shown for the 10 test HCPs (validation mode).

# COMMAND ----------

# DBTITLE 1,Section: Connection and Config
# MAGIC %md
# MAGIC ## 0. Connection and config

# COMMAND ----------

# DBTITLE 1,00_connection
# MAGIC %run "/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/00_Helper_Notebooks/00_connection"

# COMMAND ----------

# DBTITLE 1,Load cohort config
# MAGIC %run "../../00_cohort_config"

# COMMAND ----------

# DBTITLE 1,Section: Input tables
# MAGIC %md
# MAGIC ## 1. The input tables
# MAGIC
# MAGIC The original reads three tables. The cell below loads them; each following cell shows one of them.
# MAGIC
# MAGIC * **Rx claims** (`Rx_01_new`): only which HCP saw which patient on which day is used. Filtered to the 10 test HCPs.
# MAGIC * **Patient eligibility per month** (`pat_sglt2_filter_m`) and **first dialysis date** (Px journey) are keyed on the *patient*, so they are shown only for the patients of those HCPs' Rx claims.
# MAGIC * Table names come from `HCP_PATIENT_TABLES` in `00_cohort_config`: validation mode reads the 3.1 patient-journey validation tables, production the 3.0 tables (until the 3.1 production tables exist).

# COMMAND ----------

# DBTITLE 1,Load all input tables
import builtins, re, time
import numpy as np
import pandas as pd

# Paths, windows and patient tables come from 00_cohort_config (HCP shared constants)
_QUERY_OUTPUT    = HCP_QUERY_OUTPUT
_NOTEBOOK_OUTPUT = HCP_NOTEBOOK_OUTPUT

# Rx claims: the only Rx columns the original uses. Validation mode keeps only the 10 test HCPs.
# 3.1 (C2, plan in 06 Eligible HCP Claims Files/): from DATA_START_DATE the HCP Rx pull of the 3.1 Rx journey
# (HCP_RX_TABLE, same claims as NB01 / NB04); before it the 3.0 Rx_01_new (walkthrough and column list only,
# never counted). HCP_RX_SOURCE = "3.0" gives Rx_01_new only.
_RX_COLS = [NPI_COL, F.col("PATIENT_ID").cast("string").alias("PATIENT_ID"), F.to_date(SVC_COL).alias(SVC_COL)]
_rx_new  = spark.read.format("delta").load(hcp_input_path(HCP_RX_TABLE)).select(*_RX_COLS)   # 3.1 pull: full path (3.1 volume)
if HCP_RX_TABLE.rstrip("/").endswith("Rx_01_new"):
    df_rx_raw = _rx_new
else:
    _rx_old = (spark.read.format("delta").load(_QUERY_OUTPUT + "Rx_01_new").select(*_RX_COLS)
               .filter(F.col(SVC_COL) < F.lit(DATA_START_DATE)))
    df_rx_raw = _rx_new.filter(F.col(SVC_COL) >= F.lit(DATA_START_DATE)).unionByName(_rx_old)
df_rx = apply_npi_filter(df_rx_raw, NPI_COL)
print(f"Rx input: {HCP_RX_TABLE} (+ Rx_01_new before {DATA_START_DATE})")
# df_rx keeps the full history (walkthrough, fixed column list and offset-0 parity, as NB01-NB05).
# DATA_START_DATE (team rule, RUNNING_ included) is applied to the counted claims in section 4.

# Patient eligibility per month (patient journey combine) and first dialysis date (Px journey)
_ELIG_PATH = get_patient_table_path("sglt2_filter_m")
_PX_PATH   = get_patient_table_path("px")
pat_elig = spark.read.format("delta").load(_ELIG_PATH)
pat_px   = spark.read.format("delta").load(_PX_PATH)

# Rows of the patient-keyed tables that belong to the patients of this run's Rx claims
_rx_patients  = df_rx.select("PATIENT_ID").distinct()
pat_elig_view = pat_elig.join(_rx_patients, on="PATIENT_ID", how="left_semi")
pat_px_view   = pat_px.join(_rx_patients, on="PATIENT_ID", how="left_semi")

print(f"Eligibility table: {_ELIG_PATH}")
print(f"Dialysis table   : {_PX_PATH}")
if VALIDATION_MODE:   # counts on all-US tables are skipped in production
    print(f"Rx claims: {df_rx.count():,} rows | NPIs: {df_rx.select(NPI_COL).distinct().count()} | "
          f"patients: {_rx_patients.count():,}")
    print(f"Eligibility rows of those patients: {pat_elig_view.count():,} | dialysis rows: {pat_px_view.count():,}")

# COMMAND ----------

# DBTITLE 1,Section: Rx claims
# MAGIC %md
# MAGIC ### 1.1 Rx claims (`Rx_01_new`)
# MAGIC One row per Rx claim. The original keeps only the distinct (HCP, patient, month): a patient with 5 claims at one HCP in a month counts once that month.

# COMMAND ----------

# DBTITLE 1,Display: Rx claims
display(df_rx.groupBy(NPI_COL)
        .agg(F.count("*").alias("rx_claims"), F.countDistinct("PATIENT_ID").alias("patients"),
             F.min(SVC_COL).alias("first_claim"), F.max(SVC_COL).alias("last_claim"))
        .orderBy(NPI_COL))

# COMMAND ----------

# DBTITLE 1,Section: Patient eligibility table
# MAGIC %md
# MAGIC ### 1.2 Patient eligibility per month (`pat_sglt2_filter_m`)
# MAGIC One row per patient per month, built by the patient journey combine.
# MAGIC * `ELIGIBLE_PATIENT_FLAG` (0/1) = eligible that month. Only flag 1 rows are counted.
# MAGIC * `GFR_DX_STAGE` (`STAGE_2`..`STAGE_4`, `STAGE_UNKNOWN`) and `UACR_STAGE` (`STAGE_2`, `STAGE_3`, `STAGE_UNKNOWN`) = labels used for the stage columns.
# MAGIC
# MAGIC Tables below: sample rows, rows per flag x stage, and a uniqueness check (one row per patient-month means the join cannot double-count a patient).

# COMMAND ----------

# DBTITLE 1,Display: Patient eligibility table
display(pat_elig_view.orderBy("PATIENT_ID", "SVC_DT_M").limit(20))
display(pat_elig_view.groupBy("ELIGIBLE_PATIENT_FLAG", "GFR_DX_STAGE", "UACR_STAGE").count()
        .orderBy("ELIGIBLE_PATIENT_FLAG", "GFR_DX_STAGE", "UACR_STAGE"))
_n_e = pat_elig_view.count()
_k_e = pat_elig_view.select("PATIENT_ID", "SVC_DT_M").distinct().count()
print(f"Rows: {_n_e:,} | distinct (patient, month): {_k_e:,} | duplicates: {_n_e - _k_e:,} "
      f"(0 = one row per patient-month)")

# COMMAND ----------

# DBTITLE 1,Section: Dialysis table
# MAGIC %md
# MAGIC ### 1.3 First dialysis date (Px journey)
# MAGIC One row per patient with a dialysis procedure: `FIRST_DIALYSIS_DATE`. The original only uses this date (the constant `DIALYSIS_FLAG` column of the 3.0 table is not used).

# COMMAND ----------

# DBTITLE 1,Display: Dialysis table
_px_d = pat_px_view.withColumn("_FDD", F.to_date("FIRST_DIALYSIS_DATE"))
print(f"Patients with a first dialysis date: {_px_d.count():,} | distinct: {_px_d.select('PATIENT_ID').distinct().count():,} | "
      f"before 2017: {_px_d.filter(F.col('_FDD') < F.lit('2017-01-01')).count():,} | "
      f"date not readable: {_px_d.filter(F.col('_FDD').isNull()).count():,}")
display(_px_d.groupBy(F.year("_FDD").alias("first_dialysis_year")).count().orderBy("first_dialysis_year"))

# COMMAND ----------

# DBTITLE 1,Section: Claim-level joins
# MAGIC %md
# MAGIC ## 2. The patient-month table the original counts
# MAGIC
# MAGIC The original joins the distinct (HCP, patient, month) of the Rx claims to the eligibility table on patient + month and keeps `ELIGIBLE_PATIENT_FLAG = 1`. Each remaining row adds 1 to the total, 1 to its GFR / Dx stage column and 1 to its UACR stage column.
# MAGIC
# MAGIC The dialysis flag uses **all** Rx patients of the HCP that month (eligible or not): 1 when any of them had a first dialysis on or before the claim day (or before 2017).
# MAGIC
# MAGIC In the cohort version the month is the claim's cohort month (`assign_cohort_month`, = calendar month at offset 0), as in NB01-NB05. The helper functions below are used by the walkthrough, the features and the parity check.

# COMMAND ----------

# DBTITLE 1,Claim-level helpers
_DIALYSIS_BEFORE = "2017-01-01"   # original rule: a first dialysis before this date counts as on dialysis

def eligible_patient_months(df_rx_in, pat_elig_df, offset_days):
    """One row per (NPI, patient, cohort month) where the patient is eligible that month: the original
    distinct (NPI_NUMBER, PATIENT_ID, SVC_DT_M) joined to pat_sglt2_filter_m, ELIGIBLE_PATIENT_FLAG = 1.
    SVC_DT = the patient's first claim day with the NPI in that cohort month (windows start and end on
    cohort-month boundaries, so any day of the month gives the same windows)."""
    rx = (df_rx_in.withColumn("_M", assign_cohort_month(F.col(SVC_COL), offset_days))
          .groupBy(NPI_COL, "PATIENT_ID", "_M").agg(F.min(SVC_COL).alias(SVC_COL)))
    e = (pat_elig_df.filter(F.col("ELIGIBLE_PATIENT_FLAG") == 1)
         .select("PATIENT_ID", F.to_date("SVC_DT_M").alias("_M"), "GFR_DX_STAGE", "UACR_STAGE"))
    return rx.join(e, on=["PATIENT_ID", "_M"], how="inner")


def build_dialysis_claims(df_rx_in, px_df):
    """(NPI, SVC_DT, DIALYSIS_FLAG): 1 when any patient of the NPI's Rx claims that day already had a
    first dialysis (on or before the claim day, or before 2017), as the original "Adding Dialysis flag"."""
    px = px_df.select("PATIENT_ID", F.to_date("FIRST_DIALYSIS_DATE").alias("_FDD"))
    return (df_rx_in.select(NPI_COL, "PATIENT_ID", SVC_COL).distinct()
            .join(px, on="PATIENT_ID", how="left")
            .withColumn("DIALYSIS_FLAG", F.when(F.col("_FDD") < F.to_date(F.lit(_DIALYSIS_BEFORE)), 1)
                                          .when(F.col("_FDD") <= F.col(SVC_COL), 1).otherwise(0))
            .groupBy(NPI_COL, SVC_COL).agg(F.max("DIALYSIS_FLAG").alias("DIALYSIS_FLAG")))

# COMMAND ----------

# DBTITLE 1,Display: eligible patient-months per HCP
# Per HCP: patient-months with an Rx claim, how many are eligible, and by stage (run offset, full history)
_pm_all_view = (df_rx.withColumn("_M", assign_cohort_month(F.col(SVC_COL), OFFSET_DAYS))
                .select(NPI_COL, "PATIENT_ID", "_M").distinct())
_pm_elig_view = eligible_patient_months(df_rx, pat_elig_view, OFFSET_DAYS)
display(_pm_all_view.groupBy(NPI_COL).agg(F.count("*").alias("patient_months"))
        .join(_pm_elig_view.groupBy(NPI_COL).agg(
                  F.count("*").alias("eligible_patient_months"),
                  F.countDistinct("PATIENT_ID").alias("eligible_patients"),
                  *[F.sum((F.col("GFR_DX_STAGE") == s).cast("int")).alias(f"gfr_{s.lower()}")
                    for s in ["STAGE_2", "STAGE_3", "STAGE_4", "STAGE_UNKNOWN"]]),
              on=NPI_COL, how="left")
        .orderBy(NPI_COL))

# COMMAND ----------

# DBTITLE 1,Section: Original output
# MAGIC %md
# MAGIC ## 3. The original output (3.0)
# MAGIC
# MAGIC `kerendia_nba_3_0_claim_eligible_patient` from the 3.0 reference snapshot (`ops_pipeline_bkp/`), for the test providers: one row per provider per calendar month from 2022-01, 86 columns (base month, `_IN_LAST_{1,3,6,12}_MONTH`, `RUNNING_`, `PCT_`, `DIALYSIS_FLAG`, `PROVIDER_ID`).

# COMMAND ----------

# DBTITLE 1,Display: Original output
_orig_path = HCP_REF_NOTEBOOK_OUTPUT + "kerendia_nba_3_0_claim_eligible_patient"
_npis_v = get_test_npis()
if hcp_ref_missing([_orig_path, HCP_REF_QUERY_OUTPUT + HCP_NPI_MAPPING_TABLE]):
    print("SKIPPED: 3.0 reference output or mapping missing")
else:
    _map_v = load_ref_input(HCP_NPI_MAPPING_TABLE).select(NPI_COL, "PROVIDER_ID").distinct()
    _map_v = _map_v.filter(F.col(NPI_COL).isin(_npis_v)) if _npis_v else _map_v
    _orig_v = spark.read.format("delta").load(_orig_path).join(_map_v, on="PROVIDER_ID", how="inner")
    print(f"Original: {len(_orig_v.columns) - 1} columns | rows for these providers: {_orig_v.count():,}")
    display(_orig_v.groupBy(NPI_COL, "PROVIDER_ID")
            .agg(F.count("*").alias("months"), F.min("SVC_DT_M").alias("first_month"), F.max("SVC_DT_M").alias("last_month"),
                 F.sum("TOTAL_ELIGIBLE_PATIENTS").alias("eligible_patient_months"),
                 F.sum("DIALYSIS_FLAG").alias("months_with_dialysis_flag"))
            .orderBy(NPI_COL))

# COMMAND ----------

# DBTITLE 1,Walkthrough findings
# MAGIC %md
# MAGIC ### Walkthrough findings (3.0 notebook)
# MAGIC
# MAGIC 1. **The original overwrote a 3.0 production table** (`notebook_output/kerendia_nba_3_0_claim_eligible_patient`). This notebook writes only the two `*_cohort` tables.
# MAGIC 2. It ran Wenjie's 3.0 helpers (`00_config`, `00_step23_function`, `00_Physician_Filter`); now only `00_connection` + `../00_cohort_config`, as NB01-NB05.
# MAGIC 3. Paths of the eligibility and dialysis tables were typed in the notebook; now `HCP_PATIENT_TABLES` (keys `sglt2_filter_m`, `px`).
# MAGIC 4. NPI to `PROVIDER_ID` came from a Snowflake query on `STG_CAR_IQV_LAAD_DIM_PRVDR`; now the shared `kerendia_nba_3_0_npi_bhid_mapping` table, as NB01-NB04.
# MAGIC 5. Start month typed as `2022-01-01`; now `DATA_START_DATE` (team rule, `RUNNING_` included) and the shared cohort list.
# MAGIC 6. Header was out of date (data sources `IQV_LAAD_RX_VW` / `finerenone_intermediate`, 2017, April 2021, old eligibility rule).
# MAGIC 7. The dialysis flag uses all Rx patients of the HCP, not only eligible ones, and is joined after the windows (not windowed). Kept as in 3.0 (D2).
# MAGIC 8. Stage columns came from the values in the data (`pivot` without a list); now a fixed list (the 3.0 columns + any other value in the full history), so every cohort has the same columns.
# MAGIC 9. `PCT_` columns were built with `exec`; now plain expressions, same formula (count / total in the same window, 0.0 when the total is 0).

# COMMAND ----------

# DBTITLE 1,Section: Cohort features
# MAGIC %md
# MAGIC ## 4. Cohort features (the refactor)
# MAGIC
# MAGIC Same feature logic as the original, rebuilt per cohort (windows ending at each cohort cutoff, as in NB01-NB05):
# MAGIC
# MAGIC 1. **Feature rows (once):** every eligible (HCP, patient, cohort month) becomes three +1 rows: `TOTAL_ELIGIBLE_PATIENTS`, its GFR / Dx stage column, its UACR stage column. The dialysis flag is built per (HCP, claim day).
# MAGIC 2. **Per cohort (`build_cohort`, reference):** keep rows up to the cutoff, tag each row with the windows it falls in (last 1/3/6/12 months, `RUNNING_` = all counted history) and pivot into one row per NPI; `PCT_` = count / total in the same window; `DIALYSIS_FLAG` = max over the Rx claims of the cohort month.
# MAGIC 3. **All cohorts (`build_all_cohorts_fast`, used for the output):** the shared engine of `00_cohort_config` (rows summed per NPI x cohort month, one pivot for all cohorts). The check cell compares it with `build_cohort` on the first and last cohort.
# MAGIC
# MAGIC Rules kept from the original: column names use the original cleaning; base-month columns of the original are the `_IN_LAST_1_MONTH` columns here; no `PCT_` for `RUNNING_`.

# COMMAND ----------

# DBTITLE 1,Feature rows (once) and cohort list
ELIG_LOOKBACK_WINDOWS = HCP_LOOKBACK_WINDOWS["eligible"]   # original last_i_month_list (1, 3, 6, 12)
TOTAL_COL = "TOTAL_ELIGIBLE_PATIENTS"
_PFX_GFR  = TOTAL_COL + "_GFR_DX_"
_PFX_UACR = TOTAL_COL + "_UACR_"
# Original column cleaning (cells "GFR CKD Dx Stage" / "UACR Stage"), in order
_CLEAN_STEPS = [(", ", " "), ("/", "_OR_"), ("+", "_AND_"), ("-", "_"), (" ", "_"), ("__", "_")]
# Stage columns of the 3.0 output: always built, so every cohort has them
BASE_STAGE_FEATURES = ([_PFX_GFR + s for s in ["STAGE_2", "STAGE_3", "STAGE_4", "STAGE_UNKNOWN"]] +
                       [_PFX_UACR + s for s in ["STAGE_2", "STAGE_3", "STAGE_UNKNOWN"]])

def clean_name_06(c):
    for a, b in _CLEAN_STEPS:
        c = F.regexp_replace(c, re.escape(a), b)
    return F.upper(c)

def _stage_feat(prefix, colname):
    """prefix + cleaned stage label; a null stage is named 'null' (as the original pivot)."""
    return F.concat(F.lit(prefix), clean_name_06(F.coalesce(F.col(colname).cast("string"), F.lit("null"))))

def build_feature_rows(pm):
    """(NPI, SVC_DT, FEATURE, N): every eligible patient-month adds 1 to the total, its GFR / Dx stage
    and its UACR stage (original count(lit(1)) after the pivot)."""
    return (pm.select(NPI_COL, SVC_COL, F.array(F.lit(TOTAL_COL), _stage_feat(_PFX_GFR, "GFR_DX_STAGE"),
                                               _stage_feat(_PFX_UACR, "UACR_STAGE")).alias("_F"))
            .select(NPI_COL, SVC_COL, F.explode("_F").alias("FEATURE"))
            .groupBy(NPI_COL, SVC_COL, "FEATURE").agg(F.count(F.lit(1)).alias("N")))

def feature_values_of(df_feat_in):
    """Fixed column list: total, then the 3.0 stage columns + any other stage value in the rows."""
    _data = {r[0] for r in df_feat_in.select("FEATURE").distinct().collect()}
    return [TOTAL_COL] + sorted((set(BASE_STAGE_FEATURES) | _data) - {TOTAL_COL})

# Staging prefix for the shared materialize() in 00_cohort_config (in memory in validation mode)
_STAGE_PREFIX = HCP_STAGE_OUTPUT + "claim_eligible_patient_cohort_stage_"   # 3.1 volume, hcp_claims_features/_stage/

# ---------- Cohorts to process: every cohort whose cutoff is within the data of all HCP inputs ----------
DATA_MAX_DT   = df_rx_raw.agg(F.max(SVC_COL)).first()[0]
COHORT_LIST   = get_hcp_cohort_months()   # common end date of all HCP inputs (00_cohort_config)
COHORT_BOUNDS = {m: get_cohort_bounds(m) for m in COHORT_LIST}
COHORT_IDS    = [COHORT_BOUNDS[m]["cohort_id"] for m in COHORT_LIST]
PREVIEW_COHORT = COHORT_MONTH if COHORT_MONTH in COHORT_LIST else COHORT_LIST[0]
cb_preview     = COHORT_BOUNDS[PREVIEW_COHORT]
print(f"Rx data through {DATA_MAX_DT} -> {len(COHORT_LIST)} complete cohorts: "
      f"{COHORT_LIST[0]} .. {COHORT_LIST[-1]} | preview cohort: {PREVIEW_COHORT}")

# ---------- Feature rows for this run ----------
# Counted claims start at DATA_START_DATE (team rule, RUNNING_ included). The claims are filtered BEFORE the
# patient-month step, so a cohort month that straddles the start date only counts claims from the start date.
# The fixed column list is taken from the full history.
_t0 = time.time()
_rx_counted = df_rx.filter(F.col(SVC_COL) >= F.lit(DATA_START_DATE))
df_feat = materialize(build_feature_rows(eligible_patient_months(_rx_counted, pat_elig, OFFSET_DAYS)), "main")
df_dial = materialize(build_dialysis_claims(_rx_counted, pat_px), "dialysis")
FEATURE_VALUES = feature_values_of(build_feature_rows(eligible_patient_months(df_rx, pat_elig, OFFSET_DAYS)))

print(f"Feature rows: {df_feat.count():,} (NPI x day x feature) | dialysis rows: {df_dial.count():,} (NPI x day) "
      f"| {time.time() - _t0:,.0f}s")
print(f"Feature columns per window: {len(FEATURE_VALUES)} -> {FEATURE_VALUES}")

# COMMAND ----------

# DBTITLE 1,Display: feature rows
display(df_feat.groupBy("FEATURE").agg(F.sum("N").alias("patient_months"), F.countDistinct(NPI_COL).alias("npis"))
        .orderBy("FEATURE"))
display(df_dial.groupBy(NPI_COL).agg(F.count("*").alias("claim_days"), F.sum("DIALYSIS_FLAG").alias("days_with_dialysis_patient"))
        .orderBy(NPI_COL))

# COMMAND ----------

# DBTITLE 1,Build one cohort (functions + preview)
# ---- One cohort: windows + RUNNING_ in a single pivot, then PCT_, DIALYSIS_FLAG and metadata ----
def build_cohort(cb, df_feat_in=None, df_dial_in=None, feature_values=None):
    """All features for one cohort, one row per NPI with any eligible patient-month up to the cutoff.
    df_feat_in / df_dial_in / feature_values: feature rows, dialysis rows and column list (default: this run's)."""
    L    = df_feat if df_feat_in is None else df_feat_in
    Dl   = df_dial if df_dial_in is None else df_dial_in
    vals = FEATURE_VALUES if feature_values is None else feature_values
    wins = ELIG_LOOKBACK_WINDOWS
    cutoff = F.to_date(F.lit(cb["cutoff"].strftime("%Y-%m-%d")))

    # Each row goes to RUNNING_ and to every window whose (start, cutoff] contains its date
    _suffixes = F.array(F.lit("RUNNING"), *[
        F.when(F.col(SVC_COL) > F.to_date(F.lit(cb["window_bounds"][w]["start"])), F.lit(f"_IN_LAST_{w}_MONTH"))
        for w in wins])
    long = (L.filter(F.col(SVC_COL) <= cutoff)
            .select(NPI_COL, "FEATURE", "N", F.explode(_suffixes).alias("_S"))
            .filter(F.col("_S").isNotNull())
            .withColumn("_COL", F.when(F.col("_S") == "RUNNING", F.concat(F.lit("RUNNING_"), F.col("FEATURE")))
                                 .otherwise(F.concat(F.col("FEATURE"), F.col("_S"))))
            .groupBy(NPI_COL, "_COL").agg(F.sum("N").alias("N")))

    window_cols  = [f"{v}_IN_LAST_{w}_MONTH" for w in wins for v in vals]
    running_cols = [f"RUNNING_{v}" for v in vals]
    wide = (long.groupBy(NPI_COL).pivot("_COL", window_cols + running_cols)
            .agg(F.first("N")).na.fill(0))

    # PCT_: feature / TOTAL_ELIGIBLE_PATIENTS in the same window (0.0 when the total is 0); none for RUNNING_
    pct = []
    for w in wins:
        den = F.col(f"{TOTAL_COL}_IN_LAST_{w}_MONTH")
        pct += [F.when(den != 0, F.col(f"{v}_IN_LAST_{w}_MONTH") / den).otherwise(F.lit(0.0))
                 .alias(f"PCT_{v}_IN_LAST_{w}_MONTH") for v in vals if v != TOTAL_COL]

    # DIALYSIS_FLAG (D2): the Rx claims of the cohort month itself (= the 1-month window), as the original monthly flag
    _start1 = F.to_date(F.lit(cb["window_bounds"][1]["start"]))
    dial = (Dl.filter((F.col(SVC_COL) > _start1) & (F.col(SVC_COL) <= cutoff))
            .groupBy(NPI_COL).agg(F.max("DIALYSIS_FLAG").alias("DIALYSIS_FLAG")))

    return (wide.select("*", *pct)
            .join(dial, on=NPI_COL, how="left")
            .withColumn("DIALYSIS_FLAG", F.coalesce(F.col("DIALYSIS_FLAG"), F.lit(0)).cast("int"))
            .withColumn("COHORT_ID", F.lit(cb["cohort_id"]))
            .withColumn("COHORT_MONTH", F.lit(cb["cohort_month"]))
            .withColumn("OFFSET_DAYS", F.lit(cb["offset_days"]))
            .withColumn("CUTOFF_DATE", F.lit(cb["cutoff"].strftime("%Y-%m-%d")))
            .withColumn("SVC_DT_M", F.to_timestamp(F.lit(f"{cb['cohort_month']}-01")))
            .withColumn("PULL_DT", F.current_date()))


# ---- Preview on one cohort ----
_t0 = time.time()
elig_preview = build_cohort(cb_preview)
_pv_cols = elig_preview.columns
print(f"Preview {cb_preview['cohort_id']} (cutoff {cb_preview['cutoff']:%Y-%m-%d}) | "
      f"NPIs: {elig_preview.count():,} | columns: {len(_pv_cols):,} "
      f"(windows: {builtins.sum('_IN_LAST_' in c and not c.startswith('PCT_') for c in _pv_cols)}, "
      f"RUNNING_: {builtins.sum(c.startswith('RUNNING_') for c in _pv_cols)}, "
      f"PCT_: {builtins.sum(c.startswith('PCT_') for c in _pv_cols)}) | {time.time() - _t0:,.0f}s")

# COMMAND ----------

# DBTITLE 1,Display: preview cohort
_tot_cols = [f"{TOTAL_COL}_IN_LAST_{w}_MONTH" for w in ELIG_LOOKBACK_WINDOWS] + [f"RUNNING_{TOTAL_COL}"]
display(elig_preview.select(NPI_COL, "COHORT_ID", "CUTOFF_DATE", *_tot_cols,
                            *[c for c in _pv_cols if c.endswith("_IN_LAST_12_MONTH") and c.startswith(_PFX_GFR)],
                            "DIALYSIS_FLAG").orderBy(NPI_COL))

# COMMAND ----------

# DBTITLE 1,Fast cohort engine (all cohorts in one query)
# ---- Fast engine (pattern A, as NB04/NB05): all cohorts in ONE query ----
# Same columns, order, types and values as build_cohort (checked in the next cell):
# 1) feature rows -> (NPI, cohort month, FEATURE, N) and dialysis rows -> (NPI, cohort month, flag), once each
# 2) one pivot by NPI x cohort through the window tags of 00_cohort_config, then PCT_, DIALYSIS_FLAG, metadata.
OUTPUT_COLS = build_cohort(cb_preview).columns   # schema only, nothing is computed
_MONTHS = {}

def get_feat_months(df_feat_in, offset_days, name):
    if name not in _MONTHS:
        _MONTHS[name] = materialize(feature_rows_to_months(df_feat_in, NPI_COL, offset_days), f"months_{name}")
    return _MONTHS[name]

def get_dial_months(df_dial_in, offset_days, name):
    key = f"dial_{name}"
    if key not in _MONTHS:
        _MONTHS[key] = materialize(
            df_dial_in.withColumn("_CM", assign_cohort_month(F.col(SVC_COL), offset_days))
                      .groupBy(NPI_COL, "_CM").agg(F.max("DIALYSIS_FLAG").alias("DIALYSIS_FLAG")),
            f"months_{key}")
    return _MONTHS[key]

def build_all_cohorts_fast(cbs, df_feat_in=None, df_dial_in=None, feature_values=None, name="run"):
    """build_cohort for every cohort in cbs, in one query (one row per NPI x COHORT_ID).
    df_feat_in / df_dial_in / feature_values / name: other input rows (e.g. the offset-0 parity rows)."""
    L    = df_feat if df_feat_in is None else df_feat_in
    Dl   = df_dial if df_dial_in is None else df_dial_in
    vals = FEATURE_VALUES if feature_values is None else feature_values
    wins = ELIG_LOOKBACK_WINDOWS
    off  = cbs[0]["offset_days"]
    wide = build_all_cohorts_from_months(get_feat_months(L, off, f"{name}_offset{off}"), cbs, NPI_COL, vals, wins)
    pct = []
    for w in wins:
        den = F.col(f"{TOTAL_COL}_IN_LAST_{w}_MONTH")
        pct += [F.when(den != 0, F.col(f"{v}_IN_LAST_{w}_MONTH") / den).otherwise(F.lit(0.0))
                 .alias(f"PCT_{v}_IN_LAST_{w}_MONTH") for v in vals if v != TOTAL_COL]
    out = (add_cohort_meta(wide.select("*", *pct), cbs)
           .withColumn("_CM", F.to_date(F.concat(F.col("COHORT_MONTH"), F.lit("-01"))))
           .join(get_dial_months(Dl, off, f"{name}_offset{off}"), on=[NPI_COL, "_CM"], how="left")
           .withColumn("DIALYSIS_FLAG", F.coalesce(F.col("DIALYSIS_FLAG"), F.lit(0)).cast("int"))
           .drop("_CM"))
    cols = OUTPUT_COLS if vals is FEATURE_VALUES else build_cohort(cbs[0], L, Dl, vals).columns
    return out.select(*cols)

print(f"Fast engine ready: {len(OUTPUT_COLS):,} output columns per cohort, {len(COHORT_LIST)} cohorts in one query")

# COMMAND ----------

# DBTITLE 1,Check: fast engine = build_cohort (2 cohorts)
# ---- Check: the all-cohorts query gives exactly what build_cohort gives (first and last cohort) ----
# Nothing is written.
_check = [COHORT_LIST[0], COHORT_LIST[-1]]
_t0 = time.time()
_pd_fast = build_all_cohorts_fast([COHORT_BOUNDS[m] for m in _check]).toPandas()
print(f"All-cohorts query ({len(_check)} cohorts): {time.time() - _t0:,.0f}s")

_rows = []
for m in _check:
    cb = COHORT_BOUNDS[m]
    _t0 = time.time()
    _one   = build_cohort(cb)
    pd_one = _one.toPandas().set_index(NPI_COL)
    _t_one = time.time() - _t0
    pd_all = _pd_fast[_pd_fast["COHORT_ID"] == cb["cohort_id"]].set_index(NPI_COL)

    same_order = list(pd_one.columns) == list(pd_all.columns)
    same_types = _one.dtypes == build_all_cohorts_fast([cb]).dtypes
    cols = [c for c in pd_one.columns if c in pd_all.columns and c != "PULL_DT"]
    num  = [c for c in cols if pd.api.types.is_numeric_dtype(pd_one[c])]
    txt  = [c for c in cols if c not in num]
    common = sorted(set(pd_one.index) & set(pd_all.index))
    bad = ~np.isclose(pd_one.loc[common, num].astype(float).values, pd_all.loc[common, num].astype(float).values,
                      rtol=1e-9, atol=1e-9, equal_nan=True)
    bad_txt = int((pd_one.loc[common, txt].astype(str).values != pd_all.loc[common, txt].astype(str).values).sum())
    _rows.append({"cohort": cb["cohort_id"], "npis_per_cohort": len(pd_one), "npis_fast": len(pd_all),
                  "npis_common": len(common), "same_column_order": same_order, "same_types": same_types,
                  "cells_compared": int(bad.size) + len(common) * len(txt),
                  "mismatching_cells": int(bad.sum()) + bad_txt, "per_cohort_seconds": builtins.round(_t_one)})

df_fast_check = pd.DataFrame(_rows)
display(df_fast_check)
_ok = (df_fast_check["mismatching_cells"].sum() == 0 and df_fast_check["same_column_order"].all()
       and df_fast_check["same_types"].all()
       and (df_fast_check["npis_per_cohort"] == df_fast_check["npis_common"]).all()
       and (df_fast_check["npis_fast"] == df_fast_check["npis_common"]).all())
print("PASS: fast engine = build_cohort" if _ok else "CHECK: fast engine differs from build_cohort")

# COMMAND ----------

# DBTITLE 1,4b. Diabetes type and HF type features (DM_TYPE, HF_TYPE)
# 4b. Diabetes type and HF type features (2026-11-06). Built from the PJ04 table kerendia_nba_3_1_dm_hf_flags_validation
# (one row per patient: DM_TYPE, HF_TYPE, HF_FIRST_DATE). Same patient-months as the features above: (NPI, patient,
# cohort month) of the HCP's Rx claims from DATA_START_DATE; windows ELIG_LOOKBACK_WINDOWS (1, 3, 6, 12 months).
#   TOTAL_RX_PATIENTS_IN_LAST_<w>_MONTH                    all patient-months (denominator of the PCT_RX_ columns)
#   TOTAL_RX_PATIENTS_DM_TYPE_<T2D|T1D|OTHER|NONE>_...      by diabetes type (NONE = no diabetes type in PJ04)
#   TOTAL_RX_PATIENTS_HF_... / _HF_TYPE_<HFPEF_PROXY|HFREF_PROXY|MIXED|UNKNOWN>_...   patient-months with HF that month
#       (month on or after the month of HF_FIRST_DATE, same rule as the monthly HF_FLAG of PJ06), by HF type
#   TOTAL_ELIGIBLE_PATIENTS_DM_TYPE_..., _HF, _HF_TYPE_...  same, eligible patient-months only (ELIGIBLE_PATIENT_FLAG = 1)
#   PCT_RX_PATIENTS_... = / TOTAL_RX_PATIENTS, PCT_ELIGIBLE_PATIENTS_... = / TOTAL_ELIGIBLE_PATIENTS (same window, 0.0 if 0)
# HFPEF_PROXY / HFREF_PROXY: claims cannot see the ejection fraction, so the PJ04 HF type is a proxy from the HF codes;
# HFpEF (LVEF >= 40%) is the HF indication of Kerendia. Added to the existing rows only (left join, same rows).
from dateutil.relativedelta import relativedelta as _rd

DM_TYPE_VALUES = ["T2D", "T1D", "OTHER", "NONE"]
HF_TYPE_VALUES = ["HFPEF_PROXY", "HFREF_PROXY", "MIXED", "UNKNOWN"]
# The table is written by PJ04 of the same run (RUN_OUTPUT_DIR). Full run: must exist. Validation run on an older
# folder without it (e.g. validation_2026_10_30): the DM / HF columns are skipped, the rest of NB06 runs as before.
import os
_DMHF_IN_RUN = bool(RUN_OUTPUT_DIR) and os.path.exists(RUN_OUTPUT_DIR + get_patient_table("dm_hf_flags") + "/_delta_log")
DM_HF_FEATURES_ON = _DMHF_IN_RUN or not VALIDATION_MODE
if not DM_HF_FEATURES_ON:
    print(f"SKIPPED DM / HF features: {get_patient_table('dm_hf_flags')} not in {RUN_OUTPUT_DIR} (validation run)")
_DMHF_PATH = get_patient_table_path("dm_hf_flags") if DM_HF_FEATURES_ON else None
pat_dmhf = None if not DM_HF_FEATURES_ON else (spark.read.format("delta").load(_DMHF_PATH)
            .select(F.col("PATIENT_ID").cast("string").alias("PATIENT_ID"), "DM_TYPE", "HF_TYPE",
                    F.trunc(F.to_date("HF_FIRST_DATE"), "month").alias("_HF_M")))
_bad_dm = [] if not DM_HF_FEATURES_ON else sorted({r[0] for r in pat_dmhf.select("DM_TYPE").distinct().collect()} - set(DM_TYPE_VALUES) - {None})
_bad_hf = [] if not DM_HF_FEATURES_ON else sorted({r[0] for r in pat_dmhf.select("HF_TYPE").distinct().collect()} - set(HF_TYPE_VALUES) - {None})
assert not _bad_dm and not _bad_hf, f"New DM_TYPE {_bad_dm} / HF_TYPE {_bad_hf} values in {_DMHF_PATH}: add them to the lists"


def dm_hf_feature_names(windows=ELIG_LOOKBACK_WINDOWS):
    cols = []
    for w in windows:
        sfx = f"_IN_LAST_{w}_MONTH"
        groups = ([f"DM_TYPE_{v}" for v in DM_TYPE_VALUES] + ["HF"] + [f"HF_TYPE_{v}" for v in HF_TYPE_VALUES])
        cols += [f"TOTAL_RX_PATIENTS{sfx}"] + [f"TOTAL_RX_PATIENTS_{g}{sfx}" for g in groups]
        cols += [f"TOTAL_ELIGIBLE_PATIENTS_{g}{sfx}" for g in groups]
        cols += [f"PCT_RX_PATIENTS_{g}{sfx}" for g in groups] + [f"PCT_ELIGIBLE_PATIENTS_{g}{sfx}" for g in groups]
    return cols


def dm_hf_month_counts(df_rx_in, pat_elig_df, dmhf_df, offset_days):
    """(NPI, _M, KEY, N): patient-months per key. _ELIG_TOTAL = TOTAL_ELIGIBLE_PATIENTS (internal, used as the
    PCT_ELIGIBLE_ denominator and to check against the existing column)."""
    pm = (df_rx_in.withColumn("_M", assign_cohort_month(F.col(SVC_COL), offset_days))
          .select(NPI_COL, F.col("PATIENT_ID").cast("string").alias("PATIENT_ID"), "_M").distinct())
    e = (pat_elig_df.filter(F.col("ELIGIBLE_PATIENT_FLAG") == 1)
         .select(F.col("PATIENT_ID").cast("string").alias("PATIENT_ID"), F.to_date("SVC_DT_M").alias("_M"))
         .distinct().withColumn("_ELIG", F.lit(1)))
    pm = (pm.join(e, on=["PATIENT_ID", "_M"], how="left").fillna(0, subset=["_ELIG"])
            .join(dmhf_df, on="PATIENT_ID", how="left")
            .withColumn("_DM", F.coalesce(F.col("DM_TYPE"), F.lit("NONE")))
            .withColumn("_HF", F.col("_HF_M").isNotNull() & (F.col("_HF_M") <= F.col("_M")))
            .withColumn("_HFT", F.coalesce(F.col("HF_TYPE"), F.lit("UNKNOWN"))))
    el, hf = F.col("_ELIG") == 1, F.col("_HF")
    keys = F.array(
        F.lit("TOTAL_RX_PATIENTS"),
        F.concat(F.lit("TOTAL_RX_PATIENTS_DM_TYPE_"), F.col("_DM")),
        F.when(hf, F.lit("TOTAL_RX_PATIENTS_HF")),
        F.when(hf, F.concat(F.lit("TOTAL_RX_PATIENTS_HF_TYPE_"), F.col("_HFT"))),
        F.when(el, F.lit("_ELIG_TOTAL")),
        F.when(el, F.concat(F.lit("TOTAL_ELIGIBLE_PATIENTS_DM_TYPE_"), F.col("_DM"))),
        F.when(el & hf, F.lit("TOTAL_ELIGIBLE_PATIENTS_HF")),
        F.when(el & hf, F.concat(F.lit("TOTAL_ELIGIBLE_PATIENTS_HF_TYPE_"), F.col("_HFT"))))
    return (pm.select(NPI_COL, "_M", F.explode(keys).alias("KEY")).filter(F.col("KEY").isNotNull())
            .groupBy(NPI_COL, "_M", "KEY").agg(F.count(F.lit(1)).alias("N")))


def build_dm_hf_features(cbs, counts_in):
    """One row per (NPI, COHORT_ID) with every DM / HF column (+ _ELIG_TOTAL_IN_LAST_<w>_MONTH for the check).
    Window w = the w cohort months ending with the cohort month (= (cutoff - w months, cutoff])."""
    _rows = []
    for cb in cbs:
        _cm = datetime.strptime(cb["cohort_month"] + "-01", "%Y-%m-%d").date()
        _rows += [(cb["cohort_id"], w, _cm - _rd(months=w - 1), _cm) for w in ELIG_LOOKBACK_WINDOWS]
    W = spark.createDataFrame(_rows, "COHORT_ID string, W int, M_FROM date, M_TO date")
    long = (counts_in.join(F.broadcast(W), (F.col("_M") >= F.col("M_FROM")) & (F.col("_M") <= F.col("M_TO")))
            .groupBy(NPI_COL, "COHORT_ID", F.concat(F.col("KEY"), F.lit("_IN_LAST_"), F.col("W"), F.lit("_MONTH")).alias("_COL"))
            .agg(F.sum("N").alias("N")))
    _tot = [c for c in dm_hf_feature_names() if not c.startswith("PCT_")]
    _etot = [f"_ELIG_TOTAL_IN_LAST_{w}_MONTH" for w in ELIG_LOOKBACK_WINDOWS]
    wide = long.groupBy(NPI_COL, "COHORT_ID").pivot("_COL", _tot + _etot).agg(F.first("N")).na.fill(0, subset=_tot + _etot)
    pct = []
    for w in ELIG_LOOKBACK_WINDOWS:
        sfx = f"_IN_LAST_{w}_MONTH"
        for grp, den in [("RX_PATIENTS", f"TOTAL_RX_PATIENTS{sfx}"), ("ELIGIBLE_PATIENTS", f"_ELIG_TOTAL{sfx}")]:
            for c in [x for x in _tot if x.startswith(f"TOTAL_{grp}_") and x.endswith(sfx)]:
                pct.append(F.when(F.col(den) != 0, F.col(c) / F.col(den)).otherwise(F.lit(0.0)).alias("PCT_" + c[len("TOTAL_"):]))
    return wide.select(NPI_COL, "COHORT_ID", *_tot, *_etot, *pct).select(NPI_COL, "COHORT_ID", *dm_hf_feature_names(), *_etot)


def add_dm_hf_features(df_out, cbs):
    """Left join of the DM / HF columns onto the existing output (same rows). Stops if the internal eligible total
    differs from TOTAL_ELIGIBLE_PATIENTS (both must count the same eligible patient-months)."""
    if not DM_HF_FEATURES_ON:
        return df_out
    feats = build_dm_hf_features(cbs, dm_hf_month_counts(_rx_counted, pat_elig, pat_dmhf, OFFSET_DAYS))
    _new = dm_hf_feature_names()
    out = (df_out.join(feats, on=[NPI_COL, "COHORT_ID"], how="left")
           .na.fill(0, subset=[c for c in _new if not c.startswith("PCT_")] + [f"_ELIG_TOTAL_IN_LAST_{w}_MONTH" for w in ELIG_LOOKBACK_WINDOWS])
           .na.fill(0.0, subset=[c for c in _new if c.startswith("PCT_")]))
    _diff = out.filter(F.greatest(*[F.abs(F.col(f"_ELIG_TOTAL_IN_LAST_{w}_MONTH") - F.col(f"{TOTAL_COL}_IN_LAST_{w}_MONTH"))
                                    for w in ELIG_LOOKBACK_WINDOWS]) > 0).count()
    assert _diff == 0, f"{_diff:,} NPI x cohort rows: eligible patient-months of the DM / HF features differ from {TOTAL_COL}"
    return out.drop(*[f"_ELIG_TOTAL_IN_LAST_{w}_MONTH" for w in ELIG_LOOKBACK_WINDOWS])


print(f"DM / HF features: {len(dm_hf_feature_names())} columns ({len(ELIG_LOOKBACK_WINDOWS)} windows) | table: {_DMHF_PATH}")

# COMMAND ----------

# DBTITLE 1,Section: Build and Write All Cohorts
# MAGIC %md
# MAGIC ## 5. Build and write all cohorts
# MAGIC
# MAGIC One write of all cohorts: Delta, `partitionBy("COHORT_ID")`, `replaceWhere` on this run's `COHORT_ID`s, `mergeSchema` (other offsets / cohorts in the table are kept). Then completeness checks and the provider-level table (NPI mapped to `PROVIDER_ID`, NPI dropped, as the original).

# COMMAND ----------

# DBTITLE 1,Build and write all cohorts (one write)
OUTPUT_PATH = _NOTEBOOK_OUTPUT + "claim_eligible_patient_cohort"
assert "kerendia_nba_3_0" not in OUTPUT_PATH, f"Refusing to write to a 3.0 table: {OUTPUT_PATH}"

# All cohorts in one query and ONE write. replaceWhere keeps every other cohort / offset already in the table.
_ids_sql = ", ".join(f"'{c}'" for c in COHORT_IDS)
_t_all = time.time()
# 2026-11-06: diabetes type and HF type features (4b) joined onto the same rows (row count unchanged)
add_dm_hf_features(build_all_cohorts_fast([COHORT_BOUNDS[m] for m in COHORT_LIST]),
                   [COHORT_BOUNDS[m] for m in COHORT_LIST]).write \
    .format("delta") \
    .mode("overwrite") \
    .option("mergeSchema", "true") \
    .option("replaceWhere", f"COHORT_ID IN ({_ids_sql})") \
    .partitionBy("COHORT_ID") \
    .save(OUTPUT_PATH)

print(f"{len(COHORT_LIST)} cohorts ({COHORT_IDS[0]} .. {COHORT_IDS[-1]}) written to {OUTPUT_PATH} "
      f"in one write, {(time.time() - _t_all) / 60:,.1f} min")

# COMMAND ----------

# DBTITLE 1,All cohorts per NPI (completeness checks)
# Read the written table directly (independent of the preview variables)
df_all_cohorts = spark.read.format("delta").load(OUTPUT_PATH)

_ids_in_table  = sorted(r[0] for r in df_all_cohorts.select("COHORT_ID").distinct().collect())
_missing       = sorted(set(COHORT_IDS) - set(_ids_in_table))
_extra         = sorted(set(_ids_in_table) - set(COHORT_IDS))
df_all_cohorts = df_all_cohorts.filter(F.col("COHORT_ID").isin(COHORT_IDS))
_n_rows = df_all_cohorts.count()
_n_keys = df_all_cohorts.select(NPI_COL, "COHORT_ID").distinct().count()
_n_npis = df_all_cohorts.select(NPI_COL).distinct().count()
_nulls  = df_all_cohorts.select([F.sum(F.col(c).isNull().cast("int")).alias(c) for c in df_all_cohorts.columns]).first()
_null_cells = builtins.sum(v or 0 for v in _nulls)

print(f"Cohorts expected: {len(COHORT_IDS)} | in table: {len(_ids_in_table)} | "
      f"missing: {_missing or 'none'} | extra (not in this run): {_extra or 'none'}")
print(f"Rows: {_n_rows:,} | distinct (NPI, COHORT_ID): {_n_keys:,} | duplicates: {_n_rows - _n_keys} | "
      f"NPIs: {_n_npis} | Columns: {len(df_all_cohorts.columns):,} | null cells: {_null_cells:,}")
display(df_all_cohorts.groupBy("COHORT_ID", "CUTOFF_DATE").agg(F.count("*").alias("npis"),
        F.sum(f"{TOTAL_COL}_IN_LAST_1_MONTH").alias("eligible_patients_1m"),
        F.sum("DIALYSIS_FLAG").alias("npis_with_dialysis_flag")).orderBy("COHORT_ID"))

_key_cols = [NPI_COL, "COHORT_ID", "COHORT_MONTH", "OFFSET_DAYS", "CUTOFF_DATE", "SVC_DT_M", "PULL_DT"]
display(df_all_cohorts.select(*_key_cols, *_tot_cols, "DIALYSIS_FLAG").orderBy(NPI_COL, "COHORT_ID"))

# COMMAND ----------

# DBTITLE 1,Provider ID mapping and provider-level output
# Shared NPI -> PROVIDER_ID mapping (the original queried STG_CAR_IQV_LAAD_DIM_PRVDR in Snowflake). NPI dropped, as the original.
hcp_npi_mapping_df = (spark.read.format("delta").load(_QUERY_OUTPUT + HCP_NPI_MAPPING_TABLE)
                      .select("NPI_NUMBER", "PROVIDER_ID").distinct())

PROVIDER_OUTPUT_PATH = _NOTEBOOK_OUTPUT + "provider_claim_eligible_patient_cohort"
assert "kerendia_nba_3_0" not in PROVIDER_OUTPUT_PATH, f"Refusing to write to a 3.0 table: {PROVIDER_OUTPUT_PATH}"
(spark.read.format("delta").load(OUTPUT_PATH)
    .filter(F.col("COHORT_ID").isin(COHORT_IDS))
    .join(hcp_npi_mapping_df, on="NPI_NUMBER", how="left")
    .drop("NPI_NUMBER")
    .write.format("delta")
    .mode("overwrite")
    .option("mergeSchema", "true")
    .option("replaceWhere", "COHORT_ID IN (" + ", ".join(f"'{c}'" for c in COHORT_IDS) + ")")
    .partitionBy("COHORT_ID")
    .save(PROVIDER_OUTPUT_PATH))

_prov = spark.read.format("delta").load(PROVIDER_OUTPUT_PATH).filter(F.col("COHORT_ID").isin(COHORT_IDS))
print(f"Written to {PROVIDER_OUTPUT_PATH} ({len(COHORT_IDS)} cohorts) | rows: {_prov.count():,} | "
      f"null PROVIDER_ID: {_prov.filter(F.col('PROVIDER_ID').isNull()).count():,} | "
      f"duplicate (PROVIDER_ID, COHORT_ID): {_prov.count() - _prov.select('PROVIDER_ID', 'COHORT_ID').distinct().count():,}")
display(_prov.select("PROVIDER_ID", "COHORT_ID", "CUTOFF_DATE", *_tot_cols, "DIALYSIS_FLAG").orderBy("PROVIDER_ID", "COHORT_ID"))

# COMMAND ----------

# DBTITLE 1,Section: Validation
# MAGIC %md
# MAGIC ## 6. Validation
# MAGIC
# MAGIC 1. **Offset = 0 comparison with the original (every cohort):** rebuild the features at offset 0 for the test HCPs with the same inputs as the original (reference snapshot: `Rx_01_new`, the 3.0 eligibility table, the 3.0 dialysis table, full history), map NPI to `PROVIDER_ID` and compare every column with `kerendia_nba_3_0_claim_eligible_patient` for each month. Original base-month columns are compared with our `_IN_LAST_1_MONTH` columns; original nulls count as 0. Provider-months only in the original must have 0 in every count column (the original fills every month from 2022-01; their `DIALYSIS_FLAG` is reported, not failed).
# MAGIC 2. **HCP trace:** for the busiest test HCP, rebuild every count and the dialysis flag in pandas from the raw tables (filter claims by date, then distinct patient-months) and compare with the written table, for every cohort.

# COMMAND ----------

# DBTITLE 1,Offset-0 parity vs original eligible patient output
# ---- Validation 1: offset = 0 parity vs original kerendia_nba_3_0_claim_eligible_patient, every cohort ----
_npis = get_test_npis()
# 3.0 output, 3.0 patient tables, Rx_01_new and the NPI mapping all come from the reference snapshot
# (HCP_REF_VOLUME, 00_cohort_config): the refreshed inputs restate history. Skip (not fail) if the snapshot is gone.
_ref_missing = hcp_ref_missing([HCP_REF_NOTEBOOK_OUTPUT + "kerendia_nba_3_0_claim_eligible_patient",
                                get_patient_table_path("sglt2_filter_m", ref=True),
                                get_patient_table_path("px", ref=True),
                                HCP_REF_QUERY_OUTPUT + "Rx_01_new",
                                HCP_REF_QUERY_OUTPUT + HCP_NPI_MAPPING_TABLE])
if _npis is None:
    print("Production mode: parity check skipped (runs on the test NPIs only)")
elif _ref_missing:
    print("SKIPPED — 3.0 reference table(s) missing, rerun when restored:\n  " + "\n  ".join(_ref_missing))
else:
    _t_par = time.time()
    _rx_ref_raw = load_ref_input("Rx_01_new")
    _REF_MAX_DT = _rx_ref_raw.agg(F.max(SVC_COL)).first()[0]
    _rx_ref = (apply_npi_filter(_rx_ref_raw, NPI_COL)
               .select(NPI_COL, F.col("PATIENT_ID").cast("string").alias("PATIENT_ID"), SVC_COL))
    _pid_df = spark.createDataFrame(pd.DataFrame(
        {"PATIENT_ID": [r[0] for r in _rx_ref.select("PATIENT_ID").distinct().collect()]}))
    def _patients_only(path):
        return spark.read.format("delta").load(path).join(F.broadcast(_pid_df), on="PATIENT_ID", how="left_semi")
    _elig30 = _patients_only(get_patient_table_path("sglt2_filter_m", ref=True)).select(
        "PATIENT_ID", "SVC_DT_M", "ELIGIBLE_PATIENT_FLAG", "GFR_DX_STAGE", "UACR_STAGE")
    _px30 = _patients_only(get_patient_table_path("px", ref=True)).select("PATIENT_ID", "FIRST_DIALYSIS_DATE")
    # Full history, as the original (its RUNNING_ columns start at the first month of the data)
    df_feat0 = materialize(build_feature_rows(eligible_patient_months(_rx_ref, _elig30, 0)), "offset0")
    df_dial0 = materialize(build_dialysis_claims(_rx_ref, _px30), "dialysis_offset0")
    FEATURE_VALUES0 = feature_values_of(df_feat0)
    print(f"Offset-0 feature rows: {df_feat0.count():,} | feature columns: {len(FEATURE_VALUES0)} "
          f"| {time.time() - _t_par:,.0f}s")

    _map_pd = (load_ref_input(HCP_NPI_MAPPING_TABLE).select(NPI_COL, "PROVIDER_ID").distinct()
               .filter(F.col(NPI_COL).isin(_npis)).toPandas())
    _npi_to_prov = dict(zip(_map_pd[NPI_COL], _map_pd["PROVIDER_ID"]))
    _orig_all = (spark.read.format("delta").load(HCP_REF_NOTEBOOK_OUTPUT + "kerendia_nba_3_0_claim_eligible_patient")
                 .filter(F.col("PROVIDER_ID").isin(list(_npi_to_prov.values())))
                 .withColumn("_M", F.date_format("SVC_DT_M", "yyyy-MM")))
    _orig_months  = {r[0] for r in _orig_all.select("_M").distinct().collect()}
    PARITY_MONTHS = [m for m in get_cohort_months(max_data_date=_REF_MAX_DT, offset_days=0) if m in _orig_months]
    pd_orig_all = _orig_all.filter(F.col("_M").isin(PARITY_MONTHS)).toPandas()
    print(f"Original rows for the test providers: {len(pd_orig_all):,} | months compared: {len(PARITY_MONTHS)}")

    _skip = {"SVC_DT_M", "PULL_DT", "_M", "PROVIDER_ID"}
    _orig_cols = [c for c in pd_orig_all.columns if c not in _skip]
    # Original column -> cohort-based column (base-month columns map to _IN_LAST_1_MONTH; DIALYSIS_FLAG as is)
    _map = {oc: (oc if ("_IN_LAST_" in oc or oc.startswith("RUNNING_") or oc == "DIALYSIS_FLAG")
                 else f"{oc}_IN_LAST_1_MONTH") for oc in _orig_cols}
    _count_orig_cols = [oc for oc in _orig_cols if oc != "DIALYSIS_FLAG"]
    _meta = {"COHORT_ID", "COHORT_MONTH", "OFFSET_DAYS", "CUTOFF_DATE", "SVC_DT_M", "PULL_DT", NPI_COL, "PROVIDER_ID"}

    def _num(df):
        return df.apply(pd.to_numeric, errors="coerce").fillna(0).astype(float)

    # All parity months in ONE query (same engine as the written output), compared month by month
    _cbs0 = {m: get_cohort_bounds(m, offset_days=0) for m in PARITY_MONTHS}
    pd_new_all = build_all_cohorts_fast(list(_cbs0.values()), df_feat0, df_dial0, FEATURE_VALUES0, name="parity").toPandas()

    summary, mismatches = [], []
    for m in PARITY_MONTHS:
        cb0 = _cbs0[m]
        pd_new = pd_new_all[pd_new_all["COHORT_ID"] == cb0["cohort_id"]].copy()
        pd_new["PROVIDER_ID"] = pd_new[NPI_COL].map(_npi_to_prov)
        pd_new  = pd_new.set_index("PROVIDER_ID")
        pd_orig = pd_orig_all[pd_orig_all["_M"] == m].set_index("PROVIDER_ID")

        common    = sorted(set(pd_new.index) & set(pd_orig.index))
        only_orig = sorted(set(pd_orig.index) - set(pd_new.index))
        only_new  = sorted(set(pd_new.index) - set(pd_orig.index))
        present   = [oc for oc in _orig_cols if _map[oc] in pd_new.columns]
        absent    = [oc for oc in _orig_cols if _map[oc] not in pd_new.columns]
        extra_new = [c for c in pd_new.columns if c not in _meta and c not in set(_map.values())]

        o = _num(pd_orig.loc[common, present])
        n = _num(pd_new.loc[common, [_map[oc] for oc in present]])
        bad = ~np.isclose(o.values, n.values, rtol=1e-9, atol=1e-9)
        for i, j in list(zip(*np.where(bad)))[:50]:
            mismatches.append({"cohort": cb0["cohort_id"], "PROVIDER_ID": common[i], "original_col": present[j],
                               "new_col": _map[present[j]], "original": o.values[i, j], "new": n.values[i, j]})
        absent_nonzero = int((_num(pd_orig.loc[common, absent]) != 0).values.sum()) if absent else 0
        # Provider-months only in the original (no eligible patient yet): every count must be 0
        only_orig_nonzero = (int((_num(pd_orig.loc[only_orig, _count_orig_cols]) != 0).any(axis=1).sum())
                             if only_orig else 0)
        only_orig_dialysis = int(_num(pd_orig.loc[only_orig, ["DIALYSIS_FLAG"]]).values.sum()) if only_orig else 0

        summary.append({"cohort_offset0": cb0["cohort_id"], "cutoff": f"{cb0['cutoff']:%Y-%m-%d}",
                        "providers_common": len(common), "providers_only_original": len(only_orig),
                        "only_original_nonzero": only_orig_nonzero, "only_original_dialysis_1": only_orig_dialysis,
                        "providers_only_new": len(only_new), "columns_compared": len(present),
                        "original_cols_not_built": len(absent), "not_built_nonzero_cells": absent_nonzero,
                        "new_cols_not_in_original": len(extra_new), "mismatching_cells": int(bad.sum())})

    df_parity = pd.DataFrame(summary)
    display(df_parity)
    _ok = (df_parity[["mismatching_cells", "only_original_nonzero", "providers_only_new",
                      "not_built_nonzero_cells", "new_cols_not_in_original"]].values.sum() == 0)
    print(f"Cohorts compared: {len(df_parity)} | mismatching cells: {df_parity['mismatching_cells'].sum()} | "
          f"{'PASS' if _ok else 'CHECK MISMATCHES'} | total {(time.time() - _t_par) / 60:,.1f} min")
    if mismatches:
        display(pd.DataFrame(mismatches))

# COMMAND ----------

# DBTITLE 1,HCP trace across all cohorts
# ---- Validation 2: HCP trace. Every count and the dialysis flag rebuilt in pandas from the raw tables ----
TRACE_NPI = HCP_TRACE_NPIS["eligible"]   # fixed trace HCP (00_cohort_config)
_off = OFFSET_DAYS

def _pm(s):
    """Cohort month in pandas (same rule as assign_cohort_month: the offset-th day starts the month)."""
    return ((s - pd.Timedelta(days=_off - 1)) if _off > 0 else s).dt.to_period("M").dt.to_timestamp()

def _clean_py(s):
    for a, b in _CLEAN_STEPS:
        s = s.replace(a, b)
    return s.upper()

# Counted claims only: from DATA_START_DATE on, as the features (RUNNING_ included)
_rx_t = (df_rx.filter((F.col(NPI_COL) == TRACE_NPI) & (F.col(SVC_COL) >= F.lit(DATA_START_DATE)))
         .select("PATIENT_ID", SVC_COL).toPandas())
_rx_t[SVC_COL] = pd.to_datetime(_rx_t[SVC_COL])
_rx_t["_M"] = _pm(_rx_t[SVC_COL])
_pl = _rx_t["PATIENT_ID"].unique().tolist()
_el_t = (pat_elig.filter(F.col("PATIENT_ID").isin(_pl) & (F.col("ELIGIBLE_PATIENT_FLAG") == 1))
         .select("PATIENT_ID", F.to_date("SVC_DT_M").alias("_M"), "GFR_DX_STAGE", "UACR_STAGE").toPandas())
_el_t["_M"] = pd.to_datetime(_el_t["_M"])
_px_t = pat_px.filter(F.col("PATIENT_ID").isin(_pl)).select("PATIENT_ID", "FIRST_DIALYSIS_DATE").toPandas()
_px_t["_FDD"] = pd.to_datetime(_px_t["FIRST_DIALYSIS_DATE"], errors="coerce")

def _expected_counts(claims, tag):
    """Distinct (patient, cohort month) of these claims that are eligible -> {column: count}."""
    pm = claims[["PATIENT_ID", "_M"]].drop_duplicates().merge(_el_t, on=["PATIENT_ID", "_M"], how="inner")
    name = (lambda f: f"RUNNING_{f}") if tag == "RUNNING" else (lambda f: f"{f}{tag}")
    out = {name(TOTAL_COL): len(pm)}
    for prefix, c in [(_PFX_GFR, "GFR_DX_STAGE"), (_PFX_UACR, "UACR_STAGE")]:
        for v, k in pm[c].fillna("null").astype(str).value_counts().items():
            out[name(prefix + _clean_py(v))] = out.get(name(prefix + _clean_py(v)), 0) + int(k)
    return out

_out = (spark.read.format("delta").load(OUTPUT_PATH)
        .filter((F.col(NPI_COL) == TRACE_NPI) & F.col("COHORT_ID").isin(COHORT_IDS))
        .toPandas().set_index("COHORT_ID"))

rows, bad = [], []
for m in COHORT_LIST:
    cb, cid = COHORT_BOUNDS[m], COHORT_BOUNDS[m]["cohort_id"]
    feat = _out.loc[cid] if cid in _out.index else pd.Series(dtype=float)
    upto = _rx_t[_rx_t[SVC_COL] <= pd.Timestamp(cb["cutoff"])]
    expected = _expected_counts(upto, "RUNNING")
    for w in ELIG_LOOKBACK_WINDOWS:
        expected.update(_expected_counts(upto[upto[SVC_COL] > pd.Timestamp(cb["window_bounds"][w]["start"])],
                                         f"_IN_LAST_{w}_MONTH"))
    # Dialysis: any Rx patient of the cohort month with a first dialysis on/before the claim day (or before 2017)
    _cm = upto[upto[SVC_COL] > pd.Timestamp(cb["window_bounds"][1]["start"])].merge(_px_t, on="PATIENT_ID", how="left")
    _dial_exp = int(((_cm["_FDD"] < pd.Timestamp(_DIALYSIS_BEFORE)) | (_cm["_FDD"] <= _cm[SVC_COL])).any())

    _count_cols = [c for c in _out.columns if ("_IN_LAST_" in c or c.startswith("RUNNING_")) and not c.startswith("PCT_")]
    n_bad = 0
    for k in [k for k in expected if k not in _out.columns]:
        n_bad += 1
        bad.append({"COHORT_ID": cid, "feature": k, "raw": expected[k], "feature_value": "column missing"})
    for c in _count_cols:
        fv = int(feat.get(c, 0) or 0)
        if fv != int(expected.get(c, 0)):
            n_bad += 1
            bad.append({"COHORT_ID": cid, "feature": c, "raw": int(expected.get(c, 0)), "feature_value": fv})
    _dial_fv = int(feat.get("DIALYSIS_FLAG", 0) or 0) if cid in _out.index else 0
    if cid in _out.index and _dial_fv != _dial_exp:
        n_bad += 1
        bad.append({"COHORT_ID": cid, "feature": "DIALYSIS_FLAG", "raw": _dial_exp, "feature_value": _dial_fv})
    rows.append({"COHORT_ID": cid, "CUTOFF_DATE": f"{cb['cutoff']:%Y-%m-%d}",
                 **{f"{w}M_raw": int(expected.get(f"{TOTAL_COL}_IN_LAST_{w}_MONTH", 0)) for w in ELIG_LOOKBACK_WINDOWS},
                 **{f"{w}M_feature": int(feat.get(f"{TOTAL_COL}_IN_LAST_{w}_MONTH", 0) or 0) for w in ELIG_LOOKBACK_WINDOWS},
                 "RUNNING_raw": int(expected.get(f"RUNNING_{TOTAL_COL}", 0)),
                 "RUNNING_feature": int(feat.get(f"RUNNING_{TOTAL_COL}", 0) or 0),
                 "DIALYSIS_raw": _dial_exp, "DIALYSIS_feature": _dial_fv,
                 "checks": len(_count_cols) + 1, "mismatches": n_bad})

trace = pd.DataFrame(rows)
print(f"Trace NPI: {TRACE_NPI} | Rx claims: {len(_rx_t):,} | eligible patient-months: "
      f"{len(_rx_t[['PATIENT_ID', '_M']].drop_duplicates().merge(_el_t, on=['PATIENT_ID', '_M'])):,} | "
      f"cohorts: {len(trace)} | checks: {trace['checks'].sum():,} | mismatches: {trace['mismatches'].sum()}")
display(trace)
if bad:
    display(pd.DataFrame(bad).head(50))