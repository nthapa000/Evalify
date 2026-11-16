# test_demo_data.py — dummy papers and submissions for trying the UI (app/db/demo_data.py). In-memory database.

import random

import pytest

from app.db import demo_data
from app.services import marks as M
from tests.conftest import auth_headers


# Why: every dummy paper must be a valid paper of its type (counts match answer keys and questions)
@pytest.mark.parametrize("spec", demo_data.PAPERS, ids=lambda s: s["name"])
def test_paper_specs_are_consistent(spec):
    p = demo_data.build_paper(spec, "t1")
    assert len(p["mcqAnswers"]) == p["mcqCount"] and len(p["numericalAnswers"]) == p["numericalCount"]
    assert len(p["subjectiveQuestions"]) == len(p["subjectiveRubrics"]) == p["subjectiveCount"]
    assert p["demo"] is True and p["teacher_id"] == "t1"


# Why: the totals shown on result pages must equal the sum of the per-question marks, as after real grading
@pytest.mark.parametrize("state", demo_data.STATES)
def test_submission_totals_match_rows(state):
    spec = next(s for s in demo_data.PAPERS if s["type"] == "mcq_numerical_subjective")
    paper = {**demo_data.build_paper(spec, "t1"), "_id": "p1"}
    sub = demo_data.build_submission(paper, {"_id": "u1", "name": "A", "roll_no": "R1"}, state, random.Random(1))
    if state == "processing":
        assert sub["status"] == "processing" and sub["result"] is None
        return
    assert sub["result"]["totalScore"] == M.recompute(sub)["totalScore"]
    assert 0 <= sub["result"]["totalScore"] <= sub["result"]["maxScore"]


# Why: each state must land in the right TA tab (flagged / re-evaluation) or stay out of both
def test_states_match_ta_queues():
    spec = next(s for s in demo_data.PAPERS if s["type"] == "mcq_numerical_subjective")
    paper = {**demo_data.build_paper(spec, "t1"), "_id": "p1"}
    sub = {st: demo_data.build_submission(paper, {"_id": "u", "name": "A", "roll_no": "R"}, st, random.Random(2))
           for st in demo_data.STATES}
    assert sub["flagged"]["review"] and "ta_review" not in sub["flagged"]
    assert sub["ta_done"]["ta_review"]["status"] == "done" and sub["ta_done"]["marks_history"]
    assert sub["reeval_pending"]["reevaluation"]["status"] == "pending"
    assert sub["reeval_resolved"]["reevaluation"]["status"] == "resolved"


# Why: seeding must use the real demo users and be repeatable without piling up copies
@pytest.mark.asyncio
async def test_seed_is_repeatable(client, db):
    first = await demo_data.seed_demo_data()
    second = await demo_data.seed_demo_data()
    assert first == second and first["papers"] > 0 and first["submissions"] > 0
    assert await db["papers"].count_documents({"demo": True}) == first["papers"]
    assert await db["submissions"].count_documents({"demo": True}) == first["submissions"]


# Why: real (non-demo) papers and submissions must never be removed by re-seeding or clearing
@pytest.mark.asyncio
async def test_clear_keeps_real_data(client, db):
    await db["papers"].insert_one({"name": "real paper"})
    await demo_data.seed_demo_data()
    await demo_data.clear_demo_data()
    assert await db["papers"].count_documents({}) == 1 and await db["submissions"].count_documents({"demo": True}) == 0


# Why: the dummy data must show up through the real API (teacher results page and TA flagged tab)
@pytest.mark.asyncio
async def test_seeded_data_visible_through_api(client, teacher_token):
    await demo_data.seed_demo_data()
    papers = (await client.get("/api/papers", headers=auth_headers(teacher_token))).json()
    demo = [p for p in papers if p.get("demo")]
    assert demo and any(p["resultCount"] > 0 for p in demo)
    res = (await client.get(f"/api/results/paper/{demo[0]['id']}", headers=auth_headers(teacher_token))).json()
    assert res["stats"]["count"] == demo[0]["resultCount"]
