# conftest.py — Shared pytest fixtures for backend tests.
# By default the API talks to an in-memory MongoDB (mongomock-motor), so tests run anywhere (laptop, cluster,
# CI) without a database server. Set EVALIFY_TEST_REAL_MONGO=1 to use the real MongoDB from MONGO_URI instead.

import os
from pathlib import Path

# Test settings must be in place before the app modules read them
os.environ.setdefault("EVALIFY_DEMO_ENV", str(Path(__file__).parent / "fixtures" / "demo_test.env"))
os.environ.setdefault("BCRYPT_ROUNDS", "4")          # fast password hashing in tests
# Real-MongoDB mode empties the database before each test: never point it at the development database
if os.environ.get("EVALIFY_TEST_REAL_MONGO") == "1":
    os.environ["MONGO_DB_NAME"] = "evalify_test"

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.db import mongodb
from app.main import app

REAL_MONGO = os.environ.get("EVALIFY_TEST_REAL_MONGO") == "1"


@pytest_asyncio.fixture
async def db():
    """A fresh database per test: in-memory by default, the real one when EVALIFY_TEST_REAL_MONGO=1."""
    if REAL_MONGO:
        await mongodb.connect_db()
        # Every test starts from an empty database, as with the in-memory one
        for name in await mongodb.get_db().list_collection_names():
            await mongodb.get_db()[name].delete_many({})
        yield mongodb.get_db()
        await mongodb.close_db()
        return
    from mongomock_motor import AsyncMongoMockClient
    mongodb._client = AsyncMongoMockClient()
    mongodb._db = mongodb._client["evalify_test"]
    yield mongodb._db
    mongodb._client, mongodb._db = None, None


@pytest_asyncio.fixture
async def client(db):
    """Async HTTP client for the FastAPI app with the demo users seeded."""
    from app.db.seed import seed_users
    await seed_users()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _login(client, path, body):
    """Log in and return the JWT (fails the test with the server's reply otherwise)."""
    resp = await client.post(path, json=body)
    assert resp.status_code == 200, f"login {path} failed: {resp.text}"
    return resp.json()["token"]


@pytest_asyncio.fixture
async def teacher_token(client: AsyncClient):
    """JWT of the Computer Science teacher from the test demo.env."""
    return await _login(client, "/api/auth/teacher/login", {"email": "teacher@evalify.local", "password": "Teacher@123"})


@pytest_asyncio.fixture
async def physics_teacher_token(client: AsyncClient):
    """JWT of the Physics teacher (another subject)."""
    return await _login(client, "/api/auth/teacher/login", {"email": "physics@evalify.local", "password": "Teacher@123"})


@pytest_asyncio.fixture
async def science_teacher_token(client: AsyncClient):
    """JWT of the teacher with two subjects (Physics and Mathematics)."""
    return await _login(client, "/api/auth/teacher/login", {"email": "science@evalify.local", "password": "Teacher@123"})


@pytest_asyncio.fixture
async def student_token(client: AsyncClient):
    """JWT of CS2025001 (enrolled in Computer Science and Physics)."""
    return await _login(client, "/api/auth/student/login", {"roll_no": "CS2025001", "password": "Student@123"})


@pytest_asyncio.fixture
async def other_student_token(client: AsyncClient):
    """JWT of PH2025001 (Physics only)."""
    return await _login(client, "/api/auth/student/login", {"roll_no": "PH2025001", "password": "Student@123"})


@pytest_asyncio.fixture
async def ta_token(client: AsyncClient):
    """JWT of the Computer Science TA."""
    return await _login(client, "/api/auth/ta/login", {"email": "ta.cs@evalify.local", "password": "Ta@12345"})


@pytest_asyncio.fixture
async def physics_ta_token(client: AsyncClient):
    """JWT of the Physics TA (must not see Computer Science work)."""
    return await _login(client, "/api/auth/ta/login", {"email": "ta.phy@evalify.local", "password": "Ta@12345"})


def auth_headers(token: str) -> dict:
    """Build Authorization header from a JWT token."""
    return {"Authorization": f"Bearer {token}"}
