# mongodb.py — Async MongoDB connection using Motor.
# Provides connect/disconnect lifecycle hooks and collection accessors.

from __future__ import annotations
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import settings

# Module-level references (set during app startup)
_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db(max_retries: int = 10, delay_s: float = 5.0):
    """Open the Motor client and wait for MongoDB to become reachable.

    Retries up to max_retries times with delay_s between attempts.
    This makes the backend resilient to MongoDB starting slower than the
    backend container (common in Docker Compose).
    """
    import asyncio
    from pymongo.errors import ServerSelectionTimeoutError

    global _client, _db
    _client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    _db = _client[settings.MONGO_DB_NAME]

    for attempt in range(1, max_retries + 1):
        try:
            await _client.admin.command("ping")
            print(f"✅ Connected to MongoDB: {settings.MONGO_DB_NAME}")
            return
        except ServerSelectionTimeoutError as exc:
            if attempt == max_retries:
                raise RuntimeError(
                    f"MongoDB unreachable after {max_retries} attempts. "
                    f"Last error: {exc}"
                ) from exc
            print(
                f"⏳ MongoDB not ready (attempt {attempt}/{max_retries}), "
                f"retrying in {delay_s}s…"
            )
            await asyncio.sleep(delay_s)


async def close_db():
    """Close the Motor client. Called once during FastAPI lifespan shutdown."""
    global _client
    if _client:
        _client.close()
        print("❌ MongoDB connection closed")


def get_db() -> AsyncIOMotorDatabase:
    """Return the database handle. Use inside route handlers."""
    if _db is None:
        raise RuntimeError("Database not initialised — call connect_db() first")
    return _db


# ── Collection helpers (shortcuts) ────────────────────────────────────────────
def users_col():
    """users collection — stores teacher and student accounts."""
    return get_db()["users"]


def papers_col():
    """papers collection — stores exam papers created by teachers."""
    return get_db()["papers"]


def submissions_col():
    """submissions collection — one doc per student answer-sheet upload."""
    return get_db()["submissions"]


def results_col():
    """results collection — evaluation scores linked to submissions."""
    return get_db()["results"]
