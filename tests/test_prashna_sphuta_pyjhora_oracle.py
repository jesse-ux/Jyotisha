import json
from pathlib import Path


def test_public_pyjhora_prashna_sphuta_packet_is_numeric_and_guarded() -> None:
    packet = json.loads(
        Path("references/oracle/prashna_sphuta_pyjhora_public_smoke.json").read_text(encoding="utf-8")
    )

    assert packet["status"] == "local_parity_verified_single_case"
    assert packet["birth_data_policy"] == "public_synthetic_smoke_only"
    assert packet["capture"]["raw_response_available"] is True
    assert packet["engine"]["license_boundary"].startswith("AGPL external benchmark")
    assert set(packet["outputs"]) == {
        "gulika", "kunda_lagna", "tri_sphuta", "chatur_sphuta", "pancha_sphuta"
    }
    for row in packet["outputs"].values():
        assert 0 <= row["sign_index"] < 12
        assert 0 <= row["degree_in_sign"] < 30
    assert packet["local_comparison"]["status"] == "pass"
    assert max(
        value for key, value in packet["local_comparison"].items() if key.endswith("delta_degrees")
    ) <= packet["local_comparison"]["tolerance_degrees"]
    assert "remain required" in packet["boundary"]
