# User Invocation Acceptance Error Log - 2026-07-06

Purpose: read this before accepting WorkBuddy, cloud Git, local mirror, or AI-app validation claims about ordinary-user Jyotish usage.

## Trigger

A WorkBuddy validation summary claimed project-wide acceptance facts that were not reproducible from the main repository.

## Errors Found

| ID | Error | Verified Correction | Guard |
|---|---|---|---|
| WB-001 | Claimed `29/29` cross-validation without a committed, reproducible script or test artifact. | No matching `29/29` evidence artifact was found in main repo, `.workbuddy`, or bounded Desktop/Documents/Downloads scans. | Require a committed test/script path and rerun command before accepting pass counts. |
| WB-002 | Claimed stale asset counts such as `175` scripts and `157` tests. | Main repo counts differ. Counts must be regenerated from the current checkout, not memory or mirror state. | Use `find` / `rg --files` on the main repo checkout. |
| WB-003 | Claimed `印度占星分析错误文档.md` existed. | No such tracked project document was found. | Error docs must live under `docs/research/` and be referenced by `docs/research/pre_work_error_ledger.md`. |
| WB-004 | Claimed the fixture dasha timeline put 2027-03 in Mercury AD, with future Venus AD starting 2028-05-10. | Main engine reports 2027-03-01 as `Saturn / Venus`, AD `2027-02-27 -> 2030-04-29`. | Run `tests/test_user_invocation_acceptance_contract.py`. |
| WB-005 | Claimed `vivah-saham` still needed an import-path fix. | `scripts/jyotish_engine.py vivah-saham ...` runs successfully for the standard sample. | Do not report import breakage without running the command. |
| WB-006 | Overstated external-oracle completeness. | VedAstro/PyJHora/JHora status remains adapter-dependent and must be reported as `official_verified`, `official_blocked`, `local_fallback`, or equivalent audited state. | Run `scripts/diagnose_external_engine_adapters.py --json` and include blocked/partial rows in Technique Audit output. |

## Acceptance Commands

```bash
python3 scripts/pre_work_check.py --remote-timeout 8 --command-timeout 45
python3 scripts/user_invocation_acceptance_check.py
python3 -m pytest -q tests/test_user_invocation_acceptance_contract.py tests/test_project_fragment_governance.py
python3 scripts/diagnose_external_engine_adapters.py --json
python3 scripts/jyotish_engine.py vivah-saham --year 2000 --month 1 --day 1 --hour 12 --minute 0 --lat 0.0 --lon 0.0 --tz 0 --transit-date 2026-07-06
```

## Acceptance Rule

Ordinary-user invocation is accepted only when the current main repo proves:

- Skill/plugin/default prompt can guide a user who has no question.
- User entrypoint can start from a guided-topics request.
- Dasha fixture rejects stale WorkBuddy timing claims.
- Error ledger names this failure mode and the test that guards it.
- External oracle status is explicit, not silently upgraded.
