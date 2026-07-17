from __future__ import annotations

from pathlib import Path

from scripts.public_release_privacy_scan import build_report, deny_patterns, iter_release_files, scan_text


def test_public_release_privacy_scan_finds_private_configured_pattern(monkeypatch) -> None:
    monkeypatch.setenv("PUBLIC_RELEASE_DENY_PATTERNS", "SECRET_BIRTH_TOKEN")
    findings = scan_text(
        Path("sample.py"),
        "safe text SECRET_BIRTH_TOKEN",
        deny_patterns(),
    )
    assert {item["rule_id"] for item in findings} == {"private_env_pattern_01"}


def test_public_release_privacy_scan_has_no_release_findings() -> None:
    report = build_report()
    assert report["status"] == "pass", report["findings"][:20]
    assert report["finding_count"] == 0


def test_public_release_privacy_scan_supports_unpacked_zip_without_git(tmp_path: Path) -> None:
    (tmp_path / "INSTALL.md").write_text("safe install text\n", encoding="utf-8")
    (tmp_path / "scratch").mkdir()
    (tmp_path / "scratch" / "ignored.md").write_text("SECRET_BIRTH_TOKEN\n", encoding="utf-8")

    assert [path.name for path in iter_release_files(tmp_path)] == ["INSTALL.md"]
    report = build_report(tmp_path)
    assert report["status"] == "pass", report["findings"]


def test_public_release_privacy_scan_rejects_executable_redaction_placeholder(tmp_path: Path) -> None:
    (tmp_path / "unsafe.py").write_text("year = REDACTED_YEAR\n", encoding="utf-8")
    report = build_report(tmp_path)
    assert report["status"] == "fail"
    assert report["findings"][0]["rule_id"] == "executable_redaction_placeholder"


def test_private_workspace_directories_are_gitignored() -> None:
    gitignore = (Path(__file__).resolve().parents[1] / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "/scratch/" in gitignore
    assert "/.serena/" in gitignore
