# evaluator.py — evaluates one submission (one-shot, or in two stages for the teacher's batch: batch_runner.py).
#
# Flow: load submission + paper → two-reader pipeline (app/pipeline) when models
# are reachable, else the legacy single-model Ollama path → save → log to MLflow.

from __future__ import annotations

import asyncio
import json
import os
import tempfile
import time
import traceback
from datetime import datetime, timezone
from typing import Dict

from bson import ObjectId

from app.config import settings
from app.db.mongodb import papers_col, submissions_col
from app.pipeline import llm, orchestrator
from app.pipeline.scoring import grade_mcq, grade_numerical
from app.services.ollama_engine import OLLAMA_MODEL, OllamaEngine
from app.services.omr_engine import OMREngine
from app.services.pdf_utils import is_pdf, parse_mcq_text, pdf_extract_text, pdf_to_image
from app.services.subjective_grader import (
    OLLAMA_LLM_MODEL,
    grade_subjective_question,
    grade_with_template,
)

# One engine instance each, shared by all requests
_omr = OMREngine()
_ollama = OllamaEngine()


async def read_submission(submission_id: str) -> None:
    """Batch stage 1: read the sheet and store the readings (status "read"); grading follows in stage 2 via
    evaluate_submission. Sheets not read by the model pipeline (legacy path) are evaluated fully here."""
    try:
        sub = await submissions_col().find_one({"_id": ObjectId(submission_id)})
        paper = await papers_col().find_one({"_id": ObjectId(sub["paper_id"])}) if sub else None
        if not paper:
            return await _set_error(ObjectId(submission_id), "Paper not found in database")
        sheet_type = sub.get("sheet_type", "omr")
        if not _use_pipeline(sheet_type):
            return await evaluate_submission(submission_id)
        files = sub.get("file_paths") or [sub.get("file_path", "")]
        state = await asyncio.to_thread(orchestrator.read_sheet, paper, files, sheet_type)
        await submissions_col().update_one({"_id": sub["_id"]}, {"$set": {"status": "read", "read_state": state}})
    except Exception as exc:
        traceback.print_exc()
        await _set_error(ObjectId(submission_id), str(exc))


async def evaluate_submission(submission_id: str) -> None:
    """Evaluate one submission end to end and persist the result."""
    t0 = time.time()
    try:
        # Load the submission and its paper
        sub = await submissions_col().find_one({"_id": ObjectId(submission_id)})
        if not sub:
            return print(f"❌ Evaluator: submission {submission_id} not found")
        paper = await papers_col().find_one({"_id": ObjectId(sub["paper_id"])})
        if not paper:
            return await _set_error(sub["_id"], "Paper not found in database")

        # Question counts for this paper type
        ptype = paper.get("type", "mcq")
        n_mcq = int(paper.get("mcqCount", 0))
        n_num = int(paper.get("numericalCount", 0)) if "numerical" in ptype else 0
        n_subj = int(paper.get("subjectiveCount", 0)) if "subjective" in ptype else 0
        sheet_type = sub.get("sheet_type", "omr")
        files = sub.get("file_paths") or [sub.get("file_path", "")]
        print(f"\n═══ Evaluating {sub.get('roll_no', '?')} | {paper['name']} | {ptype} | {sheet_type} | {len(files)} page(s)")

        # Two-reader pipeline when models are up (OMR needs none); else legacy Ollama path
        if _use_pipeline(sheet_type):
            # Batch evaluation: the sheet was read in stage 1 (read_submission) → only grade it now
            if sub.get("read_state") is not None:
                out = await asyncio.to_thread(orchestrator.grade_sheet, paper, sub["read_state"])
            else:
                out = await asyncio.to_thread(orchestrator.run, paper, files, sheet_type)
            mcq_score, n_correct, mcq_detail = out["mcq_score"], out["n_correct"], out["mcq_detail"]
            num_score, num_detail = out["numerical_score"], out["numerical_detail"]
            subj_score, subj_detail = out["subjective_score"], out["subjective_detail"]
            engine, confidence, read_latency, llm_latency = "pipeline_v2", 1.0, out["latency_s"], 0.0
        else:
            out = None
            answers, confidence, engine, read_latency = _extract_all(files, sheet_type, n_mcq, n_num, n_subj)
            mcq_score, n_correct, mcq_detail = grade_mcq(answers, paper, n_mcq)
            num_score, num_detail = grade_numerical(answers, paper, n_num)
            subj_score, subj_detail, llm_latency = _grade_subjective(answers, paper, n_subj)

        # Totals (+ how many questions a TA must check, incl. random quality checks of written answers)
        total = mcq_score + num_score + subj_score
        max_score = float(paper.get("totalMarks", n_mcq + n_num))
        review = add_spot_checks(submission_id, subj_detail, list(out["review"]) if out else [],
                                 settings.EVALIFY_SPOT_CHECK_RATE)
        result = {
            "mcqScore": mcq_score, "numericalScore": num_score, "subjectiveScore": subj_score,
            "totalScore": total, "maxScore": max_score,
            "percentage": round(total / max_score * 100, 1) if max_score > 0 else 0.0,
            "engine": engine, "ocrConfidence": round(confidence, 3), "sheetType": sheet_type,
            "needsReview": bool(review), "reviewCount": len(review),
        }
        print(f"  Score: {total}/{max_score} ({result['percentage']}%) via {engine}; "
              f"{len(review)} question(s) flagged for TA review")

        # Save to MongoDB
        await submissions_col().update_one({"_id": sub["_id"]}, {"$set": {
            "status": "evaluated", "result": result,
            "mcqDetail": mcq_detail, "numericalDetail": num_detail, "subjectiveDetail": subj_detail,
            "review": review, "pipeline": {k: out[k] for k in ("models", "quality", "prompt_version", "usage") if k in out} if out else None,
            "evaluatedAt": datetime.now(timezone.utc).isoformat(),
        }, "$unset": {"read_state": ""}})

        # Log metrics + model versions to MLflow (never fails the evaluation)
        _log_mlflow(submission_id, paper, ptype, sheet_type, engine, n_mcq, n_num, n_subj, {
            "mcq_score": mcq_score, "numerical_score": num_score, "subjective_score": subj_score,
            "total_score": total, "max_score": max_score,
            "accuracy": n_correct / n_mcq if n_mcq else 0,
            "eval_latency_s": round(time.time() - t0, 3), "ollama_latency_s": read_latency,
            "llm_latency_s": llm_latency, "ocr_confidence": confidence,
            "review_count": len(review), "questions": n_mcq + n_num + n_subj,
            # Tokens used by all model calls for this sheet (0 for OMR / legacy runs)
            **{k: (out or {}).get("usage", {}).get(k, 0) for k in ("prompt_tokens", "completion_tokens", "total_tokens")},
        }, out)

    except Exception as exc:
        traceback.print_exc()
        await _set_error(ObjectId(submission_id), str(exc))


# ── Answer extraction ────────────────────────────────────────────────────────

def _extract_all(files: list, sheet_type: str, n_mcq: int, n_num: int, n_subj: int):
    """Read every page; earlier pages win when a question appears twice."""
    merged: Dict[str, str] = {}
    confs, engine, latency = [], "", 0.0
    for path in files:
        answers, conf, engine, t = _extract_page(path, sheet_type, n_mcq, n_num, n_subj)
        for q, a in answers.items():
            merged.setdefault(q, a)
        confs.append(conf)
        latency += t
    return merged, (sum(confs) / len(confs) if confs else 0.0), engine, latency


def _extract_page(path: str, sheet_type: str, n_mcq: int, n_num: int, n_subj: int):
    """Route one page to OMR or the handwriting reader. Returns (answers, conf, engine, latency)."""
    if not path or not os.path.exists(path):
        raise ValueError(f"Answer sheet file not found at '{path}'")

    # Bubble sheet → OpenCV
    if sheet_type == "omr":
        img = pdf_to_image(path, dpi=200) if is_pdf(path) else path
        return _omr.process_image(img, n_mcq), 1.0, "opencv_omr", 0.0

    if sheet_type != "handwritten":
        raise ValueError(f"Unknown sheet_type '{sheet_type}'. Must be 'omr' or 'handwritten'.")

    # Typed PDF with a text layer → parse the text directly (MCQ/numerical only)
    if is_pdf(path):
        text = pdf_extract_text(path)
        if text.strip() and n_subj == 0:
            return parse_mcq_text(text, n_mcq), 1.0, "pdf_text_extract", 0.0
        path = pdf_to_image(path, dpi=200)

    # Handwriting → vision model
    answers, conf, latency = _ollama.extract(path, n_mcq, n_num, n_subj)
    return answers, conf, f"ollama_{_ollama.mode}", latency


# ── Grading ──────────────────────────────────────────────────────────────────

def _grade_subjective(answers: Dict[str, str], paper: dict, n_subj: int):
    """Grade each subjective answer with the LLM. Returns (score, detail, latency_s)."""
    questions = paper.get("subjectiveQuestions", [])
    rubrics = paper.get("subjectiveRubrics", [])
    templates = paper.get("subjectivePromptTemplates", []) or []
    per_q = paper.get("subjectiveQuestionMarks", {})
    default = float(paper.get("subjectiveMarks", 5))

    score, detail, latency = 0.0, [], 0.0
    for i in range(n_subj):
        q = f"S{i + 1}"
        rubric = rubrics[i] if i < len(rubrics) else {}
        q_text = questions[i] if i < len(questions) else f"Question {i + 1}"
        answer = answers.get(q, "").strip()

        # Max marks: per-question override, else rubric total, else default
        rubric_max = len(rubric.get("key_concepts", [])) * float(rubric.get("marks_per_concept", default))
        marks = float(per_q.get(q, rubric_max or default))

        # Prefer the teacher's stored prompt template when there is one
        if i < len(templates) and templates[i]:
            g, t = grade_with_template(templates[i], answer, rubric, paper.get("subject", ""))
        else:
            g, t = grade_subjective_question(q_text, answer, rubric, paper.get("subject", ""))
        latency += t

        earned = min(float(g.get("marks_awarded", 0)), marks)
        score += earned
        detail.append({
            "question": q, "question_text": q_text, "student_answer": answer[:500] or None,
            "marks_available": marks, "marks_earned": earned,
            "status": "graded_by_llm" if answer else "unanswered",
            "concepts_found": g.get("concepts_found", []), "concepts_missing": g.get("concepts_missing", []),
            "mandatory_met": g.get("mandatory_concepts_met", True), "feedback": g.get("feedback", ""),
            "ocr_issues": g.get("ocr_issues_detected", False), "llm_detail": g,
        })
    return score, detail, round(latency, 3)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _use_pipeline(sheet_type: str) -> bool:
    """Pipeline unless forced legacy; handwriting additionally needs a live reader model."""
    mode = os.environ.get("EVALIFY_PIPELINE", "auto")
    if mode == "legacy":
        return False
    return mode == "v2" or sheet_type == "omr" or llm.any_live()


def _log_mlflow(submission_id, paper, ptype, sheet_type, engine, n_mcq, n_num, n_subj, metrics, out=None):
    """Log one run (params, metrics, full per-question outputs) and model versions to MLflow."""
    try:
        from app.db.mlflow_logger import log_evaluation_run, register_model_version
    except Exception:
        return
    counts = {"mcq_count": n_mcq, "numerical_count": n_num, "subjective_count": n_subj}

    # Pipeline run: model repo@revision per role + prompt version; every output as a JSON artifact
    if out:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(out, fh, default=str, indent=1)
        log_evaluation_run(submission_id=submission_id, paper_id=str(paper["_id"]), paper_type=ptype,
                           metrics=metrics, artifacts={"outputs": fh.name},
                           params={"engine": engine, "sheet_type": sheet_type,
                                   "prompt_version": out["prompt_version"], **out["models"], **counts})
        os.unlink(fh.name)
        return

    # Legacy run: Ollama model tags
    run_id = log_evaluation_run(
        submission_id=submission_id, paper_id=str(paper["_id"]), paper_type=ptype, metrics=metrics,
        params={"engine": engine, "sheet_type": sheet_type, "ollama_mode": _ollama.mode,
                "vision_model": OLLAMA_MODEL, "grader_model": OLLAMA_LLM_MODEL, **counts})
    # Track which model produced these scores in the Model Registry
    if run_id and _ollama.mode == "real":
        register_model_version("evalify-vision-ocr", run_id, description=f"Vision OCR: {OLLAMA_MODEL}",
                               tags={"ollama_tag": OLLAMA_MODEL, "engine": engine})
        if n_subj:
            register_model_version("evalify-subjective-grader", run_id,
                                   description=f"Grader: {OLLAMA_LLM_MODEL}",
                                   tags={"ollama_tag": OLLAMA_LLM_MODEL})


# ── Random quality checks (written answers) ──────────────────────────────────

def spot_check_pick(submission_id: str, qid: str, rate: float) -> bool:
    """Reproducible random pick: the same submission + question always gives the same answer."""
    import hashlib
    h = int(hashlib.sha256(f"{submission_id}|{qid}".encode()).hexdigest()[:8], 16)
    return h / 0xFFFFFFFF < rate


def add_spot_checks(submission_id: str, subj_rows: list, review: list, rate: float) -> list:
    """Send a random share of auto-accepted written answers to a TA ("random quality check"); returns the review list."""
    for r in subj_rows:
        if not r.get("needs_review") and r.get("student_answer", "x") is not None and spot_check_pick(submission_id, r["question"], rate):
            r.update(needs_review=True, review_reason="random quality check",
                     review_reasons=[*(r.get("review_reasons") or []), "random quality check"])
            review.append({"question": r["question"], "reason": "random quality check", "reasons": ["random quality check"]})
    return review


async def _set_error(sub_id, message: str) -> None:
    """Mark a submission as failed with a message."""
    await submissions_col().update_one({"_id": sub_id}, {"$set": {"status": "error", "error": message}})
    print(f"❌ Evaluator: {sub_id} → error: {message}")
