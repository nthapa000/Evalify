# test_pipeline_logic.py — model-free tests for the two-reader pipeline.

import numpy as np
import cv2
from PIL import Image

from app.pipeline import quality, readers, routing
from app.pipeline.grader import ConceptDecision, GradeResult, quote_in, score
from app.pipeline.readers import Question, Reading
from app.pipeline.textdist import cer, wer


# Sheet numbering: numerical continues the Q-labels, subjective uses S-labels
def test_questions_for():
    paper = {"type": "mcq_numerical_subjective", "mcqCount": 2, "numericalCount": 1, "subjectiveCount": 1}
    qs = readers.questions_for(paper)
    assert [(q.id, q.label, q.kind) for q in qs] == [
        ("Q1", "Q1", "mcq"), ("Q2", "Q2", "mcq"), ("N1", "Q3", "numerical"), ("S1", "S1", "subjective")]


# OCR-specialist output cleaning and parsing
def test_ocr_parsing():
    html = "<p>Q3: <del>B</del> D</p>"
    text = readers.clean_ocr(html)
    assert text == "Q3: ~~B~~ D"
    assert readers.parse_letters(readers.strip_label(text, "Q3")) == "D"     # struck-out B ignored
    assert readers.parse_final_number("v = u + at\n= 2 + 3\nAns = 5 m/s") == "5 m/s"
    assert readers.strip_label("7) 3.5", "Q7") == "3.5"
    assert readers.parse_final_number("23: 0.65") == "0.65"               # misread label dropped


# Reader agreement per question type
def test_agree():
    a = Reading(status="answered", value="0.5")
    assert readers.agree("numerical", a, Reading(status="answered", value="1/2")) is True
    assert readers.agree("mcq", Reading(status="answered", value="A"), Reading(status="answered", value="B")) is False
    assert readers.agree("mcq", a, Reading()) is None                       # no second reader


# Marks summed in Python with the mandatory rule
def test_concept_scoring():
    rubric = {"key_concepts": ["a", "b", "c"], "mandatory_concepts": ["b"], "marks_per_concept": 2}
    g = GradeResult(decisions=[ConceptDecision("a", True), ConceptDecision("b", True), ConceptDecision("c", False)])
    score(g, rubric)
    assert (g.marks, g.max_marks, g.mandatory_met) == (4, 6, True)
    g.decisions[1].present = False
    score(g, rubric)
    assert (g.marks, g.mandatory_met) == (0, False)
    g.decisions = [ConceptDecision(c, True) for c in "abc"]
    score(g, rubric, max_marks=5)
    assert g.marks == 5                                                     # capped


# Evidence must actually appear in a transcript
def test_quote_in():
    assert quote_in("light energy is absorbed", "Chlorophyll: light energy is absorbed by leaves")
    assert not quote_in("glucose is produced", "light energy is absorbed")


# Routing rules fire for disagreement, low confidence and grader gaps
def test_routing():
    a, b = Reading(status="answered", value="A", confidence=0.4), Reading(status="answered", value="B")
    reasons = routing.reader_reasons("mcq", a, b, agreed=False)
    assert any("disagree" in r for r in reasons) and any("confidence" in r for r in reasons)
    assert routing.omr_reasons(0.01) and not routing.omr_reasons(0.2)
    g1 = GradeResult(marks=4, decisions=[ConceptDecision("x", True, confidence=0.9)])
    g2 = GradeResult(marks=1)
    assert any("graders differ" in r for r in routing.grader_reasons(g1, g2))


# CER / WER
def test_textdist():
    assert cer("abc", "abc") == 0 and round(cer("abcd", "abed"), 2) == 0.25
    assert wer("the cat sat", "the cat sat down") == 1 / 3


# Quality gate: a sharp synthetic page passes, a blurred copy fails
def test_quality_gate(tmp_path):
    page = np.full((2200, 1600, 3), 255, np.uint8)
    for y in range(150, 2100, 60):
        cv2.putText(page, "The quick brown fox 12345", (80, y), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 0, 0), 3)
    sharp, blurry = tmp_path / "sharp.png", tmp_path / "blurry.png"
    cv2.imwrite(str(sharp), page)
    cv2.imwrite(str(blurry), cv2.GaussianBlur(page, (61, 61), 0))
    img, rep = quality.prepare(str(sharp))
    assert rep.ok and max(img.size) <= quality.TARGET_LONG_SIDE
    assert "image is blurry" in quality.prepare(str(blurry))[1].reasons


# Abstention = no usable answer; only then is the tie-break reader asked
def test_abstained():
    from app.pipeline.orchestrator import abstained
    assert abstained(Reading(status="blank")) and abstained(Reading(status="unclear", value=""))
    assert abstained(Reading(status="error")) and abstained(Reading(status="answered", value=""))
    assert not abstained(Reading(status="answered", value="B"))


# Label stripping must not eat the integer part of a decimal answer ("3. 4.01" → "4.01", not "01")
def test_label_strip_keeps_decimals():
    from app.pipeline.readers import parse_final_number, strip_label
    assert parse_final_number(strip_label("3. 4.01", "Q3")) == "4.01"
    assert parse_final_number(strip_label("Q5: 0.626", "Q5")) == "0.626"
    assert strip_label("3.5", "Q3") == "3.5"


# Students often write a comma after the question number ("4, 440 W"); "4,440" stays a number
def test_label_strip_comma():
    from app.pipeline.readers import parse_final_number, strip_label
    assert parse_final_number(strip_label("4, 440 W", "Q4")) == "440 W"
    assert strip_label("4,440", "Q4") == "4,440"


# Grader v2: a partial concept earns half its marks; mandatory still needs a full "present"
def test_score_partial_credit():
    res = GradeResult(decisions=[ConceptDecision("a", present=True), ConceptDecision("b", partial=True)])
    score(res, {"marks_per_concept": 1})
    assert res.marks == 1.5
    res = GradeResult(decisions=[ConceptDecision("a", partial=True), ConceptDecision("b", present=True)])
    score(res, {"marks_per_concept": 1, "mandatory_concepts": ["a"]})
    assert res.marks == 0.0


# A ruled frame printed on white paper must not be treated as the paper edge (margin labels were cut off)
def test_find_page_ignores_printed_frame():
    import cv2
    import numpy as np
    from app.pipeline import quality
    sheet = np.full((1000, 700, 3), 250, np.uint8)
    cv2.rectangle(sheet, (90, 80), (660, 950), (40, 40, 40), 3)          # printed answer box
    assert quality.find_page(sheet) is None
    photo = np.full((1000, 700, 3), 90, np.uint8)                          # dark desk
    cv2.rectangle(photo, (60, 50), (640, 960), (250, 250, 250), -1)        # white paper on it
    assert quality.find_page(photo) is not None
