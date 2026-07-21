from pathlib import Path


PAGE = Path("frontend/src/app/page.tsx")
STYLES = Path("frontend/src/app/globals.css")
SESSION_ROW = Path("frontend/src/components/sidebar-session-row.tsx")
SESSION_DELETE_ROUTE = Path("frontend/src/app/api/sessions/[id]/route.ts")
SESSION_DELETE_MIGRATION = Path("frontend/supabase/migrations/20260721100000_chat_sessions_delete_grant.sql")


def test_chat_history_management_actions_are_exposed() -> None:
    source = PAGE.read_text(encoding="utf-8") + STYLES.read_text(encoding="utf-8") + SESSION_ROW.read_text(encoding="utf-8")
    for expected in (
        "renameSession",
        "deleteSession",
        "pendingSessionDeletion",
        "确认删除",
        "session-delete-overlay",
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
        "focus-within",
        "置顶",
        "重命名",
        "归档",
        "恢复",
        "删除",
        "转发",
        'fetch(`/api/sessions/${encodeURIComponent(session.id)}`',
    ):
        assert expected in source


def test_chat_session_delete_is_server_controlled_and_granted() -> None:
    route = SESSION_DELETE_ROUTE.read_text(encoding="utf-8")
    migration = SESSION_DELETE_MIGRATION.read_text(encoding="utf-8")
    assert 'from("chat_sessions")' in route
    assert '.eq("user_id", user.id)' in route
    assert 'count !== 1' in route
    assert 'grant delete on table public.chat_sessions to authenticated' in migration.lower()
    assert 'create policy chat_sessions_delete_own' in migration.lower()
    assert 'using ((select auth.uid()) = user_id)' in migration.lower()
