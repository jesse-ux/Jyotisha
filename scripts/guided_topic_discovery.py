#!/usr/bin/env python3
"""Evidence-backed topic discovery for ordinary users.

This layer does not calculate astrology. It ranks existing full-reading
evidence into a small set of next topics a user can tap or ask about.
"""

from __future__ import annotations

from typing import Any


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _current_dasha(modules: dict[str, Any]) -> tuple[str | None, str | None, str | None, str | None]:
    dasha = _as_dict(modules.get("dasha"))
    current = _as_dict(dasha.get("current_dasha"))
    antar = _as_dict(current.get("antardasha"))
    return current.get("lord"), antar.get("lord"), current.get("start"), current.get("end")


def _convergence_for(modules: dict[str, Any], *tokens: str) -> dict[str, Any]:
    convergence = _as_dict(modules.get("dasa_convergence"))
    activations = _as_dict(convergence.get("domain_activations"))
    for domain, row in activations.items():
        if any(token in str(domain).lower() for token in tokens):
            found = dict(_as_dict(row))
            found.setdefault("domain", domain)
            return found
    for row in _as_list(convergence.get("top_convergent_domains")):
        if isinstance(row, dict) and any(token in str(row.get("domain", "")).lower() for token in tokens):
            return row
        if isinstance(row, (list, tuple)) and row and any(token in str(row[0]).lower() for token in tokens):
            return {"domain": row[0], "convergence_level": row[1] if len(row) > 1 else None}
    return {}


def _vedastro_snapshot(modules: dict[str, Any], domain: str) -> dict[str, Any]:
    overview = _as_dict(modules.get("vedastro_range_scan_result"))
    metadata = _as_dict(overview.get("source_metadata"))
    counts = _as_dict(metadata.get("domain_event_counts"))
    statuses = _as_dict(metadata.get("domain_statuses"))
    top = _as_dict(overview.get("top_events_by_domain")).get(domain)
    status = statuses.get(domain) or overview.get("status")
    event_count = int(counts.get(domain) or 0)
    if status == "ok" or event_count:
        return {
            "status": "used",
            "domain": domain,
            "event_count": event_count,
            "top_event": top if isinstance(top, dict) else None,
            "source": "modules.vedastro_range_scan_result",
        }
    return {
        "status": "blocked" if overview else "not_available",
        "domain": domain,
        "event_count": event_count,
        "top_event": None,
        "source": "modules.vedastro_range_scan_result",
    }


def _evidence_line(label: str, value: Any) -> dict[str, str]:
    return {"label": label, "value": str(value)}


def _strict_contracts(report: dict[str, Any], modules: dict[str, Any]) -> dict[str, Any]:
    snapshot = _as_dict(_as_dict(_as_dict(report.get("ai_prompt_pack")).get("evidence_snapshot")))
    contracts = _as_dict(snapshot.get("strict_workflow_contracts"))
    if contracts:
        return contracts
    mapping = {
        "career": "career_strict_evidence",
        "relationship": "relationship_strict_evidence",
        "finance": "finance_strict_evidence",
    }
    compact: dict[str, Any] = {}
    for route, key in mapping.items():
        strict = _as_dict(modules.get(key))
        if strict:
            compact[route] = strict
    return compact


def _topic_audit_gate(contracts: dict[str, Any], route: str) -> dict[str, Any]:
    contract = _as_dict(contracts.get(route))
    bundle = _as_dict(contract.get("strict_adjudication_bundle"))
    summary = _as_dict(bundle.get("strict_audit_gate")) or _as_dict(contract.get("technique_audit_summary"))
    if summary:
        return summary
    return {
        "functional_benefic_malefic": {"gate": "hard", "used": False, "status": "blocked"},
        "relevant_vargas": {"gate": "hard", "required_keys": [], "present_keys": []},
        "vimshottari_narayana_crosscheck": {
            "gate": "hard",
            "used": False,
            "required_timing_systems": ["Vimshottari", "Narayana"],
        },
        "source_priority_boundary": {
            "gate": "boundary",
            "official": {},
            "local": {},
            "fallback_used": [],
            "blocked_items": [],
            "conflicts": [],
        },
    }


def _topic(
    *,
    topic_id: str,
    title: str,
    reality_value: str,
    why: str,
    evidence: list[dict[str, str]],
    confidence: str,
    vedastro: dict[str, Any],
    strict_audit_gate: dict[str, Any],
    monthly_adjudication_summary: dict[str, Any],
    official_day_signal_summary: dict[str, Any],
    questions: list[str],
    answer_mode: str = "tap_or_ask",
    priority: int = 50,
) -> dict[str, Any]:
    return {
        "id": topic_id,
        "title": title,
        "reality_value": reality_value,
        "why_worth_exploring": why,
        "evidence": evidence,
        "confidence": confidence,
        "vedastro": vedastro,
        "strict_adjudication_bundle": {
            "strict_audit_gate": strict_audit_gate,
            "monthly_adjudication_summary": monthly_adjudication_summary,
            "official_day_signal_summary": official_day_signal_summary,
        },
        "strict_audit_gate": strict_audit_gate,
        "monthly_adjudication_summary": monthly_adjudication_summary,
        "official_day_signal_summary": official_day_signal_summary,
        "suggested_questions": questions,
        "answer_mode": answer_mode,
        "priority": priority,
    }


def _topic_official_day_signal_summary(contracts: dict[str, Any], modules: dict[str, Any], route: str) -> dict[str, Any]:
    contract = _as_dict(contracts.get(route))
    bundle = _as_dict(contract.get("strict_adjudication_bundle"))
    summary = _as_dict(bundle.get("official_day_signal_summary")) or _as_dict(contract.get("official_day_signal_summary"))
    if summary:
        return summary
    mapping = {
        "career": "career_strict_evidence",
        "relationship": "relationship_strict_evidence",
        "finance": "finance_strict_evidence",
    }
    strict = _as_dict(modules.get(mapping.get(route, "")))
    present = _as_dict(strict.get("present_evidence"))
    external = _as_dict(present.get("external_activation"))
    signals = _as_list(external.get("official_day_signals"))
    return {
        "available": bool(signals),
        "signal_count": len(signals),
        "top_day": _as_dict(signals[0]) if signals else None,
        "days": [_as_dict(item) for item in signals[:3] if isinstance(item, dict)],
        "source": "present_evidence.external_activation.official_day_signals" if signals else None,
    }


def _topic_monthly_adjudication_summary(contracts: dict[str, Any], modules: dict[str, Any], route: str) -> dict[str, Any]:
    contract = _as_dict(contracts.get(route))
    bundle = _as_dict(contract.get("strict_adjudication_bundle"))
    summary = _as_dict(bundle.get("monthly_adjudication_summary")) or _as_dict(contract.get("monthly_adjudication_summary"))
    if summary:
        return summary
    mapping = {
        "career": "career_strict_evidence",
        "relationship": "relationship_strict_evidence",
        "finance": "finance_strict_evidence",
    }
    strict = _as_dict(modules.get(mapping.get(route, "")))
    return _as_dict(strict.get("monthly_adjudication_summary"))


def build_guided_topics(report: dict[str, Any]) -> list[dict[str, Any]]:
    modules = _as_dict(report.get("modules"))
    contracts = _strict_contracts(report, modules)
    chart = _as_dict(report.get("chart") or modules.get("chart"))
    planets = _as_dict(chart.get("planets"))
    md, ad, md_start, md_end = _current_dasha(modules)
    md_label = f"{md or '-'} / {ad or '-'}"
    fbm = _as_dict(_as_dict(report.get("ai_prompt_pack")).get("evidence_snapshot")).get("functional_benefic_malefic")
    fbm = _as_dict(fbm) or _as_dict(modules.get("functional_benefic_malefic"))

    career_conv = _convergence_for(modules, "career", "status", "profession", "work")
    marriage_conv = _convergence_for(modules, "marriage", "partnership", "relationship")
    wealth_conv = _convergence_for(modules, "wealth", "finance", "income", "gain")
    relationship = _as_dict(modules.get("relationship_strict_evidence"))
    rel_judgement = _as_dict(relationship.get("event_judgement"))
    rel_present = _as_dict(relationship.get("present_evidence"))
    d9 = _as_dict(rel_present.get("d9_navamsa"))
    ul = _as_dict(rel_present.get("upapada_lagna"))
    dk = _as_dict(rel_present.get("darakaraka"))
    ketu_house = _as_dict(planets.get("Ketu")).get("house")

    topics = [
        _topic(
            topic_id="relationship_partnership",
            title="婚恋与长期合作为什么是当前强主题",
            reality_value="帮助用户判断关系、合作、相亲、公开关系或长期承诺是否值得深入推进。",
            why="婚恋/合作不是靠用户主动问才触发；当前证据里第7宫、D9、UL、DK 与多系统时间层已经可读。",
            evidence=[
                _evidence_line("Vimshottari", md_label),
                _evidence_line("Dasa 收敛", marriage_conv.get("convergence_level") or "not_found"),
                _evidence_line("D9", f"Asc={_as_dict(d9.get('Ascendant')).get('sign', '-')}; 7th={_as_dict(d9.get('_d9_analysis')).get('navamsa_7th_sign', '-')}"),
                _evidence_line("UL", f"{ul.get('sign', '-')} H{ul.get('house', '-')}"),
                _evidence_line("DK", f"{dk.get('dk_planet', '-')} H{dk.get('dk_house', '-')}"),
                _evidence_line("Strict verdict", rel_judgement.get("verdict") or "not_available"),
            ],
            confidence="medium" if marriage_conv or relationship else "low",
            vedastro=_vedastro_snapshot(modules, "marriage"),
            strict_audit_gate=_topic_audit_gate(contracts, "relationship"),
            monthly_adjudication_summary=_topic_monthly_adjudication_summary(contracts, modules, "relationship"),
            official_day_signal_summary=_topic_official_day_signal_summary(contracts, modules, "relationship"),
            questions=[
                "我现在适合认真发展关系，还是更适合筛选和观察？",
                "我的伴侣画像、认识场景和相处风险是什么？",
                "未来哪些时间窗口适合推进关系公开或承诺？",
            ],
            priority=90 if marriage_conv else 65,
        ),
        _topic(
            topic_id="career_direction",
            title="事业定位是否正在重构",
            reality_value="帮助用户判断是继续深耕、换方向、做产品化，还是先修系统和长期资产。",
            why="事业主题需要把10宫、A10/D10、多系统 Dasha 与 VedAstro 事业雷达放在一起看。",
            evidence=[
                _evidence_line("Vimshottari", md_label),
                _evidence_line("10宫触发", f"Ketu house={ketu_house}" if ketu_house else "check D10/A10"),
                _evidence_line("Dasa 收敛", career_conv.get("convergence_level") or "not_found"),
                _evidence_line("Functional layer", f"benefics={fbm.get('functional_benefics', [])}; malefics={fbm.get('functional_malefics', [])}"),
            ],
            confidence="medium" if career_conv or ketu_house == 10 else "low",
            vedastro=_vedastro_snapshot(modules, "career"),
            strict_audit_gate=_topic_audit_gate(contracts, "career"),
            monthly_adjudication_summary=_topic_monthly_adjudication_summary(contracts, modules, "career"),
            official_day_signal_summary=_topic_official_day_signal_summary(contracts, modules, "career"),
            questions=[
                "我现在适合换方向还是继续深耕？",
                "2026 年事业吉利在哪里，不利在哪里？",
                "哪些月份适合推进项目、发布产品或谈合作？",
            ],
            priority=82 if career_conv or ketu_house == 10 else 60,
        ),
        _topic(
            topic_id="birth_time_rectification",
            title="出生时间是否需要微调",
            reality_value="帮助用户把婚恋、事业、财富应期从泛泛判断推进到可回验时间窗口。",
            why="D9、D10、UL、A10 对出生时间敏感；如果用户想问具体月份/日期，先校正时间更有价值。",
            evidence=[
                _evidence_line("birth time", _as_dict(report.get("birth_info")).get("time", "-")),
                _evidence_line("sensitive layers", "D9 / D10 / UL / A10"),
                _evidence_line("current timing", f"{md_label}; {md_start or '-'} to {md_end or '-'}"),
            ],
            confidence="medium",
            vedastro=_vedastro_snapshot(modules, "marriage"),
            strict_audit_gate=_topic_audit_gate(contracts, "relationship"),
            monthly_adjudication_summary=_topic_monthly_adjudication_summary(contracts, modules, "relationship"),
            official_day_signal_summary=_topic_official_day_signal_summary(contracts, modules, "relationship"),
            questions=[
                "我可以用过去事件校正出生时间吗？",
                "哪些人生事件最适合用来校正出生时间？",
                "我只知道一个时间区间，系统应该先问我哪些 yes/no 问题？",
            ],
            answer_mode="yes_no_or_free_text",
            priority=80,
        ),
        _topic(
            topic_id="wealth_risk",
            title="财富、借贷和交易风险怎样用数据拆开",
            reality_value="帮助用户把收入、现金流、借贷、买卖和投资风险分开判断，而不是只说财运好坏。",
            why="财富主题必须同时看2宫、11宫、D2/D11、Dasha 与 VedAstro wealth 标签。",
            evidence=[
                _evidence_line("Vimshottari", md_label),
                _evidence_line("Dasa 收敛", wealth_conv.get("convergence_level") or "not_found"),
                _evidence_line("required vargas", "D2 / D11"),
            ],
            confidence="medium" if wealth_conv else "low",
            vedastro=_vedastro_snapshot(modules, "wealth"),
            strict_audit_gate=_topic_audit_gate(contracts, "finance"),
            monthly_adjudication_summary=_topic_monthly_adjudication_summary(contracts, modules, "finance"),
            official_day_signal_summary=_topic_official_day_signal_summary(contracts, modules, "finance"),
            questions=[
                "2026 年哪些钱可以赚，哪些钱要避险？",
                "我适合靠项目、投资、合作还是长期积累赚钱？",
                "哪些时间窗口不适合借贷、买卖或大额投入？",
            ],
            priority=70 if wealth_conv else 50,
        ),
    ]

    topics.sort(key=lambda item: (-int(item.get("priority", 0)), item["id"]))
    return topics[:4]
