# ollama_engine.py — Handwritten answer sheet extraction via Ollama vision model.
#
# Replaces TrOCR and EasyOCR (both rejected):
#   TrOCR (microsoft/trocr-base-handwritten): trained on IAM sentences dataset,
#     hallucinated full English sentences instead of isolated MCQ letters.
#   EasyOCR: character-level confidence averaged 0.36 on single handwritten letters.
#
# Supports two extraction modes:
#   MCQ-only      — returns {"Q1": "A", "Q2": "B,C", ...}
#   MCQ+Numerical — returns {"Q1": "A", ..., "N1": "3.5", "N2": "42", ...}
#
# REAL mode  — Ollama server reachable at OLLAMA_HOST (default localhost:11434)
# STUB mode  — Ollama unreachable; returns flagged mock data for pipeline testing

from __future__ import annotations
import os
import re
import json
import time
import base64
import requests
from typing import Dict, Tuple

from app.prompts.prompt_mcq import build_mcq_prompt
from app.prompts.prompt_mcq_numerical import build_mcq_numerical_prompt

OLLAMA_HOST  = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_VISION_MODEL", "llama3.2-vision:11b")
_TIMEOUT     = 120  # seconds per inference call


class OllamaEngine:
    """
    Extracts handwritten answers from answer-sheet images using a
    local Ollama vision model. Falls back to stub mode when Ollama is down.
    """

    def __init__(self):
        self._mode = "unloaded"

    # ── Lazy availability check ───────────────────────────────────────────────

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
            print(f"⚠️  Ollama: server unreachable ({e}). Running in STUB mode.")
            self._mode = "stub"

    @property
    def mode(self) -> str:
        self._ensure_loaded()
        return self._mode

    # ── Public API ────────────────────────────────────────────────────────────

    def extract_mcq(
        self,
        image_path: str,
        mcq_count: int,
    ) -> Tuple[Dict[str, str], float, float]:
        """
        Extract MCQ-only answers from a handwritten sheet.
        Returns (answers, confidence, latency_s).
        answers keys: Q1..Qn
        """
        self._ensure_loaded()
        if self._mode == "stub":
            import random
            mock = {f"Q{i}": random.choice(["A", "B", "C", "D"])
                    for i in range(1, mcq_count + 1)}
            print(f"🔧 Ollama STUB: mock MCQ {mock}")
            return mock, 0.0, 0.0

        prompt = build_mcq_prompt(mcq_count)
        raw, conf, latency = self._call_ollama(image_path, prompt)
        answers = _parse_mcq_json(raw, mcq_count)
        print(f"  Ollama MCQ: {len(answers)} answers extracted in {latency:.1f}s")
        return answers, conf, latency

    def extract_mcq_numerical(
        self,
        image_path: str,
        mcq_count: int,
        numerical_count: int,
    ) -> Tuple[Dict[str, str], float, float]:
        """
        Extract MCQ + Numerical answers from a Type 2 handwritten sheet.
        Returns (answers, confidence, latency_s).
        answers keys: Q1..Qn (MCQ) + N1..Nm (Numerical) merged in one dict.
        """
        self._ensure_loaded()
        if self._mode == "stub":
            import random
            mock = {
                **{f"Q{i}": random.choice(["A", "B", "C", "D"]) for i in range(1, mcq_count + 1)},
                **{f"N{i}": str(random.randint(0, 100)) for i in range(1, numerical_count + 1)},
            }
            print(f"🔧 Ollama STUB: mock MCQ+Num {mock}")
            return mock, 0.0, 0.0

        prompt = build_mcq_numerical_prompt(mcq_count, numerical_count)
        raw, conf, latency = self._call_ollama(image_path, prompt)
        answers = _parse_mcq_numerical_json(raw, mcq_count, numerical_count)
        print(f"  Ollama MCQ+Num: {len(answers)} answers extracted in {latency:.1f}s")
        return answers, conf, latency

    # ── Ollama HTTP call ──────────────────────────────────────────────────────

    def _call_ollama(self, image_path: str, prompt: str) -> Tuple[str, float, float]:
        """POST to /api/generate. Returns (raw_text, confidence, latency_s)."""
        t0 = time.time()
        try:
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()

            print(f"  Ollama: sending '{image_path}' → {OLLAMA_MODEL} …")
            resp = requests.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model":  OLLAMA_MODEL,
                    "prompt": prompt,
                    "images": [img_b64],
                    "stream": False,
                },
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            raw = resp.json().get("response", "").strip()
            latency = round(time.time() - t0, 3)
            print(f"  Ollama response ({latency}s): {raw[:300]}")
            return raw, 0.9, latency

        except Exception as e:
            latency = round(time.time() - t0, 3)
            print(f"❌ Ollama error ({latency}s): {e}")
            return "", 0.0, latency


# ── JSON parsers ──────────────────────────────────────────────────────────────

def _parse_mcq_json(text: str, mcq_count: int) -> Dict[str, str]:
    """
    Parse an MCQ-only JSON from Ollama. Falls back to regex.
    Returns {"Q1": "A", "Q2": "B,C", ...}.
    """
    match = re.search(r"\{[^{}]+\}", text, re.DOTALL)
    if match:
        try:
            raw = json.loads(match.group())
            results: Dict[str, str] = {}
            for k, v in raw.items():
                # Handle wrapped {"mcq": {...}} response
                if isinstance(v, dict) and str(k).lower() == "mcq":
                    for kk, vv in v.items():
                        nn = re.search(r"\d+", str(kk))
                        if nn:
                            qn = int(nn.group())
                            val = _normalise_mcq(str(vv))
                            if val and 1 <= qn <= mcq_count:
                                results[f"Q{qn}"] = val
                    continue
                num = re.search(r"\d+", str(k))
                if not num:
                    continue
                q_num = int(num.group())
                val = _normalise_mcq(str(v))
                if val and 1 <= q_num <= mcq_count:
                    results[f"Q{q_num}"] = val
            if results:
                return results
        except (json.JSONDecodeError, ValueError):
            pass

    # Regex fallback
    results = {}
    for m in re.finditer(r"[Qq]?(\d+)\s*[.\s:)]\s*([A-Ea-e](?:,[A-Ea-e])*)", text):
        q_num = int(m.group(1))
        val = _normalise_mcq(m.group(2))
        if val and 1 <= q_num <= mcq_count:
            results[f"Q{q_num}"] = val
    return results


def _parse_mcq_numerical_json(
    text: str, mcq_count: int, numerical_count: int
) -> Dict[str, str]:
    """
    Parse a combined MCQ+Numerical JSON.

    The prompt returns numerical answers keyed as Q{mcq_count+1}..Q{total} because
    students number their sheet Q1..Q_total throughout. This function:
      - Keeps Q1..Qn as MCQ keys
      - Remaps Q(n+1)..Q(n+m) → N1..Nm (numerical keys for the evaluator)
      - Also handles legacy {"mcq":{}, "numerical":{N1..Nm}} format as fallback
    """
    results: Dict[str, str] = {}
    total = mcq_count + numerical_count

    # ── Try to find any JSON block ────────────────────────────────────────────
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return results

    try:
        raw = json.loads(match.group())
    except (json.JSONDecodeError, ValueError):
        return results

    # ── Format 1: {"mcq": {...}, "numerical": {...}} ───────────────────────
    if "mcq" in raw or "numerical" in raw:
        for k, v in raw.get("mcq", {}).items():
            num = re.search(r"\d+", str(k))
            if num:
                q_num = int(num.group())
                val = _normalise_mcq(str(v))
                if val and 1 <= q_num <= mcq_count:
                    results[f"Q{q_num}"] = val

        num_section = raw.get("numerical", {})
        for k, v in num_section.items():
            k_up = str(k).strip().upper()
            num = re.search(r"\d+", k_up)
            if not num:
                continue
            idx = int(num.group())
            val = _extract_first_value(str(v))
            if not val:
                continue
            if k_up.startswith("N") and 1 <= idx <= numerical_count:
                # Already N-keyed
                results[f"N{idx}"] = val
            elif k_up.startswith("Q"):
                # Q7-style key inside "numerical" section → remap to N key
                n_idx = idx - mcq_count
                if 1 <= n_idx <= numerical_count:
                    results[f"N{n_idx}"] = val
        return results

    # ── Format 2: flat dict {"Q1":"C", ..., "Q7":"5/8", ...} ─────────────
    for k, v in raw.items():
        k_up = str(k).strip().upper()
        num = re.search(r"\d+", k_up)
        if not num:
            continue
        idx = int(num.group())

        if k_up.startswith("Q"):
            if 1 <= idx <= mcq_count:
                # MCQ question
                val = _normalise_mcq(str(v))
                if val:
                    results[f"Q{idx}"] = val
            elif mcq_count < idx <= total:
                # Numerical question (Q7, Q8 … → N1, N2 …)
                val = _extract_first_value(str(v))
                if val:
                    results[f"N{idx - mcq_count}"] = val
        elif k_up.startswith("N") and 1 <= idx <= numerical_count:
            val = _extract_first_value(str(v))
            if val:
                results[f"N{idx}"] = val

    return results


def _extract_first_value(v: str) -> str:
    """
    From a raw numerical value string, extract just the first value.
    "5/8, 0.625" → "5/8"
    "1.5, 3/2"   → "1.5"
    "3"           → "3"
    """
    v = v.strip()
    # Take everything before the first comma
    first = v.split(",")[0].strip()
    return first


def _normalise_mcq(v: str) -> str:
    """Normalise a raw MCQ value to sorted uppercase comma-joined letters."""
    v = v.strip().upper()
    # "AC" → "A,C" (letters run together)
    if re.fullmatch(r"[A-E]{2,}", v):
        v = ",".join(sorted(v))
    letters = sorted(set(re.findall(r"[A-E]", v)))
    return ",".join(letters) if letters else ""
