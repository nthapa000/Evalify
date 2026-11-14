#!/usr/bin/env python3
"""make_example.py — build eval/data/example: 2 synthetic Type-3 sheets for smoke tests.

Rendered in OpenCV's script font, so it checks plumbing, not handwriting accuracy.
Each sheet plants a deliberate spelling error ("proccess") to exercise the
over-correction metric. Real evaluation needs real scanned / photographed sheets.
"""
import json
from pathlib import Path

import cv2
import numpy as np

OUT = Path(__file__).resolve().parent / "data" / "example"

# Paper in the same shape as a MongoDB paper document
PAPER = {
    "name": "Example Biology Quiz", "subject": "Biology", "type": "mcq_numerical_subjective",
    "mcqCount": 2, "mcqMarks": 1, "mcqAnswers": {"Q1": "B", "Q2": "A,C"},
    "numericalCount": 1, "numericalMarks": 2,
    "numericalAnswers": {"N1": {"answer": "0.625", "tolerance": 0.001}},
    "subjectiveCount": 1, "subjectiveMarks": 3, "subjectiveQuestionMarks": {"S1": 3},
    "subjectiveQuestions": ["What is photosynthesis?"],
    "subjectiveRubrics": [{"key_concepts": ["uses light energy", "produces glucose", "releases oxygen"],
                           "mandatory_concepts": ["uses light energy"], "marks_per_concept": 1,
                           "model_answer": "Plants use light energy to turn CO2 and water into glucose, releasing oxygen."}],
    "totalMarks": 7,
}

# Two students: one mostly right, one with mistakes
SHEETS = [
    ("ex001", "dev", {"Q1": "B", "Q2": "A,C", "N1": "5/8",
                      "S1": "Photosynthesis is the proccess where plants\nuse light energy to make glucose\nand release oxygen."}, 3),
    ("ex002", "test", {"Q1": "C", "Q2": "A", "N1": "0.65",
                       "S1": "It is the proccess plants use to\nmake food from water."}, 0),
]


def render(answers: dict, path: Path) -> list:
    """Draw one A4-ish page; return gold crop boxes (0–1000) per question."""
    h, w = 2200, 1600
    page = np.full((h, w, 3), 250, np.uint8)
    y, boxes = 140, {}
    for label, qid in (("Q1", "Q1"), ("Q2", "Q2"), ("Q3", "N1"), ("S1", "S1")):
        lines = f"{label}: {answers[qid]}".split("\n")
        y0 = y - 60
        for line in lines:
            cv2.putText(page, line, (100, y), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 2.0, (40, 40, 120), 3, cv2.LINE_AA)
            y += 90
        boxes[qid] = {"page": 0, "bbox": [40, int(y0 / h * 1000), 960, int((y - 40) / h * 1000)]}
        y += 80
    cv2.imwrite(str(path), page)
    return boxes


def main():
    (OUT / "images").mkdir(parents=True, exist_ok=True)
    (OUT / "papers").mkdir(exist_ok=True)
    (OUT / "papers" / "bio_quiz.json").write_text(json.dumps(PAPER, indent=1))
    rows = []
    for sid, split, ans, subj_marks in SHEETS:
        boxes = render(ans, OUT / "images" / f"{sid}_p1.png")
        gold = {
            "Q1": {"answer": ans["Q1"], "crop": boxes["Q1"]},
            "Q2": {"answer": ans["Q2"], "crop": boxes["Q2"]},
            "N1": {"answer": ans["N1"], "crop": boxes["N1"]},
            "S1": {"transcript": ans["S1"], "marks": subj_marks, "crop": boxes["S1"],
                   "concepts": {"uses light energy": subj_marks > 0, "produces glucose": subj_marks > 0,
                                "releases oxygen": subj_marks > 0},
                   "planted_errors": [{"wrong": "proccess", "correct": "process"}]},
        }
        rows.append({"sheet_id": sid, "split": split, "paper": "papers/bio_quiz.json",
                     "sheet_type": "handwritten", "pages": [f"images/{sid}_p1.png"], "gold": gold})
    (OUT / "manifest.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    print(f"wrote {len(rows)} sheets → {OUT}")


if __name__ == "__main__":
    main()
