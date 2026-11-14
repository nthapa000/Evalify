# orchestrator.py — the two-reader grading pipeline for one submission.
#
#   pages → quality gate → (OMR | segment + reader A + reader B) per question
#   → MCQ / numeric scored in code → subjective graded per concept
#   → routing rules mark what a TA must check.
#
# Output keeps the legacy detail format (mcqDetail / numericalDetail /
# subjectiveDetail) and adds needs_review / review_reasons / readings per question.

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from typing import Dict, List

import cv2
import numpy as np

from app.pipeline import llm, numeric, quality, readers, routing
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
        if "final" in r and r["final"] is not r["a"]:
            d["accepted_by"] = "readers B + C (A abstained)" if r["final"] is r["b"] else "readers A + C (B abstained)"
        reasons = sheet_reasons + r["reasons"] + d.pop("_grader_reasons", [])
        d.update(needs_review=bool(reasons), review_reasons=reasons,
                 readings={k: asdict(r[k]) for k in ("a", "b", "c") if k in r})
        if reasons:
            review.append({"question": d["question"], "reasons": reasons})

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
    """Segment pages, then run reader A and reader B on every answer in parallel."""
    ep_a = llm.resolve("reader_a")
    if ep_a is None:
        raise RuntimeError("no reader model is reachable")
    ep_b = llm.resolve("reader_b", exclude=(ep_a.name,))
    ep_c = llm.resolve("reader_c", exclude=(ep_a.name, ep_b.name if ep_b else ""))
    crops = readers.segment(pages, questions, llm.resolve("segmenter"))

    def read_one(q: Question):
        # Fall back to whole pages if the segmenter did not locate this answer
        imgs = crops.get(q.id) or pages
        a = readers.read_general(ep_a, q, imgs)
        b = readers.read_ocr(ep_b, q, imgs) if ep_b else Reading()
        agreed = readers.agree(q.kind, a, b)
        sim = readers.text_similarity(a.value, b.value) if q.kind == "subjective" and b.value else None
        if q.kind == "subjective" and sim is not None:
            agreed = sim >= routing.thresholds()["transcript_min_similarity"]
        reasons = routing.reader_reasons(q.kind, a, b, agreed, sim)
        final, c = a, Reading()

        # Abstention (one reader answered, the other blank/unclear/failed): ask a third reader.
        # If it confirms the answering reader, 2 of 3 agree → accept; a real conflict
        # (both answered, different values) always stays with the TA.
        if q.kind != "subjective" and ep_c and abstained(a) != abstained(b):
            answered = b if abstained(a) else a
            c = readers.read_ocr(ep_c, q, imgs)
            if readers.agree(q.kind, c, answered) is True:
                final = answered
                reasons = [r for r in reasons if r.startswith(("page ", "answer not located"))]
            else:
                reasons.append(f"tie-break reader did not confirm ({c.reader}: {c.value or c.status!r})")

        if q.id not in crops and crops:
            reasons.append("answer not located on the sheet (read from full page)")
        return q.id, {"a": a, "b": b, "c": c, "final": final, "reasons": reasons, "images": imgs}

    with ThreadPoolExecutor(WORKERS) as pool:
        reads = dict(pool.map(read_one, questions))
    models = {"reader_a": ep_a.version, "reader_b": ep_b.version if ep_b else "none",
              "reader_c": ep_c.version if ep_c else "none"}
    return reads, models


def abstained(r: Reading) -> bool:
    """A reader that gave no usable answer (blank / unclear / failed / empty)."""
    return r.status in ("blank", "unclear", "error", "missing") or not r.value


# ── Subjective grading ───────────────────────────────────────────────────────

def _grade_subjective(paper, questions, reads, pages):
    """Grader 1 (and grader 2 when a different model is up) per subjective answer."""
    subj = [q for q in questions if q.kind == "subjective"]
    if not subj:
        return 0.0, [], {}
    g1_ep = llm.resolve("grader_1")
    g2_ep = llm.resolve("grader_2", exclude=(g1_ep.name,)) if g1_ep else None
    rubrics = paper.get("subjectiveRubrics", [])
    texts = paper.get("subjectiveQuestions", [])
    per_q = paper.get("subjectiveQuestionMarks", {})
    default = float(paper.get("subjectiveMarks", 5))

    def grade_one(i_q):
        i, q = i_q
        r = reads[q.id]
        rubric = rubrics[i] if i < len(rubrics) else {}
        rubric_max = len(rubric.get("key_concepts", [])) * float(rubric.get("marks_per_concept", default))
        max_marks = float(per_q.get(q.id, rubric_max or default))
        q_text = texts[i] if i < len(texts) else f"Question {i + 1}"
        a_txt, b_txt = r["a"].value, r["b"].value

        # Blank answer: no grader call, zero marks, no review needed if both readers agree
        if r["a"].status == "blank" and r["b"].status in ("blank", "missing"):
            return _subj_row(q, q_text, "", max_marks, 0.0, None, None, [])
        if g1_ep is None:
            return _subj_row(q, q_text, a_txt, max_marks, 0.0, None, None, ["no grader model is reachable"])

        # Graders see the question, model answer, concepts, both transcripts and the crop
        args = (q_text, rubric, a_txt, b_txt, r.get("images") or pages, paper.get("subject", ""), max_marks)
        g1 = grade(g1_ep, *args)
        g2 = grade(g2_ep, *args) if g2_ep else None
        return _subj_row(q, q_text, a_txt, max_marks, g1.marks, g1, g2, routing.grader_reasons(g1, g2))

    with ThreadPoolExecutor(WORKERS) as pool:
        detail = list(pool.map(grade_one, enumerate(subj)))
    models = {"grader_1": g1_ep.version if g1_ep else "none", "grader_2": g2_ep.version if g2_ep else "none"}
    return sum(d["marks_earned"] for d in detail), detail, models


def _subj_row(q, q_text, answer, max_marks, marks, g1, g2, reasons) -> dict:
    """Subjective detail row in the legacy shape + per-concept evidence."""
    decisions = g1.decisions if g1 else []
    return {
        "question": q.id, "question_text": q_text, "student_answer": answer[:2000] or None,
        "marks_available": max_marks, "marks_earned": marks,
        "status": "graded_by_llm" if answer else "unanswered",
        "concepts_found": [d.concept for d in decisions if d.present],
        "concepts_missing": [d.concept for d in decisions if not d.present],
        "mandatory_met": g1.mandatory_met if g1 else True,
        "feedback": "; ".join(f"{d.concept}: \"{d.evidence}\"" for d in decisions if d.present),
        "concepts": [asdict(d) for d in decisions],
        "second_grader_marks": g2.marks if g2 else None,
        "graders": [g.version for g in (g1, g2) if g],
        "_grader_reasons": reasons,
    }
