# paper.py — schemas for exam papers.
#
# The paper document is deliberately open (extra="allow"): the CreatePaper
# wizard sends many optional fields (per-question marks, rubrics, uploaded PDF
# URLs, config) and new pipeline fields (numerical tolerances, OMR template)
# must round-trip without a schema migration.
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class NumericalKey(BaseModel):
    """Rich numerical answer key. The legacy form — a list of accepted strings
    such as ["3", "3.0"] — is still accepted everywhere."""
    model_config = ConfigDict(extra="allow")

    answer: Union[str, float, List[Union[str, float]]]
    tolerance: float = 0.0
    tolerance_type: str = "abs"          # "abs" | "rel" (fraction, 0.01 = 1 %)
    unit: Optional[str] = None


class PaperCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str
    subject: str = ""
    type: str = "mcq"                    # mcq | mcq_numerical | mcq_numerical_subjective
    typeLabel: str = ""
    totalMarks: float = 0
    mcqCount: int = 0
    mcqMarks: float = 1
    mcqAnswers: Dict[str, Any] = Field(default_factory=dict)
    numericalCount: int = 0
    numericalMarks: float = 1
    numericalAnswers: Dict[str, Any] = Field(default_factory=dict)
    subjectiveCount: int = 0
    subjectiveMarks: float = 5
    subjectiveQuestions: List[Any] = Field(default_factory=list)
    subjectiveRubrics: List[Any] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)
    omrTemplate: Optional[Dict[str, Any]] = None
    answerSheetFormat: Optional[str] = None      # MCQ-only papers: "omr" or "handwritten"; None = the student chooses


class PaperOut(PaperCreate):
    id: str
    teacher_id: Optional[str] = None
    createdAt: str = ""
    resultCount: int = 0
