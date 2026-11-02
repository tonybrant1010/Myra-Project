import shutil
import subprocess
import tarfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "myra-backup.sh"
BASH = shutil.which("bash")


def shell_path(path):
    value = path.as_posix()
    return "/" + path.drive[0].lower() + value[len(path.drive):] if path.drive else value


def run_archive(tmp_path, commands):
    text = SCRIPT.read_text()
    helpers = text[text.index("archive_ready() {"):text.index("dump() {")]
    prelude = f'set -euo pipefail\nexport PATH=/usr/bin:$PATH\nPARTIAL=""\nLOCAL="{shell_path(tmp_path)}"\n'
    prelude += 'trap \'[ -z "$PARTIAL" ] || rm -f -- "$PARTIAL"\' EXIT\n'
    return subprocess.run([BASH, "-c", prelude + helpers + commands], capture_output=True, text=True)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash required")
def test_daily_archive_contains_all_backend_modules(tmp_path):
    src = tmp_path / "src"
    for rel in ("backend/server.py", "backend/models.py", "backend/seed/state_codes.json",
                "backend/data/kb_pdfs/a.pdf", "backend/data/model.bin", "ops/myra-watch.py",
                ".env", "docker-compose.yml", "docker-compose.override.yml"):
        p = src / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x")
    text = SCRIPT.read_text()
    start = text.index('  FILELIST=$(mktemp "$LOCAL/.backup-files.')
    end = text.index('\nfi\nif ! archive_ready "$LOCAL/napi/db-', start)
    snippet = text[start:end].rstrip() + "\n"
    out = tmp_path / "napi"
    out.mkdir()
    result = run_archive(tmp_path, f'SRC="{shell_path(src)}"\nTODAY=t\n' + snippet)
    assert result.returncode == 0, result.stderr
    with tarfile.open(out / "myra-t.tar.gz") as archive:
        names = set(archive.getnames())
    assert {"backend/server.py", "backend/models.py", "backend/seed/state_codes.json",
            "backend/data/kb_pdfs/a.pdf", "ops/myra-watch.py", ".env"} <= names
    assert "backend/data/model.bin" not in names


@pytest.mark.skipif(BASH is None, reason="bash required")
def test_failed_tar_never_publishes_or_leaves_partial(tmp_path):
    result = run_archive(tmp_path, 'archive_tar "$LOCAL/failed.tar.gz" -C "$LOCAL" missing-file\n')
    assert result.returncode != 0
    assert not (tmp_path / "failed.tar.gz").exists()
    assert not (tmp_path / "failed.tar.gz.partial").exists()


@pytest.mark.skipif(BASH is None, reason="bash required")
def test_corrupt_daily_archive_is_not_considered_ready(tmp_path):
    (tmp_path / "bad.tar.gz").write_bytes(b"incomplete archive")
    result = run_archive(tmp_path, 'archive_ready "$LOCAL/bad.tar.gz"\n')
    assert result.returncode != 0
