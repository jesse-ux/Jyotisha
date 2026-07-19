from scripts.minute_rectification_holdout_validator import validate


def test_empty_public_minute_protocol_blocks_verified_claims() -> None:
    report = validate()
    assert report["status"] == "blocked_awaiting_public_aa_cases"
    assert report["verified_minute_claim_allowed"] is False
    assert report["valid_public_aa_cases"] == 0
