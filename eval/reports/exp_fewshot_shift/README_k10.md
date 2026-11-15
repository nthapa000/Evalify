# Few-shot + shift with 10 teacher-marked sheets (Mendeley, experiment)

Generated 2026-11-15 14:23 by `python eval/exp_fewshot_shift.py score`. Transcripts: whole page (pagetext). Grader Gemma + prompt v2. Tested on the sheets NOT used for calibration; shifts are learned on the calibration sheets only (few-shot marks there use leave-one-sheet-out examples).

| seed | n | method | MAE | exact | within 0.5 | QWK | bias | grader s/answer |
|---|---|---|---|---|---|---|---|---|
| 0 | 437 | no calibration | 0.596 | 38% | 55% | 0.495 | -0.493 | 12.7 |
| 0 | 437 | global shift | 0.416 | 37% | 85% | 0.618 | -0.119 | 12.7 |
| 0 | 437 | per-question shift | 0.376 | 45% | 83% | 0.619 | -0.029 | 12.7 |
| 0 | 437 | few-shot | 0.452 | 50% | 66% | 0.597 | -0.28 | 62.1 |
| 0 | 437 | few-shot + global shift | 0.364 | 45% | 86% | 0.648 | 0.032 | 62.1 |
| 0 | 437 | few-shot + per-question shift | 0.37 | 45% | 85% | 0.647 | -0.006 | 62.1 |
| 1 | 438 | no calibration | 0.604 | 38% | 56% | 0.489 | -0.503 | 12.5 |
| 1 | 438 | global shift | 0.422 | 37% | 84% | 0.612 | -0.128 | 12.5 |
| 1 | 438 | per-question shift | 0.394 | 44% | 82% | 0.601 | -0.031 | 12.5 |
| 1 | 438 | few-shot | 0.447 | 51% | 67% | 0.603 | -0.285 | 59.3 |
| 1 | 438 | few-shot + global shift | 0.365 | 45% | 86% | 0.655 | 0.021 | 59.3 |
| 1 | 438 | few-shot + per-question shift | 0.369 | 45% | 84% | 0.666 | -0.029 | 59.3 |
