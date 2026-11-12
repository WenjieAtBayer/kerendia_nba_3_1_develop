# ClickStream / CLM Data Review (Nov 2024 – Oct 2026)

**Group:** Personal promotional features (promotion that involves a sales rep)  
**Purpose:** check how much Kerendia CLM (tablet content shown by reps during calls) happened in the last two years, whether the recent iVA campaign is visible in the data, and what this means for NBA 3.1.  
**Built from:** direct queries of Snowflake `CPH_DB_PROD.ANALYTICS_V2.ANLT_BASE_FACT_CLKSTRM` and `CPH_DB_PROD.MODEL_V2.FACT_CALL`  
**Date:** October 26, 2026

## What is this document about?

During a call, a rep can show Kerendia slides, videos or PDFs on a tablet. This is **CLM** ("Closed Loop Marketing"); the record of what was shown and for how long is the **clickstream**. An **iVA** is an "interactive visual aid", one kind of CLM content. How the NBA 3.0 features are built from this data is explained in `13_clickstream_clm_nba_3_0.md`; none of those features was kept in the final NBA 3.0 model.

**How to read names.** Anything written `like this` is the exact name used in the data.

**About the numbers.** The clickstream table was last loaded on 26 October 2026 and has data up to **23 October 2026**, so October 2026 is a partial month. Unless said otherwise, "Kerendia" means `BAYER_PROD_NM = 'KERENDIA'`, the same filter as NBA 3.0. A "CLM call" is a call with at least one clickstream line.

---

## 1. In short

* **CLM is small and has been falling.** About 1,000 – 1,400 CLM calls a month in early 2025, 500 – 900 in most of the last 12 months. Over the two years: 9,644 CLM calls with 4,401 doctors in the first year and 7,351 calls with 4,055 doctors in the second.
* **Less than 1% of Kerendia calls use CLM.** Matched against submitted Kerendia calls, only 0.6 – 0.9% have CLM in almost every month (1.2 – 1.8% in January – April 2025).
* **No new iVA is visible yet.** No Kerendia content named "iVA" or "interactive" appears after July 2025. The last Kerendia iVAs were `Kerendia BACC Dynamic Coverage iVA` (January – May 2025) and `Kerendia Dynamic Coverage iVA` (May – July 2025).
* **August – October 2026 shows only a small rise.** CLM calls went from about 490 – 630 a month (March – June 2026) to 744 (July), 891 (August) and 791 (September). The weekly count has stayed flat at about 160 – 260 calls since early August. Most of this is one piece of content, `BACC Kerendia - Standalone - Vault` (about 90% of CLM calls a week).
* **New content in the last two months is small:** `26 ACC HFpEF ECDP Leave Behind` (from 14 August, 210 calls) and `KER T1D Brochure` (from 24 September, 49 Kerendia calls plus 81 tagged as Lynkuet).
* **The "usage duration" measure stopped working in May 2025.** Before, 96% of lines had a usage time above 0; since June 2025 only 8 – 15% do. "Presentation duration" is still filled in (about 63 – 80% of lines). NBA 3.0 sorts and adds up mainly on usage duration, so its CLM features have been close to zero since mid-2025.

## 2. Monthly activity

"% of Kerendia calls" = share of submitted Kerendia calls in `FACT_CALL` that have Kerendia clickstream.

| Month | CLM calls | Doctors | Pieces of content | Submitted Kerendia calls | % of Kerendia calls |
| --- | --- | --- | --- | --- | --- |
| Nov 2024 | 678 | 608 | 18 | 69,255 | 0.9 |
| Dec 2024 | 412 | 383 | 21 | 50,599 | 0.8 |
| Jan 2025 | 933 | 827 | 22 | 55,070 | 1.7 |
| Feb 2025 | 1,367 | 1,096 | 23 | 76,433 | 1.8 |
| Mar 2025 | 1,146 | 892 | 19 | 80,889 | 1.4 |
| Apr 2025 | 1,014 | 757 | 17 | 84,791 | 1.2 |
| May 2025 | 617 | 514 | 22 | 76,683 | 0.8 |
| Jun 2025 | 591 | 476 | 16 | 71,201 | 0.8 |
| Jul 2025 | 522 | 436 | 25 | 63,363 | 0.8 |
| Aug 2025 | 649 | 563 | 20 | 82,616 | 0.8 |
| Sep 2025 | 806 | 661 | 23 | 99,078 | 0.8 |
| Oct 2025 | 910 | 763 | 22 | 107,415 | 0.8 |
| Nov 2025 | 646 | 554 | 19 | 79,644 | 0.8 |
| Dec 2025 | 564 | 514 | 17 | 64,684 | 0.8 |
| Jan 2026 | 323 | 292 | 21 | 40,817 | 0.7 |
| Feb 2026 | 606 | 534 | 23 | 50,347 | 0.9 |
| Mar 2026 | 488 | 401 | 17 | 56,916 | 0.6 |
| Apr 2026 | 489 | 439 | 21 | 62,436 | 0.6 |
| May 2026 | 570 | 512 | 23 | 61,399 | 0.7 |
| Jun 2026 | 630 | 560 | 24 | 66,701 | 0.6 |
| Jul 2026 | 744 | 637 | 22 | 66,003 | 0.7 |
| Aug 2026 | 891 | 799 | 28 | 63,647 | 0.7 |
| Sep 2026 | 791 | 690 | 34 | 66,899 | 0.7 |
| Oct 2026 (to 23rd) | 609 | 559 | 32 | 49,030 | 0.8 |

Two things in this table to explain:
* The number of **pieces of content** went up from about 20 to 32 – 34 in September – October 2026: new material, but each used in few calls.
* About **half of the CLM calls do not match a submitted Kerendia call** (for example August 2026: 891 CLM calls, 470 matched). They may be calls detailed for another product, or not submitted. See Q3.

## 3. What content is used

Main Kerendia content, November 2024 – October 2026:

| Content (`CLM_PRESN_NM`) | First – last month | CLM calls | Doctors | Calls Sep – Oct 2026 |
| --- | --- | --- | --- | --- |
| `BACC Kerendia - Standalone - Vault` | Jul 2025 – Oct 2026 | 8,822 | 4,401 | 1,292 |
| (no content name) | Nov 2024 – Oct 2026 | 7,583 | 4,142 | 669 |
| `Kerendia BACC Dynamic Coverage iVA` | Jan – May 2025 | 4,375 | 2,364 | 0 |
| `KER CKD/HF Digital MVA Refresh Dual Indication` | Jan – Oct 2026 | 1,312 | 727 | 191 |
| `Kerendia Dynamic Coverage iVA` | May – Jul 2025 | 1,198 | 823 | 0 |
| `LYNKUET DIGITAL MASTER VISUAL AID` | Apr – Oct 2026 | 412 | 268 | 131 |
| `Kerendia CKD & HF Prior Authorization Checklist` | Dec 2025 – Oct 2026 | 379 | 286 | 80 |
| `Tipping Point Brochure` | Nov 2024 – Oct 2026 | 304 | 265 | 17 |
| `KERENDIA CKD Guidelines Leave Behind` | Oct 2025 – Oct 2026 | 236 | 212 | 71 |
| `BACC Lynkuet - Standalone - Vault` | Jun – Oct 2026 | 232 | 202 | 66 |
| `KER HF Digital MVA Refresh Cardiologist` | Jan – Oct 2026 | 230 | 189 | 29 |
| `26 ACC HFpEF ECDP Leave Behind` | Aug – Oct 2026 | 210 | 173 | 158 |
| `UACR Brochure` | Jun – Oct 2026 | 133 | 129 | 61 |
| `KER T1D Brochure` | Sep – Oct 2026 | 49 | 48 | 49 |

("MVA" = master visual aid; "BACC" content is likely access / coverage material, to be confirmed.)

**Other brands mixed in.** The Kerendia filter also returns Lynkuet content (for example `LYNKUET DIGITAL MASTER VISUAL AID`, `BACC Lynkuet - Standalone - Vault`) and a little Adempas content. The opposite happens too: `KER T1D Brochure` is used in 81 calls tagged as Lynkuet. So the product column is not a clean brand filter (see Q4).

## 4. Is the new iVA campaign in the data?

**Not as "iVA", as of 23 October 2026.** A search of all products for content or key messages named `iVA` or `interactive` since January 2025 finds Kerendia iVAs only up to 24 July 2025. Other brands' iVAs (Adempas, Nubeqa) also end in 2025.

Content first seen from August 2026 (all products) contains no iVA either. The new Kerendia items are the HFpEF leave-behind, the T1D brochure, the T1D prior-authorization checklist, call flows, an objection handler and a UHC prior-authorization form; together they are about 300 calls.

Possible explanations, to confirm (Q1, Q2):
* the iVA has a name without "iVA" (for example the `BACC Kerendia - Standalone - Vault` item, or the new T1D materials);
* the iVA is used outside rep calls (remote or self-guided, email, website) and is recorded in a different table;
* it is not yet loaded into this table, or it is tagged under another product.

## 5. Data-quality points

| Point | What was found | Effect on NBA |
| --- | --- | --- |
| Usage duration mostly 0 since May 2025 | Lines with `USAGE_DUR` > 0: 96% in Feb – Apr 2025, 49% in May 2025, 8 – 15% from June 2025. `PRESN_DUR` still about 63 – 80% filled. Year 1: 58% filled; year 2: 15%. | The NBA 3.0 features (which keep the call line with the longest usage time and add up usage) lose most of their signal after mid-2025 |
| No content name | About 7,600 CLM calls (Nov 2024 – Oct 2026) have no `CLM_PRESN_NM` | Content-level features would miss a large part of the data |
| Product tag mixed | Kerendia and Lynkuet content appear under each other's product | A brand filter on `BAYER_PROD_NM` alone mixes brands |
| Half the CLM calls do not match a submitted Kerendia call | For example August 2026: 891 vs 470 | The NBA 3.0 inner join with submitted calls drops about half of the CLM data |
| Few doctors | About 4,000 – 4,400 doctors a year, against about 88,500 in Sales Rep Calls | Features are 0 for about 95% of doctors |

## 6. What this means for NBA 3.1 (facts, not decisions)

* With current volumes (under 1% of calls, about 4,000 doctors a year), CLM is unlikely to work as a separate set of features; at most it could be a few simple flags (any CLM call in the last N months, number of CLM calls, recency).
* If the iVA campaign makes CLM much more common, the earliest months with useful volume would be from September – October 2026. A feature needs several months of history before it can be learned, so it would probably only be ready for a later NBA 3.1 refresh.
* Any duration feature should use **presentation duration**, not usage duration, unless the usage measure is fixed (Q5).
* Content (`CLM_PRESN_NM`) could be grouped into a few themes (access / coverage, indication HF, indication CKD, T1D, guidelines, patient profiles), in line with the content groups used for HCP digital.

## 7. Open questions

| Code | Question | Who to ask |
| --- | --- | --- |
| Q1 | What is the exact name of the new iVA, its launch date, and which reps / doctors it targets? | Kerendia brand team / CLM content owner |
| Q2 | Is the iVA shown by reps on the tablet (Veeva CLM) or used remotely / by email? If remotely, which table records it? | CRM / CLM team |
| Q3 | Why do about half of the CLM calls not match a submitted Kerendia call (other detailed product, not submitted, different call ID)? | CRM / data engineering |
| Q4 | Why is Lynkuet content tagged as Kerendia (and Kerendia content as Lynkuet)? Is there a cleaner brand field? | Data engineering |
| Q5 | Why did `USAGE_DUR` become mostly 0 from May 2025? What do `USAGE_DUR` and `PRESN_DUR` measure, and in what unit? | CLM / data engineering |
| Q6 | Why do about 7,600 CLM calls have no content name? | Data engineering |
| Q7 | How quickly does new CLM activity reach `ANLT_BASE_FACT_CLKSTRM` (it currently has data to 23 October, loaded 26 October)? | Data engineering |

## 8. Answers (to fill in)

| Code | Answer | Source (who / meeting / date) |
| --- | --- | --- |
| Q1 | | |
| Q2 | | |
| Q3 | | |
| Q4 | | |
| Q5 | | |
| Q6 | | |
| Q7 | | |

## 9. References

* `13_clickstream_clm_nba_3_0.md`: how the NBA 3.0 CLM features are built, and why none is in the NBA 3.0 model
* NBA 3.0 notebook `18_promotional_ClickStream_features` (NBA 3.0 Ops pipeline)
* NBA 3.0 model: MLflow run `f583bcbc9d56477fae983d44c16f8c70`
