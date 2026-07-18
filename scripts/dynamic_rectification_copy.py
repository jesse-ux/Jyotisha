"""Localized public copy for dynamic birth-time rectification choices."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Final, Literal, TypedDict, assert_never

DIMENSION_CONTEXT: Final = {
    "education": "一次明显的升学、转学或学习方向变化",
    "relocation": "一次明显的搬家、离乡或长期居住地变化",
    "relationship": "一次明显的关系进入、结束或重要转变",
    "career": "一次明显的工作、职业方向或身份变化",
    "health_pressure": "一次持续的健康压力或生活压力变化",
}
SUPPORTED_DIMENSIONS: Final = frozenset(DIMENSION_CONTEXT)


class DateRange(TypedDict):
    window_start: str
    window_end: str


RangePrecision = Literal["year", "month", "day"]


def _range_label(item: DateRange, precision: RangePrecision) -> str:
    start = date.fromisoformat(item["window_start"])
    end = date.fromisoformat(item["window_end"])
    match precision:
        case "year":
            return f"{start.year} 年" if start.year == end.year else f"{start.year}—{end.year} 年"
        case "month":
            if start.year == end.year:
                return f"{start.year} 年 {start.month} 月—{end.month} 月"
            return f"{start.year} 年 {start.month} 月—{end.year} 年 {end.month} 月"
        case "day":
            if start.year == end.year and start.month == end.month:
                return f"{start.year} 年 {start.month} 月 {start.day} 日—{end.day} 日"
            return (
                f"{start.year} 年 {start.month} 月 {start.day} 日—"
                f"{end.year} 年 {end.month} 月 {end.day} 日"
            )
        case unreachable:
            assert_never(unreachable)


def visible_range_labels(items: Sequence[DateRange]) -> list[str]:
    """Use the least date precision that keeps every visible range distinct."""
    labels = [_range_label(item, "year") for item in items]
    for precision in ("month", "day"):
        duplicates = {label for label in labels if labels.count(label) > 1}
        if not duplicates:
            break
        labels = [
            _range_label(item, precision) if label in duplicates else label
            for item, label in zip(items, labels, strict=True)
        ]
    return labels
