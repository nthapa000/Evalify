# test_calibration.py — optional teacher calibration (per-question shift). Test-first; no GPU / MongoDB.

import pytest

from app.pipeline import calibration as cal


# Why: calibration must learn each question's teacher−grader difference and the overall one
def test_fit_global_and_per_question_shift():
    # teacher is 1 mark more generous on S1, 0 on S2
    pairs = [("S1", 0.0, 1.0), ("S1", 1.0, 2.0), ("S2", 1.0, 1.0), ("S2", 2.0, 2.0)]
    c = cal.fit(pairs, shrink=0.0)
    assert c["global"] == pytest.approx(0.5)
    assert c["per_question"]["S1"] == pytest.approx(1.0)
    assert c["per_question"]["S2"] == pytest.approx(0.0)
    assert c["n"] == 4


# Why: a question with one teacher example must not swing the shift on its own
def test_fit_shrinks_small_samples_towards_global():
    pairs = [("S1", 0.0, 2.0)] + [("S2", 1.0, 1.0)] * 9      # global = 0.2
    c = cal.fit(pairs, shrink=3.0)
    assert c["per_question"]["S1"] == pytest.approx((2.0 + 3 * 0.2) / 4)


# Why: calibrated marks must be real marks: half steps, never below 0 or above the maximum
def test_apply_rounds_to_half_and_clips():
    c = {"global": 0.63, "per_question": {"S1": 0.8}}
    assert cal.apply(c, "S1", 1.0, 2.0) == 2.0           # 1.8 → 2.0 (clipped)
    assert cal.apply(c, "S9", 0.5, 2.0) == 1.0           # unknown question → global shift; 1.13 → 1.0
    assert cal.apply(c, "S1", 0.0, 5.0) == 1.0           # 0.8 → 1.0
    assert cal.apply({"global": -3, "per_question": {}}, "S1", 1.0, 2.0) == 0.0


# Why: calibration is optional; without it the rubric mark is used unchanged
def test_apply_without_calibration_returns_mark():
    assert cal.apply(None, "S1", 1.5, 2.0) == 1.5
    assert cal.apply({}, "S1", 1.5, 2.0) == 1.5


# Why: fitting with no teacher-marked answers is a mistake and must say so
def test_fit_needs_data():
    with pytest.raises(ValueError):
        cal.fit([])
