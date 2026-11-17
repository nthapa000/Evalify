# seed.py — create/update the demo teachers, TAs and students from demo.env at startup (idempotent).

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from passlib.context import CryptContext

from app.config import settings
from app.db.demo_users import parse_demo_env
from app.db.mongodb import users_col

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=settings.BCRYPT_ROUNDS)

# Used only when demo.env is missing: the original single teacher + six students
FALLBACK = {
    "teachers": [{"email": settings.TEACHER_DEFAULT_EMAIL, "password": settings.TEACHER_DEFAULT_PASSWORD,
                  "name": "Prof. Ramesh Kumar", "subject": "Computer Science"}],
    "tas": [],
    "students": [{"roll_no": r, "password": settings.SEED_STUDENT_PASSWORD, "name": n, "subjects": ["Computer Science"]}
                 for r, n in [("CS2025001", "Aarav Sharma"), ("CS2025002", "Priya Patel"), ("CS2025003", "Rohit Verma"),
                              ("CS2025004", "Ananya Singh"), ("CS2025005", "Vikram Nair"), ("CS2025006", "Sneha Reddy")]],
}


def load_demo_users() -> dict:
    """Users from demo.env (EVALIFY_DEMO_ENV), or the fallback list when the file does not exist."""
    path = Path(settings.EVALIFY_DEMO_ENV)
    return parse_demo_env(path.read_text()) if path.exists() else FALLBACK


def _fingerprint(password: str) -> str:
    """Cheap check whether demo.env changed a password (bcrypt verify for 100+ users would slow start-up)."""
    return hashlib.sha256(password.encode()).hexdigest()


async def _upsert(query: dict, fields: dict, password: str) -> None:
    """Insert the user, or update name/subjects (and the hash only when the password changed)."""
    col = users_col()
    doc = await col.find_one(query)
    fp = _fingerprint(password)
    if doc is None:
        await col.insert_one({**query, **fields, "created_at": datetime.now(timezone.utc),
                              "password_hash": pwd_ctx.hash(password), "password_fp": fp})
        return
    update = dict(fields)
    if doc.get("password_fp") != fp or "PLACEHOLDER" in doc.get("password_hash", ""):
        update |= {"password_hash": pwd_ctx.hash(password), "password_fp": fp}
    await col.update_one({"_id": doc["_id"]}, {"$set": update})


async def seed_users(users: dict | None = None) -> None:
    """Create or update every demo user (teachers, TAs, students)."""
    users = users or load_demo_users()
    for t in users["teachers"]:
        await _upsert({"role": "teacher", "email": t["email"]},
                      {"name": t["name"], "subject": t["subject"], "subjects": t.get("subjects") or [t["subject"]]},
                      t["password"])
    for ta in users["tas"]:
        await _upsert({"role": "ta", "email": ta["email"]}, {"name": ta["name"], "subjects": ta["subjects"]},
                      ta["password"])
    for s in users["students"]:
        # "subject" (first subject) is kept for older code that expects one subject
        await _upsert({"role": "student", "roll_no": s["roll_no"]},
                      {"name": s["name"], "subjects": s["subjects"], "subject": s["subjects"][0]}, s["password"])
