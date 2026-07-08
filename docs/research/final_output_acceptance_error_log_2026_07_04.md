# Final Output Acceptance Error Log - 2026-07-04

Purpose: read this log before editing final report / evidence packet artifacts. Keep errors here so the same status drift does not repeat.

## Known Errors

| ID | Error | Seen In | Impact | Prevention |
|---|---|---|---|---|
| FOA-001 | status metadata drift | `jhora_master_evidence_packet_public_sample_19550224_1915.v13.json` and later packet chain | Top-level packet said final, but metadata stayed stale/draft or old version. | `tests/test_final_jhora_evidence_packet_acceptance.py` asserts top-level status, metadata status, `current_version`, `packet_version`, and `canonical_packet`. |
| FOA-002 | canonical packet drift | latest packet advanced to v24 while metadata still pointed at v15 | Agents may cite old packet as current truth. | Latest-version acceptance resolves numeric highest packet and requires metadata + ledger to point to that file. |
| FOA-003 | stale next-step ledger | ledger still said next useful step was Chapter 04 after chapters 04-06, PDF, and raw appendix existed | User/operator can continue wrong workstream. | Ledger acceptance rejects the old Chapter 04 next-step phrase and requires an Acceptance/error-log gate next step. |
| FOA-004 | blank PDF artifact | prior ReportLab PDF attempt was blank/invalid and discarded | A report artifact can exist but be unusable. | Acceptance requires PDF path, HTML path, rendered QA pages, and non-trivial file sizes. |
| FOA-005 | chained latest-packet drift | `jhora_master_evidence_packet_public_sample_19550224_1915.v25.json` appeared after v24, then v26 appeared after v25 while metadata still pointed one version behind | Fixing only one packet can become stale as later packet versions appear. | Acceptance always resolves the numeric highest packet and checks that exact packet, not a hard-coded version. |
| FOA-006 | wrong quality-gate CLI flag | `python3 scripts/run_quality_gate.py --runtime-truth` | The gate does not run; command exits with argument error. | Use `python3 scripts/run_quality_gate.py --profile runtime-truth`. |
| FOA-007 | long runtime-truth gate timeout | `python3 scripts/run_quality_gate.py --profile runtime-truth` exited 124 after 120s in this Codex tool session | A broad gate may not provide timely evidence inside the current command window. | Run focused acceptance first, then split runtime-truth into compile, inventory, diagnostics, and pytest target groups. |
| FOA-008 | captured quality-gate output hid the slow step | `scripts/run_quality_gate.py` used `capture_output=True` for child commands | Long gates appeared blank until timeout, making the stuck subcommand invisible. | `run()` now streams child output directly. |

## Work Rule

Before changing `scratch/local/pdf_review_123456/` final artifacts:

1. Read this file.
2. Run `python3 -m pytest -q tests/test_final_jhora_evidence_packet_acceptance.py`.
3. For the broader runtime gate, prefer `PYTHONUNBUFFERED=1 python3 scripts/run_quality_gate.py --profile runtime-truth`; if it times out, split the gate into compile, inventory, diagnostics, and pytest target groups.
4. If it fails, record the new error here before patching status/docs.
