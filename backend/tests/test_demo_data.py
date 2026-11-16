# test_demo_data.py — the user's own labelled sets as dummy data (app/db/demo_data.py). In-memory database.

import random

import pytest

from app.db import demo_data
from app.services import marks as M
from tests.conftest import auth_headers

STUDENT = {"_id": "u1", "name": "A", "roll_no": "PH2025001"}


def _paper(spec):
    """Paper of a spec with a fake database id."""
    return {**demo_data.build_paper(spec, "t1"), "_id": "p1"}


def _gold_total(paper, sheet):
    """Total the gold labels give (all states that end with a person's decision must reach it)."""
    sub = demo_data.build_submission(paper, sheet, STUDENT, "evaluated", random.Random(0))
    return sub["result"]["totalScore"]


# Why: every paper of the user's sets must load with its sheets, photos on disk and answer keys for all questions
@pytest.mark.parametrize("spec", demo_data.PAPERS, ids=lambda s: s["paper"])
def test_dataset_papers_load(spec):
    paper, sheets = _paper(spec), demo_data.load_sheets(spec)
    assert sheets and all(__import__("os").path.exists(p) for s in sheets for p in s["pages"])
    assert len(paper["mcqAnswers"]) == int(paper["mcqCount"]) and paper["demo"] and paper["subject"] == "Physics"


# Why: shown totals must equal the per-question marks, and evaluated sheets must score what the gold labels give
@pytest.mark.parametrize("state", demo_data.STATES)
def test_submission_totals(state):
    spec = demo_data.PAPERS[2]                              # MCQ + numerical paper 2A
    paper, sheet = _paper(spec), demo_data.load_sheets(spec)[0]
    sub = demo_data.build_submission(paper, sheet, STUDENT, state, random.Random(1))
    if state == "processing":
        assert sub["status"] == "processing" and sub["result"] is None
        return
    assert sub["result"]["totalScore"] == M.recompute(sub)["totalScore"]
    if state in ("evaluated", "ta_done", "reeval_resolved"):     # a person's decision restores the gold mark
        assert sub["result"]["totalScore"] == _gold_total(paper, sheet)
    else:                                                        # still the misread AI mark
        assert sub["result"]["totalScore"] != _gold_total(paper, sheet)


# Why: each state must land in the right TA tab (flagged / re-evaluation) or stay out of both
def test_states_match_ta_queues():
    spec = demo_data.PAPERS[0]
    paper, sheet = _paper(spec), demo_data.load_sheets(spec)[0]
    sub = {st: demo_data.build_submission(paper, sheet, STUDENT, st, random.Random(2)) for st in demo_data.STATES}
    assert sub["flagged"]["review"] and "ta_review" not in sub["flagged"]
    assert sub["ta_done"]["ta_review"]["status"] == "done" and sub["ta_done"]["marks_history"]
    assert sub["reeval_pending"]["reevaluation"]["status"] == "pending"
    assert sub["reeval_resolved"]["reevaluation"]["status"] == "resolved"
    assert not sub["evaluated"]["review"] and "reevaluation" not in sub["evaluated"]


# Why: seeding must use the real demo users and be repeatable without piling up copies
@pytest.mark.asyncio
async def test_seed_is_repeatable(client, db):
    first = await demo_data.seed_demo_data()
    second = await demo_data.seed_demo_data()
    assert first == second and first["papers"] == len(demo_data.PAPERS) and first["submissions"] > 0
    assert await db["submissions"].count_documents({"demo": True}) == first["submissions"]


# Why: real (non-demo) papers and submissions must never be removed by re-seeding or clearing
@pytest.mark.asyncio
async def test_clear_keeps_real_data(client, db):
    await db["papers"].insert_one({"name": "real paper"})
    await demo_data.seed_demo_data()
    await demo_data.clear_demo_data()
    assert await db["papers"].count_documents({}) == 1 and await db["submissions"].count_documents({"demo": True}) == 0


# Why: the dummy data must show up through the real API: teacher results, the sheet photo and the question paper
@pytest.mark.asyncio
async def test_seeded_data_visible_through_api(client, physics_teacher_token):
    await demo_data.seed_demo_data()
    h = auth_headers(physics_teacher_token)
    papers = [p for p in (await client.get("/api/papers", headers=h)).json() if p.get("demo")]
    assert len(papers) == len(demo_data.PAPERS)
    paper = next(p for p in papers if p["resultCount"] > 0)
    subs = (await client.get(f"/api/results/paper/{paper['id']}", headers=h)).json()["submissions"]
    assert (await client.get(f"/api/submissions/{subs[0]['id']}/pages/0", headers=h)).status_code == 200
    assert (await client.get(paper["questionPaperUrl"])).status_code == 200
