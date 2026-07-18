from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from scripts.dynamic_rectification_opportunities import _dimension_opportunity

TASK2_PACKET_FIXTURE = (
    Path(__file__).parents[1]
    / "frontend/tests/fixtures/task2-dynamic-rectification-packet.json"
)


@pytest.mark.parametrize(
    ("dimension", "domain_terms"),
    [
        ("education", ("升学", "转学", "学习")),
        ("relocation", ("搬家", "离乡", "居住")),
        ("relationship", ("关系",)),
        ("career", ("工作", "职业", "身份")),
        ("health_pressure", ("健康", "压力", "生活")),
    ],
)
def test_every_supported_dimension_emits_localized_validator_safe_copy(
    dimension: str,
    domain_terms: tuple[str, ...],
) -> None:
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

    opportunity = _dimension_opportunity(dimension, windows, ["04:00", "04:01"])

    assert opportunity is not None
    context = opportunity["neutral_context"]
    prompt = opportunity["fallback_prompt"]
    assert any(term in context for term in domain_terms)
    assert dimension not in context
    assert re.search(r"[\u3400-\u9fff]", context)
    assert re.search(r"[A-Za-z]", context) is None
    assert context in prompt
    assert prompt.endswith("？")
    assert re.search(r"[A-Za-z]", prompt) is None
    assert all(label.endswith(" 年") for label in (
        item["fallback_label"] for item in opportunity["partitions"]
    ))
    assert [item["fallback_label"].replace(" 年", "") for item in opportunity["partitions"]] == [
        "2018—2020",
        "2021—2023",
    ]


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
    assert fixture["neutral_context"] == opportunity["neutral_context"]
    assert fixture["fallback_prompt"] == opportunity["fallback_prompt"]
    assert [item["fallback_label"] for item in fixture["partitions"]] == [
        item["fallback_label"] for item in opportunity["partitions"]
    ]


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
    assert len(labels) == len(set(labels))
    assert all("月" in label for label in labels)
