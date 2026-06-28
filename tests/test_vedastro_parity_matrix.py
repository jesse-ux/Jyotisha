import json
from pathlib import Path

from scripts import vedastro_parity_matrix


def _row(matrix, capability):
    for row in matrix["rows"]:
        if row["vedastro_capability"] == capability:
            return row
    raise AssertionError(f"missing row: {capability}")


def test_build_matrix_has_p0_public_vedastro_capability_rows():
    matrix = vedastro_parity_matrix.build_matrix()

    assert matrix["scope"] == "vedastro_parity_matrix"
    assert matrix["summary"]["row_count"] >= 10
    assert matrix["summary"]["p0_count"] >= 10

    required = {
        "EventsAtRange / Life Event Graph",
        "Ayanamsa Selection",
        "D1-D60 Divisional Charts",
        "Ashtakavarga",
        "Shadbala",
        "Jaimini / Chara Dasha",
        "Synastry / Ashtakoot",
        "Tajika Annual",
        "Prashna / Horary",
        "Report Rendering",
        "MCP / API Surface",
    }
    assert required.issubset({row["vedastro_capability"] for row in matrix["rows"]})


def test_range_scan_is_adapter_gap_not_local_complete_claim():
    matrix = vedastro_parity_matrix.build_matrix()
    row = _row(matrix, "EventsAtRange / Life Event Graph")

    assert row["priority"] == "P0"
    assert row["local_status"] in {"partial", "missing"}
    assert row["can_call_vedastro"] is True
    assert row["recommended_path"] == "hybrid_local_plus_vedastro"
    assert row["adjudicator_use"] == "oracle_only"
    assert "range" in " ".join(row["local_assets"]).lower()


def test_local_assets_still_need_parity_or_bridge_when_not_fully_exploited():
    matrix = vedastro_parity_matrix.build_matrix()

    jaimini = _row(matrix, "Jaimini / Chara Dasha")
    assert jaimini["local_status"] in {"covered", "complete"}
    assert "jaimini" in " ".join(jaimini["local_assets"]).lower()
    assert jaimini["recommended_path"] in {"local_native", "hybrid_local_plus_vedastro"}

    synastry = _row(matrix, "Synastry / Ashtakoot")
    assert synastry["local_status"] in {"covered", "complete"}
    assert any("ashtakoot" in asset.lower() for asset in synastry["local_assets"])
    assert synastry["adjudicator_use"] in {"secondary", "primary"}


def test_matrix_rows_use_allowed_contract_values():
    matrix = vedastro_parity_matrix.build_matrix()

    allowed_status = {"complete", "covered", "partial", "missing", "external_only"}
    allowed_path = {
        "local_native",
        "vedastro_adapter",
        "new_local_impl",
        "external_evidence_only",
        "hybrid_local_plus_vedastro",
    }
    allowed_fastest_lane = {
        "local_native_preferred",
        "official_mcp",
        "official_python_bridge",
        "rest_adapter",
        "hybrid_router",
        "external_evidence_only",
    }
    allowed_priority = {"P0", "P1", "P2"}
    allowed_use = {"primary", "secondary", "oracle_only", "not_used"}

    for row in matrix["rows"]:
        assert set(row) == {
            "vedastro_capability",
            "category",
            "local_status",
            "local_assets",
            "can_call_vedastro",
            "recommended_path",
            "fastest_path_lane",
            "priority",
            "license_boundary",
            "adjudicator_use",
            "gap_notes",
            "route_notes",
        }
        assert row["local_status"] in allowed_status
        assert row["recommended_path"] in allowed_path
        assert row["fastest_path_lane"] in allowed_fastest_lane
        assert row["priority"] in allowed_priority
        assert row["adjudicator_use"] in allowed_use
        assert isinstance(row["local_assets"], list)
        assert isinstance(row["route_notes"], str)


def test_render_markdown_contains_summary_and_honesty_boundary():
    matrix = vedastro_parity_matrix.build_matrix()
    markdown = vedastro_parity_matrix.render_markdown(matrix)

    assert "# VedAstro Parity Matrix" in markdown
    assert "## Honesty Boundary" in markdown
    assert "EventsAtRange / Life Event Graph" in markdown
    assert "external adapter evidence" in markdown
    assert "Fastest lane" in markdown


def test_matrix_declares_fastest_path_lane_for_high_value_rows():
    matrix = vedastro_parity_matrix.build_matrix()

    assert _row(matrix, "EventsAtRange / Life Event Graph")["fastest_path_lane"] == "rest_adapter"
    assert _row(matrix, "Shadbala")["fastest_path_lane"] == "official_python_bridge"
    assert _row(matrix, "MCP / API Surface")["fastest_path_lane"] == "official_mcp"
    assert _row(matrix, "D1-D60 Divisional Charts")["fastest_path_lane"] == "local_native_preferred"


def test_write_outputs_creates_json_and_markdown(tmp_path):
    matrix = vedastro_parity_matrix.build_matrix()
    json_path = tmp_path / "matrix.json"
    md_path = tmp_path / "matrix.md"

    vedastro_parity_matrix.write_outputs(matrix, json_path=json_path, markdown_path=md_path)

    loaded = json.loads(json_path.read_text())
    assert loaded["scope"] == "vedastro_parity_matrix"
    assert md_path.read_text().startswith("# VedAstro Parity Matrix")
