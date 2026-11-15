# test_llm.py — model endpoint lookup and model-call helpers (no model server needed).

import json

import pytest

from app.pipeline import llm


# Why: models sometimes wrap JSON in ``` fences or stop before the closing bracket; we must still read it
@pytest.mark.parametrize("text,expected", [
    ('{"a": 1}', {"a": 1}),
    ('```json\n{"a": 1}\n```', {"a": 1}),
    ('Sure! {"a": 1} hope this helps', {"a": 1}),
    ('{"answers": [{"x": 1}', {"answers": [{"x": 1}]}),
    ("no json here", None),
])
def test_parse_json(text, expected):
    assert llm.parse_json(text) == expected


# Why: a role resolves to the first LIVE model in its preference list, skipping excluded ones (different reader)
def test_resolve_prefers_first_live_and_honours_exclude(monkeypatch):
    monkeypatch.setattr(llm, "_endpoint_urls", lambda: {"gemma4-31b-fp8": "http://g", "qwen38-27b-fp8": "http://q",
                                                        "glm-ocr": "http://glm"})
    monkeypatch.setattr(llm, "_is_up", lambda url: url != "http://g")     # Gemma is down
    assert llm.resolve("page_reader_a").name == "qwen38-27b-fp8"        # falls back down the list
    assert llm.resolve("page_reader_b", exclude=("qwen38-27b-fp8",)) is None
    assert llm.resolve("page_reader_c").name == "glm-ocr"


# Why: the evaluator only uses the pipeline for handwriting when a reader of the v2 pipeline is up
def test_any_live_uses_v2_reader_role(monkeypatch):
    seen = []
    monkeypatch.setattr(llm, "resolve", lambda role, exclude=(): seen.append(role) or None)
    assert llm.any_live() is False and seen == ["page_reader_a"]


# Why: every role used by the v2 pipeline must exist in infra/models.yaml (a typo would silently disable it)
def test_v2_roles_exist():
    roles = llm.registry()["roles"]
    for role in ("page_reader_a", "page_reader_b", "page_reader_c", "transcriber_a", "transcriber_b", "grader"):
        assert roles.get(role), role
        assert all(m in llm.registry()["models"] for m in roles[role])


# Why: the prompt hash is logged with every score, so the same prompt must always give the same hash
def test_prompt_hash_stable():
    assert llm.prompt_hash("a", "b") == llm.prompt_hash("a", "b") != llm.prompt_hash("a", "c")


# Why: images are sent inline as data URLs; the format must be what the OpenAI-compatible API expects
def test_image_part(tmp_path):
    from PIL import Image
    part = llm.image_part(Image.new("RGB", (4, 4), "white"))
    assert part["type"] == "image_url" and part["image_url"]["url"].startswith("data:image/png;base64,")


class _Resp:
    """Minimal requests.Response stand-in."""
    def __init__(self, content, finish="stop"):
        self._c, self._f = content, finish

    def raise_for_status(self):
        return None

    def json(self):
        return {"choices": [{"message": {"content": self._c}, "finish_reason": self._f}]}


# Why: with a JSON schema the reply is parsed, the schema is sent as guided decoding, temperature is 0
def test_chat_parses_json_and_sends_schema(monkeypatch):
    sent = {}

    def post(url, json=None, timeout=None):
        sent.update(json)
        return _Resp('{"answers": []}')
    monkeypatch.setattr(llm.requests, "post", post)
    ep = llm.Endpoint("qwen38-27b-fp8", "http://q", {"supports_json_schema": True})
    reply = llm.chat(ep, "read", schema={"type": "object", "required": ["answers"]})
    assert reply.data == {"answers": []} and reply.error == ""
    assert sent["temperature"] == 0.0 and sent["response_format"]["type"] == "json_schema"


# Why: a server error must come back as reply.error (the pipeline then flags the answer), never raise
def test_chat_reports_errors(monkeypatch):
    def post(url, json=None, timeout=None):
        raise ConnectionError("server down")
    monkeypatch.setattr(llm.requests, "post", post)
    reply = llm.chat(llm.Endpoint("x", "http://x", {}), "read")
    assert "server down" in reply.error and reply.text == ""


# Why: guided decoding can loop until max_tokens (seen with Gemma); one unconstrained retry must recover it
def test_chat_retries_runaway_json(monkeypatch):
    calls = []

    def post(url, json=None, timeout=None):
        calls.append(json)
        return _Resp("   " * 5, finish="length") if len(calls) == 1 else _Resp('{"answers": [1]}')
    monkeypatch.setattr(llm.requests, "post", post)
    ep = llm.Endpoint("gemma4-31b-fp8", "http://g", {"supports_json_schema": True})
    reply = llm.chat(ep, "read", schema={"type": "object", "required": ["answers"]})
    assert reply.data == {"answers": [1]} and len(calls) == 2 and "response_format" not in calls[1]
