# mongodb.py — async MongoDB (Motor) connection and collection accessors.

from __future__ import annotations

import asyncio

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ServerSelectionTimeoutError

from app.config import settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db(max_retries: int = 10, delay_s: float = 5.0):
    """Connect and ping, retrying while MongoDB is still starting (e.g. in Docker)."""
    global _client, _db
    # In-memory database (no server needed); everything is lost when the backend stops
    if settings.EVALIFY_INMEMORY_DB:
        from mongomock_motor import AsyncMongoMockClient
        _client = AsyncMongoMockClient()
        _db = _client[settings.MONGO_DB_NAME]
        return print("⚠️  Using an in-memory database (EVALIFY_INMEMORY_DB=1): data is lost on restart")
    _client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
    _db = _client[settings.MONGO_DB_NAME]
    for attempt in range(1, max_retries + 1):
        try:
            await _client.admin.command("ping")
            return print(f"✅ Connected to MongoDB: {settings.MONGO_DB_NAME}")
        except ServerSelectionTimeoutError as exc:
            if attempt == max_retries:
                raise RuntimeError(f"MongoDB unreachable after {max_retries} attempts: {exc}") from exc
            print(f"⏳ MongoDB not ready ({attempt}/{max_retries}), retrying in {delay_s}s…")
            await asyncio.sleep(delay_s)


async def close_db():
    """Close the client on shutdown."""
    if _client:
        _client.close()


def get_db() -> AsyncIOMotorDatabase:
    """Database handle (only valid after connect_db)."""
    if _db is None:
        raise RuntimeError("Database not initialised — call connect_db() first")
    return _db


# Collection shortcuts
def users_col():
    return get_db()["users"]


def papers_col():
    return get_db()["papers"]


def submissions_col():
    return get_db()["submissions"]
