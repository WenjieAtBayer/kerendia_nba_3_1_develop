# HCP-level features: shared config readiness

**Folder:** `NBA 3.1 - Dev/03_HCP_Level_Features/` (branch `dev/claims-comorbidity-competitor-features`)  
**Date:** 2026-11-20  
**Status:** changes made and validated, **not committed**. Notebooks not run end to end.

## 1. In short

The five HCP-level feature notebooks had business constants typed by hand: CKD / ESRD / stage code lists, LOE and approval dates, drug lists and paths. Some were typed in more than one notebook (the Entresto LOE date in `11` and `36`, the CKD codes in `09` and `11`).

They now read them from one file, `hcp_features_config.py`, in this folder. Diagnosis codes are no longer listed at all: they come from the **latest dated Dx Product Basket** in `kerendia_nba_3_1_volume/final_product_mapping/`, using the same latest-file logic as `00_cohort_config` (`product_mapping_path`) on `dev/hcp-claims-features`.

Every value that moved was checked: the notebooks get exactly the same values as before (section 4).

## 2. How to use it

Each notebook's setup cell now starts with:

```python
sys.path.insert(0, os.getcwd())          # this folder
import hcp_features_config as cfg
importlib.reload(cfg)
```

Variable names in the notebooks did not change (e.g. `CKD_CODES`, `DRUG_GROUPS`, `EVENTS`), so the rest of each notebook is untouched.

**Changing a basket:** upload a new dated file (`Kerendia_Dx_Final_Product_Mapping_YYYY_MM_DD.csv`); the next run uses it. Never edit an existing dated file. To rerun on an older basket, set `cfg.PRODUCT_MAPPING_DATE` (or pass `date=`). A file with missing columns, or a date that does not exist, stops the run with a clear message.

**Changing a date or a drug list:** edit it once in `hcp_features_config.py`; every notebook that uses it picks it up.

## 3. What moved to the config

### 3.1 Diagnosis codes (now from the Dx Product Basket, not lists)

| Before (hardcoded) | Notebook | Now | Rule on the Dx basket columns |
| --- | --- | --- | --- |
| `ST3_CODES` N18.3, N18.30, N18.31, N18.32 | 09, 11 (stage-3 check) | `cfg.dx_code_sets()["ST3"]` | `CONDITION = CKD`, `CKD_STAGE = 3` |
| `ST4_CODES` N18.4 | 09 | `["ST4"]` | `CONDITION = CKD`, `CKD_STAGE = 4` |
| `ESRD_CODES` N18.6, Z99.2, I12.0, I13.11, I13.2 | 09 | `["ESRD"]` | `CKD_SUBSTAGE = ESRD`; plus stage 5 codes that are not N18.x (I12 / I13, where the code does not separate stage 5 from ESRD); plus staged dialysis codes (`CONDITION = DIALYSIS` with a `CKD_STAGE`: Z99.2) |
| `CKD_CODES` 18 codes (N18.1-N18.5, N18.9 incl. N18.30/31/32; E10.21/22/29; E11.21/22/29; I12.9; I13.0; I13.10) | 09 | `["CKD"]` | `CONDITION = CKD`, `IS_DEFINING = Y`, `DM_TYPE` not OTHER, minus ESRD |
| `CKD_DX_CODES` 24 codes (the 18 + the 5 ESRD + D63.1) | 11 | `["CKD_ANY"]` | `CONDITION = CKD`, `DM_TYPE` not OTHER (includes D63.1), plus ESRD |
| Prefixes E11 (T2D), E10 (T1D), I50 / I50.2 / I50.3 (HF, HF systolic, HF diastolic) | 09 | `cfg.DX_PREFIXES` | Prefix rules (not a code list), now in one place |

Codes added to the basket later (e.g. a new stage-3 code) are picked up automatically. Tested on a temporary copy of the basket folder: a newer dated Dx file with an extra stage-3 code was selected and the code appeared in `ST3`; a pinned older date still gave the old list. The shared folder was not touched.

### 3.2 Market events and dates

| Before | Notebook | Now |
| --- | --- | --- |
| `EVENTS` table: FARXIGA_LOE 2026-04-06, ENTRESTO_LOE 2025-07-01 (build); ENTRESTO_FULL_GENERIC, BAXFENDY_LAUNCH, EASI_KIDNEY_READOUT, GLP1_GUIDELINES (defer) | 36 | `cfg.MARKET_EVENTS` |
| `ENTRESTO_LOE_DATE = "2025-07-01"` (second copy of the same date) | 11 | `cfg.ENTRESTO_LOE_DATE` (read from `cfg.MARKET_EVENTS`) |
| `APPROVAL_DATES` Invokana 2013-03-29, Farxiga 2014-01-08, Jardiance 2014-08-01, Entresto 2015-07-07 | 11 | `cfg.APPROVAL_DATES` |
| `DATE_FLOORS` Invokana 2019-10-01, Farxiga 2021-04-01 | 11 | `cfg.DATE_FLOORS` |

### 3.3 Drug groups and claim types

| Before | Notebook | Now |
| --- | --- | --- |
| `DRUG_GROUPS` (Rx_01_new names): Invokana, Farxiga, Jardiance, steroidal MRA = SPIRONOLACTONE + EPLERENONE, Entresto | 11 | `cfg.RX01_DRUG_GROUPS` |
| `ENTRESTO_BRAND_PRODUCTS`, `ENTRESTO_PRODUCTS` (ENTRESTO + SACUBITRIL/VALSARTAN, SACUBITRIL/VALSART) | 11 | `cfg.ENTRESTO_BRAND_PRODUCTS`, `cfg.ENTRESTO_PRODUCTS` |
| `DRUGS` (V7 product groups): Farxiga brand / generic, Jardiance, Invokana, Steglatro, GLP-1 (Ozempic, Wegovy, Wegovy HD, Rybelsus, Mounjaro, Zepbound) | 31 | `cfg.V7_DRUG_GROUPS` |
| `SMRA_CLASS = "sMRA"` | 31 | `cfg.V7_SMRA_CLASS` |
| `FARXIGA_PGS` (FARXIGA BRAND, FARXIGA GENERIC) | 36 | `cfg.V7_FARXIGA_GROUPS` |
| Approved claims = PD + RV | 10 | `cfg.APPROVED_CLAIM_TYPES` |

### 3.4 Paths and tables

| Before (typed in each notebook) | Notebooks | Now |
| --- | --- | --- |
| 3.1 volume, HCP universe, claims cohorts, dev_pipeline query output, HCP features output, notebook output | 09, 10, 11, 31, 36 | `cfg.VOL31`, `cfg.HCP_UNIVERSE_PATH`, `cfg.COHORTS_DIR`, `cfg.QUERY_OUTPUT_31`, `cfg.HCP_FEATURES_OUT_31`, `cfg.NB_OUT_31` |
| Dx event list path | 09, 11 | `cfg.DX_EVENTS_PATH` |
| LRx V7 table | 10, 31, 36 | `cfg.LRX_V7_TABLE` |
| 3.0 volume (reference table for the prior-writing check) | 10 | `cfg.VOL30` |

## 4. Validation (2026-11-20)

| Check | Result |
| --- | --- |
| Code sets from the basket vs the old lists: CKD (18), ESRD (5), stage 3 (4), stage 4 (1), CKD_ANY (24) | Identical |
| Old setup cells (from Git) vs new setup cells, run side by side, every value compared (09: 27, 10: 23, 11: 30, 31: 20, 36: 28 names) | Identical, except two differences that do not change results (next rows) |
| 31 and 36: V7 table name written with / without backticks on the schema | Same table (same columns, same 4,124,829,567 rows) |
| 09: the `isin` code lists are now sorted, so the filter text reads differently | All 368 distinct codes in the Dx event list get the same 9 flags (T2D, T1D, CKD, ESRD, ST3, ST4, HF, HF_SYS, HF_DIA): 0 differences |
| 11: CKD codes and the stage-3 check list | Identical |
| Every code cell of the 5 notebooks compiles | Pass |
| Basket loader: latest file (Rx 2026_11_13, Dx 2026_11_06), pinned date, unknown date stops, all 5 basket types have their columns | Pass |
| Constants vs the notebooks: market events (36), approval dates and floors (11), V7 drug groups (31; every group exists in V7), paths exist | Pass |

No table was written during the validation (the event-table write in `36` was switched off for the test).

**Not yet done:** an end-to-end run. Before committing, run `09`, `11`, `31` and `36` with a small `TEST_HCP_SAMPLE` (outputs go to `_test` tables). `10` has no test mode and `REFRESH_PULL = True` re-pulls from Snowflake, so leave it out of a quick run.

## 5. What stays in the notebooks, and why

| Item | Notebook | Why it stays |
| --- | --- | --- |
| Look-back windows: `WINDOWS = [3, 6, 12]` (10), `[3, 12]` (31); 24-month window (09); 3 months before / 2 after the Farxiga LOE (36) | 09, 10, 31, 36 | Feature design, different on purpose per notebook |
| Feature and column names (e.g. `ENTRESTO_BRAND_ADOPTER_FLAG`, `KERENDIA_NBRX_IN_LAST_3_MONTH`), `FEATURE_GROUPS`, `SCOPES` | all | Output definition of each notebook |
| PD / RJ / RV claim-type expressions | 10 | Fixed IQVIA claim type values; only the business rule "approved = PD + RV" moved |
| Drug keys used inside formulas (e.g. Farxiga = brand + generic; SGLT2 = Farxiga + Jardiance + Invokana + Steglatro) | 31 | Feature logic built on the config groups |
| Kerendia filter `PRODUCT_GROUP = 'KERENDIA'` (Snowflake pull and V7 check) | 10 | Single product; could move to the config later |
| Check-only dates (`2026-08-01`, `2026-09-18`) in the prior-writing cross-check | 10 | Describe the saved 3.0 reference snapshot, used only by the check |
| LRx-cohorts-if-present fallback | 31, 36 | Path logic of those notebooks |

## 6. Open decisions

| # | Decision | Detail | Owner |
| --- | --- | --- | --- |
| 1 | **ESRD rule** | The Dx basket does not tag I12.0, I13.11, I13.2 as ESRD ("stage 5 or ESRD, code does not separate them"). The config reproduces today's list with a rule (stage 5 codes that are not N18.x). Cleaner: upload a new dated Dx file that sets `CKD_SUBSTAGE = ESRD` on those three codes | NBA team |
| 2 | **Dialysis codes** | The basket flags Z49.01, Z49.02, Z49.31, Z49.32 as `DIALYSIS`; today's ESRD list has only Z99.2. Include them or not | NBA team |
| 3 | **Other diabetes kidney codes** | E08.21/22/29, E09.22, E13.21/22/29 are `CONDITION = CKD` with `DM_TYPE = OTHER`; today they are excluded | NBA team |
| 4 | **Steroidal MRA and SGLT2 lists** | Still different: `11` = SPIRONOLACTONE + EPLERENONE; `31` = V7 `PRODUCT_CLASS = sMRA`; `31_Competitor_drugs_NBRx_share_nba31` (branch `dev/nbrx-nrx-trx-features`) has its own longer MRA and SGLT2 lists. Agree one definition, then put it in the config | Sehar / NBA team |
| 5 | **Entresto LOE exact day** | 2025-07-01 is the month from the CI report (Q6, confirm with Josh). Now one place to change | Josh |
| 6 | **One global config** | Merge this file with `00_cohort_config` (`dev/hcp-claims-features`) during Ops | Ops |

## 7. Files changed

* New: `hcp_features_config.py`, `hcp_features_config_readiness.md` (this file)
* Setup cells only: `09_claim_comorbidity` (cell 3), `10_kerendia_prior_writing` (cell 3), `11_adoption_features` (cells 3 and 6), `31_Competitor_drugs_NBRX_share` (cell 3), `36_market_event_features` (cell 3)
* Notebook owner: Sehar. Agree with her before pushing.
