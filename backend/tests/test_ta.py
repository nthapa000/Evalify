# test_ta.py — the TA view: subjects, "Flagged by AI" and "Re-evaluation requests" tabs, final marks.

import pytest

from tests.conftest import auth_headers
from tests.helpers import add_evaluated_submission, make_paper


async def request_reeval(client, sid, token, remark="Q2: I wrote A, not C."):
    """Student files the one re-evaluation request for a submission."""
    resp = await client.post(f"/api/submissions/{sid}/reevaluation", json={"remark": remark}, headers=auth_headers(token))
    assert resp.status_code == 200, resp.text


# Why: a TA sees only the subjects they are TA of, with how much work waits in each tab
@pytest.mark.asyncio
async def test_subjects_with_counts(client, db, teacher_token, ta_token, student_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper)                     # flagged
    await add_evaluated_submission(db, paper, roll_no="CS2025001", flagged=False)
    await request_reeval(client, sid, student_token)
    resp = await client.get("/api/ta/subjects", headers=auth_headers(ta_token))
    assert resp.status_code == 200
    assert resp.json() == [{"subject": "Computer Science", "flagged": 1, "reevaluation": 1}]


# Why: only TAs may use the TA endpoints
@pytest.mark.asyncio
async def test_ta_endpoints_need_ta_role(client, teacher_token, student_token):
    for token in (teacher_token, student_token):
        assert (await client.get("/api/ta/subjects", headers=auth_headers(token))).status_code == 403


# Why: the "Flagged by AI" tab lists submissions with questions the pipeline was unsure of, with one reason each
@pytest.mark.asyncio
async def test_flagged_queue(client, db, teacher_token, ta_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper)
    await add_evaluated_submission(db, paper, flagged=False)
    resp = await client.get("/api/ta/queue", params={"subject": "Computer Science", "tab": "flagged"},
                            headers=auth_headers(ta_token))
    assert resp.status_code == 200
    items = resp.json()
    assert [i["submission_id"] for i in items] == [sid]
    assert items[0]["questions"] == [{"question": "Q2", "reason": "readers disagree (A: A, B: C, C: D)"}]
    assert items[0]["roll_no"] == "CS2025001" and items[0]["paper_name"] == paper["name"]


# Why: the "Re-evaluation requests" tab lists pending requests with the student's remark
@pytest.mark.asyncio
async def test_reevaluation_queue(client, db, teacher_token, ta_token, student_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper, flagged=False)
    await request_reeval(client, sid, student_token, remark="S1: I gave solar panels as the example.")
    items = (await client.get("/api/ta/queue", params={"subject": "Computer Science", "tab": "reevaluation"},
                              headers=auth_headers(ta_token))).json()
    assert len(items) == 1 and items[0]["remark"] == "S1: I gave solar panels as the example."


# Why: a TA must not see another subject's queue
@pytest.mark.asyncio
async def test_queue_other_subject_forbidden(client, ta_token):
    resp = await client.get("/api/ta/queue", params={"subject": "Physics", "tab": "flagged"}, headers=auth_headers(ta_token))
    assert resp.status_code == 403


# Why: the TA item screen needs the question paper, answer key, rubric, every question's AI mark + reason
@pytest.mark.asyncio
async def test_item_detail(client, db, teacher_token, ta_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper)
    resp = await client.get(f"/api/ta/items/{sid}", headers=auth_headers(ta_token))
    assert resp.status_code == 200
    d = resp.json()
    assert d["paper"]["questionPaperUrl"] == "/api/papers/files/qp.pdf"
    assert d["paper"]["mcqAnswers"] == {"Q1": "B", "Q2": "A"}
    assert d["paper"]["subjectiveRubrics"][0]["key_concepts"][0] == "energy derived from the sun"
    q2 = next(q for q in d["questions"] if q["question"] == "Q2")
    assert q2["kind"] == "mcq" and q2["marks_earned"] == 0 and q2["review_reason"].startswith("readers disagree")
    assert d["submission"]["roll_no"] == "CS2025001" and "page_count" in d["submission"]


# Why: TAs of another subject must not open this answer sheet
@pytest.mark.asyncio
async def test_item_detail_other_subject_forbidden(client, db, teacher_token, physics_ta_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper)
    assert (await client.get(f"/api/ta/items/{sid}", headers=auth_headers(physics_ta_token))).status_code == 403


# Why: the TA's marks are final — they change the score, are logged, and the item leaves the Flagged tab
@pytest.mark.asyncio
async def test_submit_flagged_marks(client, db, teacher_token, ta_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper)
    resp = await client.post(f"/api/ta/items/{sid}/marks", headers=auth_headers(ta_token),
                             json={"tab": "flagged", "marks": {"Q2": 1}, "remark": "Student wrote A."})
    assert resp.status_code == 200, resp.text
    assert resp.json()["result"]["totalScore"] == 5.5
    sub = await db["submissions"].find_one({})
    assert sub["ta_review"]["status"] == "done" and sub["ta_review"]["by_name"] == "Rahul Menon"
    assert sub["marks_history"][0] | {"at": None} == {"question": "Q2", "old": 0.0, "new": 1.0, "by_role": "ta",
                                                      "by_id": sub["marks_history"][0]["by_id"], "by_name": "Rahul Menon",
                                                      "remark": "Student wrote A.", "source": "flagged", "at": None}
    assert await db["ta_log"].count_documents({}) == 1
    left = (await client.get("/api/ta/queue", params={"subject": "Computer Science", "tab": "flagged"},
                             headers=auth_headers(ta_token))).json()
    assert left == []


# Why: answering a re-evaluation request resolves it (marks may stay the same) and keeps the TA's remark
@pytest.mark.asyncio
async def test_submit_reevaluation_marks(client, db, teacher_token, ta_token, student_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper, flagged=False)
    await request_reeval(client, sid, student_token)
    resp = await client.post(f"/api/ta/items/{sid}/marks", headers=auth_headers(ta_token),
                             json={"tab": "reevaluation", "marks": {}, "remark": "Checked: C is what you wrote."})
    assert resp.status_code == 200
    sub = await db["submissions"].find_one({})
    assert sub["reevaluation"]["status"] == "resolved"
    assert sub["reevaluation"]["response"] == "Checked: C is what you wrote."
    assert sub.get("marks_history", []) == []


# Why: marks above the question's maximum are refused with a clear message
@pytest.mark.asyncio
async def test_submit_marks_validation(client, db, teacher_token, ta_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper)
    resp = await client.post(f"/api/ta/items/{sid}/marks", headers=auth_headers(ta_token),
                             json={"tab": "flagged", "marks": {"S1": 3}})
    assert resp.status_code == 422 and "S1" in resp.text


# Why: the re-evaluation tab can only be answered when the student actually asked
@pytest.mark.asyncio
async def test_submit_reevaluation_without_request(client, db, teacher_token, ta_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper)
    resp = await client.post(f"/api/ta/items/{sid}/marks", headers=auth_headers(ta_token),
                             json={"tab": "reevaluation", "marks": {"Q2": 1}})
    assert resp.status_code == 409
