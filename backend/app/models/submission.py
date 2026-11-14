# submission.py — schemas for answer-sheet submissions.
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class SubmissionOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    paper_id: str
    paper_name: str = ""
    student_id: str
    student_name: str = ""
    roll_no: str = ""
    file_path: str = ""
    file_paths: List[str] = []
    page_count: int = 1
    sheet_type: str = "omr"
    status: str = "processing"
    submittedAt: str = ""
    result: Optional[Dict[str, Any]] = None


class SubmissionStatusOut(BaseModel):
    id: str
    status: str
    result: Optional[Dict[str, Any]] = None
