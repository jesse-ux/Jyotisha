from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_audit_whitelist_contains_expected_truth_files() -> None:
    script = _read("scripts/sync_skill_truth_whitelist.sh")
    for expected in (
        "AGENTS.md",
        "SKILL.md",
        "references/technique_registry.json",
        "references/quick-reference-guide.md",
        "references/strict-workflow-router.md",
        "skills/jyotish-engine-modules/SKILL.md",
        "skills/jyotish-full-reading-integration/SKILL.md",
    ):
        assert expected in script


def test_stage_whitelist_contains_expected_truth_files() -> None:
    script = _read("scripts/stage_skill_truth_whitelist.sh")
    for expected in (
        "AGENTS.md",
        "SKILL.md",
        "references/technique_registry.json",
        "references/quick-reference-guide.md",
        "references/strict-workflow-router.md",
        "skills/jyotish-engine-modules/SKILL.md",
        "skills/jyotish-full-reading-integration/SKILL.md",
    ):
        assert expected in script


def test_workbuddy_sync_script_copies_expected_truth_files() -> None:
    script = _read("scripts/sync_skill_truth_to_workbuddy.sh")
    for expected in (
        'cp "$ROOT/AGENTS.md" "$WB/AGENTS.md"',
        'cp "$ROOT/SKILL.md" "$WB/SKILL.md"',
        'cp "$ROOT/references/technique_registry.json" "$WB/references/technique_registry.json"',
        'cp "$ROOT/references/quick-reference-guide.md" "$WB/references/quick-reference-guide.md"',
        'cp "$ROOT/references/strict-workflow-router.md" "$WB/references/strict-workflow-router.md"',
        'cp "$ROOT/skills/jyotish-engine-modules/SKILL.md" "$WB/skills/jyotish-engine-modules/SKILL.md"',
        'cp "$ROOT/skills/jyotish-full-reading-integration/SKILL.md" "$WB/skills/jyotish-full-reading-integration/SKILL.md"',
    ):
        assert expected in script
