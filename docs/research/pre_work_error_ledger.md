# Pre-Work Error Ledger

Purpose: read this file before substantial project work. It exists to stop repeat mistakes caused by multiple Codex windows, WorkBuddy mirrors, local drafts, backup folders, and partial cloud-git visibility.

## Mandatory Pre-Work Check

Run or consciously verify:

```bash
sed -n '1,220p' AGENTS.md
sed -n '1,260p' docs/research/pre_work_error_ledger.md
git status --short --branch
git remote -v
python3 scripts/pre_work_check.py --remote-timeout 8 --command-timeout 45
```
The one-command gate must cover:
- `tests/test_runtime_import_boundaries.py`
- `tests/test_project_fragment_governance.py`
- `tests/test_preflight_fragment_scan.py`
- `tests/test_remote_repo_visibility_check.py`
- `tests/test_pre_work_check.py`

For large architecture or release work, also read:

- `docs/research/whole_machine_fragment_sweep_round25_2026_06_25.md`
- `docs/research/whole_machine_fragment_sweep_2026_07_05.md`
- `docs/research/unique_main_chain_map_2026_07_01.md`
- `docs/research/local_drafts_2026_06_disposition.md`

## Error Ledger

| ID | Error / Risk | Current Status | Required Guard |
|---|---|---|---|
| ERR-001 | Runtime code pulled modules from `.workbuddy` distribution mirror. | resolved | Keep `tests/test_runtime_import_boundaries.py`; `.workbuddy` is reference only. |
| ERR-002 | `mcp_server.py` documentation implied `.workbuddy` was a runtime path. | resolved | MCP top docs must point to main repo runtime; mirror wording must say distribution/reference only. |
| ERR-003 | `local_drafts` mixed high-value research with disposable drafts. | mitigated | Use `docs/research/local_drafts_2026_06_disposition.md`; do not delete or promote drafts ad hoc. |
| ERR-004 | Multiple local folders contain Jyotish fragments, older adapters, and WorkBuddy mirrors. | active | Read latest fragment sweep before changing adapters, oracle paths, or skill runtime boundaries. |
| ERR-005 | Terminal git access to GitHub can fail even when the browser can open the repo. | active | Use `python3 scripts/remote_repo_visibility_check.py`; do not claim cloud sync unless status is `verified`. |
| ERR-006 | Whole-machine `find` can time out when run too broadly. | active | Use split scans by directory and bounded `-maxdepth`; record timeouts as findings. |
| ERR-007 | `.workbuddy/skills/jyotish-vedic-astrology` is a dirty historical mirror. | active | Never copy it over main repo. Use only for read-only comparison. |
| ERR-008 | Current main workspace may be dirty with user/Codex changes. | active | Never reset or checkout. Read touched files before editing. |
| ERR-009 | Astrology interpretation can drift into story-fitting from conversation history. | active | For blind technical reports, use only declared evidence packets/PDF and mark MEVG/real-case gaps. |
| ERR-010 | VedAstro official/cloud evidence can be partial or dasha-conflicting. | active | Mark official closure partial unless exact endpoint/settings and raw output are verified. |
| ERR-011 | Bare `pytest` command may be missing from PATH even when pytest module exists. | active | Use `python3 -m pytest ...` in acceptance commands. |
| ERR-012 | Governance tests can fail if wording is narrower than the actual guardrail. | observed 2026-07-05 | Keep tests tied to explicit user-facing terms such as `开工前` and the ledger path. |
| ERR-013 | GitHub API can fail from terminal Python even when browser/Web can open GitHub. | active | Treat `remote_repo_visibility_check.py` status `blocked` as authoritative for terminal parity; browser visibility alone is not sync proof. |
| ERR-014 | Pre-work checks can be skipped when split across several manual commands. | mitigated | Use `python3 scripts/pre_work_check.py` as the one-command pre-work gate. |
| ERR-015 | One-command pre-work can exceed desktop outer timeout if child command timeout is too wide or scan runs twice. | observed 2026-07-05 | Keep pytest child timeout bounded at 45s; let `pre_work_check.py` cache `preflight_fragment_scan.py` output for `tests/test_preflight_fragment_scan.py`. |
| ERR-016 | Full `tests/test_api_server_security.py` can exceed the desktop outer timeout. | observed 2026-07-05 | Use focused API test slices during development; reserve full API file run for longer verification windows. |
| ERR-017 | Pre-work gate could pass without checking the older Round 25 fragment sweep or aggregate external-engine adapter diagnostics. | mitigated 2026-07-05 | `scripts/pre_work_check.py` must require both whole-machine sweep docs and run `scripts/diagnose_external_engine_adapters.py --json` before substantial work. |
| ERR-018 | External engine blockers can be described verbally but not carried into diagnostics. | mitigated 2026-07-05 | `diagnose_external_engine_adapters.py` must expose VedAstro closure plan and PyJHora/JHora install/license/ephemeris boundary; keep `docs/research/external_engine_blocker_research_2026_07_05.md` current. |
| ERR-019 | WorkBuddy/cloud/local acceptance summaries can invent pass counts, stale asset counts, non-existent error docs, or wrong dasha windows. | mitigated 2026-07-06 | Read `docs/research/user_invocation_acceptance_error_log_2026_07_06.md`; run `scripts/user_invocation_acceptance_check.py` and `tests/test_user_invocation_acceptance_contract.py` before accepting ordinary-user skill invocation validation claims. |
| ERR-020 | VedAstro official raw responses can be archived but hard to audit if no manifest/API listing exposes them. | mitigated 2026-07-08 | Keep `list_official_raw_response_archives()` and `GET /api/vedastro_gateway/archives`; tests must prove archived official raw responses are enumerable. |
| ERR-021 | VedAstro raw archive manifests can exist outside the high-rigor evidence packet, leaving final reports unable to prove whether official raw evidence was archived. | mitigated 2026-07-08 | Keep `vedastro_official_raw_archive_manifest` in `machine_evidence_packet.sections` for API and MCP strict workflows. |
| ERR-022 | Technique Audit Table can show VedAstro cloud state but omit whether archived official raw evidence is actually auditable. | mitigated 2026-07-08 | Keep `VedAstro Raw Archive Manifest` as a first-class Technique Audit Table row immediately after `VedAstro Cloud State`. |

## Fragment Sweep Command Set

Use split scans, not one unbounded full-home command:

```bash
for d in <home>/Documents <home>/WorkBuddy <home>/.workbuddy <home>/Downloads <home>/Desktop <home>/.codex/attachments; do
  [ -d "$d" ] && find "$d" -maxdepth 6 -type d -name .git 2>/dev/null | sed 's#/.git$##'
done | rg -i '印度|jyotish|vedic|astro|yinduzhanxing|workbuddy|星轨|codex|talk' | sort
```

```bash
for d in <home>/Documents <home>/WorkBuddy <home>/.workbuddy <home>/Downloads <home>/Desktop <home>/.codex/attachments; do
  [ -d "$d" ] && find "$d" -maxdepth 7 -type f \( -iname '*jyotish*' -o -iname '*vedic*' -o -iname '*jhora*' -o -iname '*shadbala*' -o -iname '*ashtakoot*' -o -iname '*印度占星*' -o -iname '*yinduzhanxing*' \) 2>/dev/null
done
```
