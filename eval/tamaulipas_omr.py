#!/usr/bin/env python3
"""tamaulipas_omr.py — OMR accuracy on real scans from the Tamaulipas dataset (CC BY 4.0).

    python eval/tamaulipas_omr.py <imgs_Tam_dataset dir> [--test School001/Grade10] [--n 12]
                                  [--blank-from School001/Grade12] [--no-vlm]

The dataset has no blank sheet, so one is synthesised from OTHER students' sheets of the same
form: align them and keep the lightest value at each pixel (everyone fills different bubbles).
Then the template is learned from that blank and each test sheet is read with
  (a) the template method and (b) the layout-free engine,
and compared item by item with the human labels (X = blank, M = multiple marks).
Reports accuracy, accuracy on auto-accepted items, silent errors and routing rate.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.pipeline import omr_template as T, routing  # noqa: E402
from app.services.omr_engine import OMREngine  # noqa: E402
import metrics  # noqa: E402

OUT = Path(__file__).resolve().parent / "runs"


def labels(txt: Path) -> dict:
    """'12: C' lines → {'Q12': 'C'}; X (blank) → '', M (multiple) → 'M'."""
    out = {}
    for n, v in re.findall(r"(\d+):\s*([A-Z])", txt.read_text()):
        out[f"Q{int(n)}"] = "" if v == "X" else v
    return out


def synth_blank(paths: list) -> np.ndarray:
    """Align sheets to the first one and keep the per-pixel, per-channel maximum (lightest value):
    every student fills different bubbles, so the pencil marks vanish and the print remains."""
    ref = cv2.imread(str(paths[0]))
    size = [ref.shape[1], ref.shape[0]]
    stack = [ref]
    for p in paths[1:]:
        aligned, inl = T.align(cv2.imread(str(p)), ref, size)
        if aligned is not None:
            stack.append(aligned)
    print(f"blank synthesised from {len(stack)} sheets")
    return np.max(np.stack(stack), axis=0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--test", default="School001/Grade10")
    ap.add_argument("--blank-from", default="School001/Grade12")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--no-vlm", action="store_true")
    args = ap.parse_args()
    root = Path(args.root)

    # 1. Blank from other students' sheets, then the template
    blank = synth_blank(sorted((root / args.blank_from).glob("*.jpg")))
    OUT.mkdir(exist_ok=True)
    cv2.imwrite(str(OUT / "tamaulipas_blank.png"), blank)
    t0 = time.time()
    tpl = T.build_template(blank, mcq_count=90, n_options=4,
                           use_vlm=not args.no_vlm)
    print(f"template: {tpl['questions']} questions × {tpl['options']} options, {tpl['layout']}, "
          f"numbered by {tpl['numbering']} ({time.time() - t0:.0f}s) {tpl['warnings']}")
    OUT.mkdir(exist_ok=True)
    cv2.imwrite(str(OUT / "tamaulipas_template.png"), T.preview(blank, tpl))

    # 2. Read each test sheet both ways and compare with the human labels
    legacy = OMREngine()
    rows = {"template": [], "layout_free": []}
    for jpg in sorted((root / args.test).glob("*.jpg"))[: args.n]:
        gold = labels(jpg.with_suffix(".txt"))
        img = cv2.imread(str(jpg))
        res = T.read_sheet(img, blank, tpl)
        lf = legacy.detect(img, 90)
        for q, want in gold.items():
            det = res["answers"].get(q) if res["aligned"] else None
            got = det["answer"] if det else None
            routed = det is None or bool(routing.omr_reasons(det["margin"]))
            ok = (got == want) or (want == "M" and got is not None and "," in got)
            rows["template"].append({"sheet": jpg.stem, "q": q, "gold": want, "got": got,
                                     "correct": ok, "routed": routed})
            l = lf.get(q, {})
            lgot = l.get("answer")
            lok = (lgot == want) or (want == "M" and lgot and "," in lgot)
            rows["layout_free"].append({"sheet": jpg.stem, "q": q, "gold": want, "got": lgot,
                                        "correct": bool(lok),
                                        "routed": not l or bool(routing.omr_reasons(l.get("margin")))})
        m = metrics.system_metrics(rows["template"][-len(gold):])
        print(f"  {jpg.stem}: aligned={res['aligned']} inliers={res['inliers']} "
              f"acc={m['raw_accuracy']:.3f} routed={m['routing_rate']:.3f}")

    # 3. Summary + the wrong items (for manual checking)
    for method, r in rows.items():
        m = metrics.system_metrics(r)
        print(f"\n{method}: items={m['items']} accuracy={m['raw_accuracy']:.4f} "
              f"coverage={m['coverage']:.3f} auto-accept acc={m['auto_accuracy']:.4f} "
              f"silent errors={m['silent_error']:.4f}")
        wrong = [x for x in r if not x["correct"]]
        print(f"  wrong ({len(wrong)}):", [(x["sheet"], x["q"], x["gold"] or "blank", x["got"], "routed" if x["routed"] else "AUTO")
                                          for x in wrong][:25])
    (OUT / "tamaulipas_omr.json").write_text(json.dumps(rows, indent=1))
    print(f"\npreview → {OUT / 'tamaulipas_template.png'}; rows → {OUT / 'tamaulipas_omr.json'}")


if __name__ == "__main__":
    main()
