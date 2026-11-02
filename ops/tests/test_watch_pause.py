import importlib.util
import sys
from pathlib import Path

import pytest


@pytest.fixture
def watch(tmp_path, monkeypatch):
    monkeypatch.setenv("MYRA_DB_MOD", "supabase")
    monkeypatch.setenv("MYRA_DIR", str(tmp_path))
    monkeypatch.setenv("MYRA_OPS_DIR", str(tmp_path / "ops"))
    path = Path(__file__).resolve().parents[1] / "myra-watch.py"
    spec = importlib.util.spec_from_file_location("myra_watch_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module.time, "sleep", lambda _s: None)
    yield module
    sys.modules.pop("myra_watch_under_test", None)


def test_database_ssl_false_is_respected(watch, monkeypatch):
    monkeypatch.setattr(watch, "ENV", {"DATABASE_URL": "postgresql://myra:example@localhost/myra",
                                      "DATABASE_SSL": "false", "DATABASE_SSL_MODE": "verify-full"})
    connection, _env = watch._supabase_kapcsolat()
    assert "sslmode=disable" in connection


def test_pause_event_is_logged_while_pause_is_active(watch, monkeypatch):
    seen = []
    monkeypatch.setattr(watch, "_esemeny", lambda *a, **k: seen.append(watch.szunet_aktiv_e()))

    watch.szunet_allit(30)
    assert watch.szunet_aktiv_e()
    watch.szunet_allit(0)

    assert not watch.szunet_aktiv_e()
    assert seen == [True, True]


def test_deploy_smoke_exec_matches_watch_exception(watch):
    deploy_src = (Path(__file__).resolve().parents[1] / "myra-deploy.py").read_text(encoding="utf-8")
    assert '"python", "-c", script' in deploy_src
    assert any(p.search("python -c import urllib.request.urlopen") for p in watch.EXEC_KIVETELEK)


def test_backend_stop_request_is_consumed_and_stops_only_backend(watch, tmp_path, monkeypatch):
    control = tmp_path / "control"
    control.mkdir()
    monkeypatch.setattr(watch, "LEALLITAS_FAJL", str(control / "stop-backend"))
    calls = []
    monkeypatch.setattr(watch.subprocess, "run", lambda cmd, **k: calls.append(cmd) or type("R", (), {"stderr": "", "stdout": ""})())
    monkeypatch.setattr(watch, "_esemeny", lambda *a, **k: None)

    assert watch.vezerles_feldolgoz() is False
    (control / "stop-backend").write_text("x")
    assert watch.vezerles_feldolgoz() is True
    assert calls == [["docker", "stop", watch.BACKEND_KONTENER]]
    assert not (control / "stop-backend").exists()


def test_integrity_baseline_covers_every_backend_module(tmp_path, monkeypatch):
    backend = tmp_path / "backend"
    backend.mkdir()
    for name in ("server.py", "models.py", "migrations.py"):
        (backend / name).write_text("x")
    monkeypatch.setenv("MYRA_DIR", str(tmp_path))
    monkeypatch.setenv("MYRA_OPS_DIR", str(tmp_path / "ops"))
    path = Path(__file__).resolve().parents[1] / "myra-watch.py"
    spec = importlib.util.spec_from_file_location("myra_watch_modules", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    protected = set(module.VEDETT_FAJLOK)
    for name in ("server.py", "models.py", "migrations.py"):
        assert str(backend / name) in protected
