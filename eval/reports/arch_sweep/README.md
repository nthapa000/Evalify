# Architecture sweep — own test sheets

Generated 2026-11-15 03:12 by `python eval/arch_sweep.py score`. Full table: `results.csv` (11444 rows). Per-sheet raw readings: `raw/<sheet>.json`.

**How to read this**

- *silent_errors*: auto-accepted answers whose marks are wrong (the number that matters — nobody checks them).
- *auto_rate*: share of answers accepted without a TA; *ta_items*: answers sent to a TA (assumed fixed).
- *final_accuracy*: marks-correct share after the TA fixes routed items. *read_exact_auto*: accepted value equals the label.
- Readers: `crop:<segmenter>><reader>` = segment then read the crop; `page><reader>` = whole page in one call; `direct><vlm>` = VLM reads and grades in one call; `omr:template` = learned bubble map; `omr:legacy` = old OpenCV engine.
- Architectures: `single`; `pair` (A and B must agree, else TA); `pair+tiebreak` (C asked only when one of A/B abstains — the current pipeline); `pair+majority` (C on any disagreement, 2 of 3 wins).
- Grader: `code` = deterministic rules (MCQ exact set; numbers exact value, unit ignored, no conversion); `qwen…`/`gemma…` = LLM decides numerical correctness (MCQ always code).

## omr (300 answers)

### Top 15 architectures

| arch | readers | grader | silent_errors | auto_rate | ta_items | final_accuracy | read_exact_auto | sec_per_sheet |
|---|---|---|---|---|---|---|---|---|
| single | direct>qwen | code | 0 | 1.0 | 0 | 1.0 | 0.993 | 13.3 |
| single | page>qwen | code | 0 | 1.0 | 0 | 1.0 | 1.0 | 15.0 |
| pair+majority | page>gemma + page>qwen + omr:template | code | 0 | 1.0 | 0 | 1.0 | 1.0 | 37.9 |
| pair+majority | omr:template + page>gemma + page>qwen | code | 0 | 1.0 | 0 | 1.0 | 1.0 | 39.1 |
| pair+tiebreak | omr:template + page>qwen + page>gemma | code | 0 | 1.0 | 0 | 1.0 | 1.0 | 39.1 |
| pair+majority | omr:template + page>qwen + page>gemma | code | 0 | 1.0 | 0 | 1.0 | 1.0 | 39.1 |
| single | omr:template | code | 0 | 0.997 | 1 | 1.0 | 1.0 | 1.8 |
| pair+majority | omr:legacy + page>qwen + omr:template | code | 0 | 0.997 | 1 | 1.0 | 1.0 | 16.4 |
| pair | omr:template + page>qwen | code | 0 | 0.997 | 1 | 1.0 | 1.0 | 16.7 |
| pair+majority | omr:legacy + omr:template + page>qwen | code | 0 | 0.997 | 1 | 1.0 | 1.0 | 16.7 |
| pair+tiebreak | omr:template + page>qwen + omr:legacy | code | 0 | 0.997 | 1 | 1.0 | 1.0 | 16.7 |
| pair+majority | omr:template + page>qwen + omr:legacy | code | 0 | 0.997 | 1 | 1.0 | 1.0 | 16.7 |
| pair+tiebreak | page>gemma + page>qwen + omr:template | code | 0 | 0.723 | 83 | 1.0 | 1.0 | 37.4 |
| pair+tiebreak | omr:template + page>gemma + page>qwen | code | 0 | 0.723 | 83 | 1.0 | 1.0 | 39.1 |
| pair | page>gemma + page>qwen | code | 0 | 0.717 | 85 | 1.0 | 1.0 | 37.4 |

### Every single source (one model, no cross-check)

| arch | readers | grader | silent_errors | auto_rate | ta_items | final_accuracy | read_exact_auto | sec_per_sheet |
|---|---|---|---|---|---|---|---|---|
| single | direct>qwen | code | 0 | 1.0 | 0 | 1.0 | 0.993 | 13.3 |
| single | page>qwen | code | 0 | 1.0 | 0 | 1.0 | 1.0 | 15.0 |
| single | omr:template | code | 0 | 0.997 | 1 | 1.0 | 1.0 | 1.8 |
| single | direct>gemma | code | 51 | 1.0 | 0 | 0.83 | 0.723 | 22.0 |
| single | page>gemma | code | 57 | 0.993 | 2 | 0.81 | 0.721 | 22.4 |
| single | omr:legacy | code | 83 | 0.993 | 2 | 0.7233 | 0.215 | 0.0 |

### Best per architecture × grader

| arch | readers | grader | silent_errors | auto_rate | ta_items | final_accuracy | read_exact_auto | sec_per_sheet |
|---|---|---|---|---|---|---|---|---|
| single | direct>qwen | code | 0 | 1.0 | 0 | 1.0 | 0.993 | 13.3 |
| pair+majority | page>gemma + page>qwen + omr:template | code | 0 | 1.0 | 0 | 1.0 | 1.0 | 37.9 |
| pair+tiebreak | omr:template + page>qwen + page>gemma | code | 0 | 1.0 | 0 | 1.0 | 1.0 | 39.1 |
| pair | omr:template + page>qwen | code | 0 | 0.997 | 1 | 1.0 | 1.0 | 16.7 |

### Hardest answers (single sources that got the marks wrong)

| sheet | Q | label | # wrong | readings |
|---|---|---|---|---|
| omr_L1_s01 | Q2 | C | 3 | direct>gemma=B; omr:legacy=A,B,C,D,E; page>gemma=B |
| omr_L1_s01 | Q3 | C | 3 | direct>gemma=B; omr:legacy=A,B,C,D,E; page>gemma=B |
| omr_L1_s01 | Q4 | B | 3 | direct>gemma=C; omr:legacy=A,B,C,D,E; page>gemma=∅ |
| omr_L1_s01 | Q8 | B | 3 | direct>gemma=A; omr:legacy=A,B,C,D; page>gemma=∅ |
| omr_L1_s01 | Q9 | B,D | 3 | direct>gemma=C; omr:legacy=A,B,C,D; page>gemma=C |
| omr_L1_s01 | Q19 | B | 3 | direct>gemma=C; omr:legacy=A,B,C,D; page>gemma=∅ |
| omr_L1_s02 | Q4 | B | 3 | direct>gemma=C; omr:legacy=A,B,C,D,E; page>gemma=C |
| omr_L1_s04 | Q2 | C | 3 | direct>gemma=D; omr:legacy=A,B,C,D,E; page>gemma=D |
| omr_L1_s04 | Q11 | C | 3 | direct>gemma=B; omr:legacy=A,B,C,D; page>gemma=B |
| omr_L1_s05 | Q8 | B | 3 | direct>gemma=A; omr:legacy=A,B,C,D; page>gemma=A |
| omr_L2_s01 | Q1 | B | 3 | direct>gemma=∅; omr:legacy=A; page>gemma=∅ |
| omr_L2_s01 | Q2 | C | 3 | direct>gemma=B,C; omr:legacy=A,B,C,D,E; page>gemma=B |
| omr_L2_s01 | Q5 | A,C | 3 | direct>gemma=B; omr:legacy=∅; page>gemma=∅ |
| omr_L2_s01 | Q7 | A | 3 | direct>gemma=B; omr:legacy=∅; page>gemma=∅ |
| omr_L2_s01 | Q8 | B | 3 | direct>gemma=∅; omr:legacy=∅; page>gemma=∅ |
| omr_L2_s01 | Q9 | B,D | 3 | direct>gemma=C,D; omr:legacy=∅; page>gemma=C,D |
| omr_L2_s01 | Q11 | C | 3 | direct>gemma=B,C; omr:legacy=∅; page>gemma=B,C |
| omr_L2_s01 | Q14 | B,D | 3 | direct>gemma=C; omr:legacy=∅; page>gemma=C |
| omr_L2_s01 | Q15 | A | 3 | direct>gemma=C; omr:legacy=∅; page>gemma=D |
| omr_L2_s01 | Q17 | A,B,D | 3 | direct>gemma=B,C; omr:legacy=∅; page>gemma=A,B,C |

## mcq (150 answers)

### Top 15 architectures

| arch | readers | grader | silent_errors | auto_rate | ta_items | final_accuracy | read_exact_auto | sec_per_sheet |
|---|---|---|---|---|---|---|---|---|
| single | direct>qwen | code | 0 | 1.0 | 0 | 1.0 | 0.98 | 13.0 |
| single | direct>gemma | code | 0 | 1.0 | 0 | 1.0 | 0.993 | 18.5 |
| pair+majority | page>glm + page>paddle + crop:gemma>glm | code | 0 | 0.98 | 3 | 1.0 | 0.966 | 1.9 |
| pair+majority | page>glm + page>paddle + crop:gemma>paddle | code | 0 | 0.98 | 3 | 1.0 | 0.966 | 1.9 |
| pair+majority | page>glm + page>paddle + crop:qwen>glm | code | 0 | 0.98 | 3 | 1.0 | 0.966 | 2.0 |
| single | crop:gemma>glm | code | 0 | 0.98 | 3 | 1.0 | 0.898 | 2.1 |
| pair+majority | page>glm + page>paddle + crop:qwen>paddle | code | 0 | 0.98 | 3 | 1.0 | 0.966 | 2.1 |
| pair+majority | crop:gemma>glm + page>glm + page>paddle | code | 0 | 0.98 | 3 | 1.0 | 0.966 | 3.9 |
| pair+majority | crop:gemma>glm + page>paddle + page>glm | code | 0 | 0.98 | 3 | 1.0 | 0.966 | 3.9 |
| pair+majority | crop:qwen>glm + page>glm + page>paddle | code | 0 | 0.98 | 3 | 1.0 | 0.966 | 4.7 |
| pair+majority | crop:qwen>glm + page>paddle + page>glm | code | 0 | 0.98 | 3 | 1.0 | 0.966 | 4.7 |
| pair+majority | crop:gemma>paddle + page>glm + page>paddle | code | 0 | 0.98 | 3 | 1.0 | 0.966 | 4.9 |
| pair+majority | crop:gemma>paddle + page>paddle + page>glm | code | 0 | 0.98 | 3 | 1.0 | 0.966 | 4.9 |
| pair+tiebreak | crop:gemma>glm + crop:gemma>paddle + crop:qwen>glm | code | 0 | 0.98 | 3 | 1.0 | 0.898 | 5.2 |
| pair+tiebreak | crop:gemma>glm + crop:gemma>paddle + crop:qwen>qwen | code | 0 | 0.98 | 3 | 1.0 | 0.898 | 5.2 |

### Every single source (one model, no cross-check)

| arch | readers | grader | silent_errors | auto_rate | ta_items | final_accuracy | read_exact_auto | sec_per_sheet |
|---|---|---|---|---|---|---|---|---|
| single | direct>qwen | code | 0 | 1.0 | 0 | 1.0 | 0.98 | 13.0 |
| single | direct>gemma | code | 0 | 1.0 | 0 | 1.0 | 0.993 | 18.5 |
| single | crop:gemma>glm | code | 0 | 0.98 | 3 | 1.0 | 0.898 | 2.1 |
| single | page>qwen | code | 0 | 0.98 | 3 | 1.0 | 1.0 | 14.6 |
| single | page>gemma | code | 0 | 0.98 | 3 | 1.0 | 1.0 | 18.0 |
| single | page>glm | code | 0 | 0.973 | 4 | 1.0 | 0.966 | 1.0 |
| single | crop:gemma>paddle | code | 0 | 0.973 | 4 | 1.0 | 0.897 | 3.1 |
| single | crop:qwen>paddle | code | 0 | 0.973 | 4 | 1.0 | 0.897 | 7.2 |
| single | crop:qwen>glm | code | 0 | 0.967 | 5 | 1.0 | 0.89 | 2.9 |
| single | crop:qwen>chandra | code | 0 | 0.9 | 15 | 1.0 | 0.889 | 23.6 |
| single | crop:gemma>gemma | code | 0 | 0.167 | 125 | 1.0 | 1.0 | 184.8 |
| single | crop:qwen>gemma | code | 0 | 0.147 | 128 | 1.0 | 1.0 | 205.7 |
| single | page>chandra | code | 1 | 0.96 | 6 | 0.9933 | 0.986 | 6.1 |
| single | crop:gemma>chandra | code | 1 | 0.933 | 10 | 0.9933 | 0.886 | 17.1 |
| single | page>paddle | code | 2 | 0.98 | 3 | 0.9867 | 0.952 | 0.8 |
| single | crop:qwen>qwen | code | 5 | 0.953 | 7 | 0.9667 | 0.93 | 24.8 |
| single | crop:gemma>qwen | code | 5 | 0.947 | 8 | 0.9667 | 0.951 | 20.9 |

### Best per architecture × grader

| arch | readers | grader | silent_errors | auto_rate | ta_items | final_accuracy | read_exact_auto | sec_per_sheet |
|---|---|---|---|---|---|---|---|---|
| single | direct>qwen | code | 0 | 1.0 | 0 | 1.0 | 0.98 | 13.0 |
| pair+majority | page>glm + page>paddle + crop:gemma>glm | code | 0 | 0.98 | 3 | 1.0 | 0.966 | 1.9 |
| pair+tiebreak | crop:gemma>glm + crop:gemma>paddle + crop:qwen>glm | code | 0 | 0.98 | 3 | 1.0 | 0.898 | 5.2 |
| pair | page>gemma + page>qwen | code | 0 | 0.98 | 3 | 1.0 | 1.0 | 32.6 |

### Hardest answers (single sources that got the marks wrong)

| sheet | Q | label | # wrong | readings |
|---|---|---|---|---|
| mcq_s03 | Q4 | A,C,D | 2 | crop:gemma>qwen=∅; crop:qwen>qwen=∅ |
| mcq_s09 | Q4 | A,C,D | 2 | crop:gemma>qwen=∅; crop:qwen>qwen=∅ |
| mcq_s10 | Q1 | B | 2 | crop:qwen>qwen=∅; page>paddle=∅ |
| mcq_s10 | Q4 | A,C,D | 1 | crop:gemma>chandra=D |
| mcq_s07 | Q3 | B | 1 | crop:gemma>qwen=∅ |
| mcq_s09 | Q7 | 4 | 1 | crop:gemma>qwen=D |
| mcq_s09 | Q8 | A,C,D | 1 | crop:gemma>qwen=∅ |
| mcq_s05 | Q5 | C | 1 | crop:qwen>qwen=∅ |
| mcq_s13 | Q9 | B | 1 | crop:qwen>qwen=∅ |
| mcq_s13 | Q4 | A,C,D | 1 | page>chandra=A,C,D,E |
| mcq_s11 | Q1 | B | 1 | page>paddle=∅ |

## mcqnum (75 answers)

### Top 15 architectures

| arch | readers | grader | silent_errors | auto_rate | ta_items | final_accuracy | read_exact_auto | sec_per_sheet |
|---|---|---|---|---|---|---|---|---|
| single | page>gemma | code | 0 | 1.0 | 0 | 1.0 | 0.973 | 8.9 |
| single | page>gemma | gemma4-31b-fp8 | 0 | 1.0 | 0 | 1.0 | 0.973 | 8.9 |
| pair+majority | page>chandra + page>gemma + page>qwen | code | 0 | 0.987 | 1 | 1.0 | 0.986 | 21.7 |
| pair+majority | page>chandra + page>qwen + page>gemma | code | 0 | 0.987 | 1 | 1.0 | 0.986 | 21.7 |
| pair+majority | page>gemma + page>qwen + page>chandra | code | 0 | 0.987 | 1 | 1.0 | 0.986 | 21.7 |
| pair+majority | page>chandra + page>gemma + page>qwen | gemma4-31b-fp8 | 0 | 0.987 | 1 | 1.0 | 0.986 | 21.7 |
| pair+majority | page>chandra + page>qwen + page>gemma | gemma4-31b-fp8 | 0 | 0.987 | 1 | 1.0 | 0.986 | 21.7 |
| pair+majority | page>gemma + page>qwen + page>chandra | gemma4-31b-fp8 | 0 | 0.987 | 1 | 1.0 | 0.986 | 21.7 |
| single | page>qwen | gemma4-31b-fp8 | 0 | 0.973 | 2 | 1.0 | 0.945 | 8.3 |
| pair+majority | page>gemma + page>glm + page>qwen | code | 0 | 0.973 | 2 | 1.0 | 0.986 | 18.4 |
| pair+majority | page>gemma + page>qwen + page>glm | code | 0 | 0.973 | 2 | 1.0 | 0.986 | 18.4 |
| pair+majority | page>glm + page>qwen + page>gemma | code | 0 | 0.973 | 2 | 1.0 | 0.986 | 18.4 |
| pair+majority | page>gemma + page>glm + page>qwen | gemma4-31b-fp8 | 0 | 0.973 | 2 | 1.0 | 0.986 | 18.4 |
| pair+majority | page>gemma + page>qwen + page>glm | gemma4-31b-fp8 | 0 | 0.973 | 2 | 1.0 | 0.986 | 18.4 |
| pair+majority | page>glm + page>qwen + page>gemma | gemma4-31b-fp8 | 0 | 0.973 | 2 | 1.0 | 0.986 | 18.4 |

### Every single source (one model, no cross-check)

| arch | readers | grader | silent_errors | auto_rate | ta_items | final_accuracy | read_exact_auto | sec_per_sheet |
|---|---|---|---|---|---|---|---|---|
| single | page>gemma | code | 0 | 1.0 | 0 | 1.0 | 0.973 | 8.9 |
| single | page>gemma | gemma4-31b-fp8 | 0 | 1.0 | 0 | 1.0 | 0.973 | 8.9 |
| single | page>qwen | gemma4-31b-fp8 | 0 | 0.973 | 2 | 1.0 | 0.945 | 8.3 |
| single | crop:qwen>glm | code | 0 | 0.813 | 14 | 1.0 | 0.852 | 2.3 |
| single | crop:qwen>glm | gemma4-31b-fp8 | 0 | 0.813 | 14 | 1.0 | 0.852 | 2.3 |
| single | crop:qwen>gemma | code | 0 | 0.213 | 59 | 1.0 | 0.938 | 100.0 |
| single | crop:qwen>gemma | qwen38-27b-fp8 | 0 | 0.213 | 59 | 1.0 | 0.938 | 100.0 |
| single | crop:qwen>gemma | gemma4-31b-fp8 | 0 | 0.213 | 59 | 1.0 | 0.938 | 100.0 |
| single | crop:gemma>gemma | code | 0 | 0.187 | 61 | 1.0 | 0.929 | 95.5 |
| single | crop:gemma>gemma | qwen38-27b-fp8 | 0 | 0.187 | 61 | 1.0 | 0.929 | 95.5 |
| single | crop:gemma>gemma | gemma4-31b-fp8 | 0 | 0.187 | 61 | 1.0 | 0.929 | 95.5 |
| single | page>qwen | code | 1 | 0.973 | 2 | 0.9867 | 0.945 | 8.3 |
| single | page>gemma | qwen38-27b-fp8 | 2 | 1.0 | 0 | 0.9733 | 0.973 | 8.9 |
| single | page>qwen | qwen38-27b-fp8 | 2 | 0.973 | 2 | 0.9733 | 0.945 | 8.3 |
| single | crop:qwen>glm | qwen38-27b-fp8 | 2 | 0.813 | 14 | 0.9733 | 0.852 | 2.3 |
| single | direct>gemma | code | 3 | 1.0 | 0 | 0.96 | 0.947 | 9.0 |
| single | direct>gemma | qwen38-27b-fp8 | 3 | 1.0 | 0 | 0.96 | 0.947 | 9.0 |
| single | direct>gemma | gemma4-31b-fp8 | 3 | 1.0 | 0 | 0.96 | 0.947 | 9.0 |
| single | crop:gemma>glm | code | 3 | 0.867 | 10 | 0.96 | 0.8 | 1.3 |
| single | crop:gemma>glm | gemma4-31b-fp8 | 3 | 0.867 | 10 | 0.96 | 0.8 | 1.3 |
| single | crop:qwen>paddle | code | 3 | 0.813 | 14 | 0.96 | 0.836 | 4.9 |
| single | crop:qwen>paddle | gemma4-31b-fp8 | 3 | 0.813 | 14 | 0.96 | 0.836 | 4.9 |
| single | crop:qwen>chandra | code | 4 | 0.907 | 7 | 0.9467 | 0.765 | 13.0 |
| single | crop:qwen>chandra | gemma4-31b-fp8 | 4 | 0.907 | 7 | 0.9467 | 0.765 | 13.0 |
| single | crop:qwen>paddle | qwen38-27b-fp8 | 4 | 0.813 | 14 | 0.9467 | 0.836 | 4.9 |
| single | crop:gemma>paddle | code | 4 | 0.8 | 15 | 0.9467 | 0.833 | 2.3 |
| single | crop:gemma>paddle | gemma4-31b-fp8 | 4 | 0.8 | 15 | 0.9467 | 0.833 | 2.3 |
| single | crop:qwen>qwen | code | 4 | 0.613 | 29 | 0.9467 | 0.848 | 15.0 |
| single | crop:qwen>qwen | qwen38-27b-fp8 | 4 | 0.613 | 29 | 0.9467 | 0.848 | 15.0 |
| single | crop:qwen>qwen | gemma4-31b-fp8 | 4 | 0.613 | 29 | 0.9467 | 0.848 | 15.0 |
| single | crop:gemma>chandra | code | 5 | 0.893 | 8 | 0.9333 | 0.746 | 12.0 |
| single | crop:gemma>chandra | gemma4-31b-fp8 | 5 | 0.893 | 8 | 0.9333 | 0.746 | 12.0 |
| single | crop:gemma>glm | qwen38-27b-fp8 | 5 | 0.867 | 10 | 0.9333 | 0.8 | 1.3 |
| single | crop:gemma>paddle | qwen38-27b-fp8 | 5 | 0.8 | 15 | 0.9333 | 0.833 | 2.3 |
| single | crop:qwen>chandra | qwen38-27b-fp8 | 6 | 0.907 | 7 | 0.92 | 0.765 | 13.0 |
| single | page>glm | code | 6 | 0.893 | 8 | 0.92 | 0.866 | 1.2 |
| single | page>glm | gemma4-31b-fp8 | 6 | 0.893 | 8 | 0.92 | 0.866 | 1.2 |
| single | crop:gemma>qwen | code | 6 | 0.653 | 26 | 0.92 | 0.816 | 13.9 |
| single | crop:gemma>qwen | qwen38-27b-fp8 | 6 | 0.653 | 26 | 0.92 | 0.816 | 13.9 |
| single | crop:gemma>qwen | gemma4-31b-fp8 | 6 | 0.653 | 26 | 0.92 | 0.816 | 13.9 |
| single | page>chandra | code | 7 | 0.92 | 6 | 0.9067 | 0.855 | 4.5 |
| single | page>chandra | gemma4-31b-fp8 | 7 | 0.92 | 6 | 0.9067 | 0.855 | 4.5 |
| single | crop:gemma>chandra | qwen38-27b-fp8 | 7 | 0.893 | 8 | 0.9067 | 0.746 | 12.0 |
| single | page>chandra | qwen38-27b-fp8 | 8 | 0.92 | 6 | 0.8933 | 0.855 | 4.5 |
| single | page>glm | qwen38-27b-fp8 | 8 | 0.893 | 8 | 0.8933 | 0.866 | 1.2 |
| single | page>paddle | code | 10 | 0.92 | 6 | 0.8667 | 0.754 | 1.1 |
| single | page>paddle | gemma4-31b-fp8 | 10 | 0.92 | 6 | 0.8667 | 0.754 | 1.1 |
| single | direct>qwen | code | 11 | 1.0 | 0 | 0.8533 | 0.853 | 8.2 |
| single | direct>qwen | qwen38-27b-fp8 | 11 | 1.0 | 0 | 0.8533 | 0.853 | 8.2 |
| single | direct>qwen | gemma4-31b-fp8 | 11 | 1.0 | 0 | 0.8533 | 0.853 | 8.2 |
| single | page>paddle | qwen38-27b-fp8 | 11 | 0.92 | 6 | 0.8533 | 0.754 | 1.1 |

### Best per architecture × grader

| arch | readers | grader | silent_errors | auto_rate | ta_items | final_accuracy | read_exact_auto | sec_per_sheet |
|---|---|---|---|---|---|---|---|---|
| single | page>gemma | code | 0 | 1.0 | 0 | 1.0 | 0.973 | 8.9 |
| single | page>gemma | gemma4-31b-fp8 | 0 | 1.0 | 0 | 1.0 | 0.973 | 8.9 |
| pair+majority | page>chandra + page>gemma + page>qwen | code | 0 | 0.987 | 1 | 1.0 | 0.986 | 21.7 |
| pair+majority | page>chandra + page>gemma + page>qwen | gemma4-31b-fp8 | 0 | 0.987 | 1 | 1.0 | 0.986 | 21.7 |
| pair+tiebreak | page>gemma + page>qwen + page>glm | code | 0 | 0.947 | 4 | 1.0 | 0.986 | 18.4 |
| pair+tiebreak | page>gemma + page>qwen + page>glm | gemma4-31b-fp8 | 0 | 0.947 | 4 | 1.0 | 0.986 | 18.4 |
| pair | page>gemma + page>qwen | code | 0 | 0.92 | 6 | 1.0 | 0.986 | 17.3 |
| pair | page>gemma + page>qwen | gemma4-31b-fp8 | 0 | 0.92 | 6 | 1.0 | 0.986 | 17.3 |
| pair+majority | crop:qwen>paddle + page>chandra + crop:qwen>gemma | qwen38-27b-fp8 | 0 | 0.693 | 23 | 1.0 | 0.981 | 59.3 |
| pair+tiebreak | crop:qwen>paddle + page>chandra + page>paddle | qwen38-27b-fp8 | 0 | 0.68 | 24 | 1.0 | 0.98 | 10.5 |
| pair | crop:qwen>paddle + page>chandra | qwen38-27b-fp8 | 0 | 0.547 | 34 | 1.0 | 1.0 | 9.4 |
| single | crop:qwen>gemma | qwen38-27b-fp8 | 0 | 0.213 | 59 | 1.0 | 0.938 | 100.0 |

### Hardest answers (single sources that got the marks wrong)

| sheet | Q | label | # wrong | readings |
|---|---|---|---|---|
| 2A_s05 | Q2 | ∅ | 9 | crop:gemma>chandra=A; crop:gemma>glm=A; crop:gemma>paddle=A; crop:gemma>qwen=A; crop:qwen>chandra=A; crop:qwen>paddle=A |
| 2C_s05 | Q5 | 9J | 8 | crop:gemma>chandra=95; crop:gemma>glm=95; crop:gemma>paddle=95; crop:qwen>chandra=95; crop:qwen>paddle=95; page>chandra=∅ |
| 2A_s05 | Q1 | ∅ | 6 | crop:gemma>paddle=A; crop:qwen>chandra=A; crop:qwen>paddle=A; direct>gemma=A; direct>qwen=A; page>paddle=A |
| 2A_s03 | Q1 | A | 4 | crop:qwen>qwen=∅; page>chandra=∅; page>glm=∅; page>paddle=∅ |
| 2A_s03 | Q2 | ∅ | 3 | crop:gemma>chandra=A; crop:gemma>glm=A; crop:gemma>paddle=A |
| 2C_s05 | Q1 | C | 3 | page>chandra=∅; page>glm=∅; page>paddle=∅ |
| 2C_s05 | Q2 | B | 3 | page>chandra=∅; page>glm=∅; page>paddle=∅ |
| 2C_s05 | Q3 | 0.5A | 3 | page>chandra=∅; page>glm=∅; page>paddle=∅ |
| 2C_s05 | Q4 | 440W | 3 | page>chandra=∅; page>glm=∅; page>paddle=∅ |
| 2C_s01 | Q5 | 9J | 2 | crop:gemma>chandra=95; crop:qwen>chandra=95 |
| 2A_s01 | Q3 | 50km/hr | 2 | crop:gemma>qwen=∅; crop:qwen>qwen=3.50 km/hr |
| 2B_s05 | Q1 | ∅ | 2 | direct>gemma=B; direct>qwen=B |
| 2A_s04 | Q4 | 2500m | 2 | page>chandra=∅; page>paddle=∅ |
| 2B_s03 | Q3 | -4g/cm3 | 1 | crop:gemma>chandra=4 \text{ g/cm}^3 |
| 2A_s02 | Q3 | 50km/hr | 1 | crop:gemma>qwen=∅ |
| 2B_s01 | Q4 | -7C | 1 | crop:gemma>qwen=∅ |
| 2C_s01 | Q4 | 440W | 1 | crop:gemma>qwen=∅ |
| 2C_s03 | Q4 | 440W | 1 | crop:gemma>qwen=∅ |
| 2A_s01 | Q4 | 2500m | 1 | crop:qwen>qwen=4,2500 m |
| 2B_s01 | Q5 | 0.625 | 1 | crop:qwen>qwen=∅ |

## Quality gate on the photos

Not part of the scores above. In the live pipeline a sheet whose photo fails the gate goes to a TA as a whole; a page judged blank is accepted as all-blank.

| sheet | judged blank | passes gate | reasons |
|---|---|---|---|
| 2A_s05 |  | **no** | image is blurry, glare / reflection on the page |
| 2B_s02 |  | **no** | glare / reflection on the page |
| 2B_s04 |  | **no** | glare / reflection on the page |
| 2B_s05 |  | **no** | image is blurry, glare / reflection on the page |
| 2C_s04 | yes | yes |  |
| mcq_s02 |  | **no** | glare / reflection on the page |
| mcq_s05 |  | **no** | glare / reflection on the page |
| mcq_s08 | yes | yes |  |
| mcq_s09 |  | **no** | glare / reflection on the page |
| mcq_s12 |  | **no** | glare / reflection on the page |
| mcq_s15 |  | **no** | glare / reflection on the page |
