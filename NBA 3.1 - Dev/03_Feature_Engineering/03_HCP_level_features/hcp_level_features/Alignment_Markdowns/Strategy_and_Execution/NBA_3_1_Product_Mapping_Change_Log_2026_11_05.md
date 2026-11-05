# NBA 3.1 product mapping: change log 2026-11-05

For: Saurabh, Sehar. Status: 2026-11-05. The new files are written; the patient journey (PJ01-PJ05) reads them through the loader. The GLP-1 column clash in NB01 is resolved with option C (section 5, decided 2026-11-05).

## 1. Files

Folder: `/Volumes/ph-com-ai-us-prod-catalog-2553213839599380/kerendia_nba_3/kerendia_nba_3_1_volume/final_product_mapping/`

| File | Rows | Change vs 2026_11_04 |
| --- | --- | --- |
| `Kerendia_Rx_Final_Product_Mapping_2026_11_05.csv` | 367 | 16 rows N -> Y (section 2) |
| `Kerendia_Px_Final_Product_Mapping_2026_11_05.csv` | 145 | 1 row N -> Y (section 3) |
| `Kerendia_Dx_Final_Product_Mapping_2026_11_05.csv` | 240 | none (copy) |
| `Kerendia_Lab_Final_Product_Mapping_2026_11_05.csv` | 28 | none (copy) |
| `Kerendia_Dx_Flag_Additions_2026_11_05.csv` | 116 | none (copy) |

The 2026_11_04 files are unchanged (same md5 before and after).

## 2. Rx: 16 products switched on

| Products | ACTIVE_JOURNEY | TREATMENT_CATEGORY | BRAND_LABEL |
| --- | --- | --- | --- |
| OZEMPIC, MOUNJARO, TRULICITY, RYBELSUS, VICTOZA, LIRAGLUTIDE, BYDUREON BCISE, BYETTA, EXENATIDE, WEGOVY, WEGOVY HD, ZEPBOUND, SAXENDA (13 GLP-1) | N -> Y | GLP-1 | GLP-1 |
| KERENDIA | N -> Y | KERENDIA (own category, not MRA) | KERENDIA |
| DAPAGLIFLOZIN, DAPAGLIFLOZIN/METFORMIN H (generic Farxiga) | N -> Y | SGLT2 | empty |

After the change: 245 Y and 122 N rows. Active categories (rows): Calcium channel / Beta blocker 56, Combo drug 44, Insulin 41, ACE/ARB 32, Diuretic_NON_MRA 30, SGLT2 17, GLP-1 13, metformin 6, MRA 5, KERENDIA 1.

Not changed: XULTOPHY 100/3.6 (Insulin, brand label GLP-1) and SOLIQUA 100/33 (Insulin) were already active and stay as they are.

## 3. Px: one dialysis code switched on

* J0606 (etelcalcetide): ACTIVE_DIALYSIS N -> Y, PX_GROUP = DIALYSIS_DRUG. There are now 30 dialysis codes (was 29).

## 4. File format (for Sehar)

The notebooks read the files in one fixed format, and the loader rejects a file in another format:

* Column names as in the notebook files, e.g. `PATIENTS_TOTAL` in upper case (the 2026_11_04 Rx / Px / Dx files have `patients_total`).
* Whole numbers without ".0" (e.g. `4914681`, not `4914681.0`).
* Extra columns of the 2026_11_04 files (`providers_total`, `nbrx_total`, `club_members`, `n_members`, `is_clubbed`, `club_reason`, ...) are not in the 2026_11_05 files. The Lab file keeps its 12 notebook columns.

For the next update: start from the 2026_11_05 files, keep their columns, and save with a new date in the file name. The loader picks the newest date. A job can pin a date with the parameter `PRODUCT_MAPPING_DATE`.

Loader: `product_mapping_path(kind)` in `00_cohort_config` (kinds `rx`, `px`, `dx`, `lab`, `dx_flag_additions`), used by PJ01-PJ05.

## 5. Effect on the HCP features

Measured on the Rx pull that the HCP notebooks read today (`ops_pipeline/query_output/full_2026_11_02/_stage/rx_hcp_pull`, built with the 2026_11_04 mapping). The new mapping takes effect when the patient journey (PJ03) rebuilds the pull in the next full run.

**Today**, 6 of the 13 GLP-1 products are in the pull as HCP-only rows with treatment category `Other- glucose mgmt` and brand `GLP-1`:

| Product | Claims | NPIs |
| --- | --- | --- |
| OZEMPIC | 131,221,734 | 253,210 |
| TRULICITY | 43,825,763 | 225,004 |
| RYBELSUS | 13,768,333 | 202,023 |
| VICTOZA | 4,406,689 | 148,320 |
| BYDUREON BCISE | 867,147 | 61,900 |
| BYETTA | 125,091 | 18,118 |

MOUNJARO, ZEPBOUND, WEGOVY, WEGOVY HD, LIRAGLUTIDE, EXENATIDE, SAXENDA, KERENDIA and the generic dapagliflozin products are not in the pull at all today.

**After the next full run:**

* **`OTHER_GLUCOSE_MGMT` treatment-category features (NB01, NB04)** keep the GLP-1 claims (option C below), as in 3.0, and gain the 7 GLP-1 products that are not in the pull today. Without option C they would have lost about 194.2M of today's 350.2M claims (55%).
* **New treatment-category features** `..._KERENDIA_...` (NB01 category pivots). They are not among the 268 selected features. There are no `GLP_1` treatment-category features (option C).
* **Brand `GLP-1` features** (`HCP_BRANDS`) gain the 7 GLP-1 products that are not in the pull today, Mounjaro first. Xultophy stays in the GLP-1 brand (treatment category Insulin).
* **Generic dapagliflozin** gets brand value `SGLT2`, like the other 10 SGLT2 products without a brand label (13.1M claims today). So it counts in the `SGLT2` and `SGLT2_WO_INVOKANA_300MG` features, not in `FARXIGA`.
* **Patient-journey based HCP features** that use the treatment categories (e.g. the 7 selected `..._WITH_GLP_1` features) now include all 13 GLP-1 products.
* **No double count of GLP-1 claims:** the PJ03 HCP-only rule only adds `Other- glucose mgmt` products that are not active in the mapping, so an active GLP-1 product appears once, as a journey row.

### GLP-1 column clash in NB01: decided option C (2026-11-05)

NB01 builds the treatment-category pivot and the brand pivot with the same prefix `TOTAL_RX_CLAIMS_` and joins them on NPI (cells 13-17 and 21). Today no treatment category equals a brand value. With the new mapping, `GLP-1` is both a treatment category and a brand value (`HCP_BRANDS`). Both pivots then make a column `TOTAL_RX_CLAIMS_GLP_1_IN_LAST_{N}_MONTH`, with different values: the brand count includes Xultophy, the category count does not. The same clash happens in the rejection, duration, payer, age and gender families, and in their `PCT_` and `RUNNING_` variants.

In a full run, NB01 would fail on the duplicate columns, or write two columns with the same name. Options:

| Option | What changes | Effect |
| --- | --- | --- |
| A. Rename the treatment category in the mapping, e.g. `GLP-1 RA` | Rx mapping file (13 rows) | Category columns become `..._GLP_1_RA_...`; brand `GLP-1` features keep their 3.0 meaning; patient-journey category names change too |
| B. NB01 adds a category prefix only when a category name equals a brand name | NB01 / `00_cohort_config` | Mapping unchanged; new category columns get a distinct name |
| C. NB01 counts treatment category `GLP-1` under `Other- glucose mgmt`, as in 3.0 | `00_cohort_config` helper, used by NB01 and NB04 | HCP Rx category features keep their 3.0 meaning (now with all 13 GLP-1 products); the patient journey still uses GLP-1 as its own category |

**Decision: option C.**

* `00_cohort_config` adds `HCP_RX_CATEGORY_MAP = {"GLP-1": "Other- glucose mgmt"}` and `hcp_rx_categories(df)`: the 3.0 cleanup (trailing spaces) plus this map.
* NB01 (cell "Load raw Rx claims" and the 3.0-history part of "Fixed pivot values") and NB04 (cell "Load all input tables") use it on their Rx input.
* NB01 "Fixed pivot values" now stops if any treatment category equals a brand value, so a future clash fails loudly instead of making duplicate columns.
* Not changed: brand `GLP-1` (incl. Xultophy), Kerendia's own category, and the patient journey (PJ03 tables and the patient-journey based HCP features such as `..._WITH_GLP_1`).
* NB05 is not affected: it reads the 3.0 table `kerendia_nba_3_0_Rx_05`, not the 3.1 Rx pull.

Test (cell "6. Option C test" in `Final Product Basket/00_product_mapping_update_2026_11_05`):
* Known values map as expected.
* On the full Rx pull, with the GLP-1 products relabelled `GLP-1` as PJ03 will write them, `hcp_rx_categories` gives exactly today's claim count per treatment category.
* There is no category vs brand clash with option C; without it, `GLP-1` clashes.
* NB01 and NB04 themselves run at the next full run, when the 3.1 Rx pull exists.

## 6. Checks done

* New files compared cell by cell with 2026_11_04: only the 17 planned rows differ.
* PJ03 and PJ05 basket checks pass with the new files. PJ05 reads `Kerendia_Px_Final_Product_Mapping_2026_11_05.csv`, and J0606 = DIALYSIS_DRUG / Y.
* The loader's format check accepts the 2026_11_05 files and rejects the 2026_11_04 Rx / Px / Dx / Lab files.
* HCP effects (section 5): measured on the full Rx pull with read-only queries (cells "5. HCP side effects" and "5b" in `Final Product Basket/00_product_mapping_update_2026_11_05`).
