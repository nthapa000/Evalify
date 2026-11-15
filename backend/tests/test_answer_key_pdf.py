# test_answer_key_pdf.py — reading the teacher's MCQ answer-key PDF text ("Extract Answers from PDF").

from app.services.pdf_utils import parse_mcq_text


# Why: single answers in the usual styles must still be read as before
def test_single_answers():
    assert parse_mcq_text("1. B\nQ2: c\n3) D", 3) == {"Q1": "B", "Q2": "C", "Q3": "D"}


# Why: a key with several correct options ("A, C") used to keep only "A", marking every right answer wrong
def test_multiple_correct_answers_are_kept():
    text = "1. B\n2. A, C\n3. A,C,D\n4) B & D\n5. b c"
    assert parse_mcq_text(text, 5) == {"Q1": "B", "Q2": "A,C", "Q3": "A,C,D", "Q4": "B,D", "Q5": "B,C"}


# Why: the next line's question number must never be swallowed into the previous answer
def test_answers_do_not_run_into_the_next_line():
    assert parse_mcq_text("1. A\nB is wrong\n2. C", 2) == {"Q1": "A", "Q2": "C"}


# Why: questions beyond the paper's MCQ count are ignored (e.g. subjective numbering after the MCQs)
def test_count_limit():
    assert parse_mcq_text("1. A\n2. B\n21. C", 2) == {"Q1": "A", "Q2": "B"}
