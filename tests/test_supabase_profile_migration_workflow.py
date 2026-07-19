from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "apply-supabase-profile-migrations.yml"


def test_profile_migration_workflow_is_manual_and_uses_vps_env_without_printing_secrets() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in text
    assert "PRODUCTION_SSH_PRIVATE_KEY" in text
    assert "SUPABASE_DB_URL" in text
    assert "DATABASE_URL" in text
    assert "docker run --rm -i postgres:16-alpine" in text
    assert "set +x" in text
    assert "cat \"$SQL_FILE\" |" in text


def test_profile_migration_workflow_targets_only_account_profile_migrations() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "20260718010000_recover_missing_profile_rows.sql" in text
    assert "20260718020000_profiles_service_role_upsert_grants.sql" in text
    assert "20260718050000_profiles_service_role_upsert_grants.sql" in text
    assert "20260718070000_profiles_service_role_upsert_id.sql" in text
    assert "20260718080000_profiles_service_role_account_upsert_selects.sql" in text
