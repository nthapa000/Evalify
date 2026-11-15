# ta.py — the TA view: subjects, "Flagged by AI" and "Re-evaluation requests" tabs, and final re-evaluated marks.
#
# One queue item = one submission. Flagged: the pipeline flagged questions (one reason each) and no TA has
# reviewed it yet. Re-evaluation: the student's one request is pending. TA marks are final and logged.

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Literal

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.db.mongodb import get_db, papers_col, submissions_col, users_col
from app.routers.auth import require_ta, user_subjects
from app.services import marks as M
from app.services.access import require_view

router = APIRouter(prefix="/ta", tags=["ta"])

# Paper fields the TA screen shows next to the answer sheet (question paper, key, solutions, rubric)
PAPER_FIELDS = ("name", "subject", "type", "typeLabel", "totalMarks", "mcqCount", "mcqMarks", "mcqAnswers",
                "numericalCount", "numericalMarks", "numericalAnswers", "subjectiveCount", "subjectiveMarks",
                "subjectiveQuestionMarks", "subjectiveQuestions", "subjectiveRubrics", "questionPaperUrl",
                "answerKeyPdfUrl", "answerKeyRefUrl", "answerSheetRefUrl", "detailedAnswerPdfUrl", "gradeRubricPdfUrl")

FLAGGED = {"status": "evaluated", "review.0": {"$exists": True}, "ta_review.status": {"$ne": "done"}}
REEVAL = {"status": "evaluated", "reevaluation.status": "pending"}


async def _paper_ids(subject: str) -> list:
    """Ids (as stored on submissions) of every paper of a subject."""
    return [str(p["_id"]) async for p in papers_col().find({"subject": subject}, {"_id": 1})]


async def _check_subject(user: dict, subject: str) -> None:
    """403 unless the TA is a TA of this subject."""
    if subject not in await user_subjects(user):
        raise HTTPException(status_code=403, detail="You are not a TA of this subject.")


@router.get("/subjects")
async def my_subjects(user: dict = Depends(require_ta)):
    """The TA's subjects with how many items wait in each tab."""
    out = []
    for subject in await user_subjects(user):
        ids = await _paper_ids(subject)
        out.append({"subject": subject,
                    "flagged": await submissions_col().count_documents({**FLAGGED, "paper_id": {"$in": ids}}),
                    "reevaluation": await submissions_col().count_documents({**REEVAL, "paper_id": {"$in": ids}})})
    return out


@router.get("/queue")
async def queue(subject: str, tab: Literal["flagged", "reevaluation"] = Query(...), user: dict = Depends(require_ta)):
    """Pending items of one tab for one subject, oldest first."""
    await _check_subject(user, subject)
    query = {**(FLAGGED if tab == "flagged" else REEVAL), "paper_id": {"$in": await _paper_ids(subject)}}
    items = []
    async for s in submissions_col().find(query).sort("submittedAt", 1):
        item = {"submission_id": str(s["_id"]), "paper_id": s["paper_id"], "paper_name": s.get("paper_name", ""),
                "student_name": s.get("student_name", ""), "roll_no": s.get("roll_no", ""),
                "totalScore": (s.get("result") or {}).get("totalScore"), "maxScore": (s.get("result") or {}).get("maxScore"),
                "questions": [{"question": r["question"], "reason": r.get("reason") or (r.get("reasons") or [""])[0]}
                              for r in s.get("review") or []]}
        if tab == "reevaluation":
            item |= {"remark": s["reevaluation"]["remark"], "requestedAt": s["reevaluation"].get("requestedAt")}
        items.append(item)
    return items


@router.get("/items/{submission_id}")
async def item(submission_id: str, user: dict = Depends(require_ta)):
    """Everything the TA needs for one answer sheet: paper materials, every question's AI mark and reason."""
    sub, paper = await require_view(user, submission_id)
    questions = [{"question": r["question"], "kind": M.kind_of(k), "question_text": r.get("question_text"),
                  "student_answer": r.get("student_answer"), "correct_answer": r.get("correct_answer"),
                  "accepted_answers": r.get("accepted_answers"), "marks_available": r.get("marks_available"),
                  "marks_earned": r.get("marks_earned"), "rubric_marks": r.get("rubric_marks"),
                  "needs_review": bool(r.get("needs_review")), "review_reason": r.get("review_reason", ""),
                  "concepts": r.get("concepts", []), "final_by": r.get("final_by")}
                 for k, r in M.rows(sub)]
    return {"submission": {"id": submission_id, "student_name": sub.get("student_name"), "roll_no": sub.get("roll_no"),
                           "paper_id": sub.get("paper_id"), "page_count": len(sub.get("file_paths") or []),
                           "sheet_type": sub.get("sheet_type"), "result": sub.get("result")},
            "paper": {k: paper.get(k) for k in PAPER_FIELDS} if paper else None,
            "questions": questions, "reevaluation": sub.get("reevaluation"), "ta_review": sub.get("ta_review"),
            "marks_history": sub.get("marks_history", [])}


class TaMarks(BaseModel):
    tab: Literal["flagged", "reevaluation"]
    marks: Dict[str, float] = {}
    remark: str = ""


@router.post("/items/{submission_id}/marks")
async def submit_marks(submission_id: str, body: TaMarks, user: dict = Depends(require_ta)):
    """Final re-evaluated marks from the TA; closes the flagged review or answers the re-evaluation request."""
    sub, _ = await require_view(user, submission_id)
    if body.tab == "reevaluation" and (sub.get("reevaluation") or {}).get("status") != "pending":
        raise HTTPException(status_code=409, detail="There is no pending re-evaluation request for this paper.")
    me = await users_col().find_one({"_id": ObjectId(user["sub"])})
    by = {"role": "ta", "id": user["sub"], "name": (me or {}).get("name", "")}
    try:
        updates, history = M.apply_marks(sub, body.marks, by, remark=body.remark.strip(), source=body.tab)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None

    # Close the tab's item: flagged → reviewed; re-evaluation → resolved with the TA's (optional) remark
    now = datetime.now(timezone.utc).isoformat()
    done = {"status": "done" if body.tab == "flagged" else "resolved", "by_id": user["sub"], "by_name": by["name"], "at": now}
    if body.tab == "flagged":
        updates["ta_review"] = done
    else:
        updates["reevaluation"] = {**sub["reevaluation"], **done, "response": body.remark.strip()}
    await submissions_col().update_one({"_id": sub["_id"]}, {"$set": updates,
                                                            "$push": {"marks_history": {"$each": history}}})
    # Audit log of every TA decision (also when no mark changed)
    await get_db()["ta_log"].insert_one({"submission_id": submission_id, "tab": body.tab, "ta_id": user["sub"],
                                         "ta_name": by["name"], "marks": body.marks, "changes": history,
                                         "remark": body.remark.strip(), "at": now})
    return {"id": submission_id, "result": updates["result"], "changes": history}
