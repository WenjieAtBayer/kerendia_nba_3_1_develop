---
name: hospitalization-features
description: >
  Guidance for understanding and exploring Hospitalization features in the Kerendia NBA 3.x
  pipeline. Read this skill when the user asks about hospitalization features, % hospitalized,
  hospitalization rates, DATA_SOURCE='HX', or the _hospitalization_features notebooks.
  DX and PX only — no RX or Lab hospitalization features exist.
---

# Hospitalization Features — HCP-Level Feature Engineering

Hospitalization features measure **what fraction of an HCP's claims involve hospitalized
patients** (DATA_SOURCE = 'HX'). These are **DX and PX only** — no RX or Lab hospitalization
features exist in the pipeline.

As per your instructions, these features feed the BERT Transformer model trained on Kerendia
Drug Events for Masked Event Prediction, Next Event Prediction, and Shuffled Order correction.

## Key Design Decisions

1. **Single collapsed event** — no per-event breakdown. All claims are collapsed to `ALL_DIAGNOSIS` (DX) or `ALL_PROCEDURES` (PX) via `lit("ALL_DIAGNOSIS")` / `lit("ALL_PROCEDURES")`
2. **Two input sources** — total claims (`dx1_file_path`/`px1_file_path`) + hospitalized-only claims (`dx_hosp_file_path`/`px_hosp_file_path`, filtered by `DATA_SOURCE='HX'`)
3. **HCP flags dropped** — `KERENDIA_FLAG`, `SGLT2_GLP1_FLAG`, `NEPH_FLAG`, `TARGETING_HCP_FLAG`, `BPT_HCP_FLAG` are dropped from hospitalized claims
4. **Rolling windows shorter** than frequency: `[1, 6, 12]` months (vs frequency's `[1, 2, 3, 6, 12]`)
5. **Validation filter** — rows where `TOTAL < HOSPITALIZED` are removed (data quality)

---

## Architecture: 4 Sub-Feature Types + Combine

```
Total Claims (dx1/px1_file_path)     Hospitalized Claims (dx/px_hosp_file_path)
      │                                        │
      ▼                                        ▼
  lit("ALL_DIAGNOSIS")                   lit("ALL_DIAGNOSIS")
  + SVC_DT_M = date_trunc('MM')         + SVC_DT_M = date_trunc('MM')
      │                                        │
      ▼                                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Sub-type A: Total & Hospitalized Claim Counts       │
│  TOTAL_CLAIMS_{EVENT}, TOTAL_HOSPITALIZED_CLAIMS_*   │
│  Left join total ⟕ hospitalized, fillna(0)            │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  Sub-type B: Lag Hospitalized Counts                  │
│  step2_fill_missing → step3_lag [1,6,12] months      │
│  ** Validation: remove rows TOTAL < HOSPITALIZED **   │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  Sub-type C: % Hospitalized                           │
│  WHEN TOTAL != 0 THEN HOSP / TOTAL ELSE NULL          │
│  Drop TOTAL_CLAIMS_* columns after computing %         │
│  Keep: PERC_HOSPITALIZED_* + TOTAL_HOSPITALIZED_*     │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
  Save: {claim}_percentage_hospitalized_features

      (independent)
┌─────────────────────────────────────────────────────────────┐
│  Sub-type D: Unique Hospitalized Patient Counts       │
│  Cross-join hospitalized claims × anchor dates        │
│  Time windows: [30, 180, 360] days                    │
└─────────────────────────────────────────────────────────────┘
      │
      ▼
  Save: {claim}_num_hospitalized_patients_features

      │
      ▼
  ** Combine Everything ** (joins % hosp + patient counts on HCP_COHORT_ID)
```

---

## Sub-Type A: Total & Hospitalized Claim Counts

**Grain:** `[PROVIDER_ID, SVC_DT_M]`

```python
# Total claims (all-source)
total_claims = claims.groupBy(index_cols).pivot(EVENT_COL).agg(F.count(F.lit(1)))
# Rename: TOTAL_CLAIMS_{EVENT}

# Hospitalized claims (HX-source only)
total_hosp = hosp_claims.groupBy(index_cols).pivot(EVENT_COL).agg(F.count(F.lit(1)))
# Rename: TOTAL_HOSPITALIZED_CLAIMS_{EVENT}

# Left join + fillna(0)
combined = total_claims.join(total_hosp, on=index_cols, how='left').fillna(0)
```

Since events are collapsed (`ALL_DIAGNOSIS` / `ALL_PROCEDURES`), this produces only:
* `TOTAL_CLAIMS_ALL_DIAGNOSIS` + `TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS` (DX)
* `TOTAL_CLAIMS_ALL_PROCEDURES` + `TOTAL_HOSPITALIZED_CLAIMS_ALL_PROCEDURES` (PX)

---

## Sub-Type B: Lag Hospitalized Counts

**Grain:** `[PROVIDER_ID, SVC_DT_M]`

Same `step2_fill_missing` / `step3_lag` / `process_and_join` helpers as Frequency, but:
* **Rolling windows:** `[1, 6, 12]` months (shorter than frequency's `[1,2,3,6,12]`)
* **Input:** the combined total + hospitalized counts from Sub-type A

**Output columns:**
* `TOTAL_CLAIMS_ALL_DIAGNOSIS_IN_LAST_{N}_MONTH`
* `TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS_IN_LAST_{N}_MONTH`

**Validation filter** (critical data quality step):
```python
# Remove rows where total < hospitalized (impossible — data quality issue)
lag_hosp = lag_hosp.filter(
    (col("TOTAL_CLAIMS_ALL_DIAGNOSIS_IN_LAST_1_MONTH") >= col("TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS_IN_LAST_1_MONTH")) &
    (col("TOTAL_CLAIMS_ALL_DIAGNOSIS_IN_LAST_6_MONTH") >= col("TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS_IN_LAST_6_MONTH")) &
    (col("TOTAL_CLAIMS_ALL_DIAGNOSIS_IN_LAST_12_MONTH") >= col("TOTAL_HOSPITALIZED_CLAIMS_ALL_DIAGNOSIS_IN_LAST_12_MONTH"))
)
```

---

## Sub-Type C: % Hospitalized

**Grain:** `[PROVIDER_ID, SVC_DT_M]`

**Formula:**
```python
PERC_HOSPITALIZED_HCP_CLAIMS_FOR_{EVENT}_IN_LAST_{N}_MONTH =
    WHEN TOTAL_CLAIMS_{EVENT}_IN_LAST_{N}_MONTH != 0
    THEN TOTAL_HOSPITALIZED_CLAIMS_{EVENT}_IN_LAST_{N}_MONTH / TOTAL_CLAIMS_{EVENT}_IN_LAST_{N}_MONTH
    ELSE NULL
```

**Windows:** `[1, 6, 12]` months

**After computing %:** `TOTAL_CLAIMS_*_IN_LAST_*` columns are dropped.
**Kept:** `PERC_HOSPITALIZED_*` + `TOTAL_HOSPITALIZED_*` + key columns.

---

## Sub-Type D: Unique Hospitalized Patient Counts

**Grain:** `[PROVIDER_ID, COHORT]`

Same cohort cross-join pattern as Frequency Sub-type D, but:
* **Uses hospitalized claims only** (not total claims)
* **Time windows:** `[30, 180, 360]` days (NOT `[30, 60, 90, 180, 360]` like frequency)
* **Count column:** `hospitalized_pt_cnt_{N}_days` (not `pt_cnt_{N}_days`)

**Feature prefix varies by claim type:**

| Claim | Feature Prefix |
| --- | --- |
| DX | `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DIAGNOSED_IN_LAST_{N}_DAYS` |
| PX | `NUM_OF_HOSPITALIZED_PATIENTS_THE_HCP_DID_PROCEDURE_IN_LAST_{N}_DAYS` |

---

## Combine Everything (Final Section)

Both notebooks end with a "Combine Everything" section that:
1. Reads `hcp_universe` × `cohort_anchor_dates` to create `skeleton_df` with `HCP_COHORT_ID`
2. Reads back `{claim}_percentage_hospitalized_features` and joins with HCP universe on `[PROVIDER_ID, SVC_DT_M]`
3. Reads back `{claim}_num_hospitalized_patients_features` and joins on `[PROVIDER_ID, COHORT]`
4. Joins both on `HCP_COHORT_ID`
5. **PX adds `_PX` suffix** to all non-key columns to avoid name collisions with DX

---

## Per-Claim-Type Inventory

### Notebooks

| Claim | Notebook | ID | Cells |
| --- | --- | --- | --- |
| DX | `02_dx_hospitalization_features` | 2494728515032406 | 80 |
| PX | `03_px_hospitalization_features` | 2494728515032407 | 87 |

**No RX or Lab hospitalization notebooks exist.**

### Input Paths (from config)

| Claim | Total Claims Path | Hospitalized Claims Path |
| --- | --- | --- |
| DX | `dx1_file_path` → `dx_input_claims_12M_and_first_occ_features_input` | `dx_hosp_file_path` → `dx_hospitalization_claims_all_events_features_input` |
| PX | `px1_file_path` → `px_input_claims_12M_and_first_occ_features_input` | `px_hosp_file_path` → `px_hospitalization_claims_all_events_features_input` |

### Delta Output Paths

All under `.../notebook_output/` in the volume.

| Sub-Type | DX | PX |
| --- | --- | --- |
| C: % Hospitalized | `dx_percentage_hospitalized_features` | `px_percentage_hospitalized_features` |
| D: Hosp Patient Counts | `dx_num_hospitalized_patients_features` | `px_num_hospitalized_patients_features` |

(Sub-types A and B are intermediate — not saved separately as named Delta)

### Event Collapse

| Claim | Original Event Column | Collapsed To |
| --- | --- | --- |
| DX | `DIAGNOSIS_DESCRIPTION` | `lit("ALL_DIAGNOSIS")` |
| PX | `PROCEDURE_DESCRIPTION` | `lit("ALL_PROCEDURES")` |

---

## Key Differences from Frequency Features

| Aspect | Hospitalization | Frequency |
| --- | --- | --- |
| **Claim types** | DX + PX only | RX + DX + PX + Lab |
| **Event granularity** | Single collapsed event | Per-event breakdown |
| **Two inputs** | Total + Hospitalized (HX) | Single claims input |
| **Lag windows** | `[1, 6, 12]` months | `[1, 2, 3, 6, 12]` months |
| **Patient count windows** | `[30, 180, 360]` days | `[30, 60, 90, 180, 360]` days |
| **Validation filter** | Total >= Hospitalized | None |
| **% computation** | HOSP / TOTAL per window | Rate of change vs 12M baseline |
| **Final combine** | Joins % + patient counts on HCP_COHORT_ID | No combine step |
| **PX suffix** | `_PX` appended to avoid collisions | None |

---

## Notebook References

**Feature notebooks:**
* [02_dx_hospitalization_features](/editor/notebooks/2494728515032406) — DX hospitalization (80 cells)
* [03_px_hospitalization_features](/editor/notebooks/2494728515032407) — PX hospitalization (87 cells)

**Config & infrastructure:**
* [00_config](/editor/notebooks/2494728515032290) — `dx_hosp_file_path`, `px_hosp_file_path`, `hcp_universe_path`
* [00_connection](/editor/notebooks/198916793189023) — Imports
* `hcp_model_inference_anchor_dates.csv` — Cohort anchor dates for Sub-type D
