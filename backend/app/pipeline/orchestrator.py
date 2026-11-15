# orchestrator.py — the v2 grading pipeline for one submission (V2_EVALIFY_PLAN.md §3).
#
#   pages → quality gate → OMR template | whole-page readers A + B (+ C on disagreement, 2 of 3)
#   → MCQ / numeric scored in code → subjective: whole-page transcription by label → one grader (v2)
#   → optional teacher calibration → questions the pipeline is unsure of are flagged for a TA with one reason.
#
# Output keeps the legacy detail format (mcqDetail / numericalDetail / subjectiveDetail) and adds
# needs_review / review_reason(s) / readings per question.

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from typing import Dict, List

import cv2
import numpy as np

from app.pipeline import calibration, llm, numeric, page_reading, quality, readers, routing
from app.pipeline.grader import grade
from app.pipeline.readers import Question, Reading
from app.pipeline.scoring import grade_mcq, grade_numerical
from app.prompts.prompt_pipeline import TEMPLATE_VERSION
from app.services.omr_engine import OMREngine

WORKERS = int(os.environ.get("EVALIFY_PIPELINE_WORKERS", "8"))   # parallel requests (vLLM batches them)
_omr = OMREngine()


def run(paper: dict, files: List[str], sheet_type: str) -> dict:
    """Evaluate one submission; returns answers, per-section details, scores and review info."""
    t0 = time.time()
    questions = readers.questions_for(paper)

    # 1. Ingest + quality gate (cleaned page saved next to the upload)
    pages, reports = [], []
    for f in files:
        img, rep = quality.prepare(f, out_path=os.path.splitext(f)[0] + "_clean.png")
        pages.append(img)
        reports.append(rep)
    sheet_reasons = routing.page_reasons(reports)
    # Blank pages / show-through backs carry no answers: don't read them (OMR keeps all pages)
    if sheet_type != "omr":
        pages = [p for p, r in zip(pages, reports) if not r.blank] or pages

    # 2. Read every answer
    # Template only once the teacher has confirmed its bubble map (a wrong map would mis-grade everyone)
    tpl = paper.get("omrTemplate") or {}
    if sheet_type == "omr" and tpl.get("bubbles") and tpl.get("confirmed"):
        reads, models = _read_omr_template(files, paper["omrTemplate"], questions, pages), {"reader_a": "omr_template"}
    elif sheet_type == "omr":
        reads, models = _read_omr(pages, questions), {"reader_a": "opencv_omr"}
    else:
        reads, models = _read_handwritten(pages, questions)
    # Grade whatever reader A read, even if it said "unclear" (that question is routed anyway)
    answers = {qid: r.get("final", r["a"]).value for qid, r in reads.items() if r.get("final", r["a"]).value}

    # 3. Closed-form questions: scored in code
    n_mcq = sum(q.kind == "mcq" for q in questions)
    n_num = sum(q.kind == "numerical" for q in questions)
    mcq_score, n_correct, mcq_detail = grade_mcq(answers, paper, n_mcq)
    num_score, num_detail = grade_numerical(answers, paper, n_num)
    for d in num_detail:                                    # unparseable numbers / unit problems
        reads[d["question"]]["reasons"] += routing.numeric_reasons(
            numeric.compare(d["student_answer"], paper.get("numericalAnswers", {}).get(d["question"])))

    # 4. Subjective: per-concept grading on both transcripts
    subj_score, subj_detail, grader_models = _grade_subjective(paper, questions, reads, pages)
    models.update(grader_models)

    # 5. Attach readings + review flags to every detail row
    review = []
    for d in mcq_detail + num_detail + subj_detail:
        r = reads.get(d["question"], {"reasons": [], "a": Reading(), "b": Reading()})
        if r.get("accepted") and r.get("final") is r.get("b"):
            d["accepted_by"] = "readers B + C (majority)"
        reasons = sheet_reasons + r["reasons"] + d.pop("_grader_reasons", [])
        # The TA view shows one short reason; the full list is kept for the record
        d.update(needs_review=bool(reasons), review_reason=reasons[0] if reasons else "", review_reasons=reasons,
                 readings={k: asdict(r[k]) for k in ("a", "b", "c") if k in r})
        if reasons:
            review.append({"question": d["question"], "reason": reasons[0], "reasons": reasons})

    return {
        "answers": answers, "mcq_detail": mcq_detail, "numerical_detail": num_detail,
        "subjective_detail": subj_detail, "mcq_score": mcq_score, "n_correct": n_correct,
        "numerical_score": num_score, "subjective_score": subj_score,
        "review": review, "quality": [asdict(r) for r in reports], "models": models,
        "prompt_version": TEMPLATE_VERSION, "latency_s": round(time.time() - t0, 3),
    }


# ── Reading ──────────────────────────────────────────────────────────────────

def _read_omr(pages, questions: List[Question]) -> Dict[str, dict]:
    """OMR on each page; the first page that has a question wins; margin feeds routing."""
    found: Dict[str, dict] = {}
    for page in pages:
        bgr = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
        for qid, det in _omr.detect(bgr, sum(q.kind == "mcq" for q in questions)).items():
            found.setdefault(qid, det)

    reads = {}
    for q in (q for q in questions if q.kind == "mcq"):
        det = found.get(q.id, {})
        a = Reading("opencv_omr", "omr", "answered" if det.get("answer") else "blank", det.get("answer", ""),
                    raw=str(det.get("ratios", "")))
        reasons = routing.omr_reasons(det.get("margin")) if det else ["question not found on OMR sheet"]
        reads[q.id] = {"a": a, "b": Reading(), "reasons": reasons}
    return reads


def _read_omr_template(files, template: dict, questions: List[Question], pages) -> Dict[str, dict]:
    """Align each page to the teacher's blank sheet and read fills at the known bubble spots.
    Pages that cannot be aligned fall back to the layout-free engine and are flagged."""
    from app.pipeline import omr_template as omr
    blank = cv2.imread(os.path.join("uploads/papers", template["blank_url"].rstrip("/").split("/")[-1]))
    found: Dict[str, dict] = {}
    unaligned = []
    for i, f in enumerate(files):
        res = omr.read_sheet(cv2.imread(f), blank, template) if blank is not None else {"aligned": False}
        if not res["aligned"]:
            unaligned.append(i + 1)
            continue
        for q, det in res["answers"].items():
            found.setdefault(q, det)

    # Nothing aligned → layout-free engine, every question flagged
    if not found:
        reads = _read_omr(pages, questions)
        for r in reads.values():
            r["reasons"].append("sheet could not be aligned to the blank OMR template")
        return reads

    reads = {}
    for q in (q for q in questions if q.kind == "mcq"):
        det = found.get(q.id)
        a = Reading("omr_template", "omr", "answered" if det and det["answer"] else "blank",
                    det["answer"] if det else "", raw=str(det["deltas"]) if det else "")
        reasons = routing.omr_reasons(det["margin"]) if det else ["question not in the OMR template"]
        if unaligned:
            reasons.append(f"page(s) {unaligned} could not be aligned to the template")
        reads[q.id] = {"a": a, "b": Reading(), "reasons": reasons}
    return reads


def _read_handwritten(pages, questions: List[Question]):
    """Whole-page reading (no crops): MCQ / numerical by majority of readers A, B, C;
    subjective answers transcribed page by page and grouped by the question number the student wrote."""
    ep_a = llm.resolve("page_reader_a")
    if ep_a is None:
        raise RuntimeError("no reader model is reachable")
    ep_b = llm.resolve("page_reader_b", exclude=(ep_a.name,))
    ep_c = llm.resolve("page_reader_c", exclude=(ep_a.name, ep_b.name if ep_b else ""))
    reads = page_reading.read_closed_form(pages, questions, ep_a, ep_b, ep_c, workers=WORKERS)
    models = {"reader_a": ep_a.version, "reader_b": ep_b.version if ep_b else "none",
              "reader_c": ep_c.version if ep_c else "none"}

    # Subjective answers: two transcribers from different families
    subj = [q for q in questions if q.kind == "subjective"]
    if subj:
        tr_a = llm.resolve("transcriber_a")
        tr_b = llm.resolve("transcriber_b", exclude=(tr_a.name,) if tr_a else ())
        texts, _secs = page_reading.transcribe_subjective(pages, questions, tr_a, tr_b) if tr_a else ({}, {})
        for q in subj:
            ta, tb = texts.get(q.id, ("", ""))
            found = bool(ta.strip() or tb.strip())
            a = Reading(tr_a.name if tr_a else "", tr_a.version if tr_a else "", "answered" if ta else "blank", ta)
            b = Reading(tr_b.name if tr_b else "", tr_b.version if tr_b else "", "answered" if tb else "blank", tb)
            # Never an automatic 0: an answer we could not find goes to a TA
            reasons = [] if found else ["answer not found on the page"]
            reads[q.id] = {"a": a, "b": b, "final": a, "accepted": found, "reasons": reasons}
        models.update(transcriber_a=tr_a.version if tr_a else "none", transcriber_b=tr_b.version if tr_b else "none")
    return reads, models


def abstained(r: Reading) -> bool:
    """A reader that gave no usable answer (blank / unclear / failed / empty)."""
    return r.status in ("blank", "unclear", "error", "missing") or not r.value


# ── Subjective grading ───────────────────────────────────────────────────────

def _grade_subjective(paper, questions, reads, pages):
    """One grader (Gemma + prompt v2) per subjective answer; optional teacher calibration on top."""
    subj = [q for q in questions if q.kind == "subjective"]
    if not subj:
        return 0.0, [], {}
    g_ep = llm.resolve("grader")
    rubrics = paper.get("subjectiveRubrics", [])
    texts = paper.get("subjectiveQuestions", [])
    per_q = paper.get("subjectiveQuestionMarks", {})
    default = float(paper.get("subjectiveMarks", 5))
    cal = paper.get("calibration")                      # optional, teacher-only (per-question shift)

    def grade_one(i_q):
        i, q = i_q
        r = reads[q.id]
        rubric = rubrics[i] if i < len(rubrics) else {}
        rubric_max = len(rubric.get("key_concepts", [])) * float(rubric.get("marks_per_concept", default))
        max_marks = float(per_q.get(q.id, rubric_max or default))
        q_text = texts[i] if i < len(texts) else f"Question {i + 1}"
        a_txt, b_txt = r["a"].value, r["b"].value

        # Not found on the page: no grader call, 0 for now, the TA decides (reason already in reads)
        if not (a_txt.strip() or b_txt.strip()):
            return _subj_row(q, q_text, "", max_marks, 0.0, None, [], cal)
        if g_ep is None:
            return _subj_row(q, q_text, a_txt, max_marks, 0.0, None, ["no grader model is reachable"], cal)

        # Transcripts only (the measured set-up; whole pages would show the grader other answers too)
        g = grade(g_ep, q_text, rubric, a_txt, b_txt, [], paper.get("subject", ""), max_marks, version="v2")
        return _subj_row(q, q_text, a_txt, max_marks, g.marks, g, routing.grader_reasons(g), cal)

    with ThreadPoolExecutor(WORKERS) as pool:
        detail = list(pool.map(grade_one, enumerate(subj)))
    models = {"grader": g_ep.version if g_ep else "none", "calibration": "per-question shift" if cal else "none"}
    return sum(d["marks_earned"] for d in detail), detail, models


def _subj_row(q, q_text, answer, max_marks, marks, g1, reasons, cal=None) -> dict:
    """Subjective detail row in the legacy shape + per-concept evidence + rubric / calibrated marks."""
    decisions = g1.decisions if g1 else []
    calibrated = calibration.apply(cal, q.id, marks, max_marks) if cal and g1 else None
    return {
        "question": q.id, "question_text": q_text, "student_answer": answer[:2000] or None,
        "marks_available": max_marks, "marks_earned": calibrated if calibrated is not None else marks,
        "rubric_marks": marks, "calibrated_marks": calibrated,
        "status": "graded_by_llm" if answer else "unanswered",
        "concepts_found": [d.concept for d in decisions if d.present],
        "concepts_missing": [d.concept for d in decisions if not d.present],
        "mandatory_met": g1.mandatory_met if g1 else True,
        "feedback": "; ".join(f"{d.concept}: \"{d.evidence}\"" for d in decisions if d.present),
        "concepts": [asdict(d) for d in decisions],
        "graders": [g1.version] if g1 else [],
        "_grader_reasons": reasons,
    }
