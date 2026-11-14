# llm.py — role → model endpoint lookup and OpenAI-compatible calls to vLLM servers.
#
# infra/models.yaml says which models can play each role (in preference order);
# the GPU job writes $EVALIFY_ENDPOINTS_FILE with the base URL of each live server.
# A role resolves to the first model in its list that is actually up, so the
# backend degrades (e.g. to one GPU) instead of breaking.

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import requests
import yaml

# Locations (overridable for tests / other machines)
REPO_ROOT = Path(__file__).resolve().parents[3]
MODELS_YAML = Path(os.environ.get("EVALIFY_MODELS_YAML", REPO_ROOT / "infra" / "models.yaml"))
ENDPOINTS_FILE = Path(os.environ.get("EVALIFY_ENDPOINTS_FILE",
                                     f"/scratch/{os.environ.get('USER', '')}/evalify/run/endpoints.json"))
TIMEOUT_S = int(os.environ.get("EVALIFY_LLM_TIMEOUT", "600"))


@dataclass
class Endpoint:
    """One live model server."""
    name: str                 # registry name, e.g. qwen38-27b-fp8
    base_url: str             # http://cn07:8101/v1
    spec: dict = field(default_factory=dict)

    @property
    def version(self) -> str:
        """repo@revision — logged to MLflow so every score is traceable to exact weights."""
        return f"{self.spec.get('repo', self.name)}@{str(self.spec.get('revision', ''))[:10]}"


@dataclass
class Reply:
    """A model reply plus what we log about it."""
    text: str
    data: Any = None          # parsed JSON when a schema was requested
    model: str = ""
    version: str = ""
    latency_s: float = 0.0
    prompt_hash: str = ""
    error: str = ""


@lru_cache(maxsize=1)
def registry() -> dict:
    """Parsed infra/models.yaml."""
    return yaml.safe_load(MODELS_YAML.read_text())


def _endpoint_urls() -> dict:
    """{model_name: base_url} from the endpoints file, plus EVALIFY_ENDPOINT_<NAME> env overrides."""
    urls = {}
    if ENDPOINTS_FILE.exists():
        urls = {k: v["base_url"] for k, v in json.loads(ENDPOINTS_FILE.read_text()).get("models", {}).items()}
    for name in registry()["models"]:
        env = os.environ.get("EVALIFY_ENDPOINT_" + name.upper().replace("-", "_").replace(".", "_"))
        if env:
            urls[name] = env
    return urls


_health: dict = {}            # base_url → (is_up, checked_at)


def _is_up(base_url: str) -> bool:
    """GET /models with a 60 s cache so we don't ping on every call."""
    up, t = _health.get(base_url, (None, 0.0))
    if up is None or time.time() - t > 60:
        try:
            up = requests.get(f"{base_url}/models", timeout=3).ok
        except requests.RequestException:
            up = False
        _health[base_url] = (up, time.time())
    return up


def resolve(role: str, exclude: tuple = ()) -> Optional[Endpoint]:
    """First live model for a role (skipping `exclude`, e.g. to get a *different* second reader)."""
    urls = _endpoint_urls()
    for name in registry()["roles"].get(role, []):
        if name in exclude or name not in urls:
            continue
        if _is_up(urls[name]):
            return Endpoint(name, urls[name], registry()["models"][name])
    return None


def any_live() -> bool:
    """True if at least one reader is up (else the evaluator uses the legacy Ollama path)."""
    return resolve("reader_a") is not None


def image_part(image) -> dict:
    """PIL image or file path → OpenAI image_url content part (PNG data URL)."""
    if isinstance(image, (str, Path)):
        raw = Path(image).read_bytes()
        mime = "image/png" if str(image).lower().endswith(".png") else "image/jpeg"
    else:
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        raw, mime = buf.getvalue(), "image/png"
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{base64.b64encode(raw).decode()}"}}


def prompt_hash(*parts: str) -> str:
    """Short stable hash of a prompt template (logged so prompt changes are traceable)."""
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[:12]


def chat(ep: Endpoint, prompt: str, images: list = (), schema: Optional[dict] = None,
         system: Optional[str] = None, max_tokens: int = 4096, thinking: bool = False,
         template_id: str = "") -> Reply:
    """One deterministic chat call; with `schema`, output is constrained to that JSON schema."""
    # Images first, then the instruction (what most VLMs are trained on)
    content = [image_part(im) for im in images] + [{"type": "text", "text": prompt}]
    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": content}]
    body: dict = {"model": ep.name, "messages": messages, "max_tokens": max_tokens,
                  "temperature": 0.0, "seed": 0}

    # Structured output (vLLM guided decoding) + Qwen thinking switch
    if schema is not None and ep.spec.get("supports_json_schema"):
        body["response_format"] = {"type": "json_schema",
                                   "json_schema": {"name": "out", "schema": schema, "strict": True}}
    if ep.spec.get("thinking") == "qwen":
        body["chat_template_kwargs"] = {"enable_thinking": thinking}

    reply = Reply(text="", model=ep.name, version=ep.version, prompt_hash=template_id or prompt_hash(prompt))
    t0 = time.time()
    finish = ""
    try:
        r = requests.post(f"{ep.base_url}/chat/completions", json=body, timeout=TIMEOUT_S)
        r.raise_for_status()
        choice = r.json()["choices"][0]
        reply.text, finish = (choice["message"].get("content") or "").strip(), choice.get("finish_reason", "")
    except Exception as e:
        reply.error = f"{type(e).__name__}: {e}"
        _health.pop(ep.base_url, None)          # re-check health next time
    reply.latency_s = round(time.time() - t0, 3)

    if schema is not None and reply.text:
        reply.data = parse_json(reply.text)
        # Guided decoding can loop on whitespace until max_tokens (seen with Gemma 4):
        # retry once unconstrained, asking for the same JSON keys
        if reply.data is None and finish == "length" and "response_format" in body:
            retry = {k: v for k, v in body.items() if k != "response_format"}
            retry["messages"] = messages[:-1] + [{"role": "user", "content": content[:-1] + [{
                "type": "text", "text": prompt + "\nReply with one JSON object with keys: "
                + ", ".join(schema.get("required", [])) + ". No other text."}]}]
            try:
                r = requests.post(f"{ep.base_url}/chat/completions", json=retry, timeout=TIMEOUT_S)
                reply.text = (r.json()["choices"][0]["message"].get("content") or "").strip()
                reply.data = parse_json(reply.text)
            except Exception as e:
                reply.error = f"retry failed: {e}"
            reply.latency_s = round(time.time() - t0, 3)
        if reply.data is None:
            reply.error = reply.error or "invalid JSON"
    return reply


def parse_json(text: str):
    """First JSON object in text; tolerates ``` fences and a missing closing bracket."""
    txt = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    start = txt.find("{")
    if start < 0:
        return None
    for candidate in (txt[start: txt.rfind("}") + 1], txt[start:].rstrip(", \t\n") + "}",
                      txt[start:].rstrip(", \t\n") + "]}"):
        try:
            return json.loads(candidate)
        except ValueError:
            continue
    return None
