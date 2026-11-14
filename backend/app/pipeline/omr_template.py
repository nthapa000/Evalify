# omr_template.py — layout-independent OMR: learn the bubble map from one blank sheet.
#
# Per paper (once):  blank sheet → find every bubble → group bubbles into questions
#                    (rows or columns, whichever fits) → number the groups, either by
#                    reading the printed labels with the VLM or by reading order →
#                    teacher confirms the preview → stored as paper["omrTemplate"].
# Per student sheet: align the photo to the blank (ORB features + homography) →
#                    measure ink inside each known bubble MINUS the blank's own ink
#                    (printed letters inside bubbles) → filled / empty + margin.
# Marking stays deterministic; the VLM only labels the printed template.

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from app.pipeline import llm

TEMPLATE_WIDTH = 1700          # blank sheets are normalised to this width
FILL_DELTA = 0.20              # extra mean darkness (vs blank) that counts as filled
MIN_INLIERS = 40               # fewer matched features → alignment not trusted
OPTION_LETTERS = "ABCDEFGH"


# ── Bubble detection ─────────────────────────────────────────────────────────

def _gray(img: np.ndarray) -> np.ndarray:
    """BGR or grey → grey."""
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img


def _ink(gray: np.ndarray) -> np.ndarray:
    """Binary ink mask (ink = 255) that tolerates uneven lighting."""
    return cv2.adaptiveThreshold(cv2.GaussianBlur(gray, (5, 5), 0), 255,
                                 cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 10)


def darkness(gray: np.ndarray) -> np.ndarray:
    """0–1 map of how much darker each pixel is than the local paper (light pencil ≈ 0.5,
    pen ≈ 0.9, paper ≈ 0). Dividing by a closed (marks-removed) background cancels shadows."""
    bg = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (75, 75)))
    return np.clip(1.0 - gray.astype(np.float32) / np.maximum(bg.astype(np.float32), 1.0), 0.0, 1.0)


def find_bubbles(gray: np.ndarray) -> List[Tuple[float, float, float]]:
    """(cx, cy, r) of every bubble outline: round, similar-sized contours."""
    contours, _ = cv2.findContours(_ink(gray), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cands = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        area, perim = cv2.contourArea(c), cv2.arcLength(c, True)
        if not (10 <= w <= 90 and 10 <= h <= 90 and 0.75 <= w / h <= 1.33 and perim):
            continue
        if 4 * np.pi * area / perim ** 2 >= 0.70:                       # circularity
            cands.append((x + w / 2, y + h / 2, (w + h) / 4))
    if not cands:
        return []

    # Keep the dominant size (drops round letters like "O" and dots), then de-duplicate
    # inner/outer edges of the same ring
    med = float(np.median([r for _, _, r in cands]))
    cands = sorted((b for b in cands if 0.7 * med <= b[2] <= 1.4 * med), key=lambda b: -b[2])
    out: List[Tuple[float, float, float]] = []
    for b in cands:
        if all((b[0] - o[0]) ** 2 + (b[1] - o[1]) ** 2 > (0.8 * med) ** 2 for o in out):
            out.append(b)
    return out


# ── Grouping bubbles into questions ──────────────────────────────────────────

def _lines(bubbles: list, axis: int, tol: float) -> List[list]:
    """Cluster bubbles into lines along an axis (0 = same column, 1 = same row)."""
    lines: List[list] = []
    for b in sorted(bubbles, key=lambda b: b[axis]):
        if lines and abs(b[axis] - np.mean([o[axis] for o in lines[-1]])) <= tol:
            lines[-1].append(b)
        else:
            lines.append([b])
    return [sorted(l, key=lambda b: b[1 - axis]) for l in lines]


def _split_line(line: list, axis_along: int, gap_factor: float = 1.8) -> List[list]:
    """Split a line of bubbles wherever the gap is much larger than the typical spacing."""
    if len(line) < 2:
        return [line]
    pos = [b[axis_along] for b in line]
    gaps = np.diff(pos)
    cut = np.median(gaps) * gap_factor
    groups = [[line[0]]]
    for g, b in zip(gaps, line[1:]):
        (groups.append([b]) if g > cut else groups[-1].append(b))
    return groups


def group_questions(bubbles: list, n_options: Optional[int] = None) -> Tuple[List[list], str]:
    """Bubbles → question groups. Tries options-in-a-row and options-in-a-column and keeps
    the layout whose groups most consistently have the expected option count."""
    if not bubbles:
        return [], "none"
    r = float(np.median([b[2] for b in bubbles]))
    layouts = {
        "horizontal": [g for row in _lines(bubbles, 1, r) for g in _split_line(row, 0)],
        "vertical": [g for col in _lines(bubbles, 0, r) for g in _split_line(col, 1)],
    }

    def score(groups):
        sizes = [len(g) for g in groups]
        k = n_options or max(set(sizes), key=sizes.count)          # expected or most common size
        return sum(s == k for s in sizes) / len(sizes), k

    best = max(layouts, key=lambda name: score(layouts[name])[0])
    k = score(layouts[best])[1]
    return [g for g in layouts[best] if len(g) == k], best


def reading_order(groups: List[list], layout: str = "horizontal") -> List[list]:
    """Number groups the way such sheets are usually printed (the VLM overrides this when it
    can read the printed numbers):
      horizontal options → columns of questions, left→right, top→bottom inside each column;
      vertical options   → bands of questions, top→bottom, left→right inside each band."""
    if not groups:
        return []
    cx = lambda g: float(np.mean([b[0] for b in g]))  # noqa: E731
    cy = lambda g: float(np.mean([b[1] for b in g]))  # noqa: E731
    r = groups[0][0][2]
    if layout == "vertical":
        major, minor = cy, cx
        span = np.median([max(b[1] for b in g) - min(b[1] for b in g) + 2 * r for g in groups])
    else:
        major, minor = cx, cy
        span = np.median([max(b[0] for b in g) - min(b[0] for b in g) + 2 * r for g in groups])

    # Cluster groups into columns (or bands), then read each one in order
    lines: List[list] = []
    for g in sorted(groups, key=major):
        if lines and abs(major(g) - np.mean([major(o) for o in lines[-1]])) <= span * 0.6:
            lines[-1].append(g)
        else:
            lines.append([g])
    return [g for line in lines for g in sorted(line, key=minor)]


# ── VLM labelling of the printed sheet ───────────────────────────────────────

LABEL_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["groups"],
    "properties": {"groups": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["group", "question"],
        "properties": {"group": {"type": "integer"}, "question": {"type": "integer"}}}}}}


def overlay(gray: np.ndarray, groups: List[list], labels: Optional[List[str]] = None) -> np.ndarray:
    """Draw each group's box with its index (for the VLM) or its question label (for the teacher)."""
    vis = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    for i, g in enumerate(groups):
        xs, ys, r = [b[0] for b in g], [b[1] for b in g], g[0][2]
        p0, p1 = (int(min(xs) - r - 4), int(min(ys) - r - 4)), (int(max(xs) + r + 4), int(max(ys) + r + 4))
        cv2.rectangle(vis, p0, p1, (0, 0, 255), 2)
        cv2.putText(vis, labels[i] if labels else f"G{i}", (p0[0], p0[1] - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    return vis


def label_with_vlm(gray: np.ndarray, groups: List[list]) -> Optional[Dict[int, int]]:
    """Ask the VLM which printed question number each boxed group G<i> belongs to."""
    ep = llm.resolve("segmenter")
    if ep is None:
        return None
    from PIL import Image
    img = Image.fromarray(cv2.cvtColor(overlay(gray, groups), cv2.COLOR_BGR2RGB))
    r = llm.chat(ep, "This is a blank OMR answer sheet. Red boxes labelled G0, G1, … each surround "
                     "the answer bubbles of one question. For every box, read the question number "
                     "PRINTED next to it on the sheet (not the G label). Return one entry per box.",
                 [img], schema=LABEL_SCHEMA, max_tokens=4096)
    try:
        mapping = {int(e["group"]): int(e["question"]) for e in (r.data or {}).get("groups", [])}
    except (TypeError, ValueError):
        return None
    # Only trust a complete, one-to-one mapping
    ok = len(mapping) == len(groups) and len(set(mapping.values())) == len(groups)
    return mapping if ok else None


# ── Building the template ────────────────────────────────────────────────────

def build_template(blank: np.ndarray, mcq_count: int, n_options: Optional[int] = None,
                   use_vlm: bool = True) -> dict:
    """Blank sheet → {size, layout, numbering, bubbles:[{q, opt, x, y, r, base}], warnings}."""
    # Normalise width so pixel thresholds behave the same for every upload
    s = TEMPLATE_WIDTH / blank.shape[1]
    gray = _gray(cv2.resize(blank, None, fx=s, fy=s, interpolation=cv2.INTER_AREA))
    groups, layout = group_questions(find_bubbles(gray), n_options)
    warnings = []

    # Number the groups: printed labels (VLM) if it gives a clean answer, else reading order
    groups = reading_order(groups, layout)
    mapping = label_with_vlm(gray, groups) if use_vlm else None
    if mapping:
        numbered = sorted((mapping[i], g) for i, g in enumerate(groups))
        numbering = "printed labels (VLM)"
    else:
        numbered = [(i + 1, g) for i, g in enumerate(groups)]
        numbering = "reading order"
    if len(numbered) != mcq_count:
        warnings.append(f"found {len(numbered)} questions, paper has {mcq_count}")

    # Each bubble: question, option letter (reading order within the group), position, blank ink
    ink = darkness(gray)
    bubbles = []
    for qn, g in numbered:
        for j, (x, y, r) in enumerate(g):
            bubbles.append({"q": f"Q{qn}", "opt": OPTION_LETTERS[j], "x": round(x, 1), "y": round(y, 1),
                            "r": round(r, 1), "base": round(_fill(ink, x, y, r), 3)})
    return {"size": [gray.shape[1], gray.shape[0]], "layout": layout, "numbering": numbering,
            "questions": len(numbered), "options": len(numbered[0][1]) if numbered else 0,
            "bubbles": bubbles, "warnings": warnings, "confirmed": False}


def preview(blank: np.ndarray, template: dict) -> np.ndarray:
    """Blank sheet with each detected bubble labelled 'Q12-C' for the teacher to check."""
    s = template["size"][0] / blank.shape[1]
    vis = cv2.resize(blank if blank.ndim == 3 else cv2.cvtColor(blank, cv2.COLOR_GRAY2BGR), None, fx=s, fy=s)
    for b in template["bubbles"]:
        cv2.circle(vis, (int(b["x"]), int(b["y"])), int(b["r"]) + 3, (0, 160, 0), 2)
        if b["opt"] == "A":
            cv2.putText(vis, b["q"], (int(b["x"] - 3 * b["r"]), int(b["y"] - 1.6 * b["r"])),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 220), 1)
    return vis


# ── Reading a student sheet ──────────────────────────────────────────────────

def _fill(dark: np.ndarray, x: float, y: float, r: float) -> float:
    """Mean darkness inside the inner 70 % of a bubble (skips the printed ring)."""
    mask = np.zeros(dark.shape, np.uint8)
    cv2.circle(mask, (int(round(x)), int(round(y))), max(2, int(r * 0.7)), 255, -1)
    return float(cv2.mean(dark, mask=mask)[0])


def align(photo: np.ndarray, blank: np.ndarray, size: list) -> Tuple[Optional[np.ndarray], int]:
    """Warp the student photo onto the blank template frame; returns (aligned grey, inliers)."""
    tw, th = size
    tpl = _gray(cv2.resize(blank, (tw, th), interpolation=cv2.INTER_AREA))
    s = tw / photo.shape[1]
    img = _gray(cv2.resize(photo, None, fx=s, fy=s, interpolation=cv2.INTER_AREA))

    # ORB keypoints on both, cross-checked matches, RANSAC homography
    orb = cv2.ORB_create(5000)
    k1, d1 = orb.detectAndCompute(img, None)
    k2, d2 = orb.detectAndCompute(tpl, None)
    if d1 is None or d2 is None:
        return None, 0
    matches = sorted(cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(d1, d2), key=lambda m: m.distance)[:1500]
    if len(matches) < MIN_INLIERS:
        return None, len(matches)
    src = np.float32([k1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    dst = np.float32([k2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
    H, inl = cv2.findHomography(src, dst, cv2.RANSAC, 4.0)
    n_in = int(inl.sum()) if inl is not None else 0
    if H is None or n_in < MIN_INLIERS:
        return None, n_in
    return cv2.warpPerspective(img, H, (tw, th), borderValue=255), n_in


def read_sheet(photo: np.ndarray, blank: np.ndarray, template: dict) -> dict:
    """→ {"aligned": bool, "inliers": n, "answers": {Q: {"answer", "deltas", "margin"}}}."""
    aligned, inliers = align(photo, blank, template["size"])
    if aligned is None:
        return {"aligned": False, "inliers": inliers, "answers": {}}
    ink = darkness(aligned)

    # Darkness above the blank's own (printed letters), per bubble; filled if ≥ FILL_DELTA
    by_q: Dict[str, list] = {}
    for b in template["bubbles"]:
        delta = _fill(ink, b["x"], b["y"], b["r"]) - b["base"]
        by_q.setdefault(b["q"], []).append((b["opt"], delta))
    answers = {}
    for q, opts in by_q.items():
        picked = sorted(o for o, d in opts if d >= FILL_DELTA)
        answers[q] = {"answer": ",".join(picked), "deltas": {o: round(d, 3) for o, d in opts},
                      "margin": round(min(abs(d - FILL_DELTA) for _, d in opts), 3)}
    return {"aligned": True, "inliers": inliers, "answers": answers}
