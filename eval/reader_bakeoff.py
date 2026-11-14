#!/usr/bin/env python3
"""reader_bakeoff.py — Phase 2: compare every live reader on hand-transcribed answers.

    python eval/reader_bakeoff.py eval/data/<set> [--split dev] [--limit 50]

For each live model (from the endpoints file) and each gold question:
  general VLMs  → verbatim prompt AND plain prompt (to measure the do-not-correct effect)
  OCR models    → their own fixed prompt, parsed in code
Reports per (model, variant): MCQ/numeric exact match, subjective CER/WER, over-
correction rate on planted errors, latency; plus how often two readers fail on the
same item (low = good pair). Logs to MLflow experiment evalify_bakeoff_readers and
writes eval/runs/readers_<time>.csv. Keep the two best readers from different families.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.pipeline import llm, numeric, quality, readers  # noqa: E402
from app.pipeline.readers import Question  # noqa: E402
import dataset  # noqa: E402
import metrics  # noqa: E402

RUNS = Path(__file__).resolve().parent / "runs"


def live_endpoints() -> list:
    """Every model the serving job currently exposes."""
    urls = llm._endpoint_urls()
    return [llm.Endpoint(n, u, llm.registry()["models"][n]) for n, u in urls.items() if llm._is_up(u)]


def items_for(sheets) -> list:
    """(sheet, Question, gold, images) for every gold-labelled question; crops from gold or segmenter."""
    seg = llm.resolve("segmenter")
    out = []
    for sh in sheets:
        pages = [quality.prepare(p)[0] for p in sh.pages]
        qs = {q.id: q for q in readers.questions_for(sh.paper)}
        auto = None
        for qid, g in sh.gold.items():
            if qid not in qs:
                continue
            box = sh.crop_box(qid)
            if box:
                imgs = [readers._crop(pages[box["page"]], box["bbox"])]
            else:                                            # segment once per sheet, on demand
                auto = auto if auto is not None else readers.segment(pages, list(qs.values()), seg)
                imgs = auto.get(qid) or pages
            out.append((sh, qs[qid], g, imgs))
    return out


def score_item(q: Question, gold: dict, r) -> dict:
    """Correctness / error rates of one reading against gold."""
    row = {"status": r.status, "latency": r.latency_s}
    if q.kind == "mcq":
        want = ",".join(sorted(set(str(gold.get("answer", "")).replace(" ", "").upper().split(",")) - {""}))
        row["correct"] = (r.value or "") == want
    elif q.kind == "numerical":
        want = str(gold.get("answer", ""))
        row["correct"] = bool(want and r.value and numeric.numbers_agree(r.value, want)) or (not want and not r.value)
    else:
        ref = gold.get("transcript", "")
        row["cer"], row["wer"] = metrics.cer(ref, r.value or ""), metrics.wer(ref, r.value or "")
        row["correct"] = row["cer"] <= 0.10
        row["overcorrected"] = metrics.over_correction(r.value or "", gold.get("planted_errors", []))
    return row


def run_variant(ep, variant: str, items, workers: int) -> list:
    """Read every item with one model/prompt variant."""
    def one(it):
        sh, q, g, imgs = it
        if variant == "ocr":
            r = readers.read_ocr(ep, q, imgs)
        else:
            r = readers.read_general(ep, q, imgs, verbatim=(variant == "verbatim"))
        return {"sheet": sh.sheet_id, "q": q.id, "kind": q.kind, "value": r.value, **score_item(q, g, r)}
    with ThreadPoolExecutor(workers) as pool:
        return list(pool.map(one, items))


def summarise(rows: list) -> dict:
    """Aggregate per-kind accuracy, CER/WER, over-correction and latency."""
    s = {"n": len(rows), "latency_mean_s": sum(r["latency"] for r in rows) / max(1, len(rows))}
    for kind in ("mcq", "numerical", "subjective"):
        k = [r for r in rows if r["kind"] == kind]
        if k:
            s[f"{kind}_acc"] = sum(r["correct"] for r in k) / len(k)
    subj = [r for r in rows if r["kind"] == "subjective"]
    if subj:
        s["cer"] = sum(r["cer"] for r in subj) / len(subj)
        s["wer"] = sum(r["wer"] for r in subj) / len(subj)
        oc = [r["overcorrected"] for r in subj if r["overcorrected"] is not None]
        if oc:
            s["overcorrection_rate"] = sum(oc) / len(oc)
    s["errors"] = sum(r["status"] == "error" for r in rows)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("set_dir")
    ap.add_argument("--split", default="dev")
    ap.add_argument("--limit", type=int, default=0, help="max sheets (0 = all)")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    sheets = list(dataset.load(args.set_dir, args.split))[: args.limit or None]
    items = items_for(sheets)
    eps = live_endpoints()
    print(f"{len(sheets)} sheets, {len(items)} answers, {len(eps)} live models: {[e.name for e in eps]}")

    # Run each model (general VLMs twice: verbatim vs plain prompt)
    results, per_item = {}, {}
    for ep in eps:
        if ep.spec.get("text_only"):
            continue
        variants = ["verbatim", "plain"] if ep.spec.get("prompt_style") == "general" else ["ocr"]
        for v in variants:
            key = f"{ep.name}:{v}"
            t0 = time.time()
            rows = run_variant(ep, v, items, args.workers)
            per_item[key] = {(r["sheet"], r["q"]): r for r in rows}
            results[key] = {**summarise(rows), "family": ep.spec.get("family"), "version": ep.version,
                            "wall_s": round(time.time() - t0, 1)}
            print(key, {k: round(v2, 3) if isinstance(v2, float) else v2 for k, v2 in results[key].items()})

    # Pairwise error overlap: of items either reader gets wrong, how many do BOTH get wrong?
    pairs = {}
    for a, b in itertools.combinations([k for k in per_item if not k.endswith(":plain")], 2):
        both = either = 0
        for key in per_item[a]:
            wa, wb = not per_item[a][key]["correct"], not per_item[b].get(key, {"correct": True})["correct"]
            either += wa or wb
            both += wa and wb
        pairs[f"{a} + {b}"] = both / either if either else 0.0

    # Save leaderboard + log to MLflow
    RUNS.mkdir(exist_ok=True)
    out = RUNS / f"readers_{time.strftime('%Y%m%d_%H%M')}.csv"
    cols = sorted({c for r in results.values() for c in r})
    with out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["reader"] + cols)
        for k, r in results.items():
            w.writerow([k] + [r.get(c, "") for c in cols])
    print(f"\nleaderboard → {out}\n\nshared-error rate per pair (lower = more independent):")
    for p, v in sorted(pairs.items(), key=lambda kv: kv[1]):
        print(f"  {v:.2f}  {p}")
    _log_mlflow("evalify_bakeoff_readers", results, pairs, out, args)


def _log_mlflow(exp: str, results: dict, pairs: dict, csv_path: Path, args) -> None:
    """One MLflow run per reader variant + a summary run with the pair table."""
    try:
        import mlflow
        mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5005"))
        mlflow.set_experiment(exp)
        for k, r in results.items():
            with mlflow.start_run(run_name=k):
                mlflow.log_params({"reader": k, "version": r["version"], "family": r["family"],
                                   "split": args.split, "set": args.set_dir})
                mlflow.log_metrics({m: v for m, v in r.items() if isinstance(v, (int, float))})
        with mlflow.start_run(run_name="pairs"):
            mlflow.log_dict(pairs, "pairs.json")
            mlflow.log_artifact(str(csv_path))
    except Exception as e:
        print(f"(MLflow logging skipped: {e})")


if __name__ == "__main__":
    main()
