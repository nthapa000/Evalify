# seed.py — Insert seed users (teacher + student) with real bcrypt hashes.
# Runs once at startup; idempotent (skips if users already exist).

from passlib.context import CryptContext
from app.config import settings
from app.db.mongodb import users_col
from datetime import datetime, timezone

# bcrypt hasher — same instance used in auth router
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_users():
    """Insert default teacher and student if they don't already exist.
    Also fixes placeholder password hashes left by mongo-init.js."""
    col = users_col()

    # ── Seed Teacher ──────────────────────────────────────────────────────────
    existing_teacher = await col.find_one({"email": settings.TEACHER_DEFAULT_EMAIL})
    if not existing_teacher:
        await col.insert_one({
            "role": "teacher",
            "email": settings.TEACHER_DEFAULT_EMAIL,
            "name": "Prof. Ramesh Kumar",
            "subject": "Computer Science",
            "password_hash": pwd_ctx.hash(settings.TEACHER_DEFAULT_PASSWORD),
            "created_at": datetime.now(timezone.utc),
        })
        print(f"🌱 Seeded teacher: {settings.TEACHER_DEFAULT_EMAIL}")
    else:
        updates = {}
        if "PLACEHOLDER" in existing_teacher.get("password_hash", ""):
            updates["password_hash"] = pwd_ctx.hash(settings.TEACHER_DEFAULT_PASSWORD)
            updates["name"] = "Prof. Ramesh Kumar"
        if not existing_teacher.get("subject"):
            updates["subject"] = "Computer Science"
        if updates:
            await col.update_one({"_id": existing_teacher["_id"]}, {"$set": updates})
            print(f"🔧 Updated teacher record: {settings.TEACHER_DEFAULT_EMAIL}")
        else:
            print(f"✓ Teacher already exists: {settings.TEACHER_DEFAULT_EMAIL}")

    # ── Seed Students ─────────────────────────────────────────────────────────
    DEMO_STUDENTS = [
        {"roll_no": "CS2025001", "name": "Aarav Sharma"},
        {"roll_no": "CS2025002", "name": "Priya Patel"},
        {"roll_no": "CS2025003", "name": "Rohit Verma"},
        {"roll_no": "CS2025004", "name": "Ananya Singh"},
        {"roll_no": "CS2025005", "name": "Vikram Nair"},
        {"roll_no": "CS2025006", "name": "Sneha Reddy"},
    ]

    for s in DEMO_STUDENTS:
        existing = await col.find_one({"roll_no": s["roll_no"]})
        if not existing:
            await col.insert_one({
                "role": "student",
                "roll_no": s["roll_no"],
                "name": s["name"],
                "subject": "Computer Science",
                "password_hash": pwd_ctx.hash(settings.SEED_STUDENT_PASSWORD),
                "created_at": datetime.now(timezone.utc),
            })
            print(f"🌱 Seeded student: {s['roll_no']} ({s['name']})")
        elif "PLACEHOLDER" in existing.get("password_hash", ""):
            await col.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "password_hash": pwd_ctx.hash(settings.SEED_STUDENT_PASSWORD),
                    "name": s["name"],
                    "subject": "Computer Science",
                }},
            )
            print(f"🔧 Fixed placeholder hash for student: {s['roll_no']}")
        else:
            print(f"✓ Student already exists: {s['roll_no']} ({s['name']})")
