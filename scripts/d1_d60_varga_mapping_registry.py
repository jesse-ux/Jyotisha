#!/usr/bin/env python3
"""Generate D1-D60 varga mapping coverage registry."""
from __future__ import annotations

import json

FORMAL = {
    1: ("Rashi", "本命盘/身体/整体命运", False),
    2: ("Hora", "财富/资源", True),
    3: ("Drekkana", "兄弟姐妹/勇气", True),
    4: ("Chaturthamsa", "房产/基础/运气", True),
    5: ("Panchamsa", "权力/名声", True),
    6: ("Shashthamsa", "疾病/敌人", True),
    7: ("Saptamsa", "子女/创造", True),
    8: ("Ashtamsa", "突发/寿元风险", True),
    9: ("Navamsa", "婚姻/法/内在成熟", True),
    10: ("Dasamsa", "事业/行动/地位", True),
    11: ("Rudramsa", "破坏/转化", True),
    12: ("Dwadasamsa", "父母/祖系", True),
    16: ("Shodasamsa", "车辆/舒适/享受", True),
    20: ("Vimsamsa", "灵性修行", True),
    24: ("Chaturvimsamsa", "教育/学习", True),
    27: ("Bhamsa/Saptavimsamsa", "力量/弱点", True),
    30: ("Trimsamsa", "不幸/困难/过失", True),
    40: ("Khavedamsa", "吉凶效果/母系", True),
    45: ("Akshavedamsa", "总体品格/父系", True),
    60: ("Shashtiamsa", "业力/深层因果", True),
}

JYOTISHGANIT = {1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60}
SKILL_USED = {1, 2, 4, 9, 10, 11, 24, 30, 60}
API_USED = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 20, 24, 27, 30, 40, 45, 60}
UI_USED = {1, 9, 10, 24, 30, 60}
ORACLE_PARTIAL = {1, 2, 4, 9, 10, 30, 60}
CORE = {1, 2, 4, 9, 10, 24, 30, 60}


def row(n: int) -> dict:
    formal = n in FORMAL
    name, use, special = FORMAL.get(n, (None, None, False))
    if formal:
        local_basis = "formal_branch_or_explicit_enum"
    else:
        local_basis = "generic_fallback_only_unvalidated"
    if n == 1:
        local_basis = "natal_chart_core"
    claim = (
        "ready_or_partial_core"
        if n in CORE
        else "partial_formal_not_core"
        if formal
        else "low_rigor_generic_only"
    )
    boundary = (
        "Commonly used varga with local/API coverage; still requires oracle parity for high-rigor claims."
        if n in CORE
        else "Formal named varga exists locally but is not consistently invoked by skill/UI and lacks complete oracle parity."
        if formal
        else "Only generic Dn fallback can compute a sign; no formal name/use/special formula/oracle is registered, so do not present as completed traditional varga."
    )
    return {
        "division": f"D{n}",
        "number": n,
        "local_computable": True,
        "local_basis": local_basis,
        "formal_name_present": formal,
        "formal_name": name,
        "traditional_use_present": use is not None,
        "traditional_use": use,
        "special_formula_present": special,
        "skill_invoked": n in SKILL_USED,
        "api_entry": n in API_USED,
        "ui_entry": n in UI_USED,
        "jyotishganit_external_observation": n in JYOTISHGANIT,
        "external_oracle_status": "partial_or_smoke" if n in ORACLE_PARTIAL else "missing",
        "claim_status": claim,
        "claim_boundary": boundary,
    }


def build() -> dict:
    rows = [row(n) for n in range(1, 61)]
    return {
        "scope": "d1_d60_varga_mapping_registry",
        "created_at": "2026-07-19",
        "status": "complete_registry",
        "claim_status": "partial",
        "production_tuning_allowed": False,
        "truth_matrix_allowed": False,
        "summary": {
            "total_rows": 60,
            "formal_name_count": sum(1 for r in rows if r["formal_name_present"]),
            "generic_only_count": sum(1 for r in rows if r["claim_status"] == "low_rigor_generic_only"),
            "skill_invoked_count": sum(1 for r in rows if r["skill_invoked"]),
            "ui_entry_count": sum(1 for r in rows if r["ui_entry"]),
            "oracle_partial_or_smoke_count": sum(1 for r in rows if r["external_oracle_status"] != "missing"),
        },
        "boundary": "D1-D60 rows are enumerated. Generic fallback rows are not formal traditional varga completion and must not be advertised as verified D1-D60 support.",
        "rows": rows,
    }


def main() -> int:
    print(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
