from types import SimpleNamespace

import httpx
import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

import server
from esv import _build_interpretation


def test_concurrent_tts_uses_distinct_temporary_files(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from pathlib import Path

    model = tmp_path / "model.onnx"
    model.write_bytes(b"model")
    monkeypatch.setattr(server, "_ensure_piper_ready", lambda: None)
    monkeypatch.setattr(server, "PIPER_MODEL", model)
    monkeypatch.setattr(server, "PIPER_CACHE_DIR", tmp_path / "cache")
    barrier = Barrier(2)
    outputs = []

    def synthesize(command, **kwargs):
        output = Path(command[command.index("--output_file") + 1])
        outputs.append(output)
        output.write_bytes(b"RIFF" + b"x" * 100)
        barrier.wait(timeout=5)
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(server.subprocess, "run", synthesize)
    with ThreadPoolExecutor(max_workers=2) as pool:
        files = list(pool.map(server._synthesize_piper_wav, ["same text", "same text"]))
    assert len(set(outputs)) == 2
    assert files[0] == files[1] and files[0].read_bytes().startswith(b"RIFF")
    assert not list((tmp_path / "cache").glob("*.tmp.wav"))


def test_long_password_suffix_is_verified_and_legacy_hash_still_works():
    password = "á" * 40 + "first-suffix"
    hashed = server.hash_password(password)
    assert server.verify_password(password, hashed)
    assert not server.verify_password("á" * 40 + "second-suffix", hashed)
    legacy = server.pwd_ctx.hash("legacy-password", scheme="bcrypt")
    assert server.verify_password("legacy-password", legacy)


def test_manual_code_has_no_fabricated_measurement_or_goal():
    norms = {"v": 2, "source": "manual_code"}
    result = _build_interpretation(norms)
    assert result["has_measurement"] is False
    assert all(scale["pomp"] is None and scale["band"] is None for scale in result["scales"])
    assert server._goal_suggestions_for(norms, "session", set()) == []


def test_pdf_does_not_invent_a_trend_from_manual_code():
    import io
    from datetime import datetime, timezone
    from pypdf import PdfReader
    from report_pdf import _build_professional_report_pdf

    now = datetime.now(timezone.utc)
    sessions = [server.QuizSubmission(code="1111", created_at=now,
                                      norms={"a": 0.2, "p": 0.2, "h": 0.2, "c": 0.2}),
                server.QuizSubmission(code="4444", created_at=now,
                                      norms={"v": 2, "source": "manual_code"})]
    result = _build_professional_report_pdf(SimpleNamespace(name="Test", email="test@example.com"), sessions, {})
    text = "\n".join(page.extract_text() for page in PdfReader(io.BytesIO(result)).pages)
    assert "Nincs mérési adat" in text
    assert "Változás az előző méréshez képest" not in text
    assert "POMP None" not in text


@pytest.mark.anyio
async def test_recalled_cache_is_rejected_after_source_deletion_and_optout():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(server.Base.metadata.create_all)
    current = SimpleNamespace(id="active-turn", role="user", text="most", created_at=None)
    try:
        async with sessions() as db:
            db.add(server.User(id=99101, email="cache-test@example.com", name="Test", password_hash="unused"))
            db.add(server.ChatMessage(id="past-turn", user_id=99101, role="user", text="private"))
            await db.commit()
            server._remember_local_turn(current.id, "hidden private recall", 99101, "active", ("past-turn",), True)
            await server._validate_local_history_cache(db, 99101, [current], True)
            assert "private recall" in server._local_message_text(current)
            await db.execute(delete(server.ChatMessage).where(server.ChatMessage.id == "past-turn"))
            await db.commit()
            await server._validate_local_history_cache(db, 99101, [current], True)
            assert server._local_message_text(current) == "most"
            server._remember_local_turn(current.id, "hidden private recall", 99101, "active", (), True)
            await server._validate_local_history_cache(db, 99101, [current], False)
            assert server._local_message_text(current) == "most"
    finally:
        server._clear_local_context_cache(99101)
        await engine.dispose()


@pytest.mark.anyio
async def test_migration_refuses_populated_target_before_startup_mutations(tmp_path, monkeypatch):
    import importlib.util
    from pathlib import Path

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(server.Base.metadata.create_all)
        await conn.execute(server.User.__table__.insert().values(
            id=99102, email="migration-guard@example.com", name="Test", password_hash="unchanged"))
    path = Path(server.__file__).parent / "scripts/migrate_sqlite_to_postgres.py"
    spec = importlib.util.spec_from_file_location("migration_guard_test", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    async def forbidden_startup():
        pytest.fail("Startup migration ran against a populated target")

    target = SimpleNamespace(DB_DIALECT="postgresql", Base=server.Base, engine=engine,
                             select=server.select, func=server.func, sql_text=server.sql_text,
                             _run_startup_migrations=forbidden_startup)
    monkeypatch.setattr(migration, "prepare_server_import", lambda _url: target)
    source = tmp_path / "source.db"
    source.touch()
    try:
        with pytest.raises(ValueError, match="Target contains application data"):
            await migration.migrate(source, "unused")
        async with engine.connect() as conn:
            assert (await conn.execute(server.select(server.User.password_hash))).scalar_one() == "unchanged"
    finally:
        await engine.dispose()


@pytest.mark.anyio
@pytest.mark.parametrize("streaming", [False, True])
async def test_local_chat_preserves_explicit_sampling_and_server_default(monkeypatch, streaming):
    seen = []
    real_client = httpx.AsyncClient

    def handler(request):
        seen.append(server._json.loads(request.content))
        if streaming:
            return httpx.Response(200, content=b'data: {"choices":[{"delta":{"content":"Szia!"}}]}\n\ndata: [DONE]\n\n')
        return httpx.Response(200, json={"choices": [{"message": {"content": "Szia!"}}]})

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(server.httpx, "AsyncClient", lambda **kw: real_client(transport=transport, **kw))

    async def sampling():
        return {"temperature": 0.27, "top_k": 12}

    monkeypatch.setattr(server, "_local_sampling", sampling)
    token = server._chat_stream_sink.set(lambda _text: None) if streaming else server._chat_stream_sink.set(None)
    try:
        await server._local_chat_with_guardrail("model", "unchanged system", [], "user")
        assert seen[-1]["temperature"] == 0.27 and seen[-1]["top_k"] == 12

        async def defaults():
            return {}

        monkeypatch.setattr(server, "_local_sampling", defaults)
        await server._local_chat_with_guardrail("model", "unchanged system", [], "user")
        assert "temperature" not in seen[-1]
    finally:
        server._chat_stream_sink.reset(token)
