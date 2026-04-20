# llm_service/app.py — LLM (Mistral 7B) subjective answer grading microservice.
# Phase 0: returns mock grading result after a simulated delay.
# Phase 5: replace mock_grade() with real vLLM call to Mistral-7B-Instruct.

from fastapi import FastAPI
from pydantic import BaseModel
import asyncio

app = FastAPI(title="LLM Grader Service", version="0.1.0")


class GradeRequest(BaseModel):
    question_text: str
    max_marks: float
    key_concepts: list[str]
    mandatory_concepts: list[str]
    marks_per_concept: float
    partial_credit: bool
    model_answer: str
    student_answer: str


async def mock_grade(req: GradeRequest) -> dict:
    """Simulate LLM grading. Returns structured JSON matching the prompt template."""
    await asyncio.sleep(2)
    # Mock: student gets partial credit (half the concepts found)
    found = req.key_concepts[: len(req.key_concepts) // 2]
    missing = req.key_concepts[len(req.key_concepts) // 2 :]
    raw = len(found) * req.marks_per_concept
    return {
        "concepts_found": found,
        "concepts_missing": missing,
        "mandatory_met": req.mandatory_concepts[0] in found if req.mandatory_concepts else True,
        "raw_score": raw,
        "capped_score": min(raw, req.max_marks),
        "feedback": "Mock: partial credit awarded for concepts found.",
    }


@app.post("/llm/grade")
async def grade(req: GradeRequest):
    result = await mock_grade(req)
    return result
