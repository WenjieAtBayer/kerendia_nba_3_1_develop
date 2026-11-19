# Kerendia NBA 3.1 - V7 Mapping Decisions (2026-11-17)

This document explains two new mapping files built for the switch from `kerendia_laad_based_lrx_v6` to `kerendia_laad_based_lrx_v7` in the HCP Rx feature notebooks (26 NBRx, 27 NRx, 28 TRx).

| File | Purpose | Rows |
| --- | --- | --- |
| `Kerendia_V7_Switch_AddOn_Mapping_2026_11_17.csv` | Re-labels V6-style `SWITCH_FROM` / `ADD_ON_TO` values to V7 `PRODUCT_GROUP` names | 73 |
| `Kerendia_V7_Product_Group_Priority_2026_11_17.csv` | V7 product-group priorities and the resulting action (keep / prune / drop) | 67 |

Status: applied in notebooks 26/27/28 on 2026-11-17 (output folder `hcp_features_v7_cohort_aligned/`).

## Inputs

* `Kerendia_Market_Basket_Product_Group_Mapping_V7.csv`: product-level mapping with `PRODUCT_NAME`, `PRODUCT_GROUP_V6`, `V7_PRODUCT_CLASS`, `V7_PRODUCT_GROUP`, `ADDED_IN_V7` and `TRX_OCT2024_SEP2026` (TRx volume used for tie-breaks).
* `Kerendia_Market_Basket_Product_Group_Mapping_and_Priority_v4.csv`: v4 product priorities (`PRIORITY` 1-6) and `PROPOSED_ACTION`.
* `kerendia_laad_based_lrx_v7`, restricted to the HCP universe (`HCP_Universe_without_call_hcps`): distinct `SWITCH_FROM` / `ADD_ON_TO` values and their NBRx volumes.

## Part 1 - SWITCH_FROM / ADD_ON_TO alignment

### Problem

In V7, `PRODUCT_GROUP` uses new names (e.g. `ACE`, `SPIRONOLACTONE`, `ENTRESTO BRAND`), but `SWITCH_FROM` and `ADD_ON_TO` still carry V6-style names (e.g. `ACE INHIBITORS AND COMBOS`, `MINERALOCORTICOID RECEPTOR ANTAGONISTS`, `ENTRESTO`). The switch and add-on features therefore did not line up with the product-group features.

### Method

Every V6-style value was looked up as `PRODUCT_GROUP_V6` in the V7 product mapping, which gives the V7 group(s) its products now belong to. All 73 values found a match. Each value was assigned with the first rule that applies:

| Rule | When it applies | Decision | Values |
| --- | --- | --- | --- |
| R1 | All products map to one V7 group | Use that V7 group | 58 |
| R2 | One V7 group holds at least 80% of the V6 group's TRx (or the targets have no TRx and one target has the same name) | Use the dominant V7 group | 10 |
| R3 | Below 80%, but all targets are the same brand family or molecule | Use the largest V7 group | 3 |
| R4 | No V7 group is a fair label | Keep a combined label | 2 |

Result: the 73 V6-style values collapse to 46 aligned values.

The switch/add-on data only records a group name, not the product, so a V6 group that splits into several V7 groups cannot be divided exactly. Rules R2-R4 choose the least misleading single label.

### Decisions that are not one-to-one

| V6 value | Aligned value | Rule | Why |
| --- | --- | --- | --- |
| `MINERALOCORTICOID RECEPTOR ANTAGONISTS` | `SPIRONOLACTONE` | R2 | Spironolactone 97% of TRx; eplerenone 3% |
| `DAPAGLIFLOZIN_FARXIGA COMBOS` | `XIGDUO XR` | R2 | Xigduo XR 82%; dapagliflozin/metformin generic 18% |
| `DIURETICS AND COMBOS` | `DIURETICS` | R2 | Diuretics 99.6%; spironolactone combos under 0.5% |
| `OTHERS` | `OTHERS` | R2 | Others 97%; Glyxambi 2% |
| `BYETTA` | `BYETTA` | R2 | Byetta 83%; generic exenatide 17% |
| `BYDUREON` | `BYDUREON BCISE` | R2 | Bcise holds about 100% |
| `BRENZAVVY`, `WEGOVY`, `TEKTURNA` | same name | R2 | Each holds 99-100% |
| `ADLYXIN` | `ADLYXIN` | R2 | No TRx in either target; kept the same-name group |
| `CANAGLIFLOZIN_INVOKANA COMBOS` | `INVOKAMET` | R3 | Invokamet 55%, Invokamet XR 45%; same brand family |
| `VICTOZA` | `LIRAGLUTIDE` | R3 | Generic liraglutide 70%, Victoza 30%; same molecule |
| `SYMLINPEN` | `SYMLINPEN 60` | R3 | 60 pen 68%, 120 pen 32%; same product |
| `ENTRESTO` | `ENTRESTO` (combined) | R4 | Brand 52% vs generic 48%; brand vs generic matters commercially, so neither label is used |
| `EMPAGLIFLOZIN_JARDIANCE COMBOS` | `EMPAGLIFLOZIN_JARDIANCE COMBOS` (kept) | R4 | Synjardy XR 58%, Synjardy 28%, Trijardy XR 14%; different brands, no fair single label |

`ENTRESTO` and `EMPAGLIFLOZIN_JARDIANCE COMBOS` are the only two aligned values that are not V7 `PRODUCT_GROUP` names (`IN_V7_PRODUCT_GROUP = False`).

### Notable one-to-one renames (R1)

* `ACE INHIBITORS AND COMBOS` -> `ACE`; `ANGIOTENSIN II RECEPTOR ANTAGONISTS AND COMBOS` -> `ARB`; `BETA BLOCKERS AND COMBOS` -> `BB`; `CALCIUM CHANNEL BLOCKERS AND COMBOS` -> `CCB`
* DPP4 brands (`JANUVIA`, `TRADJENTA`, `ONGLYZA`, `NESINA`, `ZITUVIO`, ...) -> `DPP4`
* `GLIMEPIRIDE`, `GLIPIZIDE`, `GLYBURIDE` and their combos -> `SULFONYLUREAS`
* Phosphate binders, iron, ESAs, vitamin D analogs -> `CKD SUPPORTIVE`
* Older oral agents (`ACARBOSE`, `ACTOS`, `CYCLOSET`, `MIGLITOL`, `PRANDIN`, `STARLIX`, ...) -> `OTHERS`
* `FARXIGA GENERICS` -> `FARXIGA GENERIC`; `ERTUGLIFLOZIN_STEGLATRO COMBOS` -> `STEGLUJAN`; `SOLIQUA` -> `SOLIQUA 100/33`; `XULTOPHY` -> `XULTOPHY 100/3.6`

## Part 2 - V7 priorities and pruning

### Why a new priority table was needed

The v4 pruning rule is: product groups with priority above 4 keep only their 1 and 12-month windows (3-month, 6-month and running-total columns are dropped). The v4 file is keyed on V6 group names, so with V7 data it would have matched only the names shared by both versions, and pruning was turned off.

### Method

1. Join v4 to the V7 mapping on `PRODUCT_NAME`. A V7 group's priority is the **lowest (most important) priority** among its products. Used for most groups.
2. If none of a V7 group's products appear in v4, use the lowest v4 priority of its `PRODUCT_GROUP_V6` group(s).
3. If neither exists, decide manually (only `BAXFENDY`).

`SOURCE` in the CSV records which step was used for each group.

Taking the lowest priority means a group that contains any important product keeps its full windows.

### Decisions

* **BAXFENDY:** new in V7 with no v4 history. Assigned priority 3 so a new launch keeps its full 1/3/6/12-month windows.
* **VERQUVO and CCB (user decision, 2026-11-17):** v4 gives both priority 5. Overridden to priority 4 so they keep all windows.
* **BASAL INSULIN (user decision, 2026-11-17):** left at its derived priority 2 (not pruned).
* **Dropped groups:** `BEXAGLIFLOZIN`, `TEKTURNA` and `TEKTURNA HCT` stay dropped (current `DROP_GROUPS`), regardless of priority.
* **v4 priorities are otherwise used as-is.**

### Result (67 V7 groups)

| Action | Groups |
| --- | --- |
| `KEEP_ALL_WINDOWS` (priority 1-4) | 56 |
| `PRUNE_3M_6M_RT` (priority 5-6) | 8 |
| `DROP` | 3 |

Pruned groups: `BB`, `CGM`, `METFORMIN`, `OTHER INSULIN`, `SULFONYLUREAS`, `SYMLINPEN 120`, `SYMLINPEN 60`, `ZEPBOUND`.

### Differences from the V6 pruning

The V6 run pruned 16 groups.

* **VERQUVO** was pruned in V6; now kept with all windows (user decision).
* **CCB** keeps all windows (user decision), as in V6.
* **ZEPBOUND** (priority 6) is pruned, as in V6.
* **BASAL INSULIN** is no longer pruned (V6 pruned `BASAL_LONG_ACTING_INSULIN`); the V7 group includes products with v4 priority 2. Kept as-is (user decision).
* Alogliptin combos were pruned in V6; they are now part of `DPP4` (priority 2, not pruned).

## Expected effect on the Rx feature tables

* Product-group window features: 64 kept groups x 4 windows (1/3/6/12 months) - 8 pruned groups x 2 windows = **240 columns** (was 256 without pruning). Confirmed in the full run 529898138891459.
* Running-total pruning fixed 2026-11-17 (run 137443284097619): running totals are named `RUNNING_TOTAL_HCP_<METRIC>_CLAIMS_<value>`, but the NBA 3.0 code looked for a `_RUNNING_TOTAL` suffix, so they were never dropped (V6 kept them for all 16 of its pruned groups). The code now builds `RUNNING_{col_base}`; exactly the 8 pruned groups' running totals are removed, and all other values are unchanged.
* `SWITCH_FROM` / `ADD_ON_TO`: up to 46 aligned values each (74 / 72 raw values in V7). The 200-HCP test produced 45 values each, all from the aligned set.
* Full run: 993 columns per Rx table (792 window + 194 running-total + 7 keys), vs 1,266 in the V6 output.

## Why some features differ from V6 (investigated 2026-11-17)

Raw V6 vs V7 tables, HCP universe, Sep 2025 - Aug 2026.

* **INDICATION_GROUP:** V6 had 16 groups, including 8 CVD combinations (e.g. `T2D + CVD` 19.5% of NBRx, `CVD` 15.7%) and `ALL_OTHERS` (26.7%). V7 has 8 groups with no CVD dimension, and `OTHERS` (32.7%). Total NBRx is nearly unchanged (48.7M vs 47.8M), so this is a regrouping, which is why e.g. `T2D + CKD + HF` grew from 4.8K to 3.0M NBRx. Even after folding V6's CVD groups into their non-CVD equivalents, V7 puts more NBRx in the CKD-containing groups (e.g. `T2D + CKD` 3.5M -> 6.1M), which points to different indication evidence in V7. Not confirmed at claim level (the tables share no claim key).
* **ADD_ON_TO ENTRESTO (+862% NBRx):** V6 `ENTRESTO` was brand only (54K NBRx). V7 adds `ENTRESTO GENERIC` (451K NBRx; `ADDED_IN_V7 = True`). Add-on-to ENTRESTO grew 9.6x, in line with the Entresto market's 9.2x.
* **SWITCH_FROM ENTRESTO (-42% TRx, -6% NBRx):** likely the same cause (unconfirmed): patients who moved from brand to generic Entresto now stay on a basket product, so later starts count as add-on rather than switch.

## INDICATION_GROUP_APP1 switch (user decision, 2026-11-17)

* Notebooks 26/27/28 read `INDICATION_GROUP_APP1 AS INDICATION_GROUP` (16 values incl. 8 T1D groups, no merging). Rx tables now have 1,033 columns.
* Side effect accepted by the user: `SELECT DISTINCT` now de-duplicates on APP1, which keeps ~0.01% more rows (200-HCP test: +71 NBRx, +395 NRx, +1,106 TRx), so all feature families shift very slightly vs the INDICATION_GROUP version.
* Full run 976066249765064: 8,252,356 rows per table; 12-month NBRx and NRx for every APP1 group (cohort c28) match the raw V7 table exactly.

## Notebook changes (applied 2026-11-17)

In notebooks 26, 27 and 28:

1. Load `Kerendia_V7_Switch_AddOn_Mapping_2026_11_17.csv` and replace `SWITCH_FROM` and `ADD_ON_TO` with `V7_ALIGNED_VALUE` before pivoting. Unmapped values are kept unchanged.
2. Load `Kerendia_V7_Product_Group_Priority_2026_11_17.csv` as the priority map, iterate over V7 groups instead of v4 names, and turn `APPLY_V4_PRIORITY_PRUNING` back on.
3. Rerun the 200-HCP test, then the full universe.
