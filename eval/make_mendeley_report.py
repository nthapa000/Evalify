#!/usr/bin/env python3
"""make_mendeley_report.py — per-sheet markdown reports + summary for the reader comparison.

    python eval/make_mendeley_report.py

Inputs (eval/reports/mendeley/):
  <sheet>.json            readings from mendeley_readers.py
  review/<sheet>.json     Claude's visual check (optional): {"transcripts": {S1: text},
                          "notes": {qid: text}, "mcq_seen": {Q1: letter}}
Outputs: <sheet>.md per sheet and README.md (summary, method, caveats).
"""
from __future__ import annotations

import itertools
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.pipeline.textdist import cer, wer  # noqa: E402

REP = ROOT / "eval" / "reports" / "mendeley"
READERS = {"qwen38-27b-fp8": "Qwen3.8", "chandra-ocr-2": "Chandra", "paddleocr-vl-1.6": "PaddleOCR", "glm-ocr": "GLM-OCR"}


def norm(text: str) -> str:
    """For CER/WER: drop struck-out text and a leading question label, lower-case, keep words/digits."""
    t = re.sub(r"~~.*?~~", " ", text or "", flags=re.S)
    t = re.sub(r"^\s*(?:Q|§|\$)?\s*\d{1,2}\s*[.):]", " ", t.strip())
    t = re.sub(r"[^a-z0-9 ]+", " ", t.lower())
    return re.sub(r"\s+", " ", t).strip()


def val(r) -> str:
    """Reading value or a marker for 'no answer'."""
    return "∅" if not r or not r.get("value") else r["value"]


def cell(s: str, n: int = 400) -> str:
    """Markdown-table-safe text."""
    s = (s or "").replace("|", "\\|").replace("\n", " ⏎ ")
    return s if len(s) <= n else s[:n] + " …"


def main():
    sheets = sorted((p for p in REP.glob("Student_*.json")), key=lambda p: int(p.stem.split("_")[1]))
    mcq_stats = {r: {"right": 0, "wrong": 0, "empty": 0} for r in READERS}
    mcq_wrong_sets = {r: set() for r in READERS}               # items each reader got wrong/empty
    subj_cer = {r: [] for r in READERS}
    subj_wer = {r: [] for r in READERS}
    index_rows = []

    for f in sheets:
        d = json.loads(f.read_text())
        sid = d["sheet"]
        review = json.loads((REP / "review" / f"{sid}.json").read_text()) if (REP / "review" / f"{sid}.json").exists() else {}
        transcripts, notes = review.get("transcripts", {}), review.get("notes", {})
        lines = [f"# {sid} — reader comparison", "",
                 f"Pages read: {', '.join(Path(p).name for p in d['pages'] if Path(p).name not in d.get('skipped_blank_pages', []))}  ",
                 f"Skipped as blank / show-through backs: {', '.join(d.get('skipped_blank_pages', [])) or 'none'}  ",
                 f"Answers located by the segmenter: {d['located']}  ",
                 f"Visual check by Claude: {'yes — transcripts for short answers below' if transcripts else 'MCQ only / disagreements' if review else 'not yet'}",
                 "", "Page images: `eval/data/mendeley/images/` · crops: `eval/reports/mendeley/crops/` (local, not in git).", ""]
        if notes.get("_pages"):                                   # sheet-level observations
            lines += [f"> **Visual check (sheet):** {notes['_pages']}", ""]
        if review.get("about"):
            lines += [f"> {review['about']}", ""]

        # ── MCQ table ──
        lines += ["## MCQ (gold = letter in the teacher's CSV)", "",
                  "| Q | crop | gold | " + " | ".join(READERS.values()) + " | note |",
                  "|---|---|---|" + "---|" * len(READERS) + "---|"]
        sheet_mcq = {r: 0 for r in READERS}
        for qid, q in d["questions"].items():
            if q["kind"] != "mcq":
                continue
            gold = (q["gold"].get("answer") or "").strip()
            marks = []
            for r in READERS:
                v = (q["readings"].get(r) or {}).get("value", "")
                if not v:
                    mcq_stats[r]["empty"] += 1
                    mcq_wrong_sets[r].add((sid, qid))
                    marks.append("∅")
                elif v == gold:
                    mcq_stats[r]["right"] += 1
                    sheet_mcq[r] += 1
                    marks.append(f"{v} ✅")
                else:
                    mcq_stats[r]["wrong"] += 1
                    mcq_wrong_sets[r].add((sid, qid))
                    marks.append(f"{v} ❌")
            crop = f"![{qid}](crops/{sid}/{qid}.jpg)" if q.get("crop") else "not located"
            lines.append(f"| {qid} | {crop} | **{gold}** | " + " | ".join(marks) + f" | {cell(notes.get(qid, ''))} |")
        n_mcq = sum(1 for q in d["questions"].values() if q["kind"] == "mcq")
        lines += ["", "Correct per reader: " + ", ".join(f"{READERS[r]} {sheet_mcq[r]}/{n_mcq}" for r in READERS), ""]

        # ── Short answers ──
        lines += ["## Short answers (Q21–Q35)", "",
                  "Teacher mark is from the CSV (out of 2). CER/WER are against Claude's transcript where one "
                  "exists (lower = better; struck-out text, punctuation, case and the question label are ignored).", ""]
        for qid, q in d["questions"].items():
            if q["kind"] != "subjective":
                continue
            ref = transcripts.get(qid)
            lines += [f"### {q['label']} ({qid}) — teacher mark: {q['gold'].get('marks')}", ""]
            lines.append(f"![{qid}](crops/{sid}/{qid}.jpg)" if q.get("crop") else "_answer not located_")
            lines.append(f"<sub>located on: {', '.join(b['page'] for b in q['boxes']) or '—'}</sub>")
            lines += ["", "| reader | text | CER | WER |", "|---|---|---|---|"]
            if ref is not None:
                lines.append(f"| **Claude (visual check)** | {cell(ref, 2000)} | — | — |")
            for r, name in READERS.items():
                v = (q["readings"].get(r) or {}).get("value", "")
                c = w = ""
                if ref is not None and q.get("crop"):
                    c, w = cer(norm(ref), norm(v)), wer(norm(ref), norm(v))
                    subj_cer[r].append(c)
                    subj_wer[r].append(w)
                    c, w = f"{c:.2f}", f"{w:.2f}"
                lines.append(f"| {name} | {cell(v or '∅', 2000)} | {c} | {w} |")
            if notes.get(qid):
                lines += ["", f"**Visual check:** {notes[qid]}"]
            lines.append("")
        (REP / f"{sid}.md").write_text("\n".join(lines))
        index_rows.append(f"| [{sid}]({sid}.md) | {d['located']} | {', '.join(d.get('skipped_blank_pages', [])) or '—'} | "
                          + " | ".join(f"{sheet_mcq[r]}/{n_mcq}" for r in READERS)
                          + f" | {'✔' if transcripts else ''} |")

    # ── Summary README ──
    tot = {r: sum(s.values()) for r, s in mcq_stats.items()}
    pairs = []
    for a, b in itertools.combinations(READERS, 2):
        both = len(mcq_wrong_sets[a] & mcq_wrong_sets[b])
        either = len(mcq_wrong_sets[a] | mcq_wrong_sets[b])
        pairs.append((f"{READERS[a]} + {READERS[b]}", both, either))
    mean = lambda xs: f"{sum(xs) / len(xs):.3f}" if xs else "—"  # noqa: E731
    readme = ["# Reader comparison on real handwriting — Mendeley exam set", "",
              "Dataset: *A Dataset of Digitized Student Examination Papers…*, Dinesh K P, Mendeley Data "
              "sf3kvjwknt v1, **CC BY 4.0** (https://data.mendeley.com/datasets/sf3kvjwknt/1). "
              "12 sheets (Student_1 … Student_12), Data Science exam: 20 MCQ + 15 short answers.", "",
              "## How this was produced", "",
              "1. `eval/build_mendeley.py` rendered each PDF page and took gold from "
              "`Teacher_manual_marks_Anonymized.csv` (MCQ letter chosen; teacher mark per short answer).",
              "2. `eval/mendeley_readers.py`: quality gate (blank / show-through backs skipped) → Qwen3.8 "
              "segmenter finds each answer by its written number → one crop per answer → four readers on every crop.",
              "3. Claude visually checked the crops: MCQ disagreements, and full transcripts of the short "
              "answers on the sheets marked ✔ below (`review/<sheet>.json`). **These transcripts are an AI's reading — "
              "please verify them against the crops.**",
              "4. `eval/make_mendeley_report.py` built these pages.", "",
              "## MCQ reading (240 answers, gold = teacher CSV)", "",
              "| reader | correct | wrong letter | no answer | accuracy |", "|---|---|---|---|---|"]
    for r, name in READERS.items():
        s = mcq_stats[r]
        readme.append(f"| {name} | {s['right']} | {s['wrong']} | {s['empty']} | {s['right'] / max(1, tot[r]):.1%} |")
    readme += ["", "**Shared mistakes per reader pair** (items both got wrong or empty, out of items either got wrong/empty). "
               "A good reader pair has few shared mistakes.", "",
               "| pair | both wrong | either wrong |", "|---|---|---|"]
    readme += [f"| {p} | {b} | {e} |" for p, b, e in sorted(pairs, key=lambda x: (x[1], x[2]))]
    readme += ["", "## Short-answer reading (vs Claude's transcripts)", "",
               "| reader | answers | mean CER | mean WER |", "|---|---|---|---|"]
    readme += [f"| {n} | {len(subj_cer[r])} | {mean(subj_cer[r])} | {mean(subj_wer[r])} |" for r, n in READERS.items()]
    readme += ["", "## Sheets", "", "| sheet | answers located | blank pages skipped | "
               + " | ".join(f"{n} MCQ" for n in READERS.values()) + " | transcribed |",
               "|---|---|---|" + "---|" * len(READERS) + "---|"] + index_rows
    readme += ["", "## Caveats", "",
               "- Gold MCQ letters come from the teacher's CSV; a CSV typo would count as a reader error.",
               "- Short-answer transcripts are Claude's reading of the crops, not a human's.",
               "- Teacher CSV oddities: blank / `NC` cells (not attempted or not corrected); Student_11 Q34 = 4.0 "
               "although each short answer is out of 2.",
               "- Rubrics for grading (Q21–Q35) were drafted by Claude from `answerkey.txt` — grading is a separate step."]
    (REP / "README.md").write_text("\n".join(readme) + "\n")
    print(f"wrote {len(sheets)} sheet reports + README.md → {REP}")


if __name__ == "__main__":
    main()
