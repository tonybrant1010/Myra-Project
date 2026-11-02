import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import Column, MetaData, String, Table, create_engine


spec = importlib.util.spec_from_file_location(
    "migration_source_queries", Path(__file__).parents[1] / "scripts/migrate_sqlite_to_postgres.py")
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)


@pytest.mark.parametrize("name", ["users", "select", 'legacy"; DROP TABLE users; --'])
def test_source_table_identifiers_are_quoted_and_missing_legacy_columns_are_supported(name):
    engine = create_engine("sqlite:///:memory:")
    legacy = Table(name, MetaData(), Column("existing", String))
    current = Table(name, MetaData(), Column("existing", String), Column("new_column", String))
    try:
        legacy.create(engine)
        with engine.begin() as connection:
            connection.execute(legacy.insert().values(existing="árvíztűrő"))
            source = connection.connection.driver_connection
            rows = list(migration.read_source_rows(source, current))
            assert [dict(row) for row in rows] == [{"existing": "árvíztűrő"}]
            assert list(migration.read_source_rows(source, current))
    finally:
        engine.dispose()
