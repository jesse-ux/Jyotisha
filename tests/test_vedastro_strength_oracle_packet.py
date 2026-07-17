from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import vedastro_strength_oracle_packet  # noqa: E402


def test_strength_packet_declares_shadbala_and_ashtakavarga_as_secondary_evidence() -> None:
    packet = vedastro_strength_oracle_packet.build_strength_oracle_packet("career")

    assert packet["scope"] == "vedastro_strength_oracle_packet"
    assert packet["domain"] == "career"
    assert packet["adjudicator_policy"]["can_change_score"] is False
    assert packet["adjudicator_policy"]["can_set_dominant_label"] is False
    assert packet["adjudicator_policy"]["can_set_payout_label"] is False
    assert [item["method"] for item in packet["requests"]] == ["CalculateShadbala", "CalculateAshtakavarga"]
    assert all(item["role"] == "external_technique_evidence" for item in packet["requests"])
    assert packet["technique_audit_rows"] == [
        {
            "technique": "VedAstro Shadbala Oracle",
            "status": "preview",
            "role": "external_strength_evidence",
            "effect": "secondary_context_only_no_score_or_label_lift",
        },
        {
            "technique": "VedAstro Ashtakavarga Oracle",
            "status": "preview",
            "role": "external_strength_evidence",
            "effect": "secondary_context_only_no_score_or_label_lift",
        },
    ]
