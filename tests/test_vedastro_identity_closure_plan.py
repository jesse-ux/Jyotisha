from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "research" / "vedastro_identity_closure_plan_2026_07_19.md"


def test_vedastro_identity_plan_keeps_hosted_output_observation_only() -> None:
    text = DOC.read_text(encoding="utf-8")

    for token in [
        "VedAstro hosted API remains observation-only",
        "build identity, method semantics, and deployment version are not archived",
        "does not prove which side is true",
        "tune production predictions from hosted output with unknown build identity",
        "silently prefer VedAstro or local output by majority vote",
    ]:
        assert token in text


def test_vedastro_identity_plan_requires_self_host_supply_chain_fields() -> None:
    text = DOC.read_text(encoding="utf-8")

    for token in [
        "source commit",
        "NuGet package hash",
        "DLL SHA-256",
        "assembly version",
        "public method inventory",
        "container image digest",
        "required_self_host_evidence",
        "truth_upgrade_gate",
    ]:
        assert token in text
