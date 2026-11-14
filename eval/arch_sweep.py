#!/usr/bin/env python3
"""arch_sweep.py — every reader / grader architecture on the own test sheets.

    python eval/arch_sweep.py import     # label CSVs + keys → eval/data/own_{omr,mcq,mcqnum}/manifest.jsonl
    python eval/arch_sweep.py read       # run every live model once per sheet (cached, resumable; GPUs up)
    python eval/arch_sweep.py score      # combine the cached readings into every architecture → report

Sets: omr (15 sheets × 20 Q), mcq (15 × 10 handwritten letters), mcqnum (papers 2A/2B/2C, 5 × 5).

Single "sources" (each model run once, results cached in eval/reports/arch_sweep/raw/<sheet>.json):
  handwritten  crop:<seg>><reader>  segmenter (Qwen / Gemma) boxes each answer → reader reads the crop
               page><reader>        whole page in one call (VLM: JSON; OCR model: text parsed "N. answer")
               direct><vlm>         VLM reads AND grades the page against the key in one call
  omr          omr:template (learned bubble map) · omr:legacy (old OpenCV engine)
               page><vlm> (VLM reads the bubbles) · direct><vlm>
Architectures (score step, all offline from the cache):
  single A · pair A+B (agree → accept, else TA) · A+B + tie-break C on abstention (current pipeline)
  · A+B + C majority vote on any disagreement; × numerical grader: code | Qwen | Gemma.
Outputs: eval/reports/arch_sweep/{results.csv, README.md, grader_check.md}.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "eval"))

from app.pipeline import numeric, readers  # noqa: E402
from app.pipeline.readers import Question  # noqa: E402

TP = ROOT / "eval" / "test_papers"
OUT = ROOT / "eval" / "reports" / "arch_sweep"
RAW = OUT / "raw"
VLMS = {"qwen38-27b-fp8": "qwen", "gemma4-31b-fp8": "gemma"}
OCRS = {"paddleocr-vl-1.6": "paddle", "glm-ocr": "glm", "chandra-ocr-2": "chandra"}
SHORT = {**VLMS, **OCRS}
# set → (label CSV(s), key file per CSV)
SETS = {"omr": [("omr_labels.csv", "omr_basic_science.json")],
        "mcq": [("mcq_labels.csv", "mcq_basic_science.json")],
        "mcqnum": [(f"paper_{p}_labels.csv", f"paper_{p}.json") for p in ("2A", "2B", "2C")]}


# ── Normalisation shared by import and scoring ───────────────────────────────

def norm_mcq(s: str) -> str:
    """'ACB' / 'A, C,b' / 'C A' → 'A,B,C'; other tokens (digits) kept: 'A3' → '3,A'; '?' stays."""
    s = (s or "").strip()
    if s in ("", "?"):
        return s
    return ",".join(sorted({t.upper() for t in re.findall(r"[A-Za-z]|\d+", s)}))


def same_value(kind: str, a: str, b: str) -> bool:
    """Do two answers say the same thing (blank = blank)?"""
    a, b = (a or "").strip(), (b or "").strip()
    if not a or not b:
        return not a and not b
    if kind == "mcq":
        return norm_mcq(a) == norm_mcq(b)
    agree = numeric.numbers_agree(a, b)
    return bool(agree) if agree is not None else re.sub(r"\s+", "", a).lower() == re.sub(r"\s+", "", b).lower()


# ── import: label CSVs → manifest ────────────────────────────────────────────

def cmd_import(_args):
    """Validate every label row and write one manifest per set (pages point into test_papers/photos)."""
    for set_name, files in SETS.items():
        out = ROOT / "eval" / "data" / f"own_{set_name}"
        (out / "papers").mkdir(parents=True, exist_ok=True)
        rows_out = []
        for csv_name, key_name in files:
            paper = json.loads((TP / "keys" / key_name).read_text())
            shutil.copy(TP / "keys" / key_name, out / "papers" / key_name)
            qs = readers.questions_for(paper)
            with open(TP / "labels" / csv_name, newline="") as f:
                for n, row in enumerate(csv.DictReader(f), start=2):
                    # Every question column must exist and the photo must be there
                    missing = [q.label for q in qs if q.label not in row]
                    photo = TP / "photos" / (row.get("photo_file") or "").strip()
                    if missing or not photo.is_file():
                        sys.exit(f"{csv_name} row {n}: missing columns {missing} or photo {photo.name}")
                    gold = {}
                    for q in qs:
                        v = (row[q.label] or "").strip()
                        gold[q.id] = {"answer": norm_mcq(v) if q.kind == "mcq" else v}
                        # Not an option letter on an MCQ: kept as written (a deliberate edge case), but reported
                        if q.kind == "mcq" and v not in ("", "?") and not re.fullmatch(r"[A-Da-d ,]+", v):
                            print(f"  note {csv_name} row {n} {q.label}: non-letter answer {v!r} kept as written")
                    rows_out.append({"sheet_id": row["sheet_id"], "split": "test", "paper": f"papers/{key_name}",
                                     "sheet_type": "omr" if set_name == "omr" else "handwritten",
                                     "pages": [f"../../test_papers/photos/{photo.name}"], "gold": gold,
                                     "layout": row.get("layout"), "edge_cases": row.get("edge_cases", ""),
                                     "notes": row.get("notes", "")})
        (out / "manifest.jsonl").write_text("\n".join(json.dumps(r) for r in rows_out) + "\n")
        print(f"{set_name}: {len(rows_out)} sheets → {out / 'manifest.jsonl'}")


def load_set(set_name: str):
    """[(manifest row, paper, questions)] for one set."""
    d = ROOT / "eval" / "data" / f"own_{set_name}"
    out = []
    for line in (d / "manifest.jsonl").read_text().splitlines():
        row = json.loads(line)
        paper = json.loads((d / row["paper"]).read_text())
        out.append((row, paper, readers.questions_for(paper)))
    return out


# ── read: run each model once per sheet ──────────────────────────────────────

def endpoint(name):
    """Live endpoint for a registry model (None if its server is down)."""
    from app.pipeline import llm
    url = llm._endpoint_urls().get(name)
    return llm.Endpoint(name, url, llm.registry()["models"][name]) if url and llm._is_up(url) else None


def rd(status="", value="", raw="", latency=0.0, **extra) -> dict:
    """Compact cached reading."""
    return {"status": status, "value": value, "raw": raw[:1500], "latency": round(latency, 2), **extra}


def page_ocr_answers(text: str, qs) -> dict:
    """Whole-page OCR text → {qid: reading} from lines that start with a question number."""
    by_num = {re.sub(r"\D", "", q.label): q for q in qs}
    found = {}
    for line in readers.clean_ocr(text).splitlines():
        m = re.match(r"^\s*(?:Q\.?\s*)?(\d{1,2})\s*[.,:)](?!\d)\s*(.*)$", line)
        if m and m.group(1) in by_num and by_num[m.group(1)].id not in found:
            q, body = by_num[m.group(1)], m.group(2).strip()
            val = readers.parse_letters(body) if q.kind == "mcq" else readers.parse_final_number(body)
            found[q.id] = (body, val)
    return {q.id: rd("answered" if found.get(q.id, ("", ""))[1] else ("unclear" if found.get(q.id, ("", ""))[0] else "blank"),
                     found.get(q.id, ("", ""))[1], found.get(q.id, ("", ""))[0]) for q in qs}


def json_answers(data: dict, qs, key: str = "value") -> dict:
    """VLM page JSON → {qid: reading}; questions it skipped count as blank."""
    by_label = {q.label.upper(): q for q in qs}
    got = {}
    for a in (data or {}).get("answers", []):
        lab = str(a.get("label", "")).strip().upper()
        lab = lab if lab.startswith("Q") else f"Q{re.sub(r'[^0-9]', '', lab)}"
        if lab in by_label:
            got[by_label[lab].id] = a
    out = {}
    for q in qs:
        a = got.get(q.id, {})
        val = str(a.get(key, "") or "").strip()
        val = norm_mcq(val) if q.kind == "mcq" else val
        if "correct" in a:                                     # direct grading
            out[q.id] = rd("answered" if val else "blank", val, correct=bool(a["correct"]))
        else:
            out[q.id] = rd(a.get("status", "blank") if val or a.get("status") == "unclear" else "blank", val)
    return out


def key_lines(paper: dict, qs) -> list:
    """Answer key as text for the direct-grading prompt."""
    lines = []
    for q in qs:
        if q.kind == "mcq":
            lines.append(f"{q.label}: {paper['mcqAnswers'][q.id]}")
        else:
            k = paper["numericalAnswers"][q.id]
            lines.append(f"{q.label}: {k['answer']} ± {k.get('tolerance', 0):g} (unit {k.get('unit') or 'none'} — ignored)")
    return lines


def read_handwritten(row, paper, qs, eps, cache) -> None:
    """All handwritten sources for one sheet (adds only the sources missing from the cache)."""
    from app.pipeline import llm, quality
    from app.prompts import prompt_pipeline as P
    page, rep = quality.prepare(str(TP / "photos" / Path(row["pages"][0]).name))
    cache["meta"] = {"blank_page": rep.blank, "quality_ok": rep.ok, "reasons": rep.reasons}
    jobs = []

    # Segmentation by each VLM (boxes cached), then every reader on every crop
    for seg, s_short in VLMS.items():
        if eps.get(seg) is None:
            continue
        key = f"seg:{s_short}"
        if key not in cache:
            r = llm.chat(eps[seg], P.segment_prompt([q.label for q in qs]), [page], schema=P.SEGMENT_SCHEMA, max_tokens=4096)
            cache[key] = {"answers": (r.data or {}).get("answers", []), "latency": r.latency_s, "error": r.error}
        boxes = {}
        for a in cache[key]["answers"]:
            q = next((q for q in qs if q.label.upper() == str(a.get("label", "")).strip().upper()), None)
            if q and len(a.get("bbox") or []) == 4:
                boxes.setdefault(q.id, []).append(a["bbox"])
        for name, r_short in SHORT.items():
            src = f"crop:{s_short}>{r_short}"
            if eps.get(name) is None or src in cache:
                continue
            for q in qs:
                imgs = [readers._crop(page, b) for b in boxes.get(q.id, [])]
                jobs.append((src, q, name, imgs or [page], bool(imgs)))

    # One reading per (source, question) in parallel
    def run(job):
        src, q, name, imgs, located = job
        ep = eps[name]
        r = readers.read_general(ep, q, imgs) if name in VLMS else readers.read_ocr(ep, q, imgs)
        return src, q.id, rd(r.status, r.value, r.raw, r.latency_s, located=located, error=r.error)

    def run_page(src_name):
        src, name = src_name
        ep = eps[name]
        if src.startswith("direct>"):
            r = llm.chat(ep, P.direct_grade_prompt(key_lines(paper, qs)), [page], schema=P.DIRECT_SCHEMA, max_tokens=2048)
            return src, {**json_answers(r.data, qs, "student_answer"), "_latency": r.latency_s, "_error": r.error}
        if name in VLMS:
            r = llm.chat(ep, P.page_prompt([(q.label, q.kind) for q in qs]), [page], schema=P.PAGE_SCHEMA, max_tokens=2048)
            return src, {**json_answers(r.data, qs), "_latency": r.latency_s, "_error": r.error}
        r = llm.chat(ep, P.OCR_PROMPTS.get(ep.spec.get("prompt_style"), P.OCR_PROMPTS["general"]), [page], max_tokens=4096)
        return src, {**page_ocr_answers(r.text, qs), "_latency": r.latency_s, "_error": r.error, "_text": r.text[:4000]}

    page_jobs = [(f"page>{s}", n) for n, s in SHORT.items()] + [(f"direct>{s}", n) for n, s in VLMS.items()]
    page_jobs = [(s, n) for s, n in page_jobs if eps.get(n) is not None and s not in cache]
    with ThreadPoolExecutor(24) as pool:
        page_futs = [pool.submit(run_page, j) for j in page_jobs]
        for src, qid, reading in pool.map(run, jobs):
            cache.setdefault(src, {})[qid] = reading
        for f in page_futs:
            src, res = f.result()
            cache[src] = res


_OMR_TPL: dict = {}


def omr_template(layout: str):
    """Learned bubble template per layout (built once, VLM numbering, cached on disk)."""
    import cv2
    from app.pipeline import omr_template as T
    f = OUT / "omr_templates.json"
    if not _OMR_TPL and f.exists():
        _OMR_TPL.update(json.loads(f.read_text()))
    if layout not in _OMR_TPL:
        blank = cv2.imread(str(TP / "omr" / f"omr_layout_{layout}.png"))
        _OMR_TPL[layout] = {**T.build_template(blank, 20, 4, use_vlm=True), "confirmed": True}
        f.write_text(json.dumps(_OMR_TPL))
    return cv2.imread(str(TP / "omr" / f"omr_layout_{layout}.png")), _OMR_TPL[layout]


def read_omr(row, paper, qs, eps, cache) -> None:
    """All OMR sources for one sheet."""
    import cv2
    from PIL import Image
    from app.pipeline import llm, omr_template as T
    from app.prompts import prompt_pipeline as P
    from app.services.omr_engine import OMREngine
    path = str((TP / "photos" / Path(row["pages"][0]).name))
    photo = cv2.imread(path)

    # Learned template (the pipeline's OMR reader): letters + margin to the fill threshold
    if "omr:template" not in cache:
        blank, tpl = omr_template(row["layout"])
        t0 = time.time()
        res = T.read_sheet(photo, blank, tpl)
        cache["omr:template"] = {q.id: rd("answered" if res["answers"].get(q.id, {}).get("answer") else "blank",
                                          res["answers"].get(q.id, {}).get("answer", ""),
                                          json.dumps(res["answers"].get(q.id, {}).get("deltas", {})),
                                          (time.time() - t0) / len(qs), margin=res["answers"].get(q.id, {}).get("margin"))
                                 for q in qs} if res["aligned"] else {q.id: rd("error") for q in qs}
    # Legacy OpenCV engine (fixed-layout heuristics)
    if "omr:legacy" not in cache:
        det = OMREngine().detect(photo, len(qs))
        cache["omr:legacy"] = {q.id: rd("answered" if det.get(q.id, {}).get("answer") else "blank",
                                        norm_mcq(det.get(q.id, {}).get("answer", "")), margin=det.get(q.id, {}).get("margin"))
                               for q in qs}

    # VLM reads the bubbles / grades directly from the page
    page = Image.open(path).convert("RGB")
    page.thumbnail((2000, 2000))

    def run(src_name):
        src, name = src_name
        if src.startswith("direct>"):
            r = llm.chat(eps[name], P.direct_grade_prompt(key_lines(paper, qs), omr=True), [page], schema=P.DIRECT_SCHEMA, max_tokens=3072)
            return src, {**json_answers(r.data, qs, "student_answer"), "_latency": r.latency_s, "_error": r.error}
        r = llm.chat(eps[name], P.omr_page_prompt(len(qs)), [page], schema=P.PAGE_SCHEMA, max_tokens=3072)
        return src, {**json_answers(r.data, qs), "_latency": r.latency_s, "_error": r.error}

    jobs = [(f"{k}>{s}", n) for n, s in VLMS.items() for k in ("page", "direct")
            if eps.get(n) is not None and f"{k}>{s}" not in cache]
    with ThreadPoolExecutor(4) as pool:
        for src, res in pool.map(run, jobs):
            cache[src] = res


def grade_numbers(eps) -> None:
    """LLM numerical graders (Qwen, Gemma) on every distinct (key, student value) seen anywhere."""
    from app.pipeline import llm
    from app.prompts import prompt_pipeline as P
    f = OUT / "numgrade_cache.json"
    cache = json.loads(f.read_text()) if f.exists() else {}
    todo = set()
    for row, paper, qs in load_set("mcqnum"):
        raw = json.loads((RAW / f"{row['sheet_id']}.json").read_text()) if (RAW / f"{row['sheet_id']}.json").exists() else {}
        for q in (q for q in qs if q.kind == "numerical"):
            k = paper["numericalAnswers"][q.id]
            vals = {row["gold"][q.id]["answer"]} | {(s.get(q.id) or {}).get("value", "") for s in raw.values()
                                                     if isinstance(s, dict) and q.id in s}
            for v in vals:
                for name in VLMS:
                    if eps.get(name) is not None and v and f"{name}|{k['answer']}|{v}" not in cache:
                        todo.add((name, k["answer"], k.get("unit") or "", float(k.get("tolerance") or 0), v))

    def run(t):
        name, kv, ku, tol, v = t
        r = llm.chat(eps[name], P.numeric_grade_prompt(v, kv, ku, tol), [], schema=P.NUM_GRADE_SCHEMA, max_tokens=256)
        return f"{name}|{kv}|{v}", (r.data or {}).get("correct")

    with ThreadPoolExecutor(16) as pool:
        for k, v in pool.map(run, sorted(todo)):
            cache[k] = v
    f.write_text(json.dumps(cache, indent=0))
    print(f"numerical grader calls: {len(todo)} new, {len(cache)} cached")


def cmd_read(args):
    """Fill the cache for every sheet of the chosen sets."""
    eps = {n: endpoint(n) for n in SHORT}
    print("live:", {SHORT[n]: bool(e) for n, e in eps.items()})
    RAW.mkdir(parents=True, exist_ok=True)
    for set_name in args.sets.split(","):
        for row, paper, qs in load_set(set_name):
            if args.sheets and row["sheet_id"] not in args.sheets.split(","):
                continue
            f = RAW / f"{row['sheet_id']}.json"
            cache = json.loads(f.read_text()) if f.exists() and not args.force else {}
            t0 = time.time()
            (read_omr if set_name == "omr" else read_handwritten)(row, paper, qs, eps, cache)
            f.write_text(json.dumps(cache, indent=0))
            print(f"{row['sheet_id']}: {len([k for k in cache if not k.startswith(('meta', 'seg:'))])} sources, {time.time() - t0:.0f}s", flush=True)
    grade_numbers(eps)


# ── score: every architecture from the cache ─────────────────────────────────

def abstain(r: dict) -> bool:
    """No usable answer from this reader (OMR: a fill too close to the threshold also abstains, as in routing)."""
    if r and r.get("margin") is not None and r["margin"] < 0.05:
        return True
    return not r or r.get("status") in ("unclear", "error", "missing", "") or (r.get("status") == "answered" and not r.get("value"))


def agree(kind, a, b) -> bool:
    """Same status-or-value test as the pipeline (both blank agrees; blank vs unclear does not)."""
    if abstain(a) or abstain(b):
        return False
    return same_value(kind, a.get("value", ""), b.get("value", ""))


def decide(kind, rs: list, mode: str):
    """→ (accepted reading | None for TA, latency). rs = [A], [A, B] or [A, B, C]."""
    lat = sum(r.get("latency", 0) for r in rs[:2])
    a = rs[0]
    if len(rs) == 1:
        return (None if abstain(a) else a), lat
    b = rs[1]
    if agree(kind, a, b):
        return a, lat
    if len(rs) == 2:
        return None, lat
    c = rs[2]
    # Current pipeline: C only when exactly one of A/B abstained; C must confirm the answer given
    if mode == "tiebreak":
        if abstain(a) != abstain(b):
            answered = b if abstain(a) else a
            return (answered if agree(kind, c, answered) else None), lat + c.get("latency", 0)
        return None, lat
    # Majority: C on any disagreement; 2 of 3 agreeing wins
    for x in (a, b):
        if agree(kind, c, x):
            return x, lat + c.get("latency", 0)
    return None, lat + c.get("latency", 0)


def marks_ok(kind, value, paper, qid, grader, numcache) -> bool:
    """Would this answer earn the marks? MCQ = exact set; numerical = code rule or an LLM grader."""
    if not (value or "").strip() or value.strip() == "?":
        return False
    if kind == "mcq":
        return norm_mcq(value) == norm_mcq(paper["mcqAnswers"][qid])
    k = paper["numericalAnswers"][qid]
    if grader == "code":
        return numeric.compare(value, k).status == "correct"
    got = numcache.get(f"{grader}|{k['answer']}|{value}")
    return bool(got) if got is not None else numeric.compare(value, k).status == "correct"


def cmd_score(_args):
    """Evaluate every architecture on every set; write results.csv + README.md + grader_check.md."""
    numcache = json.loads((OUT / "numgrade_cache.json").read_text()) if (OUT / "numgrade_cache.json").exists() else {}
    results, hard = [], {}
    grader_rows = []
    for set_name in SETS:
        data = []
        for row, paper, qs in load_set(set_name):
            f = RAW / f"{row['sheet_id']}.json"
            if f.exists():
                data.append((row, paper, qs, json.loads(f.read_text())))
        if not data:
            continue
        sources = sorted({s for *_, c in data for s in c if not s.startswith(("meta", "seg:"))})
        read_srcs = [s for s in sources if not s.startswith("direct>")]
        graders = ["code"] + ([f"{n}" for n in VLMS] if set_name == "mcqnum" else [])
        n_sheets = len(data)

        # Gold decision per item (code rule on the label); '?' = must go to a TA
        items = [(row, paper, q, c) for row, paper, qs, c in data for q in qs]

        def evaluate(arch, combo, mode, grader):
            stats = dict(n=0, auto=0, silent=0, read_ok=0, lat=0.0)
            for row, paper, q, c in items:
                gold = row["gold"][q.id]["answer"]
                gold_ok = marks_ok(q.kind, gold, paper, q.id, "code", numcache)
                stats["n"] += 1
                # Quality gate: a page judged blank is accepted as all-blank (pipeline behaviour)
                if c.get("meta", {}).get("blank_page"):
                    acc, lat = rd("blank", ""), 0.0
                elif combo[0].startswith("direct>"):
                    r = c.get(combo[0], {}).get(q.id) or {}
                    acc, lat = (r or None), c.get(combo[0], {}).get("_latency", 0) / max(1, len(row["gold"]))
                else:
                    rs = [c.get(s, {}).get(q.id) or {} for s in combo]
                    acc, lat = decide(q.kind, rs, mode)
                    lat += sum(c.get(s, {}).get("_latency", 0) for s in combo) / max(1, len(row["gold"]))
                stats["lat"] += lat
                if acc is None:
                    continue                                   # routed to a TA (assumed fixed)
                stats["auto"] += 1
                if combo[0].startswith("direct>"):
                    ok = bool(acc.get("correct"))
                    read_same = same_value(q.kind, acc.get("value", ""), gold)
                else:
                    ok = marks_ok(q.kind, acc.get("value", ""), paper, q.id, grader if q.kind == "numerical" else "code", numcache)
                    read_same = same_value(q.kind, acc.get("value", ""), gold)
                stats["read_ok"] += read_same
                if ok != gold_ok or gold == "?":
                    stats["silent"] += 1
                    if len(combo) == 1 and grader == "code":
                        hard.setdefault((set_name, row["sheet_id"], q.label, gold), []).append(f"{combo[0]}={acc.get('value', '') or '∅'}")
            n = stats["n"]
            return {"set": set_name, "arch": arch, "readers": " + ".join(combo), "grader": grader,
                    "items": n, "auto_rate": round(stats["auto"] / n, 3), "silent_errors": stats["silent"],
                    "auto_accuracy": round(1 - stats["silent"] / max(1, stats["auto"]), 4),
                    "final_accuracy": round(1 - stats["silent"] / n, 4),
                    "read_exact_auto": round(stats["read_ok"] / max(1, stats["auto"]), 3),
                    "ta_items": n - stats["auto"], "sec_per_sheet": round(stats["lat"] / n_sheets, 1)}

        # Singles (incl. direct grading), pairs, triples (tie-break / majority) × graders
        for g in graders:
            for s in sources:
                results.append(evaluate("single", [s], "", g))
            for a, b in itertools.combinations(read_srcs, 2):
                results.append(evaluate("pair", [a, b], "", g))
            for a, b in itertools.combinations(read_srcs, 2):
                for c in read_srcs:
                    if c not in (a, b):
                        results.append(evaluate("pair+tiebreak", [a, b, c], "tiebreak", g))
                        results.append(evaluate("pair+majority", [a, b, c], "majority", g))

        # Grader check: each numerical grader on the GOLD values (isolates grading from reading)
        if set_name == "mcqnum":
            for row, paper, q, c in items:
                if q.kind != "numerical":
                    continue
                gold = row["gold"][q.id]["answer"]
                k = paper["numericalAnswers"][q.id]
                grader_rows.append([row["sheet_id"], q.label, f"{k['answer']} {k.get('unit') or ''}".strip(), gold or "∅"]
                                   + ["✔" if marks_ok("numerical", gold, paper, q.id, g, numcache) else "✘" for g in graders])

    write_reports(results, hard, grader_rows)


def write_reports(results, hard, grader_rows):
    """results.csv (everything) + README.md (ranked summary) + grader_check.md."""
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0]))
        w.writeheader()
        w.writerows(results)

    # Rank: fewest silent errors, then most auto-accepted, then fastest
    rank = lambda r: (r["silent_errors"], -r["auto_rate"], r["sec_per_sheet"])  # noqa: E731
    cols = ["arch", "readers", "grader", "silent_errors", "auto_rate", "ta_items", "final_accuracy", "read_exact_auto", "sec_per_sheet"]
    head = "| " + " | ".join(cols) + " |\n|" + "---|" * len(cols)
    fmt = lambda r: "| " + " | ".join(str(r[c]) for c in cols) + " |"  # noqa: E731
    md = ["# Architecture sweep — own test sheets", "",
          f"Generated {time.strftime('%Y-%m-%d %H:%M')} by `python eval/arch_sweep.py score`. Full table: `results.csv` "
          f"({len(results)} rows). Per-sheet raw readings: `raw/<sheet>.json`.", "",
          "**How to read this**", "",
          "- *silent_errors*: auto-accepted answers whose marks are wrong (the number that matters — nobody checks them).",
          "- *auto_rate*: share of answers accepted without a TA; *ta_items*: answers sent to a TA (assumed fixed).",
          "- *final_accuracy*: marks-correct share after the TA fixes routed items. *read_exact_auto*: accepted value equals the label.",
          "- Readers: `crop:<segmenter>><reader>` = segment then read the crop; `page><reader>` = whole page in one call; "
          "`direct><vlm>` = VLM reads and grades in one call; `omr:template` = learned bubble map; `omr:legacy` = old OpenCV engine.",
          "- Architectures: `single`; `pair` (A and B must agree, else TA); `pair+tiebreak` (C asked only when one of A/B "
          "abstains — the current pipeline); `pair+majority` (C on any disagreement, 2 of 3 wins).",
          "- Grader: `code` = deterministic rules (MCQ exact set; numbers exact value, unit ignored, no conversion); "
          "`qwen…`/`gemma…` = LLM decides numerical correctness (MCQ always code).", ""]
    for set_name in SETS:
        rs = [r for r in results if r["set"] == set_name]
        if not rs:
            continue
        md += [f"## {set_name} ({rs[0]['items']} answers)", "", "### Top 15 architectures", "", head]
        md += [fmt(r) for r in sorted(rs, key=rank)[:15]]
        md += ["", "### Every single source (one model, no cross-check)", "", head]
        md += [fmt(r) for r in sorted((r for r in rs if r["arch"] == "single"), key=rank)]
        best = {}
        for r in rs:
            best.setdefault((r["arch"], r["grader"]), r)
            if rank(r) < rank(best[(r["arch"], r["grader"])]):
                best[(r["arch"], r["grader"])] = r
        md += ["", "### Best per architecture × grader", "", head] + [fmt(r) for r in sorted(best.values(), key=rank)]
        hs = sorted(((k, v) for k, v in hard.items() if k[0] == set_name), key=lambda kv: -len(kv[1]))[:20]
        if hs:
            md += ["", "### Hardest answers (single sources that got the marks wrong)", "",
                   "| sheet | Q | label | # wrong | readings |", "|---|---|---|---|---|"]
            md += [f"| {k[1]} | {k[2]} | {k[3] or '∅'} | {len(v)} | {'; '.join(v[:6])} |" for k, v in hs]
        md.append("")
    # Quality gate per photo (the sweep scores answers only; the live pipeline sends a flagged sheet to a TA)
    md += ["## Quality gate on the photos", "",
           "Not part of the scores above. In the live pipeline a sheet whose photo fails the gate goes to a TA "
           "as a whole; a page judged blank is accepted as all-blank.", "",
           "| sheet | judged blank | passes gate | reasons |", "|---|---|---|---|"]
    for f in sorted(RAW.glob("*.json")):
        m = json.loads(f.read_text()).get("meta")
        if m and (m["blank_page"] or not m["quality_ok"]):
            md.append(f"| {f.stem} | {'yes' if m['blank_page'] else ''} | {'yes' if m['quality_ok'] else '**no**'} | {', '.join(m['reasons'])} |")
    (OUT / "README.md").write_text("\n".join(md) + "\n")

    gm = ["# Numerical grader check (on the labelled values)", "",
          "Each grader judges the value the student actually wrote (from the label CSV), so reading errors "
          "play no part. Rule: number within the key tolerance (±0.001), unit ignored, no unit conversion. **Please verify the ✔/✘ column for `code`.**", "",
          "| sheet | Q | key | student wrote | code | Qwen | Gemma |", "|---|---|---|---|---|---|---|"]
    gm += ["| " + " | ".join(r) + " |" for r in grader_rows]
    (OUT / "grader_check.md").write_text("\n".join(gm) + "\n")
    print(f"wrote {OUT / 'README.md'}, results.csv ({len(results)} rows), grader_check.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["import", "read", "score"])
    ap.add_argument("--sets", default="omr,mcq,mcqnum")
    ap.add_argument("--sheets", default="")
    ap.add_argument("--force", action="store_true", help="ignore the cache")
    args = ap.parse_args()
    {"import": cmd_import, "read": cmd_read, "score": cmd_score}[args.cmd](args)


if __name__ == "__main__":
    main()
