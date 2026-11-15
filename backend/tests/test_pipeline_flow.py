# test_pipeline_flow.py — end-to-end run of the v2 pipeline with fake model replies (no GPU, no MongoDB).
#
# Type-C paper: Q1–Q2 MCQ, Q3 numerical (id N1), Q4–Q5 subjective (ids S1, S2), continuous numbering.
#   Q1  readers agree "B"                 → accepted, correct
#   Q2  A says "A", B says "C", C says "C" → majority "C", wrong, no TA
#   Q3  "2500 m" vs "2500"                → numbers agree, correct (unit ignored)
#   Q4  both transcripts found            → graded by the grader (1 present + 1 partial = 1.5)
#   Q5  not written anywhere               → sent to a TA, reason "answer not found on the page"

import json

import pytest
from PIL import Image

from app.pipeline import llm, orchestrator, quality
from app.pipeline.llm import Endpoint, Reply

PAPER = {
    "type": "mcq_numerical_subjective", "numbering": "continuous", "subject": "Physics",
    "mcqCount": 2, "mcqMarks": 1, "mcqAnswers": {"Q1": "B", "Q2": "A"},
    "numericalCount": 1, "numericalMarks": 2,
    "numericalAnswers": {"N1": {"answer": "2500", "unit": "m", "tolerance": 0.001, "tolerance_type": "abs"}},
    "subjectiveCount": 2, "subjectiveMarks": 2, "subjectiveQuestionMarks": {"S1": 2, "S2": 2},
    "subjectiveQuestions": ["What is solar energy?", "Define power."],
    "subjectiveRubrics": [
        {"key_concepts": ["energy derived from the sun", "an example of solar energy"], "marks_per_concept": 1,
         "model_answer": "Energy from the sun, e.g. solar panels."},
        {"key_concepts": ["rate of doing work", "unit watt"], "marks_per_concept": 1, "model_answer": "P = W/t"}],
}

ROLES = {"page_reader_a": "gemma", "page_reader_b": "qwen", "page_reader_c": "glm",
         "transcriber_a": "qwen", "transcriber_b": "gemma", "grader": "gemma"}
# Same prompt styles as infra/models.yaml: VLMs answer JSON, GLM-OCR gets its own OCR prompt
SPECS = {"gemma": {"supports_json_schema": True}, "qwen": {"supports_json_schema": True},
         "glm": {"prompt_style": "glm_ocr"}}


def fake_chat(ep, prompt, images=(), schema=None, **_kw):
    """Answer like each model would, keyed on the prompt."""
    if "Questions on this sheet" in prompt:                       # page_prompt (JSON)
        q2 = "A" if ep.name == "gemma" else "C"
        q3 = "2500 m" if ep.name == "gemma" else "2500"
        data = {"answers": [{"label": "Q1", "status": "answered", "value": "B"},
                            {"label": "Q2", "status": "answered", "value": q2},
                            {"label": "Q3", "status": "answered", "value": q3}]}
        return Reply(text=json.dumps(data), data=data, model=ep.name, latency_s=1.0)
    if prompt.startswith("Text Recognition"):                     # GLM-OCR page text
        return Reply(text="1. B\n2. C\n3. 2500 m", model=ep.name, latency_s=0.5)
    if "[[Q27]]" in prompt:                                       # page_text_plain_prompt (Gemma)
        return Reply(text="[[Q1]] B\n[[Q4]] solar energy is energy we get from the sun", model=ep.name)
    if "Transcribe every answer on this page" in prompt:          # page_text_prompt (Qwen, JSON)
        data = {"answers": [{"label": "Q1", "text": "B", "fully_crossed_out": False},
                            {"label": "Q4", "text": "solar energy is energy we get from the sun",
                             "fully_crossed_out": False}]}
        return Reply(text=json.dumps(data), data=data, model=ep.name)
    if "Rubric points" in prompt:                                 # grader prompt v2
        data = {"concepts": [
            {"concept": "energy derived from the sun", "evidence": "energy we get from the sun",
             "verdict": "present", "confidence": 0.95},
            {"concept": "an example of solar energy", "evidence": "solar energy is energy",
             "verdict": "partial", "confidence": 0.9}], "transcript_problem": False}
        return Reply(text=json.dumps(data), data=data, model=ep.name, latency_s=2.0)
    raise AssertionError(f"unexpected prompt for {ep.name}: {prompt[:80]}")


@pytest.fixture
def pipeline(monkeypatch, tmp_path):
    """Fake endpoints + model replies; quality gate always passes; two blank page files."""
    monkeypatch.setattr(llm, "resolve", lambda role, exclude=(): (
        Endpoint(ROLES[role], f"http://fake/{ROLES[role]}", SPECS[ROLES[role]])
        if role in ROLES and ROLES[role] not in exclude else None))
    monkeypatch.setattr(llm, "chat", fake_chat)
    monkeypatch.setattr(quality, "prepare", lambda path, out_path=None: (
        Image.new("RGB", (100, 140), "white"), quality.QualityReport(ok=True)))
    files = []
    for i in range(2):
        f = tmp_path / f"p{i}.png"
        Image.new("RGB", (100, 140), "white").save(f)
        files.append(str(f))
    return files


def run(files, paper=PAPER):
    return orchestrator.run(paper, files, "handwritten")


def rows(out):
    return {d["question"]: d for d in out["mcq_detail"] + out["numerical_detail"] + out["subjective_detail"]}


def test_mcq_majority_and_scores(pipeline):
    d = rows(run(pipeline))
    assert d["Q1"]["status"] == "correct" and not d["Q1"]["needs_review"]
    assert d["Q2"]["student_answer"] == "C" and d["Q2"]["status"] == "wrong"
    assert not d["Q2"]["needs_review"]                  # 2 of 3 readers agree → no TA


def test_numerical_unit_ignored(pipeline):
    d = rows(run(pipeline))
    assert d["N1"]["status"] == "correct" and d["N1"]["marks_earned"] == 2


def test_subjective_graded_with_half_credit(pipeline):
    d = rows(run(pipeline))
    assert d["S1"]["marks_earned"] == pytest.approx(1.5)
    assert d["S1"]["rubric_marks"] == pytest.approx(1.5)
    assert [c["partial"] for c in d["S1"]["concepts"]] == [False, True]


def test_answer_not_found_goes_to_ta_with_one_reason(pipeline):
    out = run(pipeline)
    d = rows(out)
    assert d["S2"]["needs_review"] and d["S2"]["review_reason"] == "answer not found on the page"
    flagged = {r["question"]: r for r in out["review"]}
    assert set(flagged) == {"S2"} and flagged["S2"]["reason"] == "answer not found on the page"


def test_teacher_calibration_applied_and_rubric_mark_kept(pipeline):
    paper = {**PAPER, "calibration": {"global": 0.5, "per_question": {"S1": 0.5}}}
    d = rows(run(pipeline, paper))
    assert d["S1"]["rubric_marks"] == pytest.approx(1.5)
    assert d["S1"]["calibrated_marks"] == pytest.approx(2.0)
    assert d["S1"]["marks_earned"] == pytest.approx(2.0)


def test_disagreement_without_majority_flags_with_reason(pipeline, monkeypatch):
    def chat(ep, prompt, images=(), schema=None, **kw):
        if prompt.startswith("Text Recognition"):
            return Reply(text="1. B\n2. D\n3. 2500 m", model=ep.name)      # third reader: D
        return fake_chat(ep, prompt, images, schema, **kw)
    monkeypatch.setattr(llm, "chat", chat)
    d = rows(run(pipeline))
    assert d["Q2"]["needs_review"] and "readers disagree" in d["Q2"]["review_reason"]
