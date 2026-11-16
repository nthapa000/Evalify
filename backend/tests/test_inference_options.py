# test_inference_options.py — switches and helpers for the inference-optimisation experiments
# (INFERENCE_OPTIMIZATION.md). No model server, MongoDB or GPU needed.

import base64
import importlib.util
import io
import sys
from pathlib import Path

import pytest
from PIL import Image

from app.pipeline import grader, llm
from app.prompts import prompt_pipeline as P

REPO = Path(__file__).resolve().parents[2]


def _load(name: str, path: Path):
    """Import a script that is not part of the backend package (infra / eval)."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _Resp:
    """Minimal requests.Response stand-in."""
    def raise_for_status(self):
        return None

    def json(self):
        return {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}


# ── #3 smaller page images for one model ────────────────────────────────────

# Why: the cap must really send fewer pixels (fewer image tokens) and keep the page's shape
def test_cap_pixels_downscales_and_keeps_aspect():
    out = llm.cap_pixels(Image.new("RGB", (1414, 2000), "white"), 1_000_000)
    w, h = out.size
    assert w * h <= 1_000_000 and abs(w / h - 1414 / 2000) < 0.01


# Why: with no cap (the default) or a small page the image must pass through untouched
def test_cap_pixels_leaves_small_or_uncapped_images():
    img = Image.new("RGB", (100, 100))
    assert llm.cap_pixels(img, 0) is img and llm.cap_pixels(img, 1_000_000) is img


# Why: a missing or broken setting must mean "no cap", never break marking
@pytest.mark.parametrize("value,expected", [("", 0), ("not json", 0), ('{"qwen38-27b-fp8": 1400000}', 1400000)])
def test_max_pixels_setting(monkeypatch, value, expected):
    monkeypatch.setenv("EVALIFY_IMAGE_MAX_PIXELS", value)
    assert llm.max_pixels("qwen38-27b-fp8") == expected and llm.max_pixels("gemma4-31b-fp8") == 0


# Why: only the capped model may get the smaller image; the other readers must still see the full page
def test_chat_caps_only_the_named_model(monkeypatch):
    monkeypatch.setenv("EVALIFY_IMAGE_MAX_PIXELS", '{"qwen38-27b-fp8": 500000}')
    sent = []
    monkeypatch.setattr(llm.requests, "post", lambda url, json=None, timeout=None: sent.append(json) or _Resp())
    page = Image.new("RGB", (1414, 2000), "white")
    for name in ("qwen38-27b-fp8", "gemma4-31b-fp8"):
        llm.chat(llm.Endpoint(name, "http://x", {}), "read", [page])
    sizes = []
    for body in sent:
        url = body["messages"][0]["content"][0]["image_url"]["url"]
        sizes.append(Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1]))).size)
    assert sizes[0][0] * sizes[0][1] <= 500000 and sizes[1] == (1414, 2000)


# ── #5 fixed part of the grading prompt first ────────────────────────────────

ARGS = ("Define supervised learning", "Learning from labelled data", ["uses labels", "gives an example"])


# Why: the reordered prompt must contain exactly the same words — only the order may change
def test_fixed_first_has_the_same_words():
    std = P.grade_prompt_v2(*ARGS, "ans A", "ans B", "DS")
    fixed = P.grade_prompt_v2(*ARGS, "ans A", "ans B", "DS", layout="fixed_first")
    assert std != fixed and sorted(std.split()) == sorted(fixed.split())


# Why: prefix caching only helps if two students' prompts are identical up to their own transcriptions
def test_fixed_first_shares_the_prefix_between_students():
    a = P.grade_prompt_v2(*ARGS, "first student", "x", "DS", layout="fixed_first")
    b = P.grade_prompt_v2(*ARGS, "second student", "y", "DS", layout="fixed_first")
    shared = a[:a.index("first student")]
    assert b.startswith(shared) and "Marking rules" in shared and "Rubric points" in shared


# Why: the grader must pick the layout from the setting, and default to the measured standard layout
@pytest.mark.parametrize("env,layout", [(None, "standard"), ("fixed_first", "fixed_first")])
def test_grader_reads_layout_setting(monkeypatch, env, layout):
    if env:
        monkeypatch.setenv("EVALIFY_GRADE_LAYOUT", env)
    else:
        monkeypatch.delenv("EVALIFY_GRADE_LAYOUT", raising=False)
    seen = {}
    monkeypatch.setattr(grader.llm, "chat", lambda ep, prompt, *a, **k: seen.update(prompt=prompt) or llm.Reply(text=""))
    grader.grade(llm.Endpoint("gemma4-31b-fp8", "http://g", {}), ARGS[0], {"key_concepts": ARGS[2], "model_answer": ARGS[1]},
                 "ans A", "ans B", [], "DS", version="v2")
    assert seen["prompt"] == P.grade_prompt_v2(*ARGS, "ans A", "ans B", "DS", layout=layout)


# ── Serving profiles (infra/cluster/serve.py) ────────────────────────────────

serve = _load("serve", REPO / "infra" / "cluster" / "serve.py")


# Why: a profile's extra vLLM flags must come after the model's own, so they win (e.g. a larger prefill budget)
def test_serve_cmd_appends_profile_args():
    model = {"repo": "r", "revision": "v", "vllm_args": ["--max-num-seqs", "128"]}
    cmd = serve.serve_cmd({"model": "m", "port": 8211, "mem": 0.9, "args": ["--kv-cache-dtype", "fp8"]}, model)
    assert cmd[-4:] == ["--max-num-seqs", "128", "--kv-cache-dtype", "fp8"] and "8211" in cmd


# Why: a profile that does not fit our GPU pair would silently skip a model; sizes are what nvidia-smi reports
# (A6000 49140 MiB, RTX PRO 6000 97887 MiB) — with nominal 48 / 96 GB the second Gemma copy passed here but was skipped
@pytest.mark.parametrize("profile", ["opt-lean", "opt-swap", "opt-batch", "opt-fp8kv", "opt-gemma2", "opt-gemma2-fp8"])
def test_optimisation_profiles_fit_our_gpus(profile):
    entries = serve.REG["profiles"][profile]
    plan = serve.place(entries, [49140 / 1024, 97887 / 1024])
    placed = [serve.endpoint_key(e) for es in plan.values() for e in es]
    assert sorted(placed) == sorted(serve.endpoint_key(e) for e in entries)
    assert all(e["port"] // 100 == 82 for e in entries)          # never clash with the 81xx job on cn07


# ── Scoring helpers (eval/exp_inference.py) ─────────────────────────────────

sys.path.insert(0, str(REPO / "eval"))
exp = _load("exp_inference", REPO / "eval" / "exp_inference.py")


# Why: MCQ answers are compared as sets of letters, whatever order or separators the reader used
def test_same_mcq():
    assert exp.same_mcq("C, A", "A,C") and not exp.same_mcq("A", "A,C") and exp.same_mcq("", "")


# Why: accuracy counts MCQ and numerical answers with a label, numbers by value (unit ignored)
def test_closed_accuracy():
    gold = {"Q1": {"answer": "B"}, "N1": {"answer": "50 km/hr"}, "S1": {"marks": 2.0}}
    assert exp.closed_accuracy({"Q1": "B", "N1": "50"}, gold) == (2, 2)
    assert exp.closed_accuracy({"Q1": "C"}, gold) == (0, 2)


# Why: written-answer error uses only answers the teacher actually marked (None = not marked)
def test_marks_error_skips_unmarked():
    gold = {"S1": {"marks": 2.0}, "S2": {"marks": None}, "Q1": {"answer": "A"}}
    assert exp.marks_error({"S1": 1.5, "S2": 0.0}, gold) == [0.5]


# Why: "same as baseline" compares only questions present in both runs
def test_agreement():
    assert exp.agreement({"Q1": "A", "Q2": "B", "Q3": "C"}, {"Q1": "A", "Q2": "C"}) == (1, 2)


# Why: KV-cache use and queue length are read from the vLLM /metrics text (old and new metric names)
def test_parse_metrics():
    text = ('vllm:kv_cache_usage_perc{engine="0",model_name="g"} 0.75\n'
            'vllm:num_requests_waiting{engine="0",model_name="g"} 12.0\n'
            'vllm:num_requests_waiting_by_reason{engine="0",reason="capacity"} 3.0\n'
            'vllm:num_requests_running{engine="0",model_name="g"} 30.0\n')
    assert exp.parse_metrics(text) == {"kv": 0.75, "num_requests_waiting": 12.0, "num_requests_running": 30.0}


# ── Production profile and extra model copies (#8) ──────────────────────────

# Why: user decision (16 Nov) — Chandra and PaddleOCR must not be loaded on the GPUs in production
def test_production_profile_has_no_unused_models():
    names = [e["model"] for e in serve.REG["profiles"]["tier1"]]
    assert sorted(names) == ["gemma4-31b-fp8", "glm-ocr", "qwen38-27b-fp8"]
    assert serve.REG["roles"]["page_reader_c"] == ["glm-ocr"]


# Why: a second copy is published as "model#N" but served under the model's own name, so requests stay valid
def test_extra_copy_naming():
    entry = {"model": "gemma4-31b-fp8", "port": 8212, "mem": 0.4, "replica": 2}
    assert serve.endpoint_key(entry) == "gemma4-31b-fp8#2"
    cmd = serve.serve_cmd(entry, {"repo": "r", "revision": "v"})
    assert cmd[cmd.index("--served-model-name") + 1] == "gemma4-31b-fp8"


def _two_copies(monkeypatch):
    """Endpoints file with Gemma on two servers."""
    monkeypatch.setattr(llm, "_endpoint_urls", lambda: {"gemma4-31b-fp8": "http://g1", "gemma4-31b-fp8#2": "http://g2"})
    monkeypatch.setattr(llm, "_is_up", lambda url: True)
    llm._copies_cache.clear()
    llm._inflight.clear()
    return llm.Endpoint("gemma4-31b-fp8", "http://g1", {})


# Why: each request must go to the copy with fewer requests in flight, so the faster GPU takes more work
def test_pick_url_prefers_least_busy_copy(monkeypatch):
    ep = _two_copies(monkeypatch)
    assert llm.copies(ep) == ["http://g1", "http://g2"]
    llm._inflight.update({"http://g1": 3, "http://g2": 1})
    assert llm.pick_url(ep) == "http://g2"


# Why: requests really reach both copies and the in-flight counts return to zero afterwards
def test_chat_spreads_requests_over_copies(monkeypatch):
    ep = _two_copies(monkeypatch)
    hit = []
    monkeypatch.setattr(llm.requests, "post", lambda url, json=None, timeout=None: hit.append(url) or _Resp())
    llm._inflight["http://g1"] = 1                      # another request is still running on copy 1
    llm.chat(ep, "read")
    assert hit == ["http://g2/chat/completions"] and llm._inflight["http://g2"] == 0


# Why: an endpoint given directly (tests, env override) must never be re-routed to other servers
def test_copies_ignored_for_unlisted_endpoint(monkeypatch):
    _two_copies(monkeypatch)
    assert llm.copies(llm.Endpoint("gemma4-31b-fp8", "http://elsewhere", {})) == ["http://elsewhere"]
