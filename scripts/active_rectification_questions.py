#!/usr/bin/env python3
"""Generate active-choice birth-time rectification questions."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from typing import Any

OPTIONS = [
    {"key": "A", "label": "明确有，且时间大致吻合", "score": 2},
    {"key": "B", "label": "有类似，但时间略偏或不够重大", "score": 1},
    {"key": "C", "label": "没有明显发生", "score": -2},
    {"key": "D", "label": "不确定 / 不记得", "score": 0},
]

QUESTION_TEMPLATES = [
    ("education_environment_shift", 1, "education", ["D24", "D4", "Dasha"], "age_16_to_18", "16-18岁附近，是否有明显学业、学校、专业方向或学习环境变化？", "middle_candidate_cluster", "against_D24_sensitive_cluster"),
    ("residence_relocation_shift", 1, "residence", ["D4", "12H", "Rahu/Ketu", "Transit"], "age_20_to_24", "20-24岁附近，是否有搬家、离乡、长期异地、住宿或居住结构变化？", "D4_relocation_cluster", "against_D4_relocation_cluster"),
    ("relationship_or_partner_entry", 1, "relationship", ["D9", "UL", "A7", "7H"], "age_21_to_26", "21-26岁附近，是否有关系对象进入、关系断裂、暧昧升级或关系观明显转变？", "D9_UL_A7_cluster", "against_relationship_cluster"),
    ("career_responsibility_pressure", 1, "career", ["D10", "A10", "Saturn", "10H"], "age_26_to_30", "26-30岁附近，是否有责任增加、合作压力、工作结构变化或长期压力阶段？", "D10_A10_saturn_cluster", "against_career_pressure_cluster"),
    ("research_tool_expression_shift", 1, "career_learning", ["D10", "D24", "Mercury", "A10"], "recent_three_years", "近三年是否明显进入写作、技术、系统化学习、工具搭建、内容表达、AI/研究类方向？", "Mercury_D24_A10_cluster", "against_learning_expression_cluster"),
    ("health_crisis_or_low_period", 2, "health_pressure", ["D30", "6H", "8H", "Saturn/Mars"], "largest_pressure_window", "某个压力窗口附近，是否有健康、事故、低谷、睡眠/精神压力或身体负担明显阶段？", "D30_crisis_cluster", "against_D30_crisis_cluster"),
    ("public_role_or_project_visibility", 2, "public_work", ["A10", "D10", "AmK", "Karakamsha"], "career_visibility_window", "某个事业窗口附近，是否有项目公开、作品产出、职位/身份变化或被他人看见的机会？", "A10_public_visibility_cluster", "against_A10_cluster"),
    ("sequence_inner_vs_outer", 3, "fine_timing", ["KP_cusp", "Pratyantar", "Dasha_boundary"], "top_candidate_window", "关键变化更像先有内在转向、后有外部结果，还是几乎同时发生？", "fine_boundary_cluster", "neutral"),
]


def _parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M")


def _candidate_scan(
    center: datetime,
    uncertainty_minutes: int,
    step_minutes: int,
    *,
    lat: float | None = None,
    lon: float | None = None,
    tz: float | None = None,
    ayanamsa: str = "lahiri",
) -> dict[str, Any]:
    start = center - timedelta(minutes=uncertainty_minutes)
    end = center + timedelta(minutes=uncertainty_minutes)
    total_minutes = int((end - start).total_seconds() // 60)
    candidate_count = total_minutes // step_minutes + 1
    sample_offsets = sorted({-uncertainty_minutes, 0, uncertainty_minutes})
    samples = []
    for offset in sample_offsets:
        candidate = center + timedelta(minutes=offset)
        if offset < 0:
            cluster = "early_candidate_cluster"
        elif offset > 0:
            cluster = "late_candidate_cluster"
        else:
            cluster = "middle_candidate_cluster"
        sample = {
            "time": candidate.strftime("%Y-%m-%d %H:%M"),
            "offset_minutes": offset,
            "cluster": cluster,
            "sensitivity_flags": _sensitivity_flags(abs(offset)),
        }
        recast = _candidate_recast(candidate, lat=lat, lon=lon, tz=tz, ayanamsa=ayanamsa)
        if recast:
            sample.update(recast)
        samples.append(sample)
    has_true_recast = all("varga_lagna" in sample for sample in samples)
    computed_layers = ["time_range", "candidate_cluster", "question_sensitivity_map"]
    blocked_layers = ["true_varga_recast", "true_kp_cusp_recast", "true_arudha_recast"]
    if has_true_recast:
        computed_layers.extend(["true_varga_recast", "true_arudha_recast"])
        blocked_layers = ["true_kp_cusp_recast"]
    return {
        "start": start.strftime("%Y-%m-%d %H:%M"),
        "end": end.strftime("%Y-%m-%d %H:%M"),
        "step_minutes": step_minutes,
        "candidate_count": candidate_count,
        "cluster_labels": ["early_candidate_cluster", "middle_candidate_cluster", "late_candidate_cluster"],
        "samples": samples,
        "sensitivity_summary": {
            "method": "range_bucket_scan_v1",
            "high_value_layers": ["D9", "D10", "D24", "D30", "D60", "UL", "A7", "A10", "KP_cusp"],
            "computed_layers": computed_layers,
            "blocked_layers": blocked_layers,
            "boundary": "KP cusp recast remains blocked until a validated KP cusp engine is wired into this workflow.",
        },
    }


def _sensitivity_flags(abs_offset_minutes: int) -> list[str]:
    flags = ["D9", "D10", "D24", "A10"]
    if abs_offset_minutes >= 10:
        flags.extend(["D30", "UL", "A7"])
    if abs_offset_minutes >= 20:
        flags.extend(["D60", "KP_cusp"])
    return flags


def _candidate_recast(
    candidate: datetime,
    *,
    lat: float | None,
    lon: float | None,
    tz: float | None,
    ayanamsa: str,
) -> dict[str, Any] | None:
    if lat is None or lon is None or tz is None:
        return None
    import domain_calculation_service
    import jaimini
    import varga

    chart = domain_calculation_service.compute_chart({
        "year": candidate.year,
        "month": candidate.month,
        "day": candidate.day,
        "hour": candidate.hour,
        "minute": candidate.minute,
        "second": candidate.second,
        "lat": lat,
        "lon": lon,
        "tz": tz,
        "ayanamsa": ayanamsa,
    })
    planet_lons = {
        name: data["lon"]
        for name, data in chart.get("planets", {}).items()
        if name in {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
    }
    asc_lon = chart["ascendant"]["lon"]
    vargas = varga.calc_all_vargas(planet_lons, asc_lon, divisions=[9, 10, 24, 30, 60])
    arudha = jaimini.calc_arudha_padas(int(asc_lon // 30), planet_lons)
    padas = arudha.get("padas", {})
    upapada = arudha.get("upapada", {})
    return {
        "ascendant": {
            "lon": round(asc_lon, 6),
            "sign": chart["ascendant"].get("sign"),
            "degree_in_sign": chart["ascendant"].get("degree_in_sign"),
        },
        "varga_lagna": {
            key: value.get("Ascendant", {})
            for key, value in vargas.items()
        },
        "arudha": {
            "A7": padas.get("A7", {}),
            "A10": padas.get("A10", {}),
            "UL": upapada,
        },
    }


def build_questionnaire(
    birth_time: str,
    uncertainty_minutes: int = 30,
    step_minutes: int = 1,
    *,
    lat: float | None = None,
    lon: float | None = None,
    tz: float | None = None,
    ayanamsa: str = "lahiri",
) -> dict[str, Any]:
    questions = []
    for qid, round_id, domain, sensitivity, window, prompt, yes_bias, no_bias in QUESTION_TEMPLATES:
        questions.append({
            "id": qid,
            "round": round_id,
            "domain": domain,
            "sensitivity": sensitivity,
            "window": window,
            "prompt": prompt,
            "options": OPTIONS,
            "scoring_map": {
                "A": {"effect": "support", "cluster": yes_bias, "points": 2},
                "B": {"effect": "weak_support", "cluster": yes_bias, "points": 1},
                "C": {"effect": "exclude_or_penalize", "cluster": no_bias, "points": -2},
                "D": {"effect": "neutral", "cluster": "neutral", "points": 0},
            },
        })
    return {
        "scope": "active_birth_time_rectification_questionnaire",
        "schema_version": 1,
        "candidate_scan": _candidate_scan(
            _parse_time(birth_time),
            uncertainty_minutes,
            step_minutes,
            lat=lat,
            lon=lon,
            tz=tz,
            ayanamsa=ayanamsa,
        ),
        "workflow": [
            "candidate_time_scan",
            "varga_arudha_kp_sensitivity_diff",
            "high_information_question_generation",
            "multiple_choice_user_answers",
            "dynamic_candidate_cluster_scoring",
            "next_round_question_selection",
        ],
        "rounds": {
            "1": "coarse screen",
            "2": "domain follow-up",
            "3": "fine confirmation",
        },
        "sensitivity_layers": ["D9", "D10", "D24", "D30", "D60", "D4", "UL", "A7", "A10", "KP_cusp", "Vimshottari", "Narayana", "Chara"],
        "questions": questions,
        "boundary": "Question generation only; final rectification requires scoring answers against actual candidate chart differences.",
    }


def score_answers(questionnaire: dict[str, Any], answers: dict[str, str]) -> dict[str, Any]:
    questions = questionnaire.get("questions") if isinstance(questionnaire.get("questions"), list) else []
    by_id = {question["id"]: question for question in questions if isinstance(question, dict) and question.get("id")}
    cluster_scores: dict[str, int] = {}
    applied = []
    unknown_ids = []
    invalid_answers = []

    for question_id, raw_choice in (answers or {}).items():
        question = by_id.get(question_id)
        if not question:
            unknown_ids.append(question_id)
            continue
        choice = str(raw_choice or "").strip().upper()
        scoring = (question.get("scoring_map") or {}).get(choice)
        if not isinstance(scoring, dict):
            invalid_answers.append({"id": question_id, "answer": raw_choice})
            continue
        cluster = str(scoring.get("cluster") or "neutral")
        points = int(scoring.get("points") or 0)
        if cluster != "neutral":
            cluster_scores[cluster] = cluster_scores.get(cluster, 0) + points
        applied.append({"id": question_id, "answer": choice, "cluster": cluster, "points": points})

    answered_ids = {item["id"] for item in applied}
    unanswered = [question for question in questions if question.get("id") not in answered_ids]
    next_round = min((int(question.get("round") or 0) for question in unanswered), default=None)
    rankings = [
        {"cluster": cluster, "score": score}
        for cluster, score in sorted(cluster_scores.items(), key=lambda item: (-item[1], item[0]))
    ]
    return {
        "scope": "active_birth_time_rectification_scoring",
        "schema_version": 1,
        "answered_count": len(applied),
        "candidate_cluster_rankings": rankings,
        "next_round": next_round,
        "next_round_questions": [question for question in unanswered if question.get("round") == next_round],
        "applied_scoring": applied,
        "unknown_question_ids": unknown_ids,
        "invalid_answers": invalid_answers,
        "boundary": "This narrows candidate clusters only; final rectification requires scoring answers against actual candidate chart differences.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--birth-time", required=True, help="Approximate local birth time, YYYY-MM-DD HH:MM")
    parser.add_argument("--uncertainty-minutes", type=int, default=30)
    parser.add_argument("--step-minutes", type=int, default=1)
    parser.add_argument("--answers-json", default="", help="Optional JSON object mapping question id to A/B/C/D")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    questionnaire = build_questionnaire(args.birth_time, args.uncertainty_minutes, args.step_minutes)
    report = score_answers(questionnaire, json.loads(args.answers_json)) if args.answers_json else questionnaire
    print(json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
