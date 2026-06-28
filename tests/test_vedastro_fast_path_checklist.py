import json

from scripts import vedastro_fast_path_checklist


def test_build_checklist_exposes_all_fast_path_lanes():
    checklist = vedastro_fast_path_checklist.build_checklist()

    assert checklist["scope"] == "vedastro_fast_path_checklist"
    assert checklist["boundary"]["do_not_clone_vedastro"] is True
    assert "official_mcp" in checklist["lanes"]
    assert "official_python_bridge" in checklist["lanes"]
    assert "rest_adapter" in checklist["lanes"]
    assert "local_native_preferred" in checklist["lanes"]


def test_checklist_routes_high_value_capabilities_to_expected_lanes():
    checklist = vedastro_fast_path_checklist.build_checklist()

    def capabilities(lane: str) -> set[str]:
        return {item["capability"] for item in checklist["lanes"][lane]}

    assert "MCP / API Surface" in capabilities("official_mcp")
    assert "Shadbala" in capabilities("official_python_bridge")
    assert "EventsAtRange / Life Event Graph" in capabilities("rest_adapter")
    assert "D1-D60 Divisional Charts" in capabilities("local_native_preferred")


def test_render_markdown_contains_execution_order_and_catalog_summary():
    checklist = vedastro_fast_path_checklist.build_checklist()
    markdown = vedastro_fast_path_checklist.render_markdown(checklist)

    assert "# VedAstro 596+ Nodes Fast-Path Checklist" in markdown
    assert "Official catalog methods/events" in markdown
    assert "## Immediate Execution Order" in markdown
    assert "Official Python Bridge" in markdown


def test_write_outputs_creates_latest_files(tmp_path):
    checklist = vedastro_fast_path_checklist.build_checklist()
    json_path = tmp_path / "checklist.json"
    md_path = tmp_path / "checklist.md"

    vedastro_fast_path_checklist.write_outputs(checklist, json_path=json_path, markdown_path=md_path)

    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["scope"] == "vedastro_fast_path_checklist"
    assert md_path.read_text(encoding="utf-8").startswith("# VedAstro 596+ Nodes Fast-Path Checklist")
