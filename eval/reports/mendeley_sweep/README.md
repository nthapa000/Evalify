# Type-C sweep — Mendeley exam sheets (MCQ + short answers)

Generated 2026-11-15 11:44 by `python eval/mendeley_sweep.py score`. 50 real scanned exam sheets, gold = the teacher's CSV (chosen MCQ letter; mark per short answer, 0–2).

## 1. MCQ part (20 per sheet)

Gold is the teacher's CSV, which has at least one known typo (Student_2 Q1) — a few 'silent errors' may be CSV errors.
`crop:qwen>X` = Qwen segments, X reads the crop; `page>X` = X reads whole pages.

### Top 10

| arch | readers | items | silent_errors | auto_rate | ta_items | sec_per_paper |
|---|---|---|---|---|---|---|
| single | crop:qwen>gemma | 1000 | 0 | 0.006 | 994 | 604.3 |
| pair | crop:qwen>gemma + page>paddle | 1000 | 0 | 0.002 | 998 | 610.0 |
| pair | crop:qwen>gemma + page>glm | 1000 | 0 | 0.002 | 998 | 610.7 |
| pair | crop:qwen>gemma + crop:qwen>qwen | 1000 | 0 | 0.002 | 998 | 632.1 |
| pair | crop:qwen>gemma + page>chandra | 1000 | 0 | 0.002 | 998 | 640.2 |
| pair | crop:qwen>gemma + page>qwen | 1000 | 0 | 0.002 | 998 | 669.3 |
| pair | crop:qwen>gemma + page>gemma | 1000 | 0 | 0.002 | 998 | 690.4 |
| pair | crop:qwen>gemma + crop:qwen>paddle | 1000 | 0 | 0.001 | 999 | 611.2 |
| pair | crop:qwen>chandra + crop:qwen>gemma | 1000 | 0 | 0.001 | 999 | 635.3 |
| pair | crop:qwen>gemma + crop:qwen>glm | 1000 | 0 | 0.0 | 1000 | 608.6 |

### Single readers

| arch | readers | items | silent_errors | auto_rate | ta_items | sec_per_paper |
|---|---|---|---|---|---|---|
| single | crop:qwen>gemma | 1000 | 0 | 0.006 | 994 | 604.3 |
| single | page>gemma | 1000 | 17 | 1.0 | 0 | 86.0 |
| single | page>qwen | 1000 | 23 | 0.993 | 7 | 64.9 |
| single | crop:qwen>paddle | 1000 | 40 | 0.939 | 61 | 6.9 |
| single | crop:qwen>glm | 1000 | 42 | 0.914 | 86 | 4.3 |
| single | crop:qwen>chandra | 1000 | 44 | 0.878 | 122 | 31.0 |
| single | crop:qwen>qwen | 1000 | 91 | 0.977 | 23 | 27.7 |
| single | page>paddle | 1000 | 147 | 0.975 | 25 | 5.7 |
| single | page>glm | 1000 | 156 | 0.975 | 25 | 6.3 |
| single | page>chandra | 1000 | 165 | 0.978 | 22 | 35.8 |

Planned / current set-up `page>gemma + page>qwen + page>glm`:

| arch | readers | items | silent_errors | auto_rate | ta_items | sec_per_paper |
|---|---|---|---|---|---|---|
| pair+tiebreak | page>gemma + page>qwen + page>glm | 1000 | 13 | 0.965 | 35 | 157.3 |
| pair+majority | page>gemma + page>qwen + page>glm | 1000 | 15 | 0.987 | 13 | 157.3 |

## 2. Short answers — grader set-ups (transcripts: Qwen + GLM-OCR)

exact = same mark as the teacher; within_0.5; MAE in marks (out of 2); QWK (agreement, 1 = perfect); bias > 0 = more generous than the teacher; s/answer = grader time.

| grader | n | exact | within_0.5 | MAE | QWK | bias | grader s/answer | grader s/paper |
|---|---|---|---|---|---|---|---|---|
| qwen-v1 | 564 | 0.369 | 0.392 | 0.782 | 0.329 | -0.706 | 6.9 | 77 |
| qwen-v2 | 564 | 0.291 | 0.518 | 0.726 | 0.367 | -0.668 | 7.5 | 85 |
| qwen-v2-think | 564 | 0.285 | 0.454 | 0.794 | 0.327 | -0.734 | 40.2 | 454 |
| gemma-v1 | 564 | 0.422 | 0.445 | 0.702 | 0.384 | -0.617 | 10.6 | 120 |
| gemma-v2 | 564 | 0.374 | 0.525 | 0.665 | 0.411 | -0.571 | 13.0 | 147 |

**Best by MAE: `gemma-v2`.** Difference in MAE vs each other set-up (negative = `gemma-v2` is closer to the teacher), with a 95 % interval from resampling the 50 papers:

| vs | MAE difference | 95 % interval | verdict |
|---|---|---|---|
| qwen-v1 | -0.117 | [-0.151, -0.084] | better |
| qwen-v2 | -0.061 | [-0.089, -0.031] | better |
| qwen-v2-think | -0.129 | [-0.163, -0.095] | better |
| gemma-v1 | -0.037 | [-0.055, -0.021] | better |

## 3. Short answers — transcript pairs (grader `gemma-v2`)

| transcripts | n | exact | within_0.5 | MAE | QWK | bias | s/paper (2 readers + grader) |
|---|---|---|---|---|---|---|---|
| qwen + chandra | 564 | 0.379 | 0.527 | 0.659 | 0.414 | -0.563 | 261 |
| paddle + chandra | 564 | 0.379 | 0.523 | 0.662 | 0.414 | -0.57 | 236 |
| gemma + chandra | 564 | 0.379 | 0.525 | 0.663 | 0.409 | -0.567 | 282 |
| qwen + paddle | 564 | 0.376 | 0.523 | 0.664 | 0.412 | -0.568 | 248 |
| qwen + gemma | 564 | 0.371 | 0.523 | 0.665 | 0.414 | -0.571 | 298 |
| qwen + glm | 564 | 0.374 | 0.525 | 0.665 | 0.411 | -0.571 | 178 |
| glm + chandra | 564 | 0.372 | 0.525 | 0.666 | 0.408 | -0.568 | 233 |
| gemma + paddle | 564 | 0.374 | 0.518 | 0.67 | 0.407 | -0.574 | 277 |
| gemma + glm | 564 | 0.371 | 0.521 | 0.671 | 0.406 | -0.575 | 275 |
| paddle + glm | 564 | 0.371 | 0.521 | 0.672 | 0.406 | -0.582 | 220 |

## 4. Two graders (grader 1 + grader 2; differ by ≥ 1 mark → TA)

| grader 1 | grader 2 | auto | TA | exact (auto) | MAE (auto) | big errors (auto, ≥ 1 mark off) | graders s/paper |
|---|---|---|---|---|---|---|---|
| qwen-v2 | gemma-v1 | 92% | 45 | 0.293 | 0.724 | 240 | 205 |
| qwen-v2 | qwen-v1 | 91% | 48 | 0.289 | 0.731 | 241 | 162 |
| gemma-v2 | qwen-v1 | 91% | 52 | 0.355 | 0.689 | 249 | 224 |
| gemma-v2 | qwen-v2-think | 91% | 49 | 0.359 | 0.687 | 251 | 601 |
| qwen-v2 | gemma-v2 | 95% | 30 | 0.294 | 0.721 | 252 | 232 |
| qwen-v2-think | gemma-v1 | 89% | 63 | 0.303 | 0.749 | 254 | 574 |
| qwen-v2-think | qwen-v1 | 89% | 62 | 0.301 | 0.757 | 257 | 531 |
| gemma-v2 | gemma-v1 | 97% | 15 | 0.377 | 0.664 | 258 | 267 |
| qwen-v2 | qwen-v2-think | 93% | 37 | 0.277 | 0.742 | 258 | 539 |
| gemma-v2 | qwen-v2 | 95% | 30 | 0.367 | 0.679 | 260 | 232 |
| qwen-v2-think | gemma-v2 | 91% | 49 | 0.305 | 0.746 | 264 | 601 |
| qwen-v2-think | qwen-v2 | 93% | 37 | 0.298 | 0.762 | 279 | 539 |

## 5. Time per paper (model seconds, summed over calls)

Sum of each call's latency for one sheet (35 answers, ~4 pages). The server runs many calls in parallel, so wall-clock time per sheet is lower; `wall` is what one sheet took in these runs with every model at once.

| step | avg s / paper |
|---|---|
| segmentation (Qwen) | 40 |
| read all 35 crops: qwen | 55 |
| read all 35 crops: gemma | 661 |
| read all 35 crops: paddle | 13 |
| read all 35 crops: glm | 9 |
| read all 35 crops: chandra | 49 |
| MCQ whole pages: page>qwen | 65 |
| MCQ whole pages: page>gemma | 86 |
| MCQ whole pages: page>paddle | 6 |
| MCQ whole pages: page>glm | 6 |
| MCQ whole pages: page>chandra | 36 |
| grade short answers: qwen-v1 | 77 |
| grade short answers: qwen-v2 | 85 |
| grade short answers: qwen-v2-think | 454 |
| grade short answers: gemma-v1 | 120 |
| grade short answers: gemma-v2 | 147 |

Wall-clock in these runs: reading (segment + 5 readers in parallel) 122 s / paper; whole-page MCQ (5 models in parallel) 96 s / paper.
