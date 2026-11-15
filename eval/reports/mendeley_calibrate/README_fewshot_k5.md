# Few-shot teacher calibration (5 teacher-marked sheets, Mendeley)

Generated 2026-11-15 12:51 by `python eval/mendeley_calibrate.py fewshot`. Grader Gemma + prompt v2 (p6) with, for each question, the calibration sheets' answers (Qwen transcript) and the teacher's marks. Same baseline transcripts (Qwen + GLM-OCR crops); answers not located left out. Compared on the same held-out answers with: no calibration, and the global shift learned from the same sheets.

| seed | calibration sheets | n | method | MAE | exact | within 0.5 | QWK | bias |
|---|---|---|---|---|---|---|---|---|
| 0 | 11, 24, 31, 33, 8 | 463 | none | 0.592 | 0.402 | 0.557 | 0.492 | -0.484 |
| 0 | 11, 24, 31, 33, 8 | 463 | global shift | 0.43 | 0.359 | 0.838 | 0.605 | -0.119 |
| 0 | 11, 24, 31, 33, 8 | 463 | few-shot | 0.484 | 0.462 | 0.657 | 0.565 | -0.322 |
| 0 | | | few-shot grader s/answer | 41.5 | | | | |
| 1 | 13, 17, 24, 42, 8 | 456 | none | 0.606 | 0.393 | 0.55 | 0.475 | -0.497 |
| 1 | 13, 17, 24, 42, 8 | 456 | global shift | 0.44 | 0.353 | 0.827 | 0.587 | -0.128 |
| 1 | 13, 17, 24, 42, 8 | 456 | few-shot | 0.484 | 0.482 | 0.638 | 0.565 | -0.308 |
| 1 | | | few-shot grader s/answer | 50.1 | | | | |
