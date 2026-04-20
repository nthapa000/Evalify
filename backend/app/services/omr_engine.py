# omr_engine.py — OpenCV bubble-sheet detector for MCQ OMR answer sheets.
#
# Expected sheet format:
#   • One row per question, four bubbles per row (A B C D left-to-right).
#   • Student fills exactly one bubble with dark ink/pencil.
#   • Sheet should be reasonably straight (within ~10° tilt is fine).
#
# Algorithm:
#   1. Grayscale → Gaussian blur → adaptive threshold (isolates dark marks).
#   2. Find all contours, filter to roughly circular shapes in bubble size range.
#   3. Sort bubbles into rows using Y-coordinate clustering.
#   4. Within each row sort by X (gives A, B, C, D order).
#   5. The bubble with the highest filled-pixel count in each row is the answer.

from __future__ import annotations
import os
from typing import Dict, List, Tuple, Optional

import cv2
import numpy as np


class OMREngine:
    """Detects filled bubbles on a scanned MCQ OMR sheet using OpenCV."""

    # Tunable constants for bubble detection (pixels, assuming ~200-300 DPI scans)
    BUBBLE_MIN_W    = 12    # minimum bubble width
    BUBBLE_MAX_W    = 120   # maximum bubble width
    ASPECT_MIN      = 0.60  # min width/height ratio (allow slight ovals)
    ASPECT_MAX      = 1.40  # max width/height ratio
    CIRCULARITY_MIN = 0.60  # 4π·area/perimeter² — filters out text, lines, rectangles
    MIN_ROW_BUBBLES = 4     # rows with fewer bubbles than this are noise (skip them)
    ROW_TOLERANCE   = 20    # pixels: y-diff within which two bubbles share a row
    MIN_FILL_RATIO  = 0.10  # absolute minimum fill ratio to be considered
    DOMINANCE_FACTOR = 1.5  # filled bubble must be ≥1.5× the avg of all OTHER bubbles
    COL_GAP_FACTOR  = 2.5   # X gap factor to detect multi-column question layout

    def __init__(self, debug_dir: Optional[str] = None):
        # Save intermediate images here when debugging; None = no debug output
        self.debug_dir = debug_dir
        if debug_dir:
            os.makedirs(debug_dir, exist_ok=True)

    # ── Public API ────────────────────────────────────────────────────────────

    def process_image(self, image_path: str, mcq_count: int) -> Dict[str, str]:
        """
        Detect answers for `mcq_count` questions from an OMR sheet image.
        Returns {"Q1": "A", "Q2": "C", ...}.  Missing questions are omitted.
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"OMR: cannot open image at '{image_path}'")

        thresh = self._preprocess(img)
        bubbles = self._find_bubble_contours(thresh)

        if len(bubbles) == 0:
            raise ValueError(
                "OMR: no bubble-like contours found. "
                "Check image quality or adjust BUBBLE_MIN_W / BUBBLE_MAX_W."
            )

        # Adaptively filter to the dominant bubble size.
        # OMR answer circles are large (e.g. 40px); stray text contours are small (15-20px).
        # Keep only contours whose width is ≥ 60% of the median width.
        widths = sorted([cv2.boundingRect(c)[2] for c in bubbles])
        median_w = widths[len(widths) // 2]
        min_w = max(self.BUBBLE_MIN_W, int(median_w * 0.6))
        bubbles = [c for c in bubbles if cv2.boundingRect(c)[2] >= min_w]

        if len(bubbles) == 0:
            return {}

        rows = self._cluster_into_rows(bubbles)
        results = self._grade_rows(thresh, rows, mcq_count)

        if self.debug_dir:
            self._save_debug(img, thresh, bubbles, rows, results)

        return results

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _preprocess(self, img: np.ndarray) -> np.ndarray:
        """Convert to grayscale, blur, then adaptive-threshold to binary."""
        gray    = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        # THRESH_BINARY_INV makes the filled dark ink appear as white pixels.
        thresh  = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=11, C=2
        )
        if self.debug_dir:
            cv2.imwrite(os.path.join(self.debug_dir, "01_thresh.png"), thresh)
        return thresh

    def _find_bubble_contours(self, thresh: np.ndarray) -> List[np.ndarray]:
        """Return contours that look like bubbles (roughly square/circular, right size)."""
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        bubbles = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w < self.BUBBLE_MIN_W or w > self.BUBBLE_MAX_W:
                continue
            if h < self.BUBBLE_MIN_W or h > self.BUBBLE_MAX_W:
                continue
            ar = w / float(h)
            if not (self.ASPECT_MIN <= ar <= self.ASPECT_MAX):
                continue
            # Circularity check: 4π·area/perimeter² ≈ 1.0 for circles; filters text/noise
            area = cv2.contourArea(cnt)
            perim = cv2.arcLength(cnt, True)
            circularity = (4 * np.pi * area / (perim * perim)) if perim > 0 else 0
            if circularity < self.CIRCULARITY_MIN:
                continue
            bubbles.append(cnt)
        return bubbles

    def _cluster_into_rows(self, bubbles: List[np.ndarray]) -> List[List[np.ndarray]]:
        """
        Group bubbles that share approximately the same Y centre into rows.
        Rows are returned sorted top-to-bottom; bubbles within each row are
        sorted left-to-right (giving A, B, C, D order).
        """
        # Sort all bubbles top-to-bottom first
        bubbles_sorted = sorted(bubbles, key=lambda c: cv2.boundingRect(c)[1])

        rows: List[List[np.ndarray]] = []
        current_row: List[np.ndarray] = []
        current_y: Optional[float] = None

        for cnt in bubbles_sorted:
            _, y, _, h = cv2.boundingRect(cnt)
            cy = y + h / 2  # vertical centre of this bubble

            if current_y is None or abs(cy - current_y) <= self.ROW_TOLERANCE:
                current_row.append(cnt)
                # Update the representative Y for this row (running mean)
                current_y = cy if current_y is None else (current_y + cy) / 2
            else:
                if current_row:
                    rows.append(self._sort_row_lr(current_row))
                current_row = [cnt]
                current_y = cy

        if current_row:
            rows.append(self._sort_row_lr(current_row))

        return rows

    @staticmethod
    def _sort_row_lr(row: List[np.ndarray]) -> List[np.ndarray]:
        """Sort bubbles in a row left-to-right by their X coordinate."""
        return sorted(row, key=lambda c: cv2.boundingRect(c)[0])

    def _split_row_into_questions(self, row: List[np.ndarray]) -> List[List[np.ndarray]]:
        """
        A sheet may place multiple question groups on the same horizontal band
        (e.g. Q1-Q5 left column, Q6-Q10 right column).  When a row has more
        than 4 bubbles we split on the largest X gap so each group has ≤4 bubbles.
        """
        if len(row) <= 5:
            return [row[:5]]

        # X-centres of all bubbles already sorted L→R
        xs = [cv2.boundingRect(c)[0] + cv2.boundingRect(c)[2] / 2 for c in row]
        gaps = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]

        if not gaps:
            return [row[:4]]

        median_gap = sorted(gaps)[len(gaps) // 2]
        threshold  = median_gap * self.COL_GAP_FACTOR

        groups: List[List[np.ndarray]] = [[row[0]]]
        for i, gap in enumerate(gaps):
            if gap >= threshold:
                groups.append([row[i + 1]])
            else:
                groups[-1].append(row[i + 1])

        return [g[:5] for g in groups]

    def _grade_rows(
        self, thresh: np.ndarray,
        rows: List[List[np.ndarray]],
        mcq_count: int
    ) -> Dict[str, str]:
        """
        For each question row pick the bubble with the most filled pixels.
        Handles multi-column sheets by splitting rows with > 4 bubbles on the
        largest horizontal gap.
        """
        choices = ["A", "B", "C", "D", "E"]
        results: Dict[str, str] = {}

        # Collect all (col_index, group) pairs across rows, skipping noise rows.
        # Then re-order column-first so left-column questions (Q1…Q5) are numbered
        # before right-column questions (Q6…Q10), matching the physical sheet layout.
        col_groups: Dict[int, list] = {}
        for row in rows:
            if len(row) < self.MIN_ROW_BUBBLES:
                continue
            for col_idx, group in enumerate(self._split_row_into_questions(row)):
                col_groups.setdefault(col_idx, []).append(group)

        ordered_groups = []
        for col_idx in sorted(col_groups):
            ordered_groups.extend(col_groups[col_idx])

        q_idx = 0
        for group in ordered_groups:
            if q_idx >= mcq_count:
                break
            if not group:
                continue

            # First pass: measure fill ratio for every bubble in the group
            ratios = []
            for cnt in group[:5]:
                mask = np.zeros(thresh.shape, dtype=np.uint8)
                cv2.drawContours(mask, [cnt], -1, 255, cv2.FILLED)
                filled = cv2.countNonZero(cv2.bitwise_and(thresh, thresh, mask=mask))
                area   = cv2.contourArea(cnt)
                ratios.append(filled / area if area > 0 else 0)

            # Find the best candidate (highest ratio meeting absolute minimum)
            best_idx   = -1
            best_ratio = 0
            for i, ratio in enumerate(ratios):
                if ratio >= self.MIN_FILL_RATIO and ratio > best_ratio:
                    best_ratio = ratio
                    best_idx   = i

            # Accept only if the best bubble dominates all the others
            # (compare against average of the remaining bubbles, not the whole row)
            best_choice = None
            if best_idx >= 0:
                rest = [r for i, r in enumerate(ratios) if i != best_idx]
                rest_avg = sum(rest) / len(rest) if rest else 0
                if best_ratio >= rest_avg * self.DOMINANCE_FACTOR:
                    best_choice = choices[best_idx]

            if best_choice:
                results[f"Q{q_idx + 1}"] = best_choice
            q_idx += 1

            if q_idx >= mcq_count:
                break

        return results

    def _save_debug(self, orig, thresh, bubbles, rows, results):
        """Draw detected bubbles + answers on a copy of the original image for inspection."""
        debug_img = orig.copy()
        choices   = ["A", "B", "C", "D", "E"]

        q_idx = 0
        for row in rows:
            for group in self._split_row_into_questions(row):
                q_id = f"Q{q_idx + 1}"
                for col_idx, cnt in enumerate(group):
                    x, y, w, h = cv2.boundingRect(cnt)
                    col   = choices[col_idx] if col_idx < 4 else "?"
                    color = (0, 255, 0) if results.get(q_id) == col else (200, 200, 200)
                    cv2.rectangle(debug_img, (x, y), (x + w, y + h), color, 2)
                q_idx += 1

        cv2.imwrite(os.path.join(self.debug_dir, "02_debug.png"), debug_img)
        cv2.imwrite(os.path.join(self.debug_dir, "03_thresh.png"), thresh)
