Hi Team,

 

Sharing the EOD updates from the Argentina Team for October 28th, 2026.

 

Goal. Make the 3.0 patient lab query dynamic, so adding a test or changing a rule is a file edit and not a SQL edit. The 3.0 query is untouched as a baseline.

What we did. Four steps, each compared with the one before it.

Step 1: inventory of the 15 hardcoded parts of the 3.0 query. Review only.
Step 2: test rules (LOINC codes, units, valid ranges, stage cut-offs, same-day priority) moved to our copy of Kerendia_Lab_Final.csv, one row per code. UACR parts are no longer staged, and eGFR 150-200 is now stage 1.
Step 3: run settings (dates, specialties, table names) moved to a LAB_CONFIG block (temporary, later could be in 00_config). Same output, with 19% less data pulled from Snowflake (312.9M to 252.2M rows).
Step 4: better value parsing (lab flags like 75^ are read, and above/below values like >120 are kept when the stage is certain), plus a dropped-rows report on every run.
What the comparisons showed (all US, 2025-01 to 2026-09)

99.9% of eGFR test-days are identical (106.73M), and UACR test-days are unchanged (19.81M).
55K eGFR test-days (0.05%) moved one stage, from the priority rule and the 150-200 fix.
Gained: +35.7K eGFR test-days (26.8K patients), from above/below values with a clear stage. A one-off check run from chat also found +75.7K in 2023-2024, from lab-flag values that only appear in 2023 data.
Lost: 260 eGFR test-days (outside the valid range) and about 70K UACR test-days (68.4K parts that aren’t a ratio, and 2.5K above 10,000).
Validation HCPs (2023-01 to 2026-09): no change at any step (225 patients, 6,139 patient-months).
Key insight from the dropped-rows report. The 3.0 query silently drops a large share of rows. Most is noise: 66M eGFR rows with no patient ID, 24M with no NPI, and 11M with text values like DNR. But the specialty filter alone drops 211M eGFR rows and 21M UACR rows, the largest cut, and it is real patient data. The 3.0 query already did this, and now we can see it. (Genie’s earlier total of about 370M doesn’t match the pieces above, so check the full breakdown before quoting it.)

Decisions made

eGFR valid max raised from 150 to 200.
The basket CSV is the single source of test rules. Sehar’s original is untouched.
The test-name backup is kept, so rows with no LOINC code are still found.
Same-day priority: the lowest PRIORITY number wins, and an exact value beats an above/below value.
Lab flags are read.
Decisions for the final review

Specialty filter. (a) Keep the 10 primary-care codes, (b) remove it, or (c) add cardiology, endocrinology and nephrology. Removing it adds about 16% more eGFR patients and 13% more UACR patients.
>60 eGFR (827K rows). Keep it out (conservative), or count it as “not stage 3+”.