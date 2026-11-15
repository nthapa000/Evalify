# answer_key.py — optional RAG answer-key assistant (V2 plan §6).
#
# The teacher uploads reference material (notes, textbook pages, a model solution). For each subjective question:
# split the material into passages (file + page kept), retrieve the most relevant ones with BM25 (keyword ranking,
# no extra model), and ask a language model to draft a reference answer and rubric points that cite the passages.
# The teacher edits and approves the draft; it is never used to grade students.

from __future__ import annotations

import math
import os
import re
from collections import Counter
from typing import List

from app.pipeline import llm
from app.prompts import prompt_pipeline as P

_WORD = re.compile(r"[a-z0-9]+")
STOP = set("a an and are as at be by for from has have in is it its of on or that the this to was were what which "
           "with give define explain describe why how".split())


def _tokens(text: str) -> List[str]:
    """Lower-case content words."""
    return [w for w in _WORD.findall(text.lower()) if w not in STOP]


def load_reference(paths: List[str]) -> List[dict]:
    """Reference files → [{"source", "page", "text"}]; PDF pages without a text layer (scans) are listed in
    load_reference.last_skipped so the teacher is told."""
    import fitz
    out, skipped = [], []
    for path in paths:
        name = os.path.basename(path)
        if path.lower().endswith(".pdf"):
            with fitz.open(path) as doc:
                for i, page in enumerate(doc, 1):
                    text = page.get_text().strip()
                    if text:
                        out.append({"source": name, "page": i, "text": text})
                    else:
                        skipped.append(f"{name} p{i}")
        else:
            out.append({"source": name, "page": 1, "text": open(path, encoding="utf-8", errors="ignore").read()})
    load_reference.last_skipped = skipped
    return out


load_reference.last_skipped = []


def chunk(pages: List[dict], words: int = 120, overlap: int = 30) -> List[dict]:
    """Pages → passages of about `words` words (overlapping), each keeping its file and page; ids from 1."""
    out = []
    for p in pages:
        w = p["text"].split()
        step = max(1, words - overlap)
        for start in range(0, max(1, len(w)), step):
            piece = " ".join(w[start:start + words]).strip()
            if piece:
                out.append({"id": len(out) + 1, "source": p["source"], "page": p["page"], "text": piece})
            if start + words >= len(w):
                break
    return out


def retrieve(query: str, passages: List[dict], k: int = 5, k1: float = 1.5, b: float = 0.75) -> List[dict]:
    """BM25 ranking of passages for a question; the k best (in score order)."""
    docs = [_tokens(p["text"]) for p in passages]
    if not docs:
        return []
    avg = sum(map(len, docs)) / len(docs)
    df = Counter(t for d in docs for t in set(d))
    n = len(docs)
    q = _tokens(query)

    def score(d):
        tf = Counter(d)
        return sum(math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5)) * tf[t] * (k1 + 1) /
                   (tf[t] + k1 * (1 - b + b * len(d) / avg)) for t in q if t in tf)

    ranked = sorted(range(n), key=lambda i: score(docs[i]), reverse=True)
    return [passages[i] for i in ranked[:k] if score(docs[i]) > 0] or [passages[i] for i in ranked[:1]]


def best_sentences(text: str, about: str, n: int = 2) -> str:
    """The n sentences of a passage that share most words with `about` (kept in passage order)."""
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]
    want = set(_tokens(about))
    overlap = [len(want & set(_tokens(s))) for s in sents]
    # Only sentences that share words with the points; best first, then shown in passage order
    ranked = [i for i in sorted(range(len(sents)), key=lambda i: overlap[i], reverse=True)[:n] if overlap[i] > 0]
    return " ".join(sents[i] for i in sorted(ranked)) or text[:300]


def draft(ep, question: str, marks: float, passages: List[dict], k: int = 5) -> dict:
    """One question → {"covered", "model_answer", "key_concepts", "marks_per_concept", "citations", "note"}."""
    top = retrieve(question, passages, k=k)
    # Passages are renumbered 1..k for the model; citations map back to file + page
    numbered = [{**p, "n": i + 1} for i, p in enumerate(top)]
    r = llm.chat(ep, P.answer_key_prompt(question, marks, numbered), schema=P.ANSWER_KEY_SCHEMA, max_tokens=2048)
    data = r.data or {}
    points = [p for p in data.get("points", []) if str(p.get("point", "")).strip()]
    used = sorted({s for p in points for s in p.get("sources", []) if isinstance(s, int) and 1 <= s <= len(numbered)})
    return {
        "covered": bool(data.get("covered", bool(points))),
        "model_answer": str(data.get("model_answer", "")).strip(),
        "key_concepts": [str(p["point"]).strip() for p in points],
        "marks_per_concept": round(float(marks) / len(points), 2) if points else float(marks),
        # Each citation shows the passage's sentences closest to the points that cite it
        "citations": [{"n": n, "source": numbered[n - 1]["source"], "page": numbered[n - 1]["page"],
                       "text": best_sentences(numbered[n - 1]["text"], " ".join(
                           p["point"] for p in points if n in p.get("sources", [])))[:400]} for n in used],
        "note": str(data.get("note", "")).strip() or (r.error and f"Model error: {r.error}") or "",
    }
