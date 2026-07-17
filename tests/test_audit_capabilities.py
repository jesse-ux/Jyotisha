"""Registry validator regression tests."""

from __future__ import annotations

from scripts.audit_capabilities import validate_registry


def test_blocked_is_a_valid_honest_technique_status() -> None:
    report = validate_registry({
        "techniques": {
            "external_oracle": {
                "name": "External oracle",
                "domains": ["validation"],
                "status": "blocked",
                "knowledge_refs": [],
                "commands": [],
                "output_paths": [],
                "audit_label": "External oracle",
                "missing_impact": "Cannot claim external parity.",
            }
        },
        "routes": {},
    })

    assert report["valid"] is True
