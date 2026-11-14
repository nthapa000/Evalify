# numeric.py — deterministic numeric normalisation and comparison.
#
# Plan §4.5: "Never let an LLM decide numeric equality." Readers only
# transcribe the student's number; this module parses it and compares it with
# the teacher key using an explicit tolerance.
#
# Handles: unicode minus/dashes, thousands separators and decimal commas,
# fractions (3/4, 1 1/2, \frac{3}{4}), scientific notation (1.2e-3, 1.2×10⁻³,
# 1.2*10^-3, 1.2 x 10^(-3)), percentages, trailing units with SI conversion,
# and "x = 3.5" style answers (the value after the last "=").
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Iterable, List, Optional, Tuple

# ── Units: name → (dimension, factor to the dimension's base unit) ───────────
_UNITS = {
    # length
    "m": ("L", 1.0), "km": ("L", 1e3), "cm": ("L", 1e-2), "mm": ("L", 1e-3),
    "um": ("L", 1e-6), "μm": ("L", 1e-6), "nm": ("L", 1e-9),
    # mass
    "kg": ("M", 1.0), "g": ("M", 1e-3), "mg": ("M", 1e-6),
    # time
    "s": ("T", 1.0), "sec": ("T", 1.0), "ms": ("T", 1e-3), "us": ("T", 1e-6),
    "min": ("T", 60.0), "h": ("T", 3600.0), "hr": ("T", 3600.0),
    # force / energy / power / pressure
    "n": ("F", 1.0), "kn": ("F", 1e3),
    "j": ("E", 1.0), "kj": ("E", 1e3), "mj": ("E", 1e6), "ev": ("E", 1.602176634e-19),
    "w": ("P", 1.0), "kw": ("P", 1e3), "mw": ("P", 1e-3),
    "pa": ("Pr", 1.0), "kpa": ("Pr", 1e3), "mpa": ("Pr", 1e6), "atm": ("Pr", 101325.0),
    # electrical
    "v": ("V", 1.0), "mv": ("V", 1e-3), "kv": ("V", 1e3),
    "a": ("I", 1.0), "ma": ("I", 1e-3),
    "ohm": ("R", 1.0), "ω": ("R", 1.0), "kohm": ("R", 1e3), "kω": ("R", 1e3),
    "hz": ("Fq", 1.0), "khz": ("Fq", 1e3), "mhz": ("Fq", 1e6), "ghz": ("Fq", 1e9),
    # volume
    "l": ("Vol", 1e-3), "ml": ("Vol", 1e-6), "m3": ("Vol", 1.0), "cm3": ("Vol", 1e-6),
    # angle
    "rad": ("Ang", 1.0), "deg": ("Ang", math.pi / 180), "°": ("Ang", math.pi / 180),
    # speed / acceleration (common composite spellings)
    "m/s": ("LT-1", 1.0), "km/h": ("LT-1", 1000 / 3600), "kmph": ("LT-1", 1000 / 3600), "km/hr": ("LT-1", 1000 / 3600),
    "m/s2": ("LT-2", 1.0), "m/s^2": ("LT-2", 1.0),
    # temperature (Celsius only — Kelvin/Fahrenheit need an offset, not a factor)
    "°c": ("TempC", 1.0), "degc": ("TempC", 1.0), "celsius": ("TempC", 1.0), "c°": ("TempC", 1.0),
    # dimensionless
    "%": ("pct", 1.0),
}
# Case-sensitive units that collide when lower-cased (MW vs mW, Mpa vs mPa)
_CASE_SENSITIVE = {"MW": ("P", 1e6), "mW": ("P", 1e-3), "MHz": ("Fq", 1e6), "mHz": ("Fq", 1e-3)}

_SUPERSCRIPT = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")
_DASHES = dict.fromkeys(map(ord, "−–—‒﹣－"), "-")


@dataclass
class ParsedNumber:
    raw: str
    value: Optional[float] = None
    exact: Optional[Fraction] = None
    unit: Optional[str] = None
    ok: bool = False
    note: str = ""


@dataclass
class NumericResult:
    status: str                       # correct | wrong | unanswered | unparseable
    student_raw: str
    student_value: Optional[float] = None
    student_unit: Optional[str] = None
    matched_key: Optional[str] = None
    abs_diff: Optional[float] = None
    tolerance: float = 0.0
    flags: List[str] = field(default_factory=list)


# ── Parsing ───────────────────────────────────────────────────────────────────

def _clean(s: str) -> str:
    s = str(s).strip().translate(_DASHES)
    s = s.replace("\u2009", "").replace("\u202f", "").replace("\xa0", " ")
    # LaTeX bits a reader may emit
    s = re.sub(r"\\d?frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", r"(\1)/(\2)", s)
    s = s.replace("\\times", "*").replace("\\cdot", "*").replace("\\%", "%")
    s = s.replace("\\left", "").replace("\\right", "").replace("$", "")
    s = re.sub(r"\\(mathrm|text|operatorname)\s*\{([^{}]*)\}", r"\2", s)
    s = s.replace("{", "(").replace("}", ")")
    # "x = 3.5" / "Ans: 3.5" / "v = 2 m/s" → keep what follows the last '=' or ':'
    if "=" in s:
        s = s.rsplit("=", 1)[1]
    s = re.sub(r"^\s*(ans(wer)?|a)\s*[:.\-)]\s*", "", s, flags=re.I)
    # Superscript exponents: 10⁻³ → 10^-3
    s = re.sub(r"([0-9)])([⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺]+)", lambda m: m.group(1) + "^" + m.group(2).translate(_SUPERSCRIPT), s)
    s = re.sub(r"\s*[×xX·]\s*(?=10\s*\^?)", "*", s)          # 1.2 × 10^3 → 1.2*10^3
    s = s.strip().rstrip(".").strip()
    return s


def _split_unit(s: str) -> Tuple[str, Optional[str]]:
    m = re.match(r"^(.*?[0-9)])\s*([A-Za-zΩμω°%][A-Za-z0-9Ωμω°%/^\-]*)$", s)
    if not m:
        return s, None
    return m.group(1).strip(), m.group(2).strip()


def _number_token(tok: str, decimal_comma: bool) -> Fraction:
    tok = tok.strip().replace(" ", "")
    if "," in tok:
        if "." in tok:
            tok = tok.replace(",", "")                       # 1,234.5
        elif decimal_comma or not re.fullmatch(r"-?\d{1,3}(,\d{3})+", tok):
            tok = tok.replace(",", ".")                      # 1,5 → 1.5
        else:
            tok = tok.replace(",", "")                       # 1,234 → 1234
    return Fraction(tok)


def _eval_simple(expr: str, decimal_comma: bool) -> Fraction:
    """Evaluate a tiny grammar: [sign] mantissa [*10^exp | e exp] | a/b | w a/b."""
    expr = expr.strip()
    while expr.startswith("(") and expr.endswith(")") and expr.count("(") == 1:
        expr = expr[1:-1].strip()

    m = re.fullmatch(r"(-?\d+)\s+(\d+)\s*/\s*(\d+)", expr)           # mixed 1 1/2
    if m:
        whole, num, den = int(m.group(1)), int(m.group(2)), int(m.group(3))
        frac = Fraction(num, den)
        return whole - frac if whole < 0 or m.group(1).startswith("-") else whole + frac

    m = re.fullmatch(r"\(?([^()/]+)\)?\s*/\s*\(?([^()/]+)\)?", expr)  # a/b
    if m:
        den = _eval_simple(m.group(2), decimal_comma)
        if den == 0:
            raise ValueError("division by zero")
        return _eval_simple(m.group(1), decimal_comma) / den

    m = re.fullmatch(r"([-+]?[\d.,\s]*\d|[-+]?)\s*\*?\s*10\s*\^\s*\(?\s*([-+]?\d+)\s*\)?", expr)
    if m:                                                             # 1.2*10^-3, 10^3
        mant = m.group(1)
        mant_v = Fraction(1) if mant in ("", "+") else Fraction(-1) if mant == "-" else _number_token(mant, decimal_comma)
        return mant_v * (Fraction(10) ** int(m.group(2)))

    m = re.fullmatch(r"([-+]?[\d.,]+)[eE]([-+]?\d+)", expr)           # 1.2e-3
    if m:
        return _number_token(m.group(1), decimal_comma) * (Fraction(10) ** int(m.group(2)))

    if re.fullmatch(r"[-+]?(\d[\d,\s]*)?(\.\d+)?", expr) and re.search(r"\d", expr):
        return _number_token(expr, decimal_comma)
    raise ValueError(f"cannot parse {expr!r}")


def parse_number(raw: Any, decimal_comma: bool = False) -> ParsedNumber:
    out = ParsedNumber(raw=str(raw) if raw is not None else "")
    if raw is None or not str(raw).strip():
        out.note = "empty"
        return out
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        out.exact = Fraction(raw).limit_denominator(10**12)
        out.value, out.ok = float(raw), True
        return out

    # Whole string as a number first (so "1.2e-3" isn't read as 1.2 with unit "e-3"),
    # then number + trailing unit
    s = _clean(str(raw))
    try:
        exact, unit = _eval_simple(s, decimal_comma), None
    except (ValueError, ZeroDivisionError):
        body, unit = _split_unit(s)
        try:
            exact = _eval_simple(body, decimal_comma)
        except (ValueError, ZeroDivisionError) as e:
            out.note = str(e)
            return out
    out.exact, out.value, out.unit, out.ok = exact, float(exact), unit, True
    return out


def _unit_info(unit: Optional[str]):
    if not unit:
        return None
    if unit in _CASE_SENSITIVE:
        return _CASE_SENSITIVE[unit]
    u = unit.replace("²", "2").replace("³", "3").replace("ohms", "ohm").lower()
    return _UNITS.get(u)


# ── Key handling ──────────────────────────────────────────────────────────────

def normalise_key(key: Any) -> Tuple[List[str], float, str, Optional[str]]:
    """Return (accepted_values, tolerance, tolerance_type, unit) for any key format.

    Accepted formats:
      ["3", "3.0"]                                   legacy list (tolerance 0)
      "3.5"                                          legacy single string
      {"answer": "3.5", "tolerance": 0.01, "tolerance_type": "rel", "unit": "m"}
      {"answer": ["3.5", "7/2"], "tolerance": 0.05}
    """
    if isinstance(key, dict):
        ans = key.get("answer", key.get("values", []))
        values = ans if isinstance(ans, list) else [ans]
        return ([str(v).strip() for v in values if str(v).strip()],
                float(key.get("tolerance") or 0.0),
                str(key.get("tolerance_type") or key.get("toleranceType") or "abs"),
                key.get("unit"))
    if isinstance(key, (list, tuple)):
        return [str(v).strip() for v in key if str(v).strip()], 0.0, "abs", None
    if key is None:
        return [], 0.0, "abs", None
    return ([str(key).strip()] if str(key).strip() else []), 0.0, "abs", None


def compare(student_raw: Any, key: Any, decimal_comma: bool = False,
            require_unit: bool = False) -> NumericResult:
    """Compare one student answer with one numerical answer key."""
    accepted, tol, tol_type, key_unit = normalise_key(key)
    s_raw = "" if student_raw is None else str(student_raw).strip()
    res = NumericResult(status="unanswered", student_raw=s_raw, tolerance=tol)
    if not s_raw:
        return res

    sp = parse_number(s_raw, decimal_comma)
    res.student_value, res.student_unit = sp.value, sp.unit
    if not sp.ok:
        # Exact string match still counts (teacher may accept non-numeric forms)
        if any(_canon(s_raw) == _canon(a) for a in accepted):
            res.status, res.matched_key = "correct", s_raw
            return res
        res.status = "unparseable"
        res.flags.append("unparseable_number")
        return res

    best_diff = None
    for a in accepted:
        kp = parse_number(a, decimal_comma)
        if not kp.ok:
            if _canon(s_raw) == _canon(a):
                res.status, res.matched_key = "correct", a
                return res
            continue
        k_unit = kp.unit or key_unit
        s_val, k_val = sp.value, kp.value

        # Teacher's rule: the number as written must match the key's number in the key's unit.
        # No unit conversion ("2.5 km" for 2500 m is wrong); a missing or different unit is
        # only flagged, never penalised ("2500", "2500 m", "2500 km" all score)
        if k_unit and not sp.unit:
            if require_unit:
                res.flags.append("unit_missing")
                continue
            res.flags.append("unit_missing_lenient")
        elif sp.unit and k_unit and _unit_key(sp.unit) != _unit_key(k_unit):
            res.flags.append("unit_ignored")

        diff = abs(s_val - k_val)
        allowed = tol * abs(k_val) if tol_type.startswith("rel") else tol
        allowed += 1e-9 * max(1.0, abs(k_val))                   # inclusive edge despite float round-off
        if best_diff is None or diff < best_diff:
            best_diff = diff
        if diff <= allowed:
            res.status, res.matched_key, res.abs_diff = "correct", a, diff
            return res

    res.status, res.abs_diff = "wrong", best_diff
    return res


def _unit_key(unit: str):
    """Same unit written differently ('km/hr' = 'km/h', 'C' = '°C')? Compare by table entry, else text."""
    info = _unit_info(unit) or _unit_info("°" + unit)
    return info if info else str(unit).replace(" ", "").lower()


def _canon(s: str) -> str:
    return re.sub(r"\s+", "", str(s)).lower()


def numbers_agree(a: Any, b: Any, rel: float = 1e-6) -> Optional[bool]:
    """Do two readers' transcriptions denote the same number? None if either is unparseable."""
    pa, pb = parse_number(a), parse_number(b)
    if not (pa.ok and pb.ok):
        if _canon(str(a)) == _canon(str(b)):
            return True
        return None
    ua, ub = _unit_info(pa.unit), _unit_info(pb.unit)
    va, vb = pa.value, pb.value
    if ua and ub and ua[0] == ub[0]:
        va, vb = va * ua[1], vb * ub[1]
    return abs(va - vb) <= rel * max(1.0, abs(va), abs(vb))


def accepted_display(key: Any) -> List[str]:
    vals, tol, tol_type, unit = normalise_key(key)
    suffix = f" ±{tol*100:g}%" if tol and tol_type.startswith("rel") else (f" ±{tol:g}" if tol else "")
    return [f"{v}{(' ' + unit) if unit else ''}{suffix}" for v in vals]


def iter_keys(answer_key: dict, count: int, prefix: str = "N") -> Iterable[Tuple[str, Any]]:
    for i in range(1, count + 1):
        yield f"{prefix}{i}", answer_key.get(f"{prefix}{i}")
