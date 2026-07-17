from pathlib import Path

from scripts.pyjhora_parity_summary import summarize_matrix


def test_summary_marks_partial_verified_when_only_d1_d9_d10_dasha_are_covered(tmp_path: Path):
    matrix = tmp_path / "matrix.csv"
    matrix.write_text(
        "section,status\nascendant,match\nD9,match\nD10,match\ndasha,match\n",
        encoding="utf-8",
    )

    result = summarize_matrix(matrix, settings={"ayanamsa": "lahiri", "node_mode": "mean"})

    assert result["status"] == "partial_verified"
    assert result["full_parity_verified"] is False
    assert result["missing_required_outputs"] == ["D2", "D4", "Shadbala", "Ashtakavarga"]
