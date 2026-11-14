# Evalify: Test Datasets Plan (14 Nov 2026)

Purpose: datasets we will use to test the Evalify pipeline (OMR, handwriting reading, numerical, subjective grading) until we have our own labelled sheets. These are for evaluation only. Do not train on them, do not redistribute them, and drop restricted ones once our own dataset exists.

Status note: none of these were downloaded or opened during the research. Licence and file details come from web pages and search results, so verify each licence before use. Several licences were not visible and are marked as such.

## 1. Datasets in the plan

| Plan stage | Dataset | Size and content | Licence | Link |
|---|---|---|---|---|
| Type 1: OMR bubbles | Tamaulipas MCQ Exam Image Dataset (Mendeley, 18 Mar 2026) | 5721 scanned four-choice answer sheets completed by high school students | Not seen, check the page | https://data.mendeley.com/datasets/djmynjwjpy |
| Type 1: OMR bubbles (backup) | Afifi MCQ dataset | 735 answer sheets, 33,540 answer boxes, 6 real exams, XPS and PNG | Free for reasonable academic fair use | https://sites.google.com/view/mcq-dataset |
| Types 1 and 3: handwritten MCQ and short answers | Mendeley student exam set (Dinesh K P, 14 Apr 2026) | 50 students, 20 MCQs (1 mark) and 15 short answers (2 marks), key and rubric, uncorrected and corrected PDFs, per-question marks CSV | CC BY 4.0 | https://data.mendeley.com/datasets/sf3kvjwknt/1 |
| Type 2: numerical answers | FERMAT (AI4Bharat, ACL 2025) | 2,244 handwritten solved math problems with deliberate errors, gold solution in LaTeX | Not confirmed | https://huggingface.co/datasets/ai4bharat/FERMAT |
| Type 3: handwriting to score | Handwritten ASAP Short Answer Scoring (Zenodo, 2020) | Students rewrote ASAP short answers by hand, derived from the Kaggle ASAP-SAS data | Marked open, licence not confirmed | https://zenodo.org/records/8088866 |
| Type 3: grader on gold text | SciEntsBank | Student response analysis corpus with reference answers | CC BY 4.0 | https://huggingface.co/datasets/nkazi/SciEntsBank |
| Type 3: grader on gold text | Mohler ASAG | 2,442 computer-science student responses | CC BY 4.0 | https://huggingface.co/datasets/Viswa45/ASAG |
| Type 3: rubric grading on real STEM work | EDU-CIRCUIT-HW (Georgia Tech) | 1,334 student handwritten solutions, 62 reference answers with rubrics, transcripts, split metadata | Not found, check before use | https://arxiv.org/pdf/2602.00095 |
| Reader bake-off: English handwriting | IAM Handwriting Database | 1,539 forms from 657 writers, with transcripts | Non-commercial research only, registration requested | https://fki.tic.heia-fr.ch/databases/iam-handwriting-database |
| Final check | Our own sheets | 30 to 50 sheets in Evalify's layout, phone photos, numerical edge cases | Ours | n/a |

## 2. What each dataset tests

- Tamaulipas and Afifi: OMR accuracy, per-bubble margins, multi-mark and blank handling, accuracy on auto-accepted rows, silent error rate.
- Mendeley student exam set: end-to-end pipeline on real handwritten sheets for MCQ correctness and short-answer marks against one teacher's marks.
- FERMAT: number and expression reading, and the rate at which a model changes a deliberately wrong answer into the correct one (over-correction).
- Handwritten ASAP: handwriting reading plus scoring on short answers.
- SciEntsBank and Mohler: grader quality with handwriting removed, to compare Qwen3.8-27B, gpt-oss and Qwen3.5-122B on gold text.
- EDU-CIRCUIT-HW: rubric-based grading and transcription errors on diagram-heavy STEM solutions (only if the licence allows evaluation).
- IAM: character and word error rate of each reader (Qwen3.8-27B, Chandra OCR 2, PaddleOCR-VL-1.6, GLM-OCR, Nanonets-OCR2-3B), with and without the "do not correct" prompt.
- Our own sheets: everything above under real conditions (our layout, phone photos, our rubric format).

## 3. How to use the Mendeley student exam set

1. Download with the page's "Download All" button in a browser, then copy to cluster scratch with scp or rsync. File sizes were not visible on the page.
2. Files: Question.txt, answerkey.txt, Student_Pdf (50 uncorrected sheets), Corrected_Pdf (50 teacher-marked sheets), Teacher_manual_marks_Anonymized.csv. The CSV column headers and the structure of answerkey.txt were not described, so open them first. Scan resolution is not reported.
3. Render each PDF page to PNG or JPG (Evalify accepts only png and jpg) at about 200 to 300 DPI, for example with PyMuPDF:

```
import fitz
d = fitz.open("Student_1.pdf")
for i, p in enumerate(d):
    p.get_pixmap(dpi=250).save(f"s1_p{i+1}.png")
```

4. Make phone-like copies by adding blur, skew, shadows and lighting changes, or photograph printouts.
5. Build the paper: Q1 to Q20 MCQ, Q21 to Q35 short answers, no numerical section (check that the paper wizard allows zero numerical questions). Convert answerkey.txt into Evalify's rubric format (key concepts, mandatory concepts, marks per concept), by hand or LLM-drafted then reviewed.
6. Run as a batch script, not through the UI. Log every run to MLflow with model versions and prompt hashes.
7. Freeze about 15 of the 50 sheets (30%) as a test split that is never used for prompt tuning.
8. Metrics: MCQ correct or incorrect against the teacher's 1 or 0 per question; short answers by exact match and MAE (questions are only 2 marks, so within-1-mark is too coarse); total score per student; TA routing rate; wrong-but-auto-accepted rate.

Limits of this set:
- The CSV has marks, not the letter each student chose or what they wrote, so character error rate needs about 10 hand-transcribed sheets.
- One evaluator, so no human-human agreement ceiling.
- One course, 50 sheets, scans rather than phone photos, no numerical questions.

## 4. Licence tracking

- Record the dataset name, version, licence and source URL in MLflow for every evaluation run.
- Keep restricted sets (IAM, Tamaulipas, Afifi, EDU-CIRCUIT-HW) out of training data and out of any shipped model.
- A Hugging Face mirror may show a different licence tag from the original source (for example, an IAM line-level mirror tagged MIT). The original terms still apply.
- When moving to our own dataset, remove restricted datasets from the evaluation set unless their terms clearly allow continued use.

## 5. Left out of the plan (and why)

- Small Roboflow bubble sets (72, 122, 134 images): too small, labelled for bubble detection not grading, mostly duplicate the OMR sets above.
- MathWriting (CC BY-NC-SA 4.0), HME100K, CROHME 2023, MLHME-38K: for training or testing equation recognition. Add only if math reading becomes the dominant error.
- ASAP-SAS (Kaggle): overlaps SciEntsBank and Mohler for the grader and is governed by Kaggle's rules.
- CVL Database (CC BY-NC 3.0): similar purpose to IAM.
- IEEE DataPort Student Handwritten Exam Dataset: 21 students, about 6K phone-scanned images, built for writer identification, no transcripts or marks.
- Covenant University, ClozeFormHandwriting, gated Hugging Face Handwriting_Homework_dataset, IEEE DataPort Answer sheet Dataset: limited fit or unknown content and terms.
- Datasets only described in papers with no confirmed public release: Indonesian grade 4 study (646 sheets), middle-school arithmetic set (288 responses), US probability exam (18 students).

## 6. Gaps

- No public dataset found that has all three paper types with phone photos, per-question marks and a rubric. Our own sheets fill this gap.
- Type 2 numerical grading has no public exam set with marks. FERMAT tests reading, not grading, so numerical edge cases (negatives, decimals, units, fractions, scientific notation) should be in our own sheets.
- OMR on phone photos with corner markers: none of the public sets match our template, so print and photograph our own sheets.
