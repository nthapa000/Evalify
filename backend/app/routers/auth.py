# auth.py — JWT login for teachers and TAs (email) and students (roll number) + auth dependencies.

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from app.config import settings
from app.db.mongodb import users_col
from app.models.user import LoginResponse, StudentLoginRequest, TaLoginRequest, TeacherLoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")   # verify works for any bcrypt cost
bearer_scheme = HTTPBearer()


def _create_token(payload: dict, secret: str, expire_minutes: int) -> str:
    """Sign an HS256 JWT that expires after expire_minutes."""
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    return jwt.encode(payload, secret, algorithm="HS256")


@router.post("/teacher/login", response_model=LoginResponse)
async def teacher_login(body: TeacherLoginRequest):
    """Email + password → JWT (includes the teacher's subject)."""
    user = await users_col().find_one({"email": body.email, "role": "teacher"})
    if not user or not pwd_ctx.verify(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    info = {"id": str(user["_id"]), "name": user["name"], "email": user["email"],
            "role": "teacher", "subject": user.get("subject", ""), "subjects": user.get("subjects", [])}
    token = _create_token({"sub": info["id"], "role": "teacher", "email": info["email"],
                           "subject": info["subject"]},
                          settings.TEACHER_JWT_SECRET, settings.TEACHER_JWT_EXPIRE_MINUTES)
    return LoginResponse(token=token, user=info)


@router.post("/student/login", response_model=LoginResponse)
async def student_login(body: StudentLoginRequest):
    """Roll number + password → JWT."""
    user = await users_col().find_one({"roll_no": body.roll_no, "role": "student"})
    if not user or not pwd_ctx.verify(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid roll number or password.")
    info = {"id": str(user["_id"]), "name": user["name"], "roll_no": user["roll_no"], "role": "student",
            "subjects": user.get("subjects") or ([user["subject"]] if user.get("subject") else [])}
    token = _create_token({"sub": info["id"], "role": "student", "roll_no": info["roll_no"]},
                          settings.STUDENT_JWT_SECRET, settings.STUDENT_JWT_EXPIRE_MINUTES)
    return LoginResponse(token=token, user=info)


# TA login: same shape as the teacher login, own secret, subjects from demo.env
@router.post("/ta/login", response_model=LoginResponse)
async def ta_login(body: TaLoginRequest):
    """Email + password → JWT for a TA (role "ta")."""
    user = await users_col().find_one({"email": body.email, "role": "ta"})
    if not user or not pwd_ctx.verify(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    info = {"id": str(user["_id"]), "name": user["name"], "email": user["email"], "role": "ta",
            "subjects": user.get("subjects", [])}
    token = _create_token({"sub": info["id"], "role": "ta", "email": info["email"]},
                          settings.TA_JWT_SECRET, settings.TA_JWT_EXPIRE_MINUTES)
    return LoginResponse(token=token, user=info)


async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """Decode the Bearer token with the teacher, student, then TA secret."""
    for secret in (settings.TEACHER_JWT_SECRET, settings.STUDENT_JWT_SECRET, settings.TA_JWT_SECRET):
        try:
            return jwt.decode(creds.credentials, secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired.")
        except jwt.InvalidTokenError:
            continue
    raise HTTPException(status_code=401, detail="Invalid authentication token.")


async def require_teacher(user: dict = Depends(get_current_user)):
    """403 unless the caller is a teacher."""
    if user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Teacher access required.")
    return user


async def require_student(user: dict = Depends(get_current_user)):
    """403 unless the caller is a student."""
    if user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Student access required.")
    return user


# TA-only endpoints
async def require_ta(user: dict = Depends(get_current_user)):
    """403 unless the caller is a TA."""
    if user.get("role") != "ta":
        raise HTTPException(status_code=403, detail="TA access required.")
    return user


# Subjects are read from the database (demo.env can change them without new tokens)
async def user_subjects(user: dict) -> list:
    """Subjects of the calling user: a teacher's subject, a TA's or a student's enrolled subjects."""
    from bson import ObjectId
    doc = await users_col().find_one({"_id": ObjectId(user["sub"])}) if ObjectId.is_valid(user.get("sub", "")) else None
    if not doc:
        return []
    return doc.get("subjects") or ([doc["subject"]] if doc.get("subject") else [])
