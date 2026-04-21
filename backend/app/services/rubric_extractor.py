# rubric_extractor.py — Extracts structured rubric data from teacher-uploaded PDFs.
#
# Flow (no LLM — pure text parsing):
#   1. Extract text from both PDFs (PyMuPDF).
#   2. Split text into per-question sections by number markers (Q1/S1/1. etc.).
#   3. Parse model answers from the detailed-answer PDF.
#   4. Parse key concepts, mandatory flags, marks from the rubric PDF.
#   5. Build a grading prompt template per question (<<<STUDENT_ANSWER>>> placeholder).
#
# Returns: (subjective_questions, subjective_rubrics, subjective_prompt_templates, warning)

from __future__ import annotations
import re
import os
from collections import Counter
from typing import Tuple

from app.services.pdf_utils import pdf_extract_text
from app.prompts.prompt_subjective_grading import build_grading_prompt_template


# ── Section splitter ──────────────────────────────────────────────────────────

# Matches lines like: Q1, S1, 1., 1), 1:, Question 1, Ques. 1
_SECTION_RE = re.compile(
    r'(?:^|\n)\s*(?:(?:Q|S|Question|Ques\.?)\s*)?(\d+)\s*[.):\-]',
    re.IGNORECASE | re.MULTILINE,
)


def _split_by_question(text: str, count: int) -> dict:
    """
    Split text into {1: section_text, 2: section_text, ...}.
    Falls back to {1: full_text} when count==1 and no headers found.
    """
    if not text.strip():
        return {}

    matches = [(int(m.group(1)), m.start(), m.end()) for m in _SECTION_RE.finditer(text)]
    # Keep only question numbers in expected range
    relevant = [(num, s, e) for num, s, e in matches if 1 <= num <= count]

    if not relevant:
        return {1: text.strip()} if count == 1 else {}

    sections: dict = {}
    for idx, (num, _, content_start) in enumerate(relevant):
        content_end = relevant[idx + 1][1] if idx + 1 < len(relevant) else len(text)
        sections[num] = text[content_start:content_end].strip()

    return sections


# ── Model answer parser ───────────────────────────────────────────────────────

_QUESTION_MARKER_RE = re.compile(
    r'^(?:Q\d+|S\d+|Question\s*\d+|Ques\.?\s*\d+)[.):\s]*',
    re.IGNORECASE,
)


def _extract_question_and_answer(section_text: str, question_num: int) -> tuple[str, str]:
    """
    Heuristic: if the first non-empty line looks like a question (ends with '?' or
    is a short heading), treat it as question_text and the rest as model_answer.
    """
    lines = [l.strip() for l in section_text.split('\n') if l.strip()]
    if not lines:
        return f"Question {question_num}", ""

    first = lines[0]
    # Strip leading Q1:/S1: markers from the first line
    cleaned_first = _QUESTION_MARKER_RE.sub('', first).strip()

    # Treat as question line if it ends with '?' or is short (≤ 200 chars)
    if (cleaned_first.endswith('?') or len(cleaned_first) <= 200) and len(lines) > 1:
        question_text = cleaned_first or f"Question {question_num}"
        model_answer  = '\n'.join(lines[1:])
    else:
        question_text = f"Question {question_num}"
        model_answer  = '\n'.join(lines)

    return question_text, model_answer.strip()


# ── Rubric concept parser ─────────────────────────────────────────────────────

_MARKS_RE     = re.compile(r'\((\d+(?:\.\d+)?)\s*marks?\)', re.IGNORECASE)
_MANDATORY_RE = re.compile(
    r'\b(mandatory|compulsory|must\s*mention|essential|required)\b',
    re.IGNORECASE,
)
_BULLET_RE    = re.compile(r'^[•\-\*✓✗→▶◆]\s*|^\d+[.)]\s+')


def _extract_concepts(rubric_section: str) -> tuple[list, list, float]:
    """
    Parse a rubric section into (key_concepts, mandatory_concepts, marks_per_concept).
    Looks for bullet-point lines; extracts mark values and MANDATORY flags.
    """
    if not rubric_section.strip():
        return [], [], 1.0

    key_concepts:       list  = []
    mandatory_concepts: list  = []
    marks_values:       list  = []

    for line in rubric_section.split('\n'):
        line = line.strip()
        if not line:
            continue

        # Skip section-header lines (short, ends with colon)
        if line.endswith(':') and len(line) < 60:
            continue

        # Extract mark value if present
        marks_match = _MARKS_RE.search(line)
        if marks_match:
            marks_values.append(float(marks_match.group(1)))

        is_mandatory = bool(_MANDATORY_RE.search(line))

        # Clean the concept text
        concept = _BULLET_RE.sub('', line)
        concept = _MARKS_RE.sub('', concept)
        concept = _MANDATORY_RE.sub('', concept)
        concept = re.sub(r'\s*[-–—]\s*$', '', concept)
        concept = concept.strip('.,;: ')

        if concept and 3 < len(concept) < 150 and concept not in key_concepts:
            key_concepts.append(concept)
            if is_mandatory:
                mandatory_concepts.append(concept)

    marks_per_concept = Counter(marks_values).most_common(1)[0][0] if marks_values else 1.0
    return key_concepts, mandatory_concepts, marks_per_concept


# ── Public entry-point ────────────────────────────────────────────────────────

def extract_rubric_from_pdfs(
    detailed_answer_path: str,
    grade_rubric_path:    str,
    subjective_count:     int,
) -> Tuple[list, list, list, str]:
    """
    Parse two teacher PDFs into per-question rubric data using text extraction only.

    Returns:
        subjective_questions       — list[str]   (len == subjective_count)
        subjective_rubrics         — list[dict]  (len == subjective_count)
        subjective_prompt_templates — list[str]  (len == subjective_count, <<<STUDENT_ANSWER>>> placeholder)
        warning                    — str
    """
    warnings: list = []

    # ── Extract text ──────────────────────────────────────────────────────────
    detailed_text = ""
    rubric_text   = ""

    if detailed_answer_path and os.path.exists(detailed_answer_path):
        detailed_text = pdf_extract_text(detailed_answer_path)
        if not detailed_text.strip():
            warnings.append("Detailed Answer PDF has no extractable text (may be scanned image).")
    else:
        warnings.append("Detailed Answer PDF not found.")

    if grade_rubric_path and os.path.exists(grade_rubric_path):
        rubric_text = pdf_extract_text(grade_rubric_path)
        if not rubric_text.strip():
            warnings.append("Grade Rubric PDF has no extractable text (may be scanned image).")
    else:
        warnings.append("Grade Rubric PDF not found.")

    # ── Split by question sections ────────────────────────────────────────────
    detailed_sections = _split_by_question(detailed_text, subjective_count)
    rubric_sections   = _split_by_question(rubric_text,   subjective_count)

    subjective_questions:        list = []
    subjective_rubrics:          list = []
    subjective_prompt_templates: list = []

    for i in range(1, subjective_count + 1):
        det_section = detailed_sections.get(i, "").strip()
        rub_section = rubric_sections.get(i, "").strip()

        question_text, model_answer = _extract_question_and_answer(det_section, i)
        key_concepts, mandatory_concepts, marks_per_concept = _extract_concepts(rub_section)

        rubric = {
            "key_concepts":       key_concepts,
            "mandatory_concepts": mandatory_concepts,
            "marks_per_concept":  marks_per_concept,
            "model_answer":       model_answer,
        }

        template = build_grading_prompt_template(
            question_text      = question_text,
            key_concepts       = key_concepts,
            mandatory_concepts = mandatory_concepts,
            marks_per_concept  = marks_per_concept,
            model_answer       = model_answer,
        )

        subjective_questions.append(question_text)
        subjective_rubrics.append(rubric)
        subjective_prompt_templates.append(template)

        print(f"  Rubric Q{i}: '{question_text[:60]}' | "
              f"{len(key_concepts)} concepts | {len(mandatory_concepts)} mandatory | "
              f"{marks_per_concept} marks/concept")

    total_concepts = sum(len(r["key_concepts"]) for r in subjective_rubrics)
    if total_concepts == 0:
        warnings.append(
            "No rubric concepts extracted — check that the Grade Rubric PDF has "
            "bullet-point lines per question."
        )

    return subjective_questions, subjective_rubrics, subjective_prompt_templates, " ".join(warnings)
