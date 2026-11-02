from sqlalchemy import Integer, inspect as sa_inspect, text as sql_text

from models import EMBED_COL, EMBED_DIM, Base


async def ensure_leaderboard_unique(engine) -> None:
    async with engine.begin() as conn:
        columns = await conn.run_sync(lambda sync: {c["name"] for c in sa_inspect(sync).get_columns("leaderboard")})
        if "verified_at" not in columns:
            await conn.execute(sql_text("ALTER TABLE leaderboard ADD COLUMN verified_at TIMESTAMP"))
        await conn.execute(sql_text("""
            DELETE FROM leaderboard WHERE id IN (
                SELECT id FROM (
                    SELECT id, ROW_NUMBER() OVER (
                        PARTITION BY user_id, game_type ORDER BY score DESC, id ASC
                    ) AS duplicate_rank FROM leaderboard
                ) ranked WHERE duplicate_rank > 1
            )
        """))
        await conn.execute(sql_text(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_leaderboard_user_game ON leaderboard (user_id, game_type)"
        ))


async def run_startup_migrations(engine, dialect: str, database_url: str, ensure_knowledge_fts) -> None:
    await ensure_leaderboard_unique(engine)
    if dialect == "sqlite":
        import sqlite3 as _sqlite3
        _db_path = str(database_url).replace("sqlite+aiosqlite:///", "")
        try:
            _conn = _sqlite3.connect(_db_path)
            _cols = {row[1] for row in _conn.execute("PRAGMA table_info(users)")}
            if "is_suspended" not in _cols:
                _conn.execute("ALTER TABLE users ADD COLUMN is_suspended BOOLEAN NOT NULL DEFAULT 0")
                print("[startup] migráció: users.is_suspended hozzáadva")
            if "mfa_enabled" not in _cols:
                _conn.execute("ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN NOT NULL DEFAULT 0")
                print("[startup] migráció: users.mfa_enabled hozzáadva")
            if "token_version" not in _cols:
                _conn.execute("ALTER TABLE users ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0")
                print("[startup] migráció: users.token_version hozzáadva")
            if "nickname" not in _cols:
                _conn.execute("ALTER TABLE users ADD COLUMN nickname VARCHAR(50)")
                print("[startup] migráció: users.nickname hozzáadva")
            if "last_login_ip" not in _cols:
                _conn.execute("ALTER TABLE users ADD COLUMN last_login_ip VARCHAR(80)")
                print("[startup] migráció: users.last_login_ip hozzáadva")
            if "last_login_at" not in _cols:
                _conn.execute("ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP WITH TIME ZONE")
                print("[startup] migráció: users.last_login_at hozzáadva")
            if "totp_secret" not in _cols:
                _conn.execute("ALTER TABLE users ADD COLUMN totp_secret TEXT")
                print("[startup] migráció: users.totp_secret hozzáadva")
            if "totp_enabled" not in _cols:
                _conn.execute("ALTER TABLE users ADD COLUMN totp_enabled BOOLEAN NOT NULL DEFAULT 0")
                print("[startup] migráció: users.totp_enabled hozzáadva")
            if "consent_given" not in _cols:
                _conn.execute("ALTER TABLE users ADD COLUMN consent_given BOOLEAN NOT NULL DEFAULT 0")
                print("[startup] migráció: users.consent_given hozzáadva")
            if "consent_updated_at" not in _cols:
                _conn.execute("ALTER TABLE users ADD COLUMN consent_updated_at TIMESTAMP")
                print("[startup] migráció: users.consent_updated_at hozzáadva")
            if "terms_version" not in _cols:
                _conn.execute("ALTER TABLE users ADD COLUMN terms_version VARCHAR(50)")
                print("[startup] migráció: users.terms_version hozzáadva")
            if "privacy_version" not in _cols:
                _conn.execute("ALTER TABLE users ADD COLUMN privacy_version VARCHAR(50)")
                print("[startup] migráció: users.privacy_version hozzáadva")
            if "terms_accepted_at" not in _cols:
                _conn.execute("ALTER TABLE users ADD COLUMN terms_accepted_at TIMESTAMP")
                print("[startup] migráció: users.terms_accepted_at hozzáadva")
            if "forum_nickname" not in _cols:
                _conn.execute("ALTER TABLE users ADD COLUMN forum_nickname VARCHAR(50)")
                print("[startup] migráció: users.forum_nickname hozzáadva")
            if "forum_avatar" not in _cols:
                _conn.execute("ALTER TABLE users ADD COLUMN forum_avatar VARCHAR(10)")
                print("[startup] migráció: users.forum_avatar hozzáadva")
            if "profile_memory_enabled" not in _cols:
                _conn.execute("ALTER TABLE users ADD COLUMN profile_memory_enabled BOOLEAN NOT NULL DEFAULT 0")
                print("[startup] migráció: users.profile_memory_enabled hozzáadva")
            if "email_verified" not in _cols:
                _conn.execute("ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT 1")
                print("[startup] migráció: users.email_verified hozzáadva")
            _cols2 = {row[1] for row in _conn.execute("PRAGMA table_info(chat_messages)")}
            if "session_id" not in _cols2:
                _conn.execute("ALTER TABLE chat_messages ADD COLUMN session_id VARCHAR(40)")
                print("[startup] migráció: chat_messages.session_id hozzáadva")
            ensure_knowledge_fts(_conn)
            _conn.commit()
            _conn.close()
        except Exception as _e:
            print(f"[startup] migráció figyelmeztetés: {_e}")
        return

    async with engine.begin() as conn:
        try:
            async with conn.begin_nested():
                await conn.execute(sql_text("CREATE EXTENSION IF NOT EXISTS vector"))
        except Exception as _e:
            print(f"[startup] postgresql vector extension warning: {_e}")
        try:
            async with conn.begin_nested():
                await conn.execute(sql_text(f"ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS {EMBED_COL} vector({EMBED_DIM})"))
        except Exception as _e:
            print(f"[startup] postgresql ADD COLUMN {EMBED_COL} warning: {_e}")
        try:
            async with conn.begin_nested():
                await conn.execute(sql_text(f"CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_{EMBED_COL} ON knowledge_chunks USING hnsw ({EMBED_COL} vector_cosine_ops)"))
        except Exception as _e:
            print(f"[startup] postgresql {EMBED_COL} index warning: {_e}")
        try:
            async with conn.begin_nested():
                await conn.execute(sql_text(
                    "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_hu_tsv ON knowledge_chunks "
                    "USING gin (to_tsvector('hungarian', coalesce(title, '') || ' ' || content))"
                ))
        except Exception as _e:
            print(f"[startup] postgresql hungarian tsvector index warning: {_e}")
        await conn.execute(sql_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_suspended BOOLEAN NOT NULL DEFAULT false"))
        await conn.execute(sql_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_enabled BOOLEAN NOT NULL DEFAULT false"))
        await conn.execute(sql_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0"))
        await conn.execute(sql_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS nickname VARCHAR(50)"))
        await conn.execute(sql_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token VARCHAR(80)"))
        await conn.execute(sql_text("ALTER TABLE users ALTER COLUMN reset_token TYPE VARCHAR(80)"))
        await conn.execute(sql_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_attempts INTEGER NOT NULL DEFAULT 0"))
        await conn.execute(sql_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS token_expires_at TIMESTAMP WITH TIME ZONE"))
        await conn.execute(sql_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_ip VARCHAR(80)"))
        await conn.execute(sql_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE"))
        await conn.execute(sql_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_secret TEXT"))
        await conn.execute(sql_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS totp_enabled BOOLEAN NOT NULL DEFAULT false"))
        await conn.execute(sql_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_given BOOLEAN NOT NULL DEFAULT false"))
        await conn.execute(sql_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS consent_updated_at TIMESTAMP WITH TIME ZONE"))
        await conn.execute(sql_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS terms_version VARCHAR(50)"))
        await conn.execute(sql_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS privacy_version VARCHAR(50)"))
        await conn.execute(sql_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS terms_accepted_at TIMESTAMP"))
        await conn.execute(sql_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS forum_nickname VARCHAR(50)"))
        await conn.execute(sql_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS forum_avatar VARCHAR(10)"))
        await conn.execute(sql_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_memory_enabled BOOLEAN NOT NULL DEFAULT false"))
        await conn.execute(sql_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT true"))
        try:
            async with conn.begin_nested():
                await conn.execute(sql_text(
                    "CREATE INDEX IF NOT EXISTS ix_chat_messages_hu_tsv ON chat_messages "
                    "USING gin (to_tsvector('hungarian', text))"
                ))
        except Exception as _e:
            print(f"[startup] chat_messages tsvector index warning: {_e}")
        await conn.execute(sql_text("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS session_id VARCHAR(40)"))
        await conn.execute(sql_text("CREATE INDEX IF NOT EXISTS ix_mfa_challenges_user_id ON mfa_challenges (user_id)"))
        await conn.execute(sql_text("CREATE INDEX IF NOT EXISTS ix_trusted_devices_user_id ON trusted_devices (user_id)"))
        await conn.execute(sql_text("CREATE INDEX IF NOT EXISTS ix_admin_audit_logs_admin_user_id ON admin_audit_logs (admin_user_id)"))
        await conn.execute(sql_text("CREATE INDEX IF NOT EXISTS ix_chat_messages_session_id ON chat_messages (session_id)"))
        await conn.execute(sql_text(
            "CREATE INDEX IF NOT EXISTS ix_chat_messages_user_session_created_at "
            "ON chat_messages (user_id, session_id, created_at DESC)"
        ))
        await conn.execute(sql_text("CREATE INDEX IF NOT EXISTS ix_chat_messages_state_code ON chat_messages (state_code)"))
        await conn.execute(sql_text("CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_source_name ON knowledge_chunks (source_name)"))
        await conn.execute(sql_text("CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_source_hash ON knowledge_chunks (source_hash)"))
        await conn.execute(sql_text("CREATE INDEX IF NOT EXISTS ix_security_events_created_at ON security_events (created_at DESC)"))
        try:
            async with conn.begin_nested():
                async with conn.begin_nested():
                    await conn.execute(sql_text(
                        "CREATE TABLE IF NOT EXISTS chat_message_embeddings ("
                        " message_id VARCHAR(40) PRIMARY KEY REFERENCES chat_messages(id) ON DELETE CASCADE,"
                        " user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,"
                        " created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now())"
                    ))
                    await conn.execute(sql_text(
                        f"ALTER TABLE chat_message_embeddings ADD COLUMN IF NOT EXISTS {EMBED_COL} vector({EMBED_DIM})"
                    ))
                    await conn.execute(sql_text(
                        "CREATE INDEX IF NOT EXISTS ix_chat_message_embeddings_user_id ON chat_message_embeddings (user_id)"
                    ))
                    await conn.execute(sql_text("ALTER TABLE chat_message_embeddings ENABLE ROW LEVEL SECURITY"))
        except Exception as _e:
            print(f"[startup] chat_message_embeddings warning: {_e}")
        await ensure_user_fk_cascade(conn, dialect)
        await reset_postgres_sequences(conn, dialect)


USER_FK_CASCADES = [
    ("chat_messages", "user_id", "users", "CASCADE"),
    ("forum_posts", "user_id", "users", "CASCADE"),
    ("quiz_submissions", "user_id", "users", "CASCADE"),
]


async def ensure_user_fk_cascade(conn, dialect: str) -> None:
    if dialect != "postgresql":
        return
    for table_name, column_name, ref_table, action in USER_FK_CASCADES:
        try:
            res = await conn.execute(sql_text("""
                SELECT con.conname, con.confdeltype
                FROM pg_constraint con
                JOIN pg_class rel ON rel.oid = con.conrelid
                JOIN pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = con.conkey[1]
                JOIN pg_class fref ON fref.oid = con.confrelid
                WHERE con.contype = 'f'
                  AND rel.relname = :table_name
                  AND att.attname = :column_name
                  AND fref.relname = :ref_table
                  AND array_length(con.conkey, 1) = 1
            """), {"table_name": table_name, "column_name": column_name, "ref_table": ref_table})
            row = res.first()
            if row is None:
                continue
            conname, confdeltype = row[0], row[1]
            if isinstance(confdeltype, (bytes, bytearray)):
                confdeltype = confdeltype.decode()
            if confdeltype == "c":
                continue
            await conn.execute(sql_text(
                f'ALTER TABLE {table_name} DROP CONSTRAINT "{conname}"'  # nosec B608
            ))
            await conn.execute(sql_text(
                f"ALTER TABLE {table_name} "  # nosec B608
                f"ADD CONSTRAINT {table_name}_{column_name}_fkey "
                f"FOREIGN KEY ({column_name}) REFERENCES {ref_table}(id) ON DELETE {action}"
            ))
            print(f"[startup] migráció: {table_name}.{column_name} FK -> ON DELETE {action}")
        except Exception as _e:
            print(f"[startup] {table_name} FK cascade migráció figyelmeztetés: {_e}")


async def reset_postgres_sequences(conn, dialect: str) -> None:
    if dialect != "postgresql":
        return
    quote = conn.dialect.identifier_preparer.quote
    for table in Base.metadata.sorted_tables:
        for column in table.primary_key:
            if len(table.primary_key) != 1 or not isinstance(column.type, Integer):
                continue
            table_name, column_name = quote(table.name), quote(column.name)
            await conn.execute(sql_text(f"""
                SELECT setval(
                    pg_get_serial_sequence(:table_name, :column_name),
                    COALESCE((SELECT MAX({column_name}) FROM {table_name}), 1),
                    (SELECT COUNT(*) > 0 FROM {table_name})
                )
            """), {"table_name": table.name, "column_name": column.name})  # nosec B608
