#!/usr/bin/env python3
"""mendeley_seg.py — does better segmentation close the type-C gap? (Mendeley, 50 sheets)

    python eval/mendeley_seg.py read  --variant seg2       # new box prompt → crops → Qwen + GLM-OCR read crops
    python eval/mendeley_seg.py read  --variant pagetext   # no boxes: Qwen transcribes whole pages by label,
                                                           #   Gemma transcribes whole pages as plain text with [[Qnn]] markers
    python eval/mendeley_seg.py grade --variant seg2|pagetext   # grader Gemma + prompt v2 (as the chosen set-up)
    python eval/mendeley_seg.py score                       # → eval/reports/mendeley_seg/README.md

Baseline = the first run (segment_prompt → crops → Qwen + GLM-OCR), graded by gemma-v2 in
eval/reports/mendeley_sweep/grades.json. Short answers only (S1–S15 = Q21–Q35).
"""
from __future__ import annotations

import argparse
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

import dataset  # noqa: E402
from arch_sweep import endpoint  # noqa: E402
from mendeley_sweep import subj_metrics, boot_diff  # noqa: E402

SET = ROOT / "eval" / "data" / "mendeley"
BASE = ROOT / "eval" / "reports" / "mendeley"
OUT = ROOT / "eval" / "reports" / "mendeley_seg"
QWEN, GLM, GEMMA = "qwen38-27b-fp8", "glm-ocr", "gemma4-31b-fp8"
LABEL_RE = re.compile(r"^\s*(?:Q\.?\s*|Ans\.?\s*)?(2[1-9]|3[0-5])\s*(?:[.,:)|\]\-]|\s)(?!\s*[\d%])\s*(.*)$", re.I)


def load(name):
    f = OUT / name
    return json.loads(f.read_text()) if f.exists() else {}


def save(name, data):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(data))


def subj_questions(sh):
    """Short-answer questions only (S1–S15, labels Q21–Q35)."""
    from app.pipeline import readers
    return [q for q in readers.questions_for(sh.paper) if q.kind == "subjective"]


def clean_pages(sh):
    """Non-blank pages after the quality step (same as the first run)."""
    from app.pipeline import quality
    return [img for p in sh.pages for img, rep in [quality.prepare(p)] if not rep.blank]


# ── variant seg2: improved box prompt ────────────────────────────────────────

def read_seg2(sh, eps):
    from app.pipeline import llm, readers
    from app.prompts import prompt_pipeline as P
    qs, pages, t = subj_questions(sh), clean_pages(sh), {"segment": 0.0, QWEN: 0.0, GLM: 0.0}
    by_label = {q.label.upper(): q for q in qs}
    crops = {}
    for page in pages:
        r = llm.chat(eps[QWEN], P.segment_prompt_v2([q.label for q in qs]), [page],
                     schema=P.SEGMENT_SCHEMA, max_tokens=4096)
        t["segment"] += r.latency_s
        for a in (r.data or {}).get("answers", []):
            lab = str(a.get("label", "")).strip().upper()
            lab = lab if lab.startswith("Q") else "Q" + re.sub(r"\D", "", lab)
            if lab in by_label and len(a.get("bbox") or []) == 4:
                crops.setdefault(by_label[lab].id, []).append(readers._crop(page, a["bbox"]))
    out = {}
    for q in qs:
        if q.id not in crops:
            continue
        ra = readers.read_general(eps[QWEN], q, crops[q.id])
        rb = readers.read_ocr(eps[GLM], q, crops[q.id])
        t[QWEN] += ra.latency_s
        t[GLM] += rb.latency_s
        out[q.id] = {"a": ra.value, "b": rb.value}
    return out, t


# ── variant pagetext: whole-page transcription grouped by label ──────────────

def split_ocr_page(text, last_label):
    """GLM-OCR page text → ({label: text}, last label on page). Lines before the first label continue last_label."""
    from app.pipeline import readers
    parts, cur = {}, last_label
    for line in readers.clean_ocr(text).splitlines():
        line = re.sub(r"~~.*?~~", "", line)                     # drop struck-out text if the OCR marked it
        m = LABEL_RE.match(line)
        if m:
            cur = f"Q{m.group(1)}"
            line = m.group(2)
        if cur and line.strip():
            parts.setdefault(cur, []).append(line.strip())
    return {k: "\n".join(v) for k, v in parts.items()}, cur


def split_marked(text, last_label):
    """Gemma page text with [[Qnn]] markers → ([(label, crossed, text)], last label)."""
    out, cur, crossed, buf = [], last_label, False, []
    def flush():
        if cur and "\n".join(buf).strip():
            out.append((cur, crossed, "\n".join(buf).strip()))
    for line in (text or "").splitlines():
        m = re.match(r"^\s*\[\[\s*(Q?\d+|CONTINUED)\s*(CROSSED)?\s*\]\]\s*(.*)$", line, re.I)
        if m:
            flush()
            lab = m.group(1).upper()
            cur = last_label if lab == "CONTINUED" else (lab if lab.startswith("Q") else "Q" + lab)
            crossed, buf = bool(m.group(2)), [m.group(3)]
        else:
            buf.append(line)
    flush()
    return out, (out[-1][0] if out else last_label)


def merge(store, items):
    """Add one page's [(label, crossed, text)]; a crossed-out attempt is dropped when the label has a rewrite."""
    page = {}
    for lab, crossed, x in items:
        page.setdefault(lab, []).append((crossed, x))
    for lab, its in page.items():
        keep = [x for c, x in its if not c] or [x for _, x in its]
        store[lab] = "\n".join(filter(None, [store.get(lab, "")] + keep))


def read_pagetext(sh, eps):
    from app.pipeline import llm, readers
    from app.prompts import prompt_pipeline as P
    all_labels = [q.label for q in readers.questions_for(sh.paper)]        # MCQ labels too, so "7. A" is not Q27
    qs, pages, t = subj_questions(sh), clean_pages(sh), {QWEN: 0.0, GEMMA: 0.0}
    qa, qb, last_a, last_b = {}, {}, None, None
    for page in pages:
        # Transcript A — Qwen, JSON answers by label
        r = llm.chat(eps[QWEN], P.page_text_prompt(all_labels), [page], schema=P.PAGE_TEXT_SCHEMA, max_tokens=8192)
        t[QWEN] += r.latency_s
        items = []
        for a in (r.data or {}).get("answers", []):
            lab = str(a.get("label", "")).strip().upper()
            lab = last_a if lab == "CONTINUED" else (lab if lab.startswith("Q") else "Q" + re.sub(r"\D", "", lab))
            if lab and str(a.get("text", "")).strip():
                items.append((lab, bool(a.get("fully_crossed_out")), a["text"].strip()))
        if items:
            last_a = items[-1][0]
        merge(qa, items)
        # Transcript B — Gemma, plain text with [[Qnn]] markers split in code
        r = llm.chat(eps[GEMMA], P.page_text_plain_prompt(all_labels), [page], max_tokens=8192)
        t[GEMMA] += r.latency_s
        items, last_b = split_marked(r.text, last_b)
        merge(qb, items)
    out = {q.id: {"a": qa.get(q.label, ""), "b": qb.get(q.label, "")} for q in qs if qa.get(q.label) or qb.get(q.label)}
    return out, t


def cmd_read(args):
    eps = {n: endpoint(n) for n in (QWEN, GLM, GEMMA)}
    fn = {"seg2": read_seg2, "pagetext": read_pagetext}[args.variant]
    cache = load(f"read_{args.variant}.json")
    todo = [sh for sh in dataset.load(str(SET)) if sh.sheet_id not in cache
            and (not args.sheets or sh.sheet_id in args.sheets.split(","))]   # --sheets for quick tests

    def run(sh):
        t0 = time.time()
        ans, t = fn(sh, eps)
        return sh.sheet_id, {"answers": ans, "time": t, "wall": round(time.time() - t0, 1)}

    with ThreadPoolExecutor(6) as pool:                          # 6 sheets at once
        for sid, res in pool.map(run, todo):
            cache[sid] = res
            save(f"read_{args.variant}.json", cache)
            print(f"{sid}: {len(res['answers'])}/15 answers, {res['wall']}s", flush=True)


# ── grade with the chosen grader (Gemma + prompt v2) ─────────────────────────

def cmd_grade(args):
    from PIL import Image
    from app.pipeline.grader import grade
    ep = endpoint(GEMMA)
    reads, cache = load(f"read_{args.variant}.json"), load(f"grades_{args.variant}.json")   # one cache per variant
    for sh in dataset.load(str(SET)):
        if sh.sheet_id not in reads:
            continue
        ans, todo = reads[sh.sheet_id]["answers"], []
        for i in range(1, 16):
            qid, m = f"S{i}", sh.gold.get(f"S{i}", {}).get("marks")
            key = f"{sh.sheet_id}|{qid}|{args.variant}"
            if m is not None and key not in cache:
                todo.append((key, qid, i - 1))

        def run(job):
            key, qid, qi = job
            a = ans.get(qid)
            if not a:                                            # not located → TA in the pipeline
                return key, {"marks": None, "latency": 0.0, "located": False}
            if not a["a"].strip() and not a["b"].strip():
                return key, {"marks": 0.0, "latency": 0.0, "located": True, "blank": True}
            g = grade(ep, sh.paper["subjectiveQuestions"][qi], sh.paper["subjectiveRubrics"][qi], a["a"], a["b"],
                      [], sh.paper.get("subject", ""), 2.0, version="v2")
            return key, {"marks": g.marks, "latency": g.latency_s, "located": True, "error": g.error}

        with ThreadPoolExecutor(32) as pool:
            for key, res in pool.map(run, todo):
                cache[key] = res
        save(f"grades_{args.variant}.json", cache)
        print(f"{sh.sheet_id}: {len(todo)} gradings", flush=True)


# ── score ────────────────────────────────────────────────────────────────────

def cmd_score(_args):
    sweep = json.loads((ROOT / "eval/reports/mendeley_sweep/grades.json").read_text())
    grades = {**load("grades_seg2.json"), **load("grades_pagetext.json")}
    sheets = list(dataset.load(str(SET)))
    rows, per_sheet, md = {}, {}, []

    def base_rec(sh, qid):
        # baseline: not located = no crop in the first run's readings
        loc = bool(json.loads((BASE / f"{sh.sheet_id}.json").read_text())["questions"].get(qid, {}).get("crop"))
        g = sweep.get(f"{sh.sheet_id}|{qid}|gemma-v2|qwen+glm")
        return {"marks": g["marks"] if loc and g else None, "located": loc, "latency": (g or {}).get("latency", 0)}

    for variant in ("baseline", "seg2", "pagetext"):
        recs = []
        for sh in sheets:
            for i in range(1, 16):
                qid, t = f"S{i}", sh.gold.get(f"S{i}", {}).get("marks")
                if t is None or not 0 <= t <= 2:          # skip CSV marks outside 0–2 (one "4")
                    continue
                r = base_rec(sh, qid) if variant == "baseline" else grades.get(f"{sh.sheet_id}|{qid}|{variant}")
                if r is None:
                    break
                recs.append((sh.sheet_id, t, r))
            else:
                continue
        if not recs or len({s for s, *_ in recs}) < len(sheets):
            continue
        as_zero = [((r["marks"] if r["located"] else 0.0) or 0.0, t) for _, t, r in recs]
        located = [(r["marks"], t) for _, t, r in recs if r["located"]]
        rows[variant] = {"found": f"{len(located)}/{len(recs)}", "zero": subj_metrics(as_zero),
                         "ta": subj_metrics(located), "to_ta": len(recs) - len(located)}
        per_sheet[variant] = {}
        for s, t, r in recs:
            per_sheet[variant].setdefault(s, []).append(abs(((r["marks"] if r["located"] else 0.0) or 0.0) - t))

    md += ["# Type C — segmentation variants (Mendeley, 50 sheets)", "",
           f"Generated {time.strftime('%Y-%m-%d %H:%M')} by `python eval/mendeley_seg.py score`. "
           "Grader Gemma + prompt v2 in every row; only how answers are found and transcribed changes.",
           "- *baseline*: first run — Qwen draws one box per answer (old prompt), Qwen + GLM-OCR read the crops.",
           "- *seg2*: new box prompt (check every label, skip crossed-out copy, ignore show-through, no mixed boxes).",
           "- *pagetext*: no boxes — Qwen transcribes each whole page grouped by label (struck-out text left out);"
           " Gemma transcribes the whole page as plain text with [[Qnn]] markers, split in code (GLM-OCR drops margin labels).", "",
           "| variant | answers found | MAE (not found = 0) | exact | bias | MAE (not found → TA) | bias | to TA |",
           "|---|---|---|---|---|---|---|---|"]
    for v, r in rows.items():
        md.append(f"| {v} | {r['found']} | {r['zero']['mae']} | {r['zero']['exact']} | {r['zero']['bias']} | "
                  f"{r['ta']['mae']} | {r['ta']['bias']} | {r['to_ta']} |")
    if "baseline" in per_sheet:
        md += ["", "MAE difference vs baseline (not found = 0), 95 % interval over sheets:", "",
               "| variant | difference | 95 % interval |", "|---|---|---|"]
        for v in per_sheet:
            if v != "baseline":
                d, lo, hi = boot_diff(per_sheet[v], per_sheet["baseline"])
                md.append(f"| {v} | {d:+.3f} | [{lo:+.3f}, {hi:+.3f}] |")
    # time per paper (model seconds)
    md += ["", "Model seconds per paper (reading + grader):", "", "| variant | reading | grader | wall (6 sheets in parallel) |",
           "|---|---|---|---|"]
    for v in ("seg2", "pagetext"):
        rd = load(f"read_{v}.json")
        if rd:
            g = [sum(x.get("latency", 0) for k, x in grades.items() if k.startswith(s + "|") and k.endswith("|" + v)) for s in rd]
            md.append(f"| {v} | {statistics.mean(sum(x['time'].values()) for x in rd.values()):.0f} | "
                      f"{statistics.mean(g):.0f} | {statistics.mean(x['wall'] for x in rd.values()):.0f} |")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["read", "grade", "score"])
    ap.add_argument("--variant", choices=["seg2", "pagetext"])
    ap.add_argument("--sheets", default="")
    args = ap.parse_args()
    {"read": cmd_read, "grade": cmd_grade, "score": cmd_score}[args.cmd](args)


if __name__ == "__main__":
    main()
