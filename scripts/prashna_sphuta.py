"""Formula-only Prasna Marga Sphuta evidence, without verdict interpretation."""
from __future__ import annotations

from typing import Any


def _norm(value: float) -> float:
    return float(value) % 360.0


def calculate_sphuta_evidence(
    *,
    ascendant_longitude: float,
    planet_longitudes: dict[str, Any],
    gulika_longitude: float,
) -> dict[str, Any]:
    required = ("Sun", "Moon", "Rahu")
    missing = [name for name in required if name not in planet_longitudes]
    if missing:
        return {"status": "blocked", "reason": "missing_sphuta_planets", "missing": missing}
    asc = _norm(ascendant_longitude)
    moon = _norm(planet_longitudes["Moon"])
    sun = _norm(planet_longitudes["Sun"])
    rahu = _norm(planet_longitudes["Rahu"])
    gulika = _norm(gulika_longitude)
    trisphuta = _norm(asc + moon + gulika)
    catusphuta = _norm(trisphuta + sun)
    pancasphuta = _norm(catusphuta + rahu)
    return {
        "scope": "prasna_marga_sphuta_evidence",
        "status": "partial",
        "points": {
            "trisphuta": trisphuta,
            "catusphuta": catusphuta,
            "pancasphuta": pancasphuta,
        },
        "formula_trace": {
            "trisphuta": "Lagna + Moon + Gulika",
            "catusphuta": "Trisphuta + Sun",
            "pancasphuta": "Catusphuta + Rahu",
        },
        "rule_source": "references/prashna-complete-guide.md#3.2-3.3",
        "boundary": "Formula-only supporting evidence. No health, event, or Prashna verdict is permitted without external numeric parity and adjudication rules.",
    }
