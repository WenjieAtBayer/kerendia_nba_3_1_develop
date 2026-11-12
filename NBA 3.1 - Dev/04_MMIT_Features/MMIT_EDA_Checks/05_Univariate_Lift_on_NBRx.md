# EDA Check 5 — Univariate Lift of High-Priority Access Features on Next-Month Kerendia NBRx

**Question:** Do the high-priority (H) candidate features carry signal for next-month Kerendia new-patient prescribing at HCP level, beyond the current 6-category `kerendia_access` counts?

**Status:** Complete. Ran in notebook `MMIT_EDA_Claim_Level_Checks` (section 5) using Kerendia claims from Snowflake.

---

## 1. Design

* **Grain:** `PROVIDER_ID x claim_month`, months **202510-202607** (MMIT-covered months that also have a following month in the claims window).
* **Population:** HCPs with at least 1 Kerendia claim in the month (the same population as the current features).
* **Target:** `next_month_nbrx_flag` = HCP has at least one new Kerendia patient in month t+1. A new patient is one whose first Kerendia claim since 2024-09 occurs in t+1, which gives at least 13 months of lookback for t+1 >= 202511. Secondary target: `next_month_trx` (claim count).
* **Features tested** (share of the HCP's Kerendia claims in month t):

| Group | Feature |
|---|---|
| Baseline | `share_kerendia_Covered`, `share_kerendia_Covered_with_PA_ST`, `share_kerendia_Not_Covered` |
| A Status | `share_kerendia_Preferred` (split from Covered), `share_kerendia_worse_than_jardiance` |
| B Restrictions | `share_has_PA`, `share_has_ST`, `share_step_requires_sglt2`, `share_ckd_pa_ars_R` |
| D Bayer HPM | `share_hpm_unrestricted`, `share_hpm_pa_to_label`, `share_hpm_step` (from 202601) |
| E Change | `share_kerendia_improved_l3m`, `share_kerendia_worsened_l3m` |
| F Plan | `share_medicare`, `share_commercial`, `share_top3_pbm` |

* **Metrics per feature:** fill rate; next-month NBRx rate by feature quintile / bin (lift = bin rate / overall rate); univariate AUC; Spearman correlation with `next_month_trx`; partial check controlling for the HCP's current-month Kerendia volume (lift within volume terciles), so volume does not drive the effect.

## 2. Results

Overall next-month NBRx flag rate: **17.65%** across **289,232** HCP-month rows.

| Feature | Fill rate | AUC | Top-bin lift | Bottom-bin lift | Lift within volume terciles (low / mid / high) |
| --- | --- | --- | --- | --- | --- |
| share_commercial | 89.17 | 0.5791 | 0.779 | 0.694 | 1.126 / 0.975 / 0.828 |
| share_step_requires_sglt2 | 40.92 | 0.5749 | 0.837 | 0.735 | 0.98 / 0.939 / 0.897 |
| share_kerendia_Covered | 89.17 | 0.5505 | 0.458 | 0.616 | 1.008 / 0.779 / 0.926 |
| share_ckd_pa_ars_R | 44.19 | 0.541 | 0.472 | 0.573 | 0.98 / 0.735 / 0.803 |
| share_has_ST | 74.07 | 0.5295 | 0.49 | 0.558 | 0.989 / 0.734 / 0.859 |
| share_kerendia_Not_Covered | 89.17 | 0.5195 | 1.059 | 1.009 | 0.983 / 0.717 / 0.998 |
| share_kerendia_improved_l3m | 89.17 | 0.5119 | 1.0 | 1.011 | 1.053 / 0.717 / 0.967 |
| share_hpm_pa_to_label | 62.87 | 0.5117 | 1.075 | 1.043 | 1.022 / 0.671 / 0.958 |
| share_hpm_unrestricted | 62.87 | 0.5106 | 1.081 | 1.045 | 1.068 / 0.684 / 0.958 |
| share_hpm_step | 62.87 | 0.5074 | 0.97 | 1.01 | 1.007 / 0.729 / 0.947 |
| share_kerendia_worsened_l3m | 89.17 | 0.5012 | 0.959 | 1.004 | 0.257 / 0.731 / 0.902 |
| share_has_PA | 74.07 | 0.4966 | 0.501 | 0.53 | 0.99 / 0.668 / 0.789 |
| share_kerendia_Covered_with_PA_ST | 89.17 | 0.4879 | 0.524 | 0.516 | 0.996 / 0.67 / 0.783 |
| share_kerendia_worse_than_jardiance | 89.17 | 0.487 | 0.516 | 0.515 | 0.987 / 0.655 / 0.79 |
| share_medicare | 89.17 | 0.4834 | 0.498 | 0.531 | 0.952 / 0.669 / 0.819 |
| share_top3_pbm | 89.17 | 0.4829 | 0.552 | 0.488 | 1.028 / 0.709 / 0.785 |
| share_kerendia_Preferred | 89.17 | 0.4726 | 0.526 | 0.489 | 0.996 / 0.672 / 0.784 |

## 3. Interpretation guide

* AUC 0.50-0.52 is no signal; 0.55+ is a useful univariate feature for this kind of target.
* Prefer features whose lift holds within volume terciles.
* Expect low fill for D before 202601 and for E before 202601 (see Checks 3 and 6).

## 4. Initial takeaways

* `share_commercial` and `share_step_requires_sglt2` were the strongest single variables in this pass, both with AUC around 0.575.
* The Bayer HPM splits (`share_hpm_pa_to_label`, `share_hpm_unrestricted`, `share_hpm_step`) added modest but directional signal once available, with top-bin lift just above 1.0 for the first two.
* `share_kerendia_Not_Covered` showed the clearest top-bin lift (>1.05) but weak overall discrimination, so it may act more like a sparse segment flag than a broadly ranked feature.
* Several existing coarse access-share features (`share_kerendia_Covered_with_PA_ST`, `share_kerendia_Preferred`) were below random-ranking parity on AUC, which supports splitting them into richer restriction and HPM-derived features instead of relying only on the current rollup buckets.

## 5. Stratified AUC by HCP restricted-claim tercile

**Question:** Does the discriminative power of the access features change depending on how many of the HCP's Kerendia claims sit on restricted formularies (PA, ST or QL)?

**Method:** Tercile assignment by quantile on each HCP's total restricted-claim count (202510-202607). A restricted claim is one whose winning formulary has a PA, ST or QL row in `bronze_restrictions`. Two additional features were computed for this check: `share_has_QL` and `share_any_restriction`.

### Tercile profile

| Tercile | HCPs | Restricted claims per HCP (min-max) | Median restricted claims | Median total claims | Restricted share of claims % | HCP-months | Next-month NBRx rate % |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Low | 23,604 | 0-2 | 1.0 | 2.0 | 33.74 | 47,650 | 3.07 |
| Medium | 16,154 | 3-8 | 5.0 | 6.0 | 75.53 | 68,720 | 6.06 |
| High | 19,634 | 9-3,466 | 21.0 | 27.0 | 77.30 | 172,862 | 26.27 |

Tercile method: quantile (no zero-collapse fallback was needed).

AUC below 0.5 means the feature is inversely related to next-month NBRx (higher value, lower NBRx). "Max distance from 0.5" is the largest absolute gap between the tercile AUC and 0.5, so it ranks signal strength in either direction.

### AUC by tercile

| Feature | AUC overall | AUC Low | AUC Medium | AUC High | Strongest tercile | Max distance from 0.5 | AUC range across terciles |
| --- | --- | --- | --- | --- | --- | --- | --- |
| share_any_restriction | 0.4311 | 0.451 | 0.378 | 0.3908 | Medium | 0.122 | 0.073 |
| share_has_QL | 0.4498 | 0.4583 | 0.3923 | 0.4118 | Medium | 0.1077 | 0.066 |
| share_medicare | 0.4834 | 0.4609 | 0.4115 | 0.4474 | Medium | 0.0885 | 0.0494 |
| share_kerendia_Covered_with_PA_ST | 0.4879 | 0.4699 | 0.4162 | 0.4341 | Medium | 0.0838 | 0.0537 |
| share_has_PA | 0.4966 | 0.4716 | 0.4204 | 0.4417 | Medium | 0.0796 | 0.0512 |
| share_commercial | 0.5791 | 0.508 | 0.5301 | 0.5669 | High | 0.0669 | 0.0589 |
| share_kerendia_worse_than_jardiance | 0.487 | 0.4739 | 0.4332 | 0.4424 | Medium | 0.0668 | 0.0407 |
| share_kerendia_Covered | 0.5505 | 0.5129 | 0.5438 | 0.5663 | High | 0.0663 | 0.0534 |
| share_has_ST | 0.5295 | 0.4821 | 0.4446 | 0.4757 | Medium | 0.0554 | 0.0375 |
| share_kerendia_Preferred | 0.4726 | 0.4677 | 0.4459 | 0.473 | Medium | 0.0541 | 0.0271 |
| share_ckd_pa_ars_R | 0.541 | 0.4839 | 0.4498 | 0.4863 | Medium | 0.0502 | 0.0365 |
| share_top3_pbm | 0.4829 | 0.4706 | 0.4678 | 0.4652 | High | 0.0348 | 0.0054 |
| share_step_requires_sglt2 | 0.5749 | 0.4797 | 0.4659 | 0.5283 | Medium | 0.0341 | 0.0624 |
| share_hpm_unrestricted | 0.5106 | 0.5287 | 0.5162 | 0.5088 | Low | 0.0287 | 0.0199 |
| share_kerendia_Not_Covered | 0.5195 | 0.5036 | 0.5058 | 0.5195 | High | 0.0195 | 0.0159 |
| share_hpm_pa_to_label | 0.5117 | 0.5149 | 0.5103 | 0.5058 | Low | 0.0149 | 0.0091 |
| share_kerendia_improved_l3m | 0.5119 | 0.4989 | 0.4984 | 0.5113 | High | 0.0113 | 0.0129 |
| share_hpm_step | 0.5074 | 0.5049 | 0.5039 | 0.5058 | High | 0.0058 | 0.0019 |
| share_kerendia_worsened_l3m | 0.5012 | 0.5 | 0.4993 | 0.501 | High | 0.001 | 0.0017 |

### Interpretation

* **Restriction features are strongly informative, but inversely.** `share_any_restriction` (AUC 0.43 overall, 0.38 in Medium) and `share_has_QL` (AUC 0.45, 0.39 in Medium) are the most discriminating features by distance of AUC from 0.5. A higher share of restricted claims predicts fewer new patients the next month, which makes clinical sense: restrictions are barriers to new prescribing. The model should include these features and let the learner use their inverse signal.
* **`share_commercial` is the most robust positive predictor across all terciles** (AUC 0.51 Low, 0.53 Medium, 0.57 High). Its signal strengthens in the High restriction tercile, where the commercial vs Medicare mix may determine whether a PA or step is successfully navigated.
* **`share_step_requires_sglt2` loses most of its signal within terciles** (0.47-0.53 vs 0.575 overall). Its pooled AUC was inflated by correlation with HCP volume: high-volume HCPs tend to have both more step-therapy claims and more new patients. It still has moderate signal in the High tercile (0.53).
* **PA and ST type flags are inversely predictive in Medium and High terciles** (`share_has_PA` AUC 0.42-0.44, `share_has_ST` 0.44-0.48, `share_ckd_pa_ars_R` 0.45-0.49). Within HCPs who face restrictions, knowing the specific type of restriction adds moderate discrimination.
* **Caveat: restricted-claim count is correlated with HCP total volume** (median 27 total claims in High vs 2 in Low). The NBRx rate difference across terciles (3% vs 26%) is driven as much by volume as by restriction exposure. The stratified AUC addresses this partly, but controlling for volume in the multivariate model remains essential.

## 6. Stratified AUC by HCP Kerendia NBRx tercile

**Question:** Do the access features still separate next-month NBRx once HCPs are grouped by how much new-patient Kerendia prescribing they already do?

**Method:**
* **Primary strata (no overlap with the target):** each HCP's count of new Kerendia patients in a pre-window baseline, **202504-202509** (6 months, at least 7 months of lookback from 202409 for the new-patient definition). Features and target are measured in 202510-202607, so the strata come before them.
* **Sensitivity strata (overlaps the target):** each HCP's new-patient count inside the feature window, 202510-202607. This includes the same months as the target, so it is shown only as a robustness check.
* Population: the same 59,392 HCPs and 289,232 HCP-months as Sections 2 and 5.
* **Tercile method: zero vs median split for both versions.** 70.5% of HCPs had zero baseline NBRx (47.6% in-window), so equal-size quantile terciles were not possible. Low = 0 NBRx; Medium and High split the remaining HCPs at the median. The terciles are therefore unequal in size.

### 6.1 Primary: baseline NBRx terciles (202504-202509)

| Tercile | HCPs | NBRx per HCP (min-max) | Median NBRx | Median total claims (window) | HCP-months | Next-month NBRx rate % |
| --- | --- | --- | --- | --- | --- | --- |
| Low | 41,861 | 0-0 | 0 | 4 | 154,254 | 8.05 |
| Medium | 11,405 | 1-2 | 1 | 14 | 77,289 | 17.41 |
| High | 6,126 | 3-157 | 5 | 68 | 57,689 | 43.64 |

| Feature | AUC overall | AUC Low | AUC Medium | AUC High | Strongest tercile | Max distance from 0.5 | AUC range across terciles |
| --- | --- | --- | --- | --- | --- | --- | --- |
| share_commercial | 0.5791 | 0.5417 | 0.5334 | 0.5238 | Low | 0.0417 | 0.0179 |
| share_step_requires_sglt2 | 0.5749 | 0.5232 | 0.5362 | 0.5388 | High | 0.0388 | 0.0156 |
| share_any_restriction | 0.4311 | 0.4624 | 0.4666 | 0.4711 | Low | 0.0376 | 0.0087 |
| share_has_QL | 0.4498 | 0.4707 | 0.4772 | 0.4823 | Low | 0.0293 | 0.0116 |
| share_ckd_pa_ars_R | 0.541 | 0.5196 | 0.5245 | 0.5168 | Medium | 0.0245 | 0.0077 |
| share_kerendia_Preferred | 0.4726 | 0.483 | 0.4791 | 0.4893 | Medium | 0.0209 | 0.0102 |
| share_medicare | 0.4834 | 0.4802 | 0.4928 | 0.505 | Low | 0.0198 | 0.0248 |
| share_has_ST | 0.5295 | 0.5163 | 0.5192 | 0.5101 | Medium | 0.0192 | 0.0091 |
| share_kerendia_Covered | 0.5505 | 0.5174 | 0.5158 | 0.5182 | High | 0.0182 | 0.0024 |
| share_kerendia_Not_Covered | 0.5195 | 0.5058 | 0.5067 | 0.5171 | High | 0.0171 | 0.0113 |
| share_top3_pbm | 0.4829 | 0.4927 | 0.4877 | 0.4875 | High | 0.0125 | 0.0052 |
| share_kerendia_improved_l3m | 0.5119 | 0.5028 | 0.504 | 0.5123 | High | 0.0123 | 0.0095 |
| share_hpm_pa_to_label | 0.5117 | 0.5117 | 0.5071 | 0.5049 | Low | 0.0117 | 0.0068 |
| share_hpm_unrestricted | 0.5106 | 0.5114 | 0.5055 | 0.5033 | Low | 0.0114 | 0.0081 |
| share_kerendia_worse_than_jardiance | 0.487 | 0.4916 | 0.4956 | 0.4951 | Low | 0.0084 | 0.004 |
| share_kerendia_Covered_with_PA_ST | 0.4879 | 0.4938 | 0.4976 | 0.4966 | Low | 0.0062 | 0.0038 |
| share_hpm_step | 0.5074 | 0.5052 | 0.5027 | 0.5057 | High | 0.0057 | 0.003 |
| share_has_PA | 0.4966 | 0.4967 | 0.5015 | 0.5015 | Low | 0.0033 | 0.0048 |
| share_kerendia_worsened_l3m | 0.5012 | 0.5004 | 0.5002 | 0.5012 | High | 0.0012 | 0.001 |

### 6.2 Sensitivity: in-window NBRx terciles (202510-202607)

| Tercile | HCPs | NBRx per HCP (min-max) | Median NBRx | Median total claims (window) | HCP-months | Next-month NBRx rate % |
| --- | --- | --- | --- | --- | --- | --- |
| Low | 28,249 | 0-0 | 0 | 4 | 107,511 | 0.37 |
| Medium | 20,617 | 1-2 | 1 | 5 | 90,422 | 9.95 |
| High | 10,526 | 3-307 | 5 | 43 | 91,299 | 45.61 |

| Feature | AUC overall | AUC Low | AUC Medium | AUC High | Max distance from 0.5 |
| --- | --- | --- | --- | --- | --- |
| share_hpm_unrestricted | 0.5106 | 0.6695 | 0.5059 | 0.4954 | 0.1695 |
| share_hpm_pa_to_label | 0.5117 | 0.6659 | 0.5053 | 0.4974 | 0.1659 |
| share_top3_pbm | 0.4829 | 0.4541 | 0.5146 | 0.4911 | 0.0459 |
| share_has_ST | 0.5295 | 0.5392 | 0.5052 | 0.5035 | 0.0392 |
| share_step_requires_sglt2 | 0.5749 | 0.4655 | 0.509 | 0.5283 | 0.0345 |
| share_ckd_pa_ars_R | 0.541 | 0.5345 | 0.5075 | 0.5092 | 0.0345 |
| share_any_restriction | 0.4311 | 0.4741 | 0.4978 | 0.4788 | 0.0259 |
| share_commercial | 0.5791 | 0.5087 | 0.5117 | 0.5173 | 0.0173 |
| Other features | | | | | below 0.03 |

The in-window Low tercile is not interpretable. Its HCPs have no new patients through 202607 by definition, so a positive target can only occur in 202608 (0.37% rate, about 400 positives). The 0.67 HPM AUCs come from this: HPM exists only from 202601, so it lines up with the one month where positives are possible. Use the primary version.

### 6.3 Interpretation

* **Within NBRx terciles, every access feature moves close to 0.5** (the largest distance from 0.5 is 0.04, compared with 0.08 pooled). Most of the pooled access AUC comes from differences between HCPs with different prescribing levels. Once baseline prescribing is fixed, access features add only a small signal.
* **`share_step_requires_sglt2` is the most stable access signal** (AUC 0.52 / 0.54 / 0.54, strongest in the High tercile). Unlike in the restriction-tercile study, it keeps its direction in every stratum. That makes it the best candidate for a true access effect: Kerendia sitting behind an SGLT2 step.
* **`share_commercial` keeps a positive signal in every tercile** (0.54 / 0.53 / 0.52), strongest among the lowest prescribers.
* **The inverse restriction signal is much weaker here** (`share_any_restriction` 0.46-0.47, `share_has_QL` 0.47-0.48) than in the restriction-tercile study (0.38-0.41). Part of that earlier signal was mechanical: at a fixed restricted-claim count, a lower restriction share means more total claims, and more claims means more NBRx. The direction (more restriction, less NBRx) still holds in every NBRx tercile, so it is a real but small effect.
* **`share_has_PA`, HPM groups and status-change flags are flat** (0.50-0.51) within NBRx terciles. `share_ckd_pa_ars_R` and `share_has_ST` are slightly positive (0.51-0.52). The reason has not been tested; one possibility is overlap with plan channel, which should be checked in the multivariate model.
* **Volume caveat still applies:** median window claims rise from 4 (Low) to 68 (High), so NBRx terciles also stratify volume. The NBRx rate gap (8% to 44%) is a prescribing-level effect, not an access effect.
