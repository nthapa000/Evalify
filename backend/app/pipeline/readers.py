# readers.py — segmentation + two independent readers per answer.
#
# Reader A: general VLM with a verbatim / constrained-JSON prompt.
# Reader B: an OCR specialist from a different family (its own fixed prompt);
#           its free text is parsed in code into letters / a number / text.
# Disagreement between A and B is the main signal for sending work to a TA.

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from PIL import Image

from app.pipeline import llm, numeric
from app.prompts import prompt_pipeline as P


@dataclass
class Question:
    """One question as the pipeline sees it."""
    id: str            # internal id: Q1 (MCQ) / N1 (numerical) / S1 (subjective)
    label: str         # what the student writes on the sheet: Q1..Qm, Q(m+1).., S1..
    kind: str          # mcq | numerical | subjective


@dataclass
class Reading:
    """One reader's result for one answer."""
    reader: str = ""                   # model name
    version: str = ""                  # repo@revision
    status: str = "missing"            # answered | blank | unclear | missing | error
    value: str = ""                    # "A,C" / "3.5" / transcript
    raw: str = ""                      # untouched model output
    confidence: Optional[float] = None
    latency_s: float = 0.0
    prompt_hash: str = ""
    error: str = ""


def questions_for(paper: dict) -> List[Question]:
    """Question list in sheet order; numerical answers continue the Q-numbering."""
    ptype = paper.get("type", "mcq")
    n_mcq = int(paper.get("mcqCount", 0))
    n_num = int(paper.get("numericalCount", 0)) if "numerical" in ptype else 0
    n_subj = int(paper.get("subjectiveCount", 0)) if "subjective" in ptype else 0
    # paper["numbering"] == "continuous": subjective answers continue the Q-numbers too
    # (e.g. Q21–Q35 after 20 MCQs) instead of being labelled S1, S2, …
    cont = paper.get("numbering") == "continuous"
    return ([Question(f"Q{i}", f"Q{i}", "mcq") for i in range(1, n_mcq + 1)]
            + [Question(f"N{i}", f"Q{n_mcq + i}", "numerical") for i in range(1, n_num + 1)]
            + [Question(f"S{i}", f"Q{n_mcq + n_num + i}" if cont else f"S{i}", "subjective")
               for i in range(1, n_subj + 1)])


# ── Segmentation ─────────────────────────────────────────────────────────────

def segment(pages: List[Image.Image], questions: List[Question],
            ep: Optional[llm.Endpoint]) -> Dict[str, List[Image.Image]]:
    """{question id: [crops in page order]}; answers split over pages are stitched by label."""
    by_label = {q.label.upper(): q.id for q in questions}
    crops: Dict[str, List[Image.Image]] = {}
    if ep is None:
        return crops

    for page in pages:
        reply = llm.chat(ep, P.segment_prompt([q.label for q in questions]), [page],
                         schema=P.SEGMENT_SCHEMA, max_tokens=2048)
        for a in (reply.data or {}).get("answers", []):
            qid = by_label.get(str(a.get("label", "")).strip().upper())
            box = a.get("bbox") or []
            if qid and len(box) == 4:
                crops.setdefault(qid, []).append(_crop(page, box))
    return crops


def _crop(page: Image.Image, box: list, pad: float = 0.02) -> Image.Image:
    """0–1000 box → padded pixel crop. Vertical padding is capped at a quarter of the box
    height so a one-line answer does not pick up the lines above and below."""
    w, h = page.size
    (x0, x1), (y0, y1) = sorted(box[0::2]), sorted(box[1::2])
    pad_y = min(pad * h, 0.25 * (y1 - y0) / 1000 * h)
    x0, x1 = max(0, (x0 / 1000 - pad) * w), min(w, (x1 / 1000 + pad) * w)
    y0, y1 = max(0, y0 / 1000 * h - pad_y), min(h, y1 / 1000 * h + pad_y)
    return page.crop((int(x0), int(y0), int(max(x1, x0 + 8)), int(max(y1, y0 + 8))))


# ── Reader A: general VLM, schema-constrained ────────────────────────────────

def read_general(ep: llm.Endpoint, q: Question, images: List[Image.Image], verbatim: bool = True) -> Reading:
    """Closed-form questions use constrained JSON; subjective uses verbatim transcription."""
    if q.kind == "mcq":
        prompt, schema = P.mcq_prompt(q.label), P.MCQ_SCHEMA
    elif q.kind == "numerical":
        prompt, schema = P.number_prompt(q.label), P.NUMBER_SCHEMA
    else:
        prompt, schema = P.transcribe_prompt(q.kind, verbatim), P.TRANSCRIBE_SCHEMA
    r = llm.chat(ep, prompt, images, schema=schema, max_tokens=4096 if q.kind == "subjective" else 512)
    out = Reading(ep.name, ep.version, raw=r.text, latency_s=r.latency_s, prompt_hash=r.prompt_hash, error=r.error)
    d = r.data or {}
    if r.error and not d:
        out.status = "error"
        return out

    # Normalise each schema to (status, value, confidence)
    out.confidence = _conf(d.get("confidence"))
    # Keep the value even when the reader says "unclear": it is routed, and the TA sees it
    if q.kind == "mcq":
        out.status = d.get("status", "unclear")
        out.value = ",".join(sorted(set(d.get("options", [])))) if out.status != "blank" else ""
        if out.status == "answered" and not out.value:
            out.status = "unclear"
    elif q.kind == "numerical":
        out.status = d.get("status", "unclear")
        raw = re.sub(r"^\s*[QqSs]?\d{1,3}\s*[:.),](?!\d)\s*", "", str(d.get("final_answer", "")).strip())  # copied label, not a decimal
        out.value = raw if out.status != "blank" else ""
    else:
        out.value = str(d.get("text", "")).strip()
        out.status = "answered" if out.value else "blank"
        if d.get("illegible_tokens"):
            out.confidence = min(out.confidence or 1.0, 0.5)
    return out


# ── Reader B: OCR specialist, free text parsed in code ───────────────────────

def read_ocr(ep: llm.Endpoint, q: Question, images: List[Image.Image]) -> Reading:
    """Run the model's own OCR prompt on each crop, then parse the text for this question type."""
    # A JSON-capable general model can stand in as reader B; use the constrained prompts then
    style = ep.spec.get("prompt_style", "general")
    if style == "general" and ep.spec.get("supports_json_schema"):
        return read_general(ep, q, images)

    texts, latency, err, ph = [], 0.0, "", ""
    for im in images:
        r = llm.chat(ep, P.OCR_PROMPTS.get(style, P.OCR_PROMPTS["general"]), [im], max_tokens=4096)
        texts.append(clean_ocr(r.text))
        latency, err, ph = latency + r.latency_s, err or r.error, r.prompt_hash
    text = "\n".join(t for t in texts if t).strip()
    out = Reading(ep.name, ep.version, raw=text, latency_s=round(latency, 3), prompt_hash=ph, error=err)
    if err and not text:
        out.status = "error"
        return out

    # Parse the free text according to the question type
    body = strip_label(text, q.label)
    if q.kind == "mcq":
        out.value = parse_letters(body)
    elif q.kind == "numerical":
        out.value = parse_final_number(body)
    else:
        out.value = body
    out.status = "answered" if out.value else ("unclear" if body else "blank")
    return out


def clean_ocr(text: str) -> str:
    """HTML/markdown from OCR models → plain text (struck-out text kept as ~~x~~)."""
    t = re.sub(r"<del>(.*?)</del>", r"~~\1~~", text or "", flags=re.S)
    t = re.sub(r"<br\s*/?>|</p>|</div>|</li>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    return re.sub(r"\n{3,}", "\n\n", t.replace("```", "")).strip()


def strip_label(text: str, label: str) -> str:
    """Remove a leading 'Q3:' / '3)' / 'Ans 3.' so it isn't read as part of the answer."""
    num = re.sub(r"\D", "", label)
    # The number must end at punctuation (not starting a decimal) or a space: "3. 4.01" → "4.01", "3.5" stays
    return re.sub(rf"^\s*(?:{label[0]}|ans(?:wer)?)?\s*\.?\s*{num}(?:\s*[.,:)\-](?!\d)|(?=\s)|$)\s*", "", text, count=1, flags=re.I).strip()


def parse_letters(text: str) -> str:
    """Standalone option letters that are not struck out → 'A,C'."""
    t = re.sub(r"~~.*?~~", "", text)
    letters = re.findall(r"(?<![A-Za-z])([A-Ea-e])(?![A-Za-z])", t)
    return ",".join(sorted({l.upper() for l in letters}))


def parse_final_number(text: str) -> str:
    """Last line that parses as a number (after '=' / 'Ans'), as written."""
    lines = [l for l in re.sub(r"~~.*?~~", "", text).splitlines() if l.strip()]
    for line in reversed(lines):
        # Value after the last "=" or "Ans:"; a misread label like "23:" is dropped
        cand = re.split(r"=|\bans(?:wer)?\b\s*[:.]?", line, flags=re.I)[-1]
        cand = re.sub(r"^\s*[QqSs]?\d{1,3}\s*[:.),](?!\d)\s*", "", cand).strip()            # "23:" yes, "4.01" no
        if numeric.parse_number(cand).ok:
            return cand
    return ""


def _conf(v) -> Optional[float]:
    """Clamp a self-reported confidence to [0, 1]."""
    try:
        return max(0.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return None


# ── Agreement between the two readers ────────────────────────────────────────

def agree(kind: str, a: Reading, b: Reading) -> Optional[bool]:
    """Do A and B say the same thing? None when B is missing (cannot check)."""
    if b.status in ("missing", "error"):
        return None
    if a.status != "answered" or b.status != "answered":
        return a.status == b.status
    if kind == "mcq":
        return a.value == b.value
    if kind == "numerical":
        return bool(numeric.numbers_agree(a.value, b.value))
    return text_similarity(a.value, b.value) >= 0.85


def text_similarity(a: str, b: str) -> float:
    """1 − normalised character edit distance on lower-cased, whitespace-collapsed text."""
    from app.pipeline.textdist import cer
    norm = lambda s: re.sub(r"\s+", " ", re.sub(r"~~.*?~~", "", s or "").lower()).strip()  # noqa: E731
    return max(0.0, 1.0 - cer(norm(a), norm(b)))
