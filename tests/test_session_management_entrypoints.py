from pathlib import Path


PAGE = Path("frontend/src/app/page.tsx")


def test_chat_history_management_actions_are_exposed() -> None:
    source = PAGE.read_text(encoding="utf-8")
    for expected in (
        "renameSession",
        "deleteSession",
        "togglePinnedSession",
        "toggleArchivedSession",
        "showArchivedSessions",
        "shareSession",
        "share_payload_version",
        "messages.map",
        "onContextMenu",
        "session-menu-trigger",
        'role="menu"',
        "closeSessionMenu",
        "Escape",
        "置顶",
        "重命名",
        "归档",
        "恢复",
        "删除",
        "转发",
    ):
        assert expected in source
