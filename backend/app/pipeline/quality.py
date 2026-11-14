# quality.py — ingest + quality gate for phone photos of answer pages.
#
# Steps: EXIF rotation → page perspective correction → deskew → resize long side
# to ~2000 px. Then blur / glare / darkness / contrast checks decide whether the
# page is usable or the student should re-upload it. The colour image is kept
# for the VLM; binarisation is left to OMR only.

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageOps

# Thresholds (tune on the dev split; values below are conservative defaults)
TARGET_LONG_SIDE = int(os.environ.get("EVALIFY_TARGET_LONG_SIDE", "2000"))
MIN_LONG_SIDE = 1000           # smaller photos are too coarse for handwriting
BLUR_MIN = 60.0                # variance of Laplacian at 1000 px; below = blurry
GLARE_MAX = 0.04               # max fraction of blown-out (white, unsaturated) pixels
DARK_MIN = 70.0                # min mean brightness (0–255)
CONTRAST_MIN = 25.0            # min grey-level std


@dataclass
class QualityReport:
    """What the gate measured and whether the page passes."""
    ok: bool = True
    reasons: List[str] = field(default_factory=list)
    blur: float = 0.0
    glare: float = 0.0
    brightness: float = 0.0
    contrast: float = 0.0
    deskew_deg: float = 0.0
    page_found: bool = False
    size: Tuple[int, int] = (0, 0)


def load(path: str) -> Image.Image:
    """Open an image with its EXIF orientation applied, as RGB."""
    return ImageOps.exif_transpose(Image.open(path)).convert("RGB")


def _order_corners(pts: np.ndarray) -> np.ndarray:
    """4 points → top-left, top-right, bottom-right, bottom-left."""
    s, d = pts.sum(1), np.diff(pts, axis=1).ravel()
    return np.array([pts[s.argmin()], pts[d.argmin()], pts[s.argmax()], pts[d.argmax()]], np.float32)


def find_page(bgr: np.ndarray) -> Optional[np.ndarray]:
    """Largest 4-corner contour covering ≥ 40 % of the photo (the paper), else None."""
    small = 800 / max(bgr.shape[:2])
    img = cv2.resize(bgr, None, fx=small, fy=small)
    edges = cv2.dilate(cv2.Canny(cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (5, 5), 0), 50, 150),
                       np.ones((3, 3), np.uint8))
    for c in sorted(cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0],
                    key=cv2.contourArea, reverse=True)[:5]:
        approx = cv2.approxPolyDP(c, 0.02 * cv2.arcLength(c, True), True)
        if len(approx) == 4 and cv2.contourArea(approx) >= 0.4 * img.shape[0] * img.shape[1]:
            return _order_corners(approx.reshape(4, 2) / small)
    return None


def warp_page(bgr: np.ndarray, corners: np.ndarray) -> np.ndarray:
    """Perspective-correct the page to a flat rectangle."""
    tl, tr, br, bl = corners
    w = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    h = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
    m = cv2.getPerspectiveTransform(corners, np.array([[0, 0], [w, 0], [w, h], [0, h]], np.float32))
    return cv2.warpPerspective(bgr, m, (w, h))


def skew_angle(gray: np.ndarray) -> float:
    """Dominant text-line angle in degrees from near-horizontal Hough lines (0 if unsure)."""
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 360, threshold=150,
                            minLineLength=gray.shape[1] // 4, maxLineGap=20)
    if lines is None:
        return 0.0
    angles = [np.degrees(np.arctan2(y2 - y1, x2 - x1)) for x1, y1, x2, y2 in lines[:, 0]]
    angles = [a for a in angles if abs(a) < 15]
    return float(np.median(angles)) if len(angles) >= 3 else 0.0


def rotate(bgr: np.ndarray, deg: float) -> np.ndarray:
    """Rotate about the centre, padding with white."""
    h, w = bgr.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), deg, 1.0)
    return cv2.warpAffine(bgr, m, (w, h), flags=cv2.INTER_CUBIC, borderValue=(255, 255, 255))


def measure(bgr: np.ndarray, rep: QualityReport) -> None:
    """Fill blur / glare / brightness / contrast and the pass/fail reasons."""
    # Measure at a fixed scale so blur scores are comparable across phones
    scale = 1000 / max(bgr.shape[:2])
    gray = cv2.cvtColor(cv2.resize(bgr, None, fx=scale, fy=scale), cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(cv2.resize(bgr, None, fx=scale, fy=scale), cv2.COLOR_BGR2HSV)
    rep.blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    # Glare = blown-out patches clearly brighter than the paper; a scan's paper is
    # already pure white, so glare is only measured on photos (background < 240)
    bg = float(np.median(gray))
    rep.glare = 0.0 if bg >= 240 else float(((hsv[..., 2] >= max(250, bg + 15)) & (hsv[..., 1] < 25)).mean())
    rep.brightness, rep.contrast = float(gray.mean()), float(gray.std())

    # Each failed check is a reason the student is asked to re-upload
    checks = [(max(rep.size) >= MIN_LONG_SIDE, "resolution too low"),
              (rep.blur >= BLUR_MIN, "image is blurry"),
              (rep.glare <= GLARE_MAX, "glare / reflection on the page"),
              (rep.brightness >= DARK_MIN, "image too dark"),
              (rep.contrast >= CONTRAST_MIN, "very low contrast")]
    rep.reasons = [msg for good, msg in checks if not good]
    rep.ok = not rep.reasons


def prepare(path: str, out_path: Optional[str] = None) -> Tuple[Image.Image, QualityReport]:
    """Full ingest for one page: returns the cleaned colour image and its quality report."""
    bgr = cv2.cvtColor(np.array(load(path)), cv2.COLOR_RGB2BGR)
    rep = QualityReport()
    rep.size = (bgr.shape[1], bgr.shape[0])

    # Flatten the page if the photo shows its edges
    corners = find_page(bgr)
    if corners is not None:
        bgr, rep.page_found = warp_page(bgr, corners), True

    # Straighten small rotations (0.5°–15°)
    angle = skew_angle(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY))
    if 0.5 <= abs(angle) <= 15:
        bgr, rep.deskew_deg = rotate(bgr, angle), round(angle, 2)

    # Quality is judged on the full-resolution page, before downscaling
    measure(bgr, rep)

    # Cap the long side (VLM token budget); never upscale
    s = TARGET_LONG_SIDE / max(bgr.shape[:2])
    if s < 1:
        bgr = cv2.resize(bgr, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)

    img = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    if out_path:
        img.save(out_path)
    return img, rep
