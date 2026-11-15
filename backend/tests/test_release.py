# test_release.py — results are hidden from students until the teacher releases them.

import pytest
from bson import ObjectId

from tests.conftest import auth_headers
from tests.helpers import add_evaluated_submission, make_paper


async def set_release(client, token, paper_id, released=True):
    """Teacher releases (or withdraws) the results of a paper."""
    return await client.put(f"/api/papers/{paper_id}/release", json={"released": released}, headers=auth_headers(token))


# Why: a new paper's results start hidden, so TAs can finish the flagged answers before students see marks
@pytest.mark.asyncio
async def test_new_paper_is_unreleased(client, teacher_token):
    paper = await make_paper(client, teacher_token, release=False)
    assert paper["resultsReleased"] is False


# Why: before release the student only learns that the sheet is being evaluated — no marks anywhere
@pytest.mark.asyncio
async def test_student_sees_being_evaluated_before_release(client, db, teacher_token, student_token):
    paper = await make_paper(client, teacher_token, release=False)
    sid = await add_evaluated_submission(db, paper)
    st = (await client.get(f"/api/submissions/{sid}/status", headers=auth_headers(student_token))).json()
    assert st["status"] == "awaiting_release" and st["result"] is None
    res = await client.get(f"/api/results/{sid}", headers=auth_headers(student_token))
    assert res.status_code == 409 and "not been released" in res.json()["detail"]
    avail = (await client.get("/api/papers/available", headers=auth_headers(student_token))).json()
    assert avail[0]["submissionStatus"] == "awaiting_release"


# Why: after the teacher releases, the student sees the result (and can ask for re-evaluation)
@pytest.mark.asyncio
async def test_release_shows_results(client, db, teacher_token, student_token):
    paper = await make_paper(client, teacher_token, release=False)
    sid = await add_evaluated_submission(db, paper)
    resp = await set_release(client, teacher_token, paper["id"])
    assert resp.status_code == 200 and resp.json()["resultsReleased"] is True and resp.json()["releasedAt"]
    assert (await client.get(f"/api/results/{sid}", headers=auth_headers(student_token))).status_code == 200
    assert (await client.get(f"/api/submissions/{sid}/status", headers=auth_headers(student_token))).json()["status"] == "evaluated"


# Why: re-evaluation requests only make sense once the student has seen the marks
@pytest.mark.asyncio
async def test_no_reevaluation_before_release(client, db, teacher_token, student_token):
    paper = await make_paper(client, teacher_token, release=False)
    sid = await add_evaluated_submission(db, paper)
    resp = await client.post(f"/api/submissions/{sid}/reevaluation", json={"remark": "Q2"}, headers=auth_headers(student_token))
    assert resp.status_code == 409


# Why: the teacher and TAs work on results before release (review, flagged answers, calibration)
@pytest.mark.asyncio
async def test_teacher_and_ta_see_results_before_release(client, db, teacher_token, ta_token):
    paper = await make_paper(client, teacher_token, release=False)
    sid = await add_evaluated_submission(db, paper)
    assert (await client.get(f"/api/results/{sid}", headers=auth_headers(teacher_token))).status_code == 200
    assert (await client.get(f"/api/ta/items/{sid}", headers=auth_headers(ta_token))).status_code == 200
    assert (await client.get(f"/api/results/paper/{paper['id']}", headers=auth_headers(teacher_token))).status_code == 200


# Why: the teacher can withdraw a release (e.g. released by mistake)
@pytest.mark.asyncio
async def test_withdraw_release(client, db, teacher_token, student_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper)
    await set_release(client, teacher_token, paper["id"], released=False)
    assert (await client.get(f"/api/results/{sid}", headers=auth_headers(student_token))).status_code == 409


# Why: only the paper's own teacher may release it
@pytest.mark.asyncio
async def test_release_only_by_owner(client, teacher_token, physics_teacher_token, ta_token):
    paper = await make_paper(client, teacher_token, release=False)
    assert (await set_release(client, physics_teacher_token, paper["id"])).status_code == 404
    assert (await set_release(client, ta_token, paper["id"])).status_code == 403


# Why: papers created before this feature had results visible at once; they must keep working that way
@pytest.mark.asyncio
async def test_legacy_paper_counts_as_released(client, db, teacher_token, student_token):
    paper = await make_paper(client, teacher_token, release=False)
    await db["papers"].update_one({"_id": ObjectId(paper["id"])}, {"$unset": {"resultsReleased": ""}})
    sid = await add_evaluated_submission(db, paper)
    assert (await client.get(f"/api/results/{sid}", headers=auth_headers(student_token))).status_code == 200
