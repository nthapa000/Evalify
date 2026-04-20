# test_papers.py — Tests for paper CRUD endpoints.

import pytest
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_create_paper(client, teacher_token):
    """Teacher should be able to create a paper."""
    resp = await client.post(
        "/api/papers",
        headers=auth_headers(teacher_token),
        json={
            "name": "Test Paper 1",
            "subject": "Testing",
            "type": "mcq",
            "typeLabel": "MCQ Only",
            "totalMarks": 20,
            "mcqCount": 10,
            "mcqMarks": 2,
            "mcqAnswers": {"Q1": "A", "Q2": "B"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Test Paper 1"
    assert "id" in data
    assert data["resultCount"] == 0


@pytest.mark.asyncio
async def test_list_papers(client, teacher_token):
    """Teacher should see at least the paper we just created."""
    resp = await client.get(
        "/api/papers",
        headers=auth_headers(teacher_token),
    )
    assert resp.status_code == 200
    papers = resp.json()
    assert len(papers) >= 1
    assert any(p["name"] == "Test Paper 1" for p in papers)


@pytest.mark.asyncio
async def test_get_paper_detail(client, teacher_token):
    """Fetching a specific paper by ID should return its details."""
    # First create a paper
    create_resp = await client.post(
        "/api/papers",
        headers=auth_headers(teacher_token),
        json={
            "name": "Detail Test",
            "subject": "Math",
            "type": "mcq",
            "typeLabel": "MCQ Only",
            "totalMarks": 10,
            "mcqCount": 5,
            "mcqMarks": 2,
        },
    )
    paper_id = create_resp.json()["id"]

    # Fetch it
    resp = await client.get(
        f"/api/papers/{paper_id}",
        headers=auth_headers(teacher_token),
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Detail Test"


@pytest.mark.asyncio
async def test_student_cannot_create_paper(client, student_token):
    """Students should not be allowed to create papers (403)."""
    resp = await client.post(
        "/api/papers",
        headers=auth_headers(student_token),
        json={
            "name": "Student Paper",
            "subject": "Hack",
            "type": "mcq",
            "typeLabel": "MCQ Only",
            "totalMarks": 10,
            "mcqCount": 5,
            "mcqMarks": 2,
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_available_papers(client, student_token):
    """Student should see available papers with submission status."""
    resp = await client.get(
        "/api/papers/available",
        headers=auth_headers(student_token),
    )
    assert resp.status_code == 200
    papers = resp.json()
    assert isinstance(papers, list)
    # Each paper should have submissionStatus field
    for p in papers:
        assert "submissionStatus" in p
