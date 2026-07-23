#!/usr/bin/env python3
"""Compare KP significator workflow gate with local runtime probe output."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "references/oracle/kp_significator_workflow_gate_2026_07_23.json"
PROBE = ROOT / "references/oracle/kp_precision_timing_probe_2026_07_23.json"
OUT = ROOT / "references/oracle/kp_significator_runtime_delta_2026_07_23.json"


def build_report() -> dict[str, Any]:
    workflow = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    probe = json.loads(PROBE.read_text(encoding="utf-8"))
    rows = {
        "workflow_step_count": len(workflow["workflow_steps"]),
        "workflow_blocked_steps": workflow["summary"]["blocked_step_count"],
        "probe_claim_status": probe["claim_status"],
        "probe_exact_cusp_status": probe["kp_cusp_contract"]["exact_cusp_status"],
        "probe_significator_policy": probe["kp_cusp_contract"]["significator_policy"],
        "probe_planet_significator_count": len(probe["planet_significators"]),
        "probe_house_significator_count": len(probe["house_significators"]),
        "ruling_planet_fields": sorted(probe["ruling_planets"].keys()),
    }
    return {
        "scope": "kp_significator_runtime_delta",
        "created_at": date.today().isoformat(),
        "claim_status": "observation_only",
        "truth_matrix_allowed": False,
        "production_tuning_allowed": False,
        "workflow_packet": str(WORKFLOW.relative_to(ROOT)),
        "runtime_packet": str(PROBE.relative_to(ROOT)),
        "summary": rows,
        "boundary": (
            "Local runtime can expose KP star/sub-lord and significator fields, but it remains observation-only. "
            "Exact KP timing stays blocked until a public numeric oracle and independent negative holdout close."
        ),
    }


def main() -> int:
    OUT.write_text(json.dumps(build_report(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(build_report(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
