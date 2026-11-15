# Teacher's marks vs our grader's marks (Mendeley, 50 sheets)

Generated 2026-11-15 13:35 by `python eval/mendeley_marks_table.py`. Set-up: whole-page transcription (pagetext) + Gemma grader, prompt v2. Short answers only, 15 × 2 marks per sheet.
*Calibrated* = grader + +0.63 (learned from the teacher's marks on sheets Student_8, Student_11, Student_24, Student_31, Student_33, marked ★), rounded to 0.5, clipped to 0–2. *TA* = answer not found on the page → sent to a TA. Per-answer list: `marks_per_answer.csv`.

## Agreement on the 45 non-calibration sheets

| | MAE (/2) | exact | within 0.5 | QWK | bias |
|---|---|---|---|---|---|
| grader (raw) | 0.607 | 38% | 55% | 0.484 | -0.5 |
| grader (calibrated) | 0.426 | 36% | 84% | 0.605 | -0.125 |

## Totals per sheet (short answers the teacher marked)

| sheet | answers | teacher | grader | calibrated | TA |
|---|---|---|---|---|---|
| Student_1 | 14 | 21 | 16.5 | 20.5 |  |
| Student_2 | 9 | 13 | 6 | 10 |  |
| Student_3 | 12 | 13 | 6 | 11.5 |  |
| Student_4 | 12 | 21 | 17 | 20 |  |
| Student_5 | 11 | 15 | 9.5 | 13.5 |  |
| Student_6 | 9 | 14 | 9 | 12 | 1 |
| Student_7 | 14 | 15 | 10 | 16 |  |
| Student_8 ★ | 10 | 14 | 8.5 | 13 |  |
| Student_9 | 15 | 19 | 12 | 18 |  |
| Student_10 | 9 | 14 | 11 | 14 |  |
| Student_11 ★ | 14 | 24.5 | 14.5 | 19.5 |  |
| Student_12 | 14 | 21 | 13.5 | 18.5 |  |
| Student_13 | 15 | 24 | 16.5 | 21 |  |
| Student_14 | 14 | 21 | 16 | 20.5 |  |
| Student_15 | 15 | 8 | 2 | 9.5 |  |
| Student_16 | 8 | 9 | 6 | 9 | 1 |
| Student_17 | 15 | 24 | 15 | 20.5 |  |
| Student_18 | 4 | 5 | 3.5 | 5.5 |  |
| Student_19 | 3 | 3 | 2 | 3 |  |
| Student_20 | 10 | 14 | 9.5 | 13.5 |  |
| Student_21 | 10 | 18 | 11 | 15 |  |
| Student_22 | 10 | 15 | 6.5 | 10.5 | 1 |
| Student_23 | 12 | 13 | 9.5 | 15 |  |
| Student_24 ★ | 12 | 20 | 15 | 18 |  |
| Student_25 | 11 | 14 | 4 | 9.5 |  |
| Student_26 | 7 | 11 | 6 | 8.5 |  |
| Student_27 | 14 | 15 | 7 | 12.5 | 1 |
| Student_28 | 9 | 13 | 7 | 11.5 |  |
| Student_29 | 15 | 24 | 15 | 20.5 |  |
| Student_30 | 14 | 20 | 12 | 17.5 | 1 |
| Student_31 ★ | 15 | 21 | 8.5 | 16 |  |
| Student_32 | 10 | 17.5 | 13.5 | 16 |  |
| Student_33 ★ | 9 | 15.5 | 10.5 | 13.5 |  |
| Student_34 | 10 | 18 | 14.5 | 16.5 |  |
| Student_35 | 11 | 12 | 5 | 10 | 1 |
| Student_36 | 9 | 13 | 9.5 | 13 |  |
| Student_37 | 10 | 15 | 12 | 16 |  |
| Student_38 | 10 | 18 | 11 | 15 |  |
| Student_39 | 15 | 20 | 9 | 15 |  |
| Student_40 | 13 | 16 | 12.5 | 17.5 |  |
| Student_41 | 12 | 15 | 8 | 13.5 |  |
| Student_42 | 15 | 26 | 16.5 | 21.5 |  |
| Student_43 | 11 | 20.5 | 13.5 | 17 |  |
| Student_44 | 11 | 21 | 12.5 | 16 | 1 |
| Student_45 | 7 | 12 | 11 | 12.5 |  |
| Student_46 | 13 | 21 | 19 | 21.5 |  |
| Student_47 | 9 | 18 | 10.5 | 13 | 1 |
| Student_48 | 8 | 11 | 4 | 7.5 |  |
| Student_49 | 10 | 14 | 9 | 12 | 1 |
| Student_50 | 15 | 22 | 15.5 | 20.5 |  |

## Every answer

| sheet | question | teacher | grader | calibrated |
|---|---|---|---|---|
| Student_1 | S1 (Q21) | 2 | 2 | 2 |
| Student_1 | S2 (Q22) | 1 | 0 | 0.5 |
| Student_1 | S3 (Q23) | 1 | 1 | 1.5 |
| Student_1 | S4 (Q24) | 2 | 2 | 2 |
| Student_1 | S5 (Q25) | 2 | 2 | 2 |
| Student_1 | S6 (Q26) | 2 | 2 | 2 |
| Student_1 | S7 (Q27) | 1 | 1 | 1.5 |
| Student_1 | S8 (Q28) | 2 | 1 | 1.5 |
| Student_1 | S9 (Q29) | 1 | 0 | 0.5 |
| Student_1 | S10 (Q30) | 2 | 2 | 2 |
| Student_1 | S11 (Q31) | 1 | 1.5 | 2 |
| Student_1 | S13 (Q33) | 0 | 0 | 0.5 |
| Student_1 | S14 (Q34) | 2 | 2 | 2 |
| Student_1 | S15 (Q35) | 2 | 0 | 0.5 |
| Student_2 | S1 (Q21) | 2 | 1.5 | 2 |
| Student_2 | S2 (Q22) | 1.5 | 0.5 | 1 |
| Student_2 | S3 (Q23) | 2 | 0.5 | 1 |
| Student_2 | S4 (Q24) | 1 | 0.5 | 1 |
| Student_2 | S5 (Q25) | 0 | 0 | 0.5 |
| Student_2 | S8 (Q28) | 2 | 2 | 2 |
| Student_2 | S9 (Q29) | 1 | 0.5 | 1 |
| Student_2 | S13 (Q33) | 2 | 0.5 | 1 |
| Student_2 | S15 (Q35) | 1.5 | 0 | 0.5 |
| Student_3 | S1 (Q21) | 2 | 1.5 | 2 |
| Student_3 | S2 (Q22) | 2 | 0 | 0.5 |
| Student_3 | S3 (Q23) | 0 | 1 | 1.5 |
| Student_3 | S4 (Q24) | 0 | 0 | 0.5 |
| Student_3 | S5 (Q25) | 1 | 2 | 2 |
| Student_3 | S6 (Q26) | 2 | 1 | 1.5 |
| Student_3 | S7 (Q27) | 1 | 0 | 0.5 |
| Student_3 | S8 (Q28) | 1 | 0 | 0.5 |
| Student_3 | S9 (Q29) | 2 | 0.5 | 1 |
| Student_3 | S11 (Q31) | 1 | 0 | 0.5 |
| Student_3 | S12 (Q32) | 0 | 0 | 0.5 |
| Student_3 | S14 (Q34) | 1 | 0 | 0.5 |
| Student_4 | S1 (Q21) | 2 | 2 | 2 |
| Student_4 | S2 (Q22) | 2 | 2 | 2 |
| Student_4 | S3 (Q23) | 1 | 0.5 | 1 |
| Student_4 | S4 (Q24) | 2 | 2 | 2 |
| Student_4 | S5 (Q25) | 2 | 1 | 1.5 |
| Student_4 | S6 (Q26) | 2 | 2 | 2 |
| Student_4 | S7 (Q27) | 2 | 1 | 1.5 |
| Student_4 | S8 (Q28) | 2 | 2 | 2 |
| Student_4 | S9 (Q29) | 2 | 0 | 0.5 |
| Student_4 | S11 (Q31) | 2 | 1.5 | 2 |
| Student_4 | S12 (Q32) | 0 | 1 | 1.5 |
| Student_4 | S14 (Q34) | 2 | 2 | 2 |
| Student_5 | S1 (Q21) | 1 | 2 | 2 |
| Student_5 | S2 (Q22) | 1 | 0 | 0.5 |
| Student_5 | S3 (Q23) | 1 | 0.5 | 1 |
| Student_5 | S4 (Q24) | 2 | 1.5 | 2 |
| Student_5 | S5 (Q25) | 2 | 2 | 2 |
| Student_5 | S6 (Q26) | 2 | 0.5 | 1 |
| Student_5 | S7 (Q27) | 0 | 0 | 0.5 |
| Student_5 | S8 (Q28) | 2 | 2 | 2 |
| Student_5 | S9 (Q29) | 1 | 1 | 1.5 |
| Student_5 | S10 (Q30) | 2 | 0 | 0.5 |
| Student_5 | S11 (Q31) | 1 | 0 | 0.5 |
| Student_6 | S1 (Q21) | 2 | 1.5 | 2 |
| Student_6 | S4 (Q24) | 2 | 1 | 1.5 |
| Student_6 | S5 (Q25) | 2 | 2 | 2 |
| Student_6 | S6 (Q26) | 1 | 0 | 0.5 |
| Student_6 | S7 (Q27) | 1 | 0 | 0.5 |
| Student_6 | S8 (Q28) | 1 | 1 | 1.5 |
| Student_6 | S11 (Q31) | 1 | 2 | 2 |
| Student_6 | S12 (Q32) | 2 | TA | TA |
| Student_6 | S14 (Q34) | 2 | 1.5 | 2 |
| Student_7 | S1 (Q21) | 2 | 1.5 | 2 |
| Student_7 | S2 (Q22) | 1 | 0 | 0.5 |
| Student_7 | S3 (Q23) | 1 | 0.5 | 1 |
| Student_7 | S4 (Q24) | 1 | 0 | 0.5 |
| Student_7 | S5 (Q25) | 2 | 2 | 2 |
| Student_7 | S6 (Q26) | 0 | 0 | 0.5 |
| Student_7 | S7 (Q27) | 1 | 1.5 | 2 |
| Student_7 | S8 (Q28) | 2 | 0.5 | 1 |
| Student_7 | S9 (Q29) | 2 | 0.5 | 1 |
| Student_7 | S10 (Q30) | 0 | 0 | 0.5 |
| Student_7 | S11 (Q31) | 1 | 1.5 | 2 |
| Student_7 | S12 (Q32) | 1 | 0 | 0.5 |
| Student_7 | S13 (Q33) | 0 | 0 | 0.5 |
| Student_7 | S14 (Q34) | 1 | 2 | 2 |
| Student_8 ★ | S1 (Q21) | 2 | 1.5 | 2 |
| Student_8 ★ | S4 (Q24) | 1 | 0 | 0.5 |
| Student_8 ★ | S5 (Q25) | 2 | 2 | 2 |
| Student_8 ★ | S6 (Q26) | 2 | 1 | 1.5 |
| Student_8 ★ | S7 (Q27) | 1 | 1 | 1.5 |
| Student_8 ★ | S8 (Q28) | 1 | 1 | 1.5 |
| Student_8 ★ | S9 (Q29) | 2 | 0.5 | 1 |
| Student_8 ★ | S11 (Q31) | 1 | 0 | 0.5 |
| Student_8 ★ | S12 (Q32) | 2 | 1 | 1.5 |
| Student_8 ★ | S13 (Q33) | 0 | 0.5 | 1 |
| Student_9 | S1 (Q21) | 2 | 2 | 2 |
| Student_9 | S2 (Q22) | 1 | 0 | 0.5 |
| Student_9 | S3 (Q23) | 1 | 2 | 2 |
| Student_9 | S4 (Q24) | 1 | 1 | 1.5 |
| Student_9 | S5 (Q25) | 2 | 2 | 2 |
| Student_9 | S6 (Q26) | 2 | 0 | 0.5 |
| Student_9 | S7 (Q27) | 2 | 1 | 1.5 |
| Student_9 | S8 (Q28) | 1 | 1 | 1.5 |
| Student_9 | S9 (Q29) | 2 | 0.5 | 1 |
| Student_9 | S10 (Q30) | 1 | 1 | 1.5 |
| Student_9 | S11 (Q31) | 1 | 0.5 | 1 |
| Student_9 | S12 (Q32) | 0 | 0 | 0.5 |
| Student_9 | S13 (Q33) | 1 | 0 | 0.5 |
| Student_9 | S14 (Q34) | 2 | 1 | 1.5 |
| Student_9 | S15 (Q35) | 0 | 0 | 0.5 |
| Student_10 | S1 (Q21) | 2 | 1.5 | 2 |
| Student_10 | S3 (Q23) | 2 | 2 | 2 |
| Student_10 | S4 (Q24) | 1 | 0 | 0.5 |
| Student_10 | S5 (Q25) | 2 | 2 | 2 |
| Student_10 | S6 (Q26) | 2 | 1.5 | 2 |
| Student_10 | S8 (Q28) | 1 | 0.5 | 1 |
| Student_10 | S9 (Q29) | 1 | 0.5 | 1 |
| Student_10 | S11 (Q31) | 2 | 1 | 1.5 |
| Student_10 | S14 (Q34) | 1 | 2 | 2 |
| Student_11 ★ | S1 (Q21) | 2 | 1.5 | 2 |
| Student_11 ★ | S2 (Q22) | 1 | 0.5 | 1 |
| Student_11 ★ | S3 (Q23) | 1 | 1 | 1.5 |
| Student_11 ★ | S4 (Q24) | 2 | 2 | 2 |
| Student_11 ★ | S5 (Q25) | 2 | 2 | 2 |
| Student_11 ★ | S6 (Q26) | 2 | 1.5 | 2 |
| Student_11 ★ | S7 (Q27) | 1.5 | 1 | 1.5 |
| Student_11 ★ | S8 (Q28) | 2 | 2 | 2 |
| Student_11 ★ | S9 (Q29) | 2 | 0 | 0.5 |
| Student_11 ★ | S10 (Q30) | 2 | 0 | 0.5 |
| Student_11 ★ | S11 (Q31) | 2 | 1 | 1.5 |
| Student_11 ★ | S12 (Q32) | 2 | 2 | 2 |
| Student_11 ★ | S13 (Q33) | 1.5 | 0 | 0.5 |
| Student_11 ★ | S15 (Q35) | 1.5 | 0 | 0.5 |
| Student_12 | S2 (Q22) | 1 | 0 | 0.5 |
| Student_12 | S3 (Q23) | 1 | 0.5 | 1 |
| Student_12 | S4 (Q24) | 2 | 1 | 1.5 |
| Student_12 | S5 (Q25) | 2 | 2 | 2 |
| Student_12 | S6 (Q26) | 2 | 2 | 2 |
| Student_12 | S7 (Q27) | 2 | 1 | 1.5 |
| Student_12 | S8 (Q28) | 1.5 | 2 | 2 |
| Student_12 | S9 (Q29) | 2 | 0.5 | 1 |
| Student_12 | S10 (Q30) | 1 | 0 | 0.5 |
| Student_12 | S11 (Q31) | 2 | 1 | 1.5 |
| Student_12 | S12 (Q32) | 1 | 0.5 | 1 |
| Student_12 | S13 (Q33) | 0.5 | 0 | 0.5 |
| Student_12 | S14 (Q34) | 1.5 | 2 | 2 |
| Student_12 | S15 (Q35) | 1.5 | 1 | 1.5 |
| Student_13 | S1 (Q21) | 2 | 2 | 2 |
| Student_13 | S2 (Q22) | 2 | 0 | 0.5 |
| Student_13 | S3 (Q23) | 1 | 1 | 1.5 |
| Student_13 | S4 (Q24) | 2 | 2 | 2 |
| Student_13 | S5 (Q25) | 2 | 2 | 2 |
| Student_13 | S6 (Q26) | 2 | 2 | 2 |
| Student_13 | S7 (Q27) | 2 | 2 | 2 |
| Student_13 | S8 (Q28) | 2 | 1 | 1.5 |
| Student_13 | S9 (Q29) | 1 | 0.5 | 1 |
| Student_13 | S10 (Q30) | 1 | 0 | 0.5 |
| Student_13 | S11 (Q31) | 2 | 2 | 2 |
| Student_13 | S12 (Q32) | 2 | 0.5 | 1 |
| Student_13 | S13 (Q33) | 0 | 0 | 0.5 |
| Student_13 | S14 (Q34) | 2 | 1.5 | 2 |
| Student_13 | S15 (Q35) | 1 | 0 | 0.5 |
| Student_14 | S1 (Q21) | 2 | 1.5 | 2 |
| Student_14 | S2 (Q22) | 1 | 0 | 0.5 |
| Student_14 | S3 (Q23) | 2 | 2 | 2 |
| Student_14 | S4 (Q24) | 2 | 2 | 2 |
| Student_14 | S5 (Q25) | 2 | 2 | 2 |
| Student_14 | S6 (Q26) | 2 | 1.5 | 2 |
| Student_14 | S7 (Q27) | 2 | 1 | 1.5 |
| Student_14 | S8 (Q28) | 2 | 2 | 2 |
| Student_14 | S9 (Q29) | 1 | 1 | 1.5 |
| Student_14 | S10 (Q30) | 0 | 0 | 0.5 |
| Student_14 | S11 (Q31) | 2 | 1 | 1.5 |
| Student_14 | S12 (Q32) | 0 | 0 | 0.5 |
| Student_14 | S13 (Q33) | 1 | 0 | 0.5 |
| Student_14 | S14 (Q34) | 2 | 2 | 2 |
| Student_15 | S1 (Q21) | 2 | 1 | 1.5 |
| Student_15 | S2 (Q22) | 1 | 0 | 0.5 |
| Student_15 | S3 (Q23) | 1 | 0.5 | 1 |
| Student_15 | S4 (Q24) | 0 | 0 | 0.5 |
| Student_15 | S5 (Q25) | 0 | 0 | 0.5 |
| Student_15 | S6 (Q26) | 0 | 0 | 0.5 |
| Student_15 | S7 (Q27) | 1 | 0 | 0.5 |
| Student_15 | S8 (Q28) | 1 | 0.5 | 1 |
| Student_15 | S9 (Q29) | 1 | 0 | 0.5 |
| Student_15 | S10 (Q30) | 0 | 0 | 0.5 |
| Student_15 | S11 (Q31) | 0 | 0 | 0.5 |
| Student_15 | S12 (Q32) | 0 | 0 | 0.5 |
| Student_15 | S13 (Q33) | 0 | 0 | 0.5 |
| Student_15 | S14 (Q34) | 1 | 0 | 0.5 |
| Student_15 | S15 (Q35) | 0 | 0 | 0.5 |
| Student_16 | S1 (Q21) | 1 | 1 | 1.5 |
| Student_16 | S2 (Q22) | 2 | TA | TA |
| Student_16 | S3 (Q23) | 1 | 0.5 | 1 |
| Student_16 | S4 (Q24) | 1 | 2 | 2 |
| Student_16 | S5 (Q25) | 0 | 0 | 0.5 |
| Student_16 | S6 (Q26) | 1.5 | 1 | 1.5 |
| Student_16 | S7 (Q27) | 0.5 | 0 | 0.5 |
| Student_16 | S8 (Q28) | 2 | 1.5 | 2 |
| Student_17 | S1 (Q21) | 2 | 1 | 1.5 |
| Student_17 | S2 (Q22) | 2 | 2 | 2 |
| Student_17 | S3 (Q23) | 1 | 0 | 0.5 |
| Student_17 | S4 (Q24) | 2 | 2 | 2 |
| Student_17 | S5 (Q25) | 2 | 2 | 2 |
| Student_17 | S6 (Q26) | 2 | 1 | 1.5 |
| Student_17 | S7 (Q27) | 2 | 1 | 1.5 |
| Student_17 | S8 (Q28) | 2 | 1.5 | 2 |
| Student_17 | S9 (Q29) | 1 | 0 | 0.5 |
| Student_17 | S10 (Q30) | 1 | 1 | 1.5 |
| Student_17 | S11 (Q31) | 2 | 1 | 1.5 |
| Student_17 | S12 (Q32) | 2 | 2 | 2 |
| Student_17 | S13 (Q33) | 1 | 0.5 | 1 |
| Student_17 | S14 (Q34) | 1 | 0 | 0.5 |
| Student_17 | S15 (Q35) | 1 | 0 | 0.5 |
| Student_18 | S1 (Q21) | 2 | 1.5 | 2 |
| Student_18 | S3 (Q23) | 2 | 1 | 1.5 |
| Student_18 | S7 (Q27) | 0 | 1 | 1.5 |
| Student_18 | S9 (Q29) | 1 | 0 | 0.5 |
| Student_19 | S4 (Q24) | 0 | 0 | 0.5 |
| Student_19 | S5 (Q25) | 2 | 2 | 2 |
| Student_19 | S9 (Q29) | 1 | 0 | 0.5 |
| Student_20 | S1 (Q21) | 2 | 1 | 1.5 |
| Student_20 | S3 (Q23) | 1 | 1.5 | 2 |
| Student_20 | S4 (Q24) | 0 | 0 | 0.5 |
| Student_20 | S5 (Q25) | 2 | 2 | 2 |
| Student_20 | S6 (Q26) | 0 | 0 | 0.5 |
| Student_20 | S7 (Q27) | 2 | 1 | 1.5 |
| Student_20 | S8 (Q28) | 2 | 1.5 | 2 |
| Student_20 | S9 (Q29) | 1 | 0.5 | 1 |
| Student_20 | S11 (Q31) | 2 | 2 | 2 |
| Student_20 | S14 (Q34) | 2 | 0 | 0.5 |
| Student_21 | S1 (Q21) | 2 | 2 | 2 |
| Student_21 | S2 (Q22) | 1 | 0 | 0.5 |
| Student_21 | S3 (Q23) | 1 | 1 | 1.5 |
| Student_21 | S4 (Q24) | 2 | 1 | 1.5 |
| Student_21 | S5 (Q25) | 2 | 2 | 2 |
| Student_21 | S6 (Q26) | 2 | 1.5 | 2 |
| Student_21 | S7 (Q27) | 2 | 0.5 | 1 |
| Student_21 | S9 (Q29) | 2 | 0.5 | 1 |
| Student_21 | S11 (Q31) | 2 | 1 | 1.5 |
| Student_21 | S14 (Q34) | 2 | 1.5 | 2 |
| Student_22 | S1 (Q21) | 2 | 1 | 1.5 |
| Student_22 | S2 (Q22) | 1 | 0 | 0.5 |
| Student_22 | S3 (Q23) | 1 | 1.5 | 2 |
| Student_22 | S5 (Q25) | 1 | 1 | 1.5 |
| Student_22 | S6 (Q26) | 2 | 0.5 | 1 |
| Student_22 | S7 (Q27) | 1 | 0 | 0.5 |
| Student_22 | S9 (Q29) | 1 | 0 | 0.5 |
| Student_22 | S10 (Q30) | 2 | 0.5 | 1 |
| Student_22 | S11 (Q31) | 2 | 2 | 2 |
| Student_22 | S14 (Q34) | 2 | TA | TA |
| Student_23 | S1 (Q21) | 1 | 1.5 | 2 |
| Student_23 | S2 (Q22) | 0 | 0 | 0.5 |
| Student_23 | S3 (Q23) | 0 | 1 | 1.5 |
| Student_23 | S4 (Q24) | 2 | 1.5 | 2 |
| Student_23 | S5 (Q25) | 2 | 2 | 2 |
| Student_23 | S6 (Q26) | 2 | 1 | 1.5 |
| Student_23 | S7 (Q27) | 0 | 0.5 | 1 |
| Student_23 | S8 (Q28) | 2 | 1 | 1.5 |
| Student_23 | S9 (Q29) | 1 | 0 | 0.5 |
| Student_23 | S10 (Q30) | 1 | 0 | 0.5 |
| Student_23 | S11 (Q31) | 2 | 1 | 1.5 |
| Student_23 | S12 (Q32) | 0 | 0 | 0.5 |
| Student_24 ★ | S1 (Q21) | 2 | 2 | 2 |
| Student_24 ★ | S2 (Q22) | 1 | 0 | 0.5 |
| Student_24 ★ | S4 (Q24) | 2 | 2 | 2 |
| Student_24 ★ | S5 (Q25) | 1 | 2 | 2 |
| Student_24 ★ | S6 (Q26) | 2 | 2 | 2 |
| Student_24 ★ | S7 (Q27) | 2 | 2 | 2 |
| Student_24 ★ | S8 (Q28) | 2 | 1 | 1.5 |
| Student_24 ★ | S9 (Q29) | 2 | 0.5 | 1 |
| Student_24 ★ | S11 (Q31) | 2 | 1.5 | 2 |
| Student_24 ★ | S12 (Q32) | 0 | 0 | 0.5 |
| Student_24 ★ | S14 (Q34) | 2 | 2 | 2 |
| Student_24 ★ | S15 (Q35) | 2 | 0 | 0.5 |
| Student_25 | S1 (Q21) | 2 | 1.5 | 2 |
| Student_25 | S2 (Q22) | 0 | 0 | 0.5 |
| Student_25 | S3 (Q23) | 2 | 0.5 | 1 |
| Student_25 | S4 (Q24) | 1 | 0 | 0.5 |
| Student_25 | S6 (Q26) | 2 | 1 | 1.5 |
| Student_25 | S7 (Q27) | 2 | 0 | 0.5 |
| Student_25 | S8 (Q28) | 2 | 1 | 1.5 |
| Student_25 | S11 (Q31) | 1 | 0 | 0.5 |
| Student_25 | S12 (Q32) | 1 | 0 | 0.5 |
| Student_25 | S14 (Q34) | 1 | 0 | 0.5 |
| Student_25 | S15 (Q35) | 0 | 0 | 0.5 |
| Student_26 | S1 (Q21) | 2 | 1.5 | 2 |
| Student_26 | S4 (Q24) | 1 | 0 | 0.5 |
| Student_26 | S5 (Q25) | 2 | 2 | 2 |
| Student_26 | S6 (Q26) | 1 | 0.5 | 1 |
| Student_26 | S7 (Q27) | 2 | 0 | 0.5 |
| Student_26 | S8 (Q28) | 2 | 2 | 2 |
| Student_26 | S11 (Q31) | 1 | 0 | 0.5 |
| Student_27 | S1 (Q21) | 2 | 1 | 1.5 |
| Student_27 | S2 (Q22) | 1 | 0 | 0.5 |
| Student_27 | S3 (Q23) | 1 | 0 | 0.5 |
| Student_27 | S4 (Q24) | 0.5 | 0 | 0.5 |
| Student_27 | S5 (Q25) | 2 | 2 | 2 |
| Student_27 | S6 (Q26) | 2 | 1 | 1.5 |
| Student_27 | S7 (Q27) | 1 | 1 | 1.5 |
| Student_27 | S8 (Q28) | 2 | 2 | 2 |
| Student_27 | S9 (Q29) | 0.5 | 0 | 0.5 |
| Student_27 | S10 (Q30) | 0 | 0 | 0.5 |
| Student_27 | S11 (Q31) | 0 | 0 | 0.5 |
| Student_27 | S12 (Q32) | 2 | 0 | 0.5 |
| Student_27 | S13 (Q33) | 1 | TA | TA |
| Student_27 | S15 (Q35) | 0 | 0 | 0.5 |
| Student_28 | S1 (Q21) | 2 | 1 | 1.5 |
| Student_28 | S2 (Q22) | 1 | 0 | 0.5 |
| Student_28 | S3 (Q23) | 2 | 1 | 1.5 |
| Student_28 | S6 (Q26) | 1 | 0 | 0.5 |
| Student_28 | S7 (Q27) | 1 | 1 | 1.5 |
| Student_28 | S8 (Q28) | 2 | 1 | 1.5 |
| Student_28 | S9 (Q29) | 1 | 1 | 1.5 |
| Student_28 | S11 (Q31) | 1 | 1 | 1.5 |
| Student_28 | S14 (Q34) | 2 | 1 | 1.5 |
| Student_29 | S1 (Q21) | 2 | 1.5 | 2 |
| Student_29 | S2 (Q22) | 2 | 1 | 1.5 |
| Student_29 | S3 (Q23) | 2 | 2 | 2 |
| Student_29 | S4 (Q24) | 2 | 2 | 2 |
| Student_29 | S5 (Q25) | 2 | 2 | 2 |
| Student_29 | S6 (Q26) | 2 | 1.5 | 2 |
| Student_29 | S7 (Q27) | 2 | 1 | 1.5 |
| Student_29 | S8 (Q28) | 2 | 2 | 2 |
| Student_29 | S9 (Q29) | 2 | 0.5 | 1 |
| Student_29 | S10 (Q30) | 1 | 0 | 0.5 |
| Student_29 | S11 (Q31) | 1 | 0 | 0.5 |
| Student_29 | S12 (Q32) | 0 | 0 | 0.5 |
| Student_29 | S13 (Q33) | 2 | 0.5 | 1 |
| Student_29 | S14 (Q34) | 1 | 1 | 1.5 |
| Student_29 | S15 (Q35) | 1 | 0 | 0.5 |
| Student_30 | S1 (Q21) | 2 | 1 | 1.5 |
| Student_30 | S2 (Q22) | 1 | TA | TA |
| Student_30 | S3 (Q23) | 2 | 1.5 | 2 |
| Student_30 | S4 (Q24) | 2 | 0 | 0.5 |
| Student_30 | S5 (Q25) | 0 | 0 | 0.5 |
| Student_30 | S6 (Q26) | 2 | 1.5 | 2 |
| Student_30 | S7 (Q27) | 2 | 1 | 1.5 |
| Student_30 | S8 (Q28) | 2 | 2 | 2 |
| Student_30 | S9 (Q29) | 1 | 0 | 0.5 |
| Student_30 | S10 (Q30) | 1 | 1.5 | 2 |
| Student_30 | S11 (Q31) | 2 | 2 | 2 |
| Student_30 | S12 (Q32) | 1 | 0 | 0.5 |
| Student_30 | S14 (Q34) | 2 | 1.5 | 2 |
| Student_30 | S15 (Q35) | 0 | 0 | 0.5 |
| Student_31 ★ | S1 (Q21) | 2 | 1.5 | 2 |
| Student_31 ★ | S2 (Q22) | 1 | 0 | 0.5 |
| Student_31 ★ | S3 (Q23) | 2 | 0.5 | 1 |
| Student_31 ★ | S4 (Q24) | 1 | 0 | 0.5 |
| Student_31 ★ | S5 (Q25) | 2 | 1.5 | 2 |
| Student_31 ★ | S6 (Q26) | 2 | 1 | 1.5 |
| Student_31 ★ | S7 (Q27) | 2 | 1 | 1.5 |
| Student_31 ★ | S8 (Q28) | 1 | 0.5 | 1 |
| Student_31 ★ | S9 (Q29) | 2 | 0 | 0.5 |
| Student_31 ★ | S10 (Q30) | 2 | 0 | 0.5 |
| Student_31 ★ | S11 (Q31) | 1.5 | 1 | 1.5 |
| Student_31 ★ | S12 (Q32) | 0 | 0 | 0.5 |
| Student_31 ★ | S13 (Q33) | 0.5 | 0 | 0.5 |
| Student_31 ★ | S14 (Q34) | 1 | 0.5 | 1 |
| Student_31 ★ | S15 (Q35) | 1 | 1 | 1.5 |
| Student_32 | S1 (Q21) | 2 | 2 | 2 |
| Student_32 | S4 (Q24) | 2 | 2 | 2 |
| Student_32 | S5 (Q25) | 1.5 | 2 | 2 |
| Student_32 | S6 (Q26) | 1 | 1.5 | 2 |
| Student_32 | S7 (Q27) | 2 | 1 | 1.5 |
| Student_32 | S8 (Q28) | 2 | 2 | 2 |
| Student_32 | S9 (Q29) | 2 | 0.5 | 1 |
| Student_32 | S10 (Q30) | 2 | 2 | 2 |
| Student_32 | S11 (Q31) | 1 | 0.5 | 1 |
| Student_32 | S13 (Q33) | 2 | 0 | 0.5 |
| Student_33 ★ | S1 (Q21) | 2 | 2 | 2 |
| Student_33 ★ | S3 (Q23) | 2 | 1 | 1.5 |
| Student_33 ★ | S5 (Q25) | 2 | 2 | 2 |
| Student_33 ★ | S7 (Q27) | 2 | 1 | 1.5 |
| Student_33 ★ | S8 (Q28) | 2 | 2 | 2 |
| Student_33 ★ | S9 (Q29) | 1 | 0 | 0.5 |
| Student_33 ★ | S10 (Q30) | 0.5 | 0 | 0.5 |
| Student_33 ★ | S11 (Q31) | 2 | 1 | 1.5 |
| Student_33 ★ | S14 (Q34) | 2 | 1.5 | 2 |
| Student_34 | S3 (Q23) | 2 | 2 | 2 |
| Student_34 | S4 (Q24) | 1 | 1 | 1.5 |
| Student_34 | S5 (Q25) | 2 | 2 | 2 |
| Student_34 | S6 (Q26) | 2 | 2 | 2 |
| Student_34 | S8 (Q28) | 2 | 1 | 1.5 |
| Student_34 | S9 (Q29) | 2 | 0.5 | 1 |
| Student_34 | S10 (Q30) | 1 | 0 | 0.5 |
| Student_34 | S11 (Q31) | 2 | 2 | 2 |
| Student_34 | S12 (Q32) | 2 | 2 | 2 |
| Student_34 | S14 (Q34) | 2 | 2 | 2 |
| Student_35 | S1 (Q21) | 1 | 0 | 0.5 |
| Student_35 | S2 (Q22) | 1 | 0 | 0.5 |
| Student_35 | S3 (Q23) | 0 | 1 | 1.5 |
| Student_35 | S4 (Q24) | 2 | 1.5 | 2 |
| Student_35 | S6 (Q26) | 2 | 0.5 | 1 |
| Student_35 | S7 (Q27) | 1 | 1 | 1.5 |
| Student_35 | S8 (Q28) | 2 | TA | TA |
| Student_35 | S9 (Q29) | 1 | 0 | 0.5 |
| Student_35 | S11 (Q31) | 1 | 0 | 0.5 |
| Student_35 | S12 (Q32) | 1 | 1 | 1.5 |
| Student_35 | S13 (Q33) | 0 | 0 | 0.5 |
| Student_36 | S1 (Q21) | 2 | 1.5 | 2 |
| Student_36 | S3 (Q23) | 1 | 0.5 | 1 |
| Student_36 | S4 (Q24) | 2 | 2 | 2 |
| Student_36 | S5 (Q25) | 2 | 2 | 2 |
| Student_36 | S6 (Q26) | 2 | 1.5 | 2 |
| Student_36 | S8 (Q28) | 2 | 1 | 1.5 |
| Student_36 | S9 (Q29) | 0 | 0 | 0.5 |
| Student_36 | S11 (Q31) | 2 | 1 | 1.5 |
| Student_36 | S13 (Q33) | 0 | 0 | 0.5 |
| Student_37 | S1 (Q21) | 2 | 1.5 | 2 |
| Student_37 | S2 (Q22) | 1 | 0 | 0.5 |
| Student_37 | S3 (Q23) | 1 | 1.5 | 2 |
| Student_37 | S4 (Q24) | 2 | 2 | 2 |
| Student_37 | S5 (Q25) | 2 | 2 | 2 |
| Student_37 | S6 (Q26) | 2 | 0.5 | 1 |
| Student_37 | S7 (Q27) | 2 | 1 | 1.5 |
| Student_37 | S8 (Q28) | 1 | 1.5 | 2 |
| Student_37 | S9 (Q29) | 0 | 1 | 1.5 |
| Student_37 | S11 (Q31) | 2 | 1 | 1.5 |
| Student_38 | S1 (Q21) | 2 | 2 | 2 |
| Student_38 | S2 (Q22) | 1 | 1 | 1.5 |
| Student_38 | S3 (Q23) | 2 | 1 | 1.5 |
| Student_38 | S4 (Q24) | 2 | 0.5 | 1 |
| Student_38 | S5 (Q25) | 1 | 2 | 2 |
| Student_38 | S6 (Q26) | 2 | 1.5 | 2 |
| Student_38 | S7 (Q27) | 2 | 1 | 1.5 |
| Student_38 | S8 (Q28) | 2 | 1 | 1.5 |
| Student_38 | S9 (Q29) | 2 | 0.5 | 1 |
| Student_38 | S14 (Q34) | 2 | 0.5 | 1 |
| Student_39 | S1 (Q21) | 2 | 2 | 2 |
| Student_39 | S2 (Q22) | 2 | 0 | 0.5 |
| Student_39 | S3 (Q23) | 1 | 0 | 0.5 |
| Student_39 | S4 (Q24) | 2 | 2 | 2 |
| Student_39 | S5 (Q25) | 2 | 2 | 2 |
| Student_39 | S6 (Q26) | 2 | 1 | 1.5 |
| Student_39 | S7 (Q27) | 2 | 0.5 | 1 |
| Student_39 | S8 (Q28) | 1 | 0.5 | 1 |
| Student_39 | S9 (Q29) | 1 | 0 | 0.5 |
| Student_39 | S10 (Q30) | 1 | 0 | 0.5 |
| Student_39 | S11 (Q31) | 2 | 1 | 1.5 |
| Student_39 | S12 (Q32) | 0 | 0 | 0.5 |
| Student_39 | S13 (Q33) | 0 | 0 | 0.5 |
| Student_39 | S14 (Q34) | 1 | 0 | 0.5 |
| Student_39 | S15 (Q35) | 1 | 0 | 0.5 |
| Student_40 | S1 (Q21) | 2 | 2 | 2 |
| Student_40 | S2 (Q22) | 1 | 0 | 0.5 |
| Student_40 | S3 (Q23) | 1 | 0.5 | 1 |
| Student_40 | S4 (Q24) | 2 | 2 | 2 |
| Student_40 | S5 (Q25) | 2 | 2 | 2 |
| Student_40 | S6 (Q26) | 1 | 0 | 0.5 |
| Student_40 | S7 (Q27) | 2 | 1 | 1.5 |
| Student_40 | S8 (Q28) | 1 | 1 | 1.5 |
| Student_40 | S9 (Q29) | 0 | 1 | 1.5 |
| Student_40 | S10 (Q30) | 1 | 0.5 | 1 |
| Student_40 | S11 (Q31) | 1 | 1 | 1.5 |
| Student_40 | S13 (Q33) | 0 | 0 | 0.5 |
| Student_40 | S14 (Q34) | 2 | 1.5 | 2 |
| Student_41 | S1 (Q21) | 2 | 1.5 | 2 |
| Student_41 | S2 (Q22) | 1 | 0 | 0.5 |
| Student_41 | S3 (Q23) | 2 | 0.5 | 1 |
| Student_41 | S4 (Q24) | 1 | 0.5 | 1 |
| Student_41 | S5 (Q25) | 2 | 2 | 2 |
| Student_41 | S6 (Q26) | 0 | 0 | 0.5 |
| Student_41 | S7 (Q27) | 2 | 1 | 1.5 |
| Student_41 | S8 (Q28) | 2 | 1 | 1.5 |
| Student_41 | S9 (Q29) | 1 | 0.5 | 1 |
| Student_41 | S11 (Q31) | 1 | 1 | 1.5 |
| Student_41 | S12 (Q32) | 0 | 0 | 0.5 |
| Student_41 | S14 (Q34) | 1 | 0 | 0.5 |
| Student_42 | S1 (Q21) | 2 | 2 | 2 |
| Student_42 | S2 (Q22) | 2 | 2 | 2 |
| Student_42 | S3 (Q23) | 2 | 1 | 1.5 |
| Student_42 | S4 (Q24) | 2 | 2 | 2 |
| Student_42 | S5 (Q25) | 2 | 2 | 2 |
| Student_42 | S6 (Q26) | 2 | 0 | 0.5 |
| Student_42 | S7 (Q27) | 2 | 1 | 1.5 |
| Student_42 | S8 (Q28) | 2 | 2 | 2 |
| Student_42 | S9 (Q29) | 2 | 1 | 1.5 |
| Student_42 | S10 (Q30) | 2 | 1 | 1.5 |
| Student_42 | S11 (Q31) | 2 | 0 | 0.5 |
| Student_42 | S12 (Q32) | 0 | 0 | 0.5 |
| Student_42 | S13 (Q33) | 0 | 0 | 0.5 |
| Student_42 | S14 (Q34) | 2 | 1 | 1.5 |
| Student_42 | S15 (Q35) | 2 | 1.5 | 2 |
| Student_43 | S1 (Q21) | 2 | 2 | 2 |
| Student_43 | S2 (Q22) | 2 | 0 | 0.5 |
| Student_43 | S3 (Q23) | 2 | 1 | 1.5 |
| Student_43 | S4 (Q24) | 2 | 2 | 2 |
| Student_43 | S5 (Q25) | 2 | 2 | 2 |
| Student_43 | S6 (Q26) | 1.5 | 0.5 | 1 |
| Student_43 | S7 (Q27) | 2 | 1 | 1.5 |
| Student_43 | S8 (Q28) | 2 | 2 | 2 |
| Student_43 | S9 (Q29) | 1 | 0.5 | 1 |
| Student_43 | S11 (Q31) | 2 | 1 | 1.5 |
| Student_43 | S14 (Q34) | 2 | 1.5 | 2 |
| Student_44 | S2 (Q22) | 2 | TA | TA |
| Student_44 | S3 (Q23) | 2 | 0.5 | 1 |
| Student_44 | S4 (Q24) | 2 | 1 | 1.5 |
| Student_44 | S5 (Q25) | 2 | 2 | 2 |
| Student_44 | S6 (Q26) | 2 | 1.5 | 2 |
| Student_44 | S7 (Q27) | 2 | 1 | 1.5 |
| Student_44 | S8 (Q28) | 2 | 2 | 2 |
| Student_44 | S9 (Q29) | 2 | 1 | 1.5 |
| Student_44 | S10 (Q30) | 1 | 0.5 | 1 |
| Student_44 | S11 (Q31) | 2 | 1 | 1.5 |
| Student_44 | S14 (Q34) | 2 | 2 | 2 |
| Student_45 | S1 (Q21) | 2 | 2 | 2 |
| Student_45 | S2 (Q22) | 2 | 1 | 1.5 |
| Student_45 | S5 (Q25) | 2 | 2 | 2 |
| Student_45 | S6 (Q26) | 1 | 2 | 2 |
| Student_45 | S7 (Q27) | 2 | 1 | 1.5 |
| Student_45 | S8 (Q28) | 2 | 2 | 2 |
| Student_45 | S9 (Q29) | 1 | 1 | 1.5 |
| Student_46 | S1 (Q21) | 2 | 2 | 2 |
| Student_46 | S2 (Q22) | 2 | 2 | 2 |
| Student_46 | S4 (Q24) | 1 | 2 | 2 |
| Student_46 | S5 (Q25) | 2 | 2 | 2 |
| Student_46 | S6 (Q26) | 2 | 2 | 2 |
| Student_46 | S7 (Q27) | 2 | 1 | 1.5 |
| Student_46 | S8 (Q28) | 2 | 1 | 1.5 |
| Student_46 | S9 (Q29) | 1 | 2 | 2 |
| Student_46 | S10 (Q30) | 1 | 2 | 2 |
| Student_46 | S11 (Q31) | 2 | 1 | 1.5 |
| Student_46 | S12 (Q32) | 0 | 0 | 0.5 |
| Student_46 | S14 (Q34) | 2 | 2 | 2 |
| Student_46 | S15 (Q35) | 2 | 0 | 0.5 |
| Student_47 | S1 (Q21) | 2 | 2 | 2 |
| Student_47 | S3 (Q23) | 2 | 1 | 1.5 |
| Student_47 | S5 (Q25) | 2 | 2 | 2 |
| Student_47 | S6 (Q26) | 2 | 2 | 2 |
| Student_47 | S7 (Q27) | 2 | TA | TA |
| Student_47 | S8 (Q28) | 2 | 1 | 1.5 |
| Student_47 | S9 (Q29) | 2 | 1 | 1.5 |
| Student_47 | S11 (Q31) | 2 | 0.5 | 1 |
| Student_47 | S14 (Q34) | 2 | 1 | 1.5 |
| Student_48 | S1 (Q21) | 2 | 2 | 2 |
| Student_48 | S2 (Q22) | 1 | 0 | 0.5 |
| Student_48 | S4 (Q24) | 1 | 0 | 0.5 |
| Student_48 | S5 (Q25) | 0 | 0 | 0.5 |
| Student_48 | S6 (Q26) | 2 | 1 | 1.5 |
| Student_48 | S7 (Q27) | 2 | 0 | 0.5 |
| Student_48 | S8 (Q28) | 2 | 1 | 1.5 |
| Student_48 | S12 (Q32) | 1 | 0 | 0.5 |
| Student_49 | S1 (Q21) | 2 | 2 | 2 |
| Student_49 | S2 (Q22) | 2 | 0 | 0.5 |
| Student_49 | S3 (Q23) | 0 | TA | TA |
| Student_49 | S4 (Q24) | 1 | 0 | 0.5 |
| Student_49 | S5 (Q25) | 2 | 2 | 2 |
| Student_49 | S6 (Q26) | 2 | 1.5 | 2 |
| Student_49 | S7 (Q27) | 1 | 0.5 | 1 |
| Student_49 | S8 (Q28) | 2 | 2 | 2 |
| Student_49 | S9 (Q29) | 1 | 1 | 1.5 |
| Student_49 | S11 (Q31) | 1 | 0 | 0.5 |
| Student_50 | S1 (Q21) | 2 | 2 | 2 |
| Student_50 | S2 (Q22) | 2 | 0 | 0.5 |
| Student_50 | S3 (Q23) | 1 | 1 | 1.5 |
| Student_50 | S4 (Q24) | 2 | 1 | 1.5 |
| Student_50 | S5 (Q25) | 2 | 2 | 2 |
| Student_50 | S6 (Q26) | 2 | 2 | 2 |
| Student_50 | S7 (Q27) | 2 | 1 | 1.5 |
| Student_50 | S8 (Q28) | 2 | 2 | 2 |
| Student_50 | S9 (Q29) | 2 | 1 | 1.5 |
| Student_50 | S10 (Q30) | 0 | 0.5 | 1 |
| Student_50 | S11 (Q31) | 2 | 2 | 2 |
| Student_50 | S12 (Q32) | 0 | 0 | 0.5 |
| Student_50 | S13 (Q33) | 0 | 0 | 0.5 |
| Student_50 | S14 (Q34) | 2 | 1 | 1.5 |
| Student_50 | S15 (Q35) | 1 | 0 | 0.5 |
