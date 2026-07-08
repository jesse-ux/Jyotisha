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


def _candidate_scan(center: datetime, uncertainty_minutes: int, step_minutes: int) -> dict[str, Any]:
    start = center - timedelta(minutes=uncertainty_minutes)
    end = center + timedelta(minutes=uncertainty_minutes)
    return {
        "start": start.strftime("%Y-%m-%d %H:%M"),
        "end": end.strftime("%Y-%m-%d %H:%M"),
        "step_minutes": step_minutes,
        "candidate_count": int((end - start).total_seconds() // 60 // step_minutes) + 1,
        "cluster_labels": ["early_candidate_cluster", "middle_candidate_cluster", "late_candidate_cluster"],
    }


def build_questionnaire(birth_time: str, uncertainty_minutes: int = 30, step_minutes: int = 1) -> dict[str, Any]:
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
        "candidate_scan": _candidate_scan(_parse_time(birth_time), uncertainty_minutes, step_minutes),
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--birth-time", required=True, help="Approximate local birth time, YYYY-MM-DD HH:MM")
    parser.add_argument("--uncertainty-minutes", type=int, default=30)
    parser.add_argument("--step-minutes", type=int, default=1)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build_questionnaire(args.birth_time, args.uncertainty_minutes, args.step_minutes), ensure_ascii=False, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
