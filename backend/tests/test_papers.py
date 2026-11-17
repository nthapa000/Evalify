# test_papers.py — paper CRUD and which papers each role can see.

import pytest

from tests.conftest import auth_headers
from tests.helpers import make_paper


# Why: creating a paper is the teacher's first step; the subject is forced to the teacher's own subject
@pytest.mark.asyncio
async def test_create_paper(client, teacher_token):
    data = await make_paper(client, teacher_token, name="Test Paper 1", subject="Something else")
    assert data["name"] == "Test Paper 1" and "id" in data
    assert data["subject"] == "Computer Science" and data["resultCount"] == 0


# Why: the dashboard lists only the logged-in teacher's papers
@pytest.mark.asyncio
async def test_list_papers_only_own(client, teacher_token, physics_teacher_token):
    await make_paper(client, teacher_token, name="CS paper")
    await make_paper(client, physics_teacher_token, name="Physics paper")
    resp = await client.get("/api/papers", headers=auth_headers(teacher_token))
    assert resp.status_code == 200
    assert [p["name"] for p in resp.json()] == ["CS paper"]


# Why: opening one paper must return its stored details
@pytest.mark.asyncio
async def test_get_paper_detail(client, teacher_token):
    paper = await make_paper(client, teacher_token, name="Detail Test")
    resp = await client.get(f"/api/papers/{paper['id']}", headers=auth_headers(teacher_token))
    assert resp.status_code == 200 and resp.json()["name"] == "Detail Test"


# Why: malformed ids and unknown papers give clear errors instead of crashing
@pytest.mark.asyncio
async def test_get_paper_bad_and_missing_id(client, teacher_token):
    assert (await client.get("/api/papers/not-an-id", headers=auth_headers(teacher_token))).status_code == 400
    assert (await client.get("/api/papers/" + "0" * 24, headers=auth_headers(teacher_token))).status_code == 404


# Why: students must never be able to create papers
@pytest.mark.asyncio
async def test_student_cannot_create_paper(client, student_token):
    resp = await client.post("/api/papers", json={"name": "x"}, headers=auth_headers(student_token))
    assert resp.status_code == 403


# Why: a student sees papers of the subjects they are enrolled in, each with their submission status
@pytest.mark.asyncio
async def test_available_papers_only_enrolled_subjects(client, teacher_token, other_student_token):
    await make_paper(client, teacher_token, name="CS only")              # PH2025001 is not in Computer Science
    resp = await client.get("/api/papers/available", headers=auth_headers(other_student_token))
    assert resp.status_code == 200 and resp.json() == []


# Why: an enrolled student sees the paper and that they have not submitted yet
@pytest.mark.asyncio
async def test_available_papers_status(client, teacher_token, student_token):
    await make_paper(client, teacher_token, name="CS paper")
    papers = (await client.get("/api/papers/available", headers=auth_headers(student_token))).json()
    assert [p["name"] for p in papers] == ["CS paper"]
    assert papers[0]["submissionStatus"] == "not_submitted" and papers[0]["submissionId"] is None


# Why: only the owning teacher may delete a paper
@pytest.mark.asyncio
async def test_delete_paper_owner_only(client, teacher_token, physics_teacher_token):
    paper = await make_paper(client, teacher_token)
    other = await client.delete(f"/api/papers/{paper['id']}", headers=auth_headers(physics_teacher_token))
    assert other.status_code == 404
    own = await client.delete(f"/api/papers/{paper['id']}", headers=auth_headers(teacher_token))
    assert own.status_code == 200


# Why: uploads accept only PDF / JPEG / PNG / plain-text notes and are served back by name
@pytest.mark.asyncio
async def test_upload_and_serve_file(client, teacher_token, tmp_path, monkeypatch):
    from app.routers import papers
    monkeypatch.setattr(papers, "PAPER_UPLOAD_DIR", str(tmp_path))
    bad = await client.post("/api/papers/files/upload", headers=auth_headers(teacher_token),
                            files={"file": ("notes.docx", b"PK..", "application/octet-stream")})
    assert bad.status_code == 400
    txt = await client.post("/api/papers/files/upload", headers=auth_headers(teacher_token),
                            files={"file": ("notes.txt", b"Solar energy is energy from the sun.", "text/plain")})
    assert txt.status_code == 200                      # reference notes for the answer-key assistant
    ok = await client.post("/api/papers/files/upload", headers=auth_headers(teacher_token),
                           files={"file": ("key.pdf", b"%PDF-1.4 test", "application/pdf")})
    assert ok.status_code == 200
    served = await client.get(ok.json()["url"])
    assert served.status_code == 200 and served.content.startswith(b"%PDF")


# Why: the numbering the teacher picks ("continuous" = written answers labelled Q21.. after 20 MCQs) must be saved,
# because the pipeline matches transcribed answers to questions by those labels
@pytest.mark.asyncio
async def test_paper_keeps_written_answer_numbering(client, teacher_token):
    from app.pipeline.readers import questions_for
    from tests.helpers import make_paper
    paper = await make_paper(client, teacher_token, numbering="continuous")
    got = (await client.get(f"/api/papers/{paper['id']}", headers=auth_headers(teacher_token))).json()
    assert got["numbering"] == "continuous"
    assert [q.label for q in questions_for(got) if q.kind == "subjective"] == ["Q4", "Q5"]


# Why: a teacher with two subjects chooses which one a paper is for; the choice must be kept
@pytest.mark.asyncio
async def test_two_subject_teacher_picks_subject(client, science_teacher_token):
    maths = await make_paper(client, science_teacher_token, name="Maths test", subject="Mathematics")
    physics = await make_paper(client, science_teacher_token, name="Physics test", subject="Physics")
    assert maths["subject"] == "Mathematics" and physics["subject"] == "Physics"


# Why: a subject the teacher does not teach must never be accepted (falls back to their first subject)
@pytest.mark.asyncio
async def test_two_subject_teacher_cannot_use_other_subject(client, science_teacher_token):
    paper = await make_paper(client, science_teacher_token, subject="Computer Science")
    assert paper["subject"] == "Physics"


# Why: without a choice the paper takes the teacher's first subject (older clients send no subject)
@pytest.mark.asyncio
async def test_two_subject_teacher_default_subject(client, science_teacher_token):
    assert (await make_paper(client, science_teacher_token, subject=""))["subject"] == "Physics"


def _pdf_bytes(lines):
    """A small text PDF with one line per entry."""
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    for i, line in enumerate(lines):
        page.insert_text((40, 60 + 18 * i), line)
    return doc.tobytes()


# Why: user report (17 Nov) — a paper with two questions showed three; the count is now read from the uploaded PDF
@pytest.mark.asyncio
async def test_detect_questions_from_uploaded_pdf(client, teacher_token, monkeypatch, tmp_path):
    from app.routers import papers
    monkeypatch.setattr(papers, "PAPER_UPLOAD_DIR", str(tmp_path))          # keep test PDFs out of uploads/papers
    h = auth_headers(teacher_token)
    up = await client.post("/api/papers/files/upload", headers=h,
                           files={"file": ("q.pdf", _pdf_bytes(["1. First?", "A. x", "B. y", "2. Second?", "A. x"]), "application/pdf")})
    r = await client.post("/api/papers/detect-questions", headers=h, json={"file_url": up.json()["url"]})
    assert r.status_code == 200 and r.json() == {"count": 2}
    blank = await client.post("/api/papers/files/upload", headers=h,
                              files={"file": ("b.pdf", _pdf_bytes(["no numbers here"]), "application/pdf")})
    assert (await client.post("/api/papers/detect-questions", headers=h, json={"file_url": blank.json()["url"]})).json() == {"count": None}


# Why: user decision (17 Nov) — an OMR paper must come with its blank sheet and a confirmed bubble map (an ignored
# template once scored a whole sheet 0); the server refuses it from any client, other papers are not affected
@pytest.mark.asyncio
@pytest.mark.parametrize("tpl,ok", [(None, False), ({"bubbles": [{}], "confirmed": False}, False),
                                    ({"bubbles": [{}], "confirmed": True}, True)])
async def test_omr_paper_needs_a_confirmed_template(client, teacher_token, tpl, ok):
    resp = await client.post("/api/papers", headers=auth_headers(teacher_token), json={
        "name": "OMR quiz", "type": "mcq", "mcqCount": 1, "mcqAnswers": {"Q1": "A"}, "answerSheetFormat": "omr", "omrTemplate": tpl})
    assert (resp.status_code == 200) is ok, resp.text
    assert ok or "OMR" in resp.json()["detail"]


# Why: handwritten MCQ papers and the other paper types never need an OMR template
@pytest.mark.asyncio
async def test_handwritten_paper_needs_no_template(client, teacher_token):
    resp = await client.post("/api/papers", headers=auth_headers(teacher_token), json={
        "name": "Hand quiz", "type": "mcq", "mcqCount": 1, "mcqAnswers": {"Q1": "A"}, "answerSheetFormat": "handwritten"})
    assert resp.status_code == 200
