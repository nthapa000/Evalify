# EDU-CIRCUIT-HW — findings (run 8, 15 Nov 2026)

Full tables: [README.md](README.md) (`python eval/edu_circuit.py score`). 213 handwritten circuit-homework
solutions (Georgia Tech ECE 2040), 702 final numerical values. Gold = the student's final value from the
expert transcription (Qwen and Gemma must agree); expected values from the rubric notes. Our rule: value
within ±0.001, unit ignored. Licence not stated → internal evaluation only.

Only the **final numbers** were checked, not marking of the working (part marks for method).

## Readers alone — how often the final value is read correctly (`python eval/edu_read_accuracy.py`)

| Reader | Read correctly | Wrong number | Missed (said blank) | Invented (gold blank) | s / solution |
|---|---|---|---|---|---|
| Chandra → Qwen | **86.6 %** | 25 | 38 | 31 | 47 |
| Gemma | 83.9 % | 30 | 49 | 34 | 7 |
| Qwen | 82.9 % | 34 | 22 | 64 | 18 |
| GLM-OCR → Qwen | 78.9 % | 33 | 85 | 30 | 20 |
| PaddleOCR → Qwen | 66.0 % | 57 | 151 | 31 | 22 |

Most failures are about *finding* the final answer inside the working (missed / invented), not misread digits.

## Architectures

| Set-up | Silent errors | Auto | To TA | s / solution |
|---|---|---|---|---|
| best single (Chandra → Qwen) | 81 | 100 % | 0 | 47 |
| **pair Chandra → Qwen + Gemma** (best) | **30** | 79.5 % | 144 | 55 |
| pair + tie-break (+ Qwen) | 30 | 79.5 % | 144 | 72 |
| pair + majority (+ Qwen) | 63 | 96.6 % | 24 | 72 |

## Conclusions

- Final numbers buried in long working are much harder than answer boxes (own sheets: 0 silent errors).
  Even the best pair accepts 30 / 702 (4.3 %) wrong marks.
- For numerical questions the answer sheet should have a **final-answer box**; then the type-B pipeline
  applies. Free working without a box → pair + TA, never majority (majority doubles silent errors).
- Not yet done: inspect the 30 errors (reader vs gold problems); deduction-based marking of the working.
