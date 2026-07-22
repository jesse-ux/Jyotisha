#!/usr/bin/env python3
"""Validate the frozen public AA minute-rectification holdout contract."""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "references" / "real_case_calibration" / "minute_rectification_holdout_v2.json"
SUPPORTED_SCHEMA_VERSIONS = {
    "minute-rectification-holdout-v2",
    "minute-rectification-holdout-v3",
    "minute-rectification-holdout-v4",
}
ALLOWED_DOMAINS = {
    "education", "relocation", "relationship", "career", "finance", "health_pressure",
}
ALLOWED_PRECISIONS = {"year", "month", "day"}


def _is_public_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def _parse_event_date(value: Any, precision: Any) -> date | None:
    if not isinstance(value, str) or precision not in ALLOWED_PRECISIONS:
        return None
    try:
        if precision == "day":
            return datetime.strptime(value, "%Y-%m-%d").date()
        if precision == "month":
            return datetime.strptime(value, "%Y-%m").date()
        return datetime.strptime(value, "%Y").date()
    except ValueError:
        return None


def _case_errors(case: Any, gate: dict[str, Any]) -> list[str]:
    if not isinstance(case, dict):
        return ["case_must_be_object"]
    errors: list[str] = []
    case_id = case.get("case_id")
    if not isinstance(case_id, str) or not case_id.strip():
        errors.append("missing_case_id")
    if case.get("holdout_partition") != "sealed_evaluation":
        errors.append("case_not_in_sealed_evaluation_partition")
    if case.get("excluded_from_tuning") is not True:
        errors.append("case_not_excluded_from_tuning")

    birth = case.get("birth") if isinstance(case.get("birth"), dict) else {}
    source = birth.get("source") if isinstance(birth.get("source"), dict) else {}
    try:
        birth_date = date.fromisoformat(str(birth.get("date")))
    except ValueError:
        birth_date = None
        errors.append("invalid_birth_date")
    try:
        datetime.strptime(str(birth.get("time")), "%H:%M")
    except ValueError:
        errors.append("invalid_birth_time")
    for field, lower, upper in (("latitude", -90, 90), ("longitude", -180, 180), ("timezone_offset", -14, 14)):
        value = birth.get(field)
        if not isinstance(value, int | float) or not lower <= float(value) <= upper:
            errors.append(f"invalid_birth_{field}")
    if source.get("rodden_rating") != "AA":
        errors.append("birth_source_not_rodden_aa")
    if source.get("record_type") != "birth_record":
        errors.append("birth_source_not_record_based")
    if not _is_public_url(source.get("url")):
        errors.append("invalid_birth_source_url")
    if not isinstance(source.get("publisher"), str) or not source.get("publisher", "").strip():
        errors.append("missing_birth_source_publisher")

    events = case.get("events") if isinstance(case.get("events"), list) else []
    minimum_events = int(gate.get("events_per_case", 3))
    if len(events) < minimum_events:
        errors.append("insufficient_events")
    event_ids: list[str] = []
    domains: set[str] = set()
    source_urls: set[str] = set()
    for index, event in enumerate(events):
        prefix = f"event_{index + 1}"
        if not isinstance(event, dict):
            errors.append(f"{prefix}_must_be_object")
            continue
        event_id = event.get("id")
        if not isinstance(event_id, str) or not event_id.strip():
            errors.append(f"{prefix}_missing_id")
        else:
            event_ids.append(event_id)
        domain = event.get("domain")
        if domain not in ALLOWED_DOMAINS:
            errors.append(f"{prefix}_invalid_domain")
        else:
            domains.add(domain)
        event_date = _parse_event_date(event.get("date"), event.get("precision"))
        if event_date is None:
            errors.append(f"{prefix}_invalid_date")
        elif birth_date is not None and event_date <= birth_date:
            errors.append(f"{prefix}_not_after_birth")
        event_source = event.get("source") if isinstance(event.get("source"), dict) else {}
        source_url = event_source.get("url")
        if not _is_public_url(source_url):
            errors.append(f"{prefix}_invalid_source_url")
        else:
            source_urls.add(source_url)
            if source_url == source.get("url"):
                errors.append(f"{prefix}_source_not_independent_of_birth")
        if event_source.get("independent_of_birth_source") is not True:
            errors.append(f"{prefix}_independence_not_attested")
        if not isinstance(event_source.get("publisher"), str) or not event_source.get("publisher", "").strip():
            errors.append(f"{prefix}_missing_source_publisher")
    if len(event_ids) != len(set(event_ids)):
        errors.append("duplicate_event_ids")
    if len(domains) < int(gate.get("domains_per_case", 2)):
        errors.append("insufficient_event_domains")
    if len(source_urls) < int(gate.get("independent_event_sources_per_case", 2)):
        errors.append("insufficient_independent_event_sources")

    radius = case.get("candidate_radius_minutes")
    offsets = case.get("false_minute_offsets") if isinstance(case.get("false_minute_offsets"), list) else []
    if not isinstance(radius, int) or not 5 <= radius <= 60:
        errors.append("invalid_candidate_radius")
    valid_offsets = all(isinstance(offset, int) and offset != 0 for offset in offsets)
    if not valid_offsets or len(offsets) != len(set(offsets)):
        errors.append("invalid_false_minute_offsets")
    else:
        needed = int(gate.get("negative_minutes_per_case", 4))
        if len(offsets) < needed:
            errors.append("insufficient_false_minutes")
        if not any(offset < 0 for offset in offsets) or not any(offset > 0 for offset in offsets):
            errors.append("false_minutes_do_not_cover_both_sides")
        if not {-2, -1, 1, 2}.issubset(set(offsets)):
            errors.append("false_minutes_missing_adjacent_controls")
        if isinstance(radius, int) and any(abs(offset) > radius for offset in offsets):
            errors.append("false_minute_outside_candidate_radius")
    return errors


def _review_safeguard_errors(case: Any, gate: dict[str, Any]) -> list[str]:
    """Validate safeguards required for newly admitted v4 holdout cases."""
    if not isinstance(case, dict):
        return ["case_must_be_object"]
    errors: list[str] = []
    if not isinstance(case.get("adjudicator"), str) or not case.get("adjudicator", "").strip():
        errors.append("missing_independent_adjudicator")
    if case.get("independent_human_reviewed") is not True:
        errors.append("independent_review_not_attested")
    if case.get("frozen_before_scoring") is not True:
        errors.append("case_not_frozen_before_scoring")

    events = case.get("events") if isinstance(case.get("events"), list) else []
    day_precision_count = sum(
        isinstance(event, dict)
        and event.get("precision") == "day"
        and _parse_event_date(event.get("date"), event.get("precision")) is not None
        for event in events
    )
    if day_precision_count < int(gate.get("day_precision_events_per_case", 3)):
        errors.append("insufficient_day_precision_events")

    offsets = case.get("false_minute_offsets") if isinstance(case.get("false_minute_offsets"), list) else []
    commitments = (
        case.get("false_minute_commitments")
        if isinstance(case.get("false_minute_commitments"), list)
        else []
    )
    committed_offsets: list[int] = []
    hashes: list[str] = []
    for item in commitments:
        if not isinstance(item, dict):
            errors.append("invalid_false_minute_commitment")
            continue
        offset = item.get("offset_minutes")
        commitment_hash = item.get("commitment_hash")
        if not isinstance(offset, int) or offset == 0:
            errors.append("invalid_false_minute_commitment_offset")
        else:
            committed_offsets.append(offset)
        if (
            not isinstance(commitment_hash, str)
            or len(commitment_hash) != 64
            or any(character not in "0123456789abcdef" for character in commitment_hash.lower())
        ):
            errors.append("invalid_false_minute_commitment_hash")
        else:
            hashes.append(commitment_hash.lower())
        if any(key in item for key in ("candidate_minute", "published_minute", "birth_time")):
            errors.append("false_minute_commitment_leaks_time")
    if sorted(committed_offsets) != sorted(offsets):
        errors.append("false_minute_commitments_do_not_match_offsets")
    if len(hashes) != len(set(hashes)):
        errors.append("duplicate_false_minute_commitment_hash")
    return errors


def case_errors(case: Any, gate: dict[str, Any], *, require_review_safeguards: bool = False) -> list[str]:
    """Public case-level validator shared by frozen manifests and intake tooling."""
    errors = _case_errors(case, gate)
    if require_review_safeguards:
        errors.extend(_review_safeguard_errors(case, gate))
    return sorted(set(errors))


def validate(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    gate = manifest.get("minimum_gate") if isinstance(manifest.get("minimum_gate"), dict) else {}
    cases = manifest.get("cases") if isinstance(manifest.get("cases"), list) else []
    manifest_errors: list[str] = []
    if manifest.get("schema_version") not in SUPPORTED_SCHEMA_VERSIONS:
        manifest_errors.append("unsupported_schema_version")
    if manifest.get("truth_hidden_from_ranker") is not True:
        manifest_errors.append("truth_not_hidden_from_ranker")
    if manifest.get("frozen_before_replay") is not True:
        manifest_errors.append("benchmark_not_frozen_before_replay")
    if (
        manifest.get("schema_version") in {
            "minute-rectification-holdout-v3",
            "minute-rectification-holdout-v4",
        }
        and manifest.get("source_audit_status") != "passed_before_freeze"
    ):
        manifest_errors.append("source_content_audit_not_passed_before_freeze")
    scoring = manifest.get("frozen_scoring") if isinstance(manifest.get("frozen_scoring"), dict) else {}
    if not scoring.get("algorithm_version") or not scoring.get("implementation_sha256"):
        manifest_errors.append("missing_frozen_scoring_identity")

    seen_ids: set[str] = set()
    invalid_details: list[dict[str, Any]] = []
    valid_cases = 0
    require_review_safeguards = manifest.get("schema_version") == "minute-rectification-holdout-v4"
    for case in cases:
        errors = case_errors(case, gate, require_review_safeguards=require_review_safeguards)
        case_id = case.get("case_id") if isinstance(case, dict) else "non_object_case"
        if isinstance(case_id, str) and case_id in seen_ids:
            errors.append("duplicate_case_id")
        if isinstance(case_id, str):
            seen_ids.add(case_id)
        if errors:
            invalid_details.append({"case_id": case_id or "unnamed_case", "errors": sorted(set(errors))})
        else:
            valid_cases += 1

    needed = int(gate.get("public_aa_cases", 20))
    ready = not manifest_errors and not invalid_details and valid_cases >= needed
    return {
        "scope": "minute_rectification_holdout_validation",
        "benchmark_id": manifest.get("benchmark_id"),
        "status": "ready_for_blind_replay" if ready else "blocked_awaiting_public_aa_cases",
        "valid_public_aa_cases": valid_cases,
        "minimum_public_aa_cases": needed,
        "manifest_errors": manifest_errors,
        "invalid_cases": [item["case_id"] for item in invalid_details],
        "invalid_case_details": invalid_details,
        "verified_minute_claim_allowed": False,
        "boundary": manifest.get("boundary"),
    }


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, indent=2, sort_keys=True))
