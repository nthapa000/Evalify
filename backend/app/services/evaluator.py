# evaluator.py — Orchestrates answer-sheet evaluation for all paper types.
#
# Paper types handled:
#   mcq                        → Type 1 (OMR or handwritten MCQ)
#   mcq_numerical              → Type 2 (handwritten MCQ + Numerical)
#   mcq_numerical_subjective   → Type 3 (future)
#
# Flow (triggered as a FastAPI BackgroundTask):
#   1. Load submission + paper from MongoDB.
#   2. Choose engine based on submission's `sheet_type`:
#        "omr"         → OMREngine   (OpenCV bubble detection)
#        "handwritten" → OllamaEngine (vision model extraction)
#   3. Extract answers from the uploaded image file(s).
#   4. Grade MCQ section.
#   5. Grade Numerical section (Type 2+).
#   6. Persist ResultSummary into the submission document.
#   7. Log metrics to MLflow (includes Ollama latency).

from __future__ import annotations
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any

from bson import ObjectId

from app.db.mongodb import papers_col, submissions_col
from app.services.omr_engine import OMREngine
from app.services.ollama_engine import OllamaEngine
from app.services.pdf_utils import is_pdf, pdf_to_image, pdf_extract_text
from app.services.pdf_extractor import _parse_answers as parse_mcq_text
from app.services.subjective_grader import grade_subjective_question, grade_with_template

# ── Singleton engines ─────────────────────────────────────────────────────────
_omr    = OMREngine()
_ollama = OllamaEngine()


# ── Main evaluation entry-point ───────────────────────────────────────────────

async def evaluate_submission(submission_id: str) -> None:
    """Background task: evaluate one submission and persist the result."""
    t0 = time.time()

    try:
        sub = await submissions_col().find_one({"_id": ObjectId(submission_id)})
        if not sub:
            print(f"❌ Evaluator: submission {submission_id} not found")
            return

        paper = await papers_col().find_one({"_id": ObjectId(sub["paper_id"])})
        if not paper:
            await _set_error(sub["_id"], "Paper not found in database")
            return

        roll_no          = sub.get("roll_no", "?")
        sheet_type       = sub.get("sheet_type", "omr")
        file_paths       = sub.get("file_paths") or [sub.get("file_path", "")]
        paper_type       = paper.get("type", "mcq")
        mcq_count        = int(paper.get("mcqCount", 0))
        numerical_count  = int(paper.get("numericalCount", 0)) if "numerical" in paper_type else 0
        subjective_count = int(paper.get("subjectiveCount", 0)) if "subjective" in paper_type else 0

        _print_header(roll_no, paper['name'], paper_type, sheet_type,
                      mcq_count, numerical_count, subjective_count, len(file_paths))

        # ── Extract answers ───────────────────────────────────────────────────
        extracted, confidence, engine_used, ollama_latency = _extract_answers_multi(
            file_paths, sheet_type, mcq_count, numerical_count, subjective_count
        )
        _print_extracted(extracted, mcq_count, numerical_count, subjective_count)

        # ── Grade MCQ ─────────────────────────────────────────────────────────
        cfg              = paper.get("config", {})
        negative_marking = cfg.get("negativeMaking", False)
        neg_questions    = None
        if negative_marking and cfg.get("negativeMarkingScope") == "per_question":
            neg_questions = cfg.get("negativeMarkingQuestions", [])

        mcq_answers = {k: v for k, v in extracted.items() if k.startswith("Q")}
        mcq_score, correct_count, mcq_detail = _grade_mcq(
            extracted_answers          = mcq_answers,
            answer_key                 = paper.get("mcqAnswers", {}),
            mcq_count                  = mcq_count,
            default_marks              = float(paper.get("mcqMarks", 1)),
            per_q_marks                = paper.get("mcqQuestionMarks", {}),
            negative_marking           = negative_marking,
            negative_marking_questions = neg_questions,
        )

        # ── Grade Numerical (Type 2+) ─────────────────────────────────────────
        numerical_score  = 0.0
        numerical_detail = []
        if numerical_count > 0:
            num_answers = {k: v for k, v in extracted.items() if k.startswith("N")}
            numerical_score, numerical_detail = _grade_numerical(
                extracted_numerical = num_answers,
                answer_key          = paper.get("numericalAnswers", {}),
                numerical_count     = numerical_count,
                default_marks       = float(paper.get("numericalMarks", 1)),
                per_q_marks         = paper.get("numericalQuestionMarks", {}),
            )

        # ── Grade Subjective (Type 3) ─────────────────────────────────────────
        subjective_score  = 0.0
        subjective_detail = []
        llm_latency       = 0.0
        if subjective_count > 0:
            subj_answers = {k: v for k, v in extracted.items() if k.startswith("S")}
            subjective_score, subjective_detail, llm_latency = _grade_subjective(
                extracted_subjective        = subj_answers,
                subjective_questions        = paper.get("subjectiveQuestions", []),
                subjective_rubrics          = paper.get("subjectiveRubrics", []),
                subjective_prompt_templates = paper.get("subjectivePromptTemplates", []),
                subjective_count            = subjective_count,
                default_marks               = float(paper.get("subjectiveMarks", 5)),
                per_q_marks                 = paper.get("subjectiveQuestionMarks", {}),
                subject                     = paper.get("subject", ""),
            )

        # ── Print grading table ───────────────────────────────────────────────
        _print_grading_table(mcq_detail, numerical_detail, subjective_detail)

        # ── Build result ──────────────────────────────────────────────────────
        total_score = mcq_score + numerical_score + subjective_score
        max_score   = float(paper.get("totalMarks", mcq_count + numerical_count))
        pct         = round((total_score / max_score) * 100, 1) if max_score > 0 else 0.0

        _print_score_summary(mcq_score, numerical_score, subjective_score,
                             total_score, max_score, pct,
                             engine_used, ollama_latency, llm_latency, confidence)

        result = {
            "mcqScore":        mcq_score,
            "numericalScore":  numerical_score,
            "subjectiveScore": subjective_score,
            "totalScore":      total_score,
            "maxScore":        max_score,
            "percentage":      pct,
            "engine":          engine_used,
            "ocrConfidence":   round(confidence, 3),
            "sheetType":       sheet_type,
        }

        # ── Persist ───────────────────────────────────────────────────────────
        await submissions_col().update_one(
            {"_id": sub["_id"]},
            {"$set": {
                "status":            "evaluated",
                "result":            result,
                "mcqDetail":         mcq_detail,
                "numericalDetail":   numerical_detail,
                "subjectiveDetail":  subjective_detail,
                "evaluatedAt":       datetime.now(timezone.utc).isoformat(),
            }}
        )

        # ── MLflow logging ────────────────────────────────────────────────────
        latency = round(time.time() - t0, 3)
        try:
            from app.db.mlflow_logger import log_evaluation_run
        except Exception:
            log_evaluation_run = lambda **kw: None  # noqa: E731

        log_evaluation_run(
            submission_id = submission_id,
            paper_id      = str(paper["_id"]),
            paper_type    = paper_type,
            metrics = {
                "mcq_score":          mcq_score,
                "numerical_score":    numerical_score,
                "subjective_score":   subjective_score,
                "total_score":        total_score,
                "max_score":          max_score,
                "accuracy":           correct_count / mcq_count if mcq_count > 0 else 0,
                "eval_latency_s":     latency,
                "ollama_latency_s":   ollama_latency,
                "llm_latency_s":      llm_latency,
                "ocr_confidence":     confidence,
            },
            params = {
                "engine":            engine_used,
                "sheet_type":        sheet_type,
                "mcq_count":         mcq_count,
                "numerical_count":   numerical_count,
                "subjective_count":  subjective_count,
                "ollama_mode":       _ollama.mode,
            },
        )

    except Exception as exc:
        import traceback
        traceback.print_exc()
        try:
            await _set_error(ObjectId(submission_id), str(exc))
        except Exception:
            pass


# ── Multi-page extraction wrapper ─────────────────────────────────────────────

def _extract_answers_multi(
    file_paths:       list,
    sheet_type:       str,
    mcq_count:        int,
    numerical_count:  int = 0,
    subjective_count: int = 0,
) -> tuple[Dict[str, str], float, str, float]:
    """
    Process one or more image pages, merge results.
    Later pages fill in questions not found on earlier pages.
    Returns (merged_answers, avg_confidence, engine_used, total_ollama_latency).
    """
    merged: Dict[str, str] = {}
    confidences = []
    engine_used = ""
    total_ollama_latency = 0.0

    for path in file_paths:
        answers, conf, eng, latency = _extract_answers(
            path, sheet_type, mcq_count, numerical_count, subjective_count
        )
        for q, a in answers.items():
            if q not in merged:
                merged[q] = a
        confidences.append(conf)
        engine_used = eng
        total_ollama_latency += latency

    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    return merged, avg_conf, engine_used, total_ollama_latency


# ── Engine dispatch ───────────────────────────────────────────────────────────

def _extract_answers(
    img_path:         str,
    sheet_type:       str,
    mcq_count:        int,
    numerical_count:  int = 0,
    subjective_count: int = 0,
) -> tuple[Dict[str, str], float, str, float]:
    """
    Route to the correct engine. Returns (answers, confidence, engine_name, ollama_latency).
    answers keys: Q1..Qn (MCQ) | N1..Nm (Numerical) | S1..Ss (Subjective).
    """
    if not img_path or not os.path.exists(img_path):
        raise ValueError(f"Answer sheet file not found at '{img_path}'")

    if sheet_type == "omr":
        proc_path = img_path
        if is_pdf(img_path):
            proc_path = pdf_to_image(img_path, dpi=200)
            print(f"  OMR: converted PDF → {proc_path}")
        answers = _omr.process_image(proc_path, mcq_count)
        print(f"  OMR: detected answers = {answers}")
        return answers, 1.0, "opencv_omr", 0.0

    elif sheet_type == "handwritten":
        if is_pdf(img_path):
            raw_text = pdf_extract_text(img_path)
            if raw_text.strip() and subjective_count == 0:
                answers = parse_mcq_text(raw_text, mcq_count)
                print(f"  Handwritten: PDF text extracted {len(answers)} answers")
                return answers, 1.0, "pdf_text_extract", 0.0
            img_path = pdf_to_image(img_path, dpi=200)
            print(f"  Handwritten: scanned PDF → {img_path}")

        if subjective_count > 0:
            answers, conf, latency = _ollama.extract_mcq_numerical_subjective(
                img_path, mcq_count, numerical_count, subjective_count
            )
            return answers, conf, f"ollama_{_ollama.mode}_mcq_numerical_subjective", latency
        elif numerical_count > 0:
            answers, conf, latency = _ollama.extract_mcq_numerical(
                img_path, mcq_count, numerical_count
            )
            return answers, conf, f"ollama_{_ollama.mode}_mcq_numerical", latency
        else:
            answers, conf, latency = _ollama.extract_mcq(img_path, mcq_count)
            return answers, conf, f"ollama_{_ollama.mode}", latency

    else:
        raise ValueError(f"Unknown sheet_type '{sheet_type}'. Must be 'omr' or 'handwritten'.")


# ── MCQ grading ───────────────────────────────────────────────────────────────

def _normalise_mcq_answer(ans: str | None) -> frozenset:
    """
    "A,C" → frozenset({"A", "C"})
    None  → frozenset()
    """
    if not ans:
        return frozenset()
    return frozenset(a.strip().upper() for a in ans.split(",") if a.strip())


def _grade_mcq(
    extracted_answers:          Dict[str, str],
    answer_key:                 Dict[str, str],
    mcq_count:                  int,
    default_marks:              float,
    per_q_marks:                Dict[str, Any],
    negative_marking:           bool,
    negative_marking_questions: list | None = None,
) -> tuple[float, int, list]:
    """
    Exact-set MCQ grading.
    Rules: over-fill → wrong, under-fill → wrong, exact match → correct.
    Returns (total_score, correct_count, detail_list).
    """
    score         = 0.0
    correct_count = 0
    detail        = []

    for i in range(1, mcq_count + 1):
        q_id = f"Q{i}"
        student_set = _normalise_mcq_answer(extracted_answers.get(q_id))
        correct_set = _normalise_mcq_answer(answer_key.get(q_id))
        q_marks     = float(per_q_marks.get(q_id, default_marks))

        apply_neg = negative_marking and (
            negative_marking_questions is None or q_id in negative_marking_questions
        )

        if not student_set:
            status = "unanswered"
            earned = 0.0
        elif student_set == correct_set:
            status = "correct"
            earned = q_marks
            correct_count += 1
        elif student_set > correct_set:
            status = "wrong_overfill"
            earned = -(q_marks / 4) if apply_neg else 0.0
        elif student_set < correct_set:
            status = "wrong_underfill"
            earned = -(q_marks / 4) if apply_neg else 0.0
        else:
            status = "wrong"
            earned = -(q_marks / 4) if apply_neg else 0.0

        score += earned
        detail.append({
            "question":        q_id,
            "student_answer":  ",".join(sorted(student_set)) if student_set else None,
            "correct_answer":  ",".join(sorted(correct_set)) if correct_set else None,
            "status":          status,
            "marks_available": q_marks,
            "marks_earned":    earned,
        })

    return max(0.0, score), correct_count, detail


# ── Numerical grading ─────────────────────────────────────────────────────────

def _grade_numerical(
    extracted_numerical: Dict[str, str],
    answer_key:          Dict[str, Any],
    numerical_count:     int,
    default_marks:       float,
    per_q_marks:         Dict[str, Any],
) -> tuple[float, list]:
    """
    Exact-match numerical grading.

    answer_key values can be:
      list  — ["3", "3.0", "3.00"]  (multiple accepted answers)
      str   — "3.5"                  (single accepted answer, legacy)
      dict  — old tolerance format   (graceful fallback: uses "answer" field)

    A student answer earns full marks if it exactly matches (after stripping
    whitespace) any one value in the accepted list.
    Returns (total_score, detail_list).
    """
    score  = 0.0
    detail = []

    for i in range(1, numerical_count + 1):
        n_id          = f"N{i}"
        student_raw   = str(extracted_numerical.get(n_id, "")).strip()
        accepted_raw  = answer_key.get(n_id, [])
        q_marks       = float(per_q_marks.get(n_id, default_marks))

        # Normalise accepted answers to a list of stripped strings
        if isinstance(accepted_raw, list):
            accepted = [str(v).strip() for v in accepted_raw if str(v).strip()]
        elif isinstance(accepted_raw, dict):
            # Backwards compat with old tolerance format
            accepted = [str(accepted_raw.get("answer", "")).strip()]
        else:
            accepted = [str(accepted_raw).strip()]
        accepted = [a for a in accepted if a]

        if not student_raw:
            status = "unanswered"
            earned = 0.0
        elif student_raw in accepted:
            status = "correct"
            earned = q_marks
        else:
            status = "wrong"
            earned = 0.0

        score += earned
        detail.append({
            "question":         n_id,
            "student_answer":   student_raw or None,
            "accepted_answers": accepted,
            "status":           status,
            "marks_available":  q_marks,
            "marks_earned":     earned,
        })

    return score, detail


# ── Subjective grading (Type 3) ───────────────────────────────────────────────

def _grade_subjective(
    extracted_subjective:        Dict[str, str],
    subjective_questions:        list,
    subjective_rubrics:          list,
    subjective_count:            int,
    default_marks:               float,
    per_q_marks:                 Dict[str, Any],
    subject:                     str = "",
    subjective_prompt_templates: list | None = None,
) -> tuple[float, list, float]:
    """
    Grade each subjective question via Ollama LLM.

    subjective_questions — list of question texts  (index 0 = S1)
    subjective_rubrics   — list of rubric dicts    (index 0 = S1 rubric from RubricBuilder)
      each rubric: {key_concepts, mandatory_concepts, marks_per_concept, model_answer}

    Returns (total_score, detail_list, total_llm_latency_s).
    """
    total_score  = 0.0
    detail       = []
    total_latency = 0.0

    for i in range(1, subjective_count + 1):
        s_id    = f"S{i}"
        rubric  = subjective_rubrics[i - 1] if i - 1 < len(subjective_rubrics) else {}
        q_text  = (subjective_questions[i - 1]
                   if i - 1 < len(subjective_questions) else f"Question {i}")

        # Max marks: prefer rubric-derived, then per_q override, then default
        key_concepts      = rubric.get("key_concepts", [])
        marks_per_concept = float(rubric.get("marks_per_concept", default_marks))
        rubric_max        = len(key_concepts) * marks_per_concept if key_concepts else default_marks
        q_marks           = float(per_q_marks.get(s_id, rubric_max))

        student_ans = extracted_subjective.get(s_id, "").strip()

        template = (
            subjective_prompt_templates[i - 1]
            if subjective_prompt_templates and i - 1 < len(subjective_prompt_templates)
            else None
        )

        if template:
            grading_result, latency = grade_with_template(
                prompt_template = template,
                student_answer  = student_ans,
                rubric          = rubric,
                subject         = subject,
            )
        else:
            grading_result, latency = grade_subjective_question(
                question_text  = q_text,
                student_answer = student_ans,
                rubric         = rubric,
                subject        = subject,
            )
        total_latency += latency

        awarded = min(float(grading_result.get("marks_awarded", 0)), q_marks)
        total_score += awarded

        detail.append({
            "question":         s_id,
            "question_text":    q_text,
            "student_answer":   student_ans[:500] if student_ans else None,
            "marks_available":  q_marks,
            "marks_earned":     awarded,
            "status":           "graded_by_llm" if student_ans else "unanswered",
            "concepts_found":   grading_result.get("concepts_found", []),
            "concepts_missing": grading_result.get("concepts_missing", []),
            "mandatory_met":    grading_result.get("mandatory_concepts_met", True),
            "feedback":         grading_result.get("feedback", ""),
            "ocr_issues":       grading_result.get("ocr_issues_detected", False),
            "llm_detail":       grading_result,
        })

        print(f"  {s_id}: awarded {awarded}/{q_marks}  |  "
              f"found={grading_result.get('concepts_found', [])}  |  "
              f"{grading_result.get('feedback', '')[:80]}")

    return total_score, detail, round(total_latency, 3)


# ── Terminal print helpers ────────────────────────────────────────────────────

_W = 72  # table width

def _print_header(roll_no, paper_name, paper_type, sheet_type,
                  mcq_count, numerical_count, subjective_count, pages):
    print()
    print("═" * _W)
    print(f"  EVALUATION  │  Student: {roll_no}  │  Paper: {paper_name}")
    print(f"  Type: {paper_type}  │  Sheet: {sheet_type}  │  "
          f"MCQ: {mcq_count}  Numerical: {numerical_count}  "
          f"Subjective: {subjective_count}  Pages: {pages}")
    print("═" * _W)


def _print_extracted(extracted: Dict[str, str], mcq_count: int, numerical_count: int,
                     subjective_count: int = 0):
    print()
    print("  ── Extracted Answers (raw from Ollama / OMR) ──")
    mcq_parts = [f"Q{i}={extracted.get(f'Q{i}', '—')}" for i in range(1, mcq_count + 1)]
    for chunk in _chunks(mcq_parts, 8):
        print("  MCQ │ " + "  ".join(f"{p:<8}" for p in chunk))
    if numerical_count > 0:
        num_parts = [f"N{i}={extracted.get(f'N{i}', '—')}" for i in range(1, numerical_count + 1)]
        for chunk in _chunks(num_parts, 8):
            print("  NUM │ " + "  ".join(f"{p:<12}" for p in chunk))
    if subjective_count > 0:
        for i in range(1, subjective_count + 1):
            text = extracted.get(f"S{i}", "—")
            print(f"  S{i}  │ {text[:100]}{'…' if len(text) > 100 else ''}")


def _print_grading_table(mcq_detail: list, numerical_detail: list, subjective_detail: list = []):
    print()
    print("  ── Grading Breakdown ──")
    print(f"  {'Q':<5} {'Student':<12} {'Correct':<18} {'Status':<18} {'Marks'}")
    print("  " + "─" * (_W - 2))

    STATUS_ICON = {
        "correct":          "✅",
        "wrong":            "❌",
        "wrong_overfill":   "⚠️  over-fill",
        "wrong_underfill":  "⚠️  under-fill",
        "unanswered":       "○  blank",
    }

    for d in mcq_detail:
        icon    = STATUS_ICON.get(d["status"], d["status"])
        student = d["student_answer"] or "—"
        correct = d["correct_answer"] or "—"
        earned  = f"+{d['marks_earned']:.1f}" if d["marks_earned"] > 0 else (
                  f"{d['marks_earned']:.1f}" if d["marks_earned"] < 0 else "0"
        )
        print(f"  {d['question']:<5} {student:<12} {correct:<18} {icon:<18} {earned}/{d['marks_available']:.1f}")

    if numerical_detail:
        print("  " + "─" * (_W - 2))
        for d in numerical_detail:
            icon      = STATUS_ICON.get(d["status"], d["status"])
            student   = d["student_answer"] or "—"
            accepted  = ", ".join(d["accepted_answers"]) if d["accepted_answers"] else "—"
            earned    = f"+{d['marks_earned']:.1f}" if d["marks_earned"] > 0 else "0"
            print(f"  {d['question']:<5} {student:<12} {accepted:<18} {icon:<18} {earned}/{d['marks_available']:.1f}")

    if subjective_detail:
        print("  " + "─" * (_W - 2))
        print(f"  {'Q':<5} {'Status':<18} {'Earned':<10} {'Concepts Found'}")
        for d in subjective_detail:
            earned   = f"+{d['marks_earned']:.1f}" if d["marks_earned"] > 0 else "0"
            concepts = ", ".join(d.get("concepts_found", [])) or "none"
            status   = "graded" if d["status"] == "graded_by_llm" else "unanswered"
            print(f"  {d['question']:<5} {status:<18} {earned:<10}/{d['marks_available']:.1f}   [{concepts}]")
            if d.get("feedback"):
                print(f"        feedback: {d['feedback'][:80]}")

    print("  " + "─" * (_W - 2))


def _print_score_summary(mcq_score, numerical_score, subjective_score,
                         total_score, max_score, pct,
                         engine, ollama_latency, llm_latency, confidence):
    print(f"  MCQ Score       : {mcq_score}")
    if numerical_score:
        print(f"  Numerical Score : {numerical_score}")
    if subjective_score:
        print(f"  Subjective Score: {subjective_score}")
    print(f"  Total           : {total_score} / {max_score}  ({pct}%)")
    print(f"  Engine          : {engine}")
    if ollama_latency > 0:
        print(f"  Ollama latency  : {ollama_latency:.1f}s   Confidence: {confidence:.2f}")
    if llm_latency > 0:
        print(f"  LLM grading     : {llm_latency:.1f}s")
    print("═" * _W)
    print()


def _chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


# ── Error helper ──────────────────────────────────────────────────────────────

async def _set_error(sub_id, message: str) -> None:
    await submissions_col().update_one(
        {"_id": sub_id},
        {"$set": {"status": "error", "error": message}}
    )
    print(f"❌ Evaluator: marked {sub_id} as error — {message}")
