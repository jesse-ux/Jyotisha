import re
from pathlib import Path


MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "frontend"
    / "supabase"
    / "migrations"
    / "20260715030000_user_profiles_chat_sessions.sql"
)
COORDS_MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "frontend"
    / "supabase"
    / "migrations"
    / "20260715050000_profile_coordinates.sql"
)
CONSULTATION_MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "frontend"
    / "supabase"
    / "migrations"
    / "20260717000000_consultation_request_lifecycle.sql"
)
PAGE = Path(__file__).resolve().parents[1] / "frontend" / "src" / "app" / "page.tsx"


def _sql() -> str:
    return re.sub(r"\s+", " ", MIGRATION.read_text(encoding="utf-8").lower()).strip()


def test_user_profile_and_chat_session_database_contract() -> None:
    sql = _sql()

    for definition in (
        "name text",
        "birth_date date",
        "birth_time time without time zone",
        "country_code text",
        "province_code text",
        "city_code text",
        "district_code text",
    ):
        assert f"add column if not exists {definition}" in sql

    assert "create policy profiles_update_own" in sql
    assert "for update to authenticated using ((select auth.uid()) = id) with check ((select auth.uid()) = id)" in sql
    assert "grant update ( name, birth_date, birth_time, country_code, province_code, city_code, district_code, updated_at ) on table public.profiles to authenticated" in sql

    assert "create table if not exists public.chat_sessions" in sql
    for definition in (
        "id uuid primary key default gen_random_uuid()",
        "user_id uuid not null references auth.users(id) on delete cascade",
        "title text not null default '新对话'",
        "theme text not null default 'general'",
        "messages jsonb not null default '[]'::jsonb",
        "created_at timestamptz not null default now()",
        "updated_at timestamptz not null default now()",
    ):
        assert definition in sql
    assert "check (theme in ('career', 'marriage', 'timing', 'general'))" in sql
    assert "check (jsonb_typeof(messages) = 'array')" in sql
    assert "alter table public.chat_sessions enable row level security" in sql
    assert "create policy chat_sessions_select_own on public.chat_sessions for select to authenticated using ((select auth.uid()) = user_id)" in sql
    assert "create policy chat_sessions_insert_own on public.chat_sessions for insert to authenticated with check ((select auth.uid()) = user_id)" in sql
    assert "create policy chat_sessions_update_own on public.chat_sessions for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id)" in sql
    assert "revoke all on table public.chat_sessions from anon, authenticated, service_role" in sql
    assert "grant select on table public.chat_sessions to authenticated" in sql
    assert "grant insert (id, user_id, title, theme, messages, updated_at) on table public.chat_sessions to authenticated" in sql
    assert "grant update (title, theme, messages, updated_at) on table public.chat_sessions to authenticated" in sql
    assert "grant delete" not in sql


def test_chat_page_uses_authenticated_cloud_persistence() -> None:
    source = PAGE.read_text(encoding="utf-8")

    assert '.from("profiles")' in source
    assert '.from("chat_sessions")' in source
    assert 'user_id: account.user.id' in source
    assert '.upsert(' not in source
    assert '.update(values)' in source
    assert '.insert({' in source
    assert 'await persistSession(userSession)' not in source
    assert source.index('updateSession(sessionId, () => userSession)') < source.index('await persistSession(completedSession)')
    assert 'function completedOnboardingTranscript(profile: Profile, greeting: string): Message[]' in source
    assert 'messages: [...preservedMessages, { role: "user", text: question }]' in source
    assert 'await persistSession(completedSession)' in source
    assert 'const stoppedRequestAwaitingSettlement = useRef<string | null>(null)' in source
    assert 'const stoppedSessionPersistence = useRef(new Map<string, Promise<void>>())' in source
    assert 'if (ownsInterface && !partialReply)' in source
    assert 'await persistSession(interruptedSession)' in source
    assert 'await persistence' in source
    assert 'disabled={Boolean(pendingSessionId) || cancellationPending}' in source
    assert "localStorage" not in source
    assert "ayanam-profile" not in source
    assert "ayanam-sessions" not in source


def test_consultation_credit_lifecycle_is_idempotent_and_server_only() -> None:
    sql = re.sub(r"\s+", " ", CONSULTATION_MIGRATION.read_text(encoding="utf-8").lower()).strip()

    assert "create table if not exists public.consultation_requests" in sql
    assert "primary key (user_id, request_id)" in sql
    assert "status in ('reserved', 'completed', 'cancelled')" in sql
    for function_name in (
        "begin_consultation_credit",
        "complete_consultation_credit",
        "cancel_consultation_credit",
    ):
        assert f"create or replace function public.{function_name}" in sql
        assert f"grant execute on function public.{function_name}(uuid, text) to service_role" in sql
        assert f"revoke all on function public.{function_name}(uuid, text) from public, anon, authenticated" in sql
    assert "pg_advisory_xact_lock" in sql
    assert "if v_status = 'completed'" in sql
    assert "'request_completed'::text" in sql
    assert "if v_status = 'cancelled'" in sql


def test_profile_coordinates_are_persisted_with_database_bounds() -> None:
    sql = re.sub(r"\s+", " ", COORDS_MIGRATION.read_text(encoding="utf-8").lower()).strip()
    source = PAGE.read_text(encoding="utf-8")

    for definition in (
        "latitude double precision",
        "longitude double precision",
        "timezone_offset double precision",
    ):
        assert f"add column if not exists {definition}" in sql

    assert "latitude between -90 and 90" in sql
    assert "longitude between -180 and 180" in sql
    assert "timezone_offset between -12 and 14" in sql
    assert "grant update (latitude, longitude, timezone_offset) on table public.profiles to authenticated" in sql
    assert "latitude: birthPlace?.lat ?? null" in source
    assert "longitude: birthPlace?.lon ?? null" in source
    assert "timezone_offset: birthPlace?.tz ?? null" in source
