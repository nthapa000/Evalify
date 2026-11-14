# Findings — reader comparison on 12 real Mendeley sheets (14 Nov 2026)

Numbers: [README.md](README.md) · per-sheet evidence: `Student_N.md` · Claude's visual check: `review/`.
Readers are self-hosted (cn07). Claude only produced reference transcripts (3 sheets) and the
visual verdicts below — **these are an AI's reading; please verify against the crops.**

## Results

| | MCQ letters (240, vs teacher CSV) | Short answers (36, CER vs Claude's transcripts) |
|---|---|---|
| PaddleOCR-VL | **94.6 %** (3 wrong, 10 empty) | 0.102 |
| GLM-OCR | 91.2 % (4 wrong, 17 empty) | 0.097 |
| Chandra OCR 2 | 89.2 % (3 wrong, 23 empty) | 0.181 (worst) |
| Qwen3.8 | 76.7 % (2 wrong, **54 empty**) | **0.071** (best) |

## What the visual check of the 30 disputed MCQ answers showed

1. **Unusual "D" (written like "Ɗ" or circled) is the main difficulty** — 14 cases. Readers leave it
   empty rather than guess, so it is safe (tie-breaker / TA) but costs coverage. Qwen3.8 abstains most.
2. **Struck-out letters**: Chandra, PaddleOCR and GLM-OCR sometimes report both the struck-out and the
   new letter (Student_2 Q6, Student_9 Q20). On Student_9 Q20 PaddleOCR **and** GLM-OCR both said
   "B,C" → the pipeline would have auto-accepted a wrong answer (a silent error).
3. **Words after the letter** ("D, All of the…", "B, a real…") — Chandra / PaddleOCR picked up the "a".
4. **Qwen3.8's only 2 wrong letters were invented** (it added a C and an A that are not on the page).
5. **Student_2 Q1: the teacher CSV says A, but PaddleOCR and Claude read "B"** — likely a CSV error.
6. **Segmentation**: Student_12 Q2/Q3 crops show the wrong answer; 6 sheets have 29–32 of 35
   answers located (mostly genuinely unanswered questions — check the per-sheet pages).
7. **Blank backs**: 8 of 12 sheets include the scanned blank back of a page with mirrored show-through;
   the quality gate now skips them (it would otherwise have "read" ghost answers).

## What this suggests (decision pending with the user)

- Your hunch that an OCR specialist should read is **right for MCQ/numbers** (PaddleOCR 94.6 % vs Qwen 76.7 %),
  but **Chandra is not that specialist here**: it is third on MCQ and worst on paragraphs.
- **Qwen3.8 reads paragraphs best** (lowest CER) but abstains a lot on single letters.
- A split by question type fits the data: **MCQ / numerical: A = PaddleOCR, B = GLM-OCR, tie-break = Qwen3.8**
  (PaddleOCR + GLM-OCR share the fewest mistakes: 9 of 25); **subjective: A = Qwen3.8, B = PaddleOCR or GLM-OCR**.
- Struck-out letters are the main silent-error risk for MCQ; the MCQ prompt / parsing should treat
  two letters where one is struck as a single answer, and "two letters" should route to a TA unless the
  paper allows multiple answers.

## Limits

12 sheets from one course, scanned (not phone photos), MCQ only checked against a CSV that has at least
one probable error; short-answer CER rests on Claude's transcripts of 3 sheets (36 answers).
