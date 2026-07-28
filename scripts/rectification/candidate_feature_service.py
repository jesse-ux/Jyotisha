from __future__ import annotations

from typing import Any, Sequence

from scripts.active_rectification_event_engine import compute_candidate_static_contexts
from scripts.rectification.contracts import RectificationRequest
from scripts.rectification.scoring_service import ALGORITHM_VERSION, sha256


def build_candidate_feature_snapshot(
    request: RectificationRequest,
    calculation_spec_hash: str,
    static_contexts: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    contexts = list(static_contexts) if static_contexts is not None else compute_candidate_static_contexts(request)
    features = [context["feature"] for context in contexts]
    return {
        "calculation_spec_hash": calculation_spec_hash,
        "algorithm_version": ALGORITHM_VERSION,
        "candidate_count": len(features),
        "feature_hash": sha256(features),
        "features": features,
    }
