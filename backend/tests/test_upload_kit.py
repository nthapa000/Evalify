# test_upload_kit.py — the files in uploads/ (manual test kit) must work in the app as the READMEs promise.
# Skipped when the kit has not been built (python eval/make_upload_kit.py).

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "uploads"
DATA = ROOT / "eval" / "data"
pytestmark = pytest.mark.skipif(not (KIT / "README.md").exists(), reason="upload kit not built")

KEYS = [("Pattern1/Teacher/OMR/answer_key.pdf", "own_omr/papers/omr_basic_science.json"),
        ("Pattern1/Teacher/Handwritten/answer_key.pdf", "own_mcq/papers/mcq_basic_science.json"),
        ("Pattern2/Teacher/Paper_2A/answer_key.pdf", "own_mcqnum/papers/paper_2A.json"),
        ("Pattern2/Teacher/Paper_2B/answer_key.pdf", "own_mcqnum/papers/paper_2B.json"),
        ("Pattern2/Teacher/Paper_2C/answer_key.pdf", "own_mcqnum/papers/paper_2C.json"),
        ("Pattern3/Teacher/answer_key_mcq.pdf", "mendeley/papers/ds_exam.json")]


# Why: "Extract Answers from PDF" on each kit key must give exactly the paper's MCQ key, multi-answer keys included
@pytest.mark.parametrize("pdf,paper", KEYS)
def test_answer_key_pdfs_extract_exactly(pdf, paper):
    from app.services.pdf_utils import extract_mcq_answers_from_pdf
    key = json.loads((DATA / paper).read_text())
    answers, confidence, _ = extract_mcq_answers_from_pdf(str(KIT / pdf), int(key["mcqCount"]))
    assert answers == key["mcqAnswers"] and confidence == 1.0


# Why: "Extract Rubric from PDFs" on the kit's two PDFs must rebuild all 15 Data Science questions and rubric points
def test_rubric_pdfs_extract_all_questions():
    from app.services.rubric_extractor import extract_rubric_from_pdfs
    paper = json.loads((DATA / "mendeley/papers/ds_exam.json").read_text())
    t = KIT / "Pattern3/Teacher"
    questions, rubrics, _, warning = extract_rubric_from_pdfs(str(t / "detailed_answer.pdf"), str(t / "grade_rubric.pdf"), 15)
    assert warning == ""
    assert questions == paper["subjectiveQuestions"]
    assert [r["key_concepts"] for r in rubrics] == [r["key_concepts"] for r in paper["subjectiveRubrics"]]
    assert all(r["marks_per_concept"] == 1 for r in rubrics)


# Why: every student folder must hold at least one page the upload page accepts (PNG / JPG only)
def test_every_student_folder_has_uploadable_pages():
    folders = [d for d in KIT.glob("Pattern*/Student/**/*2025*") if d.is_dir()]
    assert len(folders) == 15 + 15 + 15 + 6
    for d in folders:
        pages = list(d.iterdir())
        assert pages and all(p.suffix in (".jpg", ".jpeg", ".png") for p in pages), d


# Why: the Data Science scans were re-saved as JPEG for the kit; they must still pass the quality gate
def test_converted_scans_pass_quality_gate():
    from app.pipeline import quality
    for p in sorted(KIT.glob("Pattern3/Student/*/*_page1.jpg")):
        _, rep = quality.prepare(str(p))
        assert rep.ok and not rep.blank, (p, rep)
