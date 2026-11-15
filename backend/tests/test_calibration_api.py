# test_calibration_api.py — optional teacher calibration: hand-marked sheets → per-question shift for the paper.

import pytest
from bson import ObjectId

from tests.conftest import auth_headers
from tests.helpers import add_evaluated_submission, make_paper


async def hand_mark(client, token, paper_id, sid, marks):
    """Teacher enters their own marks for a submission's subjective questions."""
    return await client.put(f"/api/papers/{paper_id}/calibration/marks/{sid}", json={"marks": marks},
                            headers=auth_headers(token))


# Why: the teacher's own marks on a sheet are final for that sheet and are kept for calibration
@pytest.mark.asyncio
async def test_hand_marking_is_final_for_that_sheet(client, db, teacher_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper, flagged=False)
    resp = await hand_mark(client, teacher_token, paper["id"], sid, {"S1": 2, "S2": 1.5})
    assert resp.status_code == 200, resp.text
    sub = await db["submissions"].find_one({"_id": ObjectId(sid)})
    assert sub["teacher_marks"] == {"S1": 2.0, "S2": 1.5}
    assert sub["result"]["subjectiveScore"] == 3.5
    assert {h["by_role"] for h in sub["marks_history"]} == {"teacher"}


# Why: applying calibration learns this teacher's leniency and shifts the other students' subjective marks,
# keeping the rubric mark next to the calibrated one
@pytest.mark.asyncio
async def test_apply_calibration_shifts_other_sheets(client, db, teacher_token):
    paper = await make_paper(client, teacher_token)
    hand = await add_evaluated_submission(db, paper, flagged=False)
    other = await add_evaluated_submission(db, paper, flagged=False)
    await hand_mark(client, teacher_token, paper["id"], hand, {"S1": 2, "S2": 1.5})     # +1 on both
    resp = await client.post(f"/api/papers/{paper['id']}/calibration/apply", headers=auth_headers(teacher_token))
    assert resp.status_code == 200, resp.text
    summary = resp.json()
    assert summary["answers"] == 2 and summary["sheets"] == 1 and summary["updated_submissions"] == 1
    sub = await db["submissions"].find_one({"_id": ObjectId(other)})
    s1 = next(r for r in sub["subjectiveDetail"] if r["question"] == "S1")
    assert s1["rubric_marks"] == 1.0 and s1["calibrated_marks"] == 2.0 and s1["marks_earned"] == 2.0
    assert (await db["papers"].find_one({"_id": ObjectId(paper["id"])}))["calibration"]["n"] == 2


# Why: TA decisions are final — calibration must not overwrite a question a TA already marked
@pytest.mark.asyncio
async def test_calibration_keeps_ta_marks(client, db, teacher_token, ta_token):
    paper = await make_paper(client, teacher_token)
    hand = await add_evaluated_submission(db, paper, flagged=False)
    other = await add_evaluated_submission(db, paper)
    await client.post(f"/api/ta/items/{other}/marks", headers=auth_headers(ta_token), json={"tab": "flagged", "marks": {"S1": 0}})
    await hand_mark(client, teacher_token, paper["id"], hand, {"S1": 2, "S2": 1.5})
    await client.post(f"/api/papers/{paper['id']}/calibration/apply", headers=auth_headers(teacher_token))
    sub = await db["submissions"].find_one({"_id": ObjectId(other)})
    s1 = next(r for r in sub["subjectiveDetail"] if r["question"] == "S1")
    assert s1["marks_earned"] == 0.0                                       # TA's mark stays


# Why: calibration is optional — the teacher can remove it and the rubric marks come back
@pytest.mark.asyncio
async def test_remove_calibration(client, db, teacher_token):
    paper = await make_paper(client, teacher_token)
    hand = await add_evaluated_submission(db, paper, flagged=False)
    other = await add_evaluated_submission(db, paper, flagged=False)
    await hand_mark(client, teacher_token, paper["id"], hand, {"S1": 2, "S2": 1.5})
    await client.post(f"/api/papers/{paper['id']}/calibration/apply", headers=auth_headers(teacher_token))
    resp = await client.delete(f"/api/papers/{paper['id']}/calibration", headers=auth_headers(teacher_token))
    assert resp.status_code == 200
    sub = await db["submissions"].find_one({"_id": ObjectId(other)})
    s1 = next(r for r in sub["subjectiveDetail"] if r["question"] == "S1")
    assert s1["marks_earned"] == 1.0 and s1["calibrated_marks"] is None
    assert "calibration" not in await db["papers"].find_one({"_id": ObjectId(paper["id"])})


# Why: calibration needs at least one hand-marked sheet, and only the paper's teacher may use it
@pytest.mark.asyncio
async def test_calibration_guards(client, db, teacher_token, physics_teacher_token, ta_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper, flagged=False)
    assert (await client.post(f"/api/papers/{paper['id']}/calibration/apply",
                              headers=auth_headers(teacher_token))).status_code == 409
    assert (await hand_mark(client, physics_teacher_token, paper["id"], sid, {"S1": 2})).status_code == 404
    assert (await hand_mark(client, ta_token, paper["id"], sid, {"S1": 2})).status_code == 403
    assert (await hand_mark(client, teacher_token, paper["id"], sid, {"Q1": 1})).status_code == 422   # subjective only
