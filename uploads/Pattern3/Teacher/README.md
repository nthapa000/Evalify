# Pattern 3 (MCQ + subjective), teacher side

Log in as **ds.teacher@evalify.local** (password in `demo.env`). Subject: Data Science.
Data: "A Dataset of Digitized Student Examination Papers ..." (Mendeley Data sf3kvjwknt, CC BY 4.0).

| Wizard step | What to do |
|---|---|
| 1 Paper type | **MCQ + Numerical + Subjective** |
| 2 Details | Name e.g. `Data Science exam`; MCQ **20** x **1 mark**; Numerical **0**; Subjective **15** x **2 marks** (total 50); upload `question_paper.pdf`. Written-answer numbering: choose **Q21, Q22, ... (numbers continue)**, because the students wrote 21-35 |
| 3 Answer key | "Upload PDF and extract" with `answer_key_mcq.pdf` (20/20), or type from the table below |
| 4 Rubric | Upload `detailed_answer.pdf` (Detailed Answer) and `grade_rubric.pdf` (Grade Rubric), click **Extract Rubric from PDFs**: 15 questions, 2 points each at 1 mark |
| 4 (optional) | Answer-key assistant (written answers only): paste the questions from `reference_material/questions_for_assistant.txt`, upload the files of `reference_material/` as reference, **Draft answer key**. `reference_notes.txt` (the answers themselves) is the easy case |
| 5 Review | Check "Written answers numbered: Q21 onwards"; Create |

After the students upload: TAs (`ta.ds1@evalify.local`) clear flagged answers, then on the results page
click **Release results**. Until then the students see "Your answer sheet is being evaluated".

MCQ key:
| Q1 | Q2 | Q3 | Q4 | Q5 | Q6 | Q7 | Q8 | Q9 | Q10 |
|---|---|---|---|---|---|---|---|---|---|
| B | C | A | C | B | A | A | C | A | B |

| Q11 | Q12 | Q13 | Q14 | Q15 | Q16 | Q17 | Q18 | Q19 | Q20 |
|---|---|---|---|---|---|---|---|---|---|
| B | C | B | C | B | C | B | C | B | B |
