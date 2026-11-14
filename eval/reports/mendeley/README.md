# Reader comparison on real handwriting — Mendeley exam set

Dataset: *A Dataset of Digitized Student Examination Papers…*, Dinesh K P, Mendeley Data sf3kvjwknt v1, **CC BY 4.0** (https://data.mendeley.com/datasets/sf3kvjwknt/1). 12 sheets (Student_1 … Student_12), Data Science exam: 20 MCQ + 15 short answers.

## How this was produced

1. `eval/build_mendeley.py` rendered each PDF page and took gold from `Teacher_manual_marks_Anonymized.csv` (MCQ letter chosen; teacher mark per short answer).
2. `eval/mendeley_readers.py`: quality gate (blank / show-through backs skipped) → Qwen3.8 segmenter finds each answer by its written number → one crop per answer → four readers on every crop.
3. Claude visually checked the crops: MCQ disagreements, and full transcripts of the short answers on the sheets marked ✔ below (`review/<sheet>.json`). **These transcripts are an AI's reading — please verify them against the crops.**
4. `eval/make_mendeley_report.py` built these pages.

## MCQ reading (240 answers, gold = teacher CSV)

| reader | correct | wrong letter | no answer | accuracy |
|---|---|---|---|---|
| Qwen3.8 | 184 | 2 | 54 | 76.7% |
| Chandra | 214 | 3 | 23 | 89.2% |
| PaddleOCR | 227 | 3 | 10 | 94.6% |
| GLM-OCR | 219 | 4 | 17 | 91.2% |

**Shared mistakes per reader pair** (items both got wrong or empty, out of items either got wrong/empty). A good reader pair has few shared mistakes.

| pair | both wrong | either wrong |
|---|---|---|
| PaddleOCR + GLM-OCR | 9 | 25 |
| Chandra + PaddleOCR | 9 | 30 |
| Qwen3.8 + PaddleOCR | 10 | 59 |
| Chandra + GLM-OCR | 14 | 33 |
| Qwen3.8 + GLM-OCR | 19 | 58 |
| Qwen3.8 + Chandra | 20 | 62 |

## Short-answer reading (vs Claude's transcripts)

| reader | answers | mean CER | mean WER |
|---|---|---|---|
| Qwen3.8 | 36 | 0.071 | 0.108 |
| Chandra | 36 | 0.181 | 0.227 |
| PaddleOCR | 36 | 0.102 | 0.143 |
| GLM-OCR | 36 | 0.097 | 0.137 |

## Sheets

| sheet | answers located | blank pages skipped | Qwen3.8 MCQ | Chandra MCQ | PaddleOCR MCQ | GLM-OCR MCQ | transcribed |
|---|---|---|---|---|---|---|---|
| [Student_1](Student_1.md) | 35/35 | Student_1_p4.png | 16/20 | 19/20 | 20/20 | 18/20 | ✔ |
| [Student_2](Student_2.md) | 29/35 | Student_2_p4.png | 17/20 | 18/20 | 18/20 | 18/20 | ✔ |
| [Student_3](Student_3.md) | 32/35 | Student_3_p4.png | 15/20 | 15/20 | 16/20 | 15/20 | ✔ |
| [Student_4](Student_4.md) | 35/35 | Student_4_p4.png | 16/20 | 19/20 | 20/20 | 20/20 |  |
| [Student_5](Student_5.md) | 31/35 | Student_5_p4.png | 14/20 | 18/20 | 20/20 | 18/20 |  |
| [Student_6](Student_6.md) | 29/35 | Student_6_p4.png | 12/20 | 18/20 | 19/20 | 18/20 |  |
| [Student_7](Student_7.md) | 34/35 | Student_7_p4.png | 10/20 | 17/20 | 18/20 | 17/20 |  |
| [Student_8](Student_8.md) | 30/35 | Student_8_p4.png | 15/20 | 20/20 | 19/20 | 20/20 |  |
| [Student_9](Student_9.md) | 35/35 | — | 16/20 | 15/20 | 18/20 | 19/20 |  |
| [Student_10](Student_10.md) | 29/35 | — | 16/20 | 18/20 | 19/20 | 19/20 |  |
| [Student_11](Student_11.md) | 35/35 | — | 20/20 | 19/20 | 20/20 | 20/20 |  |
| [Student_12](Student_12.md) | 32/35 | — | 17/20 | 18/20 | 20/20 | 17/20 |  |

## Caveats

- Gold MCQ letters come from the teacher's CSV; a CSV typo would count as a reader error.
- Short-answer transcripts are Claude's reading of the crops, not a human's.
- Teacher CSV oddities: blank / `NC` cells (not attempted or not corrected); Student_11 Q34 = 4.0 although each short answer is out of 2.
- Rubrics for grading (Q21–Q35) were drafted by Claude from `answerkey.txt` — grading is a separate step.
