# trocr_engine.py — Handwritten answer sheet extraction via Ollama vision model.
#
# Uses llama3.2-vision:11b running locally via Ollama instead of TrOCR/EasyOCR.
# The VLM understands the image contextually, avoiding OCR character-level errors.
#
# Also used later for subjective question grading (same Ollama instance).
#
# REAL mode  — Ollama server reachable at OLLAMA_HOST (default localhost:11434)
# STUB mode  — Ollama unreachable; returns flagged mock answers for pipeline testing

from __future__ import annotations
import os
import re
import json
import base64
import requests
from typing import Dict, Tuple

from app.prompts.prompt_mcq import build_mcq_prompt

OLLAMA_HOST  = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_VISION_MODEL", "llama3.2-vision:11b")
_TIMEOUT     = 120  # seconds per image


class TrOCREngine:
    """
    Extracts handwritten MCQ answers from an answer-sheet image using a
    local Ollama vision model. Falls back to stub mode when Ollama is down.
    """

    def __init__(self):
        self._mode = "unloaded"

    # ── Lazy check ────────────────────────────────────────────────────────────

    def _ensure_loaded(self):
        if self._mode != "unloaded":
            return
        try:
            r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
            models = [m["name"] for m in r.json().get("models", [])]
            if any(OLLAMA_MODEL.split(":")[0] in m for m in models):
                print(f"✅ Ollama: '{OLLAMA_MODEL}' ready at {OLLAMA_HOST}")
                self._mode = "real"
            else:
                print(f"⚠️  Ollama: model '{OLLAMA_MODEL}' not found. Available: {models}. "
                      "Run: ollama pull llama3.2-vision:11b")
                self._mode = "stub"
        except Exception as e:
            print(f"⚠️  Ollama: server unreachable ({e}). Running in STUB mode. "
                  "Start Ollama with: ~/.local/bin/ollama serve")
            self._mode = "stub"

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def mode(self) -> str:
        self._ensure_loaded()
        return self._mode

    def extract_text(self, image_path: str, mcq_count: int = 0) -> Tuple[str, float]:
        """
        Send the image to Ollama and return (raw_text, confidence).
        mcq_count is passed into the prompt so the model knows the question range.
        In stub mode returns a sentinel string.
        """
        self._ensure_loaded()
        if self._mode == "real":
            return self._ollama_extract(image_path, mcq_count)
        print(f"🔧 OCR STUB: returning placeholder for '{image_path}'")
        return "__TROCR_STUB__", 0.0

    def parse_mcq_results(self, text: str, mcq_count: int = 0) -> Dict[str, str]:
        """
        Parse Ollama's response — tries JSON first, falls back to regex.
        Returns {"Q1": "A", "Q2": "B", ...}.
        """
        if text == "__TROCR_STUB__":
            import random
            mock = {f"Q{i}": random.choice(["A", "B", "C", "D"])
                    for i in range(1, mcq_count + 1)} if mcq_count > 0 else {}
            print(f"🔧 OCR STUB: mock answers: {mock}")
            return mock

        # Try parsing a JSON block the model may have returned
        results = _parse_json_answers(text, mcq_count)
        if results:
            return results

        # Fallback: regex for lines like "1. A", "Q2: B", "3)C"
        results = {}
        pattern = r"[Qq]?(\d+)\s*[.\s:)]\s*([A-Ea-e])"
        for match in re.finditer(pattern, text):
            q_num  = int(match.group(1))
            choice = match.group(2).upper()
            if 1 <= q_num <= (mcq_count or 200):
                results[f"Q{q_num}"] = choice
        return results

    # ── Ollama inference ──────────────────────────────────────────────────────

    def _ollama_extract(self, image_path: str, mcq_count: int = 0) -> Tuple[str, float]:
        try:
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()

            prompt = build_mcq_prompt(mcq_count) if mcq_count > 0 else build_mcq_prompt(50)
            print(f"  Ollama: sending '{image_path}' to {OLLAMA_MODEL} (mcq_count={mcq_count}) …")
            response = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model":  OLLAMA_MODEL,
                    "prompt": prompt,
                    "images": [img_b64],
                    "stream": False,
                },
                timeout=_TIMEOUT,
            )
            response.raise_for_status()
            raw_text = response.json().get("response", "").strip()
            print(f"  Ollama raw response: {raw_text[:300]}")
            return raw_text, 0.9

        except Exception as e:
            print(f"❌ Ollama inference error: {e}")
            return "", 0.0


# ── JSON answer parser ────────────────────────────────────────────────────────

def _parse_json_answers(text: str, mcq_count: int) -> Dict[str, str]:
    """Extract a JSON object from the model response and normalise keys."""
    # Find the first {...} block
    match = re.search(r"\{[^{}]+\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        raw = json.loads(match.group())
        results = {}
        for k, v in raw.items():
            # Normalise key: "1", "Q1", "q1" → "Q1"
            num = re.search(r"\d+", str(k))
            if not num:
                continue
            q_num = int(num.group())
            choice = str(v).strip().upper()
            if 1 <= q_num <= (mcq_count or 200) and choice in "ABCDE":
                results[f"Q{q_num}"] = choice
        return results
    except (json.JSONDecodeError, ValueError):
        return {}
