# subjective_grader.py — LLM-based grader for one subjective question.
#
# Flow per question:
#   1. Build grading prompt from rubric (key_concepts, mandatory_concepts, marks_per_concept).
#   2. POST to Ollama /api/generate (text-only, temperature=0.1 for determinism).
#   3. Parse JSON response; validate mandatory concepts; cap at max_marks.
#   4. Fallback to simple keyword matching if Ollama fails or returns bad JSON.

from __future__ import annotations
import re
import json
import time
import os
import requests
from typing import Tuple

from app.prompts.prompt_subjective_grading import (
    build_subjective_grading_prompt,
    STUDENT_ANSWER_PLACEHOLDER,
)

OLLAMA_HOST      = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
# Prefer a dedicated text LLM; fall back to the vision model (it handles text too).
OLLAMA_LLM_MODEL = os.environ.get(
    "OLLAMA_LLM_MODEL",
    os.environ.get("OLLAMA_VISION_MODEL", "llama3.2-vision:11b"),
)
_TIMEOUT = 120  # seconds


def grade_subjective_question(
    question_text:     str,
    student_answer:    str,
    rubric:            dict,
    subject:           str = "",
) -> Tuple[dict, float]:
    """
    Grade one subjective question using the Ollama LLM.

    rubric fields (from RubricBuilder):
        key_concepts       — list[str]
        mandatory_concepts — list[str]  (subset of key_concepts)
        marks_per_concept  — float
        model_answer       — str

    Returns (grading_result, latency_seconds).

    grading_result keys:
        concept_scores        — {concept: marks_awarded_for_it}
        concepts_found        — list[str]
        concepts_missing      — list[str]
        mandatory_concepts_met — bool
        marks_awarded         — float  (capped at max_marks)
        max_marks             — float
        feedback              — str
        ocr_issues_detected   — bool
    """
    key_concepts       = rubric.get("key_concepts", [])
    mandatory_concepts = rubric.get("mandatory_concepts", [])
    marks_per_concept  = float(rubric.get("marks_per_concept", 1))
    model_answer       = rubric.get("model_answer", "")
    max_marks          = len(key_concepts) * marks_per_concept

    # ── Edge: blank answer ────────────────────────────────────────────────────
    if not student_answer or not student_answer.strip():
        return _build_result(
            key_concepts       = key_concepts,
            found              = [],
            mandatory_concepts = mandatory_concepts,
            marks_per_concept  = marks_per_concept,
            max_marks          = max_marks,
            feedback           = "No answer provided.",
            ocr_issues         = False,
        ), 0.0

    # ── Edge: no rubric concepts → award full marks ───────────────────────────
    if not key_concepts:
        return {
            "concept_scores":         {},
            "concepts_found":         [],
            "concepts_missing":       [],
            "mandatory_concepts_met": True,
            "marks_awarded":          max_marks,
            "max_marks":              max_marks,
            "feedback":               "No rubric concepts defined; full marks awarded.",
            "ocr_issues_detected":    False,
        }, 0.0

    # ── Build and send prompt ─────────────────────────────────────────────────
    prompt = build_subjective_grading_prompt(
        question_text     = question_text,
        student_answer    = student_answer,
        key_concepts      = key_concepts,
        mandatory_concepts = mandatory_concepts,
        marks_per_concept = marks_per_concept,
        model_answer      = model_answer,
        subject           = subject,
    )

    # ── Print full prompt to terminal before sending ─────────────────────────
    _W = 72
    print()
    print("▶" * _W)
    print(f"  SUBJECTIVE GRADING PROMPT  │  {question_text[:60]}")
    print("▶" * _W)
    print(prompt)
    print("◀" * _W)
    print()

    t0 = time.time()
    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model":   OLLAMA_LLM_MODEL,
                "prompt":  prompt,
                "stream":  False,
                "options": {"temperature": 0.1},
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        raw     = resp.json().get("response", "").strip()
        latency = round(time.time() - t0, 3)
        print(f"  LLM Grading response ({latency:.1f}s):")
        print(f"  {raw}")
        print()

        result = _parse_llm_json(raw, key_concepts, mandatory_concepts, marks_per_concept, max_marks)
        return result, latency

    except Exception as exc:
        latency = round(time.time() - t0, 3)
        print(f"  LLM Grading error ({latency:.1f}s): {exc}. Using keyword fallback.")
        return _keyword_fallback(
            student_answer, key_concepts, mandatory_concepts, marks_per_concept, max_marks
        ), latency


# ── Template-based grading ────────────────────────────────────────────────────

def grade_with_template(
    prompt_template: str,
    student_answer:  str,
    rubric:          dict,
    subject:         str = "",
) -> Tuple[dict, float]:
    """
    Grade using a pre-built prompt template stored in the paper document.
    Substitutes <<<STUDENT_ANSWER>>> with the actual student answer and sends to Ollama.
    Falls back to grade_subjective_question if template is missing or empty.
    """
    if not prompt_template or not prompt_template.strip():
        return grade_subjective_question("", student_answer, rubric, subject)

    key_concepts       = rubric.get("key_concepts", [])
    mandatory_concepts = rubric.get("mandatory_concepts", [])
    marks_per_concept  = float(rubric.get("marks_per_concept", 1))
    max_marks          = len(key_concepts) * marks_per_concept

    if not student_answer or not student_answer.strip():
        return _build_result(
            key_concepts       = key_concepts,
            found              = [],
            mandatory_concepts = mandatory_concepts,
            marks_per_concept  = marks_per_concept,
            max_marks          = max_marks,
            feedback           = "No answer provided.",
        ), 0.0

    if not key_concepts:
        return {
            "concept_scores":         {},
            "concepts_found":         [],
            "concepts_missing":       [],
            "mandatory_concepts_met": True,
            "marks_awarded":          max_marks,
            "max_marks":              max_marks,
            "feedback":               "No rubric concepts defined; full marks awarded.",
            "ocr_issues_detected":    False,
        }, 0.0

    prompt = prompt_template.replace(STUDENT_ANSWER_PLACEHOLDER, student_answer.strip())

    _W = 72
    print()
    print("▶" * _W)
    print("  SUBJECTIVE GRADING PROMPT  (pre-built template)")
    print("▶" * _W)
    print(prompt)
    print("◀" * _W)
    print()

    t0 = time.time()
    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model":   OLLAMA_LLM_MODEL,
                "prompt":  prompt,
                "stream":  False,
                "options": {"temperature": 0.1},
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        raw     = resp.json().get("response", "").strip()
        latency = round(time.time() - t0, 3)
        print(f"  LLM Grading response ({latency:.1f}s):")
        print(f"  {raw}")
        print()
        return _parse_llm_json(raw, key_concepts, mandatory_concepts, marks_per_concept, max_marks), latency

    except Exception as exc:
        latency = round(time.time() - t0, 3)
        print(f"  LLM Grading error ({latency:.1f}s): {exc}. Using keyword fallback.")
        return _keyword_fallback(
            student_answer, key_concepts, mandatory_concepts, marks_per_concept, max_marks
        ), latency


# ── JSON parser ───────────────────────────────────────────────────────────────

def _parse_llm_json(
    raw:               str,
    key_concepts:      list,
    mandatory_concepts: list,
    marks_per_concept: float,
    max_marks:         float,
) -> dict:
    """
    Extract and validate the JSON block from the LLM response.
    Falls back to keyword matching if parsing fails.
    """
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        print("  LLM Grading: no JSON block found. Using keyword fallback.")
        return _keyword_fallback("", key_concepts, mandatory_concepts, marks_per_concept, max_marks)

    try:
        data = json.loads(match.group())
    except (json.JSONDecodeError, ValueError):
        print("  LLM Grading: JSON decode failed. Using keyword fallback.")
        return _keyword_fallback("", key_concepts, mandatory_concepts, marks_per_concept, max_marks)

    found   = [str(c) for c in data.get("concepts_found",   [])]
    missing = [str(c) for c in data.get("concepts_missing", [])]
    mandatory_met = bool(data.get("mandatory_concepts_met", True))

    # Enforce mandatory rule independently (don't trust LLM blindly)
    if mandatory_concepts:
        actual_mandatory_met = any(
            any(m.lower() in f.lower() or f.lower() in m.lower() for f in found)
            for m in mandatory_concepts
        )
        mandatory_met = actual_mandatory_met

    raw_marks = float(data.get("marks_awarded", len(found) * marks_per_concept))
    marks     = 0.0 if (mandatory_concepts and not mandatory_met) else min(raw_marks, max_marks)

    concept_scores_raw = data.get("concept_scores", {})
    concept_scores     = {str(k): float(v) for k, v in concept_scores_raw.items() if str(k) in key_concepts}
    # Fill missing concepts with 0
    for c in key_concepts:
        concept_scores.setdefault(c, marks_per_concept if c in found else 0.0)

    return {
        "concept_scores":         concept_scores,
        "concepts_found":         found,
        "concepts_missing":       missing,
        "mandatory_concepts_met": mandatory_met,
        "marks_awarded":          marks,
        "max_marks":              float(data.get("max_marks", max_marks)),
        "feedback":               str(data.get("feedback", "")),
        "ocr_issues_detected":    bool(data.get("ocr_issues_detected", False)),
    }


# ── Keyword fallback ──────────────────────────────────────────────────────────

def _keyword_fallback(
    student_answer:    str,
    key_concepts:      list,
    mandatory_concepts: list,
    marks_per_concept: float,
    max_marks:         float,
) -> dict:
    """Case-insensitive substring check when Ollama is unavailable or fails."""
    ans_lower = student_answer.lower()
    found     = [c for c in key_concepts if c.lower() in ans_lower]
    missing   = [c for c in key_concepts if c not in found]

    if mandatory_concepts:
        mandatory_met = any(c in found for c in mandatory_concepts)
    else:
        mandatory_met = True

    marks = 0.0 if (mandatory_concepts and not mandatory_met) else min(len(found) * marks_per_concept, max_marks)

    return _build_result(
        key_concepts       = key_concepts,
        found              = found,
        mandatory_concepts = mandatory_concepts,
        marks_per_concept  = marks_per_concept,
        max_marks          = max_marks,
        feedback           = (
            f"Keyword fallback (Ollama unavailable): "
            f"{len(found)}/{len(key_concepts)} concepts matched."
        ),
        ocr_issues         = False,
        marks_override     = marks,
        mandatory_met      = mandatory_met,
    )


# ── Result builder ────────────────────────────────────────────────────────────

def _build_result(
    key_concepts:       list,
    found:              list,
    mandatory_concepts: list,
    marks_per_concept:  float,
    max_marks:          float,
    feedback:           str,
    ocr_issues:         bool = False,
    marks_override:     float | None = None,
    mandatory_met:      bool | None = None,
) -> dict:
    if mandatory_met is None:
        mandatory_met = (
            any(c in found for c in mandatory_concepts)
            if mandatory_concepts else True
        )
    missing = [c for c in key_concepts if c not in found]
    marks   = marks_override if marks_override is not None else (
        0.0 if (mandatory_concepts and not mandatory_met)
        else min(len(found) * marks_per_concept, max_marks)
    )
    concept_scores = {c: (marks_per_concept if c in found else 0.0) for c in key_concepts}
    return {
        "concept_scores":         concept_scores,
        "concepts_found":         found,
        "concepts_missing":       missing,
        "mandatory_concepts_met": mandatory_met,
        "marks_awarded":          marks,
        "max_marks":              max_marks,
        "feedback":               feedback,
        "ocr_issues_detected":    ocr_issues,
    }
