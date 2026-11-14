# test_grading_logic.py — pure-logic tests (no MongoDB, no models needed).

import pytest

from app.pipeline import numeric
from app.services.evaluator import grade_mcq, grade_numerical
from app.services.ollama_engine import normalise_mcq, parse_answers
from app.services.subjective_grader import _result


# Numeric comparison: equivalent forms of the same value are correct
@pytest.mark.parametrize("student, key", [
    ("3", ["3.0"]), ("0.625", ["5/8"]), ("1 1/2", ["1.5"]), ("−2.5", ["-2.5"]),
    ("1.2×10⁻³", ["0.0012"]), ("1.2e-3", ["1.2*10^-3"]), ("1,234.5", ["1234.5"]),
    ("x = 3.5", ["3.5"]), ("\\frac{3}{4}", ["0.75"]), ("250 cm", {"answer": "2.5", "unit": "m"}),
])
def test_numeric_equivalent_forms(student, key):
    assert numeric.compare(student, key).status == "correct"


# Numeric comparison: tolerance, wrong values, units, blanks, garbage
def test_numeric_tolerance_and_failures():
    assert numeric.compare("9.79", {"answer": "9.8", "tolerance": 0.02}).status == "correct"
    assert numeric.compare("9.70", {"answer": "9.8", "tolerance": 0.02}).status == "wrong"
    assert numeric.compare("101", {"answer": "100", "tolerance": 0.01, "tolerance_type": "rel"}).status == "correct"
    assert numeric.compare("5 kg", {"answer": "5", "unit": "m"}).status == "wrong"
    assert numeric.compare("", ["3"]).status == "unanswered"
    assert numeric.compare("banana", ["3"]).status == "unparseable"


# Two readers agree when they wrote the same number differently
def test_numbers_agree():
    assert numeric.numbers_agree("0.5", "1/2") is True
    assert numeric.numbers_agree("0.5", "0.6") is False
    assert numeric.numbers_agree("??", "0.6") is None


# MCQ grading: exact set match, over/under-fill, negative marking
def test_grade_mcq():
    paper = {"mcqAnswers": {"Q1": "A", "Q2": "A,C", "Q3": "B"}, "mcqMarks": 4,
             "config": {"negativeMaking": True}}
    score, correct, detail = grade_mcq({"Q1": "A", "Q2": "A", "Q3": "C"}, paper, 3)
    assert [d["status"] for d in detail] == ["correct", "wrong_underfill", "wrong"]
    assert (score, correct) == (2.0, 1)          # 4 − 1 − 1


# Numerical grading uses numeric.compare (legacy list keys still work)
def test_grade_numerical():
    paper = {"numericalAnswers": {"N1": ["0.5"], "N2": ["10"]}, "numericalMarks": 5}
    score, detail = grade_numerical({"N1": "1/2", "N2": "11"}, paper, 2)
    assert score == 5 and [d["status"] for d in detail] == ["correct", "wrong"]


# Vision-model output parsing: sectioned JSON, sheet-label remap, regex fallback
def test_parse_answers():
    raw = '{"mcq":{"Q1":"c","Q2":"ca"},"numerical":{"Q3":"5/8, 0.625"},"subjective":{"S1":"plants"}}'
    assert parse_answers(raw, 2, 1, 1) == {"Q1": "C", "Q2": "A,C", "N1": "5/8", "S1": "plants"}
    assert parse_answers("Q1: B\n2) a,c", 2) == {"Q1": "B", "Q2": "A,C"}
    assert normalise_mcq("c, a") == "A,C"


# Subjective marks are recomputed in Python; missing mandatory concept → 0
def test_subjective_marks_in_python():
    rubric = {"key_concepts": ["chlorophyll", "sunlight", "glucose"],
              "mandatory_concepts": ["sunlight"], "marks_per_concept": 2}
    assert _result(rubric, ["chlorophyll", "sunlight"], "")["marks_awarded"] == 4
    assert _result(rubric, ["chlorophyll", "glucose"], "")["marks_awarded"] == 0
