# subjective_grader.py — legacy Ollama grader for one subjective answer.
#
# Fallback path (the vLLM pipeline grades per concept instead). Marks are
# recomputed in Python from the concepts found; keyword matching is used if
# Ollama fails or returns unparseable JSON.

from __future__ import annotations

import json
import os
import re
import time
from typing import Tuple

import requests

from app.prompts.prompt_subjective_grading import (
    STUDENT_ANSWER_PLACEHOLDER,
    build_subjective_grading_prompt,
)

# Server and model (a text LLM if set, else the vision model)
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_LLM_MODEL = os.environ.get("OLLAMA_LLM_MODEL",
                                  os.environ.get("OLLAMA_VISION_MODEL", "llama3.2-vision:11b"))
_TIMEOUT = 120


def grade_subjective_question(question_text: str, student_answer: str, rubric: dict,
                              subject: str = "") -> Tuple[dict, float]:
    """Grade one answer with a prompt built from the rubric. Returns (result, latency_s)."""
    prompt = build_subjective_grading_prompt(
        question_text=question_text, student_answer=student_answer or "",
        key_concepts=rubric.get("key_concepts", []),
        mandatory_concepts=rubric.get("mandatory_concepts", []),
        marks_per_concept=float(rubric.get("marks_per_concept", 1)),
        model_answer=rubric.get("model_answer", ""), subject=subject)
    return _grade(prompt, student_answer, rubric)


def grade_with_template(prompt_template: str, student_answer: str, rubric: dict,
                        subject: str = "") -> Tuple[dict, float]:
    """Grade with the teacher's stored prompt template (falls back to a fresh prompt)."""
    if not (prompt_template or "").strip():
        return grade_subjective_question("", student_answer, rubric, subject)
    prompt = prompt_template.replace(STUDENT_ANSWER_PLACEHOLDER, (student_answer or "").strip())
    return _grade(prompt, student_answer, rubric)


def _grade(prompt: str, student_answer: str, rubric: dict) -> Tuple[dict, float]:
    """Shared path: handle edge cases, call Ollama, parse, fall back to keywords."""
    concepts = rubric.get("key_concepts", [])
    per = float(rubric.get("marks_per_concept", 1))

    # Edge cases that need no LLM call
    if not (student_answer or "").strip():
        return _result(rubric, [], "No answer provided."), 0.0
    if not concepts:
        return _result(rubric, [], "No rubric concepts defined; full marks awarded.",
                       marks=len(concepts) * per), 0.0

    # Call the LLM (low temperature for repeatability)
    t0 = time.time()
    try:
        resp = requests.post(f"{OLLAMA_HOST}/api/generate", timeout=_TIMEOUT, json={
            "model": OLLAMA_LLM_MODEL, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.1}})
        resp.raise_for_status()
        raw = resp.json().get("response", "")
    except Exception as exc:
        print(f"  LLM grading error: {exc} — keyword fallback")
        raw = ""
    latency = round(time.time() - t0, 3)

    # Parse the JSON; on failure use keyword matching on the real answer
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    try:
        data = json.loads(match.group()) if match else None
    except ValueError:
        data = None
    if data is None:
        found = [c for c in concepts if c.lower() in student_answer.lower()]
        return _result(rubric, found, f"Keyword fallback: {len(found)}/{len(concepts)} concepts matched."), latency

    # Trust only the list of concepts found; marks are recomputed in _result
    found = [str(c) for c in data.get("concepts_found", [])]
    return _result(rubric, found, str(data.get("feedback", "")),
                   ocr_issues=bool(data.get("ocr_issues_detected", False))), latency


def _result(rubric: dict, found: list, feedback: str, ocr_issues: bool = False,
            marks: float | None = None) -> dict:
    """Build the result dict; mandatory rule: no mandatory concept found → 0 marks."""
    concepts = rubric.get("key_concepts", [])
    mandatory = rubric.get("mandatory_concepts", [])
    per = float(rubric.get("marks_per_concept", 1))
    max_marks = len(concepts) * per

    # Fuzzy match so "photosynthesis process" counts for "photosynthesis"
    def hit(c):
        return any(c.lower() in f.lower() or f.lower() in c.lower() for f in found)

    mandatory_met = any(hit(m) for m in mandatory) if mandatory else True
    if marks is None:
        marks = 0.0 if not mandatory_met else min(sum(per for c in concepts if hit(c)), max_marks)
    return {
        "concept_scores": {c: (per if hit(c) else 0.0) for c in concepts},
        "concepts_found": found,
        "concepts_missing": [c for c in concepts if not hit(c)],
        "mandatory_concepts_met": mandatory_met,
        "marks_awarded": marks,
        "max_marks": max_marks,
        "feedback": feedback,
        "ocr_issues_detected": ocr_issues,
    }
