from __future__ import annotations

import os
from pathlib import Path


from scripts import local_env


def test_load_local_env_reads_repo_env_file_without_overriding_explicit_env(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / ".env.local"
    env_file.write_text(
        "VEDASTRO_API_ENDPOINT=https://api.vedastro.org/api\n"
        "VEDASTRO_ENABLE_NETWORK=1\n"
        "VEDASTRO_API_KEY=from_file\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("VEDASTRO_API_ENDPOINT", raising=False)
    monkeypatch.setenv("VEDASTRO_API_KEY", "from_process")

    try:
        loaded = local_env.load_local_env(root=tmp_path)

        assert loaded == [env_file]
        assert os.environ["VEDASTRO_API_ENDPOINT"] == "https://api.vedastro.org/api"
        assert os.environ["VEDASTRO_ENABLE_NETWORK"] == "1"
        assert os.environ["VEDASTRO_API_KEY"] == "from_process"
    finally:
        os.environ.pop("VEDASTRO_API_ENDPOINT", None)
        os.environ.pop("VEDASTRO_ENABLE_NETWORK", None)


def test_load_local_env_ignores_missing_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("VEDASTRO_API_ENDPOINT", raising=False)
    os.environ.pop("VEDASTRO_ENABLE_NETWORK", None)

    loaded = local_env.load_local_env(root=tmp_path)

    assert loaded == []
    assert "VEDASTRO_API_ENDPOINT" not in os.environ


def test_load_local_env_does_not_resurrect_deleted_values_after_bootstrap(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / ".env.local"
    env_file.write_text("VEDASTRO_ENABLE_NETWORK=1\n", encoding="utf-8")
    monkeypatch.delenv("VEDASTRO_ENABLE_NETWORK", raising=False)

    loaded = local_env.load_local_env(root=tmp_path)
    assert loaded == [env_file]
    assert os.environ["VEDASTRO_ENABLE_NETWORK"] == "1"

    monkeypatch.delenv("VEDASTRO_ENABLE_NETWORK", raising=False)
    loaded_again = local_env.load_local_env(root=tmp_path)

    assert loaded_again == []
    assert "VEDASTRO_ENABLE_NETWORK" not in os.environ


def test_load_local_env_respects_explicit_skip_flag(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / ".env.local"
    env_file.write_text("VEDASTRO_API_ENDPOINT=https://api.vedastro.org/api\n", encoding="utf-8")
    monkeypatch.delenv("VEDASTRO_API_ENDPOINT", raising=False)
    monkeypatch.setenv("JYOTISH_SKIP_LOCAL_ENV", "1")

    loaded = local_env.load_local_env(root=tmp_path)

    assert loaded == []
    assert "VEDASTRO_API_ENDPOINT" not in os.environ
