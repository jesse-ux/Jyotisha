from pathlib import Path

from scripts.vedastro_reproducible_build_probe import build_identity


def test_build_identity_binds_source_and_container_inputs(tmp_path: Path) -> None:
    (tmp_path / "API").mkdir()
    (tmp_path / "API/Dockerfile").write_text(
        "FROM example/sdk:7@sha256:" + "a" * 64 + " AS build\nFROM build AS final\n",
        encoding="utf-8",
    )
    (tmp_path / "API/API.csproj").write_text("<Project />\n", encoding="utf-8")
    report = build_identity(tmp_path, source_commit="1f3a464", image_inspect=None)

    assert report["source_commit"] == "1f3a464"
    assert len(report["dockerfile_sha256"]) == 64
    assert report["base_images"] == ["example/sdk:7@sha256:" + "a" * 64]
    assert len(report["project_file_hashes"]["API/API.csproj"]) == 64
    assert report["status"] == "source_pinned_image_not_built"


def test_build_identity_records_built_image_digest(tmp_path: Path) -> None:
    (tmp_path / "API").mkdir()
    (tmp_path / "API/Dockerfile").write_text("FROM example/sdk:7\n", encoding="utf-8")
    report = build_identity(
        tmp_path,
        source_commit="abc123",
        image_inspect={"Id": "sha256:" + "b" * 64, "RepoDigests": ["repo@sha256:" + "c" * 64]},
    )

    assert report["status"] == "reproducible_candidate_built"
    assert report["image_id"] == "sha256:" + "b" * 64
    assert report["repo_digests"] == ["repo@sha256:" + "c" * 64]
