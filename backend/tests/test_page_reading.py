# test_page_reading.py — whole-page reading, majority vote and subjective transcription by label.
# Written before app/pipeline/page_reading.py (test-first). No GPU, no MongoDB.

from app.pipeline import page_reading as pr
from app.pipeline.readers import Question, Reading

QS = [Question("Q1", "Q1", "mcq"), Question("Q2", "Q2", "mcq"), Question("N1", "Q3", "numerical"),
      Question("S1", "Q4", "subjective"), Question("S2", "Q5", "subjective")]
CLOSED = [q for q in QS if q.kind != "subjective"]


def r(value="", status=None):
    """Short Reading for tests."""
    return Reading(reader="m", status=status or ("answered" if value else "blank"), value=value)


# ── page JSON / OCR text → readings ──────────────────────────────────────────

def test_page_json_maps_labels_and_normalises_mcq():
    data = {"answers": [{"label": "1", "status": "answered", "value": "c a"},
                        {"label": "Q3", "status": "answered", "value": "2500 m"},
                        {"label": "Q2", "status": "unclear", "value": ""}]}
    got = pr.readings_from_page_json(data, CLOSED, reader="m")
    assert got["Q1"].value == "A,C" and got["Q1"].status == "answered"
    assert got["N1"].value == "2500 m"
    assert got["Q2"].status == "unclear"


def test_page_json_missing_question_is_blank():
    got = pr.readings_from_page_json({"answers": []}, CLOSED, reader="m")
    assert all(x.status == "blank" and x.value == "" for x in got.values())


def test_ocr_text_lines_by_number():
    got = pr.readings_from_ocr_text("1. B\n2) A, D\n3. 4.01 V\nnotes", CLOSED, reader="glm")
    assert got["Q1"].value == "B"
    assert got["Q2"].value == "A,D"
    assert got["N1"].value.startswith("4.01")          # decimal is not taken for a label


def test_merge_pages_first_answer_wins():
    p1 = {"Q1": r("B"), "Q2": r(), "N1": r(status="unclear")}
    p2 = {"Q1": r("D"), "Q2": r("A"), "N1": r()}
    m = pr.merge_pages([p1, p2], CLOSED)
    assert m["Q1"].value == "B" and m["Q2"].value == "A"
    assert m["N1"].status == "unclear"                  # unclear beats blank


# ── majority vote ────────────────────────────────────────────────────────────

def test_decide_agree_accepts():
    final, reason = pr.decide("mcq", r("A,C"), r("C,A"))
    assert final.value == "A,C" and reason == ""


def test_decide_third_reader_breaks_tie():
    final, reason = pr.decide("mcq", r("B"), r("D"), r("D"))
    assert final.value == "D" and reason == ""


def test_decide_no_majority_goes_to_ta_with_one_reason():
    final, reason = pr.decide("mcq", r("B"), r("D"), r("A"))
    assert final is None and "B" in reason and "D" in reason


def test_decide_abstention_confirmed_by_third_reader():
    final, _ = pr.decide("numerical", r(status="unclear"), r("19.6"), r("19.60"))
    assert final.value == "19.6"


def test_decide_both_blank_is_blank():
    final, reason = pr.decide("mcq", r(), r())
    assert final is not None and final.value == "" and reason == ""


def test_decide_without_third_reader():
    final, reason = pr.decide("mcq", r("B"), r("D"), None)
    assert final is None and reason


# ── subjective: transcription grouped by label ───────────────────────────────

def test_split_marked_labels_continued_and_crossed():
    text = "[[CONTINUED]] end of four\n[[Q5]] first line\nsecond line\n[[Q4 CROSSED]] old try"
    items, last = pr.split_marked(text, last_label="Q4")
    assert items[0] == ("Q4", False, "end of four")
    assert items[1] == ("Q5", False, "first line\nsecond line")
    assert items[2] == ("Q4", True, "old try")
    assert last == "Q4"


def test_items_from_page_json():
    data = {"answers": [{"label": "CONTINUED", "text": "rest", "fully_crossed_out": False},
                        {"label": "5", "text": "answer five", "fully_crossed_out": False}]}
    items, last = pr.items_from_page_json(data, last_label="Q4")
    assert items == [("Q4", False, "rest"), ("Q5", False, "answer five")] and last == "Q5"


def test_merge_attempts_drops_crossed_out_when_rewritten():
    store = {}
    pr.merge_attempts(store, [("Q4", True, "wrong first try"), ("Q4", False, "rewrite")])
    assert store["Q4"] == "rewrite"
    pr.merge_attempts(store, [("Q5", True, "only attempt, crossed")])
    assert store["Q5"] == "only attempt, crossed"
    pr.merge_attempts(store, [("Q4", False, "continued on next page")])
    assert store["Q4"] == "rewrite\ncontinued on next page"


def test_mcq_labels_are_not_subjective_answers():
    # "7. A" on the MCQ page must not end up as a subjective answer
    store = {}
    pr.merge_attempts(store, [("Q1", False, "A"), ("Q4", False, "real answer")])
    subj = pr.subjective_texts(store, {}, QS)
    assert set(subj) == {"S1"} and subj["S1"] == ("real answer", "")
