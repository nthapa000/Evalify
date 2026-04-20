# test_auth.py — Tests for authentication endpoints.

import pytest
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_teacher_login_success(client):
    """Valid teacher credentials should return a token."""
    resp = await client.post("/api/auth/teacher/login", json={
        "email": "teacher@evalify.local",
        "password": "Teacher@123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["role"] == "teacher"
    assert data["user"]["email"] == "teacher@evalify.local"


@pytest.mark.asyncio
async def test_teacher_login_wrong_password(client):
    """Wrong password should return 401."""
    resp = await client.post("/api/auth/teacher/login", json={
        "email": "teacher@evalify.local",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_student_login_success(client):
    """Valid student credentials should return a token."""
    resp = await client.post("/api/auth/student/login", json={
        "roll_no": "CS2025001",
        "password": "Student@123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["role"] == "student"
    assert data["user"]["roll_no"] == "CS2025001"


@pytest.mark.asyncio
async def test_student_login_wrong_roll(client):
    """Non-existent roll number should return 401."""
    resp = await client.post("/api/auth/student/login", json={
        "roll_no": "INVALID999",
        "password": "Student@123",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_without_token(client):
    """Accessing papers without auth should return 403."""
    resp = await client.get("/api/papers")
    assert resp.status_code == 403
