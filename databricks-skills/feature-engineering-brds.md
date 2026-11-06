# Kerendia NBA 3.x — Feature Engineering Change Requests

---

## CR-01: Raise Event Prevalence Threshold to Prune Rare Events

**Complexity:** Low | **Impact:** First Occurrence + Recency features (all 4 claim types)

### Business Justification
The BERT Transformer model currently receives first occurrence and recency features for **every** event in the claims data, including events that appear for fewer than 1% of HCPs. These ultra-rare events (e.g., a diagnosis seen by only 50 out of 100K providers) add noise without predictive signal, inflate feature dimensionality, and slow batch processing. Raising the event prevalence threshold ensures only clinically meaningful, statistically robust events generate features.

### Current State
* **File:** [00_config](/editor/notebooks/2494728515032290) — Cell 22
* **Variable:** `event_prevalence = 0.00` (0% — keeps ALL events)
* **Enforcement:** `DataFrameMerger.prevalent_events()` in [00_load_processed_data](/editor/notebooks/2494728515032293) — Cell 3
* **Bypass list:** `relevant_rx_events = ['STEGLATRO','INVOKANA','KERENDIA']` (Cell 11) — these skip the prevalence filter

### Proposed Change
* **Change `event_prevalence` from `0.00` to `0.01`** (1% of distinct HCPs)
* Events appearing in fewer than 1% of distinct PROVIDER_IDs will be filtered out before feature engineering
* Events in `relevant_rx_events` will continue to bypass this filter (existing `isin(relevant_rx_events)` logic in `prevalent_events()`)

### Files to Modify
| File | Location | Change |
| --- | --- | --- |
| `00_config` (ID: 2494728515032290) | Cell 22 | `event_prevalence = 0.00` → `event_prevalence = 0.01` |

### Downstream Impact
* **4 notebooks affected** (via `DataFrameMerger` which reads `event_prevalence`):
  * `01_rx_features_rec_&_first_occ` (ID: 2494728515032398)
  * `02_dx_features_rec_&_first_occ` (ID: 2494728515032399)
  * `03_px_features_rec_&_first_occ` (ID: 2494728515032400)
  * `04_lab_features_rec_&_first_occ` (ID: 2494728515032401)
* **Delta outputs changed:** `{rx,dx,px,lab}_first_occurrence_features`, `{rx,dx,px,lab}_recency_features` — fewer event columns
* **No code changes** needed in the 4 notebooks — the filter is applied inside `DataFrameMerger.prevalent_events()`
* **Frequency & Hospitalization notebooks are NOT affected** — they read Delta directly without `DataFrameMerger`

### Validation (using skills)
* **Skill:** `first-occurrence-features` → Pattern 1 (Feature Column Inventory) — compare event column count before/after
* **Skill:** `recency-features` → Pattern 1 (Column Categories) — verify reduced `_time_min` columns
* **Acceptance:** Event count per claim type should drop measurably (estimate: 10–30% fewer event columns)

---

## CR-02: Align Hospitalization Patient Count Time Windows with Frequency

**Complexity:** Low | **Impact:** DX + PX hospitalization unique patient counts

### Business Justification
The frequency notebooks compute unique patient counts for 5 time windows `[30, 60, 90, 180, 360]` days, but the hospitalization notebooks only use 3 windows `[30, 180, 360]` days. This gap means the model cannot see 60-day or 90-day hospitalized patient trends — critical for detecting short-term escalation in hospitalization (e.g., a provider whose hospitalized patient count spiked in the last 60 days). Aligning the windows gives the BERT model consistent temporal resolution across both feature families.

### Current State
* **DX hospitalization:** [02_dx_hospitalization_features](/editor/notebooks/2494728515032406)
  * Cell 58: `time_windows = [30, 180, 360]` (unpivot)
  * Cell 54: `time_windows = [30, 180, 360]` (flag creation — Note: there's a separate Step 5 cell earlier using `[30, 180, 360]`)
* **PX hospitalization:** [03_px_hospitalization_features](/editor/notebooks/2494728515032407)
  * Cell 60: `time_windows = [30, 180, 360]` (flag creation)
  * Cell 64: `time_windows = [30 , 180, 360]` (unpivot)

### Proposed Change
* **Change `time_windows` from `[30, 180, 360]` to `[30, 60, 90, 180, 360]`** in both notebooks
* Update the `stack()` call from `stack(3, ...)` to `stack(5, ...)` to match the new window count

### Files to Modify
| File | Location | Change |
| --- | --- | --- |
| `02_dx_hospitalization_features` (ID: 2494728515032406) | Cells 54, 58 | `[30, 180, 360]` → `[30, 60, 90, 180, 360]` |
| `02_dx_hospitalization_features` (ID: 2494728515032406) | Cell 58 | `stack(3, ...)` → `stack(5, ...)` |
| `03_px_hospitalization_features` (ID: 2494728515032407) | Cells 60, 64 | `[30, 180, 360]` → `[30, 60, 90, 180, 360]` |
| `03_px_hospitalization_features` (ID: 2494728515032407) | Cell 64 | `stack(3, ...)` → `stack(5, ...)` |

### Downstream Impact
* **Delta outputs changed:**
  * `dx_num_hospitalized_patients_features` — gains 2 new columns per event: `..._IN_LAST_60_DAYS`, `..._IN_LAST_90_DAYS`
  * `px_num_hospitalized_patients_features` — same
* **Combined output in "Combine Everything" section** gains new columns
* **No changes** to `00_config`, `00_load_processed_data`, or any other notebook

### Validation (using skills)
* **Skill:** `hospitalization-features` → Pattern 4 (Patient Counts Over Windows) — verify 5 windows appear
* **Acceptance:** Column count increases by 2 per claim type (60d + 90d); values for 60d and 90d should fall between 30d and 180d logically

---

## CR-03: Expand Relevant RX Events to Include Key CKD Competitive Drugs

**Complexity:** Low | **Impact:** RX First Occurrence + Recency features

### Business Justification
The `relevant_rx_events` list force-keeps specific drugs through the event prevalence filter, ensuring they always generate features even if their provider reach is low. Currently it contains only `['STEGLATRO','INVOKANA','KERENDIA']`. Key CKD competitive drugs — FARXIGA, JARDIANCE, and ENTRESTO — are missing. If the event prevalence threshold is raised (CR-01), these drugs could be inadvertently filtered out for HCP subpopulations where they're rare. Given these are primary Kerendia competitors tracked by the commercial team, they must always have features in the model.

### Current State
* **File:** [00_config](/editor/notebooks/2494728515032290) — Cell 11
* **Variable:** `relevant_rx_events = ['STEGLATRO','INVOKANA','KERENDIA']`
* **Usage:** `DataFrameMerger.prevalent_events()` in [00_load_processed_data](/editor/notebooks/2494728515032293) — forces these events past the prevalence filter via `isin(relevant_rx_events)`

### Proposed Change
* **Expand to:** `relevant_rx_events = ['STEGLATRO', 'INVOKANA', 'KERENDIA', 'FARXIGA BRAND', 'JARDIANCE', 'ENTRESTO']`
* Note: `'FARXIGA BRAND'` is the correct PRODUCT_GROUP name per the market basket mapping (Cell 24 lists `sglt2_list_by_prod_group` with `"FARXIGA BRAND"`, not plain `"FARXIGA"`)

### Files to Modify
| File | Location | Change |
| --- | --- | --- |
| `00_config` (ID: 2494728515032290) | Cell 11 | Add `'FARXIGA BRAND'`, `'JARDIANCE'`, `'ENTRESTO'` to `relevant_rx_events` |

### Downstream Impact
* **Only RX claim type affected** — `relevant_rx_events` is only referenced in RX processing path
* **Delta outputs:** `rx_first_occurrence_features`, `rx_recency_features` — guaranteed to have columns for these 6 drugs
* **Especially important if CR-01 is also implemented** — without this change, raising prevalence to 1% could drop FARXIGA/JARDIANCE for niche HCP segments

### Validation (using skills)
* **Skill:** `first-occurrence-features` → Pattern 1 (Column Inventory) — confirm `max(EVENT_TIME)_FARXIGA_BRAND_first_occurrence`, `max(EVENT_TIME)_JARDIANCE_first_occurrence`, `max(EVENT_TIME)_ENTRESTO_first_occurrence` columns exist
* **Skill:** `rx-claims-eda` — verify these drugs appear in the PRODUCT_GROUP dimension
* **Acceptance:** All 6 drugs always present in feature outputs regardless of prevalence threshold

---

## CR-04: Add Near-Term Time Window (7 Days) to Recency Features

**Complexity:** Medium | **Impact:** Recency features for all 4 claim types

### Business Justification
The BERT model's Masked Event Prediction and Next Event Prediction tasks benefit from detecting **burst activity** immediately before the anchor date. The current smallest window is 30 days — too coarse to detect a sudden spike in prescriptions, diagnoses, or lab tests in the past week. Adding a 7-day window creates features like `total_events_time_7_days` and `unique_events_time_7_days` that can signal acute clinical activity (e.g., a patient hospitalized last week, a new Kerendia prescription 5 days ago). As per your instructions, the model trains on Kerendia Drug Events including hospital visits, prescription claims, and procedure codes — near-term signals are especially important for next-event prediction.

### Current State
* **File:** [00_config](/editor/notebooks/2494728515032290) — Cell 7
* **Variable:** `time_windows = [30, 60, 90, 180, 270, 360]`
* **Consumed by:** `recency` class in [00_recency_features](/editor/notebooks/3340972492350424) — Cell 5
  * `calculate_event_counts_for_time_windows()` → `total_events_time_{N}_days`, `unique_events_time_{N}_days`
  * `calculate_event_counts_by_type_and_window()` → `total_events_time_{N}_days_{type}`, `unique_events_time_{N}_days_{type}`
  * `skewness()` → `skewness_time_{N}_days_{type}`

### Proposed Change
* **Change `time_windows` from `[30, 60, 90, 180, 270, 360]` to `[7, 30, 60, 90, 180, 270, 360]`**

### Files to Modify
| File | Location | Change |
| --- | --- | --- |
| `00_config` (ID: 2494728515032290) | Cell 7 | `time_windows = [30, 60, 90, 180, 270, 360]` → `time_windows = [7, 30, 60, 90, 180, 270, 360]` |

### Downstream Impact
* **4 notebooks affected** (Section B2 — recency computation):
  * `01_rx_features_rec_&_first_occ` (ID: 2494728515032398) — Cells 26–32
  * `02_dx_features_rec_&_first_occ` (ID: 2494728515032399) — Cells 25–31
  * `03_px_features_rec_&_first_occ` (ID: 2494728515032400) — Cells 25–31
  * `04_lab_features_rec_&_first_occ` (ID: 2494728515032401) — Cells 25–31
* **No code changes** needed in notebooks — they consume `time_windows` from config
* **Delta outputs changed:** `{rx,dx,px,lab}_recency_features` — each gains ~18 new columns:
  * 2 overall counts: `total_events_time_7_days`, `unique_events_time_7_days`
  * 8 type×window counts: `total_events_time_7_days_{rx,px,dx,lab_data}`, `unique_events_time_7_days_{rx,px,dx,lab_data}`
  * 4 skewness: `skewness_time_7_days_{rx,px,dx,lab_data}`
* **Helper module** `00_recency_features` reads `time_windows` as constructor parameter — **no code change needed**
* **First Occurrence features NOT affected** — they don't use `time_windows`
* **Frequency features NOT affected** — they define their own lag windows `[1,2,3,6,12]` months

### Validation (using skills)
* **Skill:** `recency-features` → Pattern 2 (Event Volume Over Time Windows) — add `avg("total_events_time_7_days")` and verify it's ≤ 30d value
* **Skill:** `recency-features` → Column Categories — verify new `_7_days` columns appear in all categories
* **Acceptance:** 7d counts should be strictly ≤ 30d counts; skewness_time_7_days may have high NULL rate (few events in 7d window expected)

---

## CR-05: Enable Per-Event Hospitalization Breakdown (Remove Event Collapse)

**Complexity:** Medium-High | **Impact:** DX + PX hospitalization features

### Business Justification
Currently, all diagnosis and procedure claims are collapsed to a single event (`ALL_DIAGNOSIS` / `ALL_PROCEDURES`) before computing hospitalization rates. This means the model only sees "X% of this HCP's total claims are hospitalized" — it cannot distinguish between "high hospitalization for CKD" vs "high hospitalization for heart failure." Removing the collapse enables per-event hospitalization signals, letting the BERT model learn event-specific hospitalization patterns (e.g., providers with high CKD hospitalization but low T2D hospitalization may indicate a different patient acuity profile).

### Current State
* **DX:** [02_dx_hospitalization_features](/editor/notebooks/2494728515032406)
  * Cell 6: `lit("ALL_DIAGNOSIS").alias("DIAGNOSIS_DESCRIPTION")` — overwrites original diagnosis
  * Cell 8: Same collapse applied to hospitalized claims
* **PX:** [03_px_hospitalization_features](/editor/notebooks/2494728515032407)
  * Cell 6: `lit("ALL_PROCEDURES").alias("PROCEDURE_DESCRIPTION")` — overwrites original procedure
  * Cell 8: Same collapse applied to hospitalized claims

### Proposed Change
* **Remove the `lit()` overwrite** — keep original `DIAGNOSIS_DESCRIPTION` / `PROCEDURE_DESCRIPTION` from the Delta input
* DX Cell 6: Change `.select(..., lit("ALL_DIAGNOSIS").alias("DIAGNOSIS_DESCRIPTION"), ...)` to `.select(..., "DIAGNOSIS_DESCRIPTION", ...)`
* DX Cell 8: Same change for hospitalized claims
* PX Cell 6: Change `.select(..., lit("ALL_PROCEDURES").alias("PROCEDURE_DESCRIPTION"), ...)` to `.select(..., "PROCEDURE_DESCRIPTION", ...)`
* PX Cell 8: Same change for hospitalized claims

### Files to Modify
| File | Location | Change |
| --- | --- | --- |
| `02_dx_hospitalization_features` (ID: 2494728515032406) | Cell 6 | Remove `lit("ALL_DIAGNOSIS").alias("DIAGNOSIS_DESCRIPTION")` → keep `"DIAGNOSIS_DESCRIPTION"` |
| `02_dx_hospitalization_features` (ID: 2494728515032406) | Cell 8 | Same change for hospitalized claims |
| `03_px_hospitalization_features` (ID: 2494728515032407) | Cell 6 | Remove `lit("ALL_PROCEDURES").alias("PROCEDURE_DESCRIPTION")` → keep `"PROCEDURE_DESCRIPTION"` |
| `03_px_hospitalization_features` (ID: 2494728515032407) | Cell 8 | Same change for hospitalized claims |

### Downstream Impact
* **Massive feature expansion** — instead of 1 event per claim type, output will have N events (e.g., ~17 DX events, ~5 PX events based on claims EDA)
* **Column explosion in lag/% outputs:**
  * `TOTAL_CLAIMS_{EVENT}_IN_LAST_{N}_MONTH` — N events × 3 windows
  * `PERC_HOSPITALIZED_HCP_CLAIMS_FOR_{EVENT}_IN_LAST_{N}_MONTH` — same
* **Validation filter** (Cell 29/31) will need updating — currently hardcoded to `ALL_DIAGNOSIS` / `ALL_PROCEDURES` column names
* **Unique patient counts** (Sub-type D) — will now group by per-event instead of single event, significantly more columns
* **"Combine Everything" section** — PX `_PX` suffix logic still applies but to more columns
* **Memory/compute considerations:** More pivoted columns increases Spark shuffle and memory pressure

### Validation (using skills)
* **Skill:** `hospitalization-features` → Pattern 1 (Hospitalization Rate Distribution) — verify per-event rates
* **Skill:** `dx-claims-eda` — cross-reference expected event list from `DIAGNOSIS_DESCRIPTION` dimension
* **Acceptance:** Output should contain PERC_HOSPITALIZED columns for top diagnoses (e.g., CHRONIC_KIDNEY_DISEASE, TYPE_2_DIABETES, HEART_FAILURE); rates should vary across events (not all identical)

---

## CR-06: Support Per-Claim-Type Lookback Duration in DataFrameMerger

**Complexity:** High | **Impact:** All patient-level features (First Occurrence + Recency)

### Business Justification
Clinically, different claim types have different information horizons. Recent RX prescriptions (last 6 months) strongly predict near-term prescribing behavior, while DX history (chronic conditions diagnosed years ago) provides long-term patient context. The current global `lookback_duration = 365` forces a one-size-fits-all window. Supporting per-claim-type lookback durations lets the model weigh recent RX signals more heavily while retaining deep DX/Lab history — directly improving the BERT model's Masked Event Prediction by providing temporally appropriate context per event type.

### Current State
* **File:** [00_config](/editor/notebooks/2494728515032290) — Cell 7
* **Variable:** `lookback_duration = 365` (global, in days)
* **Consumed by:** `DataFrameMerger.__init__()` in [00_load_processed_data](/editor/notebooks/2494728515032293) — Cell 3
  * Used in `generate_date_list()`: `date_add(col("LOOKBACK_END_DATE"), -1*self.lookback_duration)`
  * Applied identically to RX, DX, PX, and Lab

### Proposed Change

**Phase 1 — Config change:**
* Add per-claim-type lookback durations to [00_config](/editor/notebooks/2494728515032290) Cell 7:
```python
lookback_duration = 365  # default (keep for backward compat)
lookback_duration_by_type = {
    "rx": 365,       # 12 months — recent prescribing behavior
    "dx": 730,       # 24 months — chronic condition history
    "px": 365,       # 12 months — procedure recency
    "lab": 730,      # 24 months — trending lab values over time
}
```

**Phase 2 — DataFrameMerger change:**
* Modify `DataFrameMerger.__init__()` to accept an optional `lookback_duration_override` parameter
* Modify `generate_date_list()` to use the override when provided
* Each `_rec_&_first_occ` notebook would pass the appropriate claim-specific lookback:
```python
# In 01_rx_features_rec_&_first_occ:
data_merger = DataFrameMerger(
    ..., lookback_duration=lookback_duration_by_type.get("rx", lookback_duration), ...
)
```

### Files to Modify
| File | Location | Change |
| --- | --- | --- |
| `00_config` (ID: 2494728515032290) | Cell 7 | Add `lookback_duration_by_type` dict |
| `00_load_processed_data` (ID: 2494728515032293) | Cell 3 | Add optional override param to `DataFrameMerger.__init__()` |
| `01_rx_features_rec_&_first_occ` (ID: 2494728515032398) | Section A (DataFrameMerger call) | Pass `lookback_duration_by_type["rx"]` |
| `02_dx_features_rec_&_first_occ` (ID: 2494728515032399) | Section A | Pass `lookback_duration_by_type["dx"]` |
| `03_px_features_rec_&_first_occ` (ID: 2494728515032400) | Section A | Pass `lookback_duration_by_type["px"]` |
| `04_lab_features_rec_&_first_occ` (ID: 2494728515032401) | Section A | Pass `lookback_duration_by_type["lab"]` |

### Downstream Impact
* **First Occurrence features:** DX and Lab would see events going back 24 months instead of 12 — more first-occurrence values populated (fewer NULLs)
* **Recency features:** 12M filter still applies to recency (LOOKBACK_START_DATE → LOOKBACK_END_DATE), but LOOKBACK_START_DATE itself shifts back for DX/Lab
* **Anchor dates CSV** (`hcp_model_inference_anchor_dates.csv`) — would need per-claim-type LOOKBACK_START_DATE, or generate multiple versions
* **Backward compatible:** if `lookback_duration_by_type` is not defined, falls back to global `lookback_duration = 365`
* **Frequency & Hospitalization notebooks NOT affected** — they don't use `DataFrameMerger`

### Validation (using skills)
* **Skill:** `first-occurrence-features` → Pattern 5 (Patients Who Never Had an Event) — NULL rate for DX/Lab should decrease with 730d lookback
* **Skill:** `recency-features` → Pattern 2 (Event Volume Over Time Windows) — DX/Lab should show higher event counts
* **Acceptance:** DX first occurrence NULL rate drops by 5–15% vs 365d baseline; RX features remain identical to current

---

## Summary Matrix

| CR | Change | Complexity | Files Modified | Notebooks Re-run | Skill to Validate |
| --- | --- | --- | --- | --- | --- |
| CR-01 | Event prevalence 0% → 1% | Low | `00_config` Cell 22 | 4 rec_&_first_occ | `first-occurrence-features`, `recency-features` |
| CR-02 | Hosp windows [30,180,360] → [30,60,90,180,360] | Low | 2 hosp notebooks | 2 hosp | `hospitalization-features` |
| CR-03 | Add FARXIGA/JARDIANCE/ENTRESTO to relevant_rx_events | Low | `00_config` Cell 11 | 1 rx rec_&_first_occ | `first-occurrence-features`, `rx-claims-eda` |
| CR-04 | Add 7d to time_windows | Medium | `00_config` Cell 7 | 4 rec_&_first_occ | `recency-features` |
| CR-05 | Remove ALL_DIAGNOSIS/ALL_PROCEDURES collapse | Medium-High | 2 hosp notebooks (4 cells) | 2 hosp | `hospitalization-features`, `dx-claims-eda` |
| CR-06 | Per-claim-type lookback duration | High | `00_config`, `00_load_processed_data`, 4 notebooks | 4 rec_&_first_occ | All 4 feature skills |
