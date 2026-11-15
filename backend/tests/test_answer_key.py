# test_answer_key.py — the optional RAG answer-key assistant: reference files → passages → cited draft
# (reference answer + rubric points) that the teacher edits. Never used to grade students. Fake model, no GPU.

import json

import fitz
import pytest

from app.pipeline import llm
from app.pipeline.llm import Endpoint, Reply
from app.services import answer_key as ak
from tests.conftest import auth_headers

NOTES = ("Photosynthesis happens in the chloroplast. Plants use sunlight, water and carbon dioxide "
         "to make glucose and release oxygen. ") * 3
SOLAR = ("Solar energy is energy that we get from the sun. Examples of solar energy: solar panels make "
         "electricity, solar water heaters heat water. ") * 3


def _pdf(path, pages):
    """A small PDF with one text page per string (a scanned page = empty string)."""
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        if text:
            page.insert_textbox(fitz.Rect(40, 40, 560, 800), text, fontsize=10)
    doc.save(str(path))
    return str(path)


# Why: passages must keep where they came from (file + page) so every draft point can cite its source
def test_load_and_chunk_keep_source_and_page(tmp_path):
    f = _pdf(tmp_path / "notes.pdf", [NOTES, SOLAR])
    passages = ak.chunk(ak.load_reference([f]), words=25)
    assert {p["page"] for p in passages} == {1, 2}
    assert all(p["source"] == "notes.pdf" and p["text"] for p in passages)


# Why: plain-text reference files are accepted too
def test_load_text_file(tmp_path):
    f = tmp_path / "key.txt"
    f.write_text(SOLAR)
    pages = ak.load_reference([str(f)])
    assert pages[0]["source"] == "key.txt" and "solar panels" in pages[0]["text"]


# Why: a scanned page has no text layer; it must be reported, not silently ignored
def test_scanned_page_reported(tmp_path):
    f = _pdf(tmp_path / "scan.pdf", [""])
    pages = ak.load_reference([f])
    assert pages == [] and ak.load_reference.last_skipped == ["scan.pdf p1"]


# Why: retrieval must put the passage about the question first (only top passages reach the model)
def test_retrieve_ranks_relevant_passage_first(tmp_path):
    passages = ak.chunk([{"source": "a.pdf", "page": 1, "text": NOTES}, {"source": "b.pdf", "page": 3, "text": SOLAR}], words=25)
    top = ak.retrieve("What is solar energy? Give an example.", passages, k=2)
    assert top[0]["source"] == "b.pdf"


def fake_model(reply_data, seen):
    """Fake grader-family model that records the prompt it was given."""
    def chat(ep, prompt, images=(), schema=None, **_kw):
        seen.append(prompt)
        return Reply(text=json.dumps(reply_data), data=reply_data, model=ep.name)
    return chat


# Why: the draft gives a reference answer and rubric points, each citing the passages it used; marks are split evenly
def test_draft_with_citations(monkeypatch):
    seen = []
    data = {"covered": True, "model_answer": "Energy from the sun, e.g. solar panels.",
            "points": [{"point": "energy obtained from the sun", "sources": [1]},
                       {"point": "a valid example (solar panels, solar heater)", "sources": [1]}], "note": ""}
    monkeypatch.setattr(llm, "chat", fake_model(data, seen))
    passages = ak.chunk([{"source": "a.pdf", "page": 1, "text": NOTES}, {"source": "b.pdf", "page": 3, "text": SOLAR}], words=25)
    d = ak.draft(Endpoint("qwen", "http://x", {"supports_json_schema": True}), "What is solar energy?", 2, passages, k=2)
    assert d["model_answer"].startswith("Energy from the sun")
    assert d["key_concepts"] == ["energy obtained from the sun", "a valid example (solar panels, solar heater)"]
    assert d["marks_per_concept"] == 1.0
    assert d["citations"][0]["source"] == "b.pdf" and d["citations"][0]["page"] == 3
    assert "Photosynthesis" not in seen[0] or seen[0].index("solar") < seen[0].index("Photosynthesis")


# Why: when the material does not cover the question, the draft says so instead of inventing an answer
def test_draft_not_covered(monkeypatch):
    monkeypatch.setattr(llm, "chat", fake_model({"covered": False, "model_answer": "", "points": [],
                                                 "note": "The material does not discuss this."}, []))
    passages = ak.chunk([{"source": "a.pdf", "page": 1, "text": NOTES}], words=25)
    d = ak.draft(Endpoint("qwen", "http://x", {}), "Define power.", 2, passages)
    assert d["covered"] is False and d["key_concepts"] == [] and "does not discuss" in d["note"]


# Why: the endpoint drafts every question for the teacher only, from files uploaded earlier
@pytest.mark.asyncio
async def test_endpoint(client, teacher_token, student_token, tmp_path, monkeypatch):
    from app.routers import papers
    monkeypatch.setattr(papers, "PAPER_UPLOAD_DIR", str(tmp_path))
    _pdf(tmp_path / "ref1.pdf", [SOLAR])
    monkeypatch.setattr(llm, "resolve", lambda role, exclude=(): Endpoint("qwen", "http://x", {"supports_json_schema": True}))
    monkeypatch.setattr(llm, "chat", fake_model({"covered": True, "model_answer": "Energy from the sun.",
                                                 "points": [{"point": "energy from the sun", "sources": [1]}], "note": ""}, []))
    body = {"reference_urls": ["/api/papers/files/ref1.pdf"], "questions": ["What is solar energy?"], "marks": [2]}
    ok = await client.post("/api/papers/answer-key/draft", json=body, headers=auth_headers(teacher_token))
    assert ok.status_code == 200, ok.text
    d = ok.json()["drafts"][0]
    assert d["question"] == "What is solar energy?" and d["key_concepts"] == ["energy from the sun"]
    assert d["marks_per_concept"] == 2.0 and d["citations"][0]["source"] == "ref1.pdf"
    assert (await client.post("/api/papers/answer-key/draft", json=body, headers=auth_headers(student_token))).status_code == 403
    missing = {**body, "reference_urls": ["/api/papers/files/nope.pdf"]}
    assert (await client.post("/api/papers/answer-key/draft", json=missing, headers=auth_headers(teacher_token))).status_code == 404


# Why: without a live model the teacher gets a clear "not available" instead of a crash
@pytest.mark.asyncio
async def test_endpoint_without_model(client, teacher_token, tmp_path, monkeypatch):
    from app.routers import papers
    monkeypatch.setattr(papers, "PAPER_UPLOAD_DIR", str(tmp_path))
    _pdf(tmp_path / "ref1.pdf", [SOLAR])
    monkeypatch.setattr(llm, "resolve", lambda role, exclude=(): None)
    body = {"reference_urls": ["/api/papers/files/ref1.pdf"], "questions": ["What is solar energy?"], "marks": [2]}
    resp = await client.post("/api/papers/answer-key/draft", json=body, headers=auth_headers(teacher_token))
    assert resp.status_code == 503


# Why: a citation must show the sentence the point came from, not just the start of a long passage
def test_citation_shows_matching_sentence(monkeypatch):
    text = ("Semi-structured data has markers but no grid. Photosynthesis needs sunlight. "
            "K-NN is distance-based, so features with larger scales dominate the distance unless normalised. "
            "Overfitting means memorising the training data.")
    monkeypatch.setattr(llm, "chat", fake_model({"covered": True, "model_answer": "K-NN uses distances.",
        "points": [{"point": "features with larger scales dominate the distance", "sources": [1]}], "note": ""}, []))
    d = ak.draft(Endpoint("qwen", "http://x", {}), "Why normalise data for K-NN?", 2,
                 ak.chunk([{"source": "key.txt", "page": 1, "text": text}], words=200))
    assert d["citations"][0]["text"].startswith("K-NN is distance-based")
