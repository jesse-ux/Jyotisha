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


def test_profile_migration_workflow_includes_chart_library_and_birth_time_profile_migrations() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "20260718050000_profiles_service_role_upsert_grants.sql" in text
    assert "20260718060000_profiles_service_role_least_privilege.sql" in text
    assert "20260718070000_profiles_service_role_upsert_id.sql" in text
    assert "20260718080000_profiles_service_role_account_upsert_selects.sql" in text
    assert "20260718100000_repair_missing_chart_profiles.sql" in text
    assert "20260718102000_recover_missing_profile_rows.sql" in text
    assert "20260718103000_profile_birth_time_declaration_grants.sql" in text


def test_profile_migration_workflow_does_not_reference_missing_sql_files() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "20260718010000_recover_missing_profile_rows.sql" not in text
    assert "20260718020000_profiles_service_role_upsert_grants.sql" not in text
