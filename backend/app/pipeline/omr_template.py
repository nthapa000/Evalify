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
FILL_DELTA = 0.10              # darkness above the blank (after the sheet's print offset) = filled
MIN_INLIERS = 40               # fewer matched features → alignment not trusted
OPTION_LETTERS = "ABCDEFGH"


# ── Bubble detection ─────────────────────────────────────────────────────────

def _gray(img: np.ndarray) -> np.ndarray:
    """BGR → darkest channel per pixel (coloured print, e.g. orange bubbles, becomes as dark as
    black ink; pencil and pen are unchanged). Grey images pass through."""
    return img.min(axis=2) if img.ndim == 3 else img


def _ink(gray: np.ndarray) -> np.ndarray:
    """Binary ink mask (ink = 255) that tolerates uneven lighting."""
    return cv2.adaptiveThreshold(cv2.GaussianBlur(gray, (5, 5), 0), 255,
                                 cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 10)


def darkness(gray: np.ndarray) -> np.ndarray:
    """0–1 map of how much darker each pixel is than the local paper (light pencil ≈ 0.5,
    pen ≈ 0.9, paper ≈ 0). Dividing by a closed (marks-removed) background cancels shadows."""
    bg = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (75, 75)))
    return np.clip(1.0 - gray.astype(np.float32) / np.maximum(bg.astype(np.float32), 1.0), 0.0, 1.0)


def _ring_support(ink: np.ndarray, x: float, y: float, r: float) -> float:
    """Share of 36 points around the circle that have an edge/ink pixel within ±2 px of radius r.
    A printed bubble scores high all round; a digit '0' (tall oval) fails at its sides."""
    hits = 0
    for a in np.linspace(0, 2 * np.pi, 36, endpoint=False):
        found = False
        for dr in (-2, -1, 0, 1, 2):
            px, py = int(round(x + (r + dr) * np.cos(a))), int(round(y + (r + dr) * np.sin(a)))
            if 0 <= py < ink.shape[0] and 0 <= px < ink.shape[1] and ink[py, px]:
                found = True
                break
        hits += found
    return hits / 36


def find_bubbles(gray: np.ndarray) -> List[Tuple[float, float, float]]:
    """(cx, cy, r) of every printed bubble. Hough circles find rings even when they are thin,
    broken or have a letter inside; each candidate must then have ink most of the way round."""
    circles = cv2.HoughCircles(cv2.GaussianBlur(gray, (5, 5), 1.2), cv2.HOUGH_GRADIENT, dp=1, minDist=14,
                               param1=120, param2=18, minRadius=7, maxRadius=45)
    if circles is None:
        return []
    # Edges (not an ink threshold) so faint / coloured rings still count
    edges = cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0), 40, 120)
    cands = [(float(x), float(y), float(r)) for x, y, r in circles[0] if _ring_support(edges, x, y, r) >= 0.8]
    if not cands:
        return []

    # Keep the dominant size (drops other round print), then de-duplicate concentric hits
    med = float(np.median([r for _, _, r in cands]))
    cands = sorted((b for b in cands if 0.8 * med <= b[2] <= 1.25 * med), key=lambda b: -b[2])
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


def _split_line(line: list, axis_along: int, k: Optional[int] = None) -> List[list]:
    """Split a line of bubbles into runs with the regular option spacing d. A gap of ~2d
    inside a run means one ring was missed: its position is filled in. Runs longer than k
    keep the k most evenly spaced bubbles (drops a stray circle next to the first option)."""
    if len(line) < 2:
        return [line]
    pos = [b[axis_along] for b in line]
    gaps = np.diff(pos)
    r = float(np.median([b[2] for b in line]))
    small = gaps[gaps < 6 * r]
    d = float(np.median(small)) if len(small) else float(np.median(gaps))
    groups = [[line[0]]]
    for g, b in zip(gaps, line[1:]):
        prev = groups[-1][-1]
        if 0.75 * d <= g <= 1.25 * d:
            groups[-1].append(b)
        elif 1.75 * d <= g <= 2.25 * d and (k is None or len(groups[-1]) < k - 1):
            mid = [(prev[i] + b[i]) / 2 for i in range(3)]               # missed ring in between
            groups[-1] += [tuple(mid), b]
        else:
            groups.append([b])
    if k:
        out = []
        for grp in groups:
            if len(grp) == k + 1:                                        # one stray circle: keep the most regular k
                spans = [np.std(np.diff([x[axis_along] for x in grp[i:i + k]])) for i in range(len(grp) - k + 1)]
                grp = grp[int(np.argmin(spans)): int(np.argmin(spans)) + k]
            out.append(grp)
        groups = out
    return groups


def group_questions(bubbles: list, n_options: Optional[int] = None) -> Tuple[List[list], str]:
    """Bubbles → question groups. Tries options-in-a-row and options-in-a-column and keeps
    the layout whose groups most consistently have the expected option count."""
    if not bubbles:
        return [], "none"
    r = float(np.median([b[2] for b in bubbles]))
    layouts = {
        "horizontal": [g for row in _lines(bubbles, 1, r) for g in _split_line(row, 0, n_options)],
        "vertical": [g for col in _lines(bubbles, 0, r) for g in _split_line(col, 1, n_options)],
    }

    def score(groups):
        sizes = [len(g) for g in groups if len(g) >= 2]
        if not sizes:
            return (0, 0.0), 0
        k = n_options or max(set(sizes), key=sizes.count)          # expected or most common size
        full = sum(s == k for s in sizes)
        return (full, full / len(sizes)), k                         # more complete questions wins

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


def complete_grid(groups: List[list], layout: str, edges: np.ndarray) -> List[list]:
    """Fill in whole questions the circle finder missed (faint print), using the sheet's
    regular spacing: inside each column of questions (band, for vertical options) a gap of
    m × the usual pitch gets m − 1 interpolated questions; at both ends the grid is extended
    one pitch at a time while faint rings are actually present there."""
    if len(groups) < 3:
        return groups
    step_axis = 1 if layout == "horizontal" else 0                 # questions stack along y (or x)
    ordered = reading_order(groups, layout)

    # Split the reading order back into its columns (bands): a jump backwards starts a new one
    lines, cur = [], [ordered[0]]
    for g in ordered[1:]:
        (cur.append(g) if g[0][step_axis] > cur[-1][0][step_axis] else (lines.append(cur), cur := [g]))
    lines.append(cur)

    def shifted(g, d):                                             # group moved d px along the axis
        return [tuple(b[i] + (d if i == step_axis else 0) for i in range(3)) for b in g]

    def present(g):                                                # faint rings really there?
        h, w = edges.shape
        inside = all(0 <= b[0] < w and 0 <= b[1] < h for b in g)
        return inside and np.mean([_ring_support(edges, *b) for b in g]) >= 0.5

    # One pitch for the whole sheet: the typical step between neighbours, ignoring gaps
    steps = np.array([b[0][step_axis] - a[0][step_axis] for l in lines for a, b in zip(l, l[1:])])
    if not len(steps):
        return groups
    # Start from a typical small step, then refine: total distance / total rows spanned
    # (print spacing jitters; averaging over many rows makes multi-row gaps count right)
    pitch = float(np.median(steps[steps <= 1.4 * np.percentile(steps, 25)]))
    for _ in range(3):
        rows = np.maximum(1, np.round(steps / pitch))
        pitch = float(steps.sum() / rows.sum())
    def fill(line):                                                # interpolate gaps of m × pitch
        out = [line[0]]
        for a, b in zip(line, line[1:]):
            m = int(round((b[0][step_axis] - a[0][step_axis]) / pitch))
            for j in range(1, m):
                t = j / m
                out.append([tuple(pa[i] + t * (pb[i] - pa[i]) for i in range(3)) for pa, pb in zip(a, b)])
            out.append(b)
        return out

    def extend(line, lo, hi):                                      # grow both ends one pitch at a time
        line = list(line)
        while len(line) < 200:
            nxt = shifted(line[0], -pitch)
            if not (nxt[0][step_axis] >= lo or present(nxt)):
                break
            line.insert(0, nxt)
        while len(line) < 200:
            nxt = shifted(line[-1], pitch)
            if not (nxt[0][step_axis] <= hi or present(nxt)):
                break
            line.append(nxt)
        return line

    def snap(g):                                                   # move a filled-in group onto its rings
        best, best_score = g, -1.0
        for dy in np.arange(-0.35 * pitch, 0.35 * pitch + 1, 1.0):
            for dx in (-4, -2, 0, 2, 4):
                cand = [(b[0] + dx, b[1] + dy, b[2]) if step_axis == 1 else (b[0] + dy, b[1] + dx, b[2]) for b in g]
                h, w = edges.shape
                if not all(0 <= b[0] < w and 0 <= b[1] < h for b in cand):
                    continue
                score = float(np.mean([_ring_support(edges, *b) for b in cand]))
                if score > best_score:
                    best, best_score = cand, score
        return best

    # Columns share rows (bands share columns): extend every line to the span covered by any
    # line, repeating until stable (one line found faint rings → the others follow)
    detected = {id(g) for l in lines for g in l}
    lines = [fill(l) for l in lines]
    for _ in range(3):
        lo = min(l[0][0][step_axis] for l in lines) - pitch / 2
        hi = max(l[-1][0][step_axis] for l in lines) + pitch / 2
        lines = [extend(l, lo, hi) for l in lines]
    # Interpolated / extended groups are only estimates: snap each onto its faint printed rings
    return [g if id(g) in detected else snap(g) for l in lines for g in l]


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

    # Restore questions whose faint rings were missed, then number the groups:
    # printed labels (VLM) if it gives a clean answer, else reading order
    groups = reading_order(complete_grid(groups, layout, cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0), 40, 120)), layout)
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
    """Warp the student photo onto the blank template frame; returns (aligned image, inliers)."""
    tw, th = size
    tpl = _gray(cv2.resize(blank, (tw, th), interpolation=cv2.INTER_AREA))
    s = tw / photo.shape[1]
    small = cv2.resize(photo, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    img = _gray(small)

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
    border = (255, 255, 255) if small.ndim == 3 else 255
    return cv2.warpPerspective(small, H, (tw, th), borderValue=border), n_in


def read_sheet(photo: np.ndarray, blank: np.ndarray, template: dict) -> dict:
    """→ {"aligned": bool, "inliers": n, "answers": {Q: {"answer", "deltas", "margin"}}}."""
    aligned, inliers = align(photo, blank, template["size"])
    if aligned is None:
        return {"aligned": False, "inliers": inliers, "answers": {}}
    ink = darkness(_gray(aligned))

    # Darkness above the blank's own (printed letters), per bubble
    deltas = [(b, _fill(ink, b["x"], b["y"], b["r"]) - b["base"]) for b in template["bubbles"]]
    # Scans/photos print lighter or darker than the blank on EVERY bubble; most bubbles are
    # empty, so the median delta is this sheet's print offset — remove it before thresholding
    offset = float(np.median([d for _, d in deltas]))
    by_q: Dict[str, list] = {}
    for b, d in deltas:
        by_q.setdefault(b["q"], []).append((b["opt"], d - offset))
    answers = {}
    for q, opts in by_q.items():
        picked = sorted(o for o, d in opts if d >= FILL_DELTA)
        answers[q] = {"answer": ",".join(picked), "deltas": {o: round(d, 3) for o, d in opts},
                      "margin": round(min(abs(d - FILL_DELTA) for _, d in opts), 3)}
    return {"aligned": True, "inliers": inliers, "offset": round(offset, 3), "answers": answers}
