import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "build_release.py"
REQUIRED = ["backend/seed/state_codes.json", "backend/server.py", "backend/game_validation.py",
            "backend/notification_outbox.py", "ops/verify-isolated.sh", "ops/publish_frontend.py"]


@pytest.mark.skipif(shutil.which("git") is None, reason="git required")
def test_release_skips_files_deleted_from_working_tree(tmp_path):
    for rel in REQUIRED + ["backend/scripts/old.py"]:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x\n")
    (tmp_path / "ops" / "build_release.py").write_text(SCRIPT.read_text())
    git = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
    subprocess.run(git + ["init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(git + ["add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(git + ["commit", "-qm", "x"], cwd=tmp_path, check=True)
    (tmp_path / "backend/scripts/old.py").unlink()
    out = tmp_path / "out" / "c.tgz"
    subprocess.run([sys.executable, str(tmp_path / "ops" / "build_release.py"), "--output", str(out)],
                   cwd=tmp_path, check=True, capture_output=True)
    assert out.exists()
