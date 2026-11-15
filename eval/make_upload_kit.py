#!/usr/bin/env python3
"""make_upload_kit.py — build uploads/, the files to upload when testing every flow in the browser.

    python eval/make_upload_kit.py            # (re)creates <repo>/uploads

uploads/Pattern1  MCQ only            (OMR sheets and handwritten sheets)
uploads/Pattern2  MCQ + numerical     (papers 2A, 2B, 2C)
uploads/Pattern3  MCQ + subjective    (Data Science exam, Mendeley sf3kvjwknt, CC BY 4.0)
Each pattern has Teacher/ (what the teacher uploads or types while creating the paper) and Student/
(answer sheets, one folder per student login, plus the expected marks to compare with).
Everything comes from the labelled sets used in the evaluations (eval/data, eval/test_papers).
"""
from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "eval"))

import dataset  # noqa: E402

KIT = ROOT / "uploads"
TP = ROOT / "eval" / "test_papers"
DATA = ROOT / "eval" / "data"
MENDELEY_RAW = Path("/scratch/m25csa019/evalify/datasets/mendeley_sf3kvjwknt")
# Data Science sheets spread over the marks range (teacher totals 14 … 43); Student_13 has 6 pages
DS_SHEETS = ["Student_19", "Student_2", "Student_9", "Student_1", "Student_29", "Student_13"]

PHYSICS = ("physics.teacher@evalify.local", "Physics", "PH2025")      # demo.env: basic-science papers
DS = ("ds.teacher@evalify.local", "Data Science", "DS2025")


# ── small helpers ────────────────────────────────────────────────────────────

def text_pdf(path: Path, title: str, lines: list, size: float = 10, landscape: bool = False) -> None:
    """Plain text PDF (one entry per line, long lines wrapped). Landscape keeps long lines unwrapped."""
    w, h = (842, 595) if landscape else (595, 842)
    doc, page, y = fitz.open(), None, 0

    def new_page():
        # Title on the first page only: a repeated title would be read as part of the previous question
        p = doc.new_page(width=w, height=h)
        if len(doc) == 1:
            p.insert_text((40, 50), title, fontsize=14, fontname="hebo")
        return p, 80 if len(doc) == 1 else 50
    page, y = new_page()
    for raw in lines:
        for line in _wrap(raw.replace("—", "-").replace("–", "-").replace("’", "'"), w - 80, size) or [""]:
            if y > h - 40:
                page, y = new_page()
            page.insert_text((40, y), line, fontsize=size, fontname="helv")
            y += size * 1.45
    doc.save(path)


def _wrap(s: str, width: float, size: float) -> list:
    """Word wrap to the page width."""
    out, line = [], ""
    for word in s.split():
        if line and fitz.get_text_length(line + " " + word, fontsize=size) > width:
            out.append(line)
            line = word
        else:
            line = (line + " " + word).strip()
    return out + ([line] if line else [])


def expected_marks(sheet) -> dict:
    """Marks a perfect reader would give, from the hand labels (what the student actually wrote)."""
    from app.pipeline.scoring import grade_mcq, grade_numerical
    p = sheet.paper
    answers = {q: g["answer"] for q, g in sheet.gold.items() if g.get("answer") not in (None, "", "?")}
    unclear = [q for q, g in sheet.gold.items() if g.get("answer") == "?"]
    mcq, _, mrows = grade_mcq(answers, p, int(p.get("mcqCount", 0)))
    num, nrows = grade_numerical(answers, p, int(p.get("numericalCount", 0))) if "numerical" in p["type"] else (0, [])
    return {"total": mcq + num, "max": float(p["totalMarks"]), "rows": mrows + nrows, "unclear": unclear}


def key_text(answer) -> str:
    """'A,C' → 'A, C' for a printed answer key."""
    return ", ".join(answer.split(","))


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n")


# ── Pattern 1: MCQ only ──────────────────────────────────────────────────────

def pattern1() -> None:
    base = KIT / "Pattern1"
    omr_paper = json.loads((DATA / "own_omr/papers/omr_basic_science.json").read_text())
    hw_paper = json.loads((DATA / "own_mcq/papers/mcq_basic_science.json").read_text())

    # Teacher: OMR paper (20 Q) — question paper, answer key, the three blank OMR layouts
    t = base / "Teacher" / "OMR"
    t.mkdir(parents=True)
    shutil.copy(TP / "omr/omr_question_paper.pdf", t / "question_paper.pdf")
    text_pdf(t / "answer_key.pdf", "Answer key - Basic Science OMR Test (20 questions)",
             [f"{i}. {key_text(omr_paper['mcqAnswers'][f'Q{i}'])}" for i in range(1, 21)])
    for n in (1, 2, 3):
        shutil.copy(TP / f"omr/omr_layout_{n}.png", t / f"blank_omr_sheet_layout{n}.png")

    # Teacher: handwritten MCQ paper (10 Q)
    t = base / "Teacher" / "Handwritten"
    t.mkdir(parents=True)
    shutil.copy(TP / "mcq/mcq_question_paper.pdf", t / "question_paper.pdf")
    text_pdf(t / "answer_key.pdf", "Answer key - Basic Science MCQ Test (10 questions)",
             [f"{i}. {key_text(hw_paper['mcqAnswers'][f'Q{i}'])}" for i in range(1, 11)])

    # Students: OMR sheets per layout, handwritten sheets
    omr_sheets = list(dataset.load(str(DATA / "own_omr")))
    for n in (1, 2, 3):
        sheets = [s for s in omr_sheets if s.sheet_id.startswith(f"omr_L{n}_")]
        student_folder(base / "Student" / "OMR" / f"Layout{n}", sheets, PHYSICS, "omr",
                       f"Basic Science OMR Test - layout {n}")
    student_folder(base / "Student" / "Handwritten", list(dataset.load(str(DATA / "own_mcq"))), PHYSICS,
                   "handwritten", "Basic Science MCQ Test (10)")

    write(base / "Teacher" / "README.md", f"""
# Pattern 1 (MCQ only), teacher side

Log in as **{PHYSICS[0]}** (password in `demo.env`). Subject: {PHYSICS[1]}.
Create **one paper per folder below**. For OMR, create one paper per layout you want to test
(the blank sheet of that layout is what the students' sheets are aligned to).

## A. OMR paper: `OMR/`

| Wizard step | What to do |
|---|---|
| 1 Paper type | **MCQ only** |
| 2 Details | Name e.g. `Basic Science OMR - layout 1`; MCQ questions **20**, **1 mark** each; upload `question_paper.pdf` |
| 3 Answer key | Either "Upload PDF and extract": upload `answer_key.pdf`, click **Extract Answers from PDF** (expect 20/20, including multi-answer keys like `A, C`), or enter them by hand from the table below |
| 3 Blank OMR sheet | Upload `blank_omr_sheet_layout1.png` (or 2 / 3). Check the labelled preview, then tick **Every bubble is labelled with the right question** |
| 4 Configuration | Negative marking off |
| 5 Review | Create |

Then the students in `../Student/OMR/Layout1/` (same layout number) upload their sheets and choose **OMR sheet**.

Key (20 questions; several have more than one correct option, a student must fill exactly that set):
{key_table(omr_paper['mcqAnswers'])}

## B. Handwritten MCQ paper: `Handwritten/`

| Wizard step | What to do |
|---|---|
| 1 Paper type | **MCQ only** |
| 2 Details | Name e.g. `Basic Science MCQ (handwritten)`; MCQ questions **10**, **1 mark** each; upload `question_paper.pdf` |
| 3 Answer key | Upload `answer_key.pdf` and extract, or type from the table; do **not** upload a blank OMR sheet |
| 4, 5 | Negative marking off; Create |

Students in `../Student/Handwritten/` upload their photo and choose **Handwritten**.

Key:
{key_table(hw_paper['mcqAnswers'])}
""")


def key_table(answers: dict) -> str:
    """Markdown table of an MCQ key, 10 per row."""
    qs = sorted(answers, key=lambda q: int(q[1:]))
    rows = ["| " + " | ".join(qs[i:i + 10]) + " |\n|" + "---|" * len(qs[i:i + 10]) + "\n| "
            + " | ".join(key_text(answers[q]) for q in qs[i:i + 10]) + " |" for i in range(0, len(qs), 10)]
    return "\n\n".join(rows)


def student_folder(folder: Path, sheets: list, who: tuple, sheet_type: str, paper_name: str) -> None:
    """One sub-folder per student login with the sheet's page(s), plus expected_results.md."""
    folder.mkdir(parents=True, exist_ok=True)
    lines = [f"# Expected results: {paper_name}", "",
             f"Each sub-folder is one student. Log in with that roll number (password in `demo.env`), open the paper, "
             f"choose **{'OMR sheet' if sheet_type == 'omr' else 'Handwritten'}** and upload the page(s) in that folder.",
             "", "Expected marks come from our hand labels of what each student actually wrote (not from the AI).",
             "", "| Student login | Sheet | Expected marks | What is on the sheet |", "|---|---|---|---|"]
    for i, s in enumerate(sheets, 1):
        roll = f"{who[2]}{i:03d}"
        d = folder / roll
        d.mkdir()
        for k, p in enumerate(s.pages, 1):
            shutil.copy(p, d / f"{s.sheet_id}_page{k}{Path(p).suffix.lower()}")
        e = expected_marks(s)
        wrong = [r["question"] for r in e["rows"] if r["marks_earned"] < r["marks_available"]]
        note = []
        if wrong:
            note.append("not full marks: " + ", ".join(wrong))
        if e["unclear"]:
            note.append("unclear on purpose: " + ", ".join(e["unclear"]) + " (should go to a TA)")
        lines.append(f"| {roll} | {s.sheet_id} | {e['total']:g} / {e['max']:g} | {'; '.join(note) or 'all correct'} |")
    write(folder / "expected_results.md", "\n".join(lines))


# ── Pattern 2: MCQ + numerical ───────────────────────────────────────────────

def pattern2() -> None:
    base = KIT / "Pattern2"
    sheets = list(dataset.load(str(DATA / "own_mcqnum")))
    steps = []
    for name in ("2A", "2B", "2C"):
        paper = json.loads((DATA / f"own_mcqnum/papers/paper_{name}.json").read_text())
        t = base / "Teacher" / f"Paper_{name}"
        t.mkdir(parents=True)
        shutil.copy(TP / f"mcq_num/paper_{name}_question_paper.pdf", t / "question_paper.pdf")
        nums = paper["numericalAnswers"]
        text_pdf(t / "answer_key.pdf", f"Answer key - {paper['name']}",
                 [f"{i}. {key_text(paper['mcqAnswers'][f'Q{i}'])}" for i in (1, 2)]
                 + [f"{2 + i}. {nums[f'N{i}']['answer']} {nums[f'N{i}']['unit'] or ''}".strip() for i in (1, 2, 3)])
        student_folder(base / "Student" / f"Paper_{name}", [s for s in sheets if s.sheet_id.startswith(name)],
                       PHYSICS, "handwritten", paper["name"])
        steps.append(f"""
## Paper {name}: `Paper_{name}/` ({paper['name']})

| Wizard step | What to do |
|---|---|
| 1 Paper type | **MCQ + Numerical** |
| 2 Details | Name `{paper['name']}`; MCQ **2** x **1 mark**; Numerical **3** x **2 marks** (total 8); upload `question_paper.pdf` |
| 3 Answer key | MCQ: Q1 = **{key_text(paper['mcqAnswers']['Q1'])}**, Q2 = **{key_text(paper['mcqAnswers']['Q2'])}** (or extract from `answer_key.pdf`). Numerical, type the number only: N1 = **{nums['N1']['answer']}**, N2 = **{nums['N2']['answer']}**, N3 = **{nums['N3']['answer']}** |
| 4, 5 | Negative marking off; Create |

On the sheet the numerical answers are questions 3, 4, 5 (units in the key: {', '.join(str(nums[f'N{i}']['unit'] or 'none') for i in (1, 2, 3))}).
Students: `../Student/Paper_{name}/`, choose **Handwritten**.""")
    write(base / "Teacher" / "README.md", f"""
# Pattern 2 (MCQ + numerical), teacher side

Log in as **{PHYSICS[0]}** (password in `demo.env`). Create one paper per folder.
Marking rule: the number counts within +-0.001; the written unit is ignored (no conversion, so `2.5 km`
for a key of 2500 m gets 0).
{''.join(steps)}
""")


# ── Pattern 3: MCQ + subjective (Data Science exam) ──────────────────────────

def pattern3() -> None:
    base = KIT / "Pattern3"
    paper = json.loads((DATA / "mendeley/papers/ds_exam.json").read_text())
    t = base / "Teacher"
    t.mkdir(parents=True)

    # Question paper as the students received it (Part I MCQ 1-20, Part II short answers 21-35)
    q_lines = (MENDELEY_RAW / "Question.txt").read_text().splitlines()
    text_pdf(t / "question_paper.pdf", "Data Science Examination", q_lines[1:], size=9.5)
    text_pdf(t / "answer_key_mcq.pdf", "Answer key - Part I (MCQ)",
             [f"{i}. {key_text(paper['mcqAnswers'][f'Q{i}'])}" for i in range(1, 21)])

    # Rubric PDFs in the format "Extract Rubric from PDFs" reads: sections S1..S15
    qs, rubrics = paper["subjectiveQuestions"], paper["subjectiveRubrics"]
    detailed, grading = [], []
    for i, (q, r) in enumerate(zip(qs, rubrics), 1):
        detailed += [f"S{i}. {q}", r["model_answer"], ""]
        grading += [f"S{i}."] + [f"- {c} ({r['marks_per_concept']:g} mark)" for c in r["key_concepts"]] + [""]
    text_pdf(t / "detailed_answer.pdf", "Detailed answers - Part II", detailed, size=8.5, landscape=True)
    text_pdf(t / "grade_rubric.pdf", "Grade rubric - Part II (2 marks each)", grading, size=9, landscape=True)

    # Optional reference material for the answer-key assistant (the dataset's own answer key, as text)
    ref = [f"Question {21 + i}: {q}\nAnswer: {r['model_answer']}\n" for i, (q, r) in enumerate(zip(qs, rubrics))]
    write(t / "reference_notes.txt", "Data Science - reference answers (from the dataset's answer key)\n\n" + "\n".join(ref))

    # Students: 6 sheets across the marks range, with the real teacher's marks
    by_id = {s.sheet_id: s for s in dataset.load(str(DATA / "mendeley"))}
    marks = {r["sheet_id"]: r["teacher_totals"] for r in
             (json.loads(x) for x in (DATA / "mendeley/manifest.jsonl").read_text().splitlines() if x.strip())}
    s_dir = base / "Student"
    lines = ["# Expected results: Data Science exam", "",
             "Each sub-folder is one student. Log in with that roll number (password in `demo.env`), open the paper,",
             "choose **Handwritten** and upload **all pages** of the folder in order (page1, page2, ...).", "",
             "Expected marks are the **real teacher's marks** from the dataset. Written answers are judged, so expect",
             "the AI to be close but not identical (our measured average difference is a few marks per sheet).", "",
             "**MCQ by the key** is what the answer key gives for the answers we labelled on the sheet: the app should",
             "match it. The dataset's teacher sometimes marked MCQs differently from the key (found in run 7).",
             "Without calibration the AI marks written answers about 0.5 per answer stricter than this teacher.", "",
             "| Student login | Sheet | Pages | MCQ by the key / 20 | Teacher: MCQ / 20 | Teacher: written / 30 | Teacher: total / 50 |",
             "|---|---|---|---|---|---|---|"]
    for i, sid in enumerate(DS_SHEETS, 1):
        s, roll = by_id[sid], f"{DS[2]}{i:03d}"
        d = s_dir / roll
        d.mkdir(parents=True)
        for k, p in enumerate(s.pages, 1):           # scans as JPEG (what phones upload; ~10x smaller)
            Image.open(p).convert("RGB").save(d / f"{sid}_page{k}.jpg", quality=92)
        m = marks[sid]
        from app.pipeline.scoring import grade_mcq      # MCQ marks the key gives for the labelled answers
        labelled = {q: g["answer"] for q, g in s.gold.items() if q.startswith("Q") and int(q[1:]) <= 20 and g.get("answer")}
        by_key = grade_mcq(labelled, paper, 20)[0]
        lines.append(f"| {roll} | {sid} | {len(s.pages)} | {by_key:g} | {m['mcq']:g} | {m['short']:g} | {m['total']:g} |")
    write(s_dir / "expected_results.md", "\n".join(lines))

    write(t / "README.md", f"""
# Pattern 3 (MCQ + subjective), teacher side

Log in as **{DS[0]}** (password in `demo.env`). Subject: {DS[1]}.
Data: "A Dataset of Digitized Student Examination Papers ..." (Mendeley Data sf3kvjwknt, CC BY 4.0).

| Wizard step | What to do |
|---|---|
| 1 Paper type | **MCQ + Numerical + Subjective** |
| 2 Details | Name e.g. `Data Science exam`; MCQ **20** x **1 mark**; Numerical **0**; Subjective **15** x **2 marks** (total 50); upload `question_paper.pdf`. Written-answer numbering: choose **Q21, Q22, ... (numbers continue)**, because the students wrote 21-35 |
| 3 Answer key | "Upload PDF and extract" with `answer_key_mcq.pdf` (20/20), or type from the table below |
| 4 Rubric | Upload `detailed_answer.pdf` (Detailed Answer) and `grade_rubric.pdf` (Grade Rubric), click **Extract Rubric from PDFs**: 15 questions, 2 points each at 1 mark |
| 4 (optional) | Try the answer-key assistant: upload `reference_notes.txt` as reference, type a question, **Draft answer key** |
| 5 Review | Check "Written answers numbered: Q21 onwards"; Create |

After the students upload: TAs (`ta.ds1@evalify.local`) clear flagged answers, then on the results page
click **Release results**. Until then the students see "Your answer sheet is being evaluated".

MCQ key:
{key_table(paper['mcqAnswers'])}
""")


def overview() -> None:
    write(KIT / "README.md", """
# Upload kit for testing every flow

Built by `python eval/make_upload_kit.py` from the labelled sets used in our evaluations.
Download this folder to the computer you test from (VS Code: right-click > Download).

| Pattern | Paper | Teacher login | Students |
|---|---|---|---|
| `Pattern1/` | MCQ only: OMR (20 Q, 3 sheet layouts) and handwritten (10 Q) | physics.teacher@evalify.local | PH2025001 ... |
| `Pattern2/` | MCQ + numerical: papers 2A, 2B, 2C (2 MCQ + 3 numerical) | physics.teacher@evalify.local | PH2025001 ... PH2025005 |
| `Pattern3/` | MCQ + subjective: Data Science exam (20 MCQ + 15 written) | ds.teacher@evalify.local | DS2025001 ... DS2025006 |

Passwords: `demo.env` (demo accounts only).

For each pattern:
1. **Teacher**: follow `PatternN/Teacher/README.md` to create the paper (files to upload are next to it).
2. **Students**: each folder under `PatternN/Student/...` is one student login; upload the page(s) in it.
   `expected_results.md` next to them says what marks to expect.
3. **TA** (flagged answers): `ta.physics@evalify.local` for Patterns 1-2, `ta.ds1@evalify.local` for Pattern 3.
4. **Teacher**: results page > check > **Release results**; students then see marks and can ask for one re-evaluation.

To repeat a test with clean results, create the paper again and upload the sheets to the new paper.
""")


def main() -> None:
    if KIT.exists():
        shutil.rmtree(KIT)
    KIT.mkdir()
    pattern1()
    pattern2()
    pattern3()
    overview()
    n = sum(1 for _ in KIT.rglob("*") if _.is_file())
    size = sum(f.stat().st_size for f in KIT.rglob("*") if f.is_file()) / 1e6
    print(f"{KIT}: {n} files, {size:.1f} MB")


if __name__ == "__main__":
    main()
