# page_reading.py — v2 reading: whole pages, no answer crops (chosen in runs 5–9).
#
# MCQ / numerical (types A-handwritten, B, C): reader A and reader B (different model families) read every page
#   in one call each; agreement → accept; otherwise reader C reads the page and 2 of 3 decide; no majority → TA.
#   Measured: own sheets 0 silent errors, 97–98 % auto; Mendeley MCQ ~1 error / 1000.
# Subjective (type C): transcriber A (JSON) and B (plain text with [[Qnn]] markers) transcribe each page grouped
#   by the question number the student wrote; pages are joined by label and a crossed-out attempt is dropped when
#   it was rewritten. Measured: 555 / 564 answers found (old box segmentation: 523).

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Tuple

from app.pipeline import llm, numeric, readers
from app.pipeline.readers import Question, Reading
from app.prompts import prompt_pipeline as P

ABSTAIN = ("unclear", "error", "missing")


# ── labels and values ────────────────────────────────────────────────────────

def norm_label(label) -> str:
    """'12' / 'q12' / 'Q.12' → 'Q12'; 'CONTINUED' stays."""
    s = str(label or "").strip().upper()
    if s.startswith("CONTINUED"):
        return "CONTINUED"
    digits = re.sub(r"\D", "", s)
    return f"Q{digits}" if digits else s


def norm_mcq(s: str) -> str:
    """'c a' / 'A, C' → 'A,C' (letters and digits as tokens; '' stays '')."""
    return ",".join(sorted({t.upper() for t in re.findall(r"[A-Za-z]|\d+", s or "")}))


def same_value(kind: str, a: str, b: str) -> bool:
    """Do two answers say the same thing? Blank equals blank; numbers compared as numbers."""
    a, b = (a or "").strip(), (b or "").strip()
    if not a or not b:
        return not a and not b
    if kind == "mcq":
        return norm_mcq(a) == norm_mcq(b)
    ok = numeric.numbers_agree(a, b)
    return bool(ok) if ok is not None else re.sub(r"\s+", "", a).lower() == re.sub(r"\s+", "", b).lower()


# ── one page → readings ──────────────────────────────────────────────────────

def readings_from_page_json(data, questions: List[Question], reader: str = "", latency: float = 0.0) -> Dict[str, Reading]:
    """VLM page JSON {"answers": [{label, status, value}]} → {qid: Reading}; unlisted questions are blank."""
    by_label = {q.label.upper(): q for q in questions}
    got = {}
    for a in (data or {}).get("answers", []):
        q = by_label.get(norm_label(a.get("label")))
        if q:
            got[q.id] = a
    out = {}
    for q in questions:
        a = got.get(q.id, {})
        val = str(a.get("value", "") or "").strip()
        val = norm_mcq(val) if q.kind == "mcq" else val
        status = "answered" if val else ("unclear" if a.get("status") == "unclear" else "blank")
        out[q.id] = Reading(reader, status=status, value=val, latency_s=latency)
    return out


def readings_from_ocr_text(text: str, questions: List[Question], reader: str = "", latency: float = 0.0) -> Dict[str, Reading]:
    """OCR page text → {qid: Reading} from lines that start with a question number ("2) A, D", "3. 4.01 V")."""
    by_num = {re.sub(r"\D", "", q.label): q for q in questions}
    found: Dict[str, str] = {}
    for line in readers.clean_ocr(text).splitlines():
        m = re.match(r"^\s*(?:Q\.?\s*)?(\d{1,3})\s*[.,:)](?!\d)\s*(.*)$", line)
        if m and m.group(1) in by_num and by_num[m.group(1)].id not in found:
            found[by_num[m.group(1)].id] = m.group(2).strip()
    out = {}
    for q in questions:
        body = found.get(q.id, "")
        val = readers.parse_letters(body) if q.kind == "mcq" else readers.parse_final_number(body)
        out[q.id] = Reading(reader, status="answered" if val else ("unclear" if body else "blank"),
                            value=val, raw=body, latency_s=latency)
    return out


def merge_pages(per_page: List[Dict[str, Reading]], questions: List[Question]) -> Dict[str, Reading]:
    """Several pages → one reading per question: first answered page wins, else unclear, else blank."""
    out = {}
    for q in questions:
        rs = [p[q.id] for p in per_page if q.id in p]
        pick = (next((r for r in rs if r.status == "answered"), None)
                or next((r for r in rs if r.status == "unclear"), None)
                or (rs[0] if rs else Reading(status="missing")))
        pick.latency_s = round(sum(r.latency_s for r in rs), 3)       # all page calls count towards time
        out[q.id] = pick
    return out


# ── majority vote ────────────────────────────────────────────────────────────

def _agree(kind: str, x: Optional[Reading], y: Optional[Reading]) -> bool:
    """Two readings agree when neither abstained and they give the same value (blank = blank)."""
    if x is None or y is None or x.status in ABSTAIN or y.status in ABSTAIN:
        return False
    return same_value(kind, x.value, y.value)


def _show(r: Optional[Reading]) -> str:
    """'B' / 'blank' / 'unclear' for the TA reason line."""
    if r is None:
        return "-"
    return r.value if r.value else r.status


def decide(kind: str, a: Reading, b: Reading, c: Optional[Reading] = None) -> Tuple[Optional[Reading], str]:
    """A and B agree → A. Otherwise C must agree with A or B (2 of 3). Else (None, one-line reason for the TA)."""
    winner = a if _agree(kind, a, b) else next((x for x in (a, b) if c is not None and _agree(kind, c, x)), None)
    # A blank vote while one reader saw an answer is ambiguous (faint writing, or show-through from the back):
    # a TA decides instead of a silent 0
    if winner is not None and not winner.value and any(r is not None and r.value for r in (a, b, c)):
        seen = ", ".join(f"{n}: {r.value}" for n, r in (("A", a), ("B", b), ("C", c)) if r is not None and r.value)
        return None, f"only one reader saw an answer ({seen}) — faint writing or show-through?"
    if winner is not None:
        return winner, ""
    if all(r is None or r.status in ABSTAIN for r in (a, b, c)):
        return None, "handwriting unclear to every reader"
    shown = f"A: {_show(a)}, B: {_show(b)}" + (f", C: {_show(c)}" if c is not None else "")
    return None, f"readers disagree ({shown})"


# ── subjective: transcription grouped by label ───────────────────────────────

def split_marked(text: str, last_label: Optional[str]) -> Tuple[list, Optional[str]]:
    """Plain page text with [[Qnn]] / [[Qnn CROSSED]] / [[CONTINUED]] markers → ([(label, crossed, text)], last label)."""
    out, cur, crossed, buf = [], last_label, False, []

    def flush():
        if cur and "\n".join(buf).strip():
            out.append((cur, crossed, "\n".join(buf).strip()))

    for line in (text or "").splitlines():
        m = re.match(r"^\s*\[\[\s*(Q?\s*\d+|CONTINUED)\s*(CROSSED)?\s*\]\]\s*(.*)$", line, re.I)
        if m:
            flush()
            lab = norm_label(m.group(1))
            cur = last_label if lab == "CONTINUED" else lab
            crossed, buf = bool(m.group(2)), [m.group(3)]
        else:
            buf.append(line)
    flush()
    return out, (out[-1][0] if out else last_label)


def items_from_page_json(data, last_label: Optional[str]) -> Tuple[list, Optional[str]]:
    """Page JSON {"answers": [{label, text, fully_crossed_out}]} → ([(label, crossed, text)], last label)."""
    items = []
    for a in (data or {}).get("answers", []):
        lab = norm_label(a.get("label"))
        lab = last_label if lab == "CONTINUED" else lab
        text = str(a.get("text", "") or "").strip()
        if lab and text:
            items.append((lab, bool(a.get("fully_crossed_out")), text))
            last_label = lab
    return items, last_label


def merge_attempts(store: Dict[str, str], items: list) -> None:
    """Add one page's items; a crossed-out attempt is dropped when the same label has a rewrite on that page."""
    page: Dict[str, list] = {}
    for lab, crossed, text in items:
        page.setdefault(lab, []).append((crossed, text))
    for lab, its in page.items():
        keep = [t for c, t in its if not c] or [t for _, t in its]
        store[lab] = "\n".join(filter(None, [store.get(lab, "")] + keep))


def subjective_texts(store_a: Dict[str, str], store_b: Dict[str, str],
                     questions: List[Question]) -> Dict[str, Tuple[str, str]]:
    """{subjective qid: (transcript A, transcript B)} for answers found by at least one transcriber."""
    return {q.id: (store_a.get(q.label, ""), store_b.get(q.label, "")) for q in questions
            if q.kind == "subjective" and (store_a.get(q.label) or store_b.get(q.label))}


# ── model calls ──────────────────────────────────────────────────────────────

def _page_closed(ep, page, questions):
    """One page read by one model: VLM → JSON, OCR model → its own prompt, parsed in code."""
    if ep.spec.get("supports_json_schema") and ep.spec.get("prompt_style", "general") == "general":
        r = llm.chat(ep, P.page_prompt([(q.label, q.kind) for q in questions]), [page],
                     schema=P.PAGE_SCHEMA, max_tokens=2048, stage="read_mcq_numerical")
        if r.error and not r.data:
            return {q.id: Reading(ep.name, ep.version, "error", error=r.error) for q in questions}
        return readings_from_page_json(r.data, questions, ep.name, r.latency_s)
    r = llm.chat(ep, P.OCR_PROMPTS.get(ep.spec.get("prompt_style"), P.OCR_PROMPTS["general"]), [page], max_tokens=4096,
                 stage="read_mcq_numerical")
    if r.error and not r.text:
        return {q.id: Reading(ep.name, ep.version, "error", error=r.error) for q in questions}
    return readings_from_ocr_text(r.text, questions, ep.name, r.latency_s)


def _read_all_pages(ep, pages, questions, workers):
    with ThreadPoolExecutor(max(1, workers)) as pool:
        # carry(): page reads in worker threads still count toward this sheet's tokens
        return merge_pages(list(pool.map(llm.carry(lambda p: _page_closed(ep, p, questions)), pages)), questions)


def read_closed_form(pages, questions: List[Question], ep_a, ep_b, ep_c=None, workers: int = 4) -> Dict[str, dict]:
    """{qid: {"a", "b", "c", "final", "reasons"}} for MCQ and numerical questions (whole-page majority)."""
    qs = [q for q in questions if q.kind != "subjective"]
    if not qs:
        return {}
    with ThreadPoolExecutor(2) as pool:                         # A and B in parallel
        fa = pool.submit(llm.carry(_read_all_pages), ep_a, pages, qs, workers)
        fb = pool.submit(llm.carry(_read_all_pages), ep_b, pages, qs, workers) if ep_b else None
        ra, rb = fa.result(), (fb.result() if fb else {q.id: Reading() for q in qs})
    # Reader C only when A and B do not already agree on everything
    need_c = [q for q in qs if not _agree(q.kind, ra[q.id], rb[q.id])]
    rc = _read_all_pages(ep_c, pages, qs, workers) if ep_c and need_c else {}
    out = {}
    for q in qs:
        c = rc.get(q.id)
        final, reason = decide(q.kind, ra[q.id], rb[q.id], c)
        if ep_b is None and not reason:
            final, reason = None, "only one reader available"
        out[q.id] = {"a": ra[q.id], "b": rb[q.id], "c": c or Reading(), "final": final or ra[q.id],
                     "accepted": final is not None, "reasons": [reason] if reason else []}
    return out


def transcribe_subjective(pages, questions: List[Question], ep_a, ep_b) -> Tuple[Dict[str, Tuple[str, str]], dict]:
    """Whole-page transcription by label → ({subjective qid: (A, B)}, {"a": seconds, "b": seconds}).
    Every label (MCQ too) is passed so an MCQ line like "7. A" is never taken for Q27."""
    labels = [q.label for q in questions]

    def run_a():
        store, last, t = {}, None, 0.0
        for page in pages:
            r = llm.chat(ep_a, P.page_text_prompt(labels), [page], schema=P.PAGE_TEXT_SCHEMA, max_tokens=8192,
                         stage="transcribe_subjective")
            t += r.latency_s
            items, last = items_from_page_json(r.data, last)
            merge_attempts(store, items)
        return store, t

    def run_b():
        store, last, t = {}, None, 0.0
        if ep_b is None:
            return store, t
        for page in pages:
            r = llm.chat(ep_b, P.page_text_plain_prompt(labels), [page], max_tokens=8192, stage="transcribe_subjective")
            t += r.latency_s
            items, last = split_marked(r.text, last)
            merge_attempts(store, items)
        return store, t

    with ThreadPoolExecutor(2) as pool:
        fa, fb = pool.submit(llm.carry(run_a)), pool.submit(llm.carry(run_b))
        (sa, ta), (sb, tb) = fa.result(), fb.result()
    return subjective_texts(sa, sb, questions), {"a": round(ta, 3), "b": round(tb, 3)}
