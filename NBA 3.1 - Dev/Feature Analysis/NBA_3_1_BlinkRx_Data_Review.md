# NBA 3.1 – BlinkRx Data Review

**Date:** 2026-10-27
**Sources:** `cph_db_prod.enrich.blinkrx_dispense`, `cph_db_prod.enrich.blinkrx_status`
**LAAD comparison table:** `PHCDW.PHCDW_STG_CAR.STG_CAR_IQV_LAAD_FCT_RX` (provider dimension: `PHCDW.PHCDW_STG_CAR.STG_IQVIA_LAAD_DIM_PROVIDER`)

---

## 1. What is BlinkRx?

BlinkRx is a pharmacy benefit and e-prescribing platform. The Bayer data feed contains **Kerendia only** (no other products). It captures two views:

* **Dispense table** (`blinkrx_dispense`): actual fulfilled prescriptions (1.04M rows, 63 columns)
* **Status table** (`blinkrx_status`): Rx lifecycle events tracking each prescription through stages: `discovery → onboarding → rph_review → completed → closed` (also `cancelled`, `transfer`) — 10.04M rows, 48 columns

Also mirrored at `cph_db_prod.analytics_v2.blinkrx_dispense` and `phcdw.phcdw_cdm.blinkrx_dispense` / `blinkrx_dispense_vw`.

---

## 2. Overall BlinkRx summary

| Metric | Dispense table | Status table |
| --- | --- | --- |
| Total records | 1,040,535 | 10,043,019 |
| Unique HCPs (NPI) | 2,561 | 3,407 |
| Unique patients | 5,994 | 9,400 |
| Date range | 2024-03-22 – 2026-10-23 | 2024-01 – 2026-09 |
| Products | Kerendia 10/20/40 MG only | Kerendia 10/20/40 MG only |

The status table has more HCPs (3,407 vs 2,561) and patients (9,400 vs 5,994) because it includes prescriptions that were initiated but never fulfilled (cancelled, still onboarding, etc.).

### 2.1 Product breakdown (dispense)

| Product | Dispenses | HCPs | Patients |
| --- | --- | --- | --- |
| Kerendia 10 MG | 684,523 (65.8%) | 1,893 | 4,079 |
| Kerendia 20 MG | 351,102 (33.7%) | 1,163 | 2,183 |
| Kerendia 40 MG | 4,910 (0.5%) | 56 | 84 |

### 2.2 Payer mix (dispense)

| Payer type | Dispenses | % | HCPs |
| --- | --- | --- | --- |
| Medicare | 563,992 | 54.2% | 1,813 |
| Commercial | 429,123 | 41.2% | 1,175 |
| Government | 18,474 | 1.8% | 150 |
| No insurance | 14,842 | 1.4% | 94 |
| Medicaid | 11,705 | 1.1% | 92 |
| Unknown | 1,743 | 0.2% | 16 |
| Medicare M3P | 656 | 0.1% | 4 |

### 2.3 Script type (dispense)

| Script type | Dispenses | % |
| --- | --- | --- |
| Refills | 660,436 | 63.5% |
| New to Blink | 283,740 | 27.3% |
| Renewals | 96,359 | 9.3% |

### 2.4 Status lifecycle (status table, Kerendia)

| Status | Records | HCPs | Patients |
| --- | --- | --- | --- |
| closed | 7,064,382 | 2,556 | 5,979 |
| onboarding | 1,514,773 | 3,148 | 8,582 |
| cancelled | 1,168,553 | 1,727 | 3,773 |
| discovery | 164,590 | 2,110 | 4,581 |
| completed | 123,654 | 2,562 | 5,990 |
| rph_review | 4,911 | 1,178 | 1,953 |
| transfer | 2,156 | 559 | 751 |

**Note:** "completed" HCPs (2,562) align closely with dispense HCPs (2,561), confirming the dispense table captures successfully filled prescriptions. The "onboarding" stage has 3,148 HCPs — 846 more than "completed" — representing prescribers whose Rx entered the system but didn't all convert to fills.

### 2.5 Top prescriber states (dispense)

| State | Dispenses | % | HCPs |
| --- | --- | --- | --- |
| TX | 157,936 | 15.2% | 402 |
| FL | 125,231 | 12.0% | 332 |
| GA | 105,741 | 10.2% | 232 |
| VA | 80,272 | 7.7% | 141 |
| IN | 50,092 | 4.8% | 78 |
| TN | 49,198 | 4.7% | 204 |
| OK | 40,816 | 3.9% | 55 |
| NC | 40,442 | 3.9% | 109 |
| NY | 40,005 | 3.8% | 97 |
| PA | 36,594 | 3.5% | 57 |

Top 10 states account for ~70% of dispenses.

---

## 3. LAAD coverage on BlinkRx

Join key: `PRESCRIBER_NPI` (BlinkRx) → `NPI_NUMBER` (LAAD via `STG_IQVIA_LAAD_DIM_PROVIDER`).

### 3.1 HCP-level overlap

| Metric | Count |
| --- | --- |
| BlinkRx Kerendia HCPs (dispense) | 2,561 |
| LAAD total HCPs (provider dimension) | 1,854,823 |
| BlinkRx HCPs found in LAAD (any drug) | 2,274 (88.8%) |
| BlinkRx HCPs NOT in LAAD | 287 (11.2%) |

### 3.2 Kerendia-specific HCP overlap

| Metric | Count |
| --- | --- |
| BlinkRx Kerendia HCPs | 2,561 |
| LAAD Kerendia HCPs (NDC `50419054*`, since 2024) | 70,123 |
| Overlap (in both sources for Kerendia) | 2,212 (86.4% of BlinkRx) |
| BlinkRx Kerendia HCPs NOT in LAAD Kerendia | 349 (13.6%) |
| — of which: in LAAD but no Kerendia claims | 62 |
| — of which: not in LAAD at all | 287 |

**Interpretation:**
* **86.4%** of BlinkRx Kerendia prescribers are also captured as Kerendia prescribers in LAAD.
* **13.6%** (349 HCPs) prescribe Kerendia through BlinkRx but do not appear in LAAD Kerendia claims:
  * 62 are in LAAD for other drugs but have no Kerendia claims there — these may be prescribers whose Kerendia Rx exclusively flow through BlinkRx (e.g., specialty pharmacy not captured by IQVIA).
  * 287 are not in the LAAD provider dimension at all — these are likely NPI mismatches, retired/new NPIs, or providers outside IQVIA's panel.
* **Only 3.2%** of LAAD's 70K Kerendia HCPs use BlinkRx — BlinkRx is a niche channel covering a small subset of Kerendia prescribers.

### 3.3 Patient-level overlap

**Not directly assessable.** BlinkRx uses `UNIQUE_PATIENT_ID` (BlinkRx-internal) while LAAD uses `PATIENT_ID` (IQVIA-internal). There is no common patient identifier (no shared key or crosswalk available). Patient-level linkage would require probabilistic matching on demographics (age, zip, dates), which is out of scope here.

---

## 4. Monthly volume comparison: BlinkRx vs LAAD Kerendia

| Month | BlinkRx dispenses | BlinkRx HCPs | LAAD claims | LAAD HCPs | BlinkRx as % of LAAD vol |
| --- | --- | --- | --- | --- | --- |
| 2024-03 | 710 | 3 | 191,533 | 15,954 | 0.4% |
| 2024-04 | 32,925 | 73 | 201,783 | 16,553 | 16.3% |
| 2024-05 | 48,809 | 115 | 209,280 | 16,956 | 23.3% |
| 2024-06 | 32,889 | 94 | 216,027 | 17,523 | 15.2% |
| 2024-07 | 41,365 | 123 | 232,994 | 18,266 | 17.8% |
| 2024-08 | 44,608 | 117 | 230,722 | 18,246 | 19.3% |
| 2024-09 | 32,221 | 100 | 226,238 | 18,401 | 14.2% |
| 2024-10 | 40,011 | 114 | 249,081 | 19,299 | 16.1% |
| 2024-11 | 30,168 | 81 | 232,660 | 18,819 | 13.0% |
| 2024-12 | 26,555 | 82 | 250,008 | 19,629 | 10.6% |
| 2025-01 | 45,672 | 131 | 261,974 | 20,051 | 17.4% |
| 2025-02 | 41,408 | 129 | 247,796 | 19,800 | 16.7% |
| 2025-03 | 39,221 | 130 | 276,606 | 20,865 | 14.2% |
| 2025-04 | 48,255 | 152 | 279,336 | 21,176 | 17.3% |
| 2025-05 | 37,912 | 149 | 284,168 | 21,411 | 13.3% |
| 2025-06 | 43,321 | 168 | 281,655 | 21,689 | 15.4% |
| 2025-07 | 41,393 | 167 | 297,161 | 22,206 | 13.9% |
| 2025-08 | 41,575 | 204 | 293,767 | 22,184 | 14.2% |
| 2025-09 | 45,056 | 230 | 306,127 | 22,960 | 14.7% |
| 2025-10 | 56,458 | 269 | 331,356 | 23,970 | 17.0% |
| 2025-11 | 39,309 | 224 | 306,818 | 23,501 | 12.8% |
| 2025-12 | 34,897 | 223 | 354,044 | 25,055 | 9.9% |
| 2026-01 | 38,026 | 272 | 337,848 | 24,939 | 11.3% |
| 2026-02 | 36,256 | 322 | 320,265 | 24,765 | 11.3% |
| 2026-03 | 34,957 | 387 | 337,607 | 25,670 | 10.4% |
| 2026-04 | 27,046 | 380 | 330,629 | 25,739 | 8.2% |
| 2026-05 | 20,719 | 362 | 338,488 | 26,087 | 6.1% |
| 2026-06 | 16,687 | 384 | 359,975 | 26,957 | 4.6% |
| 2026-07 | 11,822 | 397 | 364,893 | 27,797 | 3.2% |
| 2026-08 | 6,570 | 368 | 363,495 | 28,182 | 1.8% |
| 2026-09 | 3,076 | 387 | 365,556 | 28,614 | 0.8% |

**Observations:**
* BlinkRx volume peaked at **23.3% of LAAD** in May 2024, stabilized around **13–17%** through mid-2025, then declined sharply through 2026 to under **1%** by Sep 2026.
* Meanwhile LAAD Kerendia volume has grown steadily (~190K/mo in Mar 2024 → ~365K/mo in Sep 2026), with prescriber counts growing from \~16K to \~29K.
* The declining BlinkRx share despite growing HCP counts (397 unique in Jul 2026) suggests BlinkRx prescriptions per HCP are shrinking — possibly due to patients or payers shifting to other pharmacy channels.
* **Important caveat:** BlinkRx dispense counts appear inflated relative to traditional Rx counts. A single 30-day fill in the standard Rx sense may appear as multiple dispense records in BlinkRx (e.g., due to weekly data snapshots, status changes, or shipment-level records). The 1.04M BlinkRx dispenses should not be directly compared to LAAD claims as a 1:1 Rx equivalence — the ratio overstates BlinkRx's share of actual prescriptions.

---

## 5. Kerendia NDC codes

| NDC | Product | In BlinkRx | In LAAD |
| --- | --- | --- | --- |
| 50419054001 | Kerendia 10 MG (30ct) | Yes | Yes (2.01M claims) |
| 50419054002 | Kerendia 10 MG (90ct) | Yes | Yes (231K claims) |
| 50419054101 | Kerendia 20 MG (30ct) | Yes | Yes (942K claims) |
| 50419054102 | Kerendia 20 MG (90ct) | Yes | Yes (108K claims) |
| 50419054201 | Kerendia 40 MG (30ct) | Yes | Yes (8.4K claims) |
| 50419054202 | Kerendia 40 MG (90ct) | Yes | Yes (1.2K claims) |
| 50419054006 | Kerendia 10 MG (other) | No | Yes (1.6K claims) |
| 50419054106 | Kerendia 20 MG (other) | No | Yes (1.1K claims) |
| 50419054206 | Kerendia 40 MG (other) | No | Yes (243 claims) |

All 6 BlinkRx NDCs are present in LAAD. LAAD has 3 additional NDC variants not in BlinkRx (minor volume).

---

## 6. Implications for NBA 3.1

1. **BlinkRx as a supplementary signal.** BlinkRx captures a niche pharmacy channel (3.2% of LAAD Kerendia HCPs). For the 349 HCPs not in LAAD Kerendia, BlinkRx provides unique prescribing evidence.
2. **HCP-level features.** BlinkRx could contribute:
   * `BLINKRX_FLAG` (binary: HCP ever dispensed Kerendia through BlinkRx)
   * Payer mix signal (54% Medicare vs 41% commercial)
   * Prescription lifecycle features from the status table (e.g., conversion rate: `completed` / `onboarding`)
   * New-to-Blink rate as a proxy for channel switching
3. **LAAD already covers most BlinkRx HCPs.** 86.4% overlap means BlinkRx volume features would be largely redundant with LAAD Rx claims for the majority of prescribers. The incremental value is in:
   * The 349 BlinkRx-only HCPs (unique signal)
   * Lifecycle/fulfillment signals not available in LAAD (cancellations, onboarding delays)
   * Payer-level detail specific to the BlinkRx channel
4. **Volume decline.** The sharp decline in BlinkRx dispenses through 2026 (from \~40K/mo to \~3K/mo) while LAAD grows may indicate a channel shift. This should be monitored — if BlinkRx volume continues to shrink, its feature value for the model will diminish.
5. **Patient-level linkage.** No direct patient crosswalk exists between BlinkRx (`UNIQUE_PATIENT_ID`) and LAAD (`PATIENT_ID`). Patient-level features from BlinkRx would need to be aggregated to the HCP level for use in the NBA model.

---

## 7. Caveats

* LAAD Kerendia claims are filtered by NDC prefix `50419054*` and `SVC_DT >= 2024-01-01`.
* BlinkRx dispense counts may not represent individual Rx fills on a 1:1 basis; the data appears to contain snapshot-level records.
* The 287 BlinkRx NPIs absent from LAAD's provider dimension were not further investigated (could be NPI format issues, new providers, or out-of-panel).
* Oct 2026 data is incomplete in both sources (partial month).
* Correlation checks between BlinkRx and LAAD claim volumes at the HCP level were not performed (would require patient-level deduplication).
