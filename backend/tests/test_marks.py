# test_marks.py — changing marks after evaluation (TA / teacher): totals, history, locks. No database needed.

import pytest

from app.services import marks as M


def sub():
    """Minimal evaluated submission: Q1 1/1, Q2 0/1, N1 2/2, S1 1/2, S2 0.5/2 → 4.5 / 8."""
    return {
        "result": {"mcqScore": 1.0, "numericalScore": 2.0, "subjectiveScore": 1.5, "totalScore": 4.5,
                   "maxScore": 8.0, "percentage": 56.2},
        "mcqDetail": [{"question": "Q1", "marks_available": 1.0, "marks_earned": 1.0},
                      {"question": "Q2", "marks_available": 1.0, "marks_earned": 0.0}],
        "numericalDetail": [{"question": "N1", "marks_available": 2.0, "marks_earned": 2.0}],
        "subjectiveDetail": [{"question": "S1", "marks_available": 2.0, "marks_earned": 1.0, "rubric_marks": 1.0},
                             {"question": "S2", "marks_available": 2.0, "marks_earned": 0.5, "rubric_marks": 0.5}],
    }


BY = {"role": "ta", "id": "u1", "name": "Rahul Menon"}


# Why: section scores, total and percentage must follow the changed per-question marks
def test_recompute_totals():
    s = sub()
    s["subjectiveDetail"][0]["marks_earned"] = 2.0
    r = M.recompute(s)
    assert r["subjectiveScore"] == 2.5 and r["totalScore"] == 5.5 and r["percentage"] == 68.8


# Why: negative marking can push the MCQ sum below zero; the section never goes negative (as at grading)
def test_recompute_mcq_never_negative():
    s = sub()
    s["mcqDetail"][0]["marks_earned"] = -0.25
    s["mcqDetail"][1]["marks_earned"] = -0.25
    assert M.recompute(s)["mcqScore"] == 0.0


# Why: a TA change must update the row, lock it, log old → new with who/when, and fix the totals
def test_apply_marks_updates_row_history_and_totals():
    s = sub()
    upd, hist = M.apply_marks(s, {"Q2": 1, "S1": 1.0}, BY, remark="readers misread", source="flagged")
    q2 = next(r for r in upd["mcqDetail"] if r["question"] == "Q2")
    assert q2["marks_earned"] == 1.0 and q2["final_by"] == "ta"
    assert [h["question"] for h in hist] == ["Q2"]                 # S1 unchanged → no history entry
    assert hist[0]["old"] == 0.0 and hist[0]["new"] == 1.0 and hist[0]["by_name"] == "Rahul Menon"
    assert hist[0]["remark"] == "readers misread" and hist[0]["source"] == "flagged" and hist[0]["at"]
    assert upd["result"]["totalScore"] == 5.5


# Why: marks outside 0…max or for unknown questions are input mistakes and must be refused
@pytest.mark.parametrize("marks", [{"Q1": 2}, {"S1": -1}, {"Z9": 1}, {"S1": "two"}])
def test_apply_marks_rejects_bad_input(marks):
    with pytest.raises(ValueError):
        M.apply_marks(sub(), marks, BY)


# Why: questions a TA or teacher already decided are final and must not be overwritten by calibration
def test_locked_rows():
    s = sub()
    upd, _ = M.apply_marks(s, {"S1": 2}, BY)
    assert M.is_locked(next(r for r in upd["subjectiveDetail"] if r["question"] == "S1"))
    assert not M.is_locked(next(r for r in upd["subjectiveDetail"] if r["question"] == "S2"))
