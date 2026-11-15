# Pattern 1 (MCQ only), teacher side

Log in as **physics.teacher@evalify.local** (password in `demo.env`). Subject: Physics.
Create **one paper per folder below**. For OMR, create one paper per layout you want to test
(the blank sheet of that layout is what the students' sheets are aligned to).

## A. OMR paper: `OMR/`

| Wizard step | What to do |
|---|---|
| 1 Paper type | **MCQ only** |
| 2 Details | Name e.g. `Basic Science OMR - layout 1`; MCQ questions **20**, **1 mark** each; upload `question_paper.pdf` |
| 3 Answer key | Either "Upload PDF and extract": upload `answer_key.pdf`, click **Extract Answers from PDF** (expect 20/20, including multi-answer keys like `A, C`), or enter them by hand from the table below |
| 3 Blank OMR sheet | Upload `blank_omr_sheet_layout1.png` (or 2 / 3). Check the labelled preview, then tick **Every bubble is labelled with the right question** |
| 4 Configuration | Negative marking off |
| 5 Review | Create |

Then the students in `../Student/OMR/Layout1/` (same layout number) upload their sheets and choose **OMR sheet**.

Key (20 questions; several have more than one correct option, a student must fill exactly that set):
| Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q7 | Q8 | Q9 | Q10 |
|---|---|---|---|---|---|---|---|---|---|
| B | C | C | B | A, C | C | A | B | B, D | C |

| Q11 | Q12 | Q13 | Q14 | Q15 | Q16 | Q17 | Q18 | Q19 | Q20 |
|---|---|---|---|---|---|---|---|---|---|
| C | B | A, B, D | B, D | A | D | A, B, D | C | B | A, C |

## B. Handwritten MCQ paper: `Handwritten/`

| Wizard step | What to do |
|---|---|
| 1 Paper type | **MCQ only** |
| 2 Details | Name e.g. `Basic Science MCQ (handwritten)`; MCQ questions **10**, **1 mark** each; upload `question_paper.pdf` |
| 3 Answer key | Upload `answer_key.pdf` and extract, or type from the table; do **not** upload a blank OMR sheet |
| 4, 5 | Negative marking off; Create |

Students in `../Student/Handwritten/` upload their photo and choose **Handwritten**.

Key:
| Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q7 | Q8 | Q9 | Q10 |
|---|---|---|---|---|---|---|---|---|---|
| B | A, C | B | A, C, D | C | A, C | D | A, C, D | B | A, C |
