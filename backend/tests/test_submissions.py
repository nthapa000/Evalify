# test_submissions.py — uploading answer sheets, viewing pages, and the student's re-evaluation request.

import pytest

from tests.conftest import auth_headers
from tests.helpers import add_evaluated_submission, make_paper

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32


@pytest.fixture(autouse=True)
def no_evaluation(monkeypatch, tmp_path):
    """Uploads go to a temp dir and the background evaluation is skipped (tested in test_evaluator.py)."""
    from app.routers import submissions
    from app.services import evaluator
    monkeypatch.setattr(submissions, "UPLOAD_DIR", str(tmp_path))

    async def skip(_sid):
        return None
    monkeypatch.setattr(evaluator, "evaluate_submission", skip)


# Why: a student uploads page photos and gets a submission that is being evaluated
@pytest.mark.asyncio
async def test_submit_pages(client, teacher_token, student_token):
    paper = await make_paper(client, teacher_token)
    resp = await client.post(f"/api/submissions?paper_id={paper['id']}&sheet_type=handwritten",
                             headers=auth_headers(student_token),
                             files=[("files", ("p1.png", PNG, "image/png")), ("files", ("p2.png", PNG, "image/png"))])
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "processing" and data["page_count"] == 2 and data["roll_no"] == "CS2025001"


# Why: PDFs and other files are refused (the pipeline reads photos of pages)
@pytest.mark.asyncio
async def test_submit_rejects_pdf(client, teacher_token, student_token):
    paper = await make_paper(client, teacher_token)
    resp = await client.post(f"/api/submissions?paper_id={paper['id']}&sheet_type=handwritten",
                             headers=auth_headers(student_token), files=[("files", ("a.pdf", b"%PDF", "application/pdf"))])
    assert resp.status_code == 400


# Why: a student may only submit to papers of subjects they are enrolled in
@pytest.mark.asyncio
async def test_submit_requires_enrolment(client, teacher_token, other_student_token):
    paper = await make_paper(client, teacher_token)                      # Computer Science
    resp = await client.post(f"/api/submissions?paper_id={paper['id']}&sheet_type=handwritten",
                             headers=auth_headers(other_student_token), files=[("files", ("p.png", PNG, "image/png"))])
    assert resp.status_code == 403


# Why: the TA view and the student both need every page of the answer sheet, not only the first
@pytest.mark.asyncio
async def test_pages_count_and_file(client, db, teacher_token, student_token, tmp_path):
    paper = await make_paper(client, teacher_token)
    pages = []
    for i in range(2):
        f = tmp_path / f"page{i}.png"
        f.write_bytes(PNG)
        pages.append(str(f))
    sid = await add_evaluated_submission(db, paper, pages=pages)
    info = await client.get(f"/api/submissions/{sid}/pages", headers=auth_headers(student_token))
    assert info.status_code == 200 and info.json()["count"] == 2
    page = await client.get(f"/api/submissions/{sid}/pages/1", headers=auth_headers(student_token))
    assert page.status_code == 200 and page.content.startswith(b"\x89PNG")
    missing = await client.get(f"/api/submissions/{sid}/pages/5", headers=auth_headers(student_token))
    assert missing.status_code == 404


# Why: answer sheets are private — another student, or a TA/teacher of another subject, must not see them
@pytest.mark.asyncio
async def test_pages_access_control(client, db, teacher_token, other_student_token, ta_token, physics_ta_token,
                                    physics_teacher_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper)
    for token, code in ((other_student_token, 403), (physics_ta_token, 403), (physics_teacher_token, 403),
                        (ta_token, 200), (teacher_token, 200)):
        resp = await client.get(f"/api/submissions/{sid}/pages", headers=auth_headers(token))
        assert resp.status_code == code, (token[:10], resp.text)


# Why: the student can ask for re-evaluation once per paper, with a remark the TA will read
@pytest.mark.asyncio
async def test_reevaluation_request_once(client, db, teacher_token, student_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper)
    url = f"/api/submissions/{sid}/reevaluation"
    first = await client.post(url, json={"remark": "Q4 was marked wrong: I gave an example (solar panels)."},
                              headers=auth_headers(student_token))
    assert first.status_code == 200 and first.json()["reevaluation"]["status"] == "pending"
    again = await client.post(url, json={"remark": "again"}, headers=auth_headers(student_token))
    assert again.status_code == 409


# Why: an empty remark gives the TA nothing to check, and only the owner may ask
@pytest.mark.asyncio
async def test_reevaluation_validation(client, db, teacher_token, student_token, other_student_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper)
    url = f"/api/submissions/{sid}/reevaluation"
    assert (await client.post(url, json={"remark": "  "}, headers=auth_headers(student_token))).status_code == 422
    assert (await client.post(url, json={"remark": "mine?"}, headers=auth_headers(other_student_token))).status_code == 403


# Why: re-evaluation makes sense only once the paper has been evaluated
@pytest.mark.asyncio
async def test_reevaluation_needs_evaluated(client, db, teacher_token, student_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper)
    from bson import ObjectId
    await db["submissions"].update_one({"_id": ObjectId(sid)}, {"$set": {"status": "processing"}})
    resp = await client.post(f"/api/submissions/{sid}/reevaluation", json={"remark": "x"},
                             headers=auth_headers(student_token))
    assert resp.status_code == 409


# Why: the upload page polls this until evaluation finishes
@pytest.mark.asyncio
async def test_status_poll(client, db, teacher_token, student_token):
    paper = await make_paper(client, teacher_token)
    sid = await add_evaluated_submission(db, paper)
    resp = await client.get(f"/api/submissions/{sid}/status", headers=auth_headers(student_token))
    assert resp.status_code == 200 and resp.json()["status"] == "evaluated"
