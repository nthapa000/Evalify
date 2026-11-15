#!/usr/bin/env python3
"""edu_circuit.py — final numerical answers in real worked solutions (EDU-CIRCUIT-HW, Georgia Tech ECE 2040).

    python eval/edu_circuit.py build    # expected results + gold student values (two text LLMs must agree)
    python eval/edu_circuit.py read     # every reader extracts the final values from the image (cached)
    python eval/edu_circuit.py score    # every reader combination → eval/reports/edu_circuit/README.md

Data: the 320 solutions that have an expert transcription
(`Rectified_recognized_markdown_done_Anon/.../<hw>_<q>_markdown.md` + `_source.png`), rubrics in
`Screenshot_output_anon/rubric_outputs/P<q>.json` (their `notes` state the expected final results).
Only plain-number results are tested (not functions of time or phasors).

Gold:
  expected value per quantity = extracted from the rubric notes by Qwen AND Gemma (values must agree);
  student's final value       = extracted from the EXPERT TRANSCRIPT by Qwen AND Gemma (must agree;
                                disagreements are dropped and counted).
Readers (from the image): Qwen / Gemma read the image directly; PaddleOCR / GLM-OCR / Chandra OCR the
image, then Qwen picks the final values out of the OCR text. Grading = the teacher's numeric rule
(number in the key unit, ±0.001, unit ignored, no conversion) — same code as the app.
"""
from __future__ import annotations

import argparse
import glob
import itertools
import json
import re
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "eval"))

from app.pipeline import numeric  # noqa: E402
from arch_sweep import decide, endpoint  # noqa: E402

SRC = Path("/scratch/m25csa019/evalify/datasets/edu_circuit_hw/extracted/EDU-CIRCUIT-HW_v1")
DATA = ROOT / "eval" / "data" / "edu_circuit"
OUT = ROOT / "eval" / "reports" / "edu_circuit"
QWEN, GEMMA = "qwen38-27b-fp8", "gemma4-31b-fp8"
OCRS = {"paddleocr-vl-1.6": "paddle", "glm-ocr": "glm", "chandra-ocr-2": "chandra"}
TOL = 0.001                                                   # teacher's tolerance (absolute)

LIST_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["answers"],
               "properties": {"answers": {"type": "array", "items": {
                   "type": "object", "additionalProperties": False, "required": ["name", "value", "unit"],
                   "properties": {"name": {"type": "string"}, "value": {"type": "string"}, "unit": {"type": "string"}}}}}}

EXPECTED_PROMPT = """These are a teacher's grading notes for one circuit-analysis homework problem:
---
{notes}
---
List every FINAL numerical result the notes give as the correct answer, one entry per quantity:
"name" (as in the notes, e.g. "R", "v1", "i_o", "P", "cost"), "value" (the number only, e.g. "-4", "3.5",
"0.264") and "unit" (e.g. "V", "mA", "Ω", "$"; "" if none). Include only plain numbers — skip functions of
time (e.g. i(t) = 1 + e^(-t/2)), phasors / complex values, inequalities and ranges. If a quantity is given in
two equivalent forms (26.4¢ or $0.264), give the first one. Return JSON."""

FINAL_PROMPT = """{source} a student's handwritten solution to a circuit-analysis problem.
For each quantity below, give the student's FINAL value for it, copied exactly as the student wrote it
(number only in "value", the student's unit in "unit"). The final value is the boxed / underlined /
last-stated result for that quantity. Ignore struck-out work. Do NOT calculate, correct or round anything.
If the student did not give a final value for a quantity, use "" for value and unit.
Quantities: {names}
Return JSON with one entry per quantity, using these names."""


def chat_list(ep, prompt, images=()):
    """One JSON list call → ({name: (value, unit)}, latency)."""
    from app.pipeline import llm
    r = llm.chat(ep, prompt, list(images), schema=LIST_SCHEMA, max_tokens=1024)
    out = {}
    for a in (r.data or {}).get("answers", []):
        out[str(a.get("name", "")).strip()] = (str(a.get("value", "")).strip(), str(a.get("unit", "")).strip())
    return out, r.latency_s


def items():
    """The 320 transcribed solutions: id, image, transcript, rubric notes."""
    out = []
    for md in sorted(glob.glob(str(SRC / "Rectified_recognized_markdown_done_Anon/Final_4_LLM_judge/*/models/*/Compare/*_markdown.md"))):
        p = Path(md)
        hw_student = p.parts[-5].replace("Homework_collected_database_trial_", "")
        q = p.name.replace("_markdown.md", "")                     # "4_3-3" → P4.3-3
        rubric = SRC / "Screenshot_output_anon/rubric_outputs" / f"P{q.replace('_', '.')}.json"
        if rubric.exists():
            out.append({"id": f"{hw_student}/{q}", "question": f"P{q.replace('_', '.')}",
                        "image": str(p.with_name(f"{q}_source.png")), "transcript": p.read_text(),
                        "notes": json.loads(rubric.read_text()).get("notes", "")})
    return out


# ── build: gold from rubric notes + expert transcripts ───────────────────────

def cmd_build(_args):
    """Expected results per question and the student's final values, both double-extracted."""
    eps = {QWEN: endpoint(QWEN), GEMMA: endpoint(GEMMA)}
    its = items()
    # 1. Expected results per question (two models; keep values both found)
    expected = {}
    notes = {it["question"]: it["notes"] for it in its}

    def exp_one(q):
        a, _ = chat_list(eps[QWEN], EXPECTED_PROMPT.format(notes=notes[q]))
        b, _ = chat_list(eps[GEMMA], EXPECTED_PROMPT.format(notes=notes[q]))
        keep = {}
        for name, (v, u) in a.items():
            if numeric.parse_number(v).ok and any(numeric.numbers_agree(v, vb) for vb, _ in b.values()):
                keep[name] = {"value": v, "unit": u}
        return q, keep

    with ThreadPoolExecutor(16) as pool:
        expected = dict(pool.map(exp_one, sorted(notes)))

    # 2. Student's final values from the expert transcript (two models must agree)
    def gold_one(it):
        exp = expected.get(it["question"], {})
        if not exp:
            return it["id"], {}, 0
        prompt = FINAL_PROMPT.format(source="This is an expert transcription of", names=", ".join(exp)) + \
            "\n---\n" + it["transcript"][:12000]
        a, _ = chat_list(eps[QWEN], prompt)
        b, _ = chat_list(eps[GEMMA], prompt)
        gold, dropped = {}, 0
        for name in exp:
            va, vb = a.get(name, ("", ""))[0], b.get(name, ("", ""))[0]
            same = (not va and not vb) or (va and vb and (numeric.numbers_agree(va, vb) or va.replace(" ", "") == vb.replace(" ", "")))
            if same:
                gold[name] = va
            else:
                dropped += 1
        return it["id"], gold, dropped

    DATA.mkdir(parents=True, exist_ok=True)
    rows, n_drop = [], 0
    with ThreadPoolExecutor(16) as pool:
        golds = {i: (g, d) for i, g, d in pool.map(gold_one, its)}
    for it in its:
        g, d = golds[it["id"]]
        n_drop += d
        if g:
            rows.append({"id": it["id"], "question": it["question"], "image": it["image"],
                         "expected": {k: expected[it["question"]][k] for k in g}, "gold": g})
    (DATA / "manifest.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    n_items = sum(len(r["gold"]) for r in rows)
    print(f"{len(rows)} solutions, {n_items} final values with agreed gold; {n_drop} dropped (extractors disagreed); "
          f"questions with plain-number results: {sum(1 for v in expected.values() if v)}/{len(expected)}")


def load():
    return [json.loads(l) for l in (DATA / "manifest.jsonl").read_text().splitlines() if l.strip()]


# ── read: every reader on every image ────────────────────────────────────────

def cmd_read(_args):
    """VLMs read the image; OCR models transcribe, then Qwen extracts the finals from their text."""
    from PIL import Image
    from app.pipeline import llm
    from app.prompts import prompt_pipeline as P
    eps = {n: endpoint(n) for n in [QWEN, GEMMA, *OCRS]}
    f = OUT / "readings.json"
    cache = json.loads(f.read_text()) if f.exists() else {}
    OUT.mkdir(parents=True, exist_ok=True)

    def run(job):
        row, src = job
        img = Image.open(row["image"]).convert("RGB")
        names = ", ".join(row["gold"])
        if src in ("qwen", "gemma"):
            got, lat = chat_list(eps[QWEN if src == "qwen" else GEMMA],
                                 FINAL_PROMPT.format(source="This image is", names=names), [img])
        else:
            name = next(n for n, s in OCRS.items() if s == src.split(">")[0])
            r = llm.chat(eps[name], P.OCR_PROMPTS[eps[name].spec.get("prompt_style")], [img], max_tokens=4096)
            got, lat2 = chat_list(eps[QWEN], FINAL_PROMPT.format(source="This is an OCR transcription of", names=names)
                                  + "\n---\n" + r.text[:12000])
            lat = r.latency_s + lat2
        return row["id"], src, {"values": {k: got.get(k, ("", ""))[0] for k in row["gold"]}, "latency": round(lat, 2)}

    sources = ["qwen", "gemma"] + [f"{s}>qwen" for s in OCRS.values()]
    jobs = [(row, s) for row in load() for s in sources if s not in cache.get(row["id"], {})]
    t0, done = time.time(), 0
    with ThreadPoolExecutor(32) as pool:
        for rid, src, res in pool.map(run, jobs):
            cache.setdefault(rid, {})[src] = res
            done += 1
            if done % 200 == 0:
                f.write_text(json.dumps(cache))
                print(f"{done}/{len(jobs)} readings, {time.time() - t0:.0f}s", flush=True)
    f.write_text(json.dumps(cache))
    print(f"done: {len(jobs)} readings in {time.time() - t0:.0f}s")


# ── score ────────────────────────────────────────────────────────────────────

def verdict(value: str, exp: dict) -> bool:
    """Teacher's rule: number in the key unit within ±0.001, unit ignored, no conversion."""
    return numeric.compare(value, {"answer": exp["value"], "tolerance": TOL, "unit": exp.get("unit") or None}).status == "correct"


def cmd_score(_args):
    """Single readers, pairs, tie-break and majority; read accuracy, silent errors, TA, time per solution."""
    rows, cache = load(), json.loads((OUT / "readings.json").read_text())
    sources = sorted({s for v in cache.values() for s in v})
    res = []
    combos = [("single", [s], "") for s in sources] + [("pair", list(c), "") for c in itertools.combinations(sources, 2)]
    combos += [(m, [a, b, c], m.split("+")[1]) for a, b in itertools.combinations(sources, 2) for c in sources
               if c not in (a, b) for m in ("pair+tiebreak", "pair+majority")]
    n_items = sum(len(r["gold"]) for r in rows)
    for arch, combo, mode in combos:
        n = auto = silent = read_ok = 0
        secs = 0.0
        for r in rows:
            c = cache.get(r["id"], {})
            for s in combo:
                secs += (c.get(s) or {}).get("latency", 0)
            for name, gold in r["gold"].items():
                rs = []
                for s in combo:
                    v = ((c.get(s) or {}).get("values") or {}).get(name, "")
                    rs.append({"status": "answered" if v else "blank", "value": v})
                acc, _ = decide("numerical", rs, mode)
                n += 1
                if acc is None:
                    continue
                auto += 1
                v = acc.get("value", "")
                read_ok += (not v and not gold) or bool(v and gold and numeric.numbers_agree(v, gold))
                silent += verdict(v, r["expected"][name]) != verdict(gold, r["expected"][name])
        res.append({"arch": arch, "readers": " + ".join(combo), "items": n, "silent_errors": silent,
                    "auto_rate": round(auto / n, 3), "ta_items": n - auto,
                    "read_exact_auto": round(read_ok / max(1, auto), 3), "sec_per_solution": round(secs / len(rows), 1)})
    rank = lambda x: (x["silent_errors"], -x["auto_rate"], x["sec_per_solution"])  # noqa: E731
    import csv
    with open(OUT / "results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(res[0]))
        w.writeheader()
        w.writerows(res)
    cols = list(res[0])
    tbl = lambda rs: ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] + ["| " + " | ".join(str(x[c]) for c in cols) + " |" for x in rs]  # noqa: E731
    gold_ok = sum(verdict(g, r["expected"][k]) for r in rows for k, g in r["gold"].items())
    md = ["# EDU-CIRCUIT-HW — final numerical answers in real worked solutions", "",
          f"Generated {time.strftime('%Y-%m-%d %H:%M')} by `python eval/edu_circuit.py score`. "
          f"{len(rows)} solutions (Georgia Tech ECE 2040, 2025), {n_items} final values; "
          f"{gold_ok} of them are correct under the teacher's rule.", "",
          "- Gold = the student's final value from the **expert transcription**, extracted by Qwen and Gemma "
          "(kept only where both agree); expected values from the rubric notes (both must agree).",
          "- *silent_errors* = auto-accepted values whose marks (correct / wrong under the teacher's rule) differ "
          "from the gold; *read_exact_auto* = accepted value equals the gold value.",
          "- Readers: `qwen` / `gemma` read the image; `X>qwen` = OCR model X transcribes the image, Qwen extracts "
          "the final values from that text. *sec_per_solution* = model time summed over calls.",
          "- Dataset licence not stated in the download → internal evaluation only.", "",
          "## Single readers", ""] + tbl(sorted((x for x in res if x["arch"] == "single"), key=rank))
    best = {}
    for x in res:
        if x["arch"] not in best or rank(x) < rank(best[x["arch"]]):
            best[x["arch"]] = x
    md += ["", "## Best per architecture", ""] + tbl(sorted(best.values(), key=rank))
    md += ["", "## Top 15", ""] + tbl(sorted(res, key=rank)[:15])
    (OUT / "README.md").write_text("\n".join(md) + "\n")
    print(f"wrote {OUT / 'README.md'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "read", "score"])
    args = ap.parse_args()
    {"build": cmd_build, "read": cmd_read, "score": cmd_score}[args.cmd](args)


if __name__ == "__main__":
    main()
