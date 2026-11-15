# Type C on real exam sheets — findings (Mendeley sf3kvjwknt, 50 sheets, run 7, 15 Nov 2026)

Full tables: [README.md](README.md) (`python eval/mendeley_sweep.py score`). Gold = the teacher's CSV
(`Teacher_manual_marks_Anonymized.csv`). 20 MCQ + 15 short answers (0–2 marks) per sheet; 1,000 MCQ and
564 marked short answers.

## Recommended type-C set-up

| Part | Set-up | Result on 50 sheets | Model time / paper |
|---|---|---|---|
| MCQ (20) | whole page: Gemma + Qwen, GLM-OCR majority vote | 15 "silent errors", but ~14 are teacher-CSV errors (below); 98.7 % auto, 13 to TA | 157 s |
| Short answers (15) | segment (Qwen) → transcripts Qwen + GLM-OCR → grader **Gemma, prompt v2** | MAE 0.665 / 2, exact 37 %, within 0.5: 52 %, QWK 0.41, bias −0.57 | 40 + 64 + 147 ≈ 250 s |

Wall-clock with all models running in parallel: about 2–4 minutes per paper.

## 1. MCQ — the "errors" are mostly the teacher's CSV

Gemma and Qwen (whole page) agree with each other but not with the CSV on 13 answers. Checked by hand:

| Cases | What it is |
|---|---|
| Student_34 Q17–Q20 (4) | CSV row garbled: the sheet shows 17→A, 18→C; the CSV has B, B, "2", blank |
| Student_46 Q18, Q19 (2) | CSV blank, the student answered |
| Student_2 Q1, Student_23 Q20, Student_25 Q10, Student_26 Q13, Student_38 Q20, Student_49 Q19 (6) | every model that answered agrees against the CSV → almost certainly CSV typos |
| Student_15 Q19 (1) | **real model error**: the student's "A" (looped shape) read as "B" by Gemma and Qwen; teacher and the 3 OCR models say A |

→ Real silent-error rate is about **1 / 1000**. Single readers: Gemma page 98.3 %, Qwen page 97.7 % agreement
with the CSV; OCR models on whole pages 83–85 %.

**Gemma on single-answer crops does not work**: with JSON-constrained decoding it answers "unclear" or the
JSON runs away (`"B","B","B",…`) on 994 / 1000 crops (same as our own sheets, 85 %). Not a script bug — a
Gemma + guided-JSON behaviour. Rule: Gemma reads **whole pages only** (or plain text for long answers).

## 2. Short answers — which grader

| Grader | MAE | Exact | Within 0.5 | QWK | Bias | s / paper |
|---|---|---|---|---|---|---|
| Qwen, prompt v1 | 0.782 | 36.9 % | 39.2 % | 0.33 | −0.71 | 77 |
| Qwen, prompt v2 | 0.726 | 29.1 % | 51.8 % | 0.37 | −0.67 | 85 |
| Qwen, v2 + thinking | 0.794 | 28.5 % | 45.4 % | 0.33 | −0.73 | 454 |
| Gemma, prompt v1 | 0.702 | 42.2 % | 44.5 % | 0.38 | −0.62 | 120 |
| **Gemma, prompt v2** | **0.665** | 37.4 % | **52.5 %** | **0.41** | **−0.57** | 147 |

- **Prompt v2 helps** both models (Gemma −0.037 MAE, 95 % interval [−0.055, −0.021]; Qwen −0.056). Exact
  drops because half credit gives 1 where the teacher gave 0 or 2; within-0.5 rises sharply.
- **Thinking mode hurts** (worse MAE) and is ~5× slower → off.
- **A second grader adds nothing**: best grader pairs reach MAE 0.664–0.69 on auto-accepted answers, same as
  Gemma v2 alone, and still accept ~250 answers that are ≥ 1 mark off. One grader + TA routing is enough.

## 3. Short answers — which transcripts (grader Gemma v2)

All 10 reader pairs give MAE **0.659–0.672** — reading is not the bottleneck. Qwen + Chandra is best
(0.659, 261 s/paper); **Qwen + GLM-OCR** is chosen (0.665, 178 s/paper — 30 % faster, same accuracy).

## 4. Why the grader is 0.57 marks stricter than the teacher

`python eval/mendeley_strictness.py`. Teacher mark → grader mark: teacher 2 → grader 0 in 49 answers,
teacher 1 → grader 0 in 87. Hardest questions: S2 (overfitting) −1.0, S7 (outliers) −0.89, S9 (K-NN
normalisation) −0.89, S15 (RBF) −0.83; S5 (applications) matches (−0.01). Rubrics are aligned with the
questions (shifting the CSV columns makes MAE worse: 0.84 / 0.97).

1. **Answers not found by segmentation: 41** (38 with teacher marks > 0) → scored 0. MAE 1.48 on those;
   19 % of the total shortfall.
2. **Hand review of 20 random big disagreements** (teacher ≥ 1.5 marks above the grader):

| Verdict | n | Example |
|---|---|---|
| Teacher lenient — answer wrong / empty by the rubric | 10 | S9 "normalization helps to maximize and minimize the value" → teacher 2; S15 "RBF uses margin vector to calculate distance" → 2 |
| Grader too harsh — partly right, worth ~1–1.5 | 6 | S3 "regression predicts continuous values" → grader 0–0.5 |
| Segmentation fault — wrong text graded | 4 | crossed-out first attempt picked (Student_3 Q22); S10 crop holds the S4 answer; S12 crop cut short |

So about half of the gap is **this teacher giving full marks to almost any attempt**; the rest is the
segmenter (missing / crossed-out / mixed crops) and some over-strictness on vague but partly right answers.

## What to fix

1. **Segmentation**: ignore struck-out text, find answers written out of order, never mix two answers in
   one crop; an answer not found → TA, never an automatic 0.
2. **Teacher calibration** (proposal): the teacher marks ~5 sheets first; those marked answers are given to
   the grader as examples of how strict this teacher is. Without it, an LLM following the rubric will be
   stricter than a lenient teacher.
3. Grader routing to TA by confidence / disagreement still needed — grading is ~37 % exact against this
   teacher, so type C cannot be fully automatic yet.

Limits: one subject, one teacher, 15 questions; rubrics drafted from the answer key (user-approved).
