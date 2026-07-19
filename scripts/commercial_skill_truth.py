"""Load and apply commercial claim boundaries for restricted techniques.

This is deliberately a product-owned status contract. It never imports a research
workspace or reproduces research calculations.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


OVERLAY_PATH = (
    Path(__file__).resolve().parents[1]
    / "references"
    / "oracle"
    / "commercial_skill_truth_overlay.v1.json"
)
ORACLE_DIR = OVERLAY_PATH.parent
TECHNIQUE_TRUTH_IDS = (
    "kp_system",
    "muhurta",
    "gochara_event_timing",
    "sahams",
    "sphuta_trisphuta_family",
    "tajika_yogas",
    "conception_chart",
    "relationship_combinations",
)
_BLOCKED_STATUSES = {"blocked", "research_only_blocked"}


def load_commercial_skill_truth() -> dict[str, Any]:
    """Return the local, public-safe commercial status contract."""
    with OVERLAY_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    techniques = payload.get("techniques")
    if not isinstance(techniques, list):
        raise ValueError("commercial technique truth overlay must contain techniques")
    by_id = {item.get("technique_id"): item for item in techniques if isinstance(item, dict)}
    if set(by_id) != set(TECHNIQUE_TRUTH_IDS):
        raise ValueError("commercial technique truth overlay has an unexpected technique set")
    return payload


def apply_commercial_skill_truth(result: dict[str, Any]) -> dict[str, Any]:
    """Attach immutable claim limits to a server workflow receipt."""
    enriched = copy.deepcopy(result)
    techniques = load_commercial_skill_truth()["techniques"]
    blocked = [item["technique_id"] for item in techniques if item["status"] in _BLOCKED_STATUSES]
    restricted = [item["technique_id"] for item in techniques]
    enriched["technique_truth"] = {
        "status": "restricted",
        "techniques": techniques,
        "blocked_techniques": blocked,
        "reference_only_techniques": [
            item["technique_id"] for item in techniques if item["status"] == "reference_only"
        ],
        "partial_techniques": [
            item["technique_id"]
            for item in techniques
            if item["status"] in {"partial", "partial_registry_only"}
        ],
    }
    answer_policy = enriched.setdefault("answer_policy", {})
    answer_policy["deterministic_claims_forbidden_for"] = restricted
    answer_policy["blocked_techniques"] = blocked
    answer_policy["technique_truth_status"] = "restricted"
    evidence_status = _commercial_evidence_status()
    enriched["commercial_evidence_status"] = evidence_status
    consumer_context = enriched.get("consumer_context")
    if isinstance(consumer_context, dict):
        consumer_context["technique_truth"] = enriched["technique_truth"]
        consumer_context["commercial_evidence_status"] = evidence_status
    return enriched


def _read_local_object(filename: str) -> dict[str, Any]:
    try:
        with (ORACLE_DIR / filename).open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _commercial_evidence_status() -> dict[str, Any]:
    """Summarize local evidence state without returning raw external responses."""
    vedastro = _read_local_object("vedastro_identity_archive_2026_07_19.json")
    mismatch = _read_local_object("three_engine_mismatch_arbitration_2026_07_19.json")
    return {
        "claim_audit": {
            "status": "contract_enforced",
            "scope": "commercial_claim_boundaries",
        },
        "vedastro_identity": {
            "status": vedastro.get("self_host_candidate_status") or "not_archived",
            "hosted_identity": "runtime_evidence_required",
        },
        "three_engine_mismatch": {
            "status": mismatch.get("status") or "not_assessed",
            "truth_policy": mismatch.get("truth_policy") or "no_majority_vote",
            "mismatch_count": mismatch.get("mismatch_count"),
            "category_counts": mismatch.get("category_counts") or {},
        },
    }
