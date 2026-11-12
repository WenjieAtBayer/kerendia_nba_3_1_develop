# EDA Check 1 — Unmatched Rate by Claim Month (Open point D1)

**Question:** Why are 53.2% of Kerendia claims `No_MMIT_Match` (documented 17.6%), and how much is explained by MMIT period coverage?

**Status:** Formulary side complete. Claim side runs in notebook `MMIT_EDA_Claim_Level_Checks` (section 1).

---

## 1. How the pipeline limits periods

In `mmit_feature_test_notebook`:
* `bronze_iqvia_bridge` is read as `DISTINCT OrgId, IMSPayerPlanId` **across all periods**, so the bridge does not restrict months. This corrects the earlier note in `MMIT_Additional_Claim_Features_EDA.md`.
* `lives_per_org` (`bronze_states`) is grouped by `OrgId, Period` and joined on `OrgId` only. Its `Period` then joins `status_deduped` on `FormularyId, Period`. In practice, the usable periods are where **both** states and statuses exist for the target drugs.

## 2. Period availability (target drugs)

| Period | statuses (target MedIds) | states | bridge |
|---|---|---|---|
| 202506 | pilot only (31 drugs, not Kerendia) | no | no |
| 202507 | pilot only | yes | no |
| 202508 | pilot only | yes | no |
| 202509 | **missing in all tables** | no | no |
| 202510 - 202609 | yes (5,112+ drugs, ~2,100 formularies) | yes | yes |

`bronze_statuses` periods 202506-202508 contain about 114K rows and 31 MedIds (a pilot load). The full feed (about 48M rows per period) starts in **202510**.

## 3. Expected impact

* Claims window: 202409 - 202608 (24 months).
* Months with MMIT status: **202510 - 202608 = 11 months**.
* 13 of 24 months (54%) can never match. This is very close to the observed 53.2% unmatched rate, so **period coverage likely explains most of D1**. Claim volume grows over time, so the claim-weighted share is expected to be slightly below 54%; the notebook confirms this.

## 4. Claim-level results (from notebook)

* Covered-window claims (`202510`-`202608`): **1,352,113**
* Covered-window unmatched claims: **142,496** (**10.54%**)
* Covered-window split: `No_Payer_Match` = **87,158** (**6.45%**), `No_Drug_Row` = **55,338** (**4.09%**)
* `No_Period_Match` is zero inside the covered window by construction.

Unmatched-rate trend by claim month:

| claim_month | claims | matched_claims | unmatched_rate_pct | No_Period_Match_pct | No_Payer_Match_pct | No_Drug_Row_pct |
| --- | --- | --- | --- | --- | --- | --- |
| 202409 | 79155 | 0 | 100.0 | 100.0 | 0.0 | 0.0 |
| 202410 | 87278 | 0 | 100.0 | 100.0 | 0.0 | 0.0 |
| 202411 | 81724 | 0 | 100.0 | 100.0 | 0.0 | 0.0 |
| 202412 | 87856 | 0 | 100.0 | 100.0 | 0.0 | 0.0 |
| 202501 | 92270 | 0 | 100.0 | 100.0 | 0.0 | 0.0 |
| 202502 | 87447 | 0 | 100.0 | 100.0 | 0.0 | 0.0 |
| 202503 | 97963 | 0 | 100.0 | 100.0 | 0.0 | 0.0 |
| 202504 | 99302 | 0 | 100.0 | 100.0 | 0.0 | 0.0 |
| 202505 | 100943 | 0 | 100.0 | 100.0 | 0.0 | 0.0 |
| 202506 | 100169 | 0 | 100.0 | 100.0 | 0.0 | 0.0 |
| 202507 | 105725 | 0 | 100.0 | 100.0 | 0.0 | 0.0 |
| 202508 | 104578 | 0 | 100.0 | 100.0 | 0.0 | 0.0 |
| 202509 | 109229 | 0 | 100.0 | 100.0 | 0.0 | 0.0 |
| 202510 | 118510 | 111088 | 6.26 | 0.0 | 6.26 | 0.0 |
| 202511 | 109869 | 103215 | 6.06 | 0.0 | 6.06 | 0.0 |
| 202512 | 126960 | 119271 | 6.06 | 0.0 | 6.06 | 0.0 |
| 202601 | 121485 | 113416 | 6.64 | 0.0 | 6.64 | 0.0 |
| 202602 | 115462 | 107825 | 6.61 | 0.0 | 6.61 | 0.0 |
| 202603 | 121836 | 105118 | 13.72 | 0.0 | 6.54 | 7.18 |
| 202604 | 119844 | 103437 | 13.69 | 0.0 | 6.61 | 7.09 |
| 202605 | 122760 | 105769 | 13.84 | 0.0 | 6.54 | 7.3 |
| 202606 | 130696 | 112544 | 13.89 | 0.0 | 6.64 | 7.25 |
| 202607 | 132269 | 114036 | 13.78 | 0.0 | 6.45 | 7.33 |
| 202608 | 132422 | 113898 | 13.99 | 0.0 | 6.46 | 7.53 |

Top 15 unmatched `PAYER_PLAN_ID` values inside `202510`-`202608` (share of unmatched claims in-window):

| PAYER_PLAN_ID | claims | claim_share_pct |
| --- | --- | --- |
| 0002870169 | 16001 | 11.23 |
| 8888880001 | 10426 | 7.32 |
| 7000010001 | 7909 | 5.55 |
| 7000010191 | 7353 | 5.16 |
| 4444449999 | 5996 | 4.21 |
| 0000010001 | 5192 | 3.64 |
| 0010450003 | 4087 | 2.87 |
| 0002870207 | 3186 | 2.24 |
| 0002870173 | 2958 | 2.08 |
| 0002870476 | 2181 | 1.53 |
| 0035710001 | 1892 | 1.33 |
| 0019150002 | 1828 | 1.28 |
| 0002870499 | 1750 | 1.23 |
| 0002870174 | 1558 | 1.09 |
| 7003900001 | 1547 | 1.09 |

## 5. Recommendation

* Restrict MMIT features (and model training months that use them) to `claim_month >= 202510`.
* Ask MMIT / data engineering whether 202509 and pre-202510 full loads can be backfilled.
* Optionally carry 202510 status back to earlier months as a static proxy, with a flag column `mmit_status_imputed = 1`.
