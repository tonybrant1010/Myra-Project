import asyncio
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from sqlalchemy import JSON, Boolean, DateTime, Integer, create_engine, select
from sqlalchemy.ext.asyncio import create_async_engine

import server


def normalize(value):
    if isinstance(value, datetime):
        return (value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value).isoformat()
    return value


def fixture(path):
    engine = create_engine("sqlite:///" + str(path))
    server.Base.metadata.create_all(engine)
    samples = {}
    with engine.begin() as conn:
        for table in server.Base.metadata.sorted_tables:
            values = {}
            for column in table.columns:
                if column.foreign_keys:
                    reference = next(iter(column.foreign_keys)).column
                    value = samples[reference.table.name][reference.name]
                elif isinstance(column.type, Boolean):
                    value = True
                elif isinstance(column.type, Integer):
                    value = 1 if column.primary_key else 7
                elif isinstance(column.type, DateTime):
                    value = datetime(2026, 10, 1, 12, 30, tzinfo=timezone.utc)
                elif isinstance(column.type, JSON):
                    value = {"sample": [1, "árvíztűrő", True]}
                elif isinstance(column.type, server.pgvector_type):
                    value = [0.01] * column.type.dim
                else:
                    value = "1111" if getattr(column.type, "length", None) == 4 else "migrate-" + column.name
                    value = value[:getattr(column.type, "length", None)]
                if table.name == "users" and column.name == "totp_secret":
                    value = server._encrypt_field("JBSWY3DPEHPK3PXP", purpose="totp")
                if table.name == "crisis_notification_outbox" and column.name == "payload":
                    value = server._encrypt_field('["synthetic-notification"]', purpose="notification")
                values[column.name] = value
            conn.execute(table.insert().values(**values))
            samples[table.name] = dict(conn.execute(select(table)).mappings().one())
    engine.dispose()
    return samples


async def verify():
    if os.environ.get("MYRA_ISOLATED_TEST") != "1" or not server.DATABASE_URL.endswith("/myra_repair_test"):
        raise RuntimeError("Migration check is restricted to the disposable test database")
    target = server.DATABASE_URL.rsplit("/", 1)[0] + "/myra_migration_test"
    async with server.engine.connect() as conn:
        conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
        await conn.execute(server.sql_text("CREATE DATABASE myra_migration_test"))
    with tempfile.TemporaryDirectory(prefix="myra-migration-fixture-") as temporary:
        source = Path(temporary) / "source.sqlite"
        expected = await asyncio.to_thread(fixture, source)
        command = [sys.executable, str(Path(__file__).parents[1] / "scripts/migrate_sqlite_to_postgres.py"),
                   "--source", str(source), "--target-url", target]
        process = await asyncio.to_thread(subprocess.run, command, capture_output=True, text=True, timeout=120)
        if process.returncode:
            raise RuntimeError(process.stdout + process.stderr)
        target_engine = create_async_engine(target, connect_args={"ssl": False})
        try:
            async with target_engine.connect() as conn:
                for table in server.Base.metadata.sorted_tables:
                    actual = dict((await conn.execute(select(table))).mappings().one())
                    for name, value in expected[table.name].items():
                        if isinstance(table.c[name].type, server.pgvector_type):
                            assert len(value) == len(actual[name])
                            assert all(abs(a - b) < 1e-6 for a, b in zip(value, actual[name]))
                        else:
                            assert normalize(value) == normalize(actual[name]), f"Lost field: {table.name}.{name}"
                    for column in table.primary_key:
                        if len(table.primary_key) == 1 and isinstance(column.type, Integer):
                            next_id = (await conn.execute(server.sql_text(
                                "SELECT nextval(pg_get_serial_sequence(:table_name, :column_name))"),
                                {"table_name": table.name, "column_name": column.name})).scalar_one()
                            assert next_id > actual[column.name], f"Sequence not restored: {table.name}"
            second = await asyncio.to_thread(subprocess.run, command, capture_output=True, text=True, timeout=120)
            assert second.returncode != 0 and "Target contains application data" in second.stderr
        finally:
            await target_engine.dispose()
    print("SQLITE_POSTGRES_ALL_COLUMNS_OK")
