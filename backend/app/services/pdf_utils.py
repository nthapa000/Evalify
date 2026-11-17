# pdf_utils.py — PDF helpers (PyMuPDF): render a page, read the text layer, parse MCQ keys.

from __future__ import annotations

import re
from typing import Dict, Tuple

import fitz  # PyMuPDF


def is_pdf(path: str) -> bool:
    """True if the file name ends in .pdf."""
    return path.lower().endswith(".pdf")


def pdf_to_image(pdf_path: str, page_index: int = 0, dpi: int = 200) -> str:
    """Render one PDF page to a PNG next to the PDF and return its path."""
    with fitz.open(pdf_path) as doc:
        page = doc[page_index if page_index < len(doc) else 0]
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False)
        out = pdf_path.rsplit(".", 1)[0] + f"_p{page_index}.png"
        pix.save(out)
    return out


def pdf_extract_text(pdf_path: str) -> str:
    """Text layer of every page joined; empty for scanned (image-only) PDFs."""
    with fitz.open(pdf_path) as doc:
        return "\n".join(page.get_text() for page in doc).strip()


def count_questions(text: str) -> int:
    """Number of questions in a question paper's text: the longest run 1, 2, 3 ... of numbers that start a line
    ("1.", "2)", "Q3", "Question 4:"). Page numbers, marks and stray numbers do not break or add to the run."""
    expected = 1
    for line in text.splitlines():
        m = re.match(r"\s*(?:Q(?:uestion)?\.?\s*)?(\d{1,3})\s*[.):\-]", line, flags=re.I)
        if m and int(m.group(1)) == expected:
            expected += 1
    return expected - 1


def parse_mcq_text(text: str, mcq_count: int = 0) -> Dict[str, str]:
    """Parse lines like '1. A', 'Q2: B', '3) c', '4. A, C' into {'Q1': 'A', ..., 'Q4': 'A,C'}."""
    answers = {}
    # Line by line so an answer never runs into the next question; several letters = several correct options
    for line in text.splitlines():
        for m in re.finditer(r"[Qq]?(\d+)[ \t]*[.\s:)][ \t]*([A-Da-d](?:[ \t]*[,&/]?[ \t]*[A-Da-d]\b)*)\b", line):
            if mcq_count == 0 or int(m.group(1)) <= mcq_count:
                answers[f"Q{int(m.group(1))}"] = ",".join(sorted(set(re.findall(r"[A-D]", m.group(2).upper()))))
    return answers


def extract_mcq_answers_from_pdf(pdf_path: str, mcq_count: int = 0) -> Tuple[Dict[str, str], float, str]:
    """Answer-key PDF → (answers, fraction of questions found, raw text)."""
    try:
        text = pdf_extract_text(pdf_path)
    except Exception:
        return {}, 0.0, ""
    answers = parse_mcq_text(text, mcq_count)
    return answers, (min(len(answers) / mcq_count, 1.0) if mcq_count else 0.0), text
