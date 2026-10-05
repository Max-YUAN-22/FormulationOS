"""Structured extraction of in-vivo (ADME) numbers from DrugBank prose.

DrugBank stores ADME as curated text ("The serum half-life ... is 1.2-2 hours.
[A39092]"). Prose is great for reading, useless for computation/filtering. This
module pulls the headline number out of each field with conservative regexes:

  * half_life   -> {"min","max"} hours  (min/h/d normalised to hours)
  * protein_binding -> {"value"} percent (first percentage in the text)
  * volume_of_distribution -> {"value"} in L or L/kg (as stated)
  * clearance   -> {"min","max"} in the stated unit ("7 ± 1.3 ml/min/kg" -> 5.7..8.3)

Every result carries the raw matched snippet, and returns None when no confident
match exists ("negligibly bound") — no guessing. Pure functions, no I/O.
"""

from __future__ import annotations

import re
from typing import Any, Optional

_NUM = r"(\d+(?:\.\d+)?)"

# half-life: range "1.2-2 hours" and single "14 hours" as separate, flat patterns
_HL_RANGE = re.compile(_NUM + r"\s*(?:[-–—]|to)\s*" + _NUM + r"\s*"
                       r"(minutes?|mins?|hours?|hrs?|hr|days?)\b", re.I)      # g1 lo g2 hi g3 unit
_HL_SINGLE = re.compile(_NUM + r"\s*(minutes?|mins?|hours?|hrs?|hr|days?)\b", re.I)  # g1 v g2 unit

_UNIT_ALIASES = {
    "minutes": "min", "minute": "min", "mins": "min", "min": "min",
    "hours": "h", "hour": "h", "hrs": "h", "hr": "h", "h": "h",
    "days": "d", "day": "d", "d": "d",
}


def _num(s: str) -> Optional[float]:
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _norm_time_unit(u: str) -> Optional[str]:
    return _UNIT_ALIASES.get(u.strip().lower()) if u else None


def extract_half_life(text: str) -> Optional[dict[str, Any]]:
    """First 'N [- M] <time unit>' near a half-life mention, normalised to hours."""
    if not text:
        return None
    t = text[:400]  # headline number lives in the first sentence or two
    m = _HL_RANGE.search(t)
    matched_range = m is not None
    if not m:
        m = _HL_SINGLE.search(t)
    if not m:
        return None

    if matched_range:
        lo, hi, unit = _num(m.group(1)), _num(m.group(2)), _norm_time_unit(m.group(3))
    else:
        lo = hi = _num(m.group(1))
        unit = _norm_time_unit(m.group(2))
    if lo is None or hi is None or unit is None:
        return None

    factor = {"min": 1 / 60, "h": 1.0, "d": 24.0}[unit]
    return {
        "min": round(lo * factor, 3),
        "max": round(hi * factor, 3),
        "unit": "h",
        "raw": m.group(0).strip(),
    }


_PCT = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%")


def extract_protein_binding(text: str) -> Optional[dict[str, Any]]:
    """First percentage bound; None for qualitative-only text."""
    if not text:
        return None
    t = text[:300]
    if re.search(r"negligib|not\s+bound|minimally\s+bound", t, re.I):
        return {"value": 0.0, "raw": "negligibly/minimally bound"}
    m = _PCT.search(t)
    if not m:
        return None
    v = _num(m.group(1))
    if v is None or v > 100:
        return None
    return {"value": v, "raw": m.group(0)}


def extract_volume_of_distribution(text: str) -> Optional[dict[str, Any]]:
    """'21 L/kg', '380 L', '0.14 L/kg' -> value + as-stated unit."""
    if not text:
        return None
    m = re.search(_NUM + r"\s*(?:to\s+" + _NUM + r"\s*)?(L/kg|liters?\s*per\s*kg|L\b|liters?)",
                  text[:400], re.I)
    if not m:
        return None
    v = _num(m.group(1))
    if v is None:
        return None
    unit = "L/kg" if re.search(r"l/?kg|liter\s*per\s*kg", m.group(0), re.I) else "L"
    return {"value": v, "unit": unit, "raw": m.group(0).strip()}


_CLR_UNIT = r"(mL|L)\s*/\s*(min|hr|h|hour|s)(?:\s*/\s*kg)?"
_CLR_RANGE = re.compile(_NUM + r"\s*(±|[-–—])\s*" + _NUM + r"\s*" + _CLR_UNIT, re.I)  # g1 v g2 sep g3 hi g4 L g5 time
_CLR_SINGLE = re.compile(_NUM + r"\s*" + _CLR_UNIT, re.I)                              # g1 v g2 L g3 time


def extract_clearance(text: str) -> Optional[dict[str, Any]]:
    """'7 ± 1.3 ml/min/kg' -> 5.7..8.3; '3-13 L/h'; '625 ml/min'."""
    if not text:
        return None
    t = text[:400]
    m = _CLR_RANGE.search(t)
    if m:
        v1, sep, v2 = _num(m.group(1)), m.group(2), _num(m.group(3))
        big, time_u = m.group(4), m.group(5)
    else:
        m = _CLR_SINGLE.search(t)
        if not m:
            return None
        v1, sep, v2 = _num(m.group(1)), None, None
        big, time_u = m.group(2), m.group(3)
    if v1 is None:
        return None
    unit = f"{big.upper() if big.lower() == 'l' else big}/{time_u.lower()}"
    if re.search(r"/\s*kg", m.group(0), re.I):
        unit += "/kg"
    val: dict[str, Any] = {"unit": unit}
    if sep == "±" and v2 is not None:
        val["min"], val["max"] = round(max(0.0, v1 - v2), 4), round(v1 + v2, 4)
    elif v2 is not None:
        lo, hi = min(v1, v2), max(v1, v2)
        val["min"], val["max"] = round(lo, 4), round(hi, 4)
    else:
        val["min"] = val["max"] = v1
    val["raw"] = m.group(0).strip()
    return val


FIELD_EXTRACTORS = {
    "half_life": (extract_half_life, "half_life_h"),
    "protein_binding": (extract_protein_binding, "protein_binding_pct"),
    "volume_of_distribution": (extract_volume_of_distribution, "vd"),
    "clearance": (extract_clearance, "clearance_structured"),
}


def extract_structured(in_vivo: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    """Extract all structured ADME numbers from a profile's in_vivo prose bucket.

    Returns {structured_field_name: value_dict} — only confident matches.
    """
    out: dict[str, dict[str, Any]] = {}
    for prose_field, (fn, out_name) in FIELD_EXTRACTORS.items():
        vals = in_vivo.get(prose_field)
        if not vals:
            continue
        try:
            res = fn(str(vals[0].get("value", "")))
        except Exception:
            res = None
        if res:
            out[out_name] = res
    return out
