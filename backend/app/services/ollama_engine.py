# ollama_engine.py — legacy handwritten-sheet reader using one Ollama vision model.
#
# Fallback path: used only when the vLLM model servers are not reachable.
# REAL mode = Ollama is up and has the model; STUB mode = returns random mock answers.

from __future__ import annotations

import base64
import json
import os
import random
import re
import time
from typing import Dict, Tuple

import requests

from app.prompts.prompt_extraction import build_extraction_prompt

# Server, model and timeouts (override with env vars)
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_VISION_MODEL", "llama3.2-vision:11b")
_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "300"))
_TIMEOUT_SUBJECTIVE = int(os.environ.get("OLLAMA_TIMEOUT_SUBJECTIVE", "180"))


class OllamaEngine:
    """Reads MCQ / numerical / subjective answers from a sheet image via Ollama."""

    def __init__(self):
        self._mode = "unloaded"

    @property
    def mode(self) -> str:
        """'real' if Ollama has the model, else 'stub' (checked once, lazily)."""
        if self._mode == "unloaded":
            try:
                tags = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5).json()
                names = [m["name"] for m in tags.get("models", [])]
                self._mode = "real" if any(OLLAMA_MODEL.split(":")[0] in n for n in names) else "stub"
            except Exception:
                self._mode = "stub"
            print(f"Ollama: {self._mode} mode ({OLLAMA_MODEL} at {OLLAMA_HOST})")
        return self._mode

    def extract(self, image_path: str, mcq_count: int, numerical_count: int = 0,
                subjective_count: int = 0) -> Tuple[Dict[str, str], float, float]:
        """Return (answers {Q*, N*, S*}, confidence, latency_s) for one page."""
        # Stub mode: random answers so the rest of the pipeline can be exercised
        if self.mode == "stub":
            mock = {f"Q{i}": random.choice("ABCD") for i in range(1, mcq_count + 1)}
            mock |= {f"N{i}": str(random.randint(0, 100)) for i in range(1, numerical_count + 1)}
            mock |= {f"S{i}": f"[STUB] answer {i}" for i in range(1, subjective_count + 1)}
            return mock, 0.0, 0.0

        # One combined call for the whole sheet
        prompt = build_extraction_prompt(mcq_count, numerical_count, subjective_count)
        raw, latency = _call(image_path, prompt, _TIMEOUT)
        answers = parse_answers(raw, mcq_count, numerical_count, subjective_count)

        # Retry any subjective answer the combined call missed, one question at a time
        for i in range(1, subjective_count + 1):
            if not answers.get(f"S{i}"):
                text, t = _call(image_path, _single_subjective_prompt(i), _TIMEOUT_SUBJECTIVE)
                latency += t
                if text and text.upper() != "NOT_FOUND":
                    answers[f"S{i}"] = text

        print(f"  Ollama: {len(answers)} answers in {latency:.1f}s")
        return answers, (0.9 if raw else 0.0), latency


def _call(image_path: str, prompt: str, timeout: int) -> Tuple[str, float]:
    """POST one image + prompt to Ollama; return (response_text, latency_s)."""
    t0 = time.time()
    try:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        resp = requests.post(f"{OLLAMA_HOST}/api/generate", timeout=timeout, json={
            "model": OLLAMA_MODEL, "prompt": prompt, "images": [img_b64], "stream": False})
        resp.raise_for_status()
        return resp.json().get("response", "").strip(), round(time.time() - t0, 3)
    except Exception as e:
        print(f"❌ Ollama error: {e}")
        return "", round(time.time() - t0, 3)


def _single_subjective_prompt(i: int) -> str:
    """Focused prompt that asks for just one subjective answer (S{i})."""
    return (f"Find the student's handwritten answer labelled S{i} on this sheet and transcribe "
            f"it exactly, word for word, without the label. Do not summarise. "
            f"If there is no answer for S{i}, return exactly: NOT_FOUND")


def parse_answers(text: str, mcq_count: int, numerical_count: int = 0,
                  subjective_count: int = 0) -> Dict[str, str]:
    """Parse the model's JSON (sectioned or flat) into {Q1.., N1.., S1..}."""
    # Grab the outermost JSON object; fall back to regex for MCQ-only sheets
    match = re.search(r"\{.*\}", text or "", re.DOTALL)
    try:
        raw = json.loads(match.group()) if match else {}
    except ValueError:
        raw = {}
    if not raw:
        return _regex_mcq(text or "", mcq_count)

    # Flatten {"mcq": {...}, "numerical": {...}, "subjective": {...}} into one dict
    flat = {}
    for k, v in raw.items():
        flat.update(v) if isinstance(v, dict) else flat.__setitem__(k, v)

    # Map each sheet label to an internal id (Q7 on a 6-MCQ paper → N1)
    out: Dict[str, str] = {}
    for k, v in flat.items():
        label, num = str(k).strip().upper(), re.search(r"\d+", str(k))
        if not num or v in (None, ""):
            continue
        n = int(num.group())
        if label.startswith("S") and n <= subjective_count:
            out[f"S{n}"] = str(v).strip()
        elif label.startswith("N") and n <= numerical_count:
            out[f"N{n}"] = str(v).split(",")[0].strip()
        elif label.startswith("Q") and n <= mcq_count:
            if letters := normalise_mcq(str(v)):
                out[f"Q{n}"] = letters
        elif label.startswith("Q") and n - mcq_count <= numerical_count:
            out[f"N{n - mcq_count}"] = str(v).split(",")[0].strip()
    return out


def _regex_mcq(text: str, mcq_count: int) -> Dict[str, str]:
    """Last-resort parse of lines like 'Q3: B' or '3) A,C'."""
    out = {}
    for m in re.finditer(r"[Qq]?(\d+)\s*[.\s:)]\s*([A-Ea-e](?:,[A-Ea-e])*)", text):
        if 1 <= int(m.group(1)) <= mcq_count and (letters := normalise_mcq(m.group(2))):
            out[f"Q{int(m.group(1))}"] = letters
    return out


def normalise_mcq(v: str) -> str:
    """'ac' / 'A, C' / 'C,A' → 'A,C'."""
    return ",".join(sorted(set(re.findall(r"[A-E]", v.upper()))))
