# rubric_extractor.py — turn two teacher PDFs into per-question rubrics (no LLM).
#
# Detailed-answer PDF → question text + model answer per question.
# Grade-rubric PDF    → bullet-point concepts, mandatory flags, marks per concept.

from __future__ import annotations

import os
import re
from collections import Counter
from typing import Tuple

from app.prompts.prompt_subjective_grading import build_grading_prompt_template
from app.services.pdf_utils import pdf_extract_text

# Section headers: "Q1.", "S2)", "3:", "Question 4 -"
_SECTION_RE = re.compile(r"(?:^|\n)\s*(?:(?:Q|S|Question|Ques\.?)\s*)?(\d+)\s*[.):\-]", re.I | re.M)
# Leading label on a question line
_LABEL_RE = re.compile(r"^(?:Q\d+|S\d+|Question\s*\d+|Ques\.?\s*\d+)[.):\s]*", re.I)
# "(2 marks)", MANDATORY-style words, and bullet markers inside rubric lines
_MARKS_RE = re.compile(r"\((\d+(?:\.\d+)?)\s*marks?\)", re.I)
_MANDATORY_RE = re.compile(r"\b(mandatory|compulsory|must\s*mention|essential|required)\b", re.I)
_BULLET_RE = re.compile(r"^[•\-\*✓✗→▶◆]\s*|^\d+[.)]\s+")


def _split_by_question(text: str, count: int) -> dict:
    """Split text into {question_number: section_text} for numbers 1..count."""
    hits = [(int(m.group(1)), m.start(), m.end()) for m in _SECTION_RE.finditer(text)]
    hits = [h for h in hits if 1 <= h[0] <= count]
    if not hits:
        return {1: text.strip()} if count == 1 and text.strip() else {}
    # Each section runs from the end of its header to the start of the next
    return {num: text[end:(hits[i + 1][1] if i + 1 < len(hits) else len(text))].strip()
            for i, (num, _, end) in enumerate(hits)}


def _question_and_answer(section: str, n: int) -> Tuple[str, str]:
    """First line is the question (if short or ends with '?'); the rest is the model answer."""
    lines = [l.strip() for l in section.split("\n") if l.strip()]
    if not lines:
        return f"Question {n}", ""
    first = _LABEL_RE.sub("", lines[0]).strip()
    if len(lines) > 1 and (first.endswith("?") or len(first) <= 200):
        return first or f"Question {n}", "\n".join(lines[1:])
    return f"Question {n}", "\n".join(lines)


def _concepts(section: str) -> Tuple[list, list, float]:
    """Rubric section → (key_concepts, mandatory_concepts, marks_per_concept)."""
    concepts, mandatory, marks = [], [], []
    for line in (l.strip() for l in section.split("\n")):
        # Skip blanks and short "Heading:" lines
        if not line or (line.endswith(":") and len(line) < 60):
            continue
        if m := _MARKS_RE.search(line):
            marks.append(float(m.group(1)))
        # Strip bullets, marks and MANDATORY words to get the concept text
        concept = _MANDATORY_RE.sub("", _MARKS_RE.sub("", _BULLET_RE.sub("", line)))
        concept = re.sub(r"\s*[-–—]\s*$", "", concept).strip(".,;: ")
        if 3 < len(concept) < 150 and concept not in concepts:
            concepts.append(concept)
            if _MANDATORY_RE.search(line):
                mandatory.append(concept)
    # The most common "(N marks)" value is the marks per concept
    return concepts, mandatory, (Counter(marks).most_common(1)[0][0] if marks else 1.0)


def _read(path: str, label: str, warnings: list) -> str:
    """Text of a PDF, adding a warning if it is missing or image-only."""
    if not path or not os.path.exists(path):
        warnings.append(f"{label} PDF not found.")
        return ""
    text = pdf_extract_text(path)
    if not text.strip():
        warnings.append(f"{label} PDF has no extractable text (may be scanned image).")
    return text


def extract_rubric_from_pdfs(detailed_answer_path: str, grade_rubric_path: str,
                             subjective_count: int) -> Tuple[list, list, list, str]:
    """Return (questions, rubrics, prompt_templates, warning) for S1..S{subjective_count}."""
    warnings: list = []
    detailed = _split_by_question(_read(detailed_answer_path, "Detailed Answer", warnings), subjective_count)
    rubric = _split_by_question(_read(grade_rubric_path, "Grade Rubric", warnings), subjective_count)

    questions, rubrics, templates = [], [], []
    for i in range(1, subjective_count + 1):
        # Pair question i's model answer with its rubric concepts
        q_text, model_answer = _question_and_answer(detailed.get(i, ""), i)
        concepts, mandatory, per = _concepts(rubric.get(i, ""))
        questions.append(q_text)
        rubrics.append({"key_concepts": concepts, "mandatory_concepts": mandatory,
                        "marks_per_concept": per, "model_answer": model_answer})
        templates.append(build_grading_prompt_template(
            question_text=q_text, key_concepts=concepts, mandatory_concepts=mandatory,
            marks_per_concept=per, model_answer=model_answer))

    if not any(r["key_concepts"] for r in rubrics):
        warnings.append("No rubric concepts extracted — check that the Grade Rubric PDF has "
                        "bullet-point lines per question.")
    return questions, rubrics, templates, " ".join(warnings)
