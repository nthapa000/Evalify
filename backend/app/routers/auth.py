# auth.py — Authentication router: JWT login for teacher & student.
# POST /auth/teacher/login  → email + password → JWT token
# POST /auth/student/login  → roll_no + password → JWT token

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt

from app.config import settings
from app.db.mongodb import users_col
from app.models.user import TeacherLoginRequest, StudentLoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Bcrypt hasher — used to verify passwords against stored hashes
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer scheme — extracts "Authorization: Bearer <token>" header
bearer_scheme = HTTPBearer()


# ── Helper: create a signed JWT ──────────────────────────────────────────────

def _create_token(payload: dict, secret: str, expire_minutes: int) -> str:
    """Sign a JWT with the given payload, secret, and expiry."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload["exp"] = expire
    return jwt.encode(payload, secret, algorithm="HS256")


# ── Teacher Login ──────────────────────────────────────────────────────────────

@router.post("/teacher/login", response_model=LoginResponse)
async def teacher_login(body: TeacherLoginRequest):
    """Authenticate a teacher by email + password, return JWT."""
    # Look up teacher in MongoDB
    user = await users_col().find_one({"email": body.email, "role": "teacher"})
    if not user or not pwd_ctx.verify(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    # Build JWT payload — include subject so papers router can enforce it
    token = _create_token(
        payload={
            "sub":     str(user["_id"]),
            "role":    "teacher",
            "email":   user["email"],
            "subject": user.get("subject", ""),
        },
        secret=settings.TEACHER_JWT_SECRET,
        expire_minutes=settings.TEACHER_JWT_EXPIRE_MINUTES,
    )

    return LoginResponse(
        token=token,
        user={
            "id":      str(user["_id"]),
            "name":    user["name"],
            "email":   user["email"],
            "role":    "teacher",
            "subject": user.get("subject", ""),
        },
    )


# ── Student Login ──────────────────────────────────────────────────────────────

@router.post("/student/login", response_model=LoginResponse)
async def student_login(body: StudentLoginRequest):
    """Authenticate a student by roll_no + password, return JWT."""
    user = await users_col().find_one({"roll_no": body.roll_no, "role": "student"})
    if not user or not pwd_ctx.verify(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid roll number or password.")

    token = _create_token(
        payload={"sub": str(user["_id"]), "role": "student", "roll_no": user["roll_no"]},
        secret=settings.STUDENT_JWT_SECRET,
        expire_minutes=settings.STUDENT_JWT_EXPIRE_MINUTES,
    )

    return LoginResponse(
        token=token,
        user={
            "id": str(user["_id"]),
            "name": user["name"],
            "roll_no": user["roll_no"],
            "role": "student",
        },
    )


# ── Dependency: decode JWT and return current user ────────────────────────────

async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """
    FastAPI dependency — decode the Bearer token and return the user dict.
    Tries teacher secret first, then student secret.
    Raises 401 if token is invalid or expired.
    """
    token = creds.credentials
    # Try teacher secret
    for secret, role_hint in [
        (settings.TEACHER_JWT_SECRET, "teacher"),
        (settings.STUDENT_JWT_SECRET, "student"),
    ]:
        try:
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            return payload  # { sub, role, email/roll_no, exp }
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired.")
        except jwt.InvalidTokenError:
            continue  # wrong secret — try the other one

    raise HTTPException(status_code=401, detail="Invalid authentication token.")


async def require_teacher(user: dict = Depends(get_current_user)):
    """Dependency that ensures the caller is a teacher."""
    if user.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Teacher access required.")
    return user


async def require_student(user: dict = Depends(get_current_user)):
    """Dependency that ensures the caller is a student."""
    if user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Student access required.")
    return user
