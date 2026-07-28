from __future__ import annotations

import math
import re
import uuid
from datetime import date
from typing import Any, Literal, NotRequired, TypedDict, cast

DatePrecision = Literal["day", "month", "quarter", "year", "range"]

SCOREABLE_EVENT_KINDS: dict[str, frozenset[str]] = {
    "education": frozenset({"education_milestone"}),
    "relocation": frozenset({"relocation"}),
    "relationship": frozenset({"relationship_start", "relationship_end", "relationship_change"}),
    "career": frozenset({"career_change"}),
    "finance": frozenset({"finance_change"}),
    "health_pressure": frozenset({"self_health_event"}),
}
DATE_PRECISIONS = frozenset({"day", "month", "quarter", "year", "range"})
_REQUEST_FIELDS = frozenset({"birth_date", "start_time", "end_time", "lat", "lon", "tz", "events"})
_EVENT_FIELDS = frozenset({"id", "domain", "event_kind", "date_start", "date_end", "precision", "summary"})
_CLOCK = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d\Z")


class LifeEvent(TypedDict):
    id: str
    domain: str
    event_kind: str
    date_start: str
    date_end: str
    precision: DatePrecision
    summary: NotRequired[str]


class RectificationRequest(TypedDict):
    birth_date: str
    start_time: str
    end_time: str
    lat: float
    lon: float
    tz: float
    events: list[LifeEvent]


JsonObject = dict[str, Any]


def _bounded_number(body: dict[str, Any], name: str, minimum: float, maximum: float) -> float:
    value = body.get(name)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{name} must be a finite number")
    result = float(value)
    if not minimum <= result <= maximum:
        raise ValueError(f"{name} must be between {minimum:g} and {maximum:g}")
    return result


def _calendar_date(value: Any, label: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a valid YYYY-MM-DD value")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a valid YYYY-MM-DD value") from exc


def normalize_rectification_request(body: Any, *, today: date | None = None) -> RectificationRequest:
    if not isinstance(body, dict):
        raise ValueError("request body must be an object")
    unsupported = sorted(set(body) - _REQUEST_FIELDS)
    if unsupported:
        raise ValueError(f"unsupported rectification field: {unsupported[0]}")

    birth_day = _calendar_date(body.get("birth_date"), "birth_date")
    start_time, end_time = body.get("start_time"), body.get("end_time")
    if not isinstance(start_time, str) or not _CLOCK.fullmatch(start_time):
        raise ValueError("start_time must be HH:MM")
    if not isinstance(end_time, str) or not _CLOCK.fullmatch(end_time):
        raise ValueError("end_time must be HH:MM")
    if start_time > end_time:
        raise ValueError("start_time must not exceed end_time")

    events = body.get("events")
    if not isinstance(events, list) or not 1 <= len(events) <= 100:
        raise ValueError("events must contain between 1 and 100 items")
    upper_date = today or date.today()
    cleaned_events: list[LifeEvent] = []
    for index, raw_event in enumerate(events):
        if not isinstance(raw_event, dict):
            raise ValueError(f"events[{index}] must be an object")
        unsupported_event_fields = sorted(set(raw_event) - _EVENT_FIELDS)
        if unsupported_event_fields:
            raise ValueError(f"events[{index}] contains unsupported field: {unsupported_event_fields[0]}")
        try:
            event_id = str(uuid.UUID(str(raw_event.get("id") or "")))
        except (ValueError, AttributeError) as exc:
            raise ValueError(f"events[{index}].id must be a UUID") from exc
        domain, event_kind = raw_event.get("domain"), raw_event.get("event_kind")
        if domain not in SCOREABLE_EVENT_KINDS:
            raise ValueError(f"events[{index}].domain is not scoreable")
        if event_kind not in SCOREABLE_EVENT_KINDS[cast(str, domain)]:
            raise ValueError(f"events[{index}].event_kind does not match domain")
        precision = raw_event.get("precision")
        if precision not in DATE_PRECISIONS:
            raise ValueError(f"events[{index}].precision is invalid")
        start_day = _calendar_date(raw_event.get("date_start"), f"events[{index}].date_start")
        end_day = _calendar_date(raw_event.get("date_end"), f"events[{index}].date_end")
        if start_day > end_day:
            raise ValueError(f"events[{index}].date_start must not exceed date_end")
        if start_day < birth_day or end_day > upper_date:
            raise ValueError(f"events[{index}] dates must be between birth_date and today")
        summary = raw_event.get("summary", "")
        if not isinstance(summary, str) or len(summary) > 1_000:
            raise ValueError(f"events[{index}].summary must be a string up to 1000 characters")
        cleaned_events.append({
            "id": event_id,
            "domain": cast(str, domain),
            "event_kind": cast(str, event_kind),
            "date_start": start_day.isoformat(),
            "date_end": end_day.isoformat(),
            "precision": cast(DatePrecision, precision),
            "summary": summary.strip(),
        })

    return {
        "birth_date": birth_day.isoformat(),
        "start_time": start_time,
        "end_time": end_time,
        "lat": _bounded_number(body, "lat", -90, 90),
        "lon": _bounded_number(body, "lon", -180, 180),
        "tz": _bounded_number(body, "tz", -14, 14),
        "events": cleaned_events,
    }
