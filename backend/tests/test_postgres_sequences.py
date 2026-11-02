from sqlalchemy.dialects.postgresql import dialect
import pytest

import server


@pytest.mark.anyio
async def test_sequence_reset_includes_tables_added_after_initial_schema(monkeypatch):
    calls = []
    class Connection:
        dialect = dialect()

        async def execute(self, statement, parameters):
            calls.append(parameters["table_name"])
    monkeypatch.setattr(server, "DB_DIALECT", "postgresql")
    await server._reset_postgres_sequences(Connection())
    assert {"users", "knowledge_chunks", "user_profiles", "user_goals", "trusted_devices",
            "leaderboard", "security_events", "admin_audit_logs"}.issubset(calls)
    assert "chat_messages" not in calls
    assert "mfa_challenges" not in calls
    assert "game_sessions" not in calls
