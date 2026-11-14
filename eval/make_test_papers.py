#!/usr/bin/env python3
"""make_test_papers.py — printable test papers for Evalify's own dataset (basic science, A4).

    python eval/make_test_papers.py            → eval/test_papers/

  omr/        3 OMR bubble-sheet layouts (20 Q, A–D) as PDF + 200-dpi PNG, and the OMR question paper
  mcq/        handwritten MCQ paper (10 Q, single + multiple correct)
  mcq_num/    3 papers of 2 MCQ + 3 numerical (answers only)
  keys/       answer keys (one readable PDF) + Evalify paper JSON per paper
  labels/     CSV templates to record what each student actually wrote
Students write ONLY the final answer (letters / value); rough work is on a separate sheet.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import fitz  # PyMuPDF

OUT = Path(__file__).resolve().parent / "test_papers"
W, H = 595, 842                                   # A4 in points
BLACK, BLUE, ORANGE = (0, 0, 0), (0.1, 0.2, 0.7), (0.9, 0.45, 0.1)

# ── Question content ────────────────────────────────────────────────────────

OMR_QUESTIONS = [  # (question, options, answer) — single answer each
    ("Boiling point of water at sea level is", ["50 °C", "100 °C", "150 °C", "0 °C"], "B"),
    ("Plants take in which gas for photosynthesis?", ["Oxygen", "Nitrogen", "Carbon dioxide", "Hydrogen"], "C"),
    ("The SI unit of force is", ["Joule", "Watt", "Newton", "Pascal"], "C"),
    ("Which planet is called the Red Planet?", ["Venus", "Mars", "Jupiter", "Saturn"], "B"),
    ("The chemical symbol for sodium is", ["S", "So", "Na", "Sd"], "C"),
    ("The largest organ of the human body is the", ["Liver", "Heart", "Skin", "Brain"], "C"),
    ("Speed of light in vacuum is about", ["3 x 10^8 m/s", "3 x 10^5 m/s", "340 m/s", "3 x 10^3 m/s"], "A"),
    ("The pH of pure water is", ["0", "7", "10", "14"], "B"),
    ("Which of these conducts electricity?", ["Rubber", "Glass", "Copper", "Wood"], "C"),
    ("The powerhouse of the cell is the", ["Nucleus", "Ribosome", "Mitochondria", "Golgi body"], "C"),
    ("Freezing point of water on the Kelvin scale is about", ["0 K", "100 K", "273 K", "373 K"], "C"),
    ("Number of bones in an adult human body", ["106", "206", "306", "156"], "B"),
    ("Most abundant gas in Earth's atmosphere", ["Oxygen", "Nitrogen", "Argon", "Carbon dioxide"], "B"),
    ("Which is a vector quantity?", ["Mass", "Time", "Velocity", "Temperature"], "C"),
    ("The chemical formula of water is", ["H2O", "CO2", "O2", "H2O2"], "A"),
    ("Sound cannot travel through", ["Water", "Steel", "Air", "Vacuum"], "D"),
    ("Which blood cells fight infection?", ["Red blood cells", "White blood cells", "Platelets", "Plasma"], "B"),
    ("The SI unit of electric current is", ["Volt", "Ohm", "Ampere", "Watt"], "C"),
    ("The star closest to Earth is", ["Sirius", "the Sun", "Polaris", "Alpha Centauri"], "B"),
    ("The acid found in the human stomach is", ["Sulphuric acid", "Nitric acid", "Hydrochloric acid", "Acetic acid"], "C"),
]

MCQ_QUESTIONS = [  # (question, options, answer, multiple?)
    ("Which of these is a mammal?", ["Shark", "Dolphin", "Penguin", "Frog"], "B", False),
    ("Which are renewable energy sources?", ["Solar", "Coal", "Wind", "Natural gas"], "A,C", True),
    ("Which organ pumps blood around the body?", ["Lungs", "Heart", "Kidney", "Liver"], "B", False),
    ("Which are states of matter?", ["Solid", "Energy", "Liquid", "Gas"], "A,C,D", True),
    ("The Earth goes once around the Sun in about", ["1 day", "1 month", "365 days", "24 hours"], "C", False),
    ("Which are noble gases?", ["Helium", "Oxygen", "Neon", "Nitrogen"], "A,C", True),
    ("Which vitamin does skin make in sunlight?", ["Vitamin A", "Vitamin B12", "Vitamin C", "Vitamin D"], "D", False),
    ("Which are parts of a flower?", ["Petal", "Root", "Stamen", "Pistil"], "A,C,D", True),
    ("The SI unit of energy is", ["Newton", "Joule", "Watt", "Pascal"], "B", False),
    ("Which of these are magnetic materials?", ["Iron", "Copper", "Nickel", "Aluminium"], "A,C", True),
]

MCQ_NUM_PAPERS = {  # name → (title, [MCQ (q, opts, ans)], [numerical (q, answer, tolerance, unit)])
    "paper_2A": ("Motion and Measurement",
                 [("The SI unit of speed is", ["m/s", "km", "s", "m/s²"], "A"),
                  ("A body at rest has zero", ["velocity", "mass", "weight", "volume"], "A")],
                 [("A car travels 150 km in 3 hours. What is its average speed in km/h?", "50", 0.01, "km/h"),
                  ("Convert 2.5 km into metres.", "2500", 0.5, "m"),
                  ("A stone falls freely from rest for 2 s (take g = 9.8 m/s²). What is its speed after 2 s in m/s?", "19.6", 0.05, "m/s")]),
    "paper_2B": ("Matter and Heat",
                 [("Which is a chemical change?", ["Melting ice", "Burning paper", "Dissolving sugar", "Cutting wood"], "B"),
                  ("The atomic number of carbon is", ["6", "12", "8", "14"], "A")],
                 [("A block has mass 200 g and volume 50 cm³. What is its density in g/cm³?", "4", 0.01, "g/cm3"),
                  ("A liquid at 5 °C cools down by 12 °C. What is its new temperature in °C?", "-7", 0.01, "°C"),
                  ("A 40 mL solution contains 25 mL of acid. What fraction of the solution is acid? (fraction or decimal)", "0.625", 0.001, None)]),
    "paper_2C": ("Electricity and Energy",
                 [("The SI unit of resistance is", ["Ampere", "Volt", "Ohm", "Watt"], "C"),
                  ("Which device changes electrical energy into motion?", ["Generator", "Electric motor", "Battery", "Bulb"], "B")],
                 [("A 5 V battery is connected to a 10 ohm resistor. What current flows, in amperes?", "0.5", 0.01, "A"),
                  ("A bulb draws 2 A at 220 V. What is its power in watts?", "440", 0.5, "W"),
                  ("A 2 kg ball moves at 3 m/s. What is its kinetic energy in joules?", "9", 0.01, "J")]),
}


# ── Drawing helpers ─────────────────────────────────────────────────────────

def text(page, x, y, s, size=11, color=BLACK, font="helv"):
    """Single line of text with its baseline at y (long dashes → '-', the base fonts lack them)."""
    s = s.replace("—", "-").replace("–", "-")
    page.insert_text((x, y), s, fontsize=size, color=color, fontname=font)


def wrap(page, x, y, s, width, size=11, lead=14):
    """Word-wrapped paragraph; returns the y after it."""
    line = ""
    for word in s.split():
        if fitz.get_text_length(line + " " + word, fontsize=size) > width and line:
            text(page, x, y, line, size)
            y, line = y + lead, word
        else:
            line = (line + " " + word).strip()
    if line:
        text(page, x, y, line, size)
        y += lead
    return y


def header(page, title, sub, color=BLACK):
    """Paper title, subtitle and Name / Roll fields."""
    text(page, 50, 60, title, 16, color, "hebo")
    text(page, 50, 80, sub, 10, color)
    text(page, 50, 108, "Name: ______________________________      Roll no: ______________", 11, color)


def question_page(doc, title, sub, items, instructions):
    """Generic question paper (items = list of (number, text, options or None))."""
    page = doc.new_page(width=W, height=H)
    header(page, title, sub)
    y = wrap(page, 50, 140, instructions, 495, 10, 13) + 8
    for num, q, opts in items:
        if y > H - 90:
            page, y = doc.new_page(width=W, height=H), 60
        y = wrap(page, 50, y, f"{num}. {q}", 495, 11, 14)
        if opts:
            for i, o in enumerate(opts):
                text(page, 70 + (i % 2) * 240, y + (i // 2) * 15, f"({'ABCD'[i]}) {o}", 10.5)
            y += 15 * ((len(opts) + 1) // 2)
        y += 10
    return doc


# ── OMR layouts ─────────────────────────────────────────────────────────────

def omr_layout_1(page):
    """Classic: 2 columns × 10, options in a row, letters inside black bubbles, roll-number grid."""
    header(page, "EVALIFY OMR ANSWER SHEET — Layout 1", "Fill ONE bubble per question completely with a dark pen or pencil.")
    for k, (x, y) in enumerate([(20, 20), (W - 40, 20), (20, H - 40), (W - 40, H - 40)]):   # corner marks
        page.draw_rect(fitz.Rect(x, y, x + 20, y + 20), color=BLACK, fill=BLACK)
    text(page, 50, 150, "Roll number (fill one digit per row):", 10)
    for row in range(4):                                     # roll-number grid: 4 rows × digits 0–9
        for d in range(10):
            cx, cy = 90 + d * 38, 172 + row * 24
            page.draw_circle((cx, cy), 8, color=BLACK, width=0.8)
            text(page, cx - 2.8, cy + 3.5, str(d), 8)
    for q in range(20):                                      # answers: 2 columns of 10
        col, row = divmod(q, 10)
        x0, y0 = 95 + col * 255, 300 + row * 48
        text(page, x0 - 40, y0 + 4, f"{q + 1:2d}.", 12, font="hebo")
        for j in range(4):
            cx = x0 + j * 40
            page.draw_circle((cx, y0), 10, color=BLACK, width=1.0)
            text(page, cx - 3.6, y0 + 4, "ABCD"[j], 10)


def omr_layout_2(page):
    """Vertical: options A–D stacked under each question number, two bands of 10, blue print."""
    header(page, "EVALIFY OMR ANSWER SHEET — Layout 2", "Shade the bubble under each question number. Options run top to bottom.", BLUE)
    for band in range(2):
        y0 = 190 + band * 300
        for j in range(4):
            text(page, 48, y0 + j * 42 + 4, "ABCD"[j], 12, BLUE, "hebo")
        for i in range(10):
            q = band * 10 + i
            cx = 100 + i * 46
            text(page, cx - (7 if q + 1 >= 10 else 3.5), y0 - 24, str(q + 1), 12, BLUE, "hebo")
            for j in range(4):
                page.draw_circle((cx, y0 + j * 42), 11, color=BLUE, width=1.2)
        page.draw_rect(fitz.Rect(35, y0 - 45, W - 35, y0 + 150), color=BLUE, width=1)


def omr_layout_3(page):
    """Grid: 4 columns × 5 rows of numbered boxes, orange print, letters inside small bubbles, row shading."""
    header(page, "EVALIFY OMR ANSWER SHEET — Layout 3", "Fill the circle of your answer. Do not make stray marks.", ORANGE)
    for r in range(5):                                       # light shading on alternate rows
        if r % 2 == 0:
            page.draw_rect(fitz.Rect(35, 175 + r * 90, W - 35, 175 + r * 90 + 70), color=None, fill=(0.95, 0.95, 0.95))
    for q in range(20):
        col, row = q % 4, q // 4                             # numbered across rows: 1 2 3 4 / 5 6 7 8 …
        x0, y0 = 45 + col * 132, 185 + row * 90
        page.draw_rect(fitz.Rect(x0, y0, x0 + 118, y0 + 50), color=ORANGE, width=1)
        text(page, x0 + 6, y0 + 16, f"Q{q + 1}", 10, ORANGE, "hebo")
        for j in range(4):
            cx, cy = x0 + 18 + j * 27, y0 + 33
            page.draw_circle((cx, cy), 9, color=ORANGE, width=1.0)
            text(page, cx - 3, cy + 3.5, "ABCD"[j], 9, ORANGE)


# ── Answer keys / Evalify papers / label templates ──────────────────────────

def evalify_paper(name, kind, mcq, num=()):
    """Paper JSON in Evalify's format (same fields as the MongoDB document)."""
    p = {"name": name, "subject": "Basic Science", "mcqCount": len(mcq), "mcqMarks": 1,
         "mcqAnswers": {f"Q{i + 1}": a[2] for i, a in enumerate(mcq)}, "totalMarks": len(mcq) + 2 * len(num),
         "studentsWriteOnlyAnswers": True}
    if kind == "mcq":
        p["type"] = "mcq"
    else:
        p.update(type="mcq_numerical", numericalCount=len(num), numericalMarks=2,
                 numericalAnswers={f"N{i + 1}": {"answer": a, "tolerance": t, "tolerance_type": "abs", "unit": u}
                                   for i, (_, a, t, u) in enumerate(num)})
    return p


def label_csv(path, qlabels, sheet_ids, extra_cols=()):
    """Ready-to-fill template: one pre-filled row per planned sheet; type what the student ACTUALLY wrote."""
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["sheet_id", "photo_file", *extra_cols, *qlabels, "edge_cases", "notes"])
        for sid in sheet_ids:
            extra = [sid.split("_")[1][1:]] if "layout" in extra_cols else []
            w.writerow([sid, f"{sid}_p1.jpg", *extra, *["" for _ in qlabels], "", ""])


def main():
    for d in ("omr", "mcq", "mcq_num", "keys", "labels"):
        (OUT / d).mkdir(parents=True, exist_ok=True)

    # OMR: three layouts, PDF + PNG each, plus the question paper
    for i, draw in enumerate((omr_layout_1, omr_layout_2, omr_layout_3), 1):
        doc = fitz.open()
        draw(doc.new_page(width=W, height=H))
        doc.save(OUT / "omr" / f"omr_layout_{i}.pdf")
        doc[0].get_pixmap(dpi=200).save(OUT / "omr" / f"omr_layout_{i}.png")
        doc.close()
    question_page(fitz.open(), "Basic Science — OMR Test (20 questions)", "1 mark each. One correct answer per question.",
                  [(i + 1, q, o) for i, (q, o, _) in enumerate(OMR_QUESTIONS)],
                  "Mark your answers on the OMR answer sheet only. Fill exactly one bubble per question.") \
        .save(OUT / "omr" / "omr_question_paper.pdf")

    # Handwritten MCQ paper
    question_page(fitz.open(), "Basic Science — MCQ Test (10 questions)", "1 mark each. No negative marking.",
                  [(i + 1, q + ("  [one or more correct]" if multi else "  [one correct]"), o)
                   for i, (q, o, _, multi) in enumerate(MCQ_QUESTIONS)],
                  "On your answer sheet write ONLY the question number and the option letter(s), e.g. '1. B' or "
                  "'2. A, C'. Write nothing else. For [one or more correct] questions write every correct letter; "
                  "you get the mark only if your set of letters is exactly right.") \
        .save(OUT / "mcq" / "mcq_question_paper.pdf")

    # MCQ + numerical papers
    for name, (title, mcq, num) in MCQ_NUM_PAPERS.items():
        items = [(i + 1, q, o) for i, (q, o, _) in enumerate(mcq)]
        items += [(len(mcq) + i + 1, q + "  [2 marks]", None) for i, (q, *_rest) in enumerate(num)]
        question_page(fitz.open(), f"Basic Science — {title} ({name[-2:]})", "Q1–Q2: 1 mark each. Q3–Q5: 2 marks each.",
                      items, "Write ONLY the question number and your final answer, e.g. '1. B' or '4. 2500 m'. "
                             "Do rough work on the separate rough sheet — it is not evaluated.") \
            .save(OUT / "mcq_num" / f"{name}_question_paper.pdf")

    # Answer keys: one readable PDF + Evalify paper JSONs
    keys = fitz.open()
    pg = keys.new_page(width=W, height=H)
    text(pg, 50, 60, "Answer keys (teacher copy)", 16, font="hebo")
    y = 95
    sections = [("OMR test (any layout)", [f"{i + 1}. {a}" for i, (*_, a) in enumerate(OMR_QUESTIONS)]),
                ("Handwritten MCQ test", [f"{i + 1}. {a}{' (multiple)' if m else ''}" for i, (_, _, a, m) in enumerate(MCQ_QUESTIONS)])]
    for name, (title, mcq, num) in MCQ_NUM_PAPERS.items():
        sections.append((f"{name} — {title}", [f"{i + 1}. {a[2]}" for i, a in enumerate(mcq)]
                         + [f"{len(mcq) + i + 1}. {a} {u or ''} (±{t})".replace("  ", " ") for i, (_, a, t, u) in enumerate(num)]))
    for title, lines in sections:
        if y > H - 120:
            pg, y = keys.new_page(width=W, height=H), 60
        text(pg, 50, y, title, 12, font="hebo")
        y = wrap(pg, 60, y + 16, "    ".join(lines), 480, 10.5, 14) + 10
    keys.save(OUT / "keys" / "answer_keys.pdf")

    papers = {"omr_basic_science": evalify_paper("OMR Basic Science (20)", "mcq", OMR_QUESTIONS),
              "mcq_basic_science": evalify_paper("MCQ Basic Science (10)", "mcq", [(q, o, a) for q, o, a, _ in MCQ_QUESTIONS])}
    for name, (title, mcq, num) in MCQ_NUM_PAPERS.items():
        papers[name] = evalify_paper(f"{title} ({name[-2:]})", "mcq_num", mcq, num)
    for name, p in papers.items():
        (OUT / "keys" / f"{name}.json").write_text(json.dumps(p, indent=1, ensure_ascii=False))

    # Label templates: one pre-filled row per planned sheet
    label_csv(OUT / "labels" / "omr_labels.csv", [f"Q{i}" for i in range(1, 21)],
              [f"omr_L{l}_s{n:02d}" for l in (1, 2, 3) for n in range(1, 6)], extra_cols=("layout",))
    label_csv(OUT / "labels" / "mcq_labels.csv", [f"Q{i}" for i in range(1, 11)],
              [f"mcq_s{n:02d}" for n in range(1, 16)])
    for name in MCQ_NUM_PAPERS:
        label_csv(OUT / "labels" / f"{name}_labels.csv", [f"Q{i}" for i in range(1, 6)],
                  [f"{name[-2:]}_s{n:02d}" for n in range(1, 6)])

    print("written to", OUT)


if __name__ == "__main__":
    main()
