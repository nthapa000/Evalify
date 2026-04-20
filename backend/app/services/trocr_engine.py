# trocr_engine.py — Handwritten text extraction for "Normal Answer Sheet" mode.
#
# Two operating modes (selected automatically at startup):
#
#   REAL mode   — uses Microsoft TrOCR (HuggingFace transformers + torch).
#                 Activated when both `torch` and `transformers` are installed
#                 and the model can be loaded.
#
#   STUB mode   — activated when torch/transformers are missing or the model
#                 cannot be loaded (e.g. no internet to download weights).
#                 Returns clearly-flagged mock answers so the rest of the
#                 pipeline can still be tested end-to-end.
#
# Answer format expected on a Normal Answer Sheet:
#   Each line: "<question_number>. <A|B|C|D>"
#   Examples:  "1. A"   "2: B"   "Q3 C"   "4)D"

from __future__ import annotations
import re
from typing import Dict, Tuple

# ── Availability check ────────────────────────────────────────────────────────

# Try to import heavy ML libraries; set flags used later for engine selection.
try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False

try:
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False

from PIL import Image


# ── Engine class ─────────────────────────────────────────────────────────────

class TrOCREngine:
    """
    Extracts handwritten MCQ answers from an answer-sheet image.
    Falls back to stub mode when torch/transformers are unavailable.
    """

    MODEL_NAME = "microsoft/trocr-base-handwritten"

    def __init__(self):
        self._processor = None
        self._model     = None
        self._mode      = "unloaded"   # "real" | "stub" | "unloaded"

    # ── Lazy initialisation ───────────────────────────────────────────────────

    def _ensure_loaded(self):
        """Load the TrOCR model on first use (lazy, avoids startup delay)."""
        if self._mode != "unloaded":
            return

        if not (_TORCH_AVAILABLE and _TRANSFORMERS_AVAILABLE):
            print(
                "⚠️  TrOCR: torch or transformers not installed. "
                "Running in STUB mode — install both packages and restart to use real OCR."
            )
            self._mode = "stub"
            return

        try:
            import torch  # re-import inside scope so type checkers are happy
            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"🤖 TrOCR: Loading '{self.MODEL_NAME}' on {device} …")

            self._processor = TrOCRProcessor.from_pretrained(self.MODEL_NAME)
            self._model     = VisionEncoderDecoderModel.from_pretrained(
                self.MODEL_NAME
            ).to(device)
            self._device    = device
            self._mode      = "real"
            print(f"✅ TrOCR: Model loaded successfully.")

        except Exception as e:
            print(f"⚠️  TrOCR: Model load failed ({e}). Running in STUB mode.")
            self._mode = "stub"

    # ── Public API ────────────────────────────────────────────────────────────

    def extract_text(self, image_path: str) -> Tuple[str, float]:
        """
        Run inference on an image.
        Returns (extracted_text, confidence).
        In stub mode returns a clearly labelled placeholder string.
        """
        self._ensure_loaded()

        if self._mode == "real":
            return self._real_extract(image_path)

        # Stub: return a detectable sentinel so callers know it's simulated
        print(f"🔧 TrOCR STUB: returning placeholder text for '{image_path}'")
        return "__TROCR_STUB__", 0.0

    def parse_mcq_results(self, text: str, mcq_count: int = 0) -> Dict[str, str]:
        """
        Parse patterns like "1. A", "2: B", "Q3 C", "4)D" from OCR text.
        Returns {"Q1": "A", "Q2": "B", ...}.
        In stub mode returns empty dict (caller handles missing answers).
        """
        if text == "__TROCR_STUB__":
            # Stub mode: return empty results — scored as wrong answers.
            # Log clearly so developers know this isn't real OCR.
            print("🔧 TrOCR STUB: no real OCR performed; returning empty answer map.")
            return {}

        results: Dict[str, str] = {}
        # Matches: optional "Q", digits, separator (. : ) space), optional space, letter A-D
        pattern = r"[Qq]?(\d+)\s*[.\s:)]\s*([A-Da-d])"
        for match in re.finditer(pattern, text):
            q_num  = int(match.group(1))
            choice = match.group(2).upper()
            results[f"Q{q_num}"] = choice
        return results

    @property
    def mode(self) -> str:
        """Return current operating mode: 'real', 'stub', or 'unloaded'."""
        self._ensure_loaded()
        return self._mode

    # ── Real inference ────────────────────────────────────────────────────────

    def _real_extract(self, image_path: str) -> Tuple[str, float]:
        """Run actual TrOCR inference."""
        try:
            import torch
            image = Image.open(image_path).convert("RGB")
            pixel_values = self._processor(
                images=image, return_tensors="pt"
            ).pixel_values.to(self._device)

            with torch.no_grad():
                generated_ids = self._model.generate(pixel_values)

            text = self._processor.batch_decode(
                generated_ids, skip_special_tokens=True
            )[0].strip()

            # Confidence heuristic: longer non-empty text → higher confidence
            confidence = min(0.95, 0.5 + len(text) * 0.01) if text else 0.0
            return text, confidence

        except Exception as e:
            print(f"❌ TrOCR inference error: {e}")
            return "", 0.0
