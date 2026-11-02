import importlib.util
import json
from pathlib import Path


def test_new_log_at_same_path_is_read_from_start(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("stats_rotation", Path(__file__).parents[1] / "myra-stats.py")
    stats = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stats)
    log = tmp_path / "access.log"
    record = json.dumps({"ts": stats.datetime.now(stats.timezone.utc).timestamp(), "status": 200,
                         "request": {"uri": "/", "remote_ip": "127.0.0.1"}}) + "\n"
    log.write_text(record)
    monkeypatch.setattr(stats, "LOG_DIR", tmp_path)
    state = {"fajlok": {}, "napok": {}, "orak": {}}
    monkeypatch.setattr(stats, "_allapot_betolt", lambda: state)
    first = stats._feldolgoz()
    assert first["feldolgozott_sorok"] == 1
    assert stats._feldolgoz()["feldolgozott_sorok"] == 0
    log.rename(tmp_path / "access-rotated.log")
    log.write_text(record * 2)
    assert stats._feldolgoz()["feldolgozott_sorok"] == 2
