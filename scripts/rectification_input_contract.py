"""Stable, privacy-safe identities for birth-time rectification evidence."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any

INPUT_CONTRACT_VERSION = "rectification-input-v1"
REQUIRED_FIELDS = ("year", "month", "day", "hour", "minute", "lat", "lon", "tz")
STABILITY_OFFSETS = (-5, -2, -1, 1, 2, 5)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def canonical_birth_input(case: dict[str, Any]) -> dict[str, Any]:
    """Normalize only calculation-bearing fields using deployed defaults."""
    missing = [field for field in REQUIRED_FIELDS if case.get(field) is None]
    if missing:
        raise ValueError(f"missing rectification input fields: {', '.join(missing)}")

    year, month, day = int(case["year"]), int(case["month"]), int(case["day"])
    hour, minute, second = int(case["hour"]), int(case["minute"]), int(case.get("second", 0))
    datetime(year, month, day, hour, minute, second)
    node_mode = str(case.get("node_mode", case.get("nodeMode", "mean"))).strip().lower()
    if node_mode not in {"mean", "true"}:
        raise ValueError("node_mode must be mean or true")

    return {
        "year": year,
        "month": month,
        "day": day,
        "hour": hour,
        "minute": minute,
        "second": second,
        "lat": float(case["lat"]),
        "lon": float(case["lon"]),
        "tz": float(case["tz"]),
        "ayanamsa": str(case.get("ayanamsa", "lahiri")).strip().lower(),
        "node_mode": node_mode,
    }


def candidate_input_fingerprint(case: dict[str, Any]) -> str:
    payload = {
        "schema_version": INPUT_CONTRACT_VERSION,
        "calculation_input": canonical_birth_input(case),
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def stability_probe_contract(case: dict[str, Any]) -> dict[str, Any]:
    """Materialize adjacent-minute identities without claiming that they passed."""
    baseline = canonical_birth_input(case)
    center = datetime(
        baseline["year"],
        baseline["month"],
        baseline["day"],
        baseline["hour"],
        baseline["minute"],
        baseline["second"],
    )
    probes = []
    for offset in STABILITY_OFFSETS:
        moment = center + timedelta(minutes=offset)
        probe = {
            **baseline,
            "year": moment.year,
            "month": moment.month,
            "day": moment.day,
            "hour": moment.hour,
            "minute": moment.minute,
            "second": moment.second,
        }
        probes.append({
            "offset_minutes": offset,
            "input_fingerprint": candidate_input_fingerprint(probe),
        })
    return {
        "scope": "candidate_minute_stability_contract",
        "status": "pending_score_comparison",
        "baseline_input_fingerprint": candidate_input_fingerprint(baseline),
        "probes": probes,
        "minute_confirmation_allowed": False,
        "blocker": "public_blind_minute_holdout_not_closed",
        "boundary": (
            "Probe identities are reproducible inputs, not evidence that a minute passed "
            "stability or outcome validation."
        ),
    }


def _semantic_normalize(value: Any, *, parent_key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {
            key: _semantic_normalize(item, parent_key=key)
            for key, item in sorted(value.items())
        }
    if isinstance(value, list):
        normalized = [_semantic_normalize(item, parent_key=parent_key) for item in value]
        if parent_key in {"gives", "receives"}:
            return sorted(normalized, key=_canonical_json)
        return normalized
    return value


def semantic_evidence_hash(value: Any) -> str:
    """Hash known order-insensitive evidence while raw artifact hashes remain intact."""
    normalized = _semantic_normalize(value)
    return hashlib.sha256(_canonical_json(normalized).encode("utf-8")).hexdigest()
