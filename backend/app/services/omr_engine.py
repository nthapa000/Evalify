# omr_engine.py — OpenCV bubble detector for MCQ OMR sheets (no template needed).
#
# Steps: threshold → find round contours → group into rows → split rows into
# questions (handles 2-column sheets) → a bubble is filled if enough of it is dark.
# Returns every filled option per question, e.g. {"Q1": "A", "Q2": "A,C"}.

from __future__ import annotations

import os
from typing import Dict, List, Optional

import cv2
import numpy as np

CHOICES = "ABCDE"


class OMREngine:
    """Detects filled bubbles on a scanned or photographed OMR sheet."""

    # Bubble shape limits (tuned for ~200–300 DPI scans)
    BUBBLE_MIN_W, BUBBLE_MAX_W = 12, 120
    ASPECT_MIN, ASPECT_MAX = 0.60, 1.40
    CIRCULARITY_MIN = 0.60
    MIN_ROW_BUBBLES = 4          # fewer bubbles in a row = noise
    ROW_TOLERANCE = 45           # px: bubbles within this y-distance share a row
    COL_GAP_FACTOR = 2.5         # x-gap this many times the median = new column

    # Fill thresholds: empty bubbles measure ~0.20–0.24, filled ~0.33–0.46
    FILLED_RATIO_THRESHOLD = 0.28
    LIGHT_FILL_FLOOR = 0.16      # light pencil: accept if ≥ this and clearly dominant
    DOMINANCE_FACTOR = 1.8

    def __init__(self, debug_dir: Optional[str] = None):
        self.debug_dir = debug_dir
        if debug_dir:
            os.makedirs(debug_dir, exist_ok=True)

    def process_image(self, image_path: str, mcq_count: int) -> Dict[str, str]:
        """Return {"Q1": "A", "Q2": "A,C", ...} for up to mcq_count questions."""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"OMR: cannot open image at '{image_path}'")
        return {q: r["answer"] for q, r in self.detect(img, mcq_count).items() if r["answer"]}

    def detect(self, img: np.ndarray, mcq_count: int) -> Dict[str, dict]:
        """Per question: answer + raw fill ratios + margin (gap to the decision threshold)."""
        # Binarise (ink = white) and find bubble-shaped contours
        thresh = cv2.adaptiveThreshold(cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (5, 5), 0),
                                       255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        bubbles = self._find_bubbles(thresh)
        if not bubbles:
            raise ValueError("OMR: no bubble-like contours found (need ~150 DPI or better).")

        # Drop small outliers (well below the median bubble width)
        median_w = sorted(cv2.boundingRect(c)[2] for c in bubbles)[len(bubbles) // 2]
        bubbles = [c for c in bubbles if cv2.boundingRect(c)[2] >= max(self.BUBBLE_MIN_W, median_w * 0.6)]

        # Rows → question groups (left column first, then right) → graded
        groups = self._question_groups(self._rows(bubbles))
        results = {f"Q{i + 1}": self._grade(thresh, g) for i, g in enumerate(groups[:mcq_count]) if g}

        if self.debug_dir:
            self._save_debug(img, thresh, groups, results)
        return results

    def _find_bubbles(self, thresh: np.ndarray) -> List[np.ndarray]:
        """Outer contours that are bubble-sized, roughly square and roughly round."""
        out = []
        for c in cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
            x, y, w, h = cv2.boundingRect(c)
            perim = cv2.arcLength(c, True)
            circ = 4 * np.pi * cv2.contourArea(c) / (perim * perim) if perim else 0
            if (self.BUBBLE_MIN_W <= w <= self.BUBBLE_MAX_W and self.BUBBLE_MIN_W <= h <= self.BUBBLE_MAX_W
                    and self.ASPECT_MIN <= w / h <= self.ASPECT_MAX and circ >= self.CIRCULARITY_MIN):
                out.append(c)
        return out

    def _rows(self, bubbles: List[np.ndarray]) -> List[List[np.ndarray]]:
        """Cluster bubbles into rows by y-centre, each row sorted left → right."""
        rows, row, row_y = [], [], None
        for c in sorted(bubbles, key=lambda c: cv2.boundingRect(c)[1]):
            _, y, _, h = cv2.boundingRect(c)
            cy = y + h / 2
            if row_y is None or abs(cy - row_y) <= self.ROW_TOLERANCE:
                row.append(c)
                row_y = cy if row_y is None else (row_y + cy) / 2
            else:
                rows.append(row)
                row, row_y = [c], cy
        if row:
            rows.append(row)
        return [sorted(r, key=lambda c: cv2.boundingRect(c)[0]) for r in rows]

    def _question_groups(self, rows: List[List[np.ndarray]]) -> List[List[np.ndarray]]:
        """Split each row at large x-gaps (multi-column sheets); number columns top-to-bottom."""
        columns: Dict[int, list] = {}
        for row in rows:
            if len(row) < self.MIN_ROW_BUBBLES:
                continue
            # Split where the gap between bubble centres is much larger than usual
            xs = [cv2.boundingRect(c)[0] + cv2.boundingRect(c)[2] / 2 for c in row]
            gaps = [b - a for a, b in zip(xs, xs[1:])]
            cut = sorted(gaps)[len(gaps) // 2] * self.COL_GAP_FACTOR if len(row) > 5 else float("inf")
            groups = [[row[0]]]
            for gap, c in zip(gaps, row[1:]):
                groups.append([c]) if gap >= cut else groups[-1].append(c)
            for col, g in enumerate(groups):
                columns.setdefault(col, []).append(g[:5])
        return [g for col in sorted(columns) for g in columns[col]]

    def _grade(self, thresh: np.ndarray, group: List[np.ndarray]) -> dict:
        """Fill ratio of each bubble → filled options, plus a margin for TA routing."""
        # Fraction of each bubble's area that is ink
        ratios = []
        for c in group[:5]:
            mask = np.zeros(thresh.shape, np.uint8)
            cv2.drawContours(mask, [c], -1, 255, cv2.FILLED)
            area = cv2.contourArea(c)
            ratios.append(cv2.countNonZero(cv2.bitwise_and(thresh, thresh, mask=mask)) / area if area else 0.0)

        # Strict threshold first; then the light-pencil fallback
        filled = [CHOICES[i] for i, r in enumerate(ratios) if r >= self.FILLED_RATIO_THRESHOLD]
        if not filled:
            mean = sum(ratios) / len(ratios)
            filled = [CHOICES[i] for i, r in enumerate(ratios)
                      if r >= self.LIGHT_FILL_FLOOR and r >= mean * self.DOMINANCE_FACTOR]

        # Margin = how far the closest bubble is from the threshold (small = ambiguous)
        margin = min(abs(r - self.FILLED_RATIO_THRESHOLD) for r in ratios) if ratios else 0.0
        return {"answer": ",".join(sorted(filled)), "ratios": [round(r, 3) for r in ratios],
                "margin": round(margin, 3)}

    def _save_debug(self, img, thresh, groups, results):
        """Write an annotated image (green = detected fill) and the threshold mask."""
        dbg = img.copy()
        for qi, group in enumerate(groups):
            picked = set(results.get(f"Q{qi + 1}", {}).get("answer", "").split(","))
            for ci, c in enumerate(group[:5]):
                x, y, w, h = cv2.boundingRect(c)
                color = (0, 220, 0) if CHOICES[ci] in picked else (180, 180, 180)
                cv2.rectangle(dbg, (x, y), (x + w, y + h), color, 2)
                cv2.putText(dbg, f"Q{qi + 1}{CHOICES[ci]}", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        cv2.imwrite(os.path.join(self.debug_dir, "02_debug.png"), dbg)
        cv2.imwrite(os.path.join(self.debug_dir, "03_thresh.png"), thresh)
