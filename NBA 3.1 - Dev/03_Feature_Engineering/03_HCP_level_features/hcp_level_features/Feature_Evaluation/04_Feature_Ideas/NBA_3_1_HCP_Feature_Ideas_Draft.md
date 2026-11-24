# NBA 3.1 — HCP Feature Ideas (Draft for discussion)

**Purpose:** Candidate new or reworked HCP-level features, based on the source reviews, the NBA 3.0 model evaluation and the new Kerendia indications. These are proposals; none has been built or tested.
**Date:** 2026-11-23
**Inputs:** `../01_Source_Review/`, `../02_NBA_3_0_Model_Evaluation/NBA_3_0_Model_Feature_Evaluation.md`, `../03_Claims_Feature_Review/NBA_3_1_HCP_Claims_Feature_Review.md`

Indications in scope: T2D + CKD (2021), HF with LVEF ≥ 40% (July 2025), T1D + CKD (Sept 2026).

---

## 1. Ideas

| # | Idea | Source | Grain | Why | Risk |
| --- | --- | --- | --- | --- | --- |
| F1 | Split Kerendia claims into paid / rejected / reversed counts and a rejection rate | Rx (`CLAIM_TYPE`) | HCP × month | Rejected Kerendia claims rank 7 in 3.0; fixes RX-A and matches the PD-only target | Needs NB01/NB05 rework |
| F2 | HF-eligible patient count (I50 + HFpEF proxy, no dialysis) per HCP | Dx, Px | HCP × month | New indication; I50 patients 7.78M in 2025 | HFpEF proxy is imprecise; Jan 2023 step |
| F3 | T1D + CKD patient count per HCP | Dx (E10 + N18) | HCP × month | New indication (Sept 2026); E10 ~1.4M patients/yr | Little post-approval history to learn from |
| F4 | Potassium monitoring: share of CKD patients with a K+ test, and share with high K+ | Lab (LabCorp only) | HCP × month | K+ is a key MRA safety check; only LabCorp has it | LabCorp patient IDs missing pre-2025-08 |
| F5 | HbA1c-tested share of CKD patients | Lab (LabCorp only) | HCP × month | Marks diabetes management intensity | Same LabCorp gap |
| F6 | UACR testing rate among T2D-CKD patients | Lab (Quest + LabCorp) | HCP × month | Guideline-driven screening; signals CKD-aware HCP | Lab reload dedup (S3) needed first |
| F7 | SGLT2 + no-MRA patients (SGLT2 on board, no Kerendia) | Rx | HCP × month | Natural add-on pool; add-on SOB cluster carries 1.40% SHAP | Overlaps existing SGLT2 features |
| F8 | Single F2F recency + one window instead of five F2F windows | Calls | HCP × month | Five F2F windows in the 3.0 top 20; reduces redundancy | Non-claims; check with promotion owners |
| F9 | Data-completeness flag for the latest month | Dx, Px | HCP × month | Oct 2026 is thin in Dx/Px (DX-B, PX-D) | Adds a non-clinical feature |
| F10 | Pre/post Jan 2023 coverage flag, or growth features that start in 2023 only | Dx, Px | HCP | Avoids the Jan 2023 step (DX-A) | Loses 2021–2022 history |

## 2. Suggested order

1. **F1** (fixes a known bug and keeps a top-10 signal).
2. **F2, F3** (new indications; the 3.0 model has no HF- or T1D-specific feature in its top 20; 3.1 NB coverage not checked).
3. **F4, F6** (lab signal, after the S3 dedup rule is set).
4. **F8, F10** (clean-up and redundancy).

## 3. Open questions

* Should F2/F3 be counts, shares of the HCP's CKD panel, or both?
* Is the HFpEF proxy good enough, or do we need echo/procedure codes?
* Should features for the new indications be trained only on post-approval months?
