from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import capture_commercial_astrology_e2e_contexts as capture_script  # noqa: E402


def test_capture_writes_runtime_contexts_without_required_layer_echo(tmp_path: Path) -> None:
    manifest = capture_script.capture(output_dir=tmp_path)

    assert manifest["question_count"] == 10
    assert (tmp_path / "capture_manifest.json").exists()
    for row in manifest["rows"]:
        context_path = ROOT / row["context_file"] if not Path(row["context_file"]).is_absolute() else Path(row["context_file"])
        data = json.loads(context_path.read_text(encoding="utf-8"))
        assert data["success"] is True
        assert "consumer_context" in data
        assert "required_layers" not in data
