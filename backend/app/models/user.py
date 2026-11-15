# user.py — request/response schemas for authentication.
from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel


class TeacherLoginRequest(BaseModel):
    email: str
    password: str


class StudentLoginRequest(BaseModel):
    roll_no: str
    password: str


# TA login (email + password), same as the teacher's
class TaLoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user: Dict[str, Any]
