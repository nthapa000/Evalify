# metrics.py — evaluation metrics from plan §10 (readers, graders, whole system).

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.pipeline.textdist import cer, wer  # noqa: E402

__all__ = ["cer", "wer", "over_correction", "qwk", "mae", "agreement", "system_metrics"]


def over_correction(output: str, planted: List[dict]) -> Optional[bool]:
    """PINK-style check on deliberately wrong answers: did the reader 'fix' a planted error?

    planted: [{"wrong": "2 + 2 = 5", "correct": "2 + 2 = 4"}, ...]. True if any planted
    error was rewritten into its correct form; None if the sheet has no planted errors.
    """
    if not planted:
        return None
    norm = lambda s: " ".join(s.lower().split())  # noqa: E731
    out = norm(output)
    return any(norm(p["correct"]) in out and norm(p["wrong"]) not in out for p in planted)


def qwk(a: Sequence[float], b: Sequence[float]) -> float:
    """Quadratic weighted kappa on marks rounded to half-marks."""
    a = [round(x * 2) for x in a]
    b = [round(x * 2) for x in b]
    if not a:
        return float("nan")
    lo, hi = min(a + b), max(a + b)
    n, k = len(a), hi - lo + 1
    if k == 1:
        return 1.0
    obs = [[0] * k for _ in range(k)]
    for x, y in zip(a, b):
        obs[x - lo][y - lo] += 1
    ha, hb = Counter(x - lo for x in a), Counter(y - lo for y in b)
    num = den = 0.0
    for i in range(k):
        for j in range(k):
            w = (i - j) ** 2 / (k - 1) ** 2
            num += w * obs[i][j]
            den += w * ha[i] * hb[j] / n
    return 1.0 - num / den if den else 1.0


def mae(a: Sequence[float], b: Sequence[float]) -> float:
    """Mean absolute error between two mark lists."""
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a) if a else float("nan")


def agreement(a: Sequence[float], b: Sequence[float], tol: float = 0.0) -> float:
    """Share of items whose marks differ by at most tol (0 = exact, 1 = within one mark)."""
    return sum(abs(x - y) <= tol + 1e-9 for x, y in zip(a, b)) / len(a) if a else float("nan")


def system_metrics(items: List[Dict]) -> Dict[str, float]:
    """Plan §10 system metrics over per-question items {correct: bool, routed: bool}.

    coverage         share auto-accepted (not sent to a TA)
    auto_accuracy    accuracy on auto-accepted items
    silent_error     share of ALL items that are wrong AND auto-accepted (the dangerous ones)
    routing_rate     share sent to a TA (= 1 − coverage)
    """
    n = len(items)
    if not n:
        return {}
    auto = [i for i in items if not i["routed"]]
    return {
        "items": n,
        "coverage": len(auto) / n,
        "auto_accuracy": sum(i["correct"] for i in auto) / len(auto) if auto else float("nan"),
        "silent_error": sum(not i["correct"] for i in auto) / n,
        "routing_rate": 1 - len(auto) / n,
        "raw_accuracy": sum(i["correct"] for i in items) / n,
    }
