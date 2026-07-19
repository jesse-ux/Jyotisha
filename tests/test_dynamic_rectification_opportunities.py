from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from scripts.dynamic_rectification_opportunities import _dimension_opportunity

TASK2_PACKET_FIXTURE = (
    Path(__file__).parents[1]
    / "frontend/tests/fixtures/task2-dynamic-rectification-packet.json"
)


def test_every_supported_dimension_emits_distinct_validator_safe_copy() -> None:
    windows = [
        {
            "window_start": "2018-01-01",
            "window_end": "2020-12-31",
            "activations": {"04:00": 1.0, "04:01": 0.0},
        },
        {
            "window_start": "2021-01-01",
            "window_end": "2023-12-31",
            "activations": {"04:00": 0.0, "04:01": 1.0},
        },
    ]

    dimensions = ["education", "relocation", "relationship", "career", "health_pressure"]
    opportunities = [
        _dimension_opportunity(dimension, windows, ["04:00", "04:01"])
        for dimension in dimensions
    ]

    assert all(opportunity is not None for opportunity in opportunities)
    contexts = [opportunity["neutral_context"] for opportunity in opportunities if opportunity]
    assert len(contexts) == len(set(contexts)) == len(dimensions)
    for dimension, opportunity in zip(dimensions, opportunities, strict=True):
        assert opportunity is not None
        context = opportunity["neutral_context"]
        prompt = opportunity["fallback_prompt"]
        labels = [item["fallback_label"] for item in opportunity["partitions"]]
        assert dimension not in context
        assert re.search(r"[\u3400-\u9fff]", context)
        assert re.search(r"[A-Za-z]", context + prompt) is None
        assert prompt.endswith("？") and prompt.count("？") == 1
        assert len(labels) == len(set(re.sub(r"\s+", "", label) for label in labels))
        assert all(re.search(r"[\u3400-\u9fff]", label) for label in labels)


def test_frontend_adapter_fixture_is_real_task2_opportunity_output() -> None:
    packet = json.loads(TASK2_PACKET_FIXTURE.read_text(encoding="utf-8"))
    windows = [
        {
            "window_start": "2018-01-01",
            "window_end": "2020-12-31",
            "activations": {"04:00": 1.0, "04:01": 0.0},
        },
        {
            "window_start": "2021-01-01",
            "window_end": "2023-12-31",
            "activations": {"04:00": 0.0, "04:01": 1.0},
        },
    ]

    opportunity = _dimension_opportunity("career", windows, ["04:00", "04:01"])

    fixture = packet["opportunities"][0]
    assert fixture["opportunity_id"] == opportunity["opportunity_id"]
    assert fixture["candidate_partition_fingerprint"] == opportunity[
        "candidate_partition_fingerprint"
    ]
    assert [item["partition_id"] for item in fixture["partitions"]] == [
        item["partition_id"] for item in opportunity["partitions"]
    ]
    assert fixture["dimension_code"] == "career"
    assert "career" not in fixture["neutral_context"]
    assert len(fixture["partitions"]) == len(opportunity["partitions"])
    assert re.search(r"[A-Za-z]", fixture["neutral_context"] + fixture["fallback_prompt"]) is None
    fixture_labels = [item["fallback_label"] for item in fixture["partitions"]]
    assert len(fixture_labels) == len(
        set(re.sub(r"\s+", "", label) for label in fixture_labels)
    )


def test_same_year_windows_receive_distinct_visible_labels() -> None:
    windows = [
        {
            "window_start": "2012-01-01",
            "window_end": "2012-03-31",
            "activations": {"04:00": 1.0, "04:01": 0.0},
        },
        {
            "window_start": "2012-04-01",
            "window_end": "2012-06-30",
            "activations": {"04:00": 0.0, "04:01": 1.0},
        },
    ]

    opportunity = _dimension_opportunity("career", windows, ["04:00", "04:01"])

    assert opportunity is not None
    labels = [item["fallback_label"] for item in opportunity["partitions"]]
    normalized = [
        re.sub(r"\s+", "", unicodedata.normalize("NFKC", label)) for label in labels
    ]
    assert len(normalized) == len(set(normalized))
    assert all(len(re.findall(r"\d+", label)) >= 3 for label in labels)


def test_same_month_windows_receive_distinct_day_precision_labels() -> None:
    windows = [
        {
            "window_start": "2012-01-01",
            "window_end": "2012-01-10",
            "activations": {"04:00": 1.0, "04:01": 0.0},
        },
        {
            "window_start": "2012-01-11",
            "window_end": "2012-01-20",
            "activations": {"04:00": 0.0, "04:01": 1.0},
        },
    ]

    opportunity = _dimension_opportunity("career", windows, ["04:00", "04:01"])

    assert opportunity is not None
    labels = [item["fallback_label"] for item in opportunity["partitions"]]
    normalized = [
        re.sub(r"\s+", "", unicodedata.normalize("NFKC", label)) for label in labels
    ]
    assert len(normalized) == len(set(normalized))
    assert all(len(re.findall(r"\d+", label)) >= 4 for label in labels)
