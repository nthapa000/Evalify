# test_auth.py — login for teachers, students and TAs, and role checks.

import pytest
from tests.conftest import auth_headers


# Why: teachers log in by email and the token must carry their role and subject
@pytest.mark.asyncio
async def test_teacher_login_success(client):
    resp = await client.post("/api/auth/teacher/login", json={"email": "teacher@evalify.local", "password": "Teacher@123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["role"] == "teacher"
    assert data["user"]["email"] == "teacher@evalify.local"
    assert data["user"]["subject"] == "Computer Science"


# Why: a wrong password must never log anyone in
@pytest.mark.asyncio
async def test_teacher_login_wrong_password(client):
    resp = await client.post("/api/auth/teacher/login", json={"email": "teacher@evalify.local", "password": "wrongpassword"})
    assert resp.status_code == 401


# Why: students log in by roll number and the UI needs their enrolled subjects
@pytest.mark.asyncio
async def test_student_login_success(client):
    resp = await client.post("/api/auth/student/login", json={"roll_no": "CS2025001", "password": "Student@123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["role"] == "student"
    assert data["user"]["subjects"] == ["Computer Science", "Physics"]


# Why: unknown roll numbers are rejected like wrong passwords
@pytest.mark.asyncio
async def test_student_login_wrong_roll(client):
    resp = await client.post("/api/auth/student/login", json={"roll_no": "NOPE999", "password": "Student@123"})
    assert resp.status_code == 401


# Why: TA is the new third role; it logs in by email and sees its subjects
@pytest.mark.asyncio
async def test_ta_login_success(client):
    resp = await client.post("/api/auth/ta/login", json={"email": "ta.cs@evalify.local", "password": "Ta@12345"})
    assert resp.status_code == 200
    user = resp.json()["user"]
    assert user["role"] == "ta" and user["subjects"] == ["Computer Science"]


# Why: a teacher account must not be usable on the TA login (roles are separate)
@pytest.mark.asyncio
async def test_ta_login_rejects_teacher_account(client):
    resp = await client.post("/api/auth/ta/login", json={"email": "teacher@evalify.local", "password": "Teacher@123"})
    assert resp.status_code == 401


# Why: a TA token must not unlock teacher-only actions such as creating papers
@pytest.mark.asyncio
async def test_ta_cannot_create_paper(client, ta_token):
    resp = await client.post("/api/papers", json={"name": "x"}, headers=auth_headers(ta_token))
    assert resp.status_code == 403


# Why: requests without a token or with a forged token must be refused
@pytest.mark.asyncio
async def test_missing_or_bad_token(client):
    assert (await client.get("/api/papers")).status_code in (401, 403)
    assert (await client.get("/api/papers", headers=auth_headers("not.a.token"))).status_code == 401
