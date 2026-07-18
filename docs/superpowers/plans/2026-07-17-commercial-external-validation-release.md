# Commercial External Validation Release Implementation Plan
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the commercial repository's public external-validation evidence a versioned, hash-verified release gate while preserving every unresolved external-oracle boundary.

**Architecture:** The existing public research reports remain the evidence payload. A small manifest records their expected SHA-256 digests and declared engine boundaries; a standalone Python gate validates file integrity and projects the VedAstro/JHora closure states into machine-readable output. The runtime-truth quality profile executes the gate so evidence drift blocks acceptance without requiring private raw artifacts or credentials.

**Tech Stack:** Python 3 standard library, JSON, pytest, existing `scripts/run_quality_gate.py` profiles.

### Task 1: Specify the public evidence release

**Files:**
- Create: `references/evidence_manifests/commercial_external_validation_release.v1.json`
- Test: `tests/test_external_validation_release_gate.py`

- [x] **Step 1: Write the failing manifest-contract test**

```python
def test_release_manifest_declares_public_assets_and_external_boundaries() -> None:
    manifest = _manifest()
    assert manifest["schema_version"] == 1
    assert manifest["release_scope"] == "public_research_evidence_snapshot"
    assert manifest["engines"]["PyJHora"]["status"] == "available"
    assert manifest["engines"]["VedAstro"]["status"] == "blocked"
    assert manifest["engines"]["JHora"]["official_raw_status"] != "verified"
```

- [x] **Step 2: Run the test to verify it fails**

Run: `python3 -m pytest -q tests/test_external_validation_release_gate.py::test_release_manifest_declares_public_assets_and_external_boundaries`

Expected: FAIL because the manifest and `_manifest` helper do not exist.

- [x] **Step 3: Add the versioned manifest**

Record the eight already-versioned research reports, their SHA-256 digests, scope, and non-escalation boundaries. Record `PyJHora` and `jyotishganit` as locally available, `VedAstro` as blocked pending official replay closure, and JHora raw evidence as not verified.

- [x] **Step 4: Run the manifest-contract test**

Run: `python3 -m pytest -q tests/test_external_validation_release_gate.py::test_release_manifest_declares_public_assets_and_external_boundaries`

Expected: PASS.

### Task 2: Implement integrity and boundary gate

**Files:**
- Create: `scripts/external_validation_release_gate.py`
- Modify: `tests/test_external_validation_release_gate.py`

- [x] **Step 1: Write failing gate behavior tests**

```python
def test_evaluate_manifest_accepts_current_public_release() -> None:
    report = gate.evaluate_manifest(MANIFEST)
    assert report["status"] == "pass"
    assert report["summary"]["assets_verified"] == report["summary"]["assets_total"]
    assert report["summary"]["production_tuning_allowed"] is False

def test_evaluate_manifest_reports_digest_drift(tmp_path: Path) -> None:
    manifest = _copy_manifest_with_one_bad_digest(tmp_path)
    report = gate.evaluate_manifest(manifest)
    assert report["status"] == "blocked"
    assert report["assets"][0]["integrity"] == "mismatch"
```

- [x] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest -q tests/test_external_validation_release_gate.py -v`

Expected: FAIL because `scripts.external_validation_release_gate` does not exist.

- [x] **Step 3: Add the minimal gate**

Implement `evaluate_manifest(path)` using `hashlib.sha256`; return JSON with per-asset existence/integrity, engine states, `production_tuning_allowed: false`, and `status: pass` only when every asset matches. Add CLI `--manifest`, `--format json`, and `--require-match`; `--require-match` returns non-zero for missing or mismatched assets only, not merely because VedAstro remains blocked.

- [x] **Step 4: Run focused tests and CLI**

Run:

```bash
python3 -m pytest -q tests/test_external_validation_release_gate.py
python3 scripts/external_validation_release_gate.py --format json --require-match
```

Expected: tests PASS; CLI returns zero with `status: pass` and preserves `VedAstro: blocked` plus `production_tuning_allowed: false`.

### Task 3: Wire the gate into runtime truth

**Files:**
- Modify: `scripts/run_quality_gate.py`
- Modify: `tests/test_external_validation_release_gate.py`

- [x] **Step 1: Write the failing quality-profile test**

```python
def test_runtime_truth_profile_runs_external_validation_release_gate() -> None:
    text = (ROOT / "scripts" / "run_quality_gate.py").read_text(encoding="utf-8")
    assert "external_validation_release_gate.py" in text
```

- [x] **Step 2: Run it to verify it fails**

Run: `python3 -m pytest -q tests/test_external_validation_release_gate.py::test_runtime_truth_profile_runs_external_validation_release_gate`

Expected: FAIL because the release gate is not yet part of the quality gate.

- [x] **Step 3: Add the runtime-truth command**

Add the release-gate invocation to the runtime-truth command list with `--require-match`; retain the existing oracle collection semantics and do not convert blocked external engines into failures.

- [x] **Step 4: Run runtime-truth and focused regression suite**

Run:

```bash
python3 scripts/run_quality_gate.py --profile runtime-truth
python3 -m pytest -q tests/test_external_validation_release_gate.py tests/test_oracle_closure_master_dashboard.py tests/test_three_engine_parity_replay_validator.py tests/test_cross_project_contract.py tests/test_cross_project_sync_status.py
```

Expected: PASS. The gate proves release integrity; output continues to state that prediction accuracy and production tuning remain blocked.

### Task 4: Record the commercial release boundary

**Files:**
- Modify: `docs/superpowers/plans/2026-07-17-commercial-external-validation-release.md`

- [x] **Step 1: Keep the gate commercial-only**

The evidence files are already byte-identical research-derived public assets. The new manifest and validator are a commercial acceptance layer, so they are deliberately not added to the bidirectional calculation-contract policy or ledger. No private scratch, credentials, or raw oracle captures are added.

- [x] **Step 2: Record the completed scope in this plan**

This release verifies public evidence integrity only. It does not claim external oracle closure, prediction accuracy, or production-tuning authorization.

- [x] **Step 3: Verify release hygiene and working tree**

Run:

```bash
git diff --check
git status --short --branch
python3 scripts/scan_public_artifact_privacy.py --format json
```

Expected: no whitespace errors, no privacy findings, and only intended files modified before commit.

- [ ] **Step 4: Commit and push**

```bash
git add docs/superpowers/plans/2026-07-17-commercial-external-validation-release.md \
  references/evidence_manifests/commercial_external_validation_release.v1.json \
  scripts/external_validation_release_gate.py \
  scripts/run_quality_gate.py \
  tests/test_external_validation_release_gate.py \
  references/cross_project_contract/sync_policy.v1.json \
  references/cross_project_contract/sync_ledger.json
git commit -m "feat: gate commercial external validation release"
git push origin codex/cross-project-contract
```

Expected: remote branch contains the integrity gate; `main` remains untouched pending merge review.
