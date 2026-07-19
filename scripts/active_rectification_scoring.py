"""Build and score deterministic birth-time rectification questions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Literal, TypeAlias, TypedDict

AnswerChoice: TypeAlias = Literal["A", "B", "C", "D"]
JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


class QuestionOption(TypedDict):
    key: AnswerChoice
    label: str
    score: int


class ScoringRule(TypedDict):
    effect: str
    cluster: str
    points: int


class RectificationQuestion(TypedDict):
    id: str
    round: int
    domain: str
    sensitivity: list[str]
    window: str
    prompt: str
    options: list[QuestionOption]
    scoring_map: dict[AnswerChoice, ScoringRule]


class AppliedScore(TypedDict):
    id: str
    answer: str
    cluster: str
    points: int


class ClusterRanking(TypedDict):
    cluster: str
    score: int


class InvalidAnswer(TypedDict):
    id: str
    answer: str


class ScoringResult(TypedDict):
    scope: str
    schema_version: int
    answered_count: int
    candidate_cluster_rankings: list[ClusterRanking]
    next_round: int | None
    next_round_questions: list[dict[str, JsonValue]]
    applied_scoring: list[AppliedScore]
    unknown_question_ids: list[str]
    invalid_answers: list[InvalidAnswer]
    boundary: str


@dataclass(frozen=True, slots=True)
class QuestionTemplate:
    id: str
    round: int
    domain: str
    sensitivity: tuple[str, ...]
    window: str
    prompt: str
    yes_bias: str
    no_bias: str


OPTIONS: Final[tuple[QuestionOption, ...]] = (
    {"key": "A", "label": "明确有，且时间大致吻合", "score": 2},
    {"key": "B", "label": "有类似，但时间略偏或不够重大", "score": 1},
    {"key": "C", "label": "没有明显发生", "score": -2},
    {"key": "D", "label": "不确定 / 不记得", "score": 0},
)

QUESTION_TEMPLATES: Final[tuple[QuestionTemplate, ...]] = (
    QuestionTemplate("education_environment_shift", 1, "education", ("D24", "D4", "Dasha"), "age_16_to_18", "16-18岁附近，是否有明显学业、学校、专业方向或学习环境变化？", "middle_candidate_cluster", "against_D24_sensitive_cluster"),
    QuestionTemplate("residence_relocation_shift", 1, "residence", ("D4", "12H", "Rahu/Ketu", "Transit"), "age_20_to_24", "20-24岁附近，是否有搬家、离乡、长期异地、住宿或居住结构变化？", "D4_relocation_cluster", "against_D4_relocation_cluster"),
    QuestionTemplate("relationship_or_partner_entry", 1, "relationship", ("D9", "UL", "A7", "7H"), "age_21_to_26", "21-26岁附近，是否有关系对象进入、关系断裂、暧昧升级或关系观明显转变？", "D9_UL_A7_cluster", "against_relationship_cluster"),
    QuestionTemplate("career_responsibility_pressure", 1, "career", ("D10", "A10", "Saturn", "10H"), "age_26_to_30", "26-30岁附近，是否有责任增加、合作压力、工作结构变化或长期压力阶段？", "D10_A10_saturn_cluster", "against_career_pressure_cluster"),
    QuestionTemplate("finance_resource_shift", 1, "finance", ("D2", "2H", "11H"), "resource_change_window", "是否有收入结构、重要资产、资助、负债或资源渠道发生明显变化的阶段？", "D2_resource_cluster", "against_D2_resource_cluster"),
    QuestionTemplate("research_tool_expression_shift", 1, "career_learning", ("D10", "D24", "Mercury", "A10"), "recent_three_years", "近三年是否明显进入写作、技术、系统化学习、工具搭建、内容表达、AI/研究类方向？", "Mercury_D24_A10_cluster", "against_learning_expression_cluster"),
    QuestionTemplate("health_crisis_or_low_period", 2, "health_pressure", ("D30", "6H", "8H", "Saturn/Mars"), "largest_pressure_window", "某个压力窗口附近，是否有健康、事故、低谷、睡眠/精神压力或身体负担明显阶段？", "D30_crisis_cluster", "against_D30_crisis_cluster"),
    QuestionTemplate("public_role_or_project_visibility", 2, "public_work", ("A10", "D10", "AmK", "Karakamsha"), "career_visibility_window", "某个事业窗口附近，是否有项目公开、作品产出、职位/身份变化或被他人看见的机会？", "A10_public_visibility_cluster", "against_A10_cluster"),
    QuestionTemplate("sequence_inner_vs_outer", 3, "fine_timing", ("KP_cusp", "Pratyantar", "Dasha_boundary"), "top_candidate_window", "关键变化更像先有内在转向、后有外部结果，还是几乎同时发生？", "fine_boundary_cluster", "neutral"),
)


def build_questions() -> list[RectificationQuestion]:
    return [
        {
            "id": template.id,
            "round": template.round,
            "domain": template.domain,
            "sensitivity": list(template.sensitivity),
            "window": template.window,
            "prompt": template.prompt,
            "options": list(OPTIONS),
            "scoring_map": {
                "A": {"effect": "support", "cluster": template.yes_bias, "points": 2},
                "B": {"effect": "weak_support", "cluster": template.yes_bias, "points": 1},
                "C": {"effect": "exclude_or_penalize", "cluster": template.no_bias, "points": -2},
                "D": {"effect": "neutral", "cluster": "neutral", "points": 0},
            },
        }
        for template in QUESTION_TEMPLATES
    ]


def score_answers(
    questionnaire: Mapping[str, JsonValue],
    answers: Mapping[str, str],
) -> ScoringResult:
    questions_value = questionnaire.get("questions")
    questions = questions_value if isinstance(questions_value, list) else []
    by_id = {
        question["id"]: question
        for question in questions
        if isinstance(question, dict) and isinstance(question.get("id"), str)
    }
    canonical_by_id = {question["id"]: question for question in build_questions()}
    cluster_scores: dict[str, int] = {}
    applied: list[AppliedScore] = []
    unknown_ids: list[str] = []
    invalid_answers: list[InvalidAnswer] = []

    for question_id, raw_choice in answers.items():
        question = by_id.get(question_id)
        if not question:
            unknown_ids.append(question_id)
            continue
        choice = raw_choice.strip().upper()
        scoring_map = question.get("scoring_map")
        if not isinstance(scoring_map, dict):
            canonical = canonical_by_id.get(question_id)
            scoring_map = canonical["scoring_map"] if canonical else None
        scoring = scoring_map.get(choice) if isinstance(scoring_map, dict) else None
        if not isinstance(scoring, dict):
            invalid_answers.append({"id": question_id, "answer": raw_choice})
            continue
        cluster_value = scoring.get("cluster")
        points_value = scoring.get("points")
        cluster = cluster_value if isinstance(cluster_value, str) else "neutral"
        points = int(points_value) if isinstance(points_value, int | float | str) else 0
        if cluster != "neutral":
            cluster_scores[cluster] = cluster_scores.get(cluster, 0) + points
        applied.append({"id": question_id, "answer": choice, "cluster": cluster, "points": points})

    answered_ids = {item["id"] for item in applied}
    unanswered = [question for question in questions if question.get("id") not in answered_ids]
    round_values = [question.get("round") for question in unanswered]
    next_round = min((int(value) for value in round_values if isinstance(value, int | float | str)), default=None)
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
