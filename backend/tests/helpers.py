# helpers.py — shared builders for API tests (papers and already-evaluated submissions).

from datetime import datetime, timezone

from bson import ObjectId

from tests.conftest import auth_headers

# A small type-C paper: 2 MCQ (1 mark), 1 numerical (2 marks), 2 subjective (2 marks each) = 8 marks
TYPE_C = {
    "name": "Unit Test 1", "type": "mcq_numerical_subjective", "typeLabel": "MCQ + Numerical + Subjective",
    "totalMarks": 8, "mcqCount": 2, "mcqMarks": 1, "mcqAnswers": {"Q1": "B", "Q2": "A"},
    "numericalCount": 1, "numericalMarks": 2,
    "numericalAnswers": {"N1": {"answer": "2500", "unit": "m", "tolerance": 0.001, "tolerance_type": "abs"}},
    "subjectiveCount": 2, "subjectiveMarks": 2, "subjectiveQuestionMarks": {"S1": 2, "S2": 2},
    "subjectiveQuestions": ["What is solar energy?", "Define power."],
    "subjectiveRubrics": [
        {"key_concepts": ["energy derived from the sun", "an example"], "marks_per_concept": 1},
        {"key_concepts": ["rate of doing work", "unit watt"], "marks_per_concept": 1}],
    "questionPaperUrl": "/api/papers/files/qp.pdf", "answerKeyRefUrl": "/api/papers/files/key.pdf",
}


async def make_paper(client, token, **overrides) -> dict:
    """Create a paper through the API as the given teacher and return it."""
    resp = await client.post("/api/papers", json={**TYPE_C, **overrides}, headers=auth_headers(token))
    assert resp.status_code == 200, resp.text
    return resp.json()


async def student_id(db, roll_no: str) -> str:
    """Database id of a seeded student."""
    return str((await db["users"].find_one({"roll_no": roll_no}))["_id"])


async def add_evaluated_submission(db, paper: dict, roll_no: str = "CS2025001", flagged: bool = True,
                                   pages=None) -> str:
    """Insert a submission as the evaluator would leave it: per-question details, scores, TA flags."""
    sid = ObjectId()
    mcq = [{"question": "Q1", "student_answer": "B", "correct_answer": "B", "status": "correct",
            "marks_available": 1.0, "marks_earned": 1.0, "needs_review": False, "review_reason": ""},
           {"question": "Q2", "student_answer": "C", "correct_answer": "A", "status": "wrong",
            "marks_available": 1.0, "marks_earned": 0.0, "needs_review": flagged,
            "review_reason": "readers disagree (A: A, B: C, C: D)" if flagged else ""}]
    num = [{"question": "N1", "student_answer": "2500 m", "status": "correct", "marks_available": 2.0,
            "marks_earned": 2.0, "needs_review": False, "review_reason": ""}]
    subj = [{"question": "S1", "question_text": "What is solar energy?", "student_answer": "energy from the sun",
             "marks_available": 2.0, "marks_earned": 1.0, "rubric_marks": 1.0, "calibrated_marks": None,
             "status": "graded_by_llm", "needs_review": False, "review_reason": "",
             "concepts": [{"concept": "energy derived from the sun", "present": True, "partial": False,
                           "evidence": "energy from the sun"},
                          {"concept": "an example", "present": False, "partial": False, "evidence": ""}]},
            {"question": "S2", "question_text": "Define power.", "student_answer": "work per time",
             "marks_available": 2.0, "marks_earned": 0.5, "rubric_marks": 0.5, "calibrated_marks": None,
             "status": "graded_by_llm", "needs_review": False, "review_reason": "", "concepts": []}]
    review = [{"question": "Q2", "reason": "readers disagree (A: A, B: C, C: D)"}] if flagged else []
    user = await db["users"].find_one({"roll_no": roll_no})
    await db["submissions"].insert_one({
        "_id": sid, "paper_id": paper["id"], "paper_name": paper["name"], "student_id": str(user["_id"]),
        "student_name": user["name"], "roll_no": roll_no, "file_paths": pages or [], "page_count": len(pages or []),
        "file_path": (pages or [""])[0], "sheet_type": "handwritten", "status": "evaluated",
        "submittedAt": datetime.now(timezone.utc).isoformat(),
        "result": {"mcqScore": 1.0, "numericalScore": 2.0, "subjectiveScore": 1.5, "totalScore": 4.5,
                   "maxScore": 8.0, "percentage": 56.2, "needsReview": flagged, "reviewCount": len(review)},
        "mcqDetail": mcq, "numericalDetail": num, "subjectiveDetail": subj, "review": review,
    })
    return str(sid)
