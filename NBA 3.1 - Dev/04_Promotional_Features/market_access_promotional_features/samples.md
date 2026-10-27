# Samples Features — NBA 3.0 (Legacy)

**Group:** Market access promotional features (helping patients get started on and pay for Kerendia)  
**Notebook:** `17_promotional_features_samples` in `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**Saved table:** `kerendia_nba_3_hcp_model_samples_features_for_inference`  
**Built from:** a review of the notebook code  
**Date:** October 22, 2026

## What is this document about?

Bayer uses a model called **Next Best Action (NBA)** to suggest, for each doctor, which Kerendia promotional action is most useful next. Kerendia is a Bayer medicine for chronic kidney disease in people with type 2 diabetes (and, more recently, heart failure). The model needs each doctor's recent history, turned into numbers called **features** (one fact about a doctor written as a number).

This document explains the **Samples** features: free Kerendia samples each doctor received. Samples were previously documented with the non-personal features; they now belong to the market access group. It describes the **old version** of the pipeline (NBA 3.0); a "pipeline" is the chain of notebooks that runs one after another to prepare the data for the model.

**How it is organised:** the key ideas shared by the channels of this folder (time frame, dates table, doctor key, helper notebooks, how "last N months" is calculated) are in `00_introduction.md`. This file has: 1. In short, 2. Where the data comes from, 3. How the features are built step by step (*what*, *why*, *detail to know*), 4. The features explained, 5. What the final table looks like, 6. Things to watch out for. Codes such as LS-1 refer to the companion legacy file; each problem is also explained here.

**How to read names.** Anything written `like this` is the exact name used in the data or in the code. Its meaning is always given next to it.

**About the numbers.** Figures come from the last time the notebook was run (27 May 2026). They will be different at the next run.

---

## 1. In short

Doctors can receive **free Kerendia samples** to give to patients, so a patient can start treatment straight away. Samples reach the doctor in two ways:

* **Dropped**: a sales rep hands them over in person during a visit.
* **Shipped**: the doctor orders them and they are sent to the office.

This channel counts **how many sample units** each doctor received, of which product, and in which way. A doctor who receives (and especially who **asks for**) many samples is often starting new patients on Kerendia.

## 2. Where the data comes from

**Table:** `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER` in Snowflake, read with `Get_Data_Snowflakes`. It contains both dropped and shipped samples in one table.

**History of the source.** This table has been used since 19 December 2025. The notebook still contains, switched off (commented out), the older sources: `PHCDW.PHCDW_DSAA.VIEW_KERENDIA_SAMPLES_DROPPED_SHIPPED`; a version from 30 October 2025 that combined `ANALYTICS_V2.KERENDIA_SAMPLES` (dropped) with `ANALYTICS_V2.KERENDIA_SAMPLES_SHIPPED` (shipped, leaving out the Bayer product `KYLEENA BRC`, which is not Kerendia); and a test table (`..._TEST`).

**One line of the table** = one delivery of one product to one doctor.

**Columns used:**

| Column | What it means |
| --- | --- |
| `BHID` | The doctor's Bayer ID |
| `SMPLE_CALL_DT` | The date of the delivery. Used as the event day (the code also copies it into a column called `MONTH_ID`, even though it is a day, not a month). |
| `SMPLE_CALL_NM` | The identifier of the visit or order the delivery belongs to |
| `SMPLE_NM` | The product delivered (converted to capital letters). Values: see the table below. |
| `SMPLE_QTY` | How many units were delivered |
| `SAMPLE_FLAG` | `DROPPED` (handed over by a rep during a visit) or `SHIPPED` (ordered and sent to the office) |

**Which lines are kept:** all of them in the query (it uses `SELECT DISTINCT`, which keeps only one copy of identical lines). The lookback dates are applied later, in step 4.

**Size at the last run (27 May 2026):** 159,970 lines; the latest delivery date was 19 May 2026.

**Other inputs:** the HCP universe (`kerendia_nba_3_hcp_model_base_hcp_universe_for_inference`, the list of doctors the model is allowed to score) and the provider mapping table `kerendia_nba_3.SOURCE_PROVIDER_BHID_NPI_MAPPING`, used in step 8 to keep only target doctors.

Products in the data:

| Product name in the data | What it is |
| --- | --- |
| Kerendia 10mg BRC | 10 mg tablets (usual starting dose for kidney disease with diabetes) |
| Kerendia 20mg BRC | 20 mg tablets (usual ongoing dose) |
| Kerendia 40mg BRC | 40 mg tablets (newer dose, used for heart failure) |
| Kerendia Sampling Kit BRC | A sampling kit (supply, not medicine) |
| Kerendia Sample Housing Box BRC | A box for storing samples in the office (supply) |
| Kerendia Patient Brochures BRC | Leaflets for patients; **ignored** in all features |

("BRC" is just part of the product code in the sample system.)

## 3. How the features are built, step by step

**Step 1. Get the lookback dates** (cohort `I01`).

**Step 2. Read the deliveries** (query above).

**Step 3. Split the quantity into columns.**
*What:* the notebook creates one column per product, from a fixed (hard-coded) list of six names. Each column holds the quantity when the line is for that product, and 0 otherwise:

| Column | Product name it looks for |
| --- | --- |
| `SAMPLE_10MG` | `KERENDIA 10MG` (an old name, no longer in the data) |
| `SAMPLE_20MG` | `KERENDIA 20MG` (an old name, no longer in the data) |
| `SAMPLE_10MG_BRC` | `KERENDIA 10MG BRC` |
| `SAMPLE_20MG_BRC` | `KERENDIA 20MG BRC` |
| `SAMPLE_SAMPLING_KIT_BRC` | `KERENDIA SAMPLING KIT BRC` |
| `SAMPLE_SAMPLE_HOUSING_BOX_BRC` | `KERENDIA SAMPLE HOUSING BOX BRC` |

There is **no column for `KERENDIA 40MG BRC`** (LS-1). Then three more columns, all leaving out patient brochures:

* `OVERALL_SAMPLE`: the quantity of every line (all products, **including** 40 mg, kits and boxes).
* `SAMPLE_DROPPED`: the quantity when the line is `DROPPED`.
* `SAMPLE_SHIPPED`: the quantity when the line is `SHIPPED`.

**Step 4. Attach the dates and build the doctor key.**
*What:* cross join with the dates, keep deliveries inside the lookback, remove rows without a BHID, create `HCP_COHORT_ID`.

**Step 5. Add up per doctor and day.**
*What:* add up each of the 9 columns for each doctor and day. The totals get `TOTAL_` in front (e.g. `TOTAL_SAMPLE_SHIPPED`).

**Step 6. Fill in the calendar and add up the periods.**
*What:* `step2_fill_missing_date`, empty days become 0, then `step3_lag_date` for 30, 60, 90, 120, 150 and 180 days (see the introduction file, section 0.3).

**Step 7. Keep the last day only and tidy up.**
*What:* keep the row for `LOOKBACK_END_DATE`, remove the daily totals, rename the day column `SVC_DT`, put the BHID in its own column `BHID`.

**Step 8. Keep only target doctors.**
*What:* read the HCP universe (its doctor column is `PROVIDER_ID`), translate it to BHID with `SOURCE_PROVIDER_BHID_NPI_MAPPING`, attach the cohort and build `HCP_COHORT_ID`. Then an **inner join** with the features (LS-4): only doctors that are both in the universe **and** received samples remain. A check then counts empty values per column.
*Why:* the model only scores doctors in the universe.

**Step 9. Save.**
*What:* add `PULL_DT` (text) and overwrite `kerendia_nba_3_hcp_model_samples_features_for_inference`.

## 4. The features explained

All values are **numbers of units** (for example, packs), not numbers of deliveries. There are 9 measures, each for 6 periods (`_IN_LAST_1_MONTH` to `_IN_LAST_6_MONTH`) = **54 features**.

| Feature (+ period ending) | What it counts | How to interpret it |
| --- | --- | --- |
| `TOTAL_OVERALL_SAMPLE` | All sample units and supplies received (brochures excluded; includes 40 mg) | Overall sampling activity with this doctor |
| `TOTAL_SAMPLE_10MG_BRC` | 10 mg units | Samples for starting patients |
| `TOTAL_SAMPLE_20MG_BRC` | 20 mg units | Samples for patients continuing treatment |
| `TOTAL_SAMPLE_SAMPLING_KIT_BRC` | Sampling kits | Supplies to run sampling in the office |
| `TOTAL_SAMPLE_SAMPLE_HOUSING_BOX_BRC` | Storage boxes | Office set up to keep samples |
| `TOTAL_SAMPLE_DROPPED` | Units handed over by reps | Sampling driven by rep visits |
| `TOTAL_SAMPLE_SHIPPED` | Units the doctor ordered and had shipped | The doctor actively asked for samples: a strong interest signal |
| `TOTAL_SAMPLE_10MG` | Units with the old name "Kerendia 10mg" (without BRC) | This name no longer appears in the data, so always 0 |
| `TOTAL_SAMPLE_20MG` | Units with the old name "Kerendia 20mg" (without BRC) | Always 0, same reason |

Useful rule: **dropped + shipped = overall.**

**Example.** In the last 90 days, a rep gave Dr. Garcia 10 units of 20 mg, and she ordered 6 units of 10 mg by mail. Her features for `_IN_LAST_3_MONTH`: overall = 16, 20 mg = 10, 10 mg = 6, dropped = 10, shipped = 6.

## 5. What the final table looks like

One row per doctor:

| Column | Meaning |
| --- | --- |
| `HCP_COHORT_ID` | The doctor (Bayer ID + `_I01`) |
| `SVC_DT` | The end of the lookback (the "as of" date) |
| `LOOKBACK_END_DATE` | Same date, kept again |
| 54 features | Above |
| `BHID` | The doctor's Bayer ID |
| `PULL_DT` | Date the notebook was run |

## 6. Things to watch out for

* **No separate 40 mg feature** (LS-1). The fixed product list in step 3 has no 40 mg column, so 40 mg samples are only counted inside overall, dropped and shipped. With heart failure now a Kerendia use, this hides a potentially important signal.
* **Two features are always 0.** `TOTAL_SAMPLE_10MG` and `TOTAL_SAMPLE_20MG` look for old product names without "BRC", which no longer appear in the data.
* **Fixed product list.** Any new product name (for example a new kit) is counted only in overall / dropped / shipped, never in its own column.
* **Only doctors in the target list are kept** (LS-4). The inner join removes doctors outside the HCP universe, even if they received samples; and doctors in the universe without samples are not added (they are treated as 0 later).
* **Identical lines are merged.** `SELECT DISTINCT` keeps one copy of identical lines, so two genuinely separate deliveries with exactly the same doctor, date, visit, product, quantity and type would count once.
