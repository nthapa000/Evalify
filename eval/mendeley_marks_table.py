#!/usr/bin/env python3
"""mendeley_marks_table.py — teacher's marks vs our grader's marks, per answer and per sheet.

    python eval/mendeley_marks_table.py [--variant pagetext] [--calib 8,11,24,31,33]
    → eval/reports/mendeley_marks/{marks_table.md, marks_per_answer.csv}

Final type-C set-up: whole-page transcription (pagetext) + Gemma grader prompt v2. "Calibrated" = grader mark
+ the mean (teacher − grader) on the calibration sheets, rounded to 0.5 and clipped to [0, 2].
Answers not located go to a TA (shown as "TA").
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "eval"))

import dataset  # noqa: E402
from mendeley_sweep import subj_metrics  # noqa: E402

SET = ROOT / "eval" / "data" / "mendeley"
OUT = ROOT / "eval" / "reports" / "mendeley_marks"


def as_mark(x: float) -> float:
    """Clip to [0, 2] and round to the nearest half mark."""
    return min(2.0, max(0.0, round(x * 2) / 2))


def fmt(x) -> str:
    return "TA" if x is None else f"{x:g}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="pagetext", choices=["pagetext", "seg2"])
    ap.add_argument("--calib", default="8,11,24,31,33", help="teacher-marked calibration sheet numbers")
    args = ap.parse_args()
    grades = json.loads((ROOT / f"eval/reports/mendeley_seg/grades_{args.variant}.json").read_text())
    sheets = sorted(dataset.load(str(SET)), key=lambda s: int(s.sheet_id.split("_")[1]))
    calib = {f"Student_{n}" for n in args.calib.split(",")}

    # one row per teacher-marked short answer
    rows = []
    for sh in sheets:
        for i in range(1, 16):
            q, t = f"S{i}", sh.gold.get(f"S{i}", {}).get("marks")
            if t is None or not 0 <= t <= 2:
                continue
            g = grades.get(f"{sh.sheet_id}|{q}|{args.variant}") or {}
            rows.append({"sheet": sh.sheet_id, "question": f"{q} (Q{20 + i})", "teacher": float(t),
                         "grader": g.get("marks"), "calibration_sheet": sh.sheet_id in calib})
    # global shift learned from the calibration sheets only
    train = [(r["grader"], r["teacher"]) for r in rows if r["calibration_sheet"] and r["grader"] is not None]
    shift = statistics.mean(t - g for g, t in train)
    for r in rows:
        r["calibrated"] = None if r["grader"] is None else as_mark(r["grader"] + shift)

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "marks_per_answer.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["sheet", "question", "teacher", "grader", "calibrated", "calibration_sheet"])
        w.writeheader()
        w.writerows(rows)

    test = [r for r in rows if not r["calibration_sheet"] and r["grader"] is not None]
    m_raw = subj_metrics([(r["grader"], r["teacher"]) for r in test])
    m_cal = subj_metrics([(r["calibrated"], r["teacher"]) for r in test])
    md = ["# Teacher's marks vs our grader's marks (Mendeley, 50 sheets)", "",
          f"Generated {time.strftime('%Y-%m-%d %H:%M')} by `python eval/mendeley_marks_table.py`. Set-up: whole-page "
          f"transcription ({args.variant}) + Gemma grader, prompt v2. Short answers only, 15 × 2 marks per sheet.",
          f"*Calibrated* = grader + {shift:+.2f} (learned from the teacher's marks on sheets "
          f"{', '.join(sorted(calib, key=lambda s: int(s.split('_')[1])))}, marked ★), rounded to 0.5, clipped to 0–2. "
          "*TA* = answer not found on the page → sent to a TA. Per-answer list: `marks_per_answer.csv`.", "",
          "## Agreement on the 45 non-calibration sheets", "",
          "| | MAE (/2) | exact | within 0.5 | QWK | bias |", "|---|---|---|---|---|---|",
          f"| grader (raw) | {m_raw['mae']} | {m_raw['exact']:.0%} | {m_raw['within_0.5']:.0%} | {m_raw['qwk']} | {m_raw['bias']} |",
          f"| grader (calibrated) | {m_cal['mae']} | {m_cal['exact']:.0%} | {m_cal['within_0.5']:.0%} | {m_cal['qwk']} | {m_cal['bias']} |",
          "", "## Totals per sheet (short answers the teacher marked)", "",
          "| sheet | answers | teacher | grader | calibrated | TA |", "|---|---|---|---|---|---|"]
    for sh in sheets:
        rs = [r for r in rows if r["sheet"] == sh.sheet_id]
        if not rs:
            continue
        ta = sum(r["grader"] is None for r in rs)
        star = " ★" if sh.sheet_id in calib else ""
        md.append(f"| {sh.sheet_id}{star} | {len(rs)} | {sum(r['teacher'] for r in rs):g} | "
                  f"{sum(r['grader'] or 0 for r in rs):g} | {sum(r['calibrated'] or 0 for r in rs):g} | {ta or ''} |")
    md += ["", "## Every answer", "", "| sheet | question | teacher | grader | calibrated |", "|---|---|---|---|---|"]
    for r in rows:
        star = " ★" if r["calibration_sheet"] else ""
        md.append(f"| {r['sheet']}{star} | {r['question']} | {fmt(r['teacher'])} | {fmt(r['grader'])} | {fmt(r['calibrated'])} |")
    (OUT / "marks_table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[:60]))


if __name__ == "__main__":
    main()
