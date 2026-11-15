# config.py — typed settings from environment variables and the credential .env files.

from pathlib import Path

from pydantic_settings import BaseSettings

# Repo root (backend/app/config.py → Evalify/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Backend settings; any field can be overridden by an env var of the same name."""

    # MongoDB
    MONGO_URI: str = "mongodb://evalify:evalify_dev_pass@localhost:27017/evalify_db?authSource=admin"
    MONGO_DB_NAME: str = "evalify_db"

    # Teacher auth + seed account
    TEACHER_DEFAULT_EMAIL: str = "teacher@evalify.local"
    TEACHER_DEFAULT_PASSWORD: str = "Teacher@123"
    TEACHER_JWT_SECRET: str = "change_me_teacher_jwt_secret_32chars"
    TEACHER_JWT_EXPIRE_MINUTES: int = 480

    # Student auth + seed account
    STUDENT_JWT_SECRET: str = "change_me_student_jwt_secret_32chars"
    STUDENT_JWT_EXPIRE_MINUTES: int = 240
    SEED_STUDENT_ROLL: str = "CS2025001"
    SEED_STUDENT_PASSWORD: str = "Student@123"

    # TA auth (third role)
    TA_JWT_SECRET: str = "change_me_ta_jwt_secret_32_chars_x"
    TA_JWT_EXPIRE_MINUTES: int = 480

    # Demo users (teachers, TAs, students) come from this file; no admin UI yet
    EVALIFY_DEMO_ENV: str = str(PROJECT_ROOT / "demo.env")
    BCRYPT_ROUNDS: int = 12            # tests lower this to keep seeding fast

    # Share of auto-accepted written answers sent to a TA at random ("random quality check"); 0 = off.
    # Grader confidence did not predict wrong marks (eval/reports/exp_routing), so random checks measure quality.
    EVALIFY_SPOT_CHECK_RATE: float = 0.05

    # Run without a MongoDB server (data is lost on restart) — for UI testing on the GPU cluster
    EVALIFY_INMEMORY_DB: bool = False

    class Config:
        env_file = (str(PROJECT_ROOT / "teacher_credentials.env"),
                    str(PROJECT_ROOT / "student_credentials.env"))
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
