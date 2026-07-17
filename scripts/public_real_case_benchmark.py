#!/usr/bin/env python3
"""Replay research-grade public events through the local Jyotish evidence stack."""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

from scripts.functional_benefics import derive_functional_benefic_malefic
from scripts.narayana_dasha import narayana_dasha_full_report


ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "scripts" / "jyotish_engine.py"
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
EVENT_HOUSES = {"career": [10, 6, 9, 11], "marriage": [7, 2, 11, 5]}
EVENT_KARAKAS = {"career": {"Sun", "Saturn", "Mercury"}, "marriage": {"Venus", "Jupiter"}}
PRIMARY_HOUSE = {"career": 10, "marriage": 7}
EXPECTED_LABEL = {"career": "career_status", "marriage": "legal_marriage"}
SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}
_ENGINE_JSON_CACHE: dict[str, dict[str, Any]] = {}


def clear_engine_cache() -> None:
    _ENGINE_JSON_CACHE.clear()


def summarize_results(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    blocked = sum(bool(row.get("blocked")) for row in rows)
    evaluated = total - blocked
    hits = sum(row.get("result_class") in {"strong_hit", "weak_hit"} for row in rows if not row.get("blocked"))
    exact = sum(bool(row.get("matched_expected_label")) for row in rows if not row.get("blocked"))
    activation_rate = hits / evaluated if evaluated else None
    strong_rate = exact / evaluated if evaluated else None
    return {
        "total_events": total,
        "evaluated_events": evaluated,
        "strong_hits": sum(row.get("result_class") == "strong_hit" for row in rows),
        "weak_hits": sum(row.get("result_class") == "weak_hit" for row in rows),
        "misses": sum(row.get("result_class") == "miss" for row in rows),
        "blocked_events": blocked,
        "known_event_activation_rate": activation_rate,
        "strong_activation_rate": strong_rate,
        "positive_event_recall": activation_rate,
        "positive_event_recall_deprecated": True,
        "exact_label_rate": strong_rate,
        "exact_label_rate_deprecated": True,
        "blocked_rate": blocked / total if total else None,
        "balanced_accuracy": None,
        "balanced_accuracy_blocked_reason": "no_verified_negative_control_dates",
    }


def promotion_decision(v1: dict[str, Any], v2: dict[str, Any]) -> dict[str, Any]:
    if int(v2.get("blocked_events") or 0) > int(v1.get("blocked_events") or 0):
        return {"promote": False, "reason": "v2_increased_blocked_events"}
    recall1 = v1.get("positive_event_recall")
    recall2 = v2.get("positive_event_recall")
    exact1 = v1.get("exact_label_rate")
    exact2 = v2.get("exact_label_rate")
    if None in {recall1, recall2, exact1, exact2}:
        return {"promote": False, "reason": "comparison_metric_missing"}
    improved = recall2 >= recall1 and exact2 >= exact1 and (recall2 > recall1 or exact2 > exact1)
    return {"promote": improved, "reason": "holdout_metrics_improved" if improved else "no_holdout_improvement"}


def compare_reports(v1: dict[str, Any], v2: dict[str, Any]) -> dict[str, Any]:
    """Compare frozen rule versions without reinterpreting holdout outcomes."""
    v1_cases = {row["case_id"]: row for row in v1.get("cases") or []}
    v2_cases = {row["case_id"]: row for row in v2.get("cases") or []}
    deltas = []
    for case_id in sorted(v1_cases.keys() & v2_cases.keys()):
        before = v1_cases[case_id]
        after = v2_cases[case_id]
        before_signals = set(before.get("signals") or [])
        deltas.append({
            "case_id": case_id,
            "v1_score": before.get("score"),
            "v2_score": after.get("score"),
            "score_delta": (after.get("score") or 0) - (before.get("score") or 0),
            "v1_result_class": before.get("result_class"),
            "v2_result_class": after.get("result_class"),
            "added_signals": sorted(set(after.get("signals") or []) - before_signals),
        })
    return {
        "benchmark_id": "public_real_case_holdout_comparison_2026_07_11",
        "boundary": "Blind positive-event holdout comparison; no negative controls and no scientific accuracy claim.",
        "v1_summary": v1.get("summary") or {},
        "v2_summary": v2.get("summary") or {},
        "promotion": promotion_decision(v1.get("summary") or {}, v2.get("summary") or {}),
        "case_deltas": deltas,
    }


def combine_reports(reports: list[dict[str, Any]], promotion: dict[str, Any]) -> dict[str, Any]:
    rows = [row for report in reports for row in report.get("cases") or []]
    return {
        "benchmark_id": "public_real_case_20_case_closure_2026_07_11",
        "rule_version": "v2",
        "method": {
            "cohorts": ["batch1_discovery_10", "frozen_holdout_10"],
            "selection": "Rodden A/AA public figures with independently dated public career or legal-marriage events",
            "score_thresholds": {"strong_hit": ">=7", "weak_hit": "4-6", "miss": "<4"},
        },
        "summary": summarize_results(rows),
        "domain_summaries": {
            domain: summarize_results([row for row in rows if row.get("domain") == domain])
            for domain in ("career", "marriage")
        },
        "holdout_promotion": promotion,
        "boundary": "Twenty positive public events; no negative controls, specificity estimate, or scientific accuracy claim.",
        "technique_audit": [
            {"technique": "D1 + Functional Benefic/Malefic", "status": "used", "scope": "20/20"},
            {"technique": "D9/UL/Darakaraka", "status": "used", "scope": "10 marriage events"},
            {"technique": "D10/A10/Amatyakaraka", "status": "used", "scope": "10 career events"},
            {"technique": "Vimshottari MD/AD", "status": "used", "scope": "20/20"},
            {"technique": "Narayana Dasha", "status": "used", "scope": "20/20"},
            {"technique": "Double Transit PAC", "status": "used", "scope": "20/20"},
            {"technique": "Rahu/Ketu dispositor", "status": "used", "scope": "v2 scoring"},
            {"technique": "Vimshottari PD/PrAD", "status": "partial", "reason": "ratio expansion available but not externally validated or scored"},
            {"technique": "Tajika/Varshaphala/Muntha", "status": "partial", "reason": "local annual layer remains simplified and external oracle closure is incomplete"},
            {"technique": "KP exact cusp/significators", "status": "partial", "reason": "current local KP house layer uses sign-center approximation rather than exact cusps"},
            {"technique": "VedAstro official raw", "status": "blocked", "reason": "official_snapshot_budget_exhausted"},
            {"technique": "PyJHora/JHora/jyotishganit parity", "status": "blocked", "reason": "external canonical raw comparison incomplete"},
            {"technique": "MEVG / Global Web Evidence", "status": "used", "scope": "20 public birth/event source pairs"},
            {"technique": "Real Case Calibration", "status": "used", "scope": "10 discovery + 10 frozen holdout"},
            {"technique": "Negative controls", "status": "blocked", "reason": "no verified non-event dates"},
        ],
        "technique_debt": {
            "vimshottari_pd_prad": "available_ratio_expansion_not_scored_or_externally_validated",
            "tajika_varshaphala_muntha": "available_experimental_not_scored_due_simplified_year_lord_and_oracle_gap",
            "kp_cusp_significators": "partial_not_scored_house_centers_are_not_precise_cusps",
            "annual_transit_to_arudha_or_ul": "untested_candidate_layer",
            "negative_control_dates": "missing_blocks_balanced_accuracy",
        },
        "cases": rows,
    }


def node_dispositor_bonus(
    active_lords: set[str],
    domain: str,
    chart: dict[str, Any],
    roles: dict[str, Any],
) -> tuple[int, list[str]]:
    event_houses = set(EVENT_HOUSES[domain])
    score = 0
    signals: list[str] = []
    planets = chart.get("planets") or {}
    for node in sorted(active_lords & {"Rahu", "Ketu"}):
        node_sign = (planets.get(node) or {}).get("sign")
        dispositor = SIGN_LORDS.get(node_sign)
        if not dispositor:
            continue
        if set((roles.get("owned_houses") or {}).get(dispositor) or []) & event_houses:
            score += 1
            signals.append(f"{node}_dispositor_{dispositor}_owns_event_house")
        occupied = (planets.get(dispositor) or {}).get("house")
        if occupied in event_houses:
            score += 1
            signals.append(f"{node}_dispositor_{dispositor}_occupies_event_house:{occupied}")
    return score, signals


def _house_from_sign(ascendant: str, target: str) -> int | None:
    if ascendant not in SIGNS or target not in SIGNS:
        return None
    return (SIGNS.index(target) - SIGNS.index(ascendant)) % 12 + 1


def varga_and_karaka_bonus(
    active_lords: set[str],
    domain: str,
    varga: dict[str, Any],
    jaimini: dict[str, Any],
) -> tuple[int, list[str]]:
    chart_key = "D10_Dasamsa" if domain == "career" else "D9_Navamsa"
    chart = ((varga.get("divisional_charts") or {}).get(chart_key) or {})
    ascendant = chart.get("ascendant")
    primary_house = PRIMARY_HOUSE[domain]
    primary_sign = SIGNS[(SIGNS.index(ascendant) + primary_house - 1) % 12] if ascendant in SIGNS else None
    primary_lord = SIGN_LORDS.get(primary_sign)
    lagna_lord = SIGN_LORDS.get(ascendant)
    score = 0
    signals: list[str] = []
    label = "D10" if domain == "career" else "D9"
    for lord in sorted(active_lords):
        if lord == lagna_lord:
            score += 1
            signals.append(f"active_dasha_matches_{label}_Lagna_lord:{lord}")
        if lord == primary_lord:
            score += 1
            signals.append(f"active_dasha_matches_{label}_{primary_house}L:{lord}")
        lord_sign = (chart.get(lord) or {}).get("sign")
        if _house_from_sign(ascendant, lord_sign) == primary_house:
            score += 1
            signals.append(f"active_dasha_occupies_{label}_house_{primary_house}:{lord}")
    karaka_name = "Amatyakaraka" if domain == "career" else "Darakaraka"
    karaka_planet = ((((jaimini.get("chara_karaka_7") or {}).get("karaka_table") or {}).get(karaka_name) or {}).get("planet"))
    if karaka_planet in active_lords:
        score += 1
        signals.append(f"active_dasha_matches_{karaka_name}:{karaka_planet}")
    return score, signals


def _engine_json(command: str, subject: dict[str, Any], *extra: str, timeout: int = 30) -> dict[str, Any]:
    cache_key = json.dumps(
        {"command": command, "subject": subject, "extra": extra},
        sort_keys=True,
        ensure_ascii=True,
        default=str,
    )
    if cache_key in _ENGINE_JSON_CACHE:
        return copy.deepcopy(_ENGINE_JSON_CACHE[cache_key])
    args = [
        sys.executable, str(ENGINE), command,
        "--year", str(subject["year"]), "--month", str(subject["month"]),
        "--day", str(subject["day"]), "--hour", str(subject["hour"]),
        "--minute", str(subject["minute"]), "--lat", str(subject["lat"]),
        "--lon", str(subject["lon"]), "--tz", str(subject["tz"]),
        "--node-mode", str(subject.get("node_mode", "mean")),
        *extra,
    ]
    completed = subprocess.run(args, cwd=ROOT, check=True, capture_output=True, text=True, timeout=timeout)
    payload = json.loads(completed.stdout)
    _ENGINE_JSON_CACHE[cache_key] = payload
    return copy.deepcopy(payload)


def _find_dasha(dasha: dict[str, Any], event_date: str) -> tuple[str | None, str | None]:
    target = date.fromisoformat(event_date)
    for md in dasha.get("timeline") or []:
        if date.fromisoformat(md["start"][:10]) <= target < date.fromisoformat(md["end"][:10]):
            for ad in md.get("antardasha_timeline") or []:
                if date.fromisoformat(ad["start"][:10]) <= target < date.fromisoformat(ad["end"][:10]):
                    return md.get("lord"), ad.get("lord")
            return md.get("lord"), None
    return None, None


def _planet_score(planet: str | None, event_houses: set[int], chart: dict[str, Any], roles: dict[str, Any], karakas: set[str]) -> tuple[int, list[str]]:
    if not planet:
        return 0, []
    score = 0
    signals: list[str] = []
    owned = set((roles.get("owned_houses") or {}).get(planet) or [])
    occupied = (chart.get("planets") or {}).get(planet, {}).get("house")
    owned_hits = sorted(owned & event_houses)
    if owned_hits:
        score += 2
        signals.append(f"{planet}_owns_event_houses:{owned_hits}")
    if occupied in event_houses:
        score += 1
        signals.append(f"{planet}_occupies_event_house:{occupied}")
    if planet in karakas:
        score += 1
        signals.append(f"{planet}_domain_karaka")
    return score, signals


def score_active_dasha_lords(
    lords: list[str | None],
    event_houses: set[int],
    chart: dict[str, Any],
    roles: dict[str, Any],
    karakas: set[str],
) -> tuple[int, list[str]]:
    score = 0
    signals: list[str] = []
    for lord in dict.fromkeys(lord for lord in lords if lord):
        points, lord_signals = _planet_score(lord, event_houses, chart, roles, karakas)
        score += points
        signals.extend(lord_signals)
    return score, signals


def _transit_json(event_date: str, subject: dict[str, Any]) -> dict[str, Any]:
    target = date.fromisoformat(event_date)
    command = [
        sys.executable, str(ENGINE), "transit",
        "--year", str(target.year), "--month", str(target.month), "--day", str(target.day),
        "--planet", "Jupiter,Saturn", "--tz", str(subject["tz"]),
        "--node-mode", str(subject.get("node_mode", "mean")),
    ]
    completed = subprocess.run(command, cwd=ROOT, check=True, capture_output=True, text=True, timeout=30)
    return json.loads(completed.stdout)


def ashtakavarga_audit(domain: str, packet: dict[str, Any], transit: dict[str, Any]) -> dict[str, Any]:
    event_houses = EVENT_HOUSES[domain]
    sav = packet.get("sav") or {}
    bav = packet.get("bav") or {}
    event_house_sav = {
        str(house): (packet.get("house_scores") or {}).get(f"house_{house}")
        for house in event_houses
    }
    transit_support = {}
    for planet in ("Jupiter", "Saturn"):
        sign = ((transit.get("planets") or {}).get(planet) or {}).get("sign")
        sign_index = SIGNS.index(sign) if sign in SIGNS else None
        bindus = ((bav.get(planet) or {}).get("bindus") or [])
        transit_support[planet] = {
            "sign": sign,
            "sav": (sav.get("scores") or {}).get(sign),
            "bav": bindus[sign_index] if sign_index is not None and sign_index < len(bindus) else None,
        }
    return {
        "status": "used_non_scoring",
        "scoring_effect": 0,
        "method": packet.get("method"),
        "version": packet.get("version"),
        "sav_total": sav.get("total"),
        "sav_valid": sav.get("valid"),
        "all_bav_valid": packet.get("all_bav_valid"),
        "event_house_sav": event_house_sav,
        "transit_support": transit_support,
        "settings": {
            "ayanamsa": transit.get("ayanamsa"),
            "node_mode": transit.get("node_mode"),
        },
        "boundary": "Audit evidence only. SAV/BAV does not change V2.1 event scores until a fresh holdout validates it.",
    }


def _narayana_at_event(subject: dict[str, Any], chart: dict[str, Any], event_date: str) -> dict[str, Any]:
    asc_sign = chart["ascendant"]["sign"]
    asc_idx = SIGNS.index(asc_sign)
    planet_lons = {name: data["degree"] for name, data in chart["planets"].items() if "degree" in data}
    born = date(subject["year"], subject["month"], subject["day"])
    target = date.fromisoformat(event_date)
    age = (target - born).days / 365.2425
    report = narayana_dasha_full_report(asc_idx, planet_lons, current_age=age, birth_year=subject["year"])
    return report.get("current_dasha") or {}


def _arudha_lord(jaimini: dict[str, Any], domain: str) -> str | None:
    arudha = jaimini.get("arudha_padas") or {}
    if domain == "career":
        return ((arudha.get("padas") or {}).get("A10") or {}).get("lord")
    return (arudha.get("upapada") or {}).get("lord")


def _double_transit_score(packet: dict[str, Any]) -> tuple[int, list[str]]:
    strengths = [row.get("strength") for row in packet.get("double_transit") or []]
    if "strong" in strengths:
        return 2, ["double_transit_pac_strong"]
    if strengths:
        return 1, ["double_transit_pac_present"]
    return 0, []


def replay_case(case: dict[str, Any], rule_version: str = "v1") -> dict[str, Any]:
    subject = case["subject"]
    event = case["event_outcomes"][0]
    domain = event["domain"]
    event_houses = set(EVENT_HOUSES[domain])
    try:
        chart = _engine_json("chart", subject)
        dasha = _engine_json("dasha", subject, "--years", "100")
        varga = _engine_json("varga", subject, "--d10" if domain == "career" else "--d9")
        jaimini = _engine_json("jaimini", subject)
        pac = _engine_json(
            "double-transit-pac", subject,
            "--date", event["event_date"], "--house", str(PRIMARY_HOUSE[domain]),
        )
    except (subprocess.SubprocessError, json.JSONDecodeError, KeyError, ValueError) as exc:
        return {
            "case_id": case["case_id"], "name": subject["name"], "domain": domain,
            "event_date": event["event_date"], "blocked": True, "result_class": "blocked",
            "matched_expected_label": False, "blocked_reason": f"{type(exc).__name__}: {exc}",
        }

    roles = derive_functional_benefic_malefic(chart["ascendant"]["sign"])
    md, ad = _find_dasha(dasha, event["event_date"])
    score = 0
    signals: list[str] = []
    if rule_version == "v2_1":
        score, signals = score_active_dasha_lords([md, ad], event_houses, chart, roles, EVENT_KARAKAS[domain])
    else:
        for lord in (md, ad):
            points, lord_signals = _planet_score(lord, event_houses, chart, roles, EVENT_KARAKAS[domain])
            score += points
            signals.extend(lord_signals)

    active_lords = {lord for lord in (md, ad) if lord}
    if rule_version in {"v2", "v2_1"}:
        node_points, node_signals = node_dispositor_bonus(active_lords, domain, chart, roles)
        varga_points, varga_signals = varga_and_karaka_bonus(active_lords, domain, varga, jaimini)
        score += node_points + varga_points
        signals.extend(node_signals)
        signals.extend(varga_signals)

    arudha_lord = _arudha_lord(jaimini, domain)
    if arudha_lord in {md, ad}:
        score += 1
        signals.append(f"active_dasha_matches_{'A10' if domain == 'career' else 'UL'}_lord:{arudha_lord}")

    narayana = _narayana_at_event(subject, chart, event["event_date"])
    narayana_md = narayana.get("md") or {}
    event_sign = SIGNS[(SIGNS.index(chart["ascendant"]["sign"]) + PRIMARY_HOUSE[domain] - 1) % 12]
    if narayana_md.get("sign") == event_sign:
        score += 2
        signals.append(f"narayana_activates_primary_event_sign:{event_sign}")
    narayana_lord = narayana_md.get("lord")
    if set((roles.get("owned_houses") or {}).get(narayana_lord) or []) & event_houses:
        score += 1
        signals.append(f"narayana_lord_owns_event_house:{narayana_lord}")

    pac_points, pac_signals = _double_transit_score(pac)
    score += pac_points
    signals.extend(pac_signals)

    ashtakavarga = {"status": "not_run", "scoring_effect": 0}
    if rule_version == "v2_1":
        try:
            ashtakavarga_packet = _engine_json("ashtakavarga", subject)
            transit_packet = _transit_json(event["event_date"], subject)
            ashtakavarga = ashtakavarga_audit(domain, ashtakavarga_packet, transit_packet)
        except (subprocess.SubprocessError, json.JSONDecodeError, KeyError, ValueError) as exc:
            ashtakavarga = {
                "status": "blocked",
                "scoring_effect": 0,
                "blocked_reason": f"{type(exc).__name__}: {exc}",
            }

    if score >= 7:
        result_class = "strong_hit"
        actual_label = EXPECTED_LABEL[domain]
    elif score >= 4:
        result_class = "weak_hit"
        actual_label = "domain_activation"
    else:
        result_class = "miss"
        actual_label = None

    return {
        "case_id": case["case_id"],
        "name": subject["name"],
        "domain": domain,
        "event_date": event["event_date"],
        "outcome": event["outcome"],
        "birth_time_rating": subject["birth_source"]["time_accuracy_rating"],
        "rule_version": rule_version,
        "blocked": False,
        "result_class": result_class,
        "score": score,
        "expected_label": EXPECTED_LABEL[domain],
        "actual_label": actual_label,
        "matched_expected_label": actual_label == EXPECTED_LABEL[domain],
        "signals": signals,
        "evidence": {
            "ascendant": chart["ascendant"],
            "vimshottari": {"mahadasha": md, "antardasha": ad},
            "narayana": narayana,
            "functional_benefic_malefic": roles,
            "domain_varga": varga,
            "arudha_lord": arudha_lord,
            "double_transit_pac": pac,
            "ashtakavarga_audit": ashtakavarga,
            "birth_source": subject["birth_source"],
            "event_source": event["source"],
        },
    }


def build_report(
    manifest: dict[str, Any],
    strict_probe_blocked_reason: str | None = None,
    rule_version: str = "v1",
) -> dict[str, Any]:
    rows = [replay_case(case, rule_version=rule_version) for case in manifest.get("cases") or []]
    return {
        "benchmark_id": "public_real_case_benchmark_2026_07_11",
        "rule_version": rule_version,
        "method": {
            "selection": "Rodden A/AA public figures with independently dated public events",
            "pre_registered_layers": ["D1", "D9_or_D10", "UL_or_A10", "Functional Benefic/Malefic", "Vimshottari MD/AD", "Narayana Dasha", "Double Transit PAC"] + (["Rahu/Ketu dispositor", "D9/D10 Lagna and primary-house lord", "Amatyakaraka/Darakaraka"] if rule_version in {"v2", "v2_1"} else []) + (["SAV/BAV non-scoring audit", "deduplicated MD/AD lord scoring"] if rule_version == "v2_1" else []),
            "score_thresholds": {"strong_hit": ">=7", "weak_hit": "4-6", "miss": "<4"},
            "boundary": "Positive-event technical activation replay; not scientific predictive accuracy.",
        },
        "summary": summarize_results(rows),
        "strict_workflow_batch": {
            "status": "blocked" if strict_probe_blocked_reason else "not_run",
            "blocked_reason": strict_probe_blocked_reason,
        },
        "external_oracle_boundary": {
            "VedAstro": "diagnostic_only_unless_official_raw_present",
            "PyJHora": "blocked_or_benchmark_only_until_dependency_available",
            "JHora": "manual_oracle_not_automated",
            "jyotishganit": "parity_contract_separate_from_this_event_replay",
        },
        "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="references/real_case_calibration/replay_manifest.json")
    parser.add_argument("--output")
    parser.add_argument("--strict-probe-blocked-reason")
    parser.add_argument("--rule-version", choices=["v1", "v2", "v2_1", "compare"], default="v1")
    parser.add_argument("--comparison-v1")
    parser.add_argument("--comparison-v2")
    args = parser.parse_args()
    manifest = json.loads((ROOT / args.manifest).read_text(encoding="utf-8"))
    if args.rule_version == "compare":
        if not args.comparison_v1 or not args.comparison_v2:
            parser.error("compare requires --comparison-v1 and --comparison-v2 to avoid duplicate engine replay")
        v1 = json.loads((ROOT / args.comparison_v1).read_text(encoding="utf-8"))
        v2 = json.loads((ROOT / args.comparison_v2).read_text(encoding="utf-8"))
        report = compare_reports(v1, v2)
    else:
        report = build_report(manifest, args.strict_probe_blocked_reason, rule_version=args.rule_version)
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        output_path = ROOT / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
