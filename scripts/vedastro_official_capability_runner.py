#!/usr/bin/env python3
"""Run selected official VedAstro Python capabilities through the shared bridge."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from scripts.vedastro_python_bridge import call_method as call_bridge_method
    from scripts.vedastro_python_bridge import list_capabilities as list_bridge_capabilities
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from vedastro_python_bridge import call_method as call_bridge_method
    from vedastro_python_bridge import list_capabilities as list_bridge_capabilities


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
BRIDGE = ROOT / "scripts" / "vedastro_python_bridge.py"
STUB_ENV = "VEDASTRO_OFFICIAL_CAPABILITY_RUNNER_STUB"
CATALOG_STUB_ENV = "VEDASTRO_OFFICIAL_CAPABILITY_CATALOG_STUB"
PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu", "Ascendant"]
HOUSES = [f"House{i}" for i in range(1, 13)]
DEFAULT_SIGIL_SAMPLE_LIMIT = int(os.environ.get("VEDASTRO_FULL_CATALOG_SAMPLE_LIMIT", "0") or 0)
SNAPSHOT_FANOUT_ENABLED = os.environ.get("VEDASTRO_FULL_SNAPSHOT_FANOUT_ENABLED", "1").strip().lower() in {"1", "true", "yes", "on"}
DOMAIN_ORDER = [
    "career",
    "marriage",
    "wealth",
    "health",
    "education",
    "property",
    "children",
    "migration",
    "prashna",
    "rectification",
    "timing",
    "general",
    "unknown",
]
DEFAULT_DYNAMIC_THEMES = ["career", "marriage", "wealth", "rectification", "timing"]
POLICY_BUCKETS = {
    "needs_user_context": "needs_user_context_methods",
    "needs_user_text": "needs_user_text_methods",
    "needs_rectification_profile": "needs_rectification_profile_methods",
    "blocked": "blocked_methods",
}


def _method_words(method: str) -> set[str]:
    return {item.lower() for item in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|\d+", method)}


def _domain_routing_for_method(method: str, capability: dict[str, Any], parameter_strategy: str) -> dict[str, Any]:
    method_lower = method.lower()
    words = _method_words(method)
    text = " ".join(
        str(value or "")
        for value in (
            method,
            capability.get("signature"),
            capability.get("bucket"),
            " ".join(str(name) for name in capability.get("parameter_names") or []),
        )
    ).lower()
    if method_lower == "getalleventdatagroupedbytag" or "groupedbytag" in text:
        return {
            "domains": ["general"],
            "execution_policy": "auto" if parameter_strategy != "unsupported_signature" else "blocked",
            "priority": "low",
        }
    domains: set[str] = set()
    priority = "low"
    is_dasha_timing = (
        "dasa" in words
        or "dasha" in words
        or method_lower.startswith(("dasaat", "dashaat", "getdasaat", "getdashaat"))
    )

    if is_dasha_timing or any(token in text for token in ("event", "search", "timing", "transit", "gochara")):
        domains.update({"career", "marriage", "wealth", "rectification", "timing"})
        priority = "high"
    if any(token in text for token in ("marriage", "spouse", "match", "compat", "relationship", "ashtakoot", "kuta")):
        domains.add("marriage")
        priority = "high" if any(token in text for token in ("marriage", "match", "compat")) else priority
    if any(token in text for token in ("career", "profession", "job", "work", "tenth", "house10", "house 10")):
        domains.add("career")
        priority = "high"
    if any(token in text for token in ("wealth", "money", "finance", "income", "gain", "house2", "house11", "ashtakvarga")):
        domains.add("wealth")
        priority = "high" if priority == "low" else priority
    if any(token in text for token in ("health", "illness", "disease", "medical", "medicine", "hospital", "accident", "injury", "surgery")):
        domains.add("health")
        priority = "high" if any(token in text for token in ("health", "disease", "illness", "accident")) else priority
    if any(token in text for token in ("education", "school", "college", "degree", "study", "studies", "learning", "exam")):
        domains.add("education")
        priority = "high" if any(token in text for token in ("education", "degree", "exam")) else priority
    if any(token in text for token in ("property", "vehicle", "home", "house4", "house 4", "land", "realestate", "real estate", "residence")):
        domains.add("property")
        priority = "high" if any(token in text for token in ("property", "vehicle", "land")) else priority
    if any(token in text for token in ("children", "child", "progeny", "putra", "pregnancy", "fertility")):
        domains.add("children")
        priority = "high" if any(token in text for token in ("children", "progeny", "pregnancy")) else priority
    if any(token in text for token in ("foreign", "travel", "migration", "relocation", "abroad", "immigration", "journey")):
        domains.add("migration")
        priority = "high" if any(token in text for token in ("migration", "relocation", "abroad")) else priority
    if any(token in text for token in ("prashna", "horary", "questiontext", "question text", "muhurta")):
        domains.add("prashna")
        priority = "high" if any(token in text for token in ("prashna", "horary")) else priority
    if any(token in text for token in ("rectification", "appearance", "body", "height", "shape", "complexion")):
        domains.add("rectification")
        if priority == "low":
            priority = "medium"
    if any(token in text for token in ("planet", "house", "strength", "bala", "longitude", "rasi", "navamsa", "varga")):
        domains.update({"career", "marriage", "wealth"})
        if priority == "low":
            priority = "medium"

    if parameter_strategy in {"requires_user_context", "requires_user_text", "requires_rectification_profile"}:
        execution_policy = {
            "requires_user_context": "needs_user_context",
            "requires_user_text": "needs_user_text",
            "requires_rectification_profile": "needs_rectification_profile",
        }[parameter_strategy]
    elif parameter_strategy == "unsupported_signature":
        execution_policy = "blocked"
    else:
        execution_policy = "auto"

    if not domains:
        domains.add("unknown" if execution_policy == "blocked" else "general")

    blocked_reason = None
    if execution_policy == "blocked":
        blocked_reason = parameter_strategy
    elif execution_policy == "needs_user_context":
        blocked_reason = "requires_additional_user_context"
    elif execution_policy == "needs_user_text":
        blocked_reason = "requires_user_text_or_question"
    elif execution_policy == "needs_rectification_profile":
        blocked_reason = "requires_rectification_profile"

    ordered_domains = [domain for domain in DOMAIN_ORDER if domain in domains]
    return {
        "domains": ordered_domains,
        "execution_policy": execution_policy,
        "priority": priority,
        "adjudicator_use": _adjudicator_use(execution_policy, priority),
        "confidence_role": _confidence_role(execution_policy, priority),
        "blocked_reason": blocked_reason,
    }


def _adjudicator_use(execution_policy: str, priority: str) -> str:
    if execution_policy == "auto":
        return "primary_candidate" if priority == "high" else "secondary_context"
    if execution_policy in {"needs_user_context", "needs_user_text", "needs_rectification_profile"}:
        return "secondary_context"
    return "not_used"


def _confidence_role(execution_policy: str, priority: str) -> str:
    if execution_policy == "auto":
        return "confidence_support" if priority == "high" else "background_reference"
    if execution_policy in {"needs_user_context", "needs_user_text", "needs_rectification_profile"}:
        return "confidence_cap_until_context_available"
    return "blocked"


def _build_domain_routing(method_statuses: dict[str, Any]) -> dict[str, Any]:
    routing: dict[str, dict[str, Any]] = {}
    for method, status in method_statuses.items():
        if not isinstance(status, dict):
            continue
        for domain in status.get("domains") or ["general"]:
            row = routing.setdefault(
                domain,
                {
                    "method_count": 0,
                    "auto_method_count": 0,
                    "needs_user_context_count": 0,
                    "needs_user_text_count": 0,
                    "blocked_method_count": 0,
                    "high_priority_methods": [],
                },
            )
            row["method_count"] += 1
            policy = status.get("execution_policy")
            if policy == "auto":
                row["auto_method_count"] += 1
            elif policy == "needs_user_context":
                row["needs_user_context_count"] += 1
            elif policy == "needs_user_text":
                row["needs_user_text_count"] += 1
            elif policy in {"blocked", "needs_rectification_profile"}:
                row["blocked_method_count"] += 1
            if policy == "auto" and status.get("priority") == "high" and method not in row["high_priority_methods"]:
                row["high_priority_methods"].append(method)
    for row in routing.values():
        row["high_priority_methods"] = row["high_priority_methods"][:24]
    return routing


def _requested_dynamic_themes(payload: dict[str, Any]) -> list[str]:
    raw = payload.get("themes") or payload.get("theme") or DEFAULT_DYNAMIC_THEMES
    if isinstance(raw, str):
        values = [raw]
    elif isinstance(raw, list):
        values = raw
    else:
        values = DEFAULT_DYNAMIC_THEMES
    aliases = {
        "relationship": "marriage",
        "relationships": "marriage",
        "finance": "wealth",
        "money": "wealth",
        "birth_time": "rectification",
        "birth-time": "rectification",
        "birthtime": "rectification",
        "event": "timing",
        "events": "timing",
        "事业": "career",
        "婚恋": "marriage",
        "婚姻": "marriage",
        "财富": "wealth",
        "健康": "health",
        "教育": "education",
        "房产": "property",
        "子女": "children",
        "迁移": "migration",
        "问卜": "prashna",
        "卜卦": "prashna",
        "校时": "rectification",
        "应期": "timing",
    }
    themes: list[str] = []
    for value in values:
        key = aliases.get(str(value).strip().lower(), str(value).strip().lower())
        if key in DOMAIN_ORDER and key not in themes:
            themes.append(key)
    return themes or list(DEFAULT_DYNAMIC_THEMES)


def _method_priority_score(method: str, status: dict[str, Any], theme: str) -> tuple[int, str]:
    policy = str(status.get("execution_policy") or "")
    priority = str(status.get("priority") or "low")
    score = 0
    if policy == "auto":
        score += 100
    elif policy == "needs_user_context":
        score += 60
    elif policy in {"needs_user_text", "needs_rectification_profile"}:
        score += 45
    else:
        score += 10
    if priority == "high":
        score += 40
    elif priority == "medium":
        score += 20
    if status.get("status") == "ok":
        score += 12
    if status.get("executed") is True:
        score += 8
    if theme in status.get("domains", []):
        score += 5
    method_lower = method.lower()
    if any(token in method_lower for token in ("searchevents", "eventsatrange", "eventsattime", "geteventtiming")):
        score += 10
    if theme == "career" and any(token in method_lower for token in ("dashamamsha", "profession", "career", "tenth")):
        score += 8
    if theme == "marriage" and any(token in method_lower for token in ("match", "marriage", "spouse", "ashtakoot")):
        score += 8
    if theme == "wealth" and any(token in method_lower for token in ("wealth", "money", "income", "gain", "ashtakvarga")):
        score += 8
    if theme == "rectification" and any(token in method_lower for token in ("birth", "appearance", "body")):
        score += 8
    if theme == "timing" and any(token in method_lower for token in ("dasa", "dasha", "event", "transit")):
        score += 8
    return (-score, method)


def _capability_reference(method: str, status: dict[str, Any], theme: str) -> dict[str, Any]:
    return {
        "citation_id": f"vedastro:{theme}:{method}",
        "method": method,
        "status": status.get("status"),
        "execution_policy": status.get("execution_policy"),
        "priority": status.get("priority"),
        "adjudicator_use": status.get("adjudicator_use"),
        "confidence_role": status.get("confidence_role"),
        "blocked_reason": status.get("blocked_reason"),
        "domains": status.get("domains") or [],
        "bucket": status.get("bucket"),
        "signature": status.get("signature"),
        "parameter_names": status.get("parameter_names") or [],
        "executed": bool(status.get("executed")),
        "source": "official_full_capability_catalog",
    }


def _build_dynamic_selection(
    method_statuses: dict[str, Any],
    domain_routing: dict[str, Any],
    requested_themes: list[str],
    *,
    limit: int = 12,
) -> dict[str, Any]:
    selection: dict[str, Any] = {}
    for theme in requested_themes:
        candidates = [
            (method, status)
            for method, status in method_statuses.items()
            if isinstance(status, dict) and theme in (status.get("domains") or [])
        ]
        candidates.sort(key=lambda item: _method_priority_score(item[0], item[1], theme))
        selected = [
            _capability_reference(method, status, theme)
            for method, status in candidates
            if status.get("execution_policy") == "auto"
        ][:limit]
        policy_groups: dict[str, list[dict[str, Any]]] = {
            "needs_user_context_methods": [],
            "needs_user_text_methods": [],
            "needs_rectification_profile_methods": [],
            "blocked_methods": [],
        }
        for method, status in candidates:
            bucket_name = POLICY_BUCKETS.get(str(status.get("execution_policy") or ""))
            if bucket_name and len(policy_groups[bucket_name]) < limit:
                policy_groups[bucket_name].append(_capability_reference(method, status, theme))
        citation_ids = [item["citation_id"] for item in selected]
        selection[theme] = {
            "requested_theme": theme,
            "selection_policy": "official_catalog_theme_top_n",
            "domain_summary": domain_routing.get(theme) or {},
            "selected_methods": selected,
            **policy_groups,
            "report_reference": {
                "theme": theme,
                "citation_ids": citation_ids,
                "auto_count": len(selected),
                "needs_user_context_count": len(policy_groups["needs_user_context_methods"]),
                "needs_user_text_count": len(policy_groups["needs_user_text_methods"]),
                "needs_rectification_profile_count": len(policy_groups["needs_rectification_profile_methods"]),
                "blocked_count": len(policy_groups["blocked_methods"]),
                "boundary": "Citations identify official VedAstro capability evidence used or requested by the workflow; skipped or context-dependent methods are not treated as executed evidence.",
            },
        }
    return selection


def schema() -> dict[str, Any]:
    return {
        "runner": "vedastro_official_capability_runner",
        "primary_source": "vedastro_python_bridge",
        "operations": ["run_bucket", "run_selected_methods", "run_snapshot_bundle", "run_full_capability_catalog"],
        "request_contract": ["methods_json", "birth_json", "bundle?"],
        "response_contract": ["summary", "results", "result?"],
    }


def _normalize_tz(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return "+00:00"
    sign = "+" if float(value) >= 0 else "-"
    absolute = abs(float(value))
    hours = int(absolute)
    minutes = int(round((absolute - hours) * 60))
    return f"{sign}{hours:02d}:{minutes:02d}"


def _bridge_time(case: dict[str, Any], date_text: str, *, hour: int | None = None, minute: int | None = None) -> dict[str, Any]:
    year, month, day = str(date_text).split("-")
    return {
        "__vedastro_type__": "Time",
        "year": int(year),
        "month": int(month),
        "day": int(day),
        "hour": int(case.get("hour", 0) if hour is None else hour),
        "minute": int(case.get("minute", 0) if minute is None else minute),
        "offset": _normalize_tz(case.get("tz")),
        "geolocation": {
            "__vedastro_type__": "GeoLocation",
            "location_name": "UserLocation",
            "longitude": case.get("lon"),
            "latitude": case.get("lat"),
        },
    }


def _reference_date(case: dict[str, Any]) -> str:
    for key in ("reference_date", "today", "transit_date", "current_date"):
        value = case.get(key)
        if value:
            return str(value)[:10]
    return datetime.utcnow().strftime("%Y-%m-%d")


def _build_method_payload(method: str, case: dict[str, Any]) -> dict[str, Any] | None:
    birth_date = f"{int(case['year']):04d}-{int(case['month']):02d}-{int(case['day']):02d}"
    birth_time = _bridge_time(case, birth_date)
    ref_date = _reference_date(case)
    check_time = _bridge_time(case, ref_date)
    start_of_year = f"{ref_date[:4]}-01-01"
    end_of_year = f"{ref_date[:4]}-12-31"

    if method == "GetAllEventDataGroupedByTag":
        return {}
    if method == "DasaAtTime":
        return {"args": [birth_time, check_time, 3]}
    if method == "GetCharaDasaAtTime":
        return {"args": [birth_time, check_time]}
    if method == "DasaAtRange":
        return {"args": [birth_time, _bridge_time(case, start_of_year, hour=0, minute=0), _bridge_time(case, end_of_year, hour=23, minute=59), 3, 100]}
    if method in {"AllPlanetStrength", "AshtakvargaLifeMap"}:
        return {"args": [birth_time]}
    if method == "AllPlanetData":
        return {"args": [{"__vedastro_enum__": "PlanetName", "value": "Sun"}, birth_time]}
    if method == "AllHouseData":
        return {"args": [{"__vedastro_enum__": "HouseName", "value": "House1"}, birth_time]}
    return None


def _method_payload_for_instance(method: str, case: dict[str, Any], identity: str | None = None) -> dict[str, Any] | None:
    payload = _build_method_payload(method, case)
    if payload is None:
        return None
    if method == "AllPlanetData" and identity:
        return {"args": [{"__vedastro_enum__": "PlanetName", "value": str(identity)}, payload["args"][1]]}
    if method == "AllHouseData" and identity:
        return {"args": [{"__vedastro_enum__": "HouseName", "value": str(identity)}, payload["args"][1]]}
    return payload


def _call_bridge(method: str, payload: dict[str, Any]) -> dict[str, Any]:
    return call_bridge_method(method, payload)


def _list_official_capabilities() -> dict[str, Any]:
    stub_raw = os.environ.get(CATALOG_STUB_ENV, "").strip()
    if stub_raw:
        payload = json.loads(stub_raw)
        payload.setdefault("source", "stubbed_official_capability_catalog")
        return payload
    return list_bridge_capabilities()


def run_selected_methods(methods: list[str], birth_payload: dict[str, Any]) -> dict[str, Any]:
    stub_raw = os.environ.get(STUB_ENV, "").strip()
    stub_map = json.loads(stub_raw) if stub_raw else {}
    results: dict[str, Any] = {}
    ok_count = 0
    skipped_count = 0
    for method in methods:
        if method in stub_map:
            results[method] = stub_map[method]
        else:
            payload = _build_method_payload(method, birth_payload)
            if payload is None:
                results[method] = {"available": False, "status": "unsupported_signature"}
                skipped_count += 1
                continue
            results[method] = _call_bridge(method, payload)
        if results[method].get("status") == "ok":
            ok_count += 1

    return {
        "runner": "vedastro_official_capability_runner",
        "primary_source": "vedastro_python_bridge",
        "summary": {
            "requested_method_count": len(methods),
            "executed_method_count": len(results),
            "ok_count": ok_count,
            "skipped_count": skipped_count,
        },
        "results": results,
    }


def _sample_identity_for_method(method: str, parameter_names: list[str]) -> Any:
    lowered = [name.lower() for name in parameter_names]
    if "planetname" in lowered or "inputplanet" in lowered or "planet" in lowered:
        return "Sun"
    if "housename" in lowered:
        return "House1"
    if "housenumber" in lowered or "inputhousenumber" in lowered:
        return 1
    if "inputhouse" in lowered or "house" in lowered:
        return "House1"
    if "zodiacname" in lowered or "signname" in lowered or "inputsign" in lowered or "zodiacsign" in lowered:
        return "Aries"
    if "constellation" in lowered:
        return "Aswini"
    if "divisionalno" in lowered:
        return 9
    if "longitude" in lowered or "longitudedeg" in lowered or "totaldegrees" in lowered:
        return 3.5
    return None


def _full_catalog_method_payload(method: str, capability: dict[str, Any], case: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    parameter_names = [str(name) for name in capability.get("parameter_names") or []]
    lowered = [name.lower() for name in parameter_names]
    bucket = str(capability.get("bucket") or "")
    birth_date = f"{int(case['year']):04d}-{int(case['month']):02d}-{int(case['day']):02d}"
    birth_time = _bridge_time(case, birth_date)
    ref_date = _reference_date(case)
    check_time = _bridge_time(case, ref_date)
    start_of_year = _bridge_time(case, f"{ref_date[:4]}-01-01", hour=0, minute=0)
    end_of_year = _bridge_time(case, f"{ref_date[:4]}-12-31", hour=23, minute=59)

    if not parameter_names:
        return {}, "auto_zero_arg"
    if bucket in {"time_only", "(inputTime)", "(queryTime)", "(time1)"} or lowered in (["time"], ["inputtime"], ["querytime"], ["time1"]):
        key = parameter_names[0]
        return {"kwargs": {key: check_time}}, "auto_time_only"
    if bucket == "birth_time_only" or lowered == ["birthtime"]:
        return {"kwargs": {parameter_names[0]: birth_time}}, "auto_birth_time_only"
    if bucket == "planet_time" or lowered == ["planetname", "time"]:
        return {"args": [{"__vedastro_enum__": "PlanetName", "value": "Sun"}, birth_time]}, "auto_planet_time"
    if bucket == "planet_alias_time" or lowered == ["planet", "time"]:
        return {"args": [{"__vedastro_enum__": "PlanetName", "value": "Sun"}, birth_time]}, "auto_planet_time"
    if bucket == "house_name_time" or lowered == ["housename", "time"]:
        return {"args": [{"__vedastro_enum__": "HouseName", "value": "House1"}, birth_time]}, "auto_house_name_time"
    if bucket == "house_number_time" or lowered == ["housenumber", "time"]:
        return {"args": [1, birth_time]}, "auto_house_number_time"
    if bucket == "dasha_at_time" or lowered == ["birthtime", "checktime", "levels"]:
        return {"args": [birth_time, check_time, 3]}, "auto_dasha_at_time"
    if bucket == "dasha_at_range" or lowered == ["birthtime", "starttime", "endtime", "levels", "precisionhours"]:
        return {"args": [birth_time, start_of_year, end_of_year, 3, 100]}, "auto_dasha_at_range"

    if lowered == ["birthtime", "checktime"]:
        return {"args": [birth_time, check_time]}, "auto_birth_check_time"
    if lowered == ["birthtime", "levels"]:
        return {"args": [birth_time, 3]}, "auto_birth_levels"
    if lowered == ["birthtime", "scanyear"]:
        return {"args": [birth_time, int(ref_date[:4])]}, "auto_birth_scan_year"
    if lowered == ["birthtime", "querytime"]:
        return {"args": [birth_time, check_time]}, "auto_birth_query_time"
    if lowered == ["birthtime", "sortbyweight"]:
        return {"args": [birth_time, False]}, "auto_birth_bool"
    if lowered == ["birthtime", "filtertags", "sortbyweight"]:
        return {"args": [birth_time, [], False]}, "auto_birth_filter_tags"
    if lowered == ["birthtime", "starttime", "endtime", "eventtaglist", "precisionhours"]:
        return {"args": [birth_time, start_of_year, end_of_year, ["Marriage"], 100]}, "auto_events_range"
    if lowered == ["birthtime", "checktime", "eventtaglist"]:
        return {"args": [birth_time, check_time, ["Marriage"]]}, "auto_events_time"
    if lowered == ["birthtime", "attime", "eventtaglist"]:
        return {"args": [birth_time, check_time, ["Marriage"]]}, "auto_search_events"

    if len(parameter_names) == 1:
        sample = _sample_identity_for_method(method, parameter_names)
        if sample is not None:
            return {"args": [sample]}, "auto_single_sample"
    if len(parameter_names) == 2 and any(name in lowered for name in ("time", "inputtime", "birthtime")):
        sample = _sample_identity_for_method(method, parameter_names)
        if sample is not None:
            args = []
            for name in lowered:
                if name in {"time", "inputtime", "birthtime"}:
                    args.append(birth_time)
                else:
                    args.append(sample)
            return {"args": args}, "auto_two_arg_sample"

    if any(name in lowered for name in ("malebirthtime", "femalebirthtime", "partnerbirthtime", "personb", "personbirthtime")):
        return None, "requires_user_context"
    if any(name in lowered for name in ("bodyheight", "bodyshape", "hair", "lips", "nose", "complexion", "faceshape", "constitution", "personality")):
        return None, "requires_rectification_profile"
    if any(name in lowered for name in ("rawtextdata", "birthdatarawtext", "inputtext", "textinput", "query", "questiontext", "question", "fullname", "personfullname", "address", "locationname", "ipaddress")):
        return None, "requires_user_text"
    return None, "unsupported_signature"


def run_full_capability_catalog(birth_payload: dict[str, Any]) -> dict[str, Any]:
    catalog = _list_official_capabilities()
    capabilities = catalog.get("capabilities") if isinstance(catalog.get("capabilities"), list) else []
    buckets = catalog.get("buckets") if isinstance(catalog.get("buckets"), dict) else {}
    stub_raw = os.environ.get(STUB_ENV, "").strip()
    stub_map = json.loads(stub_raw) if stub_raw else {}
    method_statuses: dict[str, Any] = {}
    bucket_statuses: dict[str, dict[str, int]] = {}
    executed_count = 0
    ok_count = 0
    unsupported_count = 0
    blocked_count = 0
    sample_limit = max(0, int(os.environ.get("VEDASTRO_FULL_CATALOG_SAMPLE_LIMIT", str(DEFAULT_SIGIL_SAMPLE_LIMIT)) or 0))

    for capability in capabilities:
        method = str(capability.get("method") or "")
        if not method:
            continue
        bucket = str(capability.get("bucket") or "unknown")
        payload, strategy = _full_catalog_method_payload(method, capability, birth_payload)
        routing_meta = _domain_routing_for_method(method, capability, strategy)
        bucket_row = bucket_statuses.setdefault(bucket, {"total": 0, "executed": 0, "ok": 0, "unsupported": 0, "blocked": 0})
        bucket_row["total"] += 1

        if payload is None:
            unsupported_count += 1
            bucket_row["unsupported"] += 1
            method_statuses[method] = {
                "status": strategy,
                "bucket": bucket,
                "signature": capability.get("signature"),
                "parameter_names": capability.get("parameter_names") or [],
                "executed": False,
                **routing_meta,
            }
            continue

        if executed_count >= sample_limit and method not in stub_map:
            blocked_count += 1
            bucket_row["blocked"] += 1
            method_statuses[method] = {
                "status": "skipped_by_sample_limit",
                "bucket": bucket,
                "signature": capability.get("signature"),
                "parameter_names": capability.get("parameter_names") or [],
                "executed": False,
                "parameter_strategy": strategy,
                **routing_meta,
            }
            continue

        if method in stub_map:
            report = stub_map[method]
        else:
            report = _call_bridge(method, payload)
        status = str(report.get("status") or "blocked")
        executed_count += 1
        bucket_row["executed"] += 1
        if status == "ok":
            ok_count += 1
            bucket_row["ok"] += 1
        else:
            blocked_count += 1
            bucket_row["blocked"] += 1
        method_statuses[method] = {
            "status": status,
            "bucket": bucket,
            "signature": capability.get("signature"),
            "parameter_names": capability.get("parameter_names") or [],
            "executed": True,
            "parameter_strategy": strategy,
            "available": bool(report.get("available")),
            "source": report.get("source"),
            **routing_meta,
        }

    overall_status = "blocked"
    if capabilities:
        overall_status = "ok" if unsupported_count == 0 and blocked_count == 0 else "partial"
    domain_routing = _build_domain_routing(method_statuses)
    requested_themes = _requested_dynamic_themes(birth_payload)
    dynamic_selection = _build_dynamic_selection(method_statuses, domain_routing, requested_themes)
    unknown_method_count = sum(
        1
        for status in method_statuses.values()
        if isinstance(status, dict) and status.get("domains") == ["unknown"]
    )
    misrouted_general_method_count = sum(
        1
        for status in method_statuses.values()
        if isinstance(status, dict)
        and "general" in (status.get("domains") or [])
        and len(status.get("domains") or []) > 1
    )

    return {
        "runner": "vedastro_official_capability_runner",
        "primary_source": "vedastro_python_bridge",
        "bundle": "official_full_capability_catalog",
        "available": bool(capabilities),
        "status": overall_status,
        "summary": {
            "catalog_method_count": len(capabilities),
            "official_callable_count": sum(1 for item in capabilities if item.get("callable")),
            "signature_bucket_count": len(buckets),
            "executed_method_count": executed_count,
            "ok_method_count": ok_count,
            "unsupported_method_count": unsupported_count,
            "blocked_method_count": blocked_count,
            "unknown_method_count": unknown_method_count,
            "misrouted_general_method_count": misrouted_general_method_count,
            "sample_limit": sample_limit,
            "domain_routing_count": len(domain_routing),
            "dynamic_selection_theme_count": len(dynamic_selection),
        },
        "coverage": {
            "source_mode": "official_full_capability_catalog",
            "catalog_source": catalog.get("source") or "vedastro_python_bridge",
            "python_bin": catalog.get("python_bin"),
            "bucket_count": len(buckets),
            "safe_sampling": True,
            "not_user_exposed": True,
            "lightweight_domain_mapping": True,
            "dynamic_theme_selection": True,
        },
        "domain_routing": domain_routing,
        "dynamic_selection": dynamic_selection,
        "bucket_statuses": bucket_statuses,
        "method_statuses": method_statuses,
    }


def run_snapshot_bundle(bundle: str, birth_payload: dict[str, Any]) -> dict[str, Any]:
    if bundle == "official_full_capability_catalog":
        return run_full_capability_catalog(birth_payload)

    if bundle != "official_full_snapshot":
        return {
            "runner": "vedastro_official_capability_runner",
            "bundle": bundle,
            "available": False,
            "status": "unsupported_bundle",
        "reason": f"Unsupported bundle: {bundle}",
        }

    stub_raw = os.environ.get(STUB_ENV, "").strip()
    stub_map = json.loads(stub_raw) if stub_raw else {}
    stub_mode = bool(stub_raw)
    snapshot_sections: dict[str, Any] = {}
    section_statuses: dict[str, str] = {}
    coverage_sections: list[str] = []
    ok_count = 0
    skipped_count = 0

    chart_core: dict[str, Any] = {}
    planet_statuses: dict[str, str] = {}
    for planet in PLANETS if SNAPSHOT_FANOUT_ENABLED else []:
        stub_key = f"AllPlanetData:{planet}"
        if stub_key in stub_map:
            report = stub_map[stub_key]
        elif stub_mode:
            report = {"available": False, "status": "stub_not_provided"}
        else:
            payload = _method_payload_for_instance("AllPlanetData", birth_payload, planet)
            report = {"available": False, "status": "unsupported_signature"} if payload is None else _call_bridge("AllPlanetData", payload)
        status = str(report.get("status") or "blocked")
        planet_statuses[planet] = "ok" if status == "ok" else status
        if status == "ok":
            ok_count += 1
        else:
            skipped_count += 1
        chart_core[planet] = {
            "Status": "Pass" if status == "ok" else "Fail",
            "Payload": {"AllPlanetData": report.get("result")} if status == "ok" else report,
        }
    if chart_core:
        snapshot_sections["chart_core"] = chart_core
        section_statuses["chart_core"] = "ok" if all(value == "ok" for value in planet_statuses.values()) else "partial"
        section_statuses["chart_core_fanout"] = planet_statuses
        if section_statuses["chart_core"] == "ok":
            coverage_sections.append("chart_core")

    house_core: dict[str, Any] = {}
    house_statuses: dict[str, str] = {}
    for house in HOUSES if SNAPSHOT_FANOUT_ENABLED else []:
        stub_key = f"AllHouseData:{house}"
        if stub_key in stub_map:
            report = stub_map[stub_key]
        elif stub_mode:
            report = {"available": False, "status": "stub_not_provided"}
        else:
            payload = _method_payload_for_instance("AllHouseData", birth_payload, house)
            report = {"available": False, "status": "unsupported_signature"} if payload is None else _call_bridge("AllHouseData", payload)
        status = str(report.get("status") or "blocked")
        house_statuses[house] = "ok" if status == "ok" else status
        if status == "ok":
            ok_count += 1
        else:
            skipped_count += 1
        house_core[house] = {
            "Status": "Pass" if status == "ok" else "Fail",
            "Payload": {"AllHouseData": report.get("result")} if status == "ok" else report,
        }
    if house_core:
        snapshot_sections["house_core"] = house_core
        section_statuses["house_core"] = "ok" if all(value == "ok" for value in house_statuses.values()) else "partial"
        section_statuses["house_core_fanout"] = house_statuses
        if section_statuses["house_core"] == "ok":
            coverage_sections.append("house_core")

    scalar_methods = [
        ("dasha_all", "DasaAtRange", "DasaAtRange"),
        ("vimshottari_now", "DasaAtTime", "DasaAtTime"),
        ("chara_dasha_now", "GetCharaDasaAtTime", "GetCharaDasaAtTime"),
        ("shadbala", "AllPlanetStrength", "AllPlanetStrength"),
        ("ashtakavarga", "AshtakvargaLifeMap", "AshtakvargaLifeMap"),
    ]
    for section_name, method, payload_key in scalar_methods:
        if method in stub_map:
            report = stub_map[method]
        elif stub_mode:
            report = {"available": False, "status": "stub_not_provided"}
        else:
            payload = _method_payload_for_instance(method, birth_payload)
            report = {"available": False, "status": "unsupported_signature"} if payload is None else _call_bridge(method, payload)
        status = str(report.get("status") or "blocked")
        section_statuses[section_name] = "ok" if status == "ok" else status
        if status == "ok":
            ok_count += 1
            coverage_sections.append(section_name)
        else:
            skipped_count += 1
        snapshot_sections[section_name] = {
            "Status": "Pass" if status == "ok" else "Fail",
            "Payload": {payload_key: report.get("result")} if status == "ok" else report,
        }

    overall_status = "blocked"
    if coverage_sections:
        overall_status = "ok" if len(coverage_sections) == 7 else "partial"

    return {
        "runner": "vedastro_official_capability_runner",
        "primary_source": "vedastro_python_bridge",
        "bundle": bundle,
        "available": bool(coverage_sections),
        "status": overall_status,
        "summary": {
            "requested_method_count": (len(PLANETS) + len(HOUSES) if SNAPSHOT_FANOUT_ENABLED else 0) + len(scalar_methods),
            "executed_method_count": (len(PLANETS) + len(HOUSES) if SNAPSHOT_FANOUT_ENABLED else 0) + len(scalar_methods),
            "ok_count": ok_count,
            "skipped_count": skipped_count,
            "fanout_enabled": SNAPSHOT_FANOUT_ENABLED,
        },
        "result": {
            "snapshot_sections": snapshot_sections,
            "section_statuses": section_statuses,
            "coverage": {
                "source_mode": "official_capability_runner_bundle",
                "filled_sections": coverage_sections,
                "planet_count": len(chart_core),
                "house_count": len(house_core),
                "fanout_enabled": SNAPSHOT_FANOUT_ENABLED,
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--print-schema", action="store_true")
    parser.add_argument("--methods-json", default="[]")
    parser.add_argument("--birth-json", default="{}")
    parser.add_argument("--bundle", default="")
    args = parser.parse_args()

    if args.print_schema:
        result = schema()
    elif args.bundle:
        birth_payload = json.loads(args.birth_json or "{}")
        result = run_snapshot_bundle(args.bundle, birth_payload)
    else:
        methods = json.loads(args.methods_json or "[]")
        birth_payload = json.loads(args.birth_json or "{}")
        result = run_selected_methods(methods, birth_payload)

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
