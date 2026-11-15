# test_evaluator.py — the background evaluation of one submission (pipeline faked; database in memory).

import pytest
from bson import ObjectId

from app.services import evaluator
from tests.helpers import make_paper

FAKE_OUT = {
    "answers": {"Q1": "B"}, "mcq_score": 1.0, "n_correct": 1, "numerical_score": 2.0, "subjective_score": 1.5,
    "mcq_detail": [{"question": "Q1", "marks_earned": 1.0, "needs_review": False, "review_reason": ""}],
    "numerical_detail": [{"question": "N1", "marks_earned": 2.0, "needs_review": False, "review_reason": ""}],
    "subjective_detail": [{"question": "S1", "marks_earned": 1.5, "needs_review": True,
                           "review_reason": "grader flagged a transcription problem"}],
    "review": [{"question": "S1", "reason": "grader flagged a transcription problem"}],
    "quality": [], "models": {"grader": "gemma"}, "prompt_version": "p6", "latency_s": 3.0,
}


async def _submission(db, paper_id):
    """A freshly uploaded (still processing) submission."""
    sid = ObjectId()
    await db["submissions"].insert_one({"_id": sid, "paper_id": paper_id, "roll_no": "CS2025001",
                                        "file_paths": ["p0.png"], "sheet_type": "handwritten", "status": "processing"})
    return sid


@pytest.fixture(autouse=True)
def no_mlflow(monkeypatch):
    """MLflow logging is best-effort and not part of these tests."""
    monkeypatch.setattr(evaluator, "_log_mlflow", lambda *a, **k: None)


# Why: after evaluation the submission must hold scores, per-question rows and the TA flags from the pipeline
@pytest.mark.asyncio
async def test_evaluation_saves_result_and_flags(client, db, teacher_token, monkeypatch):
    paper = await make_paper(client, teacher_token)
    monkeypatch.setattr(evaluator, "_use_pipeline", lambda sheet_type: True)
    monkeypatch.setattr(evaluator.orchestrator, "run", lambda paper, files, sheet_type: FAKE_OUT)
    sid = await _submission(db, paper["id"])
    await evaluator.evaluate_submission(str(sid))
    sub = await db["submissions"].find_one({"_id": sid})
    assert sub["status"] == "evaluated"
    assert sub["result"]["totalScore"] == 4.5 and sub["result"]["maxScore"] == 8.0
    assert sub["result"]["needsReview"] is True and sub["result"]["reviewCount"] == 1
    assert sub["review"][0]["reason"] == "grader flagged a transcription problem"
    assert sub["pipeline"]["prompt_version"] == "p6"


# Why: a pipeline crash must leave the submission in "error" with the message, not stuck in "processing"
@pytest.mark.asyncio
async def test_evaluation_error_is_recorded(client, db, teacher_token, monkeypatch):
    paper = await make_paper(client, teacher_token)
    monkeypatch.setattr(evaluator, "_use_pipeline", lambda sheet_type: True)

    def boom(*_a):
        raise RuntimeError("no reader model is reachable")
    monkeypatch.setattr(evaluator.orchestrator, "run", boom)
    sid = await _submission(db, paper["id"])
    await evaluator.evaluate_submission(str(sid))
    sub = await db["submissions"].find_one({"_id": sid})
    assert sub["status"] == "error" and "no reader model" in sub["error"]


# Why: a submission whose paper was deleted fails cleanly
@pytest.mark.asyncio
async def test_evaluation_missing_paper(db):
    sid = await _submission(db, str(ObjectId()))
    await evaluator.evaluate_submission(str(sid))
    assert (await db["submissions"].find_one({"_id": sid}))["status"] == "error"


# Why: EVALIFY_PIPELINE switches between the v2 pipeline and the legacy path; OMR never needs a model
@pytest.mark.parametrize("mode,sheet,live,expected", [
    ("legacy", "omr", True, False), ("v2", "handwritten", False, True),
    ("auto", "omr", False, True), ("auto", "handwritten", False, False), ("auto", "handwritten", True, True)])
def test_use_pipeline_modes(monkeypatch, mode, sheet, live, expected):
    monkeypatch.setenv("EVALIFY_PIPELINE", mode)
    monkeypatch.setattr(evaluator.llm, "any_live", lambda: live)
    assert evaluator._use_pipeline(sheet) is expected


# Why: grader confidence does not predict wrong written-answer marks (measured on 437 Mendeley answers), so quality is
# controlled by a random 5 % spot-check of auto-accepted written answers, shown to TAs as "random quality check"
@pytest.mark.asyncio
async def test_random_spot_check(client, db, teacher_token, monkeypatch):
    paper = await make_paper(client, teacher_token)
    rows = [{"question": f"S{i}", "marks_earned": 1.0, "needs_review": False, "review_reason": ""} for i in range(1, 201)]
    out = {**FAKE_OUT, "subjective_detail": rows, "review": []}
    monkeypatch.setattr(evaluator, "_use_pipeline", lambda sheet_type: True)
    monkeypatch.setattr(evaluator.orchestrator, "run", lambda paper, files, sheet_type: {**out, "subjective_detail": [dict(r) for r in rows]})
    monkeypatch.setattr(evaluator.settings, "EVALIFY_SPOT_CHECK_RATE", 0.05)
    sid = await _submission(db, paper["id"])
    await evaluator.evaluate_submission(str(sid))
    sub = await db["submissions"].find_one({"_id": sid})
    picked = [r for r in sub["subjectiveDetail"] if r["needs_review"]]
    assert 3 <= len(picked) <= 20 and all(r["review_reason"] == "random quality check" for r in picked)
    assert {r["question"] for r in sub["review"]} == {r["question"] for r in picked}
    # same submission → same picks (reproducible)
    assert evaluator.spot_check_pick(str(sid), "S7", 0.05) == evaluator.spot_check_pick(str(sid), "S7", 0.05)


# Why: the spot-check can be switched off (rate 0) and never touches answers already flagged for another reason
def test_spot_check_off_and_flagged_untouched():
    rows = [{"question": "S1", "needs_review": True, "review_reason": "grader failed"},
            {"question": "S2", "needs_review": False, "review_reason": ""}]
    review = evaluator.add_spot_checks("sub1", [dict(r) for r in rows], [], rate=0.0)
    assert review == []
    review = evaluator.add_spot_checks("sub1", flagged := [dict(r) for r in rows], [], rate=1.0)
    assert flagged[0]["review_reason"] == "grader failed" and flagged[1]["review_reason"] == "random quality check"
    assert [r["question"] for r in review] == ["S2"]
