from __future__ import annotations

from scripts.remote_repo_visibility_check import github_slug_from_remote_url, parse_ls_remote


def test_github_slug_from_remote_url_accepts_ssh_and_https() -> None:
    assert github_slug_from_remote_url("git@github.com:732642856/yinduzhanxing.git") == "732642856/yinduzhanxing"
    assert github_slug_from_remote_url("https://github.com/732642856/yinduzhanxing.git") == "732642856/yinduzhanxing"


def test_parse_ls_remote_separates_heads_and_tags() -> None:
    parsed = parse_ls_remote(
        "\n".join(
            [
                "abc123 refs/heads/main",
                "def456 refs/heads/codex/release-hygiene-ci",
                "aaa111 refs/tags/v1.0.0",
                "bbb222 refs/tags/v1.0.0^{}",
            ]
        )
    )
    assert parsed["heads"]["main"] == "abc123"
    assert parsed["heads"]["codex/release-hygiene-ci"] == "def456"
    assert parsed["tags"]["v1.0.0"] == "aaa111"
    assert parsed["ref_count"] == 3
