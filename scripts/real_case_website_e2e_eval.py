#!/usr/bin/env python3
"""Build a public-real-case website E2E evaluation contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


CASES = [
    ("steve_jobs", "Steve Jobs", "1955-02-24", "19:15", "San Francisco, CA, USA", ["career", "wealth", "timing"]),
    ("albert_einstein", "Albert Einstein", "1879-03-14", "11:30", "Ulm, Germany", ["education", "career", "timing"]),
    ("barack_obama", "Barack Obama", "1961-08-04", "19:24", "Honolulu, HI, USA", ["career", "migration", "annual"]),
    ("princess_diana", "Princess Diana", "1961-07-01", "19:45", "Sandringham, England", ["marriage", "family", "timing"]),
    ("donald_trump", "Donald Trump", "1946-06-14", "10:54", "Queens, NY, USA", ["career", "wealth", "annual"]),
    ("oprah_winfrey", "Oprah Winfrey", "1954-01-29", "04:30", "Kosciusko, MS, USA", ["career", "wealth", "family"]),
    ("elon_musk", "Elon Musk", "1971-06-28", "07:30", "Pretoria, South Africa", ["career", "migration", "wealth"]),
    ("mahatma_gandhi", "Mahatma Gandhi", "1869-10-02", "07:11", "Porbandar, India", ["career", "migration", "timing"]),
    ("marilyn_monroe", "Marilyn Monroe", "1926-06-01", "09:30", "Los Angeles, CA, USA", ["marriage", "career", "health"]),
    ("bill_gates", "Bill Gates", "1955-10-28", "22:00", "Seattle, WA, USA", ["career", "wealth", "education"]),
    ("j_k_rowling", "J. K. Rowling", "1965-07-31", "14:00", "Yate, England", ["career", "wealth", "timing"]),
    ("nelson_mandela", "Nelson Mandela", "1918-07-18", "14:54", "Mvezo, South Africa", ["career", "timing", "migration"]),
    ("mother_teresa", "Mother Teresa", "1910-08-26", "14:25", "Skopje, North Macedonia", ["career", "migration", "health"]),
    ("michael_jackson", "Michael Jackson", "1958-08-29", "19:33", "Gary, IN, USA", ["career", "wealth", "health"]),
    ("queen_elizabeth_ii", "Queen Elizabeth II", "1926-04-21", "02:40", "London, England", ["career", "family", "annual"]),
    ("john_f_kennedy", "John F. Kennedy", "1917-05-29", "15:00", "Brookline, MA, USA", ["career", "family", "health"]),
    ("martin_luther_king_jr", "Martin Luther King Jr.", "1929-01-15", "12:00", "Atlanta, GA, USA", ["career", "timing", "health"]),
    ("angelina_jolie", "Angelina Jolie", "1975-06-04", "09:09", "Los Angeles, CA, USA", ["marriage", "family", "career"]),
    ("brad_pitt", "Brad Pitt", "1963-12-18", "06:31", "Shawnee, OK, USA", ["marriage", "career", "wealth"]),
    ("serena_williams", "Serena Williams", "1981-09-26", "20:28", "Saginaw, MI, USA", ["career", "health", "annual"]),
]


QUESTION_MATRIX = {
    "career": ["事业主轴是什么？", "哪类阶段更容易爆发？"],
    "wealth": ["财富来源和风险是什么？"],
    "marriage": ["婚恋关系中应看哪些印度占星指标？"],
    "health": ["健康主题只能如何非医疗表达？"],
    "migration": ["迁移/海外发展应看哪些宫位和 Dasha？"],
    "family": ["家庭/子女主题应调用哪些分盘和宫位？"],
    "education": ["学习与教育路径怎么看？"],
    "timing": ["历史关键阶段能否用 Dasha + Narayana 回看？"],
    "annual": ["年度运势应如何避免过度承诺？"],
}


def build(date: str) -> dict[str, Any]:
    cases = []
    for case_id, subject, date_s, time_s, place, domains in CASES:
        cases.append(
            {
                "case_id": case_id,
                "subject": subject,
                "birth": {"date": date_s, "time": time_s, "place": place, "source_policy": "public_record_candidate"},
                "domains": domains,
                "prompts": [q for d in domains for q in QUESTION_MATRIX[d]],
                "expected_runtime_context": [
                    "birth_input_contract",
                    "ayanamsa_node_mode",
                    "D1",
                    "D9_or_relevant_varga",
                    "Dasha",
                    "Narayana_Dasha_for_timing",
                    "functional_benefic_malefic",
                    "claim_boundary",
                    "similar_case_reference_allowed",
                ],
            }
        )
    return {
        "scope": "real_case_website_e2e_eval",
        "created_at": date,
        "claim_status": "ready_contract",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "case_count": len(cases),
        "cases": cases,
        "acceptance_rules": [
            "Website must save/render input contract and runtime context JSON for each prompt.",
            "Answers may use public cases as explanation references, not prediction proof.",
            "Precise day/month claims must stay exploratory_unvalidated unless holdout closes.",
            "Marriage/career/wealth/health/migration/family/education/timing/annual domains must route to matching technique context.",
            "Any Shadbala/AV/KP conflict must be described as method/source difference, not majority-vote truth.",
        ],
        "boundary": "Product E2E quality harness only; not an accuracy benchmark or independent holdout.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default="2026-07-20")
    args = parser.parse_args()
    print(json.dumps(build(args.date), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
