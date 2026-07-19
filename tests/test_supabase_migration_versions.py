from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "frontend" / "supabase" / "migrations"


def test_supabase_migration_versions_are_unique() -> None:
    # Given: Supabase records the timestamp prefix as the migration identity.
    versions: defaultdict[str, list[str]] = defaultdict(list)

    # When: every local migration is grouped by that identity.
    for migration in sorted(MIGRATIONS.glob("*.sql")):
        versions[migration.name.split("_", maxsplit=1)[0]].append(migration.name)

    # Then: no migration can be silently skipped behind a duplicate identity.
    duplicates = {
        version: names
        for version, names in versions.items()
        if len(names) > 1
    }
    assert duplicates == {}
