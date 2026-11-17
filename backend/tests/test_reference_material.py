# test_reference_material.py — the reference material in the upload kit (uploads/Pattern3/Teacher/reference_material)
# must work with the answer-key assistant: readable text, the right passage found for every written question.

import re
from pathlib import Path

import pytest

from app.services import answer_key as ak

KIT = Path(__file__).resolve().parents[2] / "uploads" / "Pattern3" / "Teacher"
REF = KIT / "reference_material"
TEXT_FILES = ["lecture_notes_part1_data_basics.pdf", "lecture_notes_part2_models.pdf", "revision_sheet.txt"]

# The 15 written questions (Q21-Q35) and a word the best passages must contain
TOPIC = ["supervised", "overfitting", "regression", "challenges", "applications", "semi-structured", "outliers",
         "pre-processing", "normalization", "discretiz", "k-means", "hyperparameter", "gradient descent", "margin", "rbf"]


def _questions():
    """The paper's written questions, from the kit's answer notes."""
    text = (KIT / "reference_notes.txt").read_text()
    return re.findall(r"^Question \d+: (.+)$", text, flags=re.M)


# Why: the teacher uploads these files in the wizard; they must be present and the PDFs must have a text layer
def test_files_exist_and_pdfs_have_text():
    pages = ak.load_reference([str(REF / f) for f in TEXT_FILES])
    assert {p["source"] for p in pages} == set(TEXT_FILES) and not ak.load_reference.last_skipped
    assert sum(len(p["text"].split()) for p in pages) > 1500


# Why: the scanned page is there to test the "no text layer" message, so it must really be skipped and reported
def test_scanned_page_is_reported_as_skipped():
    pages = ak.load_reference([str(REF / "scanned_notes_page.pdf")])
    assert pages == [] and ak.load_reference.last_skipped == ["scanned_notes_page.pdf p1"]


# Why: for every written question the assistant's search must put a passage on that topic in its top 3
@pytest.mark.parametrize("i", range(15))
def test_search_finds_the_topic_for_each_question(i):
    q = _questions()[i]
    passages = ak.chunk(ak.load_reference([str(REF / f) for f in TEXT_FILES]))
    top = ak.retrieve(q, passages, k=3)
    assert any(TOPIC[i] in p["text"].lower() for p in top), f"{q!r}: no {TOPIC[i]!r} passage in the top 3"


# Why: the teacher pastes these questions into the assistant, so the list must match the paper's 15 questions
def test_questions_file_matches_the_paper():
    lines = [l for l in (REF / "questions_for_assistant.txt").read_text().splitlines() if l.strip()]
    assert [re.sub(r"^S\d+\. ", "", l) for l in lines[-15:]] == _questions()
