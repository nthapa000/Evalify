# batch_runner.py — the teacher's "Start evaluation": marks every waiting answer sheet of a paper as one batch.
#
# Uploads are only stored (status "submitted"). start() queues all waiting sheets of the paper; run_batch() then
#   stage 1 "reading": every sheet is read (evaluator.read_submission → status "read", readings stored)
#   stage 2 "grading": every sheet is scored and its written answers graded (evaluator.evaluate_submission)
# Reading everything first lets the grading stage have the GPUs to itself (INFERENCE_OPTIMIZATION.md #9):
# stage_hook() can switch the GPU job to a grader-only profile between the stages (off unless configured).
# State lives in MongoDB (batches collection + submission status), so recover() resumes after a restart.

from __future__ import annotations

import asyncio
import json
import os
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId

from app.db.mongodb import get_db, submissions_col
from app.pipeline import llm
from app.services import evaluator

WAITING = ("submitted", "error")                     # sheets the next "Start evaluation" picks up
STATUSES = ("queued", "reading", "read", "grading", "evaluated", "error")
_tasks: dict = {}                                    # batch id → running asyncio task (one per batch)


class BatchError(Exception):
    """Why a batch cannot start (shown to the teacher)."""


def batches_col():
    return get_db()["batches"]


def concurrency() -> int:
    """Sheets in flight per stage (the model servers batch them; 32 measured best, INFERENCE_OPTIMIZATION.md)."""
    return int(os.environ.get("EVALIFY_BATCH_CONCURRENCY", "32"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def start(paper: dict, teacher_id: str) -> dict:
    """Queue every waiting sheet of the paper as one new batch (BatchError if none, or one is running)."""
    pid = str(paper["_id"])
    if await batches_col().find_one({"paper_id": pid, "status": "running"}):
        raise BatchError("An evaluation of this paper is already running.")
    ids = [s["_id"] async for s in submissions_col().find({"paper_id": pid, "status": {"$in": list(WAITING)}}, {"_id": 1})]
    if not ids:
        raise BatchError("No answer sheets are waiting for evaluation.")
    batch = {"paper_id": pid, "teacher_id": teacher_id, "status": "running", "stage": "reading",
             "total": len(ids), "created_at": _now(), "finished_at": None}
    bid = str((await batches_col().insert_one(batch)).inserted_id)
    await submissions_col().update_many({"_id": {"$in": ids}},
                                        {"$set": {"status": "queued", "batch_id": bid}, "$unset": {"error": ""}})
    return await describe(await batches_col().find_one({"_id": ObjectId(bid)}))


async def describe(batch: dict | None) -> dict | None:
    """Batch for the API: stage, total and how many of its sheets are in each status."""
    if not batch:
        return None
    bid = str(batch["_id"])
    counts = dict.fromkeys(STATUSES, 0)
    async for s in submissions_col().find({"batch_id": bid}, {"status": 1}):
        counts[s.get("status", "queued")] = counts.get(s.get("status", "queued"), 0) + 1
    return {"id": bid, "status": batch["status"], "stage": batch.get("stage"), "total": batch["total"],
            "counts": counts, "created_at": batch["created_at"], "finished_at": batch.get("finished_at")}


async def progress(paper_id: str) -> dict:
    """Sheets waiting for the next "Start evaluation", and the paper's latest batch."""
    waiting = await submissions_col().count_documents({"paper_id": paper_id, "status": {"$in": list(WAITING)}})
    latest = await batches_col().find({"paper_id": paper_id}).sort("created_at", -1).to_list(1)
    return {"waiting": waiting, "batch": await describe(latest[0] if latest else None)}


async def _step(sem: asyncio.Semaphore, sid: ObjectId, status: str, fn) -> None:
    """Run one sheet through one stage (the evaluator records errors on the sheet itself)."""
    async with sem:
        await submissions_col().update_one({"_id": sid}, {"$set": {"status": status}})
        await fn(str(sid))


async def _stage(bid: str, stage: str, pick: str, fn) -> None:
    """Run every sheet of the batch that is in status `pick` through one stage."""
    await batches_col().update_one({"_id": ObjectId(bid)}, {"$set": {"stage": stage}})
    ids = [s["_id"] async for s in submissions_col().find({"batch_id": bid, "status": pick}, {"_id": 1})]
    sem = asyncio.Semaphore(concurrency())
    t0 = time.time()
    await asyncio.gather(*[_step(sem, i, stage, fn) for i in ids])
    print(f"Batch {bid}: {stage} {len(ids)} sheet(s) in {time.time() - t0:.0f}s")


async def run_batch(bid: str) -> None:
    """Stage 1 read every sheet, (optional model swap), stage 2 grade every sheet, then mark the batch done."""
    await stage_hook("reading")
    await _stage(bid, "reading", "queued", evaluator.read_submission)
    await stage_hook("grading")
    await _stage(bid, "grading", "read", evaluator.evaluate_submission)
    await batches_col().update_one({"_id": ObjectId(bid)}, {"$set": {"status": "done", "stage": "done",
                                                                    "finished_at": _now()}})
    await stage_hook("done")


async def _guarded(bid: str) -> None:
    """run_batch in the background; an unexpected failure marks the batch failed and its unfinished sheets as errors."""
    try:
        await run_batch(bid)
    except Exception as exc:
        traceback.print_exc()
        await batches_col().update_one({"_id": ObjectId(bid)}, {"$set": {"status": "failed", "error": str(exc),
                                                                        "finished_at": _now()}})
        # Unfinished sheets become errors so the teacher can send them again (finished sheets keep their marks)
        await submissions_col().update_many({"batch_id": bid, "status": {"$in": ["queued", "reading", "read", "grading"]}},
                                            {"$set": {"status": "error", "error": f"Evaluation stopped: {exc}"}})
    finally:
        _tasks.pop(bid, None)


def kick(bid: str) -> None:
    """Start the batch in the background of the running server (once per batch)."""
    if bid not in _tasks:
        _tasks[bid] = asyncio.get_running_loop().create_task(_guarded(bid))


async def recover() -> list:
    """At start-up: sheets cut off mid-stage go back one step, and every running batch continues."""
    await submissions_col().update_many({"batch_id": {"$exists": True}, "status": "reading"}, {"$set": {"status": "queued"}})
    await submissions_col().update_many({"batch_id": {"$exists": True}, "status": "grading"}, {"$set": {"status": "read"}})
    ids = [str(b["_id"]) async for b in batches_col().find({"status": "running"}, {"_id": 1})]
    for bid in ids:
        kick(bid)
    return ids


# ── Optional model swap between the stages (#9) ─────────────────────────────

async def stage_hook(stage: str) -> None:
    """Switch the GPU job's profile for a stage, when configured (serve_switch.sbatch watches the profile file):
    EVALIFY_BATCH_PROFILE_FILE + EVALIFY_BATCH_READ_PROFILE (reading / done) + EVALIFY_BATCH_GRADE_PROFILE."""
    path = os.environ.get("EVALIFY_BATCH_PROFILE_FILE")
    prof = os.environ.get("EVALIFY_BATCH_GRADE_PROFILE" if stage == "grading" else "EVALIFY_BATCH_READ_PROFILE")
    if not (path and prof):
        return
    Path(path).write_text(prof + "\n")
    # Wait until the GPU job reports the profile's servers (model loads take a few minutes)
    for _ in range(240):
        try:
            if json.loads(llm.ENDPOINTS_FILE.read_text()).get("profile") == prof:
                break
        except (OSError, ValueError):
            pass
        await asyncio.sleep(10)
    llm._endpoint_urls.cache_clear()                 # new servers → fresh endpoint list and health checks
    llm._health.clear()
    llm._copies_cache.clear()
