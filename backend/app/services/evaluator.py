# evaluator.py — Orchestrates answer-sheet evaluation for MCQ papers.
#
# Flow (triggered as a FastAPI BackgroundTask):
#   1. Load submission + paper from MongoDB.
#   2. Choose engine based on submission's `sheet_type`:
#        "omr"         → OMREngine   (OpenCV bubble detection)
#        "handwritten" → TrOCREngine (Handwriting OCR)
#   3. Extract answers from the uploaded image file.
#   4. Grade extracted answers against the paper's answer key.
#   5. Persist ResultSummary into the submission document.
#   6. Log metrics to MLflow.

from __future__ import annotations
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any

from bson import ObjectId

from app.db.mongodb import papers_col, submissions_col
from app.db.mlflow_logger import log_evaluation_run
from app.services.omr_engine import OMREngine
from app.services.trocr_engine import TrOCREngine
from app.services.pdf_utils import is_pdf, pdf_to_image, pdf_extract_text
from app.services.pdf_extractor import _parse_answers as parse_mcq_text

# ── Singleton engines (instantiated once per process) ─────────────────────────
# Avoids reloading OpenCV / TrOCR model on every request.
_omr   = OMREngine()
_trocr = TrOCREngine()


# ── Main evaluation entry-point ───────────────────────────────────────────────

async def evaluate_submission(submission_id: str) -> None:
    """
    Background task: evaluate one submission and persist the result.
    Called by submissions router after the file is saved.
    """
    t0 = time.time()

    try:
        # 1. Fetch submission ──────────────────────────────────────────────────
        sub = await submissions_col().find_one({"_id": ObjectId(submission_id)})
        if not sub:
            print(f"❌ Evaluator: submission {submission_id} not found")
            return

        # 2. Fetch associated paper ────────────────────────────────────────────
        paper = await papers_col().find_one({"_id": ObjectId(sub["paper_id"])})
        if not paper:
            await _set_error(sub["_id"], "Paper not found in database")
            return

        roll_no    = sub.get("roll_no", "?")
        sheet_type = sub.get("sheet_type", "omr")
        # Support both legacy single-file and new multi-page submissions
        file_paths = sub.get("file_paths") or [sub.get("file_path", "")]
        mcq_count  = int(paper.get("mcqCount", 0))

        print(
            f"🔄 Evaluator: [{roll_no}] paper='{paper['name']}' "
            f"sheet_type={sheet_type} mcq_count={mcq_count} pages={len(file_paths)}"
        )

        # 3. Extract answers — process each page, merge results ───────────────
        extracted, confidence, engine_used = _extract_answers_multi(
            file_paths, sheet_type, mcq_count
        )

        # 4. Grade MCQ section ─────────────────────────────────────────────────
        cfg = paper.get("config", {})
        negative_marking = cfg.get("negativeMaking", False)   # note: stored as "negativeMaking"
        # Determine which questions have negative marking (None = all)
        neg_questions = None
        if negative_marking and cfg.get("negativeMarkingScope") == "per_question":
            neg_questions = cfg.get("negativeMarkingQuestions", [])

        mcq_score, correct_count, mcq_detail = _grade_mcq(
            extracted_answers          = extracted,
            answer_key                 = paper.get("mcqAnswers", {}),
            mcq_count                  = mcq_count,
            default_marks              = float(paper.get("mcqMarks", 1)),
            per_q_marks                = paper.get("mcqQuestionMarks", {}),
            negative_marking           = negative_marking,
            negative_marking_questions = neg_questions,
        )

        # 5. Build result summary ──────────────────────────────────────────────
        max_score = float(paper.get("totalMarks", mcq_count))
        pct       = round((mcq_score / max_score) * 100, 1) if max_score > 0 else 0.0

        result = {
            "mcqScore":        mcq_score,
            "numericalScore":  0.0,
            "subjectiveScore": 0.0,
            "totalScore":      mcq_score,
            "maxScore":        max_score,
            "percentage":      pct,
            "engine":          engine_used,
            "ocrConfidence":   round(confidence, 3),
            "sheetType":       sheet_type,
        }

        # 6. Persist to MongoDB ────────────────────────────────────────────────
        await submissions_col().update_one(
            {"_id": sub["_id"]},
            {"$set": {
                "status":      "evaluated",
                "result":      result,
                "mcqDetail":   mcq_detail,
                "evaluatedAt": datetime.now(timezone.utc).isoformat(),
            }}
        )

        # 7. Log to MLflow ─────────────────────────────────────────────────────
        latency = round(time.time() - t0, 3)
        log_evaluation_run(
            submission_id = submission_id,
            paper_id      = str(paper["_id"]),
            paper_type    = paper.get("type", "mcq"),
            metrics = {
                "score":          mcq_score,
                "max_score":      max_score,
                "accuracy":       correct_count / mcq_count if mcq_count > 0 else 0,
                "latency_s":      latency,
                "ocr_confidence": confidence,
            },
            params = {
                "engine":         engine_used,
                "sheet_type":     sheet_type,
                "mcq_count":      mcq_count,
                "trocr_mode":     _trocr.mode,
            },
        )

        print(
            f"✅ Evaluator: [{roll_no}] done — "
            f"score={mcq_score}/{max_score} ({pct}%) engine={engine_used} t={latency}s"
        )

    except Exception as exc:
        import traceback
        traceback.print_exc()
        try:
            await _set_error(ObjectId(submission_id), str(exc))
        except Exception:
            pass


# ── Multi-page wrapper ────────────────────────────────────────────────────────

def _extract_answers_multi(
    file_paths: list,
    sheet_type: str,
    mcq_count: int,
) -> tuple[Dict[str, str], float, str]:
    """
    Process one or more image pages and merge extracted answers.
    Later pages fill in questions not found on earlier pages.
    Returns (merged_answers, avg_confidence, engine_used).
    """
    merged: Dict[str, str] = {}
    confidences = []
    engine_used = ""

    for path in file_paths:
        answers, conf, eng = _extract_answers(path, sheet_type, mcq_count)
        # Fill in only questions not yet answered by a previous page
        for q, a in answers.items():
            if q not in merged:
                merged[q] = a
        confidences.append(conf)
        engine_used = eng  # use last engine name

    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    return merged, avg_conf, engine_used


# ── Engine dispatch ───────────────────────────────────────────────────────────

def _extract_answers(
    img_path: str,
    sheet_type: str,
    mcq_count: int,
) -> tuple[Dict[str, str], float, str]:
    """
    Route to the correct engine based on sheet_type.
    Returns (extracted_answers, confidence, engine_name).
    Raises ValueError with a human-readable message on failure.
    """
    file_exists = img_path and os.path.exists(img_path)

    if not file_exists:
        raise ValueError(f"Answer sheet file not found at '{img_path}'")

    if sheet_type == "omr":
        # ── OMR: OpenCV bubble detection ──────────────────────────────────────
        # If student uploaded a PDF, render the first page to PNG first.
        engine_used = "opencv_omr"
        proc_path = img_path
        if is_pdf(img_path):
            proc_path = pdf_to_image(img_path, dpi=200)
            print(f"  OMR: converted PDF → {proc_path}")
        answers = _omr.process_image(proc_path, mcq_count)
        return answers, 1.0, engine_used

    elif sheet_type == "handwritten":
        # ── Handwritten: try text extraction first, fall back to TrOCR ────────
        if is_pdf(img_path):
            raw_text = pdf_extract_text(img_path)
            if raw_text.strip():
                # PDF has selectable text (typed / digital sheet) — parse directly
                answers = parse_mcq_text(raw_text, mcq_count)
                engine_used = "pdf_text_extract"
                print(f"  Handwritten: PDF has text, extracted {len(answers)} answers directly")
                return answers, 1.0, engine_used
            else:
                # Scanned/image PDF — render to PNG and run TrOCR
                img_path = pdf_to_image(img_path, dpi=200)
                print(f"  Handwritten: PDF is scanned, converted → {img_path}")

        engine_used = f"trocr_{_trocr.mode}"
        text, confidence = _trocr.extract_text(img_path)
        answers = _trocr.parse_mcq_results(text, mcq_count)
        return answers, confidence, engine_used

    else:
        raise ValueError(f"Unknown sheet_type '{sheet_type}'. Must be 'omr' or 'handwritten'.")


# ── Grading ───────────────────────────────────────────────────────────────────

def _grade_mcq(
    extracted_answers:          Dict[str, str],
    answer_key:                 Dict[str, str],
    mcq_count:                  int,
    default_marks:              float,
    per_q_marks:                Dict[str, Any],
    negative_marking:           bool,
    negative_marking_questions: list | None = None,  # None = apply to all questions
) -> tuple[float, int, list]:
    """
    Compare extracted answers against the answer key.
    Returns (total_mcq_score, correct_count, per_question_detail_list).
    """
    score         = 0.0
    correct_count = 0
    detail        = []

    for i in range(1, mcq_count + 1):
        q_id        = f"Q{i}"
        student_ans = extracted_answers.get(q_id)
        correct_ans = answer_key.get(q_id)

        # Per-question marks take priority; fall back to paper-level default
        q_marks = float(per_q_marks.get(q_id, default_marks))

        # Negative marking applies to this question when:
        #   - negative_marking is globally on, AND
        #   - either scope is "all" (negative_marking_questions is None)
        #     or this specific question is in the per-question list
        apply_negative = negative_marking and (
            negative_marking_questions is None or q_id in negative_marking_questions
        )

        if student_ans is None:
            status = "unanswered"
            earned = 0.0
        elif student_ans == correct_ans:
            status = "correct"
            earned = q_marks
            correct_count += 1
        else:
            status = "wrong"
            earned = -(q_marks / 4) if apply_negative else 0.0

        score += earned
        detail.append({
            "question":        q_id,
            "student_answer":  student_ans,
            "correct_answer":  correct_ans,
            "status":          status,
            "marks_available": q_marks,
            "marks_earned":    earned,
        })

    # Clamp score to 0 (negative marking can't push total below 0)
    return max(0.0, score), correct_count, detail


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _set_error(sub_id, message: str) -> None:
    """Mark a submission as errored in MongoDB."""
    await submissions_col().update_one(
        {"_id": sub_id},
        {"$set": {"status": "error", "error": message}}
    )
    print(f"❌ Evaluator: marked submission {sub_id} as error — {message}")
