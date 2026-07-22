from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
BUG_HISTORY = ROOT / "docs" / "BUG_HISTORY.md"


def test_bug_history_exists_with_required_entry_contract() -> None:
    text = BUG_HISTORY.read_text(encoding="utf-8")

    assert "## 使用流程" in text
    assert "## 新记录模板" in text
    for field in ("用户现象", "触发条件", "根因", "修复", "验证", "防复发", "复发自"):
        assert field in text


def test_agents_requires_read_before_and_update_after_bug_work() -> None:
    text = AGENTS.read_text(encoding="utf-8")

    assert "docs/BUG_HISTORY.md" in text
    assert "开始诊断前必须完整读取并搜索" in text
    assert "必须在同一变更中更新" in text
    assert "严禁写入" in text
