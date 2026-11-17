# routing.py — decide which questions go to a TA, and why.
#
# A question is auto-accepted only if no rule fires. Thresholds live in
# infra/routing.yaml (calibrated on the dev split by eval/calibrate.py);
# the defaults below are deliberately cautious.

from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

import yaml

from app.pipeline import llm

DEFAULTS = {
    "omr_min_margin": 0.05,           # fill ratio this close to the threshold = ambiguous
    "reader_min_confidence": 0.6,     # self-reported reader confidence
    "transcript_min_similarity": 0.85,  # subjective A vs B agreement
    "concept_min_confidence": 0.7,    # any concept judged below this → review
    "grader_max_mark_gap": 1.0,       # two graders differ by more than this → review
}


@lru_cache(maxsize=1)
def thresholds() -> dict:
    """Defaults overridden by infra/routing.yaml when present."""
    path = llm.REPO_ROOT / "infra" / "routing.yaml"
    loaded = yaml.safe_load(path.read_text()) if path.exists() else {}
    return {**DEFAULTS, **(loaded or {})}


def page_reasons(quality_reports: list) -> List[str]:
    """A page that failed the quality gate sends every question on the sheet to review."""
    return [f"page {i + 1}: {', '.join(r.reasons)}" for i, r in enumerate(quality_reports)
            if not r.ok and not getattr(r, "blank", False)]


def omr_reasons(margin: Optional[float]) -> List[str]:
    """Thin OMR margin (a bubble is half-filled or smudged)."""
    t = thresholds()
    return [f"thin OMR margin ({margin:.2f})"] if margin is not None and margin < t["omr_min_margin"] else []


def omr_all_filled(answer: str, n_options: int) -> bool:
    """Every option of a question read as filled: not a real answer, usually the sheet was misread (skewed photo)."""
    return n_options >= 3 and len([a for a in answer.split(",") if a]) >= n_options


def reader_reasons(kind: str, a, b, agreed: Optional[bool], similarity: Optional[float] = None) -> List[str]:
    """Reader disagreement, unreadable answers, low confidence, missing second reader."""
    t, out = thresholds(), []
    if a.status in ("error", "missing"):
        out.append("reader A failed")
    if a.status == "unclear" or b.status == "unclear":
        out.append("answer marked unclear by a reader")
    if agreed is False:
        out.append(f"readers disagree (A={a.value!r}, B={b.value!r})" if kind != "subjective"
                   else f"transcripts differ (similarity {similarity:.2f})")
    if agreed is None and kind != "subjective":
        out.append("no second reader available")      # exact answers need two readers
    if a.confidence is not None and a.confidence < t["reader_min_confidence"]:
        out.append(f"low reader confidence ({a.confidence:.2f})")
    return out


def numeric_reasons(result) -> List[str]:
    """A number we could not parse, or unit problems, needs a human."""
    out = ["could not parse the number"] if result.status == "unparseable" else []
    out += [f"unit: {f}" for f in result.flags if f in ("unit_mismatch", "unknown_unit")]
    return out


def grader_reasons(g1, g2=None) -> List[str]:
    """Low concept confidence, unverifiable evidence, transcript problems, grader disagreement."""
    t, out = thresholds(), []
    if g1.error:
        out.append(f"grader failed: {g1.error}")
    low = [d.concept for d in g1.decisions if d.confidence is not None and d.confidence < t["concept_min_confidence"]]
    if low:
        out.append(f"low confidence on: {', '.join(low)}")
    bad = [d.concept for d in g1.decisions if not d.evidence_found]
    if bad:
        out.append(f"evidence not found in transcript for: {', '.join(bad)}")
    if g1.transcript_problem:
        out.append("grader flagged a transcription problem")
    if g2 is not None and not g2.error and abs(g1.marks - g2.marks) > t["grader_max_mark_gap"]:
        out.append(f"graders differ ({g1.marks:g} vs {g2.marks:g})")
    return out
