#!/usr/bin/env python3
"""cost_compare.py — cost per 1,000 answer sheets: open-model API vs our own (rented) GPUs.

    python eval/cost_compare.py      # writes eval/reports/cost_compare/README.md

API side:  measured tokens per sheet per model (exp_tokens/sheets.json) x provider prices per 1M tokens.
Self-host: measured sheets per hour at the best concurrency (exp_throughput/runs.json) x GPU rental per hour.
Prices are web lookups from 16 Nov 2026 (aggregator pages; they change often): edit PRICES / GPU_HOUR below.
"""
from __future__ import annotations

import json
from pathlib import Path

REP = Path(__file__).resolve().parent / "reports"
OUT = REP / "cost_compare"

# $ per 1M tokens (input, output). "low" = cheapest provider seen, "typical" = common mid-range listing
PRICES = {
    "low": {"gemma4-31b-fp8": (0.09, 0.34), "qwen38-27b-fp8": (0.04, 1.50), "glm-ocr": (0.03, 0.03)},
    "typical": {"gemma4-31b-fp8": (0.14, 0.40), "qwen38-27b-fp8": (0.15, 1.88), "glm-ocr": (0.03, 0.03)},
}
# $ per GPU-hour, on demand; our node = 1 x RTX A6000 + 1 x RTX PRO 6000
GPU_HOUR = {"low": 0.35 + 1.69, "typical": 0.55 + 2.20}

# Where the prices came from
SOURCES = ["https://computeprices.com/models/gemma-4-31b-it", "https://models.litellm.ai/models/gemma-4-31b",
           "https://openrouter.ai/qwen/qwen3.8-27b", "https://pricepertoken.com/pricing-page/model/qwen-qwen3.8-27b",
           "https://docs.z.ai/guides/overview/pricing", "https://www.thundercompute.com/blog/nvidia-rtx-a6000-pricing",
           "https://flopper.io/pricing/nvidia-rtx-pro-6000-blackwell", "https://gpu.ai/gpus/rtx-pro-6000"]

# Workloads: token set label in exp_tokens → throughput workload in exp_throughput
WORKLOADS = [("Handwritten MCQ (10 Q, 1 page)", "A  MCQ only (handwritten)", "Handwritten MCQ / MCQ+numerical (1 page)"),
             ("MCQ + numerical (5 Q, 1 page)", "B  MCQ + numerical", "Handwritten MCQ / MCQ+numerical (1 page)"),
             ("Data Science exam (20 MCQ + 15 written, ~3.5 pages)", "C  MCQ + subjective (Data Science exam)",
              "Data Science exam (20 MCQ + 15 written, 4-6 pages)")]


def tokens_per_sheet(rows: list, label: str) -> dict:
    """{model: (input, output)} average per sheet."""
    rs = [r for r in rows if r["set"] == label]
    per: dict = {}
    for r in rs:
        for g in r["usage"]["by_stage"]:
            i, o = per.get(g["model"], (0, 0))
            per[g["model"]] = (i + g["prompt_tokens"], o + g["completion_tokens"])
    return {m: (i / len(rs), o / len(rs)) for m, (i, o) in per.items()}


def api_cost(tok: dict, tier: str) -> float:
    """$ per 1,000 sheets."""
    return sum(i * PRICES[tier][m][0] + o * PRICES[tier][m][1] for m, (i, o) in tok.items()) / 1e6 * 1000


def main() -> None:
    sheets = json.loads((REP / "exp_tokens/sheets.json").read_text())
    runs = json.loads((REP / "exp_throughput/runs.json").read_text())
    best = {}
    for r in runs:
        if r["sheets_per_hour"] > best.get(r["workload"], {}).get("sheets_per_hour", 0):
            best[r["workload"]] = r

    md = ["# Cost per 1,000 answer sheets: open-model API vs own GPUs", "",
          "Tokens: measured per sheet (`exp_tokens`). Throughput: measured on our node (`exp_throughput`), best",
          "concurrency. Prices: web lookups 16 Nov 2026, see the sources list; they change often (edit the constants",
          "in `eval/cost_compare.py`). OMR sheets are read by code: 0 tokens, about 1 s of CPU per sheet.", "",
          "| Paper type | API, low | API, typical | Our GPUs: sheets / hour | Rented GPUs, low | Rented GPUs, typical |",
          "|---|---|---|---|---|---|"]
    for name, tok_label, tp_label in WORKLOADS:
        tok = tokens_per_sheet(sheets, tok_label)
        sph = best[tp_label]["sheets_per_hour"]
        md.append(f"| {name} | ${api_cost(tok, 'low'):.2f} | ${api_cost(tok, 'typical'):.2f} | {sph:.0f} "
                  f"| ${GPU_HOUR['low'] / sph * 1000:.2f} | ${GPU_HOUR['typical'] / sph * 1000:.2f} |")

    md += ["", "Rented GPUs = the node's hourly price / sheets per hour, assuming it is kept busy. An idle rented node",
           f"still costs ${GPU_HOUR['low']:.2f}-${GPU_HOUR['typical']:.2f} per hour.", "",
           "## Prices used ($ per 1M tokens, input / output)", "", "| Model | Low | Typical |", "|---|---|---|"]
    for m in PRICES["low"]:
        md.append(f"| {m} | {PRICES['low'][m][0]} / {PRICES['low'][m][1]} | {PRICES['typical'][m][0]} / {PRICES['typical'][m][1]} |")
    md += ["", f"GPU node per hour (A6000 + RTX PRO 6000): low ${GPU_HOUR['low']:.2f}, typical ${GPU_HOUR['typical']:.2f}."]
    md += ["", "## Sources (16 Nov 2026)", ""] + [f"- {u}" for u in SOURCES]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text("\n".join(md) + "\n")
    print((OUT / "README.md").read_text())


if __name__ == "__main__":
    main()
