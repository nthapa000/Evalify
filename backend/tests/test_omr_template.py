# test_omr_template.py — layout-independent OMR on synthetic sheets in two different layouts.

import random

import cv2
import numpy as np
import pytest

from app.pipeline import omr_template as T

FONT = cv2.FONT_HERSHEY_SIMPLEX


def make_blank(layout: str, n_q: int = 24, n_opt: int = 4, seed: int = 0):
    """Draw a blank OMR sheet; returns (image, {Qn: [(opt, cx, cy, r)]})."""
    rng = random.Random(seed)
    h, w = 2200, 1700
    img = np.full((h, w, 3), 255, np.uint8)
    # Header with text gives the aligner something to lock on to
    cv2.putText(img, "EVALIFY  MIDTERM  QUIZ", (330, 140), FONT, 2.2, (0, 0, 0), 4)
    cv2.putText(img, "Name: ____________  Roll: ________", (120, 240), FONT, 1.2, (0, 0, 0), 2)
    for k in range(12):                                            # random decorations
        x, y = rng.randint(80, w - 200), rng.randint(2000, 2150)
        cv2.putText(img, rng.choice(["#", "*", "Q", "%", "&"]), (x, y), FONT, 1.4, (0, 0, 0), 2)
    cv2.rectangle(img, (60, 60), (w - 60, h - 60), (0, 0, 0), 3)
    pos, r = {}, 22
    if layout == "horizontal":                                     # 3 columns, options in a row
        for q in range(n_q):
            col, row = divmod(q, n_q // 3)
            x0, y0 = 150 + col * 520, 380 + row * 190
            cv2.putText(img, f"{q + 1}.", (x0 - 70, y0 + 10), FONT, 1.0, (0, 0, 0), 2)
            pos[f"Q{q + 1}"] = []
            for j in range(n_opt):
                cx = x0 + j * 90
                cv2.circle(img, (cx, y0), r, (0, 0, 0), 2)
                cv2.putText(img, "ABCD"[j], (cx - 9, y0 + 9), FONT, 0.7, (90, 90, 90), 1)
                pos[f"Q{q + 1}"].append(("ABCD"[j], cx, y0, r))
    else:                                                          # options stacked vertically
        for q in range(n_q):
            band, idx = divmod(q, n_q // 2)
            x0, y0 = 160 + idx * 115, 420 + band * 820
            cv2.putText(img, f"{q + 1}", (x0 - 14, y0 - 50), FONT, 1.0, (0, 0, 0), 2)
            pos[f"Q{q + 1}"] = []
            for j in range(n_opt):
                cy = y0 + j * 95
                cv2.circle(img, (x0, cy), r, (0, 0, 0), 2)
                pos[f"Q{q + 1}"].append(("ABCD"[j], x0, cy, r))
    return img, pos


def fill(blank, pos, seed: int = 1):
    """Fill answers (some light pencil, one double mark, one blank); returns (sheet, truth)."""
    rng = random.Random(seed)
    img, truth = blank.copy(), {}
    for i, (q, opts) in enumerate(pos.items()):
        if i == 3:
            truth[q] = ""                                          # left blank
            continue
        picks = rng.sample(opts, 2) if i == 5 else [rng.choice(opts)]   # one double mark
        shade = 120 if i % 7 == 0 else 20                          # some light pencil
        for opt, cx, cy, r in picks:
            cv2.circle(img, (cx, cy), r - 3, (shade, shade, shade), -1)
        truth[q] = ",".join(sorted(o for o, *_ in picks))
    return img, truth


def as_photo(img, seed: int = 2):
    """Tilt, perspective, uneven light, blur and noise — a phone photo of the sheet."""
    rng = np.random.default_rng(seed)
    h, w = img.shape[:2]
    canvas = np.full((h + 400, w + 400, 3), 70, np.uint8)          # dark table around the page
    canvas[200:200 + h, 200:200 + w] = img
    src = np.float32([[200, 200], [200 + w, 200], [200 + w, 200 + h], [200, 200 + h]])
    dst = src + rng.uniform(-90, 90, src.shape).astype(np.float32)
    out = cv2.warpPerspective(canvas, cv2.getPerspectiveTransform(src, dst), (w + 400, h + 400))
    grad = np.linspace(0.75, 1.05, out.shape[1])[None, :, None]    # lighting gradient
    out = np.clip(out * grad + rng.normal(0, 6, out.shape), 0, 255).astype(np.uint8)
    return cv2.GaussianBlur(out, (3, 3), 0)


# Why: the OMR template must find every bubble on the teacher's blank sheet
@pytest.mark.parametrize("layout", ["horizontal", "vertical"])
def test_template_learns_layout(layout):
    blank, pos = make_blank(layout)
    tpl = T.build_template(blank, mcq_count=24, use_vlm=False)
    assert tpl["layout"] == layout
    assert tpl["questions"] == 24 and tpl["options"] == 4 and not tpl["warnings"]


# Why: a phone photo of a filled OMR sheet must be read through the template (partial fills count)
@pytest.mark.parametrize("layout", ["horizontal", "vertical"])
def test_reads_phone_photo(layout):
    blank, pos = make_blank(layout)
    tpl = T.build_template(blank, mcq_count=24, use_vlm=False)
    sheet, truth = fill(blank, pos)
    res = T.read_sheet(as_photo(sheet), blank, tpl)
    assert res["aligned"], res
    got = {q: a["answer"] for q, a in res["answers"].items()}
    assert got == truth


# Why: a photo that is not this OMR sheet must not be read as one
def test_unrelated_photo_is_not_aligned():
    blank, _ = make_blank("horizontal")
    tpl = T.build_template(blank, mcq_count=24, use_vlm=False)
    noise = np.random.default_rng(0).integers(0, 255, (2000, 1500, 3), dtype=np.uint8)
    assert not T.read_sheet(noise, blank, tpl)["aligned"]


# Full pipeline: paper with a learned template → photographed sheet → scores + routing
# Why: a paper with a confirmed OMR template must be graded with it
def test_orchestrator_uses_template(tmp_path, monkeypatch):
    from app.pipeline import orchestrator
    monkeypatch.chdir(tmp_path)
    (tmp_path / "uploads" / "papers").mkdir(parents=True)
    blank, pos = make_blank("vertical")
    cv2.imwrite(str(tmp_path / "uploads" / "papers" / "blank.png"), blank)
    tpl = T.build_template(blank, mcq_count=24, use_vlm=False)
    tpl.update(blank_url="/api/papers/files/blank.png", confirmed=True)

    sheet, truth = fill(blank, pos)
    photo = tmp_path / "sub_p0.png"
    cv2.imwrite(str(photo), as_photo(sheet))
    paper = {"type": "mcq", "mcqCount": 24, "mcqMarks": 1, "omrTemplate": tpl,
             "mcqAnswers": {q: (a or "A") for q, a in truth.items()}}       # key = what was marked

    out = orchestrator.run(paper, [str(photo)], "omr")
    assert out["models"]["reader_a"] == "omr_template"
    # Every marked question is correct; only the blank one (Q4) scores 0
    assert out["n_correct"] == 23
    assert {d["question"]: d["student_answer"] for d in out["mcq_detail"]}["Q6"] == truth["Q6"]
