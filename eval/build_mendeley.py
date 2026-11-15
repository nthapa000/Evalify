#!/usr/bin/env python3
"""build_mendeley.py — turn the Mendeley exam set into an Evalify labelled set (eval/data/mendeley).

Source: "A Dataset of Digitized Student Examination Papers, Answer Keys, and Manual
Evaluations for Automated Grading Research", Dinesh K P, Mendeley Data sf3kvjwknt v1,
CC BY 4.0. https://data.mendeley.com/datasets/sf3kvjwknt/1

    python eval/build_mendeley.py <extracted dataset dir> [--sheets 1-12]

Writes papers/ds_exam.json (answer key + rubric), images/Student_N_p<k>.png and
manifest.jsonl. Gold: MCQ letters and per-question teacher marks come from
Teacher_manual_marks_Anonymized.csv (anonymised; Student_MCQ.csv is NOT used because it
contains real names). Short-answer transcripts are not in the dataset.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import fitz

OUT = Path(__file__).resolve().parent / "data" / "mendeley"

# Short-answer questions Q21–Q35 (from Question.txt)
QUESTIONS = [
    "Define Supervised Learning.",
    "Evaluation Case Study: A model (M1) achieves 99% accuracy on the training set but only 30% accuracy on the testing set. What is happening to this model?",
    "What is Regression Analysis?",
    "List and elucidate two major challenges in Machine Learning.",
    "List any two major real-world applications of Data Science.",
    "Distinguish between Structured and Semi-structured data.",
    "Describe methods used to detect and handle outliers in a dataset.",
    "What is Data Pre-processing?",
    "Why is Data Normalization required for the K-Nearest Neighbors (K-NN) algorithm?",
    "How are continuous attributes discretized? Give an example.",
    "What does the 'K' represent in the K-Means clustering algorithm?",
    "Name three common Hyperparameters in Machine Learning algorithms.",
    "Define Gradient Descent.",
    "Classifier Comparison: Compare three SVM classifiers based on their margins and boundaries.",
    "Explain how the Radial Basis Function (RBF) Kernel works in SVM.",
]

# Model answers (answerkey.txt) and concept rubrics DRAFTED BY CLAUDE from them — 2 concepts
# × 1 mark per question; the teacher's real rubric is not in the dataset, review before use.
RUBRICS = [
    ("A type of ML where the model is trained on labeled data with known inputs and outputs.",
     ["model is trained on labeled data", "learns from known inputs and outputs to make predictions"]),
    ("Overfitting; the model has memorized the training data but failed to generalize.",
     ["identifies the problem as overfitting", "model memorised training data and fails to generalise to new/test data"]),
    ("A statistical process for estimating the relationships between a dependent variable and one or more independent variables.",
     ["a statistical method / process", "estimates the relationship between a dependent and independent variable(s)"]),
    ("Data quality/missing values, overfitting/underfitting, data collection, or time consumption.",
     ["names and explains one valid machine-learning challenge", "names and explains a second, different valid challenge"]),
    ("Healthcare/disease prediction, Finance/fraud detection, E-commerce recommendation systems.",
     ["one valid real-world application of data science", "a second, different valid application"]),
    ("Structured is organized in rows/columns (SQL, Excel); Semi-structured has some markers but isn't in a grid (JSON, XML, HTML).",
     ["structured data is organised in rows/columns or tables (e.g. SQL, Excel, CSV)",
      "semi-structured data has tags/markers but no fixed table form (e.g. JSON, XML, HTML)"]),
    ("Detection: Z-score, IQR, Scatter plots, Box plots. Handling: Trimming, Capping, or Imputation.",
     ["a method to detect outliers (e.g. Z-score, IQR, box or scatter plot)",
      "a method to handle outliers (e.g. trimming, capping, imputation)"]),
    ("The steps taken to clean and transform raw data into a format suitable for a machine learning model.",
     ["cleaning raw data (missing, incorrect or noisy values)", "transforming data into a form suitable for a model"]),
    ("K-NN is distance-based; features with larger scales will dominate the distance calculation if not normalized.",
     ["K-NN relies on distances between points", "features with larger scales dominate the distance unless normalised"]),
    ("By grouping values into bins or intervals, e.g., turning ages 1-100 into 'Child,' 'Adult,' 'Senior.'",
     ["continuous values are grouped into bins / intervals", "gives a valid example of discretisation"]),
    ("The predefined number of clusters or groups the data will be divided into.",
     ["K is the number of clusters", "K is chosen / fixed beforehand"]),
    ("K in K-NN, Learning Rate, Number of Estimators/Trees, Max Depth, or Batch Size.",
     ["names at least two valid hyperparameters", "names a third valid hyperparameter"]),
    ("An optimization algorithm used to minimize the cost function by iteratively moving toward the steepest descent.",
     ["an optimisation algorithm that minimises a cost / loss function",
      "iteratively updates parameters in the direction of steepest descent (negative gradient)"]),
    ("Discussion on maximizing the margin and ensuring no data points fall within the 'gutter' or margin.",
     ["compares the classifiers by margin width (wider margin is better)",
      "considers whether data points fall inside the margin / gutter"]),
    ("It transforms data into a higher-dimensional space to find a non-linear decision boundary.",
     ["maps data into a higher-dimensional space", "allows a non-linear decision boundary"]),
]

MCQ_KEY = "B C A C B A A C A B B C B C B C B C B B".split()


def paper() -> dict:
    """Evalify paper document for this exam."""
    return {
        "name": "Data Science exam (Mendeley sf3kvjwknt)", "subject": "Data Science",
        "type": "mcq_numerical_subjective", "numbering": "continuous",
        "mcqCount": 20, "mcqMarks": 1, "mcqAnswers": {f"Q{i + 1}": k for i, k in enumerate(MCQ_KEY)},
        "numericalCount": 0, "subjectiveCount": 15, "subjectiveMarks": 2,
        "subjectiveQuestionMarks": {f"S{i}": 2 for i in range(1, 16)},
        "subjectiveQuestions": QUESTIONS,
        "subjectiveRubrics": [{"key_concepts": c, "mandatory_concepts": [], "marks_per_concept": 1,
                               "model_answer": m, "rubric_source": "drafted by Claude from answerkey.txt"}
                              for m, c in RUBRICS],
        "totalMarks": 50,
        "source": {"dataset": "Mendeley sf3kvjwknt v1", "licence": "CC BY 4.0",
                   "url": "https://data.mendeley.com/datasets/sf3kvjwknt/1"},
    }


def mark(v: str):
    """Teacher mark cell → float, or None for blank / NC (not attempted / not corrected)."""
    v = (v or "").strip()
    return None if v.upper() in ("", "NC", "NM") else float(v)        # NC / NM = not corrected / not marked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="extracted dataset folder (contains Student_Pdf/)")
    ap.add_argument("--sheets", default="1-12", help="student numbers, e.g. 1-12")
    args = ap.parse_args()
    src = Path(args.src)
    lo, hi = (int(x) for x in args.sheets.split("-"))

    (OUT / "papers").mkdir(parents=True, exist_ok=True)
    (OUT / "images").mkdir(exist_ok=True)
    (OUT / "papers" / "ds_exam.json").write_text(json.dumps(paper(), indent=1))
    rows = {r["Student_ID"]: r for r in csv.DictReader(open(src / "Teacher_manual_marks_Anonymized.csv"))}

    lines = []
    for n in range(lo, hi + 1):
        sid = f"Student_{n}"
        # Render each PDF page at its native ~1786 px width (pages are scanned images)
        pages = []
        with fitz.open(src / "Student_Pdf" / f"{sid}.pdf") as doc:
            for i, page in enumerate(doc):
                name = f"images/{sid}_p{i + 1}.png"
                page.get_pixmap(matrix=fitz.Matrix(1, 1)).save(OUT / name)
                pages.append(name)

        # Gold: chosen MCQ letter + teacher mark per short answer (S1 = Q21 … S15 = Q35)
        r = rows[sid]
        gold = {f"Q{i}": {"answer": r[str(i)].strip()} for i in range(1, 21)}
        for i in range(21, 36):
            m = mark(r[str(i)])
            gold[f"S{i - 20}"] = {"marks": m} if m is not None else {"marks": None, "note": "blank/NC in teacher CSV"}
        lines.append({"sheet_id": sid, "split": "dev", "paper": "papers/ds_exam.json",
                      "sheet_type": "handwritten", "pages": pages, "gold": gold,
                      "teacher_totals": {"mcq": mark(r["MCQ mark"]), "short": mark(r["2 marks"]), "total": mark(r["total"])}})
        print(f"{sid}: {len(pages)} pages")
    (OUT / "manifest.jsonl").write_text("\n".join(json.dumps(l) for l in lines) + "\n")


if __name__ == "__main__":
    main()
