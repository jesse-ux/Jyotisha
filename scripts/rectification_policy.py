"""Shared birth-time rectification convergence policy."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

_POLICY_PATH = Path(__file__).resolve().parents[1] / "references" / "rectification_policy.v1.json"
POLICY: Final[dict[str, int | str]] = json.loads(_POLICY_PATH.read_text(encoding="utf-8"))

MIN_SCORING_EVENTS: Final = int(POLICY["minScoringEvents"])
MIN_CONFIRMATION_EVENTS: Final = int(POLICY["minConfirmationEvents"])
MIN_CONFIRMATION_DOMAINS: Final = int(POLICY["minConfirmationDomains"])
MAX_EXTERNAL_VALIDATION_WIDTH_MINUTES: Final = int(POLICY["maxExternalValidationWidthMinutes"])
MAX_CONFIRMATION_WIDTH_MINUTES: Final = int(POLICY["maxConfirmationWidthMinutes"])
MIN_CONFIRMATION_MARGIN_PERCENT: Final = int(POLICY["minConfirmationMarginPercent"])
MAX_PLATEAU_ROUNDS: Final = int(POLICY["maxPlateauRounds"])
