# test_results.py — result pages for students and teachers, incl. marks history after a TA change.

import pytest

from tests.conftest import auth_headers
from tests.helpers import add_evaluated_submission, make_paper


# Why: the student's result page needs totals, per-question rows, the paper and class stats
@pytest.mark.asyncio
async def test_student_result(client, db, teacher_token, student_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper)
    resp = await client.get(f"/api/results/{sid}", headers=auth_headers(student_token))
    assert resp.status_code == 200
    d = resp.json()
    assert d["result"]["totalScore"] == 4.5 and d["paper"]["name"] == paper["name"]
    assert [r["question"] for r in d["subjectiveDetail"]] == ["S1", "S2"]
    assert d["stats"] == {"average": 4.5, "highest": 4.5}
    assert d["marks_history"] == [] and d["reevaluation"] is None


# Why: results are private — another student must not read them (this was open before)
@pytest.mark.asyncio
async def test_result_private(client, db, teacher_token, other_student_token, physics_ta_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper)
    for token in (other_student_token, physics_ta_token):
        assert (await client.get(f"/api/results/{sid}", headers=auth_headers(token))).status_code == 403


# Why: after a TA re-evaluates, the student sees the new marks and the history of earlier marks
@pytest.mark.asyncio
async def test_result_shows_updated_marks_and_history(client, db, teacher_token, student_token, ta_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper)
    await client.post(f"/api/submissions/{sid}/reevaluation", json={"remark": "Q2 was A"}, headers=auth_headers(student_token))
    await client.post(f"/api/ta/items/{sid}/marks", headers=auth_headers(ta_token),
                      json={"tab": "reevaluation", "marks": {"Q2": 1}, "remark": "Yes, A."})
    d = (await client.get(f"/api/results/{sid}", headers=auth_headers(student_token))).json()
    assert d["result"]["totalScore"] == 5.5
    assert next(r for r in d["mcqDetail"] if r["question"] == "Q2")["marks_earned"] == 1.0
    assert [(h["question"], h["old"], h["new"], h["by_role"]) for h in d["marks_history"]] == [("Q2", 0.0, 1.0, "ta")]
    assert d["reevaluation"]["status"] == "resolved" and d["reevaluation"]["response"] == "Yes, A."


# Why: students must not see TA names or internal pipeline data — only role and marks
@pytest.mark.asyncio
async def test_student_result_hides_internal_fields(client, db, teacher_token, student_token, ta_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper)
    await client.post(f"/api/ta/items/{sid}/marks", headers=auth_headers(ta_token), json={"tab": "flagged", "marks": {"Q2": 1}})
    d = (await client.get(f"/api/results/{sid}", headers=auth_headers(student_token))).json()
    assert "by_name" not in d["marks_history"][0] and "by_id" not in d["marks_history"][0]
    assert "review" not in d and "pipeline" not in d and "ta_review" not in d


# Why: the teacher's results table lists every evaluated submission with stats and TA status
@pytest.mark.asyncio
async def test_paper_results_for_teacher(client, db, teacher_token, ta_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper)
    await add_evaluated_submission(db, paper, flagged=False)
    await client.post(f"/api/ta/items/{sid}/marks", headers=auth_headers(ta_token), json={"tab": "flagged", "marks": {}})
    d = (await client.get(f"/api/results/paper/{paper['id']}", headers=auth_headers(teacher_token))).json()
    assert d["stats"]["count"] == 2
    row = next(s for s in d["submissions"] if s["id"] == sid)
    assert row["ta_review"]["status"] == "done"


# Why: a teacher sees results of their own papers only
@pytest.mark.asyncio
async def test_paper_results_other_teacher(client, db, teacher_token, physics_teacher_token):
    paper = await make_paper(client, teacher_token)
    resp = await client.get(f"/api/results/paper/{paper['id']}", headers=auth_headers(physics_teacher_token))
    assert resp.status_code == 403
