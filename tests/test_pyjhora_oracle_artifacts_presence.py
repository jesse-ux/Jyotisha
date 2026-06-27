from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "references" / "oracle" / "artifacts"


def test_pyjhora_blackbox_artifacts_exist_for_current_hard_fronts() -> None:
    required = [
        "pyjhora_steve_jobs_dasha_stdout_20260627.txt",
        "pyjhora_steve_jobs_shadbala_lahiri_stdout_20260627.txt",
        "pyjhora_steve_jobs_varshaphala_1984_lahiri_stdout_20260627.txt",
        "pyjhora_user_REDACTED_YEAR_shadbala_lahiri_stdout_20260627.txt",
        "pyjhora_historical_epoch_dasha_stdout_20260627.txt",
    ]
    for name in required:
        path = ARTIFACTS / name
        assert path.exists(), name
        assert path.read_text(encoding="utf-8").strip(), name


def test_pyjhora_pending_packets_exist_for_replayable_external_capture() -> None:
    pending = ARTIFACTS / "pending_packets"
    required = [
        "external_template_steve_jobs_dasha_lahiri_pyjhora_20260627.json",
        "external_template_user_REDACTED_YEAR_shadbala_lahiri_pyjhora_20260627.json",
        "external_template_steve_jobs_varshaphala_1984_lahiri_pyjhora_20260627.json",
        "external_template_historical_epoch_lahiri_pyjhora_20260627.json",
    ]
    for name in required:
        assert (pending / name).exists(), name
