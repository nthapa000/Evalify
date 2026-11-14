# scoring.py — deterministic MCQ + numerical scoring (no models involved).
# Shared by the legacy Ollama path and the two-reader pipeline.

from __future__ import annotations

from typing import Dict

from app.pipeline import numeric


def _letters(ans) -> frozenset:
    """'A,C' → {'A','C'}; None → empty set."""
    return frozenset(a.strip().upper() for a in str(ans or "").split(",") if a.strip())


def grade_mcq(answers: Dict[str, str], paper: dict, n_mcq: int):
    """Exact-set MCQ grading with optional negative marking. Returns (score, n_correct, detail)."""
    key = paper.get("mcqAnswers", {})
    per_q = paper.get("mcqQuestionMarks", {})
    default = float(paper.get("mcqMarks", 1))
    cfg = paper.get("config", {})
    neg_qs = cfg.get("negativeMarkingQuestions", []) if cfg.get("negativeMarkingScope") == "per_question" else None

    score, n_correct, detail = 0.0, 0, []
    for i in range(1, n_mcq + 1):
        q = f"Q{i}"
        got, want = _letters(answers.get(q)), _letters(key.get(q))
        marks = float(per_q.get(q, default))
        penalty = -(marks / 4) if cfg.get("negativeMaking") and (neg_qs is None or q in neg_qs) else 0.0

        # Status: blank / correct / over-filled / under-filled / wrong
        if not got:
            status, earned = "unanswered", 0.0
        elif got == want:
            status, earned = "correct", marks
            n_correct += 1
        else:
            status = "wrong_overfill" if got > want else "wrong_underfill" if got < want else "wrong"
            earned = penalty

        score += earned
        detail.append({"question": q, "student_answer": ",".join(sorted(got)) or None,
                       "correct_answer": ",".join(sorted(want)) or None, "status": status,
                       "marks_available": marks, "marks_earned": earned})
    return max(0.0, score), n_correct, detail


def grade_numerical(answers: Dict[str, str], paper: dict, n_num: int):
    """Numeric grading in code (fractions, units, tolerance). Returns (score, detail)."""
    key = paper.get("numericalAnswers", {})
    per_q = paper.get("numericalQuestionMarks", {})
    default = float(paper.get("numericalMarks", 1))

    score, detail = 0.0, []
    for i in range(1, n_num + 1):
        q = f"N{i}"
        marks = float(per_q.get(q, default))
        res = numeric.compare(answers.get(q), key.get(q))
        earned = marks if res.status == "correct" else 0.0
        score += earned
        detail.append({"question": q, "student_answer": res.student_raw or None,
                       "accepted_answers": numeric.accepted_display(key.get(q)),
                       "status": res.status, "flags": res.flags,
                       "marks_available": marks, "marks_earned": earned})
    return score, detail
