# DTC Direct Buy + Social Features — NBA 3.0 (Legacy)

**Group:** Non-personal promotional features (promotion that does not involve a sales rep)  
**Notebook:** `34_promotional_features_DTC` in `/Workspace/Users/wenjie.chen@bayer.com/kerendia_nba_3_0_develop/NBA 3.0 Ops - Pipeline/03_Feature_Engineering/03_HCP_Level_Features/`  
**Saved table:** `kerendia_nba_3_hcp_model_DTC_PROMOTION_for_inference`  
**Built from:** a review of the notebook code  
**Date:** October 22, 2026

## What is this document about?

Bayer uses a model called **Next Best Action (NBA)** to suggest, for each doctor, which Kerendia promotional action is most useful next. Kerendia is a Bayer medicine for chronic kidney disease in people with type 2 diabetes (and, more recently, heart failure). The model needs each doctor's recent history and situation, turned into numbers called **features** (one fact written as a number).

This document explains the **DTC** features: Kerendia ads shown to the public in each doctor's area. It describes the **old version** of the pipeline (NBA 3.0); a "pipeline" is the chain of notebooks that runs one after another to prepare the data for the model.

**How it is organised:** the key ideas shared by the channels of this folder (time frame, helper notebooks, how the notebooks differ) are in `00_introduction.md`. This file has: 1. In short, 2. Where the data comes from, 3. How the features are built step by step (*what*, *why*, *detail to know*), 4. The features explained, 5. What the final table looks like, 6. Things to watch out for. Codes such as LT-1 refer to the companion legacy file; each problem is also explained here.

**How to read names.** Anything written `like this` is the exact name used in the data or in the code. Its meaning is always given next to it.

**About the numbers.** Figures come from the last time the notebook was run (31 July 2026). They will be different at the next run.

---

## 1. In short

"DTC" means **Direct-to-Consumer**: Kerendia ads shown to the **public (patients)**, not to doctors. Examples are ads on health websites such as WebMD, or on Facebook and Instagram.

These ads are not targeted at a particular doctor, so the data is not per doctor. It is per **region**: the US is divided into about 210 media regions (called "DMAs", Designated Market Areas; roughly one per large city and its surroundings). Each doctor gets the numbers of the region where they work.

The idea: if many patients around a doctor saw Kerendia ads, more of them may ask that doctor about Kerendia. It describes the doctor's **surroundings**. It is not an action that can be taken with the doctor.

## 2. Where the data comes from

Unlike the other channels, this notebook does **not** read Snowflake. It reads tables that were prepared and saved earlier by other notebooks (as Delta tables). If those tables are not refreshed, this notebook produces the same numbers again.

**The input tables:**

| Table (saved path) | What it contains | Used? |
| --- | --- | --- |
| `ops_pipeline/query_output/kerendia_nba_3_0_hcp_model_DirectBuys` | **Direct buys**: ads bought directly from health websites. Vendors: Health Union, Healthline, Sharecare, WebMD. | Yes |
| `ops_pipeline/query_output/kerendia_nba_3_0_hcp_model_social` | **Social media**: Facebook and Instagram together. Vendor: `FB+IG`. | Yes |
| `ops_pipeline/notebook_output/DTC/Pulsepoint` | PulsePoint programmatic display ads (ads placed automatically across many websites) | Loaded and prepared, but **never added** to the result (LT-1) |
| `ops_pipeline/notebook_output/DTC/TTD Display` | The Trade Desk display ads (another automatic ad-placement platform) | Loaded and prepared, but **never added** (LT-1) |

**One line of each input** = one region, one month, one vendor.

**Columns used:**

| Column | What it means |
| --- | --- |
| `DMA_Code` | The region (DMA number, e.g. `500`) |
| `MONTH` | The month (its first day, e.g. 2023-02-01) |
| `VENDOR` | The website or platform that showed the ad |
| `IMPRESSIONS` | How many times the ad was shown to people in that region that month |
| `CLICKS` | How many times people clicked the ad |

No lines are removed and there is no date filter: the data starts in January 2023 and goes up to whatever the input tables contain.

## 3. How the features are built, step by step

**Step 1. Load the input tables** (all four).

**Step 2. For each input separately: add up and pivot.**
*What:* group by region and month, turn each vendor into its own columns (a **pivot**), and add up impressions (`TOTAL_IMPRESSIONS`) and clicks (`TOTAL_CLICKS`). Empty cells are filled with 0. `MONTH` is renamed `DATA_MONTH`.
*Why:* one row per region and month, with one number per vendor.

**Step 3. Clean the column names.**
*What:* every feature column gets the prefix `DTC_PROMOTION_`; symbols and spaces are replaced (`+` becomes "and", spaces and `-` become `_`, brackets and `&` are removed) and everything is in capital letters. So vendor "Health Union" becomes `DTC_PROMOTION_HEALTH_UNION_TOTAL_IMPRESSIONS`, and "FB+IG" becomes `DTC_PROMOTION_FB_AND_IG_TOTAL_IMPRESSIONS`.

**Step 4. Combine direct buys and social media.**
*What:* a **full outer join** on region + month: every region-month that appears in either table is kept.
*Detail to know:* the 0-filling happened in step 2, **before** this join. So when a region-month exists in only one table, the columns of the other table are empty (NULL), not 0 (LT-2).

**Step 5. Save.**
*What:* add `PULL_DT` (text) and overwrite `kerendia_nba_3_hcp_model_DTC_PROMOTION_for_inference`. All months are kept; there is no lookback period here. Last run: 31 July 2026.

**Step 6. Check.** The last cell checks that 9 feature names expected by the model exist in the table (all but `DTC_PROMOTION_HEALTHLINE_TOTAL_CLICKS`). All 9 were found.

## 4. The features explained

**10 features**, each for **one region in one month** (no "last N months" totals):

| Feature | What it means |
| --- | --- |
| `DTC_PROMOTION_HEALTH_UNION_TOTAL_IMPRESSIONS` | Times a Kerendia ad was shown to people in the region on Health Union websites that month |
| `DTC_PROMOTION_HEALTH_UNION_TOTAL_CLICKS` | Times people in the region clicked those ads |
| `DTC_PROMOTION_HEALTHLINE_TOTAL_IMPRESSIONS` | Ads shown on Healthline |
| `DTC_PROMOTION_HEALTHLINE_TOTAL_CLICKS` | Clicks on Healthline ads |
| `DTC_PROMOTION_SHARECARE_TOTAL_IMPRESSIONS` | Ads shown on Sharecare |
| `DTC_PROMOTION_SHARECARE_TOTAL_CLICKS` | Clicks on Sharecare ads |
| `DTC_PROMOTION_WEBMD_TOTAL_IMPRESSIONS` | Ads shown on WebMD |
| `DTC_PROMOTION_WEBMD_TOTAL_CLICKS` | Clicks on WebMD ads |
| `DTC_PROMOTION_FB_AND_IG_TOTAL_IMPRESSIONS` | Ads shown on Facebook and Instagram |
| `DTC_PROMOTION_FB_AND_IG_TOTAL_CLICKS` | Clicks on Facebook and Instagram ads |

Impressions = how much patients were **exposed** to Kerendia ads; clicks = how many **responded**. Direct-buy values are stored as decimal numbers (e.g. `6180.0`), social-media values as whole numbers (e.g. `25855`); the meaning is the same.

**Example.** Region 500, February 2023: WebMD showed the ad 6,180 times and got 5 clicks; Facebook/Instagram showed it 25,855 times and got 51 clicks. Every doctor working in region 500 gets these numbers for that month.

## 5. What the final table looks like

One row per region per month:

| Column | Meaning |
| --- | --- |
| `DMA_Code` | The region |
| `DATA_MONTH` | The month (its first day) |
| 10 features | Above |
| `PULL_DT` | Date the notebook was run |

Linking regions to doctors is not done in this notebook; it happens in a later step.

## 6. Things to watch out for

* **Empty values instead of 0** (LT-2). If a region-month has direct-buy ads but no social ads (or the opposite), the missing side is empty (NULL), not 0, because the 0-filling happens before the two tables are combined. Example: region 500, January 2023 has direct-buy numbers but empty Facebook/Instagram columns. A later step must decide whether empty means "no ads" (0) or "unknown".
* **Two prepared sources are never used** (LT-1). PulsePoint and The Trade Desk are loaded and prepared (steps 1 to 3) but not included in the join of step 4, so their ads are not in any feature.
* **The data is only as recent as the prepared tables.** The notebook does not fetch new data; if the input tables are not refreshed, the features stay the same.
* **Pivot columns depend on the data.** A new vendor in an input table would add new columns; a vendor that disappears would remove them.
* **These are not doctor actions.** They describe the doctor's area. They should be treated as background information, not as something the model can recommend.
* **Linking to doctors happens later.** Each doctor's region (DMA) must be looked up in a later step; that link is not part of this notebook.
