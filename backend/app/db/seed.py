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
            "password_hash": pwd_ctx.hash(settings.TEACHER_DEFAULT_PASSWORD),
            "created_at": datetime.now(timezone.utc),
        })
        print(f"🌱 Seeded teacher: {settings.TEACHER_DEFAULT_EMAIL}")
    elif "PLACEHOLDER" in existing_teacher.get("password_hash", ""):
        # Fix placeholder hash left by mongo-init.js
        await col.update_one(
            {"_id": existing_teacher["_id"]},
            {"$set": {
                "password_hash": pwd_ctx.hash(settings.TEACHER_DEFAULT_PASSWORD),
                "name": "Prof. Ramesh Kumar",
            }},
        )
        print(f"🔧 Fixed placeholder hash for teacher: {settings.TEACHER_DEFAULT_EMAIL}")
    else:
        print(f"✓ Teacher already exists: {settings.TEACHER_DEFAULT_EMAIL}")

    # ── Seed Student ──────────────────────────────────────────────────────────
    existing_student = await col.find_one({"roll_no": settings.SEED_STUDENT_ROLL})
    if not existing_student:
        await col.insert_one({
            "role": "student",
            "roll_no": settings.SEED_STUDENT_ROLL,
            "name": "Aarav Sharma",
            "subject": "Computer Science",
            "password_hash": pwd_ctx.hash(settings.SEED_STUDENT_PASSWORD),
            "created_at": datetime.now(timezone.utc),
        })
        print(f"🌱 Seeded student: {settings.SEED_STUDENT_ROLL}")
    elif "PLACEHOLDER" in existing_student.get("password_hash", ""):
        # Fix placeholder hash left by mongo-init.js
        await col.update_one(
            {"_id": existing_student["_id"]},
            {"$set": {
                "password_hash": pwd_ctx.hash(settings.SEED_STUDENT_PASSWORD),
                "name": "Aarav Sharma",
                "subject": "Computer Science",
            }},
        )
        print(f"🔧 Fixed placeholder hash for student: {settings.SEED_STUDENT_ROLL}")
    else:
        print(f"✓ Student already exists: {settings.SEED_STUDENT_ROLL}")
