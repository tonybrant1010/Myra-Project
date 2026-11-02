import argparse
import asyncio
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import JSON, Boolean, DateTime, literal_column, select
from sqlalchemy.dialects import sqlite


def parse_dt(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
    except ValueError:
        try:
            dt = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def parse_json(value):
    if isinstance(value, (list, dict)):
        return value
    if value in (None, ""):
        return None
    return json.loads(value)


def bool_value(value):
    return bool(int(value or 0))


def read_source_rows(source, table):
    # Compile identifiers with SQLite's dialect; '*' also supports older schemas
    # that do not yet contain every column in the current application metadata.
    statement = select(literal_column("*")).select_from(table)
    source.row_factory = sqlite3.Row
    return source.execute(str(statement.compile(dialect=sqlite.dialect())))


def prepare_server_import(target_url):
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    if not os.environ.get("JWT_SECRET"):
        raise RuntimeError("Set the original JWT_SECRET before migrating encrypted account data")
    os.environ["DATABASE_URL"] = target_url
    backend_dir = Path(__file__).resolve().parents[1]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    import server
    return server


async def migrate(source_sqlite, target_url, wipe_target=False):
    server = prepare_server_import(target_url)
    if server.DB_DIALECT != "postgresql":
        raise ValueError("The target must be PostgreSQL")
    source = sqlite3.connect(Path(source_sqlite).resolve().as_uri() + "?mode=ro", uri=True)
    available = {r[0] for r in source.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    tables = list(server.Base.metadata.sorted_tables)
    async with server.engine.begin() as conn:
        if not wipe_target:
            from sqlalchemy import inspect
            existing = await conn.run_sync(lambda sync: set(inspect(sync).get_table_names()))
            for table in tables:
                if table.name in existing:
                    count = (await conn.execute(server.select(server.func.count()).select_from(table))).scalar_one()
                    if count:
                        raise ValueError("Target contains application data. Use an empty database or explicitly request --wipe-target after a verified backup.")
        if server.DB_DIALECT == "postgresql":
            await conn.execute(server.sql_text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(server.Base.metadata.create_all)
    await server._run_startup_migrations()
    async with server.SessionLocal() as db:
        if not wipe_target:
            for table in tables:
                if (await db.execute(server.select(server.func.count()).select_from(table))).scalar_one():
                    raise ValueError("Target contains application data. Use an empty database or explicitly request --wipe-target after a verified backup.")
        if wipe_target:
            for table in reversed(tables):
                await db.execute(table.delete())
        for table in tables:
            if table.name not in available:
                continue
            for raw in read_source_rows(source, table):
                row = dict(raw)
                if table.name == "users" and row.get("totp_secret"):
                    server._decrypt_field(row["totp_secret"], purpose="totp")
                if table.name == "crisis_notification_outbox":
                    server._decrypt_field(row["payload"], purpose="notification")
                values = {}
                for col in table.columns:
                    if col.name not in row:
                        continue
                    value = row[col.name]
                    if isinstance(col.type, DateTime):
                        value = parse_dt(value)
                    elif isinstance(col.type, Boolean):
                        value = bool_value(value)
                    elif isinstance(col.type, JSON):
                        value = parse_json(value)
                    values[col.name] = value
                from sqlalchemy.dialects.postgresql import insert
                stmt = insert(table).values(**values)
                keys = ["user_id", "game_type"] if table.name == "leaderboard" else [col.name for col in table.primary_key]
                changes = {k: stmt.excluded[k] for k in values if k not in keys}
                if table.name == "leaderboard":
                    changes.pop("id", None)
                    changes["score"] = server.func.greatest(table.c.score, stmt.excluded.score)
                stmt = stmt.on_conflict_do_update(index_elements=keys, set_=changes) if changes else stmt.on_conflict_do_nothing(index_elements=keys)
                await db.execute(stmt)
        await db.commit()

    source.close()

    if server.DB_DIALECT == "postgresql":
        async with server.engine.begin() as conn:
            await server._reset_postgres_sequences(conn)

    async with server.SessionLocal() as db:
        counts = {}
        for name, model in [
            ("users", server.User),
            ("state_codes", server.StateCode),
            ("quiz_submissions", server.QuizSubmission),
            ("chat_messages", server.ChatMessage),
            ("app_settings", server.AppSetting),
            ("knowledge_chunks", server.KnowledgeChunk),
        ]:
            result = await db.execute(server.select(server.func.count()).select_from(model))
            counts[name] = result.scalar_one()
    await server.engine.dispose()
    return counts


def main():
    parser = argparse.ArgumentParser(description="Copy Myra SQLite data into a Postgres/Supabase database.")
    parser.add_argument("--source", default=str(Path(__file__).resolve().parents[1] / "data" / "myra.db"))
    parser.add_argument("--target-url", default=os.environ.get("SUPABASE_DATABASE_URL") or os.environ.get("DATABASE_URL"))
    parser.add_argument("--wipe-target", action="store_true", help="Delete target Myra tables before import.")
    args = parser.parse_args()

    if not args.target_url:
        raise SystemExit("Missing --target-url or SUPABASE_DATABASE_URL.")
    if not Path(args.source).exists():
        raise SystemExit(f"SQLite source not found: {args.source}")

    counts = asyncio.run(migrate(args.source, args.target_url, wipe_target=args.wipe_target))
    print(json.dumps({"ok": True, "counts": counts}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
