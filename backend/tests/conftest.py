# conftest.py — Shared pytest fixtures for backend tests.
# Sets up a test FastAPI client that talks to the real MongoDB.

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.mongodb import connect_db, close_db


# Use function-scoped fixtures (compatible with pytest-asyncio 0.23.x)

@pytest_asyncio.fixture
async def client():
    """
    Async HTTP client pointing at the FastAPI app.
    Connects to MongoDB, seeds users, yields the client, then disconnects.
    """
    await connect_db()
    from app.db.seed import seed_users
    await seed_users()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    await close_db()


@pytest_asyncio.fixture
async def teacher_token(client: AsyncClient):
    """Login as the seed teacher and return the JWT token."""
    resp = await client.post("/api/auth/teacher/login", json={
        "email": "teacher@evalify.local",
        "password": "Teacher@123",
    })
    assert resp.status_code == 200, f"Teacher login failed: {resp.text}"
    return resp.json()["token"]


@pytest_asyncio.fixture
async def student_token(client: AsyncClient):
    """Login as the seed student and return the JWT token."""
    resp = await client.post("/api/auth/student/login", json={
        "roll_no": "CS2025001",
        "password": "Student@123",
    })
    assert resp.status_code == 200, f"Student login failed: {resp.text}"
    return resp.json()["token"]


def auth_headers(token: str) -> dict:
    """Build Authorization header from a JWT token."""
    return {"Authorization": f"Bearer {token}"}
