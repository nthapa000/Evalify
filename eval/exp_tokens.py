#!/usr/bin/env python3
"""exp_tokens.py — how many model tokens the v2 pipeline uses, per paper type and per question type.

    python eval/exp_tokens.py run   [--limit-subjective 12] [--workers 3]
    python eval/exp_tokens.py score

run:   evaluates real labelled sheets of every paper type with orchestrator.run (live models) and
       keeps the per-sheet token meter (out["usage"]); also measures what one page image costs per model.
score: writes eval/reports/exp_tokens/README.md (tables per paper type, per question type, per step).
"""
from __future__ import annotations

import argparse
import json
import shutil
import statistics as st
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import dataset  # noqa: E402

DATA = Path(__file__).resolve().parent / "data"
OUT = Path(__file__).resolve().parent / "reports" / "exp_tokens"

# (label shown in the report, dataset folder, how many sheets)
SETS = [("A  MCQ only (handwritten)", "own_mcq", None),
        ("A  MCQ only (OMR sheet)", "own_omr", None),
        ("B  MCQ + numerical", "own_mcqnum", None),
        ("C  MCQ + subjective (Data Science exam)", "mendeley", None)]

STAGES = {"read_mcq_numerical": "Read MCQ / numerical answers (readers A, B, C)",
          "transcribe_subjective": "Transcribe written answers (2 transcribers)",
          "grade_subjective": "Grade written answers against the rubric",
          "answer_key_draft": "Draft an answer key (teacher, once per question)"}


def kinds(paper: dict) -> dict:
    """Number of questions of each kind on the paper."""
    from app.pipeline import readers
    qs = readers.questions_for(paper)
    return {k: sum(q.kind == k for q in qs) for k in ("mcq", "numerical", "subjective")}


def one_sheet(label: str, sheet) -> dict:
    """Evaluate one sheet on a copy of its pages (the pipeline writes cleaned pages next to its input)."""
    from app.pipeline import orchestrator
    with tempfile.TemporaryDirectory() as tmp:
        pages = []
        for i, p in enumerate(sheet.pages):
            dst = Path(tmp) / f"p{i}{Path(p).suffix}"
            shutil.copy(p, dst)
            pages.append(str(dst))
        out = orchestrator.run(sheet.paper, pages, sheet.sheet_type)
    return {"set": label, "sheet": sheet.sheet_id, "sheet_type": sheet.sheet_type, "pages": len(sheet.pages),
            "pages_read": sum(1 for q in out["quality"] if not q.get("blank")) if sheet.sheet_type != "omr" else 0,
            "questions": kinds(sheet.paper), "usage": out["usage"], "latency_s": out["latency_s"],
            "models": out["models"]}


def image_cost(page: str) -> list:
    """Prompt tokens of one page image per live model: (image + 'OK') minus ('OK' alone)."""
    from PIL import Image
    from app.pipeline import llm, quality
    img, _ = quality.prepare(page)
    rows, seen = [], set()
    for role in ("page_reader_a", "page_reader_b", "page_reader_c", "transcriber_a", "transcriber_b", "grader"):
        ep = llm.resolve(role)
        if ep is None or ep.name in seen:
            continue
        seen.add(ep.name)
        with_img = llm.chat(ep, "Reply OK.", [img], max_tokens=1)
        text = llm.chat(ep, "Reply OK.", max_tokens=1)
        rows.append({"model": ep.name, "image_px": list(img.size),
                     "image_tokens": with_img.prompt_tokens - text.prompt_tokens})
    return rows


def run(args) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = []
    for label, folder, _ in SETS:
        sheets = list(dataset.load(str(DATA / folder)))
        limit = args.limit_subjective if folder == "mendeley" else None   # subjective sheets are slow: a sample
        jobs += [(label, s) for s in sheets[:limit]]
    print(f"{len(jobs)} sheets", flush=True)
    rows = []
    with ThreadPoolExecutor(args.workers) as pool:
        for r in pool.map(lambda j: one_sheet(*j), jobs):
            rows.append(r)
            print(f"{r['set'][:3]} {r['sheet']:<14} pages {r['pages']}  calls {r['usage']['calls']:>3}  "
                  f"tokens {r['usage']['total_tokens']:>8}  {r['latency_s']:.0f}s", flush=True)
    (OUT / "sheets.json").write_text(json.dumps(rows, indent=1))
    first = next(dataset.load(str(DATA / "mendeley"))).pages[0]
    (OUT / "image_cost.json").write_text(json.dumps(image_cost(first), indent=1))
    print("saved", OUT)


def _mean(xs):
    return round(st.mean(xs)) if xs else 0


def score(_args) -> None:
    rows = json.loads((OUT / "sheets.json").read_text())
    img = json.loads((OUT / "image_cost.json").read_text()) if (OUT / "image_cost.json").exists() else []
    md = ["# Token use of the v2 pipeline", "",
          "Real labelled sheets run through `orchestrator.run` with the live models; tokens are the counts the",
          "vLLM servers return (`usage`), summed over every request, retries included. Input tokens include the",
          "page images.", ""]

    # 1. Per paper type
    md += ["## Per answer sheet", "",
           "| Paper type | Sheets | Pages read / sheet | Questions | Model calls / sheet | Input tokens / sheet "
           "| Output tokens / sheet | **Total / sheet** | Min – max | Time / sheet |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for label, *_ in SETS:
        rs = [r for r in rows if r["set"] == label]
        if not rs:
            continue
        q = rs[0]["questions"]
        qtxt = " + ".join(f"{n} {k}" for k, n in q.items() if n)
        tot = [r["usage"]["total_tokens"] for r in rs]
        md.append(f"| {label} | {len(rs)} | {st.mean(r['pages_read'] for r in rs):.1f} | {qtxt} "
                  f"| {st.mean(r['usage']['calls'] for r in rs):.1f} | {_mean([r['usage']['prompt_tokens'] for r in rs]):,} "
                  f"| {_mean([r['usage']['completion_tokens'] for r in rs]):,} | **{_mean(tot):,}** "
                  f"| {min(tot):,} – {max(tot):,} | {st.mean(r['latency_s'] for r in rs):.0f} s |")

    # 2. Per pipeline step and model
    md += ["", "## Per pipeline step (average per sheet)", ""]
    for label, *_ in SETS:
        rs = [r for r in rows if r["set"] == label]
        if not rs or not any(r["usage"]["calls"] for r in rs):
            continue
        agg = {}
        for r in rs:
            for g in r["usage"]["by_stage"]:
                a = agg.setdefault((g["stage"], g["model"]), {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0})
                for k in a:
                    a[k] += g[k]
        md += [f"**{label}**", "", "| Step | Model | Calls / sheet | Input / sheet | Output / sheet | Total / sheet |",
               "|---|---|---|---|---|---|"]
        for (stage, model), a in sorted(agg.items()):
            n = len(rs)
            md.append(f"| {STAGES.get(stage, stage)} | {model} | {a['calls'] / n:.1f} | {a['prompt_tokens'] / n:,.0f} "
                      f"| {a['completion_tokens'] / n:,.0f} | {(a['prompt_tokens'] + a['completion_tokens']) / n:,.0f} |")
        md.append("")

    # 3. Per question type
    md += ["## Per question", "",
           "Page reading reads all MCQ / numerical answers of a page in one request, so its cost is shared by",
           "those questions. Written answers are transcribed page by page and then graded one by one.", "",
           "| Question type | Measured on | Tokens per question |", "|---|---|---|"]
    for label, *_ in SETS:
        rs = [r for r in rows if r["set"] == label]
        if not rs:
            continue
        q = rs[0]["questions"]
        closed = q["mcq"] + q["numerical"]
        read = st.mean(sum(g["prompt_tokens"] + g["completion_tokens"] for g in r["usage"]["by_stage"]
                           if g["stage"] == "read_mcq_numerical") for r in rs)
        name = "MCQ" if not q["numerical"] else "MCQ / numerical"
        if closed:
            md.append(f"| {name}{' (OMR)' if 'OMR' in label else ''} | {label} | {read / closed:,.0f} |")
        if q["subjective"]:
            for stage, what in (("transcribe_subjective", "Written answer: transcription"),
                                ("grade_subjective", "Written answer: grading")):
                v = st.mean(sum(g["prompt_tokens"] + g["completion_tokens"] for g in r["usage"]["by_stage"]
                                if g["stage"] == stage) for r in rs)
                md.append(f"| {what} | {label} | {v / q['subjective']:,.0f} |")
            graded = [g for r in rs for g in r["usage"]["by_stage"] if g["stage"] == "grade_subjective"]
            if graded:
                n_calls = sum(g["calls"] for g in graded)
                md.append(f"| Written answer: one grading call (answered only) | {label} "
                          f"| {sum(g['prompt_tokens'] + g['completion_tokens'] for g in graded) / n_calls:,.0f} |")

    if img:
        md += ["", "## What one page image costs", "",
               f"One Data Science page after the quality gate ({img[0]['image_px'][0]} x {img[0]['image_px'][1]} px):", "",
               "| Model | Input tokens for the image |", "|---|---|"]
        md += [f"| {r['model']} | {r['image_tokens']:,} |" for r in img]
    (OUT / "README.md").write_text("\n".join(x for x in md if x is not None) + "\n")
    print((OUT / "README.md").read_text())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--limit-subjective", type=int, default=12)
    r.add_argument("--workers", type=int, default=3)
    sub.add_parser("score")
    a = ap.parse_args()
    {"run": run, "score": score}[a.cmd](a)
