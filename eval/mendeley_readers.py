#!/usr/bin/env python3
"""mendeley_readers.py — run every live reader on every answer of the Mendeley sheets.

    python eval/mendeley_readers.py [--sheets Student_1,Student_2] [--set eval/data/mendeley]

Per sheet: clean pages → segment once (Qwen3.8, cached) → save one crop per answer
(eval/reports/mendeley/crops/<sheet>/<qid>.jpg) → read each crop with Qwen3.8 (general,
verbatim prompt), Chandra OCR 2, PaddleOCR-VL and GLM-OCR → eval/reports/mendeley/<sheet>.json.
make_mendeley_report.py turns these into the per-sheet markdown reports.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "eval"))

from app.pipeline import llm, quality, readers  # noqa: E402
import dataset  # noqa: E402

REPORTS = ROOT / "eval" / "reports" / "mendeley"
READERS = ["qwen38-27b-fp8", "chandra-ocr-2", "paddleocr-vl-1.6", "glm-ocr"]


def endpoint(name: str):
    """Live endpoint for a registry model name (or None)."""
    url = llm._endpoint_urls().get(name)
    return llm.Endpoint(name, url, llm.registry()["models"][name]) if url and llm._is_up(url) else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default=str(ROOT / "eval" / "data" / "mendeley"))
    ap.add_argument("--sheets", default="")
    args = ap.parse_args()
    eps = {n: endpoint(n) for n in READERS}
    print("readers:", {n: bool(e) for n, e in eps.items()})
    seg = llm.resolve("segmenter")

    for sh in dataset.load(args.set):
        if args.sheets and sh.sheet_id not in args.sheets.split(","):
            continue
        t0 = time.time()
        out_dir = REPORTS / "crops" / sh.sheet_id
        out_dir.mkdir(parents=True, exist_ok=True)
        prepared = [(p, *quality.prepare(p)) for p in sh.pages]
        skipped = [p for p, _, rep in prepared if rep.blank]           # scanned blank backs
        pages = [img for _, img, rep in prepared if not rep.blank]
        page_files = [p for p, _, rep in prepared if not rep.blank]
        qs = readers.questions_for(sh.paper)

        # Segment once, keeping the boxes so the report can say where each crop came from
        crops, boxes = {}, {}
        for pi, page in enumerate(pages):
            from app.prompts import prompt_pipeline as P
            r = llm.chat(seg, P.segment_prompt([q.label for q in qs]), [page], schema=P.SEGMENT_SCHEMA, max_tokens=4096)
            for a in (r.data or {}).get("answers", []):
                q = next((q for q in qs if q.label.upper() == str(a.get("label", "")).upper()), None)
                if q and len(a.get("bbox") or []) == 4:
                    crops.setdefault(q.id, []).append(readers._crop(page, a["bbox"]))
                    boxes.setdefault(q.id, []).append({"page": Path(page_files[pi]).name, "bbox": a["bbox"]})

        # Save crops (multi-part answers stacked vertically into one image)
        files = {}
        for qid, ims in crops.items():
            from PIL import Image
            w, h = max(i.width for i in ims), sum(i.height for i in ims)
            canvas, y = Image.new("RGB", (w, h), "white"), 0
            for im in ims:
                canvas.paste(im, (0, y))
                y += im.height
            canvas.thumbnail((1400, 1400))
            f = out_dir / f"{qid}.jpg"
            canvas.save(f, quality=82)
            files[qid] = str(f.relative_to(REPORTS))

        # Every reader on every located answer, in parallel per reader
        def read(args_):
            name, q = args_
            ep = eps[name]
            if ep is None or q.id not in crops:
                return name, q.id, None
            r = readers.read_general(ep, q, crops[q.id]) if name.startswith("qwen") else readers.read_ocr(ep, q, crops[q.id])
            return name, q.id, asdict(r)

        results: dict = {q.id: {"label": q.label, "kind": q.kind, "crop": files.get(q.id),
                                "boxes": boxes.get(q.id, []), "gold": sh.gold.get(q.id, {}), "readings": {}}
                         for q in qs}
        with ThreadPoolExecutor(12) as pool:
            for name, qid, reading in pool.map(read, [(n, q) for n in READERS for q in qs]):
                results[qid]["readings"][name] = reading

        (REPORTS / f"{sh.sheet_id}.json").write_text(json.dumps(
            {"sheet": sh.sheet_id, "pages": sh.pages, "skipped_blank_pages": [Path(p).name for p in skipped],
             "located": f"{len(crops)}/{len(qs)}", "questions": results}, indent=1))
        print(f"{sh.sheet_id}: located {len(crops)}/{len(qs)} answers, {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
