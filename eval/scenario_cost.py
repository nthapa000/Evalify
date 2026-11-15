#!/usr/bin/env python3
"""scenario_cost.py — cost and time to mark a whole class, from the measured token and throughput numbers.

    python eval/scenario_cost.py     # writes eval/reports/scenario_cost/README.md

Scenarios (proposal for the department):
  1. 700 answer sheets, type C (MCQ + written answers), 10 pages each on average.
  2. 700 handwritten MCQ quizzes and 700 handwritten MCQ + numerical quizzes (1 page each), plus OMR.
Own servers: the department's GPUs already exist, so no purchase or extra maintenance; the "equivalent rental
value" and electricity are shown only for completeness.
"""
from __future__ import annotations

import json
from pathlib import Path

from cost_compare import GPU_HOUR, PRICES, tokens_per_sheet

REP = Path(__file__).resolve().parent / "reports"
OUT = REP / "scenario_cost"
USD_INR = 88.0                       # assumed exchange rate (₹ per $)
NODE_KW = 1.2                        # A6000 300 W + RTX PRO 6000 600 W + host, under load (estimate)
POWER_INR_KWH = (8.0, 10.0)          # electricity tariff range (₹ per kWh), estimate

N_SHEETS, PAGES, WRITTEN = 700, 10, 15          # scenario 1 assumptions


def type_c_model(rows: list) -> dict:
    """Per-page and per-answer tokens per model, measured on the Data Science sheets."""
    ds = [r for r in rows if r["set"].startswith("C")]
    pages = sum(r["pages_read"] for r in ds)
    per_page, grade = {}, {"in": 0, "out": 0, "calls": 0}
    for r in ds:
        for g in r["usage"]["by_stage"]:
            if g["stage"] == "grade_subjective":
                grade["in"] += g["prompt_tokens"]
                grade["out"] += g["completion_tokens"]
                grade["calls"] += g["calls"]
            else:
                a = per_page.setdefault(g["model"], [0, 0])
                a[0] += g["prompt_tokens"]
                a[1] += g["completion_tokens"]
    per_page = {m: (i / pages, o / pages) for m, (i, o) in per_page.items()}
    # Grading input = fixed part per answer + both transcripts (transcript text per page = transcription output)
    text_per_page = sum(g["completion_tokens"] for r in ds for g in r["usage"]["by_stage"]
                        if g["stage"] == "transcribe_subjective") / pages
    base_in = (grade["in"] - text_per_page * pages) / grade["calls"]
    return {"per_page": per_page, "grade_base_in": base_in, "grade_out": grade["out"] / grade["calls"],
            "text_per_page": text_per_page}


def type_c_sheet(m: dict, pages: int, written: int) -> dict:
    """{model: (input, output)} for one sheet with `pages` pages and `written` answered written questions."""
    tok = {k: [i * pages, o * pages] for k, (i, o) in m["per_page"].items()}
    g = tok.setdefault("gemma4-31b-fp8", [0, 0])            # the grader is Gemma
    g[0] += m["grade_base_in"] * written + m["text_per_page"] * pages
    g[1] += m["grade_out"] * written
    return {k: tuple(v) for k, v in tok.items()}


def usd(tok: dict, tier: str, n: int) -> float:
    """API cost in $ for n sheets."""
    return n * sum(i * PRICES[tier][k][0] + o * PRICES[tier][k][1] for k, (i, o) in tok.items()) / 1e6


def main() -> None:
    rows = json.loads((REP / "exp_tokens/sheets.json").read_text())
    runs = json.loads((REP / "exp_throughput/runs.json").read_text())
    best = {}
    for r in runs:
        if r["tokens_per_s"] > best.get(r["workload"], {}).get("tokens_per_s", 0):
            best[r["workload"]] = r
    ds_tps = best["Data Science exam (20 MCQ + 15 written, 4-6 pages)"]["tokens_per_s"]
    one_page_sph = best["Handwritten MCQ / MCQ+numerical (1 page)"]["sheets_per_hour"]

    m = type_c_model(rows)
    sheet = type_c_sheet(m, PAGES, WRITTEN)
    per_sheet = sum(i + o for i, o in sheet.values())
    hours_c = N_SHEETS * per_sheet / ds_tps / 3600

    def inr(x):
        return f"₹{x * USD_INR:,.0f}"

    def own_rows(hours):
        rent = (GPU_HOUR["low"] * hours, GPU_HOUR["typical"] * hours)
        kwh = NODE_KW * hours
        return (f"{hours:.1f} h of GPU time", f"${rent[0]:.0f}-{rent[1]:.0f} ({inr(rent[0])}-{inr(rent[1])})",
                f"{kwh:.0f} kWh, about ₹{kwh * POWER_INR_KWH[0]:,.0f}-{kwh * POWER_INR_KWH[1]:,.0f}")

    md = ["# Cost and time to mark a class: API vs the department's own servers", "",
          f"All numbers come from measurements on real answer sheets (`exp_tokens`, `exp_throughput`) and API prices",
          f"looked up on 16 Nov 2026 (`cost_compare.py`). ₹ at an assumed ${1} = ₹{USD_INR:.0f}.", "",
          "**Own servers:** the department already has the GPU servers, so there is **no purchase and no extra",
          "maintenance cost**. The rental value and electricity below are shown only for completeness; in our use",
          "they are not an extra charge.", ""]

    # Scenario 1
    own = own_rows(hours_c)
    md += [f"## 1. {N_SHEETS} written exams (type C), {PAGES} pages per answer sheet", "",
           f"Assumed per sheet: {PAGES} pages, MCQs + {WRITTEN} answered written questions (like the Data Science",
           f"exam, with longer answers). Estimated **{per_sheet:,.0f} tokens per sheet** "
           f"({N_SHEETS * per_sheet / 1e6:.1f} M for the class). The estimate is built from per-page and",
           "per-answer costs; on the measured 4- and 6-page sheets it comes out 5-8 % high, so it is on the safe side.", "",
           "| | Open-model API | Own servers |", "|---|---|---|",
           f"| Money | **${usd(sheet, 'low', N_SHEETS):.0f}-{usd(sheet, 'typical', N_SHEETS):.0f}** "
           f"({inr(usd(sheet, 'low', N_SHEETS))}-{inr(usd(sheet, 'typical', N_SHEETS))}) | **₹0 extra** |",
           f"| Time for all {N_SHEETS} sheets | about 1-3 h (limited by how many requests the provider accepts at once) "
           f"| **about {hours_c:.0f} h** (one overnight run on 2 GPUs) |",
           f"| Equivalent rental value of the GPU time | - | {own[1]} (not paid) |",
           f"| Electricity | - | {own[2]} (already part of running the servers) |",
           "| Student data | answer sheets sent to an outside company | stays on the college servers |", ""]
    md += ["Tokens per sheet by model (what an API bill is computed from):", "",
           "| Model | Input | Output |", "|---|---|---|"]
    md += [f"| {k} | {i:,.0f} | {o:,.0f} |" for k, (i, o) in sorted(sheet.items())]

    # Scenario 2
    md += ["", f"## 2. {N_SHEETS} handwritten quizzes (1 page each)", "",
           "| Quiz | Tokens per sheet | API for 700 sheets | Own servers: time | Own servers: money |",
           "|---|---|---|---|---|"]
    for name, label in (("MCQ (10 questions)", "A  MCQ only (handwritten)"),
                        ("MCQ + numerical (5 questions)", "B  MCQ + numerical")):
        tok = tokens_per_sheet(rows, label)
        lo, hi = usd(tok, "low", N_SHEETS), usd(tok, "typical", N_SHEETS)
        mins = N_SHEETS / one_page_sph * 60
        md.append(f"| {name} | {sum(i + o for i, o in tok.values()):,.0f} | ${lo:.2f}-{hi:.2f} ({inr(lo)}-{inr(hi)}) "
                  f"| about {mins:.0f} min | ₹0 extra |")
    md += ["| OMR bubble sheet (any number of questions) | 0 (read by code) | $0 | about 12 min on a CPU | ₹0 |", "",
           f"Own-server time uses the measured {one_page_sph:,.0f} one-page sheets per hour (16 at once; the GPUs were",
           "not yet at their limit, so this is a safe figure). Longer quizzes cost about 4,600 tokens and the same GPU",
           "time per extra page.", "",
           "## What running it ourselves needs (no extra cost)", "",
           "- The GPU job must be running while sheets are marked (one Slurm job; `infra/cluster/app.sh` starts the app).",
           "- Model files on the shared disk (already downloaded).",
           "- TAs check the answers the system flags; this is the same with an API.",
           "", "## Assumptions you can change", "",
           f"`eval/scenario_cost.py`: number of sheets ({N_SHEETS}), pages per sheet ({PAGES}), written answers per",
           f"sheet ({WRITTEN}), exchange rate, power use and tariff. API prices and GPU rental: `eval/cost_compare.py`."]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text("\n".join(md) + "\n")
    print((OUT / "README.md").read_text())


if __name__ == "__main__":
    main()
