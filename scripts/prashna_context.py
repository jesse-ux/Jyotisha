"""Production Prashna chart context: question moment only, Swiss backend only."""

from __future__ import annotations

from datetime import datetime
from typing import Any

try:
    from scripts.domain_calculation_service import CalculationError, compute_chart
except ModuleNotFoundError:  # pragma: no cover - CLI execution path
    from domain_calculation_service import CalculationError, compute_chart
try:
    from scripts.gulika import calculate_gulika
except ModuleNotFoundError:  # pragma: no cover - CLI execution path
    from gulika import calculate_gulika


class PrashnaContextError(ValueError):
    pass


def _timezone_offset(value: Any, moment: datetime) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        raw = value.strip().upper().replace("UTC", "")
        try:
            return float(raw)
        except ValueError:
            pass
    if moment.tzinfo is not None:
        offset = moment.utcoffset()
        if offset is not None:
            return offset.total_seconds() / 3600
    raise PrashnaContextError("timezone must be a numeric UTC offset or present in question_timestamp")


def build_prashna_context(payload: dict[str, Any]) -> dict[str, Any]:
    required = ("question_text", "question_timestamp", "lat", "lon", "timezone")
    missing = [field for field in required if payload.get(field) in (None, "")]
    if missing:
        raise PrashnaContextError(f"missing required Prashna fields: {', '.join(missing)}")
    if str(payload.get("location_convention") or "wgs84").lower() != "wgs84":
        raise PrashnaContextError("location_convention must be wgs84")
    try:
        moment = datetime.fromisoformat(str(payload["question_timestamp"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise PrashnaContextError("question_timestamp must be ISO-8601") from exc
    tz = _timezone_offset(payload["timezone"], moment)
    if moment.tzinfo is not None:
        timestamp_tz = moment.utcoffset().total_seconds() / 3600
        if abs(timestamp_tz - tz) > 0.001:
            raise PrashnaContextError("timezone conflicts with question_timestamp offset")
        moment = moment.replace(tzinfo=None)
    try:
        chart = compute_chart({
            "year": moment.year, "month": moment.month, "day": moment.day,
            "hour": moment.hour, "minute": moment.minute, "second": moment.second,
            "lat": float(payload["lat"]), "lon": float(payload["lon"]), "tz": tz,
            "ayanamsa": str(payload.get("ayanamsa") or "lahiri"),
            "node_mode": str(payload.get("node_mode") or "mean"),
        })
    except (CalculationError, ValueError, TypeError) as exc:
        raise PrashnaContextError(f"Swiss Prashna chart blocked: {exc}") from exc
    try:
        gulika = calculate_gulika(moment, lat=float(payload["lat"]), lon=float(payload["lon"]), tz=tz)
    except Exception as exc:
        gulika = {
            "status": "blocked",
            "reason": f"gulika_supporting_indicator_failed:{type(exc).__name__}",
        }
    return {
        "scope": "prashna_context",
        "status": "computed",
        "question_text": str(payload["question_text"])[:500],
        "question_timestamp": str(payload["question_timestamp"]),
        "location": {"lat": float(payload["lat"]), "lon": float(payload["lon"]), "timezone": tz, "location_convention": "wgs84"},
        "ayanamsa": str(payload.get("ayanamsa") or "lahiri"),
        "node_mode": str(payload.get("node_mode") or "mean"),
        "chart_source": "swiss_ephemeris_backend",
        "ascendant": chart["ascendant"],
        "planets": chart["planets"],
        "calculation_contract": chart["calculation_contract"],
        "result_hash": chart["result_hash"],
        "supporting_indicators": {"gulika": gulika},
        "blocked_layers": ["Trisphuta", "Kunda", "Prashna verdict"],
        "boundary": "No client-supplied planets or ascendant are accepted. Gulika is supporting-only pending external numeric parity; Sphuta and verdict layers remain blocked.",
    }
