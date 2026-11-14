# seed.py — create the demo teacher and students at startup (idempotent).

from datetime import datetime, timezone

from passlib.context import CryptContext

from app.config import settings
from app.db.mongodb import users_col

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
SUBJECT = "Computer Science"
DEMO_STUDENTS = [
    ("CS2025001", "Aarav Sharma"), ("CS2025002", "Priya Patel"), ("CS2025003", "Rohit Verma"),
    ("CS2025004", "Ananya Singh"), ("CS2025005", "Vikram Nair"), ("CS2025006", "Sneha Reddy"),
]


async def seed_users():
    """Insert missing demo users; replace PLACEHOLDER hashes left by mongo-init.js."""
    col = users_col()
    now = datetime.now(timezone.utc)

    # Teacher
    t = await col.find_one({"email": settings.TEACHER_DEFAULT_EMAIL})
    if not t:
        await col.insert_one({"role": "teacher", "email": settings.TEACHER_DEFAULT_EMAIL,
                              "name": "Prof. Ramesh Kumar", "subject": SUBJECT, "created_at": now,
                              "password_hash": pwd_ctx.hash(settings.TEACHER_DEFAULT_PASSWORD)})
    else:
        fix = {}
        if "PLACEHOLDER" in t.get("password_hash", ""):
            fix |= {"password_hash": pwd_ctx.hash(settings.TEACHER_DEFAULT_PASSWORD), "name": "Prof. Ramesh Kumar"}
        if not t.get("subject"):
            fix["subject"] = SUBJECT
        if fix:
            await col.update_one({"_id": t["_id"]}, {"$set": fix})

    # Students
    for roll, name in DEMO_STUDENTS:
        s = await col.find_one({"roll_no": roll})
        if not s:
            await col.insert_one({"role": "student", "roll_no": roll, "name": name, "subject": SUBJECT,
                                  "created_at": now, "password_hash": pwd_ctx.hash(settings.SEED_STUDENT_PASSWORD)})
        elif "PLACEHOLDER" in s.get("password_hash", ""):
            await col.update_one({"_id": s["_id"]}, {"$set": {
                "password_hash": pwd_ctx.hash(settings.SEED_STUDENT_PASSWORD), "name": name, "subject": SUBJECT}})
