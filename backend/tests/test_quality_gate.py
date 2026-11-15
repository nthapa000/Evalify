# test_quality_gate.py — the upload gate must accept good phone photos and reject only unusable ones.

from pathlib import Path

import cv2
import numpy as np
import pytest

from app.pipeline import quality

PHOTOS = Path(__file__).resolve().parents[2] / "eval" / "test_papers" / "photos"
# The 9 good photos the old gate rejected (glare / blur) + 3 ordinary ones
NAMES = ["2A_s05_p1", "2B_s02_p1", "2B_s04_p1", "2B_s05_p1", "mcq_s02_p1", "mcq_s05_p1", "mcq_s09_p1",
         "mcq_s12_p1", "mcq_s15_p1", "2A_s01_p1", "2C_s02_p1", "omr_L2_s01_p1"]
pytestmark = pytest.mark.skipif(not PHOTOS.exists(), reason="own test photos not available")


@pytest.fixture(scope="module")
def photos(tmp_path_factory):
    """Downscaled copies (1400 px long side; the gate measures at 1000 px) so the tests stay fast."""
    out = {}
    d = tmp_path_factory.mktemp("photos")
    for n in NAMES:
        bgr = cv2.cvtColor(np.array(quality.load(str(PHOTOS / f"{n}.jpg"))), cv2.COLOR_RGB2BGR)
        s = 1400 / max(bgr.shape[:2])
        out[n] = cv2.resize(bgr, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(d / f"{n}.png"), out[n])
    return d, out


def _hotspot(bgr, frac):
    """A soft, white, blown-out ellipse covering about `frac` of the page, over the writing."""
    h, w = bgr.shape[:2]
    a = int(np.sqrt(frac * h * w / np.pi * 1.6))
    mask = np.zeros((h, w), np.float32)
    cv2.ellipse(mask, (w // 2, h // 2), (a, int(a / 1.6)), 0, 0, 360, 1, -1)
    mask = cv2.GaussianBlur(mask, (0, 0), a / 6)[..., None]
    return (bgr * (1 - mask) + 255 * mask).clip(0, 255).astype(np.uint8)


# Why: the old gate rejected 9 of 30 good phone photos (bright paper counted as glare), forcing needless re-uploads
@pytest.mark.parametrize("name", NAMES)
def test_good_photos_pass(photos, name):
    d, _ = photos
    _, rep = quality.prepare(str(d / f"{name}.png"))
    assert rep.ok, (name, rep.reasons, round(rep.glare, 3), round(rep.blur))


# Why: a hotspot that washes out half of a darker photo must be sent back for a re-take; otherwise the washed-out
# answers would look blank and silently score 0
def test_large_glare_rejected(photos, tmp_path):
    _, imgs = photos
    f = tmp_path / "glare.png"
    cv2.imwrite(str(f), _hotspot(imgs["2B_s04_p1"], 0.5))
    _, rep = quality.prepare(str(f))
    assert "glare / reflection on the page" in rep.reasons


# Why: a truly out-of-focus photo must still be rejected (handwriting becomes unreadable)
def test_blurred_photo_rejected(photos, tmp_path):
    _, imgs = photos
    f = tmp_path / "blur.png"
    cv2.imwrite(str(f), cv2.GaussianBlur(imgs["2A_s01_p1"], (0, 0), 4))
    _, rep = quality.prepare(str(f))
    assert "image is blurry" in rep.reasons


# Why: regression — a heavily blurred written page used to be classed as a blank back and skipped silently
# (its answers would have scored 0 with no TA); it must be rejected as blurry instead
def test_very_blurred_page_is_not_blank(photos, tmp_path):
    _, imgs = photos
    f = tmp_path / "blur6.png"
    cv2.imwrite(str(f), cv2.GaussianBlur(imgs["mcq_s02_p1"], (0, 0), 6))
    _, rep = quality.prepare(str(f))
    assert not rep.blank and "image is blurry" in rep.reasons
