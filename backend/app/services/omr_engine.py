# omr_engine.py — OpenCV bubble-sheet detector for MCQ OMR answer sheets.
#
# Single heuristic mode — works on any OMR sheet without a template.
#
# Algorithm:
#   1. Grayscale → Gaussian blur → adaptive threshold.
#   2. Find all contours, filter to roughly circular shapes in bubble size range.
#   3. Sort bubbles into rows using Y-coordinate clustering.
#   4. Within each row sort by X (gives A, B, C, D order).
#   5. For each question detect filled bubbles using a hybrid strategy:
#        a. Primary:  filled_px / contour_area >= FILLED_RATIO_THRESHOLD
#        b. Fallback: if no bubble clears the primary threshold but one
#                     clearly dominates (ratio >= mean*DOMINANCE_FACTOR and
#                     ratio >= LIGHT_FILL_FLOOR), accept that one bubble.
#      This keeps strict detection for normal fills while recovering lightly
#      filled or pencil-shaded bubbles on low-contrast scans.
#
# Multiple-answer support:
#   Returns all filled bubbles per question as a comma-joined sorted string
#   e.g. "A" for single fill, "A,C" for double fill.
#   Grading does an exact-set comparison — no partial credit, no over-fill.

from __future__ import annotations
import os
from typing import Dict, List, Optional

import cv2
import numpy as np


class OMREngine:
    """Detects filled bubbles on a scanned MCQ OMR sheet using OpenCV."""

    # ── Bubble detection constants (tuned for ~200-300 DPI scans) ────────────
    BUBBLE_MIN_W      = 12    # minimum bubble width (px)
    BUBBLE_MAX_W      = 120   # maximum bubble width (px)
    ASPECT_MIN        = 0.60  # min width/height ratio (allow slight ovals)
    ASPECT_MAX        = 1.40  # max width/height ratio
    CIRCULARITY_MIN   = 0.60  # 4π·area/perimeter² ≈ 1.0 for circles
    MIN_ROW_BUBBLES   = 4     # rows with fewer bubbles are noise → skip
    ROW_TOLERANCE     = 45    # px: y-diff within which bubbles share a row
    COL_GAP_FACTOR    = 2.5   # X-gap multiplier to detect multi-column layout

    # ── Fill detection ────────────────────────────────────────────────────────
    # Primary threshold — empirical values from real scans:
    #   unfilled bubbles:  filled_px/contour_area ≈ 0.20–0.24
    #   filled bubbles:    filled_px/contour_area ≈ 0.33–0.46
    # 0.28 sits cleanly between the two clusters.
    FILLED_RATIO_THRESHOLD = 0.28

    # Fallback for light pencil / low-contrast scans:
    # If no bubble in a question clears 0.28, but one bubble has ratio ≥ 0.16
    # AND is ≥ DOMINANCE_FACTOR times the per-question mean, accept it.
    LIGHT_FILL_FLOOR   = 0.16
    DOMINANCE_FACTOR   = 1.8

    def __init__(self, debug_dir: Optional[str] = None):
        self.debug_dir = debug_dir
        if debug_dir:
            os.makedirs(debug_dir, exist_ok=True)

    # ── Public API ────────────────────────────────────────────────────────────

    def process_image(self, image_path: str, mcq_count: int) -> Dict[str, str]:
        """
        Detect filled bubbles for `mcq_count` questions.

        Returns {"Q1": "A", "Q2": "A,C", ...} where the value is a
        comma-joined sorted string of all filled option letters.
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"OMR: cannot open image at '{image_path}'")
        return self._evaluate_heuristic(img, mcq_count)

    # ── Heuristic evaluation ──────────────────────────────────────────────────

    def _evaluate_heuristic(self, img: np.ndarray, mcq_count: int) -> Dict[str, str]:
        thresh  = self._preprocess(img)
        bubbles = self._find_bubble_contours(thresh)

        if not bubbles:
            raise ValueError(
                "OMR: no bubble-like contours found. "
                "Check image quality (minimum ~150 DPI recommended)."
            )

        # Filter out small outliers: keep only bubbles near the median width
        widths   = sorted([cv2.boundingRect(c)[2] for c in bubbles])
        median_w = widths[len(widths) // 2]
        min_w    = max(self.BUBBLE_MIN_W, int(median_w * 0.6))
        bubbles  = [c for c in bubbles if cv2.boundingRect(c)[2] >= min_w]

        if not bubbles:
            return {}

        rows           = self._cluster_into_rows(bubbles)
        ordered_groups = self._order_question_groups(rows, mcq_count)
        results        = self._grade_groups(thresh, ordered_groups, mcq_count)

        if self.debug_dir:
            self._save_debug(img, thresh, bubbles, rows, results)

        return results

    # ── Contour detection ─────────────────────────────────────────────────────

    def _preprocess(self, img: np.ndarray) -> np.ndarray:
        gray    = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh  = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=11, C=2
        )
        return thresh

    def _find_bubble_contours(self, thresh: np.ndarray) -> List[np.ndarray]:
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        bubbles = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if not (self.BUBBLE_MIN_W <= w <= self.BUBBLE_MAX_W):
                continue
            if not (self.BUBBLE_MIN_W <= h <= self.BUBBLE_MAX_W):
                continue
            if not (self.ASPECT_MIN <= w / float(h) <= self.ASPECT_MAX):
                continue
            area  = cv2.contourArea(cnt)
            perim = cv2.arcLength(cnt, True)
            circ  = (4 * np.pi * area / (perim * perim)) if perim > 0 else 0
            if circ < self.CIRCULARITY_MIN:
                continue
            bubbles.append(cnt)
        return bubbles

    # ── Row clustering ────────────────────────────────────────────────────────

    def _cluster_into_rows(self, bubbles: List[np.ndarray]) -> List[List[np.ndarray]]:
        bubbles_sorted = sorted(bubbles, key=lambda c: cv2.boundingRect(c)[1])
        rows: List[List[np.ndarray]] = []
        current_row: List[np.ndarray] = []
        current_y: Optional[float] = None

        for cnt in bubbles_sorted:
            _, y, _, h = cv2.boundingRect(cnt)
            cy = y + h / 2
            if current_y is None or abs(cy - current_y) <= self.ROW_TOLERANCE:
                current_row.append(cnt)
                current_y = cy if current_y is None else (current_y + cy) / 2
            else:
                if current_row:
                    rows.append(self._sort_row_lr(current_row))
                current_row = [cnt]
                current_y   = cy

        if current_row:
            rows.append(self._sort_row_lr(current_row))
        return rows

    @staticmethod
    def _sort_row_lr(row: List[np.ndarray]) -> List[np.ndarray]:
        return sorted(row, key=lambda c: cv2.boundingRect(c)[0])

    def _split_row_into_questions(self, row: List[np.ndarray]) -> List[List[np.ndarray]]:
        """Split a row with > 5 bubbles on the largest X gap (multi-column sheets)."""
        if len(row) <= 5:
            return [row[:5]]

        xs    = [cv2.boundingRect(c)[0] + cv2.boundingRect(c)[2] / 2 for c in row]
        gaps  = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
        if not gaps:
            return [row[:5]]

        median_gap = sorted(gaps)[len(gaps) // 2]
        threshold  = median_gap * self.COL_GAP_FACTOR
        groups: List[List[np.ndarray]] = [[row[0]]]
        for i, gap in enumerate(gaps):
            if gap >= threshold:
                groups.append([row[i + 1]])
            else:
                groups[-1].append(row[i + 1])
        return [g[:5] for g in groups]

    def _order_question_groups(
        self, rows: List[List[np.ndarray]], mcq_count: int
    ) -> List[List[np.ndarray]]:
        """
        Collect question groups in column-first order so a 2-column sheet
        (Q1–Q5 left, Q6–Q10 right) numbers the left column first.
        """
        col_groups: Dict[int, list] = {}
        for row in rows:
            if len(row) < self.MIN_ROW_BUBBLES:
                continue
            for col_idx, group in enumerate(self._split_row_into_questions(row)):
                col_groups.setdefault(col_idx, []).append(group)

        ordered: List[List[np.ndarray]] = []
        for col_idx in sorted(col_groups):
            ordered.extend(col_groups[col_idx])
        return ordered

    # ── Grading ───────────────────────────────────────────────────────────────

    def _grade_groups(
        self,
        thresh: np.ndarray,
        ordered_groups: List[List[np.ndarray]],
        mcq_count: int,
    ) -> Dict[str, str]:
        """
        For each question group detect ALL filled bubbles using a hybrid strategy:

          1. Primary:  ratio >= FILLED_RATIO_THRESHOLD (0.28) — strict, works on
                       good-quality pen/pencil fills.
          2. Fallback: if nothing clears the primary threshold but one bubble has
                       ratio >= LIGHT_FILL_FLOOR (0.16) AND ratio >= per-question
                       mean * DOMINANCE_FACTOR (1.8), accept that bubble.  Handles
                       very light pencil marks and low-contrast scans.

        ratio = filled_px_inside_contour / contour_area (not bounding box).
        """
        choices = ["A", "B", "C", "D", "E"]
        results: Dict[str, str] = {}

        for q_idx, group in enumerate(ordered_groups):
            if q_idx >= mcq_count:
                break
            if not group:
                continue

            ratios = []
            for cnt in group[:5]:
                mask   = np.zeros(thresh.shape, dtype=np.uint8)
                cv2.drawContours(mask, [cnt], -1, 255, cv2.FILLED)
                filled = cv2.countNonZero(cv2.bitwise_and(thresh, thresh, mask=mask))
                area   = cv2.contourArea(cnt)
                ratios.append(filled / area if area > 0 else 0.0)

            # Primary: strict absolute threshold
            filled_opts = sorted([
                choices[i] for i, r in enumerate(ratios)
                if i < len(choices) and r >= self.FILLED_RATIO_THRESHOLD
            ])

            # Fallback: dominance-based for light fills
            if not filled_opts:
                mean_r = sum(ratios) / len(ratios) if ratios else 0.0
                filled_opts = sorted([
                    choices[i] for i, r in enumerate(ratios)
                    if i < len(choices)
                    and r >= self.LIGHT_FILL_FLOOR
                    and r >= mean_r * self.DOMINANCE_FACTOR
                ])

            if filled_opts:
                results[f"Q{q_idx + 1}"] = ",".join(filled_opts)

        return results

    # ── Debug output ──────────────────────────────────────────────────────────

    def _save_debug(self, orig, thresh, bubbles, rows, results):
        debug_img = orig.copy()
        choices   = ["A", "B", "C", "D", "E"]
        ordered   = self._order_question_groups(rows, len(results))

        for q_idx, group in enumerate(ordered):
            q_id          = f"Q{q_idx + 1}"
            detected_opts = set(results.get(q_id, "").split(","))
            for col_idx, cnt in enumerate(group[:5]):
                x, y, w, h = cv2.boundingRect(cnt)
                label = choices[col_idx] if col_idx < 5 else "?"
                color = (0, 220, 0) if label in detected_opts else (180, 180, 180)
                cv2.rectangle(debug_img, (x, y), (x + w, y + h), color, 2)
                cv2.putText(debug_img, f"{q_id}{label}", (x, y - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        cv2.imwrite(os.path.join(self.debug_dir, "02_debug.png"), debug_img)
        cv2.imwrite(os.path.join(self.debug_dir, "03_thresh.png"), thresh)
