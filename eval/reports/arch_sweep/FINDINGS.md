# Findings — architecture sweep on the own test sheets (15 Nov 2026)

45 phone photos written by the user (15 OMR, 15 handwritten MCQ, 15 MCQ + numerical), labels in
`eval/test_papers/labels/`. Every live model was run once per sheet; 11,444 reader × grader ×
architecture combinations were scored offline. Full ranking: [README.md](README.md), all rows: `results.csv`,
numerical graders on the labelled values: [grader_check.md](grader_check.md).

**Main metric = silent errors**: answers accepted without a TA whose marks are wrong.

## Recommended architecture per pattern

| pattern | architecture | silent errors | auto-accepted | to TA | s / sheet |
|---|---|---|---|---|---|
| OMR (300) | **template OMR + Qwen reads the page; disagree → TA** | 0 | 99.7 % | 1 | 17 |
| handwritten MCQ (150) | **whole page: Gemma + Qwen, GLM-OCR page as 3rd vote (majority)** | 0 | 98 % | 3 | 34 |
| MCQ + numerical (75) | **same as MCQ** (Gemma + Qwen + GLM-OCR page, majority) | 0 | 97.3 % | 2 | 18 |
| *current pipeline (crop: Qwen A, Paddle B, GLM tie-break)* | MCQ / MCQ+num | 0 / 0 | 85 % / 57 % | 22 / 32 | 32 / 21 |

The current crop-based pipeline is safe (no silent errors) but sends far more to TAs. Reading the
**whole page** in one call beats segment-then-crop for short "1. B" sheets: segmentation crops lose context
(a label `3.` merged with `50` became `3.50`) and Gemma refuses to answer on single-letter crops (85 % "unclear").
Single sources with 0 silent errors exist (Gemma page on MCQ+num, Qwen page on OMR) but one model with no
cross-check is a single point of failure; the recommended rows keep two families agreeing.

## What the sweep found

1. **OMR:** template OMR (no GPU, ~2 s) and Qwen page reading are both perfect here; Gemma misreads bubbles
   (57 / 300) and the legacy OpenCV engine fails (83 / 300). Partial fills: every filled bubble ≥ 0.46 darkness,
   every empty ≤ 0.07 — partial fills are marked, as required.
2. **Ghost answers from show-through**: on blank answer sheets (2A_s05, 2A_s03 Q2, 2B_s05) up to 9 readers "read"
   the faint mirrored letters from the back. The blank-page detector does not catch these (the printed question
   numbers count as ink); whole-page Gemma/Qwen do not fall for it (prompt says to ignore show-through).
3. **`9J` read as `95`** by PaddleOCR, GLM-OCR and Chandra on crops — a silent wrong mark if two of them pair up.
4. **Numerical grader:** Gemma agrees with the code rule on all 45 labelled values; **Qwen gives marks outside
   the tolerance** (`19.61` for 19.6 ± 0.001, `0.505` for 0.5). Keep the code rule; Gemma is an acceptable
   second opinion, Qwen is not.
5. **Direct grading** (VLM reads and grades in one call) is perfect on MCQ but makes 3 (Gemma) / 11 (Qwen)
   errors on numbers — reading in a VLM and grading in code is safer.
6. **Quality gate too strict for phone photos:** 9 of 30 handwritten photos fail on "glare" (lamp light /
   vignetting) although every reader handled them; in the live pipeline those whole sheets would go to a TA.
7. **Parser bugs fixed during the sweep** (affected the live pipeline too): label stripping ate the integer part
   of decimals (`3. 4.01` → `01`) and kept a comma label (`4, 440 W`). Both fixed with tests.

## Limits

45 sheets, one writer (the user), 525 answers; a "0 silent errors" here is not a guarantee. Nanonets-OCR2 and
gpt-oss were not loaded in this GPU job, so they are not in the sweep. Page-level OCR parsing needs the
question number at the start of each line (2C_s05 OCR output had none → all empty).

## Proposed next steps (not done — need the user's go-ahead)

- Switch handwritten MCQ / numerical reading to whole-page Gemma + Qwen + GLM-OCR majority; keep crop
  reading for subjective answers.
- OMR: template primary + Qwen page cross-check.
- Loosen the glare threshold for phone photos; detect show-through ghosts (mirrored text) on blank sheets.
