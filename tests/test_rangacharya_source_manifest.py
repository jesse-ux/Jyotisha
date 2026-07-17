import json
from pathlib import Path


MANIFEST = Path("references/rangacharya_source_manifest.json")


def test_manifest_exists_and_has_required_sections():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert "sources" in data
    assert "rules" in data
    assert "validation_ladder" in data


def test_manifest_does_not_contain_secrets():
    text = MANIFEST.read_text(encoding="utf-8")
    assert "sk_live_" not in text
    assert "api_key" not in text.lower()


def test_rules_default_below_adjudication():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for rule in data["rules"]:
        assert rule["status"] in {
            "transcribed",
            "source_verified",
            "golden_verified",
            "engine_cross_checked",
            "case_calibrated",
            "blocked",
        }
        assert rule["status"] != "adjudication_enabled"
        assert rule["adjudication_enabled"] is False


def test_screenshot_source_paths_are_located_and_hashed():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source = next(item for item in data["sources"] if item["id"] == "uploaded_screenshots_20260716")
    assert source["extraction_status"] == "located_and_hashed_ocr_blocked_tesseract_missing"
    assert len(source["paths"]) == 6
    assert all("/文件仓库/印度占星文章/260716/" in path for path in source["paths"])
    assert set(source["sha256"]) == {
        "IMG_3502.PNG",
        "IMG_3503.PNG",
        "IMG_3504.PNG",
        "IMG_3505.PNG",
        "IMG_3506.PNG",
        "IMG_3507.PNG",
    }
