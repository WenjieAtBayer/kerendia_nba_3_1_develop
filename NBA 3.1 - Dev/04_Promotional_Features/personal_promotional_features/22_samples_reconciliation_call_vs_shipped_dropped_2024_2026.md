# Samples Reconciliation: Call-Level Samples vs Shipped / Dropped Table (Nov 2024 – Oct 2026)

**Group:** Personal promotional features (validation step V5 of `40_field_activity_nba_3_1_readiness_plan.md`)  
**Purpose:** check whether call-level samples (`FACT_CALL_SAMPLE`) agree with the samples table used by the market access block, and whether sample strength (10 / 20 / 40 mg) is reliable enough to use  
**Built from:** direct queries of Snowflake `CPH_DB_PROD.MODEL_V2.FACT_CALL_SAMPLE`, `MAP_CUSTOMER_XREF`, `FACT_CALL`, `FACT_CALL_KEY_MESSAGE` and `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER`  
**Date:** October 30, 2026 (data to 23 Oct 2026)

**About the numbers.** Kerendia sample products only (`Kerendia 10mg / 20mg / 40mg BRC`; brochures, boxes and kits excluded). `FACT_CALL_SAMPLE` rows with `SYS_DELETE_FLAG = '0'`; doctor ID (BHID) from `MAP_CUSTOMER_XREF` (99.99% mapped). The market access table is read with `SELECT DISTINCT`, as in `17_promotional_features_samples`. "Year 1" = Nov 2024 – Oct 2025, "Year 2" = Nov 2025 – Oct 2026. My own queries; not checked by the samples or CRM teams.

**Business rule (Source: Wenjie Chen, previously aligned with MV).** Only `Delivered` and `AOC Received` count as samples **received** by the HCP. `Shipped` is not received: a small share of shipments is recalled to the CareTria warehouse (office refuses delivery, wrong address given by the Sales Consultant, or lost by FedEx and reported to the FDA as lost in transit). The data comes from CareTria as 12-month rolling data, updated weekly, so an order still `Shipped` at month end is counted only in the month it reaches `Delivered` or `AOC Received`.

## 1. In short

* **The two sources are not independent.** Every line of the market access table (56,507 `DROPPED` and 1,047 `SHIPPED` lines in the period) is found in `FACT_CALL_SAMPLE` with the same sample record (`SMPLE_CALL_NM` = `CALL_SMPL_NM`), product, doctor, date and quantity (100% match). The market access table is a **status-filtered copy** of `FACT_CALL_SAMPLE`: `DROPPED` = status `DELIVERED` or `Delivered_vod`, `SHIPPED` = `Shipped_vod`.
* **Since the Vault CRM change (late July 2025) the market access table misses most samples.** The status `DELIVERED` stops on 23 July 2025. From July 2025 almost all completed sample lines have the new status `aoc_received__c` (acknowledgement of content received), which the market access table does not keep.
* **Effect:** against the business rule (received = `Delivered` + `AOC Received`), in Year 2 the market access table holds only **13% of received units** (59K of 449K) and **23% of doctors who received samples** (4.6K of 20.3K). In Year 1 it held 87% of units and 90% of doctors. So the samples features of NBA 3.0 (and of NBA 3.1 if unchanged) collapse from August 2025 for a data reason, not a field reason.
* **The market access table also counts samples that are not yet received.** Its `SHIPPED` flag (`Shipped_vod`) is in transit by the business rule: 6.7K of its 65K Year 2 units (10%), almost all ordered in the last two weeks of the data.
* **`aoc_received__c` is a real delivery** (business rule), and the data agrees: the lines sit on submitted doctor calls (100%), with the same CKD / HF profile as the lines the market access table keeps (section 4).
* **Orders settle in about two to three weeks.** Orders more than three weeks old are 95 – 98% received and 1 – 4% failed (rejected, returned, cancelled, lost); the last week of data is only 14% received (section 5.1). There is no delivery-date column, so the month of receipt must be handled through the data cut (section 6, R7).
* **Strength is reliable and carries information.** The 10 / 20 mg mix is stable (about 61% / 37% of units every quarter). 40 mg exists since August 2025 (1.3 – 2.7% of units, about 380 – 990 doctors a quarter, 2,366 doctors in Year 2) and is clearly HF-related: 58 – 62% of 40 mg sample calls carry an HF key message vs 25 – 32% for 10 / 20 mg.

## 2. Line-level match (market access table found in `FACT_CALL_SAMPLE`)

| Market access flag | Lines (Nov 2024 – 23 Oct 2026) | Found in `FACT_CALL_SAMPLE` | Same doctor | Same quantity | Same date | `FACT_CALL_SAMPLE` status |
| --- | --- | --- | --- | --- | --- | --- |
| `DROPPED` | 56,507 | 100% | 100% | 100% | 100% | `DELIVERED`, `Delivered_vod` |
| `SHIPPED` | 1,047 | 100% | 100% | 100% | 100% | `Shipped_vod` |

No duplicates (one line per sample record and product); no organisation (`BHO`) IDs in either source.

## 3. Status of the call-level sample lines

**Monthly lines in `FACT_CALL_SAMPLE` by status (main statuses):**

| Month | `DELIVERED` | `Delivered_vod` | `aoc_received__c` | `Shipped_vod` | `In_Progress_vod` / `on_hold__c` | `rejected__c` | Market access table lines |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Nov 2024 | 5,629 | 0 | 9 | 14 | 0 | 86 | 5,643 |
| Feb 2025 | 6,651 | 0 | 3 | 0 | 0 | 103 | 6,651 |
| May 2025 | 5,430 | 0 | 1 | 0 | 0 | 96 | 5,430 |
| Jun 2025 | 4,971 | 1 | 14 | 0 | 0 | 75 | 4,972 |
| Jul 2025 | 3,093 | 60 | 1,203 | 0 | 0 | 117 | 3,153 |
| Aug 2025 | 0 | 156 | 2,982 | 0 | 9 | 176 | 156 |
| Oct 2025 | 0 | 87 | 2,218 | 0 | 1 | 98 | 87 |
| Jan 2026 | 0 | 70 | 3,080 | 0 | 3 | 122 | 70 |
| Apr 2026 | 0 | 276 | 7,220 | 0 | 3 | 147 | 276 |
| Jun 2026 | 0 | 588 | 8,085 | 0 | 0 | 172 | 586 |
| Aug 2026 | 0 | 1,030 | 7,185 | 2 | 25 | 205 | 1,032 |
| Sep 2026 | 0 | 2,254 | 5,727 | 23 | 174 | 97 | 2,277 |
| Oct 2026 (to 23rd) | 0 | 2,635 | 1,530 | 1,008 | 738 | 22 | 3,643 |

**Before and after 28 July 2025** (the same date call length became `30` on 97% of calls):

| Period | Delivered (`DELIVERED` / `Delivered_vod`) | `aoc_received__c` | `Shipped_vod` | Other (rejected, returned, cancelled, lost, in progress, on hold) |
| --- | --- | --- | --- | --- |
| Nov 2024 – 27 Jul 2025 | 47,765 lines / 367K units | 1,237 / 10K | 14 / 0.1K | 1,331 / 11K |
| 28 Jul 2025 – 23 Oct 2026 | 8,738 / 60K | 63,927 / 437K | 1,033 / 7K | 3,393 / 25K |

The last two months show another shift: `Delivered_vod` and `Shipped_vod` rise and `aoc_received__c` falls. Section 5.1 shows this is mostly timing: recent orders are still `Shipped_vod`, `In_Progress_vod` or `on_hold__c` and become `Delivered` / `AOC Received` within two to three weeks.

## 4. Doctor x month x strength comparison

Two definitions:

* **A (market access table)** = `DELIVERED`, `Delivered_vod`, `Shipped_vod`.
* **R (received, business rule)** = `DELIVERED`, `Delivered_vod`, `aoc_received__c`. `Shipped_vod` (in transit), in progress, on hold, rejected, returned, cancelled and lost in transit are not received.

| | Year 1 | Year 2 |
| --- | --- | --- |
| Doctor-month-strength cells with received samples (R) | 52,159 | 61,406 |
| Cells identical in A | 84.9% | 13.1% |
| Received units (R) | 425,450 | 449,246 |
| Received units also in A | 369,271 (86.8%) | 58,660 (13.1%) |
| Units in A that are not received (`Shipped_vod`) | 104 | 6,652 |
| Doctors who received samples (R) | 16,793 | 20,270 |
| Of whom also in A | 15,058 (89.7%) | 4,569 (22.5%) |

By strength (R, and share also in A):

| Year | Strength | Received units | Also in A | Doctors | Also in A |
| --- | --- | --- | --- | --- | --- |
| Year 1 | 10 mg | 268,457 | 87.9% | 16,182 | 14,531 |
| Year 1 | 20 mg | 154,901 | 86.0% | 13,118 | 11,496 |
| Year 1 | 40 mg | 2,092 | 7.5% | 710 | 48 |
| Year 2 | 10 mg | 275,038 | 13.1% | 19,379 | 4,278 |
| Year 2 | 20 mg | 167,751 | 12.9% | 15,817 | 3,303 |
| Year 2 | 40 mg | 6,457 | 15.6% | 2,366 | 511 |

**Are `aoc_received__c` lines real deliveries?** Year 2 sample lines joined to their call and key messages:

| Group | Strength | Lines | On a submitted call | HF key message | CKD key message |
| --- | --- | --- | --- | --- | --- |
| `aoc_received__c` | 10 mg | 30,755 | 100% | 30.1% | 82.9% |
| `aoc_received__c` | 20 mg | 23,491 | 100% | 31.5% | 82.7% |
| `aoc_received__c` | 40 mg | 2,856 | 100% | 59.6% | 64.5% |
| In market access table | 10 mg | 5,030 | 100% | 30.4% | 77.9% |
| In market access table | 20 mg | 3,872 | 100% | 32.0% | 77.0% |
| In market access table | 40 mg | 571 | 100% | 61.6% | 56.4% |

The two groups behave the same, consistent with the business rule that `aoc_received__c` is a received sample.

## 5. Dosage-specific volume (received, definition R)

| Quarter | Units | 10 mg | 20 mg | 40 mg | Doctors 10 mg | Doctors 20 mg | Doctors 40 mg |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Q4 2024 (Nov – Dec) | 77,194 | 64.6% | 35.4% | 0% | 4,933 | 3,542 | 0 |
| Q1 2025 | 142,206 | 63.9% | 36.1% | 0% | 7,707 | 5,804 | 0 |
| Q2 2025 | 125,175 | 64.1% | 35.9% | 0% | 6,891 | 5,139 | 0 |
| Q3 2025 | 65,234 | 58.5% | 38.8% | 2.7% | 4,103 | 3,404 | 547 |
| Q4 2025 | 37,386 | 60.4% | 37.5% | 2.0% | 2,509 | 1,996 | 379 |
| Q1 2026 | 69,258 | 61.9% | 36.5% | 1.6% | 4,400 | 3,410 | 526 |
| Q2 2026 | 161,967 | 61.0% | 37.6% | 1.4% | 9,562 | 7,599 | 985 |
| Q3 2026 | 167,583 | 61.2% | 37.4% | 1.4% | 10,149 | 7,928 | 990 |
| Oct 2026 (to 23rd, not settled) | 28,693 | 61.2% | 37.5% | 1.3% | 2,190 | 1,673 | 186 |

Reading:

* **Total volume** is the main signal; it dipped in H2 2025 and more than doubled in 2026 (this dip is real in `FACT_CALL_SAMPLE`, independent of the market access gap).
* **10 vs 20 mg** is stable and close to the same split everywhere: little extra information beyond total units.
* **40 mg** is small in units (about 2 units per line) but reaches about 1,000 doctors a quarter and is strongly HF-related. A "received 40 mg in the last 6 / 12 months" flag is a credible candidate, to be tested in the model (E5). No 40 mg before August 2025, so it needs a data-available flag.

### 5.1 How quickly orders settle

Status today of sample lines by order week (Jul – Oct 2026):

| Order week | Lines | Received | `Shipped_vod` | In progress / on hold | Failed (rejected, returned, cancelled, lost) |
| --- | --- | --- | --- | --- | --- |
| 6 Jul – 17 Aug 2026 (weekly) | 1,760 – 2,211 | 96.3 – 97.7% | 0% | 0% | 2.3 – 3.7% |
| 24 Aug – 21 Sep 2026 (weekly) | 1,495 – 2,124 | 95.9 – 97.8% | 0.1 – 0.2% | 1.0 – 2.3% | 1.2 – 2.2% |
| 28 Sep 2026 | 1,581 | 95.1% | 1.0% | 3.0% | 0.9% |
| 5 Oct 2026 | 1,839 | 96.5% | 0.3% | 2.9% | 0.3% |
| 12 Oct 2026 | 1,904 | 88.2% | 7.4% | 3.9% | 0.5% |
| 19 Oct 2026 (last week of data) | 1,706 | 14.4% | 50.2% | 35.1% | 0.4% |

* After two to three weeks almost every order is resolved. Failed orders are about 3% of units in both years (rejected 2.1 – 2.3%, returned 0.5%, lost in transit under 0.1%); failures appear with a delay, so recent weeks show fewer of them.
* The October 2026 rise in `Shipped_vod` and pending statuses (section 3) is mostly this settling effect on recent orders, not a new process.
* `SYS_MODIFIED_ON` cannot be used as a delivery date (median 145 days after the order, because the rolling weekly reload touches old rows), and `LAST_ACTY_DATE` is empty. The data has the order (call) date and the **current** status only.

## 6. Conclusions for NBA 3.1

| # | Conclusion | Action | Owner |
| --- | --- | --- | --- |
| R1 | The market access table is a filtered copy of `FACT_CALL_SAMPLE`, not an independent source. "Call samples" and "samples received / dropped" are the same records | Build sample features **once**, from one source; drop X1 as a separate call-level block | NBA team |
| R2 | The market access table misses `aoc_received__c` (87% of Year 2 received units) and counts `Shipped_vod` as received | Either fix the table / notebook 17 (received = `Delivered` + `AOC Received`, drop `Shipped`), or build sample features directly from `FACT_CALL_SAMPLE` with the status map below | NBA team, owner of `ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER` |
| R3 | Status map (business rule aligned with MV) | Received = `DELIVERED`, `Delivered_vod`, `aoc_received__c`. Not (yet) received = `Shipped_vod`, `In_Progress_vod`, `on_hold__c`. Failed = `rejected__c`, `Returned`, `Cancelled_vod`, `lost_in_transit__c`. Keep the map in a config table | NBA team |
| R4 | NBA 3.0 sample features have been near-empty since August 2025 | Note as a drift cause in the NBA 3.0 vs 3.1 comparison; check sample-feature importance in the NBA 3.0 model | NBA team |
| R5 | Strength: keep total units and sample-call counts; add a 40 mg flag; do not split 10 vs 20 mg | Candidate features for E5 | NBA team |
| R6 | Recent status shift (Oct 2026: more `Shipped_vod` / pending) is mostly orders not yet settled (5.1); within received, `Delivered_vod` is growing relative to `aoc_received__c` since Aug 2026 | No action for received counts (both count); recheck the status mix in December 2026 | NBA team |
| R7 | No delivery date, only current status; recent orders are not yet settled at the data cut, while training history is fully settled | Count received lines by order month. At inference, the last two to three weeks before the data cut are under-counted (consistent with the business rule). In training, rebuild the same effect: for each anchor, ignore orders in the last 21 days before that run's data cut, or use weekly snapshots of the status if they can be kept from now on. Test both in E5. Note: order month is a proxy for the reporting rule (month of receipt); the two differ only for orders placed in the last two to three weeks of a month | NBA team |

**Open questions**

| Code | Question | Who to ask |
| --- | --- | --- |
| Q-S1 | Does `aoc_received__c` count as received? | **Answered:** yes. Received = `Delivered` + `AOC Received`; `Shipped` is not received (business rule aligned with MV; Wenjie Chen, 30 Oct 2026) |
| Q-S2 | Why does the market access table keep only `DELIVERED` / `Delivered_vod` / `Shipped_vod`? Was it built before the Vault CRM status change? | Owner of the table (data team) |
| Q-S3 | What changed in October 2026 (more `Shipped_vod` and pending)? | Mostly answered by 5.1 (orders not yet settled). Open: why `Delivered_vod` is replacing `aoc_received__c` since Aug 2026 | Samples operations / CareTria |
| Q-S5 | Can we get a delivery or status-change date from CareTria, or keep weekly status snapshots, so receipts can be dated? | Samples operations / data team |
| Q-S4 | Is 40 mg sampled mainly for HF patients (as the key messages suggest)? | Kerendia brand team |
