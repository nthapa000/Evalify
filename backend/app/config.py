# config.py — Application settings loaded from .env files.
# Uses pydantic-settings to auto-parse environment variables into typed fields.

from pydantic_settings import BaseSettings
from pathlib import Path

# Project root is two levels up from this file (backend/app/config.py → Evalify/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """All config values the backend needs. Loaded from .env files + environment."""

    # ── MongoDB ───────────────────────────────────────────────────────────────
    # Connection string for the local dev MongoDB container
    MONGO_URI: str = "mongodb://evalify:evalify_dev_pass@localhost:27017/evalify_db?authSource=admin"
    MONGO_DB_NAME: str = "evalify_db"

    # ── Teacher auth ──────────────────────────────────────────────────────────
    TEACHER_DEFAULT_EMAIL: str = "teacher@evalify.local"
    TEACHER_DEFAULT_PASSWORD: str = "Teacher@123"
    TEACHER_JWT_SECRET: str = "change_me_teacher_jwt_secret_32chars"
    TEACHER_JWT_EXPIRE_MINUTES: int = 480  # 8 hours

    # ── Student auth ──────────────────────────────────────────────────────────
    STUDENT_JWT_SECRET: str = "change_me_student_jwt_secret_32chars"
    STUDENT_JWT_EXPIRE_MINUTES: int = 240  # 4 hours
    SEED_STUDENT_ROLL: str = "CS2025001"
    SEED_STUDENT_PASSWORD: str = "Student@123"

    class Config:
        # Load variables from both credential files
        env_file = (
            str(PROJECT_ROOT / "teacher_credentials.env"),
            str(PROJECT_ROOT / "student_credentials.env"),
        )
        env_file_encoding = "utf-8"
        extra = "ignore"  # silently skip env vars not listed above


# Singleton — import this from anywhere
settings = Settings()
