import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location("backend_deploy", Path(__file__).parents[1] / "myra-deploy.py")
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


@pytest.mark.parametrize("outcomes", [[1], [0, 1]])
def test_rollback_command_failure_is_not_reported_as_success(monkeypatch, outcomes):
    commands = iter(outcomes)
    monkeypatch.setattr(deploy, "fut", lambda *a, **k: SimpleNamespace(returncode=next(commands)))
    with pytest.raises(RuntimeError, match="failed"):
        deploy.visszaallas()


def test_rollback_verifies_health_and_api(monkeypatch):
    monkeypatch.setattr(deploy, "fut", lambda *a, **k: SimpleNamespace(returncode=0))
    monkeypatch.setattr(deploy, "varj_healthre", lambda: True)
    monkeypatch.setattr(deploy, "fustteszt", lambda: (False, "failed"))
    with pytest.raises(RuntimeError, match="API verification failed"):
        deploy.visszaallas()


def test_missing_rollback_snapshot_stops_before_build(monkeypatch):
    commands = []
    monkeypatch.setattr(deploy, "kimenet", lambda *a: "existing-image")
    def fail_snapshot(command):
        commands.append(command)
        return SimpleNamespace(returncode=1)
    monkeypatch.setattr(deploy, "fut", fail_snapshot)
    assert deploy.main() == 1
    assert len(commands) == 1 and commands[0][:2] == ["docker", "tag"]
