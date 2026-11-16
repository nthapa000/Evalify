# demo_data.py — dummy papers and evaluated submissions in MongoDB, so every screen has something to show.
#
#   cd backend && python -m app.db.demo_data            # (re)create the dummy data
#   cd backend && python -m app.db.demo_data --clear    # remove it again
#
# Uses the demo users already seeded from demo.env (teachers, TAs, students). Every document written here has
# demo: true; re-running replaces only those documents, real papers and submissions are never touched.
# The marks are random (fixed seed), not real grading; every answer sheet points to one placeholder page image.

from __future__ import annotations

import argparse
import asyncio
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from bson import ObjectId

from app.db.mongodb import get_db, papers_col, submissions_col, users_col
from app.pipeline.scoring import grade_mcq, grade_numerical
from app.services import marks as M

PAGE = "uploads/demo_answer_sheet.png"                   # placeholder page, relative to backend/ like real uploads
STATES = ("evaluated", "flagged", "ta_done", "reeval_pending", "reeval_resolved", "processing")

# Subjective questions per subject: (question, model answer, rubric points)
WRITTEN = {
    "Computer Science": [
        ("What is a stack? Give one use.", "A LIFO list; used for function calls.", ["last in first out", "one use, e.g. call stack or undo"]),
        ("Compare an array and a linked list.", "Arrays have O(1) index access; lists grow without copying.", ["array index access is constant time", "linked list insert without shifting", "memory layout difference"]),
        ("What does a compiler do?", "Translates source code into machine code before running.", ["translates source to machine code", "before execution"]),
    ],
    "Physics": [
        ("State Newton's second law.", "Force equals rate of change of momentum, F = ma.", ["force proportional to rate of change of momentum", "F = ma"]),
        ("What is total internal reflection?", "Light in a denser medium hitting the surface above the critical angle reflects fully.", ["denser to rarer medium", "angle above the critical angle"]),
    ],
    "Mathematics": [
        ("State the mean value theorem.", "For f continuous on [a,b] and differentiable on (a,b), some c has f'(c) = (f(b)-f(a))/(b-a).", ["continuity and differentiability conditions", "f'(c) equals the average slope"]),
    ],
    "Data Science": [
        ("Define supervised learning.", "Learning a mapping from labelled examples.", ["trained on labelled data", "predicts outputs for new inputs"]),
        ("Why is accuracy misleading on imbalanced data?", "A model predicting only the majority class scores high.", ["majority class dominates", "use precision, recall or F1"]),
        ("What is overfitting?", "The model fits noise in training data and generalises badly.", ["fits training noise", "poor performance on unseen data"]),
    ],
}

# One entry per dummy paper; "states" is the mix of submission states (cycled over the enrolled students)
PAPERS = [
    {"subject": "Computer Science", "name": "Programming Basics Quiz", "type": "mcq", "mcq": 10, "num": 0, "subj": 0,
     "released": True, "students": 12, "states": ["evaluated"] * 4 + ["reeval_pending", "reeval_resolved"]},
    {"subject": "Computer Science", "name": "Data Structures Mid-semester", "type": "mcq_numerical_subjective",
     "mcq": 8, "num": 2, "subj": 3, "released": False, "students": 14,
     "states": ["evaluated", "evaluated", "flagged", "ta_done", "processing"]},
    {"subject": "Physics", "name": "Kinematics Unit Test", "type": "mcq_numerical", "mcq": 6, "num": 4, "subj": 0,
     "released": True, "students": 10, "states": ["evaluated", "evaluated", "ta_done", "reeval_pending"]},
    {"subject": "Physics", "name": "Optics and Laws of Motion", "type": "mcq_numerical_subjective",
     "mcq": 5, "num": 2, "subj": 2, "released": False, "students": 8, "states": ["evaluated", "flagged", "processing"]},
    {"subject": "Mathematics", "name": "Calculus Test 1", "type": "mcq_numerical_subjective", "mcq": 5, "num": 3,
     "subj": 1, "released": True, "students": 10, "states": ["evaluated", "evaluated", "reeval_pending", "ta_done"]},
    {"subject": "Data Science", "name": "Machine Learning Basics Quiz", "type": "mcq_numerical_subjective",
     "mcq": 10, "num": 0, "subj": 3, "released": False, "students": 16,
     "states": ["evaluated", "evaluated", "flagged", "flagged", "ta_done", "processing"]},
]

# Numerical answer keys (value, unit), cycled over N1, N2, ...
NUM_KEYS = [("25", "m/s"), ("9.8", "m/s^2"), ("120", "J"), ("0.5", ""), ("3.14", ""), ("42", "N")]
FLAG_REASONS = ["readers disagree on the answer", "low confidence in the handwriting", "random quality check",
                "answer crossed out and rewritten"]


def _now() -> datetime:
    """Current UTC time (one place, so tests can rely on ISO strings)."""
    return datetime.now(timezone.utc)


def build_paper(spec: dict, teacher_id: str) -> dict:
    """Paper document for one PAPERS entry, in the shape the CreatePaper wizard stores."""
    rng = random.Random(spec["name"])                     # same answer key every run
    written = (WRITTEN[spec["subject"]] * 3)[:spec["subj"]]
    mcq_marks, num_marks, subj_marks = 1, 2, 4
    total = spec["mcq"] * mcq_marks + spec["num"] * num_marks + spec["subj"] * subj_marks
    created = _now() - timedelta(days=len(spec["name"]) % 9 + 1)
    return {
        "name": spec["name"], "subject": spec["subject"], "type": spec["type"], "typeLabel": spec["type"].replace("_", " + ").upper(),
        "totalMarks": total, "mcqCount": spec["mcq"], "mcqMarks": mcq_marks,
        "mcqAnswers": {f"Q{i}": rng.choice("ABCD") for i in range(1, spec["mcq"] + 1)},
        "numericalCount": spec["num"], "numericalMarks": num_marks,
        "numericalAnswers": {f"N{i}": {"answer": v, "unit": u or None, "tolerance": 0.01, "tolerance_type": "rel"}
                             for i, (v, u) in enumerate(NUM_KEYS[:spec["num"]], 1)},
        "subjectiveCount": spec["subj"], "subjectiveMarks": subj_marks,
        "subjectiveQuestionMarks": {f"S{i}": subj_marks for i in range(1, spec["subj"] + 1)},
        "subjectiveQuestions": [q for q, _, _ in written],
        "subjectiveRubrics": [{"key_concepts": pts, "model_answer": ans, "marks_per_concept": subj_marks / len(pts)}
                              for _, ans, pts in written],
        "config": {}, "omrTemplate": None, "numbering": "continuous", "teacher_id": teacher_id,
        "createdAt": created.isoformat(), "resultCount": 0,
        "resultsReleased": spec["released"], **({"releasedAt": (created + timedelta(days=1)).isoformat()} if spec["released"] else {}),
        "demo": True,
    }


def _answers(paper: dict, rng: random.Random, skill: float) -> dict:
    """Random student answers: right with probability `skill`, else wrong or blank."""
    out = {}
    for q, key in paper["mcqAnswers"].items():
        r = rng.random()
        out[q] = key if r < skill else ("" if r > 0.95 else rng.choice([c for c in "ABCD" if c != key]))
    for q, key in paper["numericalAnswers"].items():
        right = rng.random() < skill
        out[q] = f"{key['answer']} {key['unit'] or ''}".strip() if right else str(round(float(key["answer"]) * rng.uniform(0.5, 1.5), 2))
    return out


def _written_rows(paper: dict, rng: random.Random, skill: float) -> list:
    """Subjective rows in the pipeline's shape with random rubric decisions."""
    rows = []
    for i, (q_text, rub) in enumerate(zip(paper["subjectiveQuestions"], paper["subjectiveRubrics"]), 1):
        mx = float(paper["subjectiveQuestionMarks"][f"S{i}"])
        found = [c for c in rub["key_concepts"] if rng.random() < skill]
        marks = round(mx * len(found) / len(rub["key_concepts"]) * 2) / 2   # half marks, like the grader
        rows.append({"question": f"S{i}", "question_text": q_text,
                     "student_answer": rub["model_answer"] if found else "I am not sure about this one.",
                     "marks_available": mx, "marks_earned": marks, "rubric_marks": marks, "calibrated_marks": None,
                     "status": "graded_by_llm", "concepts_found": found,
                     "concepts_missing": [c for c in rub["key_concepts"] if c not in found], "mandatory_met": True,
                     "feedback": "; ".join(found), "graders": ["demo"],
                     "concepts": [{"concept": c, "present": c in found, "evidence": c if c in found else ""}
                                  for c in rub["key_concepts"]]})
    return rows


def build_submission(paper: dict, student: dict, state: str, rng: random.Random) -> dict:
    """One submission of `student` for `paper` in the given STATES entry (marks random but self-consistent)."""
    submitted = _now() - timedelta(hours=rng.randint(2, 48))
    sub = {"_id": ObjectId(), "paper_id": str(paper["_id"]), "paper_name": paper["name"],
           "student_id": str(student["_id"]), "student_name": student.get("name", ""), "roll_no": student.get("roll_no", ""),
           "file_path": PAGE, "file_paths": [PAGE], "file_ext": ".png", "page_count": 1,
           "sheet_type": "handwritten" if paper["subjectiveCount"] else "omr",
           "status": "processing", "submittedAt": submitted.isoformat(), "result": None, "demo": True}
    if state == "processing":                             # uploaded, not evaluated yet
        return sub

    # Grade MCQ and numerical with the real scoring code, written answers with random rubric decisions
    skill = rng.uniform(0.35, 0.95)
    answers = _answers(paper, rng, skill)
    _, _, mcq = grade_mcq(answers, paper, paper["mcqCount"])
    _, num = grade_numerical(answers, paper, paper["numericalCount"])
    sub.update(mcqDetail=mcq, numericalDetail=num, subjectiveDetail=_written_rows(paper, rng, skill))
    review = []
    if state in ("flagged", "ta_done"):                   # questions the pipeline sent to a TA
        for key, row in rng.sample(list(M.rows(sub)), k=min(2, len(list(M.rows(sub))))):
            reason = rng.choice(FLAG_REASONS)
            row.update(needs_review=True, review_reason=reason)
            review.append({"question": row["question"], "reason": reason, "reasons": [reason]})
    sub.update(status="evaluated", review=review, evaluatedAt=(submitted + timedelta(minutes=3)).isoformat(),
               pipeline={"models": {"grader": "demo"}, "prompt_version": "v2"},
               result={"maxScore": float(paper["totalMarks"]), "engine": "demo", "ocrConfidence": 1.0,
                       "sheetType": sub["sheet_type"], "needsReview": bool(review), "reviewCount": len(review)})
    sub["result"] = M.recompute(sub)

    # TA work: change one flagged question's mark, or answer a student's re-evaluation request
    ta = {"role": "ta", "id": "demo-ta", "name": "Demo TA"}
    at = (submitted + timedelta(hours=5)).isoformat()
    if state == "ta_done":
        q = review[0]["question"]
        row = next(r for _, r in M.rows(sub) if r["question"] == q)
        new = row["marks_available"] if row["marks_earned"] < row["marks_available"] else 0.0
        upd, hist = M.apply_marks(sub, {q: new}, ta, remark="Checked the answer sheet", source="flagged")
        sub.update(upd, marks_history=hist, ta_review={"status": "done", "by_id": ta["id"], "by_name": ta["name"], "at": at})
    if state in ("reeval_pending", "reeval_resolved"):
        q = next(r for _, r in M.rows(sub))["question"]
        req = {"remark": f"Please re-check {q}, I think my answer is correct.", "status": "pending",
               "requestedAt": (submitted + timedelta(days=1)).isoformat()}
        if state == "reeval_resolved":
            upd, hist = M.apply_marks(sub, {q: next(r for _, r in M.rows(sub))["marks_available"]}, ta,
                                      remark="Answer accepted on re-check", source="reevaluation")
            sub.update(upd, marks_history=hist)
            req |= {"status": "resolved", "by_id": ta["id"], "by_name": ta["name"], "at": at,
                    "response": "Answer accepted on re-check"}
        sub["reevaluation"] = req
    return sub


def _placeholder_page() -> None:
    """Write the placeholder answer-sheet image once (the page viewer needs a real file)."""
    path = Path(__file__).resolve().parents[2] / PAGE
    if path.exists():
        return
    from PIL import Image, ImageDraw
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1240, 1754), "white")
    draw = ImageDraw.Draw(img)
    for y in range(200, 1700, 60):                       # ruled lines like an answer booklet
        draw.line((80, y, 1160, y), fill=(200, 210, 230), width=2)
    draw.text((80, 80), "Demo answer sheet (dummy data, no real scan)", fill="black")
    img.save(path)


async def clear_demo_data() -> dict:
    """Delete every dummy paper, submission and TA log entry (documents with demo: true)."""
    out = {}
    for name in ("papers", "submissions", "ta_log"):
        out[name] = (await get_db()[name].delete_many({"demo": True})).deleted_count
    return out


async def seed_demo_data() -> dict:
    """Replace the dummy data: papers for each subject with a teacher, submissions from its enrolled students."""
    await clear_demo_data()
    _placeholder_page()
    papers = subs = 0
    for spec in PAPERS:
        # Teacher of the subject and its students, from the demo users already in the database
        teacher = await users_col().find_one({"role": "teacher", "subjects": spec["subject"]})
        if not teacher:
            continue
        students = await users_col().find({"role": "student", "subjects": spec["subject"]}).sort("roll_no", 1).to_list(spec["students"])
        paper = build_paper(spec, str(teacher["_id"]))
        paper["_id"] = (await papers_col().insert_one(paper)).inserted_id
        papers += 1
        rng = random.Random(spec["name"] + "-subs")
        states = [st for st in spec["states"] if spec["released"] or not st.startswith("reeval")]
        docs = [build_submission(paper, s, states[i % len(states)], rng) for i, s in enumerate(students)]
        if docs:
            await submissions_col().insert_many(docs)
            subs += len(docs)
        # Audit log entries for the TA decisions, as the TA screen writes them
        logs = [{"submission_id": str(d["_id"]), "tab": h["source"], "ta_id": h["by_id"], "ta_name": h["by_name"],
                 "marks": {h["question"]: h["new"]}, "changes": [h], "remark": h["remark"], "at": h["at"], "demo": True}
                for d in docs for h in d.get("marks_history", [])]
        if logs:
            await get_db()["ta_log"].insert_many(logs)
    return {"papers": papers, "submissions": subs}


async def _main(clear: bool) -> None:
    """Command line: connect with the backend's settings, seed users first (so names exist), then the data."""
    from app.db.mongodb import close_db, connect_db
    from app.db.seed import seed_users
    await connect_db(max_retries=1)
    try:
        if clear:
            print("Removed:", await clear_demo_data())
        else:
            await seed_users()
            print("Created:", await seed_demo_data())
    finally:
        await close_db()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Create or remove Evalify dummy data (documents with demo: true).")
    ap.add_argument("--clear", action="store_true", help="remove the dummy data instead of creating it")
    asyncio.run(_main(ap.parse_args().clear))
