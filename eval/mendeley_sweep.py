#!/usr/bin/env python3
"""mendeley_sweep.py — type-C (MCQ + subjective) architecture sweep on the 50 Mendeley sheets.

    python eval/mendeley_sweep.py pages              # whole-page MCQ reading by every model (cached)
    python eval/mendeley_sweep.py grade --stage A    # 5 grader set-ups on transcripts Qwen + GLM-OCR
    python eval/mendeley_sweep.py grade --stage B --config qwen-v2   # that grader × every transcript pair
    python eval/mendeley_sweep.py score              # → eval/reports/mendeley_sweep/{README.md, *.csv}

Inputs: eval/data/mendeley (build_mendeley.py --sheets 1-50) and the crop readings from
mendeley_readers.py (eval/reports/mendeley/Student_N.json; Qwen segments, 5 models read each crop).
Gold: the teacher's chosen MCQ letter and mark per short answer (anonymised CSV only).
Every model call's latency is stored, so the time per paper is reported for each architecture.
"""
from __future__ import annotations

import argparse
import csv
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

import dataset  # noqa: E402
from arch_sweep import decide, endpoint, norm_mcq, page_ocr_answers, json_answers, same_value  # noqa: E402
from metrics import qwk  # noqa: E402

SET = ROOT / "eval" / "data" / "mendeley"
READS = ROOT / "eval" / "reports" / "mendeley"
OUT = ROOT / "eval" / "reports" / "mendeley_sweep"
SHORT = {"qwen38-27b-fp8": "qwen", "gemma4-31b-fp8": "gemma", "paddleocr-vl-1.6": "paddle",
         "glm-ocr": "glm", "chandra-ocr-2": "chandra"}
VLMS = ("qwen38-27b-fp8", "gemma4-31b-fp8")
# Grader set-ups: model, prompt version, thinking
CONFIGS = {"qwen-v1": ("qwen38-27b-fp8", "v1", False), "qwen-v2": ("qwen38-27b-fp8", "v2", False),
           "qwen-v2-think": ("qwen38-27b-fp8", "v2", True),
           "gemma-v1": ("gemma4-31b-fp8", "v1", False), "gemma-v2": ("gemma4-31b-fp8", "v2", False)}


def sheets():
    """[(Sheet, crop readings json)] for every built sheet that has been read."""
    out = []
    for sh in dataset.load(str(SET)):
        f = READS / f"{sh.sheet_id}.json"
        if f.exists():
            out.append((sh, json.loads(f.read_text())))
    return out


def load_cache(name: str) -> dict:
    f = OUT / name
    return json.loads(f.read_text()) if f.exists() else {}


def save_cache(name: str, data: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(data))


# ── pages: whole-page MCQ reading ────────────────────────────────────────────

def cmd_pages(_args):
    """Every model reads the MCQ answers (Q1–Q20) from each non-blank page; first answer found wins."""
    from app.pipeline import llm, quality, readers
    from app.prompts import prompt_pipeline as P
    eps = {n: endpoint(n) for n in SHORT}
    cache = load_cache("pages.json")
    for sh, rd_json in sheets():
        if sh.sheet_id in cache:
            continue
        t0 = time.time()
        qs = [q for q in readers.questions_for(sh.paper) if q.kind == "mcq"]
        pages = [img for img, rep in (quality.prepare(p) for p in sh.pages) if not rep.blank]

        def run(name):
            ep, merged, lat = eps[name], {}, 0.0
            for page in pages:
                if name in VLMS:
                    r = llm.chat(ep, P.page_prompt([(q.label, q.kind) for q in qs]), [page], schema=P.PAGE_SCHEMA, max_tokens=2048)
                    got = json_answers(r.data, qs)
                else:
                    r = llm.chat(ep, P.OCR_PROMPTS.get(ep.spec.get("prompt_style"), P.OCR_PROMPTS["general"]), [page], max_tokens=4096)
                    got = page_ocr_answers(r.text, qs)
                lat += r.latency_s
                for qid, v in got.items():                              # keep the first real answer
                    if qid not in merged or (merged[qid]["status"] == "blank" and v["status"] != "blank"):
                        merged[qid] = v
            return f"page>{SHORT[name]}", {**merged, "_latency": round(lat, 1)}

        with ThreadPoolExecutor(5) as pool:
            cache[sh.sheet_id] = dict(pool.map(run, [n for n in SHORT if eps.get(n)]))
        cache[sh.sheet_id]["_wall"] = round(time.time() - t0, 1)
        save_cache("pages.json", cache)
        print(f"{sh.sheet_id}: pages read, {time.time() - t0:.0f}s", flush=True)


# ── grade: subjective answers ────────────────────────────────────────────────

def answers(sh, rd_json):
    """[(qid, question index, teacher mark, crop path)] for short answers the teacher marked (0–2)."""
    out = []
    for i in range(1, 16):
        qid = f"S{i}"
        m = sh.gold.get(qid, {}).get("marks")
        q = rd_json["questions"].get(qid, {})
        if m is not None and 0 <= m <= 2:
            out.append((qid, i - 1, m, q.get("crop")))
    return out


def cmd_grade(args):
    """Run grader set-ups on transcript pairs; cache key sheet|qid|config|readerA+readerB."""
    from PIL import Image
    from app.pipeline import llm
    from app.pipeline.grader import grade
    eps = {n: endpoint(n) for n in VLMS}
    cache = load_cache("grades.json")
    if args.stage == "A":
        jobs = [(c, ("qwen38-27b-fp8", "glm-ocr")) for c in CONFIGS]
    else:
        jobs = [(args.config, pair) for pair in itertools.combinations(SHORT, 2)]
    for sh, rd_json in sheets():
        if args.sheets and sh.sheet_id not in args.sheets.split(","):
            continue
        t0, todo = time.time(), []
        for qid, qi, _m, crop in answers(sh, rd_json):
            for cfg, (ra, rb) in jobs:
                key = f"{sh.sheet_id}|{qid}|{cfg}|{SHORT[ra]}+{SHORT[rb]}"
                if key not in cache:
                    todo.append((key, qid, qi, crop, cfg, ra, rb))

        def run(job):
            key, qid, qi, crop, cfg, ra, rb = job
            q = rd_json["questions"][qid]
            ta = (q["readings"].get(ra) or {}).get("value", "")
            tb = (q["readings"].get(rb) or {}).get("value", "")
            if not ta.strip() and not tb.strip():                       # pipeline: blank → 0, no grader call
                return key, {"marks": 0.0, "latency": 0.0, "blank": True}
            model, version, thinking = CONFIGS[cfg]
            imgs = [Image.open(READS / crop).convert("RGB")] if crop else []
            g = grade(eps[model], sh.paper["subjectiveQuestions"][qi], sh.paper["subjectiveRubrics"][qi], ta, tb,
                      imgs, sh.paper.get("subject", ""), 2.0, thinking=thinking, version=version)
            return key, {"marks": g.marks, "latency": g.latency_s, "error": g.error,
                         "decisions": [[d.present, d.partial, d.evidence_found] for d in g.decisions],
                         "transcript_problem": g.transcript_problem}

        with ThreadPoolExecutor(32) as pool:
            for key, res in pool.map(run, todo):
                cache[key] = res
        save_cache("grades.json", cache)
        print(f"{sh.sheet_id}: {len(todo)} gradings, {time.time() - t0:.0f}s", flush=True)


# ── score ────────────────────────────────────────────────────────────────────

def subj_metrics(pairs):
    """pairs = [(pred, teacher)] → exact / within 0.5 / MAE / QWK / bias."""
    p, t = [x for x, _ in pairs], [y for _, y in pairs]
    return {"n": len(pairs), "exact": round(sum(a == b for a, b in pairs) / len(pairs), 3),
            "within_0.5": round(sum(abs(a - b) <= 0.5 for a, b in pairs) / len(pairs), 3),
            "mae": round(sum(abs(a - b) for a, b in pairs) / len(pairs), 3),
            "qwk": round(qwk([round(x * 2) for x in p], [round(x * 2) for x in t]), 3),
            "bias": round(statistics.mean(a - b for a, b in pairs), 3)}


def boot_diff(by_sheet_a: dict, by_sheet_b: dict, n: int = 2000, seed: int = 0):
    """Paired bootstrap over SHEETS of MAE(a) − MAE(b) → (mean, 2.5 %, 97.5 %).
    by_sheet_x = {sheet: [abs errors]}; both must cover the same answers."""
    import random
    rnd, ids = random.Random(seed), sorted(set(by_sheet_a) & set(by_sheet_b))
    diffs = []
    for _ in range(n):
        pick = [rnd.choice(ids) for _ in ids]
        ea = [e for i in pick for e in by_sheet_a[i]]
        eb = [e for i in pick for e in by_sheet_b[i]]
        diffs.append(sum(ea) / len(ea) - sum(eb) / len(eb))
    diffs.sort()
    return statistics.mean(diffs), diffs[int(0.025 * n)], diffs[int(0.975 * n)]


def cmd_score(_args):
    """MCQ reader architectures, grader set-ups, transcript pairs, grader pairs, time per paper."""
    data = sheets()
    grades, pages = load_cache("grades.json"), load_cache("pages.json")
    md = ["# Type-C sweep — Mendeley exam sheets (MCQ + short answers)", "",
          f"Generated {time.strftime('%Y-%m-%d %H:%M')} by `python eval/mendeley_sweep.py score`. "
          f"{len(data)} real scanned exam sheets, gold = the teacher's CSV (chosen MCQ letter; mark per short answer, 0–2).", ""]

    # ── MCQ: every reader source and combination (same logic as arch_sweep) ──
    key = data[0][0].paper["mcqAnswers"]
    srcs = {}
    for sh, rj in data:
        s = {f"crop:qwen>{SHORT[n]}": {qid: {**(q["readings"].get(n) or {}), "latency": (q["readings"].get(n) or {}).get("latency_s", 0)}
                                      for qid, q in rj["questions"].items() if q["kind"] == "mcq"} for n in SHORT}
        s.update({k: v for k, v in pages.get(sh.sheet_id, {}).items() if k.startswith("page>")})
        srcs[sh.sheet_id] = s
    names = sorted({k for s in srcs.values() for k in s})
    rows = []
    combos = [("single", [a], "") for a in names] + [("pair", list(c), "") for c in itertools.combinations(names, 2)]
    combos += [(m, [a, b, c], m.split("+")[1]) for a, b in itertools.combinations(names, 2) for c in names if c not in (a, b)
               for m in ("pair+tiebreak", "pair+majority")]
    for arch, combo, mode in combos:
        n = auto = silent = 0
        secs = 0.0
        for sh, rj in data:
            s = srcs[sh.sheet_id]
            secs += sum(s.get(c, {}).get("_latency", 0) for c in combo if c.startswith("page>"))
            for i in range(1, 21):
                qid, gold = f"Q{i}", sh.gold[f"Q{i}"]["answer"]
                rs = [s.get(c, {}).get(qid) or {} for c in combo]
                acc, lat = decide("mcq", rs, mode)
                secs += lat
                n += 1
                if acc is None:
                    continue
                auto += 1
                ok = norm_mcq(acc.get("value", "")) == norm_mcq(key[qid])
                silent += ok != (norm_mcq(gold) == norm_mcq(key[qid]))
        rows.append({"arch": arch, "readers": " + ".join(combo), "items": n, "silent_errors": silent,
                     "auto_rate": round(auto / n, 3), "ta_items": n - auto, "sec_per_paper": round(secs / len(data), 1)})
    rank = lambda r: (r["silent_errors"], -r["auto_rate"], r["sec_per_paper"])  # noqa: E731
    with open(OUT / "mcq_results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    cols = list(rows[0])
    tbl = lambda rs: ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] + ["| " + " | ".join(str(r[c]) for c in cols) + " |" for r in rs]  # noqa: E731
    md += ["## 1. MCQ part (20 per sheet)", "",
           "Gold is the teacher's CSV, which has at least one known typo (Student_2 Q1) — a few 'silent errors' may be CSV errors.",
           "`crop:qwen>X` = Qwen segments, X reads the crop; `page>X` = X reads whole pages.", "", "### Top 10", ""]
    md += tbl(sorted(rows, key=rank)[:10])
    md += ["", "### Single readers", ""] + tbl(sorted((r for r in rows if r["arch"] == "single"), key=rank))
    for want in ["page>gemma + page>qwen + page>glm", "crop:qwen>qwen + crop:qwen>paddle + crop:qwen>glm"]:
        hit = [r for r in rows if r["readers"] == want and r["arch"] in ("pair+majority", "pair+tiebreak")]
        if hit:
            md += ["", f"Planned / current set-up `{want}`:", ""] + tbl(hit)

    # ── Subjective: grader set-ups on Qwen + GLM transcripts ──
    md += ["", "## 2. Short answers — grader set-ups (transcripts: Qwen + GLM-OCR)", "",
           "exact = same mark as the teacher; within_0.5; MAE in marks (out of 2); QWK (agreement, 1 = perfect); "
           "bias > 0 = more generous than the teacher; s/answer = grader time.", "",
           "| grader | n | exact | within_0.5 | MAE | QWK | bias | grader s/answer | grader s/paper |", "|---|---|---|---|---|---|---|---|---|"]
    per_cfg, errs = {}, {}
    for cfg in CONFIGS:
        pairs, lats, by_sheet = [], [], {}
        for sh, rj in data:
            for qid, _qi, m, _c in answers(sh, rj):
                g = grades.get(f"{sh.sheet_id}|{qid}|{cfg}|qwen+glm")
                if g:
                    pairs.append((g["marks"], m))
                    lats.append(g["latency"])
                    by_sheet.setdefault(sh.sheet_id, []).append(abs(g["marks"] - m))
        if pairs:
            per_cfg[cfg], errs[cfg] = subj_metrics(pairs), by_sheet
            mm = per_cfg[cfg]
            md.append(f"| {cfg} | {mm['n']} | {mm['exact']} | {mm['within_0.5']} | {mm['mae']} | {mm['qwk']} | {mm['bias']} | "
                      f"{statistics.mean(lats):.1f} | {sum(lats) / len(by_sheet):.0f} |")
    # Is the best grader really better? Paired bootstrap over sheets vs every other set-up
    if len(per_cfg) > 1:
        best = min(per_cfg, key=lambda c: per_cfg[c]["mae"])
        md += ["", f"**Best by MAE: `{best}`.** Difference in MAE vs each other set-up (negative = `{best}` is closer "
               "to the teacher), with a 95 % interval from resampling the 50 papers:", "",
               "| vs | MAE difference | 95 % interval | verdict |", "|---|---|---|---|"]
        for cfg in per_cfg:
            if cfg != best:
                m_, lo, hi = boot_diff(errs[best], errs[cfg])
                md.append(f"| {cfg} | {m_:+.3f} | [{lo:+.3f}, {hi:+.3f}] | {'better' if hi < 0 else 'no clear difference'} |")

    # ── Subjective: transcript pairs with the stage-B grader ──
    b_cfgs = sorted({k.split("|")[2] for k in grades if not k.endswith("qwen+glm")})
    for cfg in b_cfgs:
        md += ["", f"## 3. Short answers — transcript pairs (grader `{cfg}`)", "",
               "| transcripts | n | exact | within_0.5 | MAE | QWK | bias | s/paper (2 readers + grader) |", "|---|---|---|---|---|---|---|---|"]
        res = []
        long_name = {v: k for k, v in SHORT.items()}
        for ra, rb in itertools.combinations(SHORT.values(), 2):
            pairs, secs = [], 0.0
            for sh, rj in data:
                for qid, _qi, m, _c in answers(sh, rj):
                    k = f"{sh.sheet_id}|{qid}|{cfg}|{ra}+{rb}"
                    if k in grades:
                        pairs.append((grades[k]["marks"], m))
                        q = rj["questions"][qid]["readings"]
                        secs += grades[k]["latency"] + sum((q.get(long_name[r]) or {}).get("latency_s", 0) for r in (ra, rb))
            if pairs:
                res.append((f"{ra} + {rb}", subj_metrics(pairs), secs / len(data)))
        for name, mm, sp in sorted(res, key=lambda x: x[1]["mae"]):
            md.append(f"| {name} | {mm['n']} | {mm['exact']} | {mm['within_0.5']} | {mm['mae']} | {mm['qwk']} | {mm['bias']} | {sp:.0f} |")

    # ── Two graders: accept when they agree within 0.5, else TA (TA gives the teacher's mark) ──
    md += ["", "## 4. Two graders (grader 1 + grader 2; differ by ≥ 1 mark → TA)", "",
           "| grader 1 | grader 2 | auto | TA | exact (auto) | MAE (auto) | big errors (auto, ≥ 1 mark off) | graders s/paper |", "|---|---|---|---|---|---|---|---|"]
    gp = []
    for c1, c2 in itertools.permutations(CONFIGS, 2):
        n = auto = big = 0
        pairs, secs = [], 0.0
        for sh, rj in data:
            for qid, _qi, m, _c in answers(sh, rj):
                g1, g2 = grades.get(f"{sh.sheet_id}|{qid}|{c1}|qwen+glm"), grades.get(f"{sh.sheet_id}|{qid}|{c2}|qwen+glm")
                if not g1 or not g2:
                    continue
                n += 1
                secs += g1["latency"] + g2["latency"]
                if abs(g1["marks"] - g2["marks"]) >= 1:
                    continue
                auto += 1
                pairs.append((g1["marks"], m))
                big += abs(g1["marks"] - m) >= 1
        if pairs:
            mm = subj_metrics(pairs)
            gp.append((big, -auto, f"| {c1} | {c2} | {auto / n:.0%} | {n - auto} | {mm['exact']} | {mm['mae']} | {big} | {secs / len(data):.0f} |"))
    md += [r for *_, r in sorted(gp)[:12]]

    # ── Time per paper ──
    md += ["", "## 5. Time per paper (model seconds, summed over calls)", "",
           "Sum of each call's latency for one sheet (35 answers, ~4 pages). The server runs many calls in parallel, "
           "so wall-clock time per sheet is lower; `wall` is what one sheet took in these runs with every model at once.", ""]
    seg = [rj.get("segment_s", 0) for _, rj in data]
    tr = {n: [sum((q["readings"].get(n) or {}).get("latency_s", 0) for q in rj["questions"].values()) for _, rj in data] for n in SHORT}
    pg = {k: [pages.get(sh.sheet_id, {}).get(k, {}).get("_latency", 0) for sh, _ in data] for k in (f"page>{s}" for s in SHORT.values())}
    gr = {cfg: [sum(grades.get(f"{sh.sheet_id}|{qid}|{cfg}|qwen+glm", {}).get("latency", 0) for qid, *_ in answers(sh, rj)) for sh, rj in data] for cfg in CONFIGS}
    avg = lambda xs: f"{statistics.mean(xs):.0f}" if xs else "—"  # noqa: E731
    md += ["| step | avg s / paper |", "|---|---|", f"| segmentation (Qwen) | {avg(seg)} |"]
    md += [f"| read all 35 crops: {s} | {avg(tr[n])} |" for n, s in SHORT.items()]
    md += [f"| MCQ whole pages: {k} | {avg(v)} |" for k, v in pg.items()]
    md += [f"| grade short answers: {c} | {avg(v)} |" for c, v in gr.items()]
    walls = [rj.get("wall_s") for _, rj in data if rj.get("wall_s")]
    md += ["", f"Wall-clock in these runs: reading (segment + 5 readers in parallel) {avg(walls)} s / paper; "
           f"whole-page MCQ (5 models in parallel) {avg([pages.get(sh.sheet_id, {}).get('_wall', 0) for sh, _ in data])} s / paper."]
    (OUT / "README.md").write_text("\n".join(md) + "\n")
    print(f"wrote {OUT / 'README.md'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["pages", "grade", "score"])
    ap.add_argument("--stage", default="A", choices=["A", "B"])
    ap.add_argument("--config", default="qwen-v2")
    ap.add_argument("--sheets", default="", help="only these sheet ids (comma-separated)")
    args = ap.parse_args()
    {"pages": cmd_pages, "grade": cmd_grade, "score": cmd_score}[args.cmd](args)


if __name__ == "__main__":
    main()
