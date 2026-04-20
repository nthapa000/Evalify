# pdf_extractor.py — Extract MCQ answers from PDF files using pdfplumber + regex.
# Falls back gracefully when pdfplumber is not installed.

import re
from typing import Dict, Tuple

try:
    import pdfplumber
    _PDFPLUMBER = True
except ImportError:
    _PDFPLUMBER = False


def extract_mcq_answers_from_pdf(
    pdf_path: str,
    mcq_count: int = 0,
) -> Tuple[Dict[str, str], float, str]:
    """
    Open a PDF, concatenate all page text, then regex-match MCQ answers.
    Returns (answers_dict, confidence, raw_text).
    confidence = fraction of expected questions found (0.0 if pdfplumber missing).
    """
    if not _PDFPLUMBER:
        return {}, 0.0, ""

    raw_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                raw_text += (page.extract_text() or "") + "\n"
    except Exception:
        return {}, 0.0, raw_text

    answers = _parse_answers(raw_text, mcq_count)
    confidence = len(answers) / mcq_count if mcq_count > 0 else 0.0
    return answers, min(confidence, 1.0), raw_text


def _parse_answers(text: str, mcq_count: int = 0) -> Dict[str, str]:
    """
    Match lines like:  1. A  |  Q2: B  |  3) C  |  Q4 D  |  4. d
    Returns { "Q1": "A", "Q2": "B", ... }.
    """
    pattern = re.compile(r"[Qq]?(\d+)\s*[.\s:)]\s*([A-Da-d])\b")
    answers: Dict[str, str] = {}
    for match in pattern.finditer(text):
        q_num = int(match.group(1))
        if mcq_count == 0 or q_num <= mcq_count:
            answers[f"Q{q_num}"] = match.group(2).upper()
    return answers
