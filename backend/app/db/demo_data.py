# demo_data.py — the user's own labelled basic-science sets as dummy data in MongoDB, so every screen has content.
#
#   cd backend && python -m app.db.demo_data            # (re)create the dummy data
#   cd backend && python -m app.db.demo_data --clear    # remove it again
#
# Source: eval/data/own_omr, own_mcq, own_mcqnum (45 photographed sheets with the user's gold labels; papers in
# eval/test_papers). The papers go to the Physics teacher of demo.env (as in uploads/Pattern1-2); sheet sNN of a
# paper is submitted by student PH2025<NNN>. Marks = the real scoring code on the gold answers. To show every TA
# and student state, some sheets get one MCQ misread on purpose (the AI mark a TA or re-evaluation then fixes).
# Every document written here has demo: true; re-running replaces only those, real data is never touched.

from __future__ import annotations

import argparse
import asyncio
import json
import random
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from bson import ObjectId

from app.db.mongodb import get_db, papers_col, submissions_col, users_col
from app.pipeline.scoring import grade_mcq, grade_numerical
from app.services import marks as M

BACKEND = Path(__file__).resolve().parents[2]
REPO = BACKEND.parent
DATA = REPO / "eval" / "data"
TP = REPO / "eval" / "test_papers"
PAGE_DIR = "uploads/demo"                                 # sheet photos, relative to backend/ like real uploads
PAPER_DIR = "uploads/papers"                              # served by /api/papers/files/<name>
SUBJECT, ROLL_PREFIX, TEACHER_EMAIL = "Physics", "PH2025", "physics.teacher@evalify.local"
STATES = ("evaluated", "flagged", "ta_done", "reeval_pending", "reeval_resolved", "submitted")

# One entry per paper: dataset set, paper JSON, question paper PDF, released?, mix of states cycled over its sheets
PAPERS = [
    {"set": "own_omr", "paper": "omr_basic_science.json", "pdf": "omr/omr_question_paper.pdf", "released": True,
     "states": ["evaluated", "evaluated", "reeval_pending", "evaluated", "ta_done", "reeval_resolved"]},
    {"set": "own_mcq", "paper": "mcq_basic_science.json", "pdf": "mcq/mcq_question_paper.pdf", "released": False,
     "states": ["evaluated", "flagged", "evaluated", "ta_done", "submitted"]},
    {"set": "own_mcqnum", "paper": "paper_2A.json", "pdf": "mcq_num/paper_2A_question_paper.pdf", "released": True,
     "states": ["evaluated", "reeval_pending", "evaluated", "reeval_resolved", "ta_done"]},
    {"set": "own_mcqnum", "paper": "paper_2B.json", "pdf": "mcq_num/paper_2B_question_paper.pdf", "released": False,
     "states": ["flagged", "evaluated", "submitted", "ta_done", "evaluated"]},
    {"set": "own_mcqnum", "paper": "paper_2C.json", "pdf": "mcq_num/paper_2C_question_paper.pdf", "released": True,
     "states": ["evaluated", "evaluated", "evaluated", "reeval_pending", "evaluated"]},
]
FLAG_REASONS = ["readers disagree on the answer", "low confidence in the handwriting", "random quality check"]
TA = {"role": "ta", "id": "demo-ta", "name": "Demo TA"}


def _now() -> datetime:
    """Current UTC time."""
    return datetime.now(timezone.utc)


def load_sheets(spec: dict) -> list:
    """Manifest rows of one paper, in sheet order (each: sheet_id, sheet_type, pages, gold, edge_cases)."""
    root = DATA / spec["set"]
    rows = [json.loads(l) for l in (root / "manifest.jsonl").read_text().splitlines() if l.strip()]
    rows = [r for r in rows if r["paper"] == f"papers/{spec['paper']}"]
    for r in rows:
        r["pages"] = [str((root / p).resolve()) for p in r["pages"]]
    return sorted(rows, key=lambda r: r["sheet_id"])


def build_paper(spec: dict, teacher_id: str) -> dict:
    """Paper document from the dataset's paper JSON (Evalify paper format), owned by the given teacher."""
    paper = json.loads((DATA / spec["set"] / "papers" / spec["paper"]).read_text())
    created = _now() - timedelta(days=3)
    paper.update(subject=SUBJECT, teacher_id=teacher_id, createdAt=created.isoformat(), resultCount=0,
                 typeLabel={"mcq": "MCQ", "mcq_numerical": "MCQ + Numerical"}.get(paper.get("type", "mcq"), ""),
                 resultsReleased=spec["released"], config=paper.get("config", {}), demo=True,
                 questionPaperUrl=f"/api/papers/files/demo_{Path(spec['pdf']).name}",
                 answerKeyPdfUrl="/api/papers/files/demo_answer_keys.pdf")
    if spec["released"]:
        paper["releasedAt"] = (created + timedelta(days=1)).isoformat()
    return paper


def _misread(sub: dict, rng: random.Random) -> dict:
    """Change one MCQ row as if the reader got it wrong (correct → wrong letter, else → the key); returns the row."""
    row = rng.choice(sub["mcqDetail"])
    key = row["correct_answer"] or "A"
    if row["status"] == "correct":
        row.update(student_answer=rng.choice([c for c in "ABCD" if c not in key]), status="wrong", marks_earned=0.0)
    else:
        row.update(student_answer=key, status="correct", marks_earned=row["marks_available"])
    return row


def build_submission(paper: dict, sheet: dict, student: dict, state: str, rng: random.Random) -> dict:
    """Submission of one dataset sheet by `student` in the given STATES entry."""
    submitted = _now() - timedelta(hours=rng.randint(2, 48))
    pages = [f"{PAGE_DIR}/{Path(p).name}" for p in sheet["pages"]]
    sub = {"_id": ObjectId(), "paper_id": str(paper["_id"]), "paper_name": paper["name"],
           "student_id": str(student["_id"]), "student_name": student.get("name", ""), "roll_no": student.get("roll_no", ""),
           "file_path": pages[0], "file_paths": pages, "file_ext": Path(pages[0]).suffix, "page_count": len(pages),
           "sheet_type": sheet.get("sheet_type", "handwritten"), "status": "submitted",
           "submittedAt": submitted.isoformat(), "result": None, "dataset_sheet": sheet["sheet_id"], "demo": True}
    if state == "submitted":                             # uploaded and stored, waiting for "Start evaluation"
        return sub

    # Real scoring code on the user's gold answers (what the student actually wrote)
    answers = {q: g.get("answer") for q, g in sheet["gold"].items()}
    _, _, mcq = grade_mcq(answers, paper, int(paper.get("mcqCount", 0)))
    _, num = grade_numerical(answers, paper, int(paper.get("numericalCount", 0)))
    sub.update(mcqDetail=mcq, numericalDetail=num, subjectiveDetail=[])

    # Flagged / TA / re-evaluation states: one MCQ misread by the "AI"; the person's decision restores the gold mark
    review, wrong = [], None
    if state != "evaluated":
        gold_row = dict(rng.choice(mcq))
        wrong = next(r for r in mcq if r["question"] == gold_row["question"])
        rng2 = random.Random(sheet["sheet_id"])
        _misread({"mcqDetail": [wrong]}, rng2)
    if state in ("flagged", "ta_done"):
        reason = sheet.get("edge_cases") or rng.choice(FLAG_REASONS)
        wrong.update(needs_review=True, review_reason=reason)
        review.append({"question": wrong["question"], "reason": reason, "reasons": [reason]})
    sub.update(status="evaluated", review=review, evaluatedAt=(submitted + timedelta(minutes=3)).isoformat(),
               pipeline={"models": {"source": "demo dataset (gold labels)"}},
               result={"maxScore": float(paper["totalMarks"]), "engine": "demo", "ocrConfidence": 1.0,
                       "sheetType": sub["sheet_type"], "needsReview": bool(review), "reviewCount": len(review)})
    sub["result"] = M.recompute(sub)

    # The person's decision: back to the mark the gold label gives
    at = (submitted + timedelta(hours=5)).isoformat()
    if state == "ta_done":
        upd, hist = M.apply_marks(sub, {gold_row["question"]: gold_row["marks_earned"]}, TA,
                                  remark="Checked on the answer sheet", source="flagged")
        sub.update(upd, marks_history=hist, ta_review={"status": "done", "by_id": TA["id"], "by_name": TA["name"], "at": at})
    if state in ("reeval_pending", "reeval_resolved"):
        q = gold_row["question"]
        req = {"remark": f"Please re-check {q}; my answer on the sheet is different.", "status": "pending",
               "requestedAt": (submitted + timedelta(days=1)).isoformat()}
        if state == "reeval_resolved":
            upd, hist = M.apply_marks(sub, {q: gold_row["marks_earned"]}, TA, remark="Corrected after re-check",
                                      source="reevaluation")
            sub.update(upd, marks_history=hist)
            req |= {"status": "resolved", "by_id": TA["id"], "by_name": TA["name"], "at": at,
                    "response": "Corrected after re-check"}
        sub["reevaluation"] = req
    return sub


def _copy_files(specs: list) -> None:
    """Copy the sheet photos and question papers next to the real uploads (the viewers serve from there)."""
    for spec in specs:
        for sheet in load_sheets(spec):
            for p in sheet["pages"]:
                dst = BACKEND / PAGE_DIR / Path(p).name
                if not dst.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(p, dst)
        for src, name in ((TP / spec["pdf"], f"demo_{Path(spec['pdf']).name}"), (TP / "keys" / "answer_keys.pdf", "demo_answer_keys.pdf")):
            dst = BACKEND / PAPER_DIR / name
            if src.exists() and not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)


async def clear_demo_data() -> dict:
    """Delete every dummy paper, submission and TA log entry (documents with demo: true)."""
    out = {}
    for name in ("papers", "submissions", "ta_log"):
        out[name] = (await get_db()[name].delete_many({"demo": True})).deleted_count
    return out


async def seed_demo_data(specs: list = PAPERS) -> dict:
    """Replace the dummy data with the user's sets: 5 Physics papers and their sheets (skips missing students)."""
    await clear_demo_data()
    teacher = await users_col().find_one({"role": "teacher", "subjects": SUBJECT})
    if not teacher:
        return {"papers": 0, "submissions": 0}
    _copy_files(specs)
    papers = subs = 0
    for spec in specs:
        paper = build_paper(spec, str(teacher["_id"]))
        paper["_id"] = (await papers_col().insert_one(paper)).inserted_id
        papers += 1
        rng = random.Random(spec["paper"])                 # same data every run
        docs = []
        for i, sheet in enumerate(load_sheets(spec), 1):
            # Sheet number i is written by student PH2025<i> (as in uploads/Pattern1-2)
            student = await users_col().find_one({"role": "student", "roll_no": f"{ROLL_PREFIX}{i:03d}"})
            if student:
                docs.append(build_submission(paper, sheet, student, spec["states"][(i - 1) % len(spec["states"])], rng))
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
    """Command line: connect with the backend's settings, seed users first (so students exist), then the data."""
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
