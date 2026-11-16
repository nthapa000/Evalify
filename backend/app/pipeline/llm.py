# llm.py — role → model endpoint lookup and OpenAI-compatible calls to vLLM servers.
#
# infra/models.yaml says which models can play each role (in preference order);
# the GPU job writes $EVALIFY_ENDPOINTS_FILE with the base URL of each live server.
# A role resolves to the first model in its list that is actually up, so the
# backend degrades (e.g. to one GPU) instead of breaking.

from __future__ import annotations

import base64
import contextvars
import hashlib
import io
import json
import os
import sys
import threading
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
    prompt_tokens: int = 0    # input tokens (text + image) as counted by the server, retry included
    completion_tokens: int = 0


# ── Token usage meter ────────────────────────────────────────────────────────
# One meter per evaluated sheet. It lives in a context variable so two sheets graded at the
# same time never mix; carry() hands it to the worker threads the pipeline uses.

_meter: contextvars.ContextVar = contextvars.ContextVar("evalify_usage_meter", default=None)


class UsageMeter:
    """Counts the tokens of every model call made inside `with UsageMeter() as m:`."""

    def __init__(self):
        self.calls: list = []
        self._lock = threading.Lock()
        self._token = None

    def __enter__(self):
        self._token = _meter.set(self)
        return self

    def __exit__(self, *exc):
        _meter.reset(self._token)
        return False

    def add(self, stage: str, model: str, prompt_tokens: int, completion_tokens: int, n_images: int) -> None:
        """Record one request."""
        with self._lock:
            self.calls.append({"stage": stage, "model": model, "prompt_tokens": prompt_tokens,
                               "completion_tokens": completion_tokens, "images": n_images})

    def summary(self) -> dict:
        """Totals plus one row per (pipeline step, model)."""
        with self._lock:
            calls = list(self.calls)
        groups: dict = {}
        for c in calls:
            g = groups.setdefault((c["stage"], c["model"]), {"stage": c["stage"], "model": c["model"], "calls": 0,
                                                            "images": 0, "prompt_tokens": 0, "completion_tokens": 0})
            for k in ("images", "prompt_tokens", "completion_tokens"):
                g[k] += c[k]
            g["calls"] += 1
        rows = [{**g, "total_tokens": g["prompt_tokens"] + g["completion_tokens"]} for g in groups.values()]
        pt, ct = sum(c["prompt_tokens"] for c in calls), sum(c["completion_tokens"] for c in calls)
        return {"calls": len(calls), "prompt_tokens": pt, "completion_tokens": ct, "total_tokens": pt + ct,
                "by_stage": rows}


def record(reply: "Reply", stage: str, n_images: int = 0, requests_made: int = 1) -> None:
    """Add a reply's tokens to the active meter (no-op when none is active)."""
    m = _meter.get()
    if m is not None:
        m.add(stage, reply.model, reply.prompt_tokens, reply.completion_tokens, n_images)
        for _ in range(requests_made - 1):            # extra requests (retry): counted as calls, tokens already summed
            m.add(stage, reply.model, 0, 0, 0)


def carry(fn):
    """Wrap fn so that, run in a worker thread, it still records into the caller's meter."""
    m = _meter.get()

    def run(*args, **kwargs):
        token = _meter.set(m)
        try:
            return fn(*args, **kwargs)
        finally:
            _meter.reset(token)
    return run


def _usage(resp_json: dict) -> tuple:
    """(prompt_tokens, completion_tokens) from an OpenAI-style reply (0, 0 if absent)."""
    u = resp_json.get("usage") or {}
    return int(u.get("prompt_tokens") or 0), int(u.get("completion_tokens") or 0)


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


# Extra copies of a model ("name#2" in the endpoints file): each request goes to the least busy copy
_inflight: dict = {}                     # base_url → requests this process has in flight
_inflight_lock = threading.Lock()
_copies_cache: dict = {}                 # model name → (checked_at, [base_url, ...])


def copies(ep: "Endpoint") -> list:
    """Live base URLs serving ep's model: its own plus any "name#N" copies (cached 10 s)."""
    t, urls = _copies_cache.get(ep.name, (0.0, None))
    if urls is None or time.time() - t > 10:
        found = _endpoint_urls()
        # Only for endpoints that come from the endpoints file (never re-route an explicitly given URL)
        urls = [u for n, u in sorted(found.items()) if n.startswith(ep.name + "#") and _is_up(u)] \
            if found.get(ep.name) == ep.base_url else []
        urls = [ep.base_url] + [u for u in urls if u != ep.base_url]
        _copies_cache[ep.name] = (time.time(), urls)
    return urls


def pick_url(ep: "Endpoint") -> str:
    """The copy with the fewest requests in flight from this process (ties: the first listed)."""
    urls = copies(ep)
    if len(urls) == 1:
        return urls[0]
    with _inflight_lock:
        return min(urls, key=lambda u: _inflight.get(u, 0))


def any_live() -> bool:
    """True if at least one v2 page reader is up (else the evaluator uses the legacy Ollama path)."""
    return resolve("page_reader_a") is not None


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


def max_pixels(model: str) -> int:
    """Pixel cap for page images sent to `model` (0 = none), from EVALIFY_IMAGE_MAX_PIXELS='{"model": pixels}'."""
    # Inference experiment #3: fewer image tokens for one model (Qwen spends ~10x Gemma's tokens per page)
    try:
        return int(json.loads(os.environ.get("EVALIFY_IMAGE_MAX_PIXELS", "") or "{}").get(model, 0))
    except (ValueError, AttributeError):
        return 0


def cap_pixels(image, limit: int):
    """Downscale (keeping the aspect ratio) so width x height <= limit; path or PIL image in, PIL or as-is out."""
    if not limit:
        return image
    from PIL import Image
    img = Image.open(image) if isinstance(image, (str, Path)) else image
    w, h = img.size
    if w * h <= limit:
        return image
    scale = (limit / (w * h)) ** 0.5
    return img.convert("RGB").resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)


def prompt_hash(*parts: str) -> str:
    """Short stable hash of a prompt template (logged so prompt changes are traceable)."""
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()[:12]


def chat(ep: Endpoint, prompt: str, images: list = (), schema: Optional[dict] = None,
         system: Optional[str] = None, max_tokens: int = 4096, thinking: bool = False,
         template_id: str = "", stage: str = "") -> Reply:
    """One deterministic chat call; with `schema`, output is constrained to that JSON schema."""
    # Images first, then the instruction (what most VLMs are trained on)
    cap = max_pixels(ep.name)                    # optional per-model image size cap (off by default)
    content = [image_part(cap_pixels(im, cap)) for im in images] + [{"type": "text", "text": prompt}]
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
    requests_made = 1
    url = pick_url(ep)                           # one server, or the least busy copy of this model
    with _inflight_lock:
        _inflight[url] = _inflight.get(url, 0) + 1
    try:
        r = requests.post(f"{url}/chat/completions", json=body, timeout=TIMEOUT_S)
        r.raise_for_status()
        payload = r.json()
        reply.prompt_tokens, reply.completion_tokens = _usage(payload)
        choice = payload["choices"][0]
        reply.text, finish = (choice["message"].get("content") or "").strip(), choice.get("finish_reason", "")
    except Exception as e:
        reply.error = f"{type(e).__name__}: {e}"
        _health.pop(url, None)                  # re-check health next time
    finally:
        with _inflight_lock:
            _inflight[url] -= 1
    reply.latency_s = round(time.time() - t0, 3)

    # Also when the text is empty: a whitespace runaway strips to "" and still needs the retry / an error
    if schema is not None and not reply.error:
        reply.data = parse_json(reply.text) if reply.text else None
        # Guided decoding can loop on whitespace until max_tokens (seen with Gemma 4):
        # retry once unconstrained, asking for the same JSON keys
        if reply.data is None and finish == "length" and "response_format" in body:
            retry = {k: v for k, v in body.items() if k != "response_format"}
            retry["messages"] = messages[:-1] + [{"role": "user", "content": content[:-1] + [{
                "type": "text", "text": prompt + "\nReply with one JSON object with keys: "
                + ", ".join(schema.get("required", [])) + ". No other text."}]}]
            try:
                r = requests.post(f"{url}/chat/completions", json=retry, timeout=TIMEOUT_S)
                requests_made += 1
                payload = r.json()
                pt, ct = _usage(payload)                    # the retry is a second paid request
                reply.prompt_tokens += pt
                reply.completion_tokens += ct
                reply.text = (payload["choices"][0]["message"].get("content") or "").strip()
                reply.data = parse_json(reply.text)
            except Exception as e:
                reply.error = f"retry failed: {e}"
            reply.latency_s = round(time.time() - t0, 3)
        if reply.data is None:
            reply.error = reply.error or "invalid JSON"
    # Pipeline step = the function that called chat() (e.g. _page_closed, run_a, grade)
    record(reply, stage or sys._getframe(1).f_code.co_name, len(images), requests_made)
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
