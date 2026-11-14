# grader.py — rubric-decomposed subjective grading.
#
# The grader judges each rubric concept separately (present yes/no + evidence
# quote + confidence). Python then applies the mandatory rule and sums marks,
# so the model never does arithmetic or decides the final score.

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from PIL import Image

from app.pipeline import llm
from app.prompts import prompt_pipeline as P


@dataclass
class ConceptDecision:
    """One rubric concept as judged by one grader."""
    concept: str
    present: bool = False
    evidence: str = ""
    confidence: Optional[float] = None
    evidence_found: bool = True       # is the quote really in a transcript?


@dataclass
class GradeResult:
    """One grader's verdict on one answer."""
    grader: str = ""
    version: str = ""
    marks: float = 0.0
    max_marks: float = 0.0
    mandatory_met: bool = True
    decisions: List[ConceptDecision] = field(default_factory=list)
    transcript_problem: bool = False
    latency_s: float = 0.0
    prompt_hash: str = ""
    error: str = ""


def grade(ep: llm.Endpoint, question: str, rubric: dict, transcript_a: str, transcript_b: str,
          images: List[Image.Image], subject: str = "", max_marks: Optional[float] = None,
          thinking: bool = False) -> GradeResult:
    """Ask one grader for per-concept decisions, then score them in Python."""
    concepts = list(rubric.get("key_concepts", []))
    res = GradeResult(grader=ep.name, version=ep.version)
    if not concepts:
        res.error = "rubric has no concepts"
        return res

    # Text-only graders (e.g. gpt-oss) get the transcripts but no image
    imgs = [] if ep.spec.get("text_only") else images
    r = llm.chat(ep, P.grade_prompt(question, rubric.get("model_answer", ""), concepts,
                                    transcript_a, transcript_b, subject),
                 imgs, schema=P.GRADE_SCHEMA, max_tokens=8192 if thinking else 2048, thinking=thinking)
    res.latency_s, res.prompt_hash, res.error = r.latency_s, r.prompt_hash, r.error
    data = r.data or {}
    res.transcript_problem = bool(data.get("transcript_problem", False))

    # Match decisions back to concepts by position (fallback: by name)
    got = data.get("concepts", [])
    by_name = {str(d.get("concept", "")).strip().lower(): d for d in got}
    for i, c in enumerate(concepts):
        d = got[i] if i < len(got) and _same(got[i].get("concept"), c) else by_name.get(c.strip().lower(), {})
        dec = ConceptDecision(c, bool(d.get("present", False)), str(d.get("evidence", "")).strip(),
                              _conf(d.get("confidence")) if d else None)
        dec.evidence_found = (not dec.present) or quote_in(dec.evidence, transcript_a, transcript_b)
        res.decisions.append(dec)

    score(res, rubric, max_marks)
    return res


def score(res: GradeResult, rubric: dict, max_marks: Optional[float] = None) -> None:
    """Mandatory rule (no mandatory concept present → 0) + marks per concept, capped at max."""
    per = float(rubric.get("marks_per_concept", 1))
    mandatory = {m.strip().lower() for m in rubric.get("mandatory_concepts", [])}
    present = {d.concept.strip().lower() for d in res.decisions if d.present}
    res.max_marks = float(max_marks if max_marks is not None else len(res.decisions) * per)
    res.mandatory_met = (not mandatory) or bool(mandatory & present)
    res.marks = min(len(present) * per, res.max_marks) if res.mandatory_met else 0.0


def quote_in(quote: str, *texts: str) -> bool:
    """Is the evidence quote (≥ 80 % of its words, in order-insensitive form) in any transcript?"""
    words = _words(quote)
    if not words:
        return False
    return any(len(words & _words(t)) >= 0.8 * len(words) for t in texts if t)


def _words(s: str) -> set:
    """Lower-case word set, ignoring punctuation and struck-out text."""
    return set(re.findall(r"[a-z0-9]+", re.sub(r"~~.*?~~", "", s or "").lower()))


def _same(a, b) -> bool:
    """Loose concept-name match (models sometimes rephrase the concept)."""
    a, b = str(a or "").strip().lower(), str(b or "").strip().lower()
    return a == b or a in b or b in a


def _conf(v) -> Optional[float]:
    """Clamp confidence to [0, 1]."""
    try:
        return max(0.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return None
