"""Stable, privacy-safe input identities for birth-time rectification evidence."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any


_REQUIRED = ("year", "month", "day", "hour", "minute", "lat", "lon", "tz")
_STABILITY_OFFSETS = (-5, -2, -1, 1, 2, 5)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def canonical_birth_input(case: dict[str, Any]) -> dict[str, Any]:
    """Return the calculation-relevant input with explicit calculation settings."""
    missing = [field for field in _REQUIRED if case.get(field) is None]
    if missing:
        raise ValueError(f"missing rectification input fields: {', '.join(missing)}")
    year, month, day = int(case["year"]), int(case["month"]), int(case["day"])
    hour, minute, second = int(case["hour"]), int(case["minute"]), int(case.get("second", 0))
    datetime(year, month, day, hour, minute, second)
    return {
        "version": "rectification-input-v1",
        "birth": {
            "year": year,
            "month": month,
            "day": day,
            "hour": hour,
            "minute": minute,
            "second": second,
            "latitude": float(case["lat"]),
            "longitude": float(case["lon"]),
            "timezone": float(case["tz"]),
        },
        "ayanamsa": str(case.get("ayanamsa") or "lahiri").lower(),
        # Preserve the deployed request-level default; callers must make any
        # node-mode change explicit so it receives a different fingerprint.
        "node_mode": str(case.get("node_mode") or "true").lower(),
    }


def candidate_input_fingerprint(case: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(canonical_birth_input(case)).encode("utf-8")).hexdigest()


def stability_probe_contract(case: dict[str, Any]) -> dict[str, Any]:
    """List required local perturbations without claiming they have passed."""
    baseline = canonical_birth_input(case)
    birth = baseline["birth"]
    center = datetime(birth["year"], birth["month"], birth["day"], birth["hour"], birth["minute"], birth["second"])
    probes = []
    for offset in _STABILITY_OFFSETS:
        moment = center + timedelta(minutes=offset)
        probe = {
            "year": moment.year,
            "month": moment.month,
            "day": moment.day,
            "hour": moment.hour,
            "minute": moment.minute,
            "second": moment.second,
            "lat": birth["latitude"],
            "lon": birth["longitude"],
            "tz": birth["timezone"],
            "ayanamsa": baseline["ayanamsa"],
            "node_mode": baseline["node_mode"],
        }
        probes.append({"offset_minutes": offset, "input_fingerprint": candidate_input_fingerprint(probe)})
    return {
        "scope": "candidate_minute_stability_contract",
        "status": "pending_score_comparison",
        "baseline_input_fingerprint": candidate_input_fingerprint(case),
        "probes": probes,
        "minute_confirmation_allowed": False,
        "blocker": "public_blind_minute_holdout_not_closed",
        "boundary": "Probe identities are reproducible inputs, not evidence that a minute has passed stability or outcome validation.",
    }


def _semantic_normalize(value: Any, *, parent_key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {key: _semantic_normalize(item, parent_key=key) for key, item in sorted(value.items())}
    if isinstance(value, list):
        normalized = [_semantic_normalize(item, parent_key=parent_key) for item in value]
        if parent_key in {"gives", "receives"}:
            return sorted(normalized, key=_canonical_json)
        return normalized
    return value


def semantic_evidence_hash(value: Any) -> str:
    """Hash known order-insensitive evidence fields while retaining raw hashes elsewhere."""
    return hashlib.sha256(_canonical_json(_semantic_normalize(value)).encode("utf-8")).hexdigest()
