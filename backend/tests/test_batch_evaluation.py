# test_batch_evaluation.py — uploads are only stored; the teacher's "Start evaluation" marks the whole set
# (every sheet read first, then every sheet graded). No model server, MongoDB or GPU: the pipeline is stubbed.

import json

import pytest
from bson import ObjectId

from app.pipeline import orchestrator
from app.pipeline.readers import Reading
from app.services import batch_runner, evaluator
from tests.conftest import auth_headers
from tests.helpers import make_paper

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32


@pytest.fixture(autouse=True)
def uploads(monkeypatch, tmp_path):
    """Uploads go to a temp dir; starting a batch only records the kick (tests run the batch themselves)."""
    from app.routers import submissions
    monkeypatch.setattr(submissions, "UPLOAD_DIR", str(tmp_path))
    kicked = []
    monkeypatch.setattr(batch_runner, "kick", lambda bid: kicked.append(bid))
    return kicked


async def _upload(client, token, paper_id):
    """A student uploads one page; returns the submission JSON."""
    r = await client.post(f"/api/submissions?paper_id={paper_id}&sheet_type=handwritten", headers=auth_headers(token),
                          files=[("files", ("p1.png", PNG, "image/png"))])
    assert r.status_code == 200, r.text
    return r.json()


def _stub_pipeline(monkeypatch, log):
    """Fake read_sheet / grade_sheet that record their order and return run()-shaped output."""
    monkeypatch.setattr(evaluator, "_use_pipeline", lambda sheet_type: True)

    def read(paper, files, sheet_type):
        log.append(("read", files[0]))
        return {"reads": {}, "models": {"reader_a": "stub"}, "quality": [], "sheet_reasons": [], "read_s": 0.1}

    def grade(paper, state):
        log.append(("grade", state["models"]["reader_a"]))
        return {"answers": {}, "mcq_detail": [{"question": "Q1", "marks_available": 1.0, "marks_earned": 1.0}],
                "numerical_detail": [], "subjective_detail": [], "mcq_score": 1.0, "n_correct": 1,
                "numerical_score": 0.0, "subjective_score": 0.0, "review": [], "quality": [],
                "models": {"reader_a": "stub"}, "prompt_version": "v2", "latency_s": 0.2, "usage": {}}
    monkeypatch.setattr(orchestrator, "read_sheet", read)
    monkeypatch.setattr(orchestrator, "grade_sheet", grade)
    monkeypatch.setattr(evaluator, "_log_mlflow", lambda *a, **k: None)


# ── Uploads are only stored ──────────────────────────────────────────────────

# Why: user decision (17 Nov) — evaluation no longer starts on upload; the sheet waits for the teacher
@pytest.mark.asyncio
async def test_upload_is_only_stored(client, physics_teacher_token, student_token, monkeypatch):
    started = []
    monkeypatch.setattr(evaluator, "evaluate_submission", lambda sid: started.append(sid))
    paper = await make_paper(client, physics_teacher_token)
    sub = await _upload(client, student_token, paper["id"])
    assert sub["status"] == "submitted" and started == []


# Why: the student's paper list says the sheet was received and is waiting, not "being evaluated"
@pytest.mark.asyncio
async def test_student_sees_submitted(client, physics_teacher_token, student_token):
    paper = await make_paper(client, physics_teacher_token)
    await _upload(client, student_token, paper["id"])
    avail = (await client.get("/api/papers/available", headers=auth_headers(student_token))).json()
    assert next(p for p in avail if p["id"] == paper["id"])["submissionStatus"] == "submitted"


# ── Start evaluation (teacher) ───────────────────────────────────────────────

# Why: the button queues every waiting sheet of the paper at once and starts the batch
@pytest.mark.asyncio
async def test_start_evaluation_queues_all_waiting(client, db, physics_teacher_token, student_token, other_student_token, uploads):
    paper = await make_paper(client, physics_teacher_token)
    await _upload(client, student_token, paper["id"])
    await _upload(client, other_student_token, paper["id"])
    r = await client.post(f"/api/papers/{paper['id']}/evaluate", headers=auth_headers(physics_teacher_token))
    assert r.status_code == 200, r.text
    assert r.json()["total"] == 2 and uploads == [r.json()["id"]]
    assert await db["submissions"].count_documents({"paper_id": paper["id"], "status": "queued"}) == 2


# Why: nothing to evaluate, or a batch already running, must not start a second batch
@pytest.mark.asyncio
async def test_start_evaluation_refuses_empty_or_running(client, physics_teacher_token, student_token):
    paper = await make_paper(client, physics_teacher_token)
    empty = await client.post(f"/api/papers/{paper['id']}/evaluate", headers=auth_headers(physics_teacher_token))
    assert empty.status_code == 409
    await _upload(client, student_token, paper["id"])
    assert (await client.post(f"/api/papers/{paper['id']}/evaluate", headers=auth_headers(physics_teacher_token))).status_code == 200
    again = await client.post(f"/api/papers/{paper['id']}/evaluate", headers=auth_headers(physics_teacher_token))
    assert again.status_code == 409 and "running" in again.json()["detail"]


# Papers below belong to the Physics teacher: both test students are enrolled in Physics

# Why: only the paper's own teacher may start its evaluation or see its progress
@pytest.mark.asyncio
async def test_only_owner_can_start(client, physics_teacher_token, teacher_token, student_token):
    paper = await make_paper(client, physics_teacher_token)
    await _upload(client, student_token, paper["id"])
    r = await client.post(f"/api/papers/{paper['id']}/evaluate", headers=auth_headers(teacher_token))
    assert r.status_code == 404
    assert (await client.get(f"/api/papers/{paper['id']}/evaluation", headers=auth_headers(student_token))).status_code == 403


# Why: the teacher's page shows how many sheets wait and, during a batch, the stage and counts
@pytest.mark.asyncio
async def test_evaluation_status(client, physics_teacher_token, student_token):
    paper = await make_paper(client, physics_teacher_token)
    h = auth_headers(physics_teacher_token)
    await _upload(client, student_token, paper["id"])
    before = (await client.get(f"/api/papers/{paper['id']}/evaluation", headers=h)).json()
    assert before["waiting"] == 1 and before["batch"] is None
    await client.post(f"/api/papers/{paper['id']}/evaluate", headers=h)
    during = (await client.get(f"/api/papers/{paper['id']}/evaluation", headers=h)).json()
    assert during["waiting"] == 0 and during["batch"]["status"] == "running" and during["batch"]["counts"]["queued"] == 1


# ── The batch itself ─────────────────────────────────────────────────────────

# Why: #9 — every sheet is read before any is graded, so the grading stage can have the GPUs to itself
@pytest.mark.asyncio
async def test_batch_reads_all_then_grades(client, db, physics_teacher_token, student_token, other_student_token, monkeypatch):
    log = []
    _stub_pipeline(monkeypatch, log)
    paper = await make_paper(client, physics_teacher_token)
    await _upload(client, student_token, paper["id"])
    await _upload(client, other_student_token, paper["id"])
    bid = (await client.post(f"/api/papers/{paper['id']}/evaluate", headers=auth_headers(physics_teacher_token))).json()["id"]
    await batch_runner.run_batch(bid)
    assert [s for s, _ in log] == ["read", "read", "grade", "grade"]
    subs = await db["submissions"].find({"paper_id": paper["id"]}).to_list(None)
    assert all(s["status"] == "evaluated" and s["result"]["totalScore"] == 1.0 and "read_state" not in s for s in subs)
    batch = await db["batches"].find_one({"_id": ObjectId(bid)})
    assert batch["status"] == "done" and batch["finished_at"]


# Why: the optional model swap (#9) happens once, between the reading and the grading stage
@pytest.mark.asyncio
async def test_stage_hook_between_stages(client, physics_teacher_token, student_token, monkeypatch):
    log = []
    _stub_pipeline(monkeypatch, log)

    async def hook(stage):
        log.append((f"stage:{stage}", ""))
    monkeypatch.setattr(batch_runner, "stage_hook", hook)
    paper = await make_paper(client, physics_teacher_token)
    await _upload(client, student_token, paper["id"])
    bid = (await client.post(f"/api/papers/{paper['id']}/evaluate", headers=auth_headers(physics_teacher_token))).json()["id"]
    await batch_runner.run_batch(bid)
    assert [s for s, _ in log] == ["stage:reading", "read", "stage:grading", "grade", "stage:done"]


# Why: a sheet that fails is marked as an error (with the reason) and does not stop the rest of the class
@pytest.mark.asyncio
async def test_one_failure_does_not_stop_batch(client, db, physics_teacher_token, student_token, other_student_token, monkeypatch):
    log = []
    _stub_pipeline(monkeypatch, log)
    good = orchestrator.read_sheet

    def flaky(paper, files, sheet_type):
        if len([x for x in log if x[0] == "read"]) == 0:
            log.append(("read", "boom"))
            raise RuntimeError("page unreadable")
        return good(paper, files, sheet_type)
    monkeypatch.setattr(orchestrator, "read_sheet", flaky)
    paper = await make_paper(client, physics_teacher_token)
    await _upload(client, student_token, paper["id"])
    await _upload(client, other_student_token, paper["id"])
    bid = (await client.post(f"/api/papers/{paper['id']}/evaluate", headers=auth_headers(physics_teacher_token))).json()["id"]
    await batch_runner.run_batch(bid)
    statuses = sorted(s["status"] for s in await db["submissions"].find({"paper_id": paper["id"]}).to_list(None))
    assert statuses == ["error", "evaluated"]
    # A failed sheet can be sent again with the next "Start evaluation"
    assert (await client.get(f"/api/papers/{paper['id']}/evaluation", headers=auth_headers(physics_teacher_token))).json()["waiting"] == 1


# Why: after a backend restart the batch continues where it stopped instead of losing half-done sheets
@pytest.mark.asyncio
async def test_recover_resumes_interrupted_batch(client, db, physics_teacher_token, student_token, other_student_token, uploads):
    paper = await make_paper(client, physics_teacher_token)
    await _upload(client, student_token, paper["id"])
    await _upload(client, other_student_token, paper["id"])
    bid = (await client.post(f"/api/papers/{paper['id']}/evaluate", headers=auth_headers(physics_teacher_token))).json()["id"]
    subs = await db["submissions"].find({"paper_id": paper["id"]}).to_list(None)
    await db["submissions"].update_one({"_id": subs[0]["_id"]}, {"$set": {"status": "reading"}})
    await db["submissions"].update_one({"_id": subs[1]["_id"]}, {"$set": {"status": "grading", "read_state": {"x": 1}}})
    uploads.clear()
    assert await batch_runner.recover() == [bid] and uploads == [bid]
    after = {s["_id"]: s["status"] for s in await db["submissions"].find({"paper_id": paper["id"]}).to_list(None)}
    assert after[subs[0]["_id"]] == "queued" and after[subs[1]["_id"]] == "read"


# ── Reading state survives storage ──────────────────────────────────────────

# Why: readings are stored in MongoDB between the stages; "final" must stay the same reader after reloading
def test_reads_round_trip_through_json():
    a, b = Reading("gemma", "g@1", "answered", "B"), Reading("qwen", "q@1", "answered", "C")
    reads = {"Q1": {"a": a, "b": b, "final": b, "accepted": True, "reasons": ["x"]},
             "Q2": {"a": a, "b": b, "reasons": []}}
    back = orchestrator.load_reads(json.loads(json.dumps(orchestrator.dump_reads(reads))))
    assert back["Q1"]["final"] is back["Q1"]["b"] and back["Q1"]["b"].value == "C" and back["Q1"]["reasons"] == ["x"]
    assert "final" not in back["Q2"] and back["Q2"]["a"] == a


# Why: if a batch crashes its unfinished sheets must become errors, so the teacher can send them again with
# "Start evaluation" (before, they stayed "reading" forever and the button stayed disabled)
@pytest.mark.asyncio
async def test_crashed_batch_sheets_can_be_restarted(client, db, physics_teacher_token, student_token, other_student_token, monkeypatch):
    paper = await make_paper(client, physics_teacher_token)
    await _upload(client, student_token, paper["id"])
    await _upload(client, other_student_token, paper["id"])
    h = auth_headers(physics_teacher_token)
    bid = (await client.post(f"/api/papers/{paper['id']}/evaluate", headers=h)).json()["id"]
    done = (await db["submissions"].find({"batch_id": bid}).to_list(None))[0]
    await db["submissions"].update_one({"_id": done["_id"]}, {"$set": {"status": "evaluated"}})   # one sheet finished

    async def boom(_bid):
        raise RuntimeError("database connection lost")
    monkeypatch.setattr(batch_runner, "run_batch", boom)
    await batch_runner._guarded(bid)
    batch = await db["batches"].find_one({"_id": ObjectId(bid)})
    assert batch["status"] == "failed" and "database connection lost" in batch["error"]
    subs = {s["_id"]: s for s in await db["submissions"].find({"batch_id": bid}).to_list(None)}
    assert subs[done["_id"]]["status"] == "evaluated"                       # finished work is kept
    assert [s["status"] for i, s in subs.items() if i != done["_id"]] == ["error"]
    assert (await client.get(f"/api/papers/{paper['id']}/evaluation", headers=h)).json()["waiting"] == 1



# Why: user report (17 Nov) — one sheet took 62 s because the MLflow call (60 s of retries when MLflow is down) ran
# on the server's main thread and froze it; it must run in a worker thread so nothing else waits for it
@pytest.mark.asyncio
async def test_mlflow_logging_does_not_block_the_server(client, physics_teacher_token, student_token, monkeypatch):
    import threading
    log, seen = [], {}
    _stub_pipeline(monkeypatch, log)
    main = threading.get_ident()
    monkeypatch.setattr(evaluator, "_log_mlflow", lambda *a, **k: seen.setdefault("thread", threading.get_ident()))
    paper = await make_paper(client, physics_teacher_token)
    await _upload(client, student_token, paper["id"])
    bid = (await client.post(f"/api/papers/{paper['id']}/evaluate", headers=auth_headers(physics_teacher_token))).json()["id"]
    await batch_runner.run_batch(bid)
    assert "thread" in seen and seen["thread"] != main
