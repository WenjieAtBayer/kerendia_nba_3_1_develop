# Phase 0 Samples Explained (V5)

**For:** readers new to the Kerendia samples data  
**Validation step:** V5 of `40_field_activity_nba_3_1_readiness_plan.md`  
**Source:** `22_samples_reconciliation_call_vs_shipped_dropped_2024_2026.md` (30 Oct 2026, data to 23 Oct 2026)  
**Years:** Year 1 = Nov 2024 – Oct 2025, Year 2 = Nov 2025 – Oct 2026

**V5 in one sentence.** We have two tables about Kerendia samples; V5 checks whether they are two different sources or the same data twice. Answer: the same data, and one of them has lost most records since mid-2025.

---

## 1. What is a sample?

A rep visits a doctor and orders free Kerendia sample packs (10 mg, 20 mg or 40 mg tablets) for the practice. A warehouse company, **CareTria**, ships them to the doctor's office by FedEx. So a sample has a life: **ordered, then in transit, then received**, or it **fails** (refused, returned, lost).

**Business rule (aligned with MV, Source: Wenjie Chen):** a sample counts only when the doctor has **received** it, i.e. status `Delivered` or `AOC Received`. `Shipped` is not received, because some shipments come back.

---

## 2. Table 1: `CPH_DB_PROD.MODEL_V2.FACT_CALL_SAMPLE`

The **original source**, straight from Veeva CRM (the reps' tool). One row per sample product ordered during a call (a "sample line"):

* sample record ID (`CALL_SMPL_NM`) and the call it belongs to;
* doctor (turned into a BHID through `MAP_CUSTOMER_XREF`);
* product (`Kerendia 10mg / 20mg / 40mg BRC`; brochures, boxes and kits are excluded);
* date (call / order date) and quantity (units);
* the **current status** of the order (section 4);
* a deletion flag (`SYS_DELETE_FLAG`, we keep `'0'`).

There is **no delivery date**: only the order date and where the order stands today.

---

## 3. Table 2: `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_KERENDIA_SAMPLES_SHIPPED_DROPPED_KER`

The **market access table**, built by another team and read by the NBA 3.0 market access block (notebook `17_promotional_features_samples`). Same kind of row (sample record ID `SMPLE_CALL_NM`, doctor, product, date, quantity), but instead of the full status it has just one flag:

* `DROPPED` = sample dropped off (delivered);
* `SHIPPED` = sample sent.

---

## 4. Which values are in each table

| Status in `FACT_CALL_SAMPLE` | Plain meaning | Business rule | In the market access table? |
| --- | --- | --- | --- |
| `DELIVERED` | Delivered (old CRM, until 23 Jul 2025) | Received | Yes, as `DROPPED` |
| `Delivered_vod` | Delivered (new Vault CRM) | Received | Yes, as `DROPPED` |
| `aoc_received__c` | Doctor confirmed receipt ("acknowledgement of content") | **Received** | **No, missing** |
| `Shipped_vod` | On the way | Not yet received | Yes, as `SHIPPED` (counted too early, section 7) |
| `In_Progress_vod`, `on_hold__c` | Being processed | Not yet received | No |
| `rejected__c`, `Returned`, `Cancelled_vod`, `lost_in_transit__c` | Failed | Never received | No |

**Values in both tables:** Kerendia 10 / 20 / 40 mg sample lines with status `DELIVERED` / `Delivered_vod` (shown as `DROPPED`) and `Shipped_vod` (shown as `SHIPPED`). In Nov 2024 – 23 Oct 2026: 56,507 `DROPPED` and 1,047 `SHIPPED` lines. **Every one** is found in `FACT_CALL_SAMPLE` with the same record ID, doctor, product, date and quantity (100% match). The market access table is a **filtered copy** of `FACT_CALL_SAMPLE`, not a second source.

---

## 5. Why this matters: the July 2025 CRM change

At the end of July 2025 Bayer moved to Vault CRM. From then on, most completed samples get the new status `aoc_received__c` instead of `DELIVERED`. The market access table was never updated to keep this status, so it lost most samples:

| | Year 1 | Year 2 |
| --- | --- | --- |
| Received units (business rule, `FACT_CALL_SAMPLE`) | 425,450 | 449,246 |
| Of which also in the market access table | 86.8% | **13.1%** |
| Doctors who received samples | 16,793 | 20,270 |
| Of whom also in the market access table | 89.7% | **22.5%** |

The market access table also counts 6,652 Year 2 units that are only `Shipped_vod` (in transit, section 7).

---

## 6. A small example

Dr. A gets three sample lines in Sep 2026:

| Line | Product | Units | Status in `FACT_CALL_SAMPLE` | Market access table | Counted as received? |
| --- | --- | --- | --- | --- | --- |
| S1 | 10 mg | 6 | `Delivered_vod` | `DROPPED`, 6 | Yes |
| S2 | 20 mg | 4 | `aoc_received__c` | (not there) | Yes |
| S3 | 40 mg | 2 | `Shipped_vod` | `SHIPPED`, 2 | No (in transit) |

Truth: **10 units received**. The market access table shows **8 units**: it misses S2 and includes S3 too early.

---

## 7. What "`SHIPPED` counted too early" means

The market access table includes samples that are **still on their way** to the doctor, and NBA 3.0 counts them as if the doctor already has them.

**Step by step**

1. A rep orders samples. CareTria ships them; Veeva sets status `Shipped_vod` (in transit).
2. The market access table copies the line with flag `SHIPPED`.
3. The NBA 3.0 market access block (notebook `17_promotional_features_samples`) adds `SHIPPED` and `DROPPED` lines together as "samples the doctor got".
4. But it is not yet known whether the package will arrive. Most do, a few days later. A few don't: the office refuses delivery, the address is wrong, or FedEx loses it; they go back to the warehouse.

**Example**

* 20 Oct 2026: a rep orders 2 packs of 40 mg for Dr. B. Status `Shipped_vod`.
* Data cut 23 Oct: the market access table shows Dr. B with 2 units (`SHIPPED`); the NBA 3.0 feature says "Dr. B received 2 units".
* 27 Oct: the office refuses delivery, status becomes `Returned`. Dr. B **never received** anything, but the model already used it.
* If instead it arrives on 27 Oct, status becomes `Delivered_vod` and next week's refresh shows it as `DROPPED`, so it is right, just counted a few days early.

**How big it is**

* 1,047 `SHIPPED` lines in the whole period vs 56,507 `DROPPED`.
* Year 2: 6,652 units, about 10% of the table's Year 2 units, almost all ordered in the last two weeks before the data cut (older orders are already settled).
* About 3% of orders fail in the end, so most `SHIPPED` lines do become received.

So it is a **small** problem, much smaller than the missing `aoc_received__c` lines (87% of Year 2 received units). It matters mainly at the latest data cut, which is exactly the period the model scores on. "Counted too early" means counted before receipt, not an invented sample.

---

## 8. Other findings

* **Orders settle in about 2 – 3 weeks.** Older orders are 95 – 98% received; the last week of data only 14%.
* **Strength is reliable.** 10 / 20 mg is a stable split (about 61% / 37% of units), so it adds little. 40 mg exists only since August 2025 and is linked to heart failure: about 60% of 40 mg sample calls carry an HF key message vs about 30% for 10 / 20 mg. A 40 mg flag is a candidate feature.

---

## 9. Decision for NBA 3.1

Build sample features **once**, directly from `FACT_CALL_SAMPLE`, with this status map:

| Group | Statuses |
| --- | --- |
| Received | `DELIVERED`, `Delivered_vod`, `aoc_received__c` |
| Not yet received | `Shipped_vod`, `In_Progress_vod`, `on_hold__c` |
| Failed | `rejected__c`, `Returned`, `Cancelled_vod`, `lost_in_transit__c` |

Open question **Q-S2** for the table owner: fix the market access table or retire it. Until then, NBA 3.0 sample features have been almost empty since August 2025 for a data reason, not because reps stopped sampling.
