from __future__ import annotations

from typing import Any
from uuid import NAMESPACE_URL, uuid5

from scripts.rectification.candidate_feature_service import build_candidate_feature_snapshot
from scripts.rectification.contracts import RectificationRequest
from scripts.rectification.diagnostics_service import run_diagnostics
from scripts.rectification.scoring_service import (
    ALGORITHM_VERSION,
    build_event_contribution_matrix,
    calculation_spec,
    score_from_matrix,
    sha256,
)


def candidate_features(request: RectificationRequest) -> dict[str, Any]:
    spec = calculation_spec(request)
    spec_hash = sha256(spec)
    return {
        "algorithm_version": ALGORITHM_VERSION,
        "calculation_spec": spec,
        "calculation_spec_hash": spec_hash,
        "candidate_feature_snapshot": build_candidate_feature_snapshot(request, spec_hash),
        "can_confirm_exact_minute": False,
    }


def score_candidates(request: RectificationRequest) -> dict[str, Any]:
    built = build_event_contribution_matrix(request)
    rows = score_from_matrix(request, built)
    spec = calculation_spec(request)
    spec_hash = sha256(spec)
    diagnostics = run_diagnostics(request, rows, built)
    fingerprint = sha256(request)
    return {
        "result_id": str(uuid5(NAMESPACE_URL, f"{ALGORITHM_VERSION}:{fingerprint}")),
        "algorithm_version": ALGORITHM_VERSION,
        "calculation_spec": spec,
        "calculation_spec_hash": spec_hash,
        "candidate_scores": [{
            "time": row["time"],
            "score": row["score"],
            "supporting_event_ids": [item["event_id"] for item in row["evidence"] if item["points"] > 0],
            "conflicting_event_ids": [item["event_id"] for item in row["evidence"] if item["points"] < 0],
        } for row in rows],
        "event_contribution_matrix": built["matrix"],
        "candidate_feature_snapshot": build_candidate_feature_snapshot(request, spec_hash, built.get("static_contexts")),
        "diagnostics": diagnostics,
        "robustness": {
            "neighbor_support_minutes": diagnostics["neighbor_support_minutes"],
            "leave_one_out_retention_rate": diagnostics["leave_one_event_out_retention_rate"],
            "leave_one_domain_out_retention_rate": diagnostics["leave_one_domain_out_retention_rate"],
            "date_sensitivity_retention_rate": diagnostics["date_sensitivity_retention_rate"],
        },
        "missing_layers": built["missing_layers"],
        "can_confirm_exact_minute": False,
    }


def diagnostics(request: RectificationRequest) -> dict[str, Any]:
    scored = score_candidates(request)
    return {
        "result_id": scored["result_id"],
        "algorithm_version": scored["algorithm_version"],
        "calculation_spec_hash": scored["calculation_spec_hash"],
        "diagnostics": scored["diagnostics"],
        "missing_layers": scored["missing_layers"],
        "can_confirm_exact_minute": False,
    }
