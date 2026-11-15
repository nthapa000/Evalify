# test_mongodb.py — database connection modes.

import pytest

from app.db import mongodb


# Why: on the GPU cluster there is no MongoDB; EVALIFY_INMEMORY_DB=1 lets the whole app run for UI testing
@pytest.mark.asyncio
async def test_inmemory_mode(monkeypatch):
    monkeypatch.setattr(mongodb.settings, "EVALIFY_INMEMORY_DB", True)
    await mongodb.connect_db(max_retries=1)
    await mongodb.users_col().insert_one({"role": "ta", "email": "x@y.z"})
    assert await mongodb.users_col().count_documents({}) == 1
    await mongodb.close_db()


# Why: collection helpers must refuse to run before connect_db (clear error instead of a None crash)
def test_db_not_initialised(monkeypatch):
    monkeypatch.setattr(mongodb, "_db", None)
    with pytest.raises(RuntimeError, match="not initialised"):
        mongodb.get_db()
