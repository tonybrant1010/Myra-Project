import importlib.util
import io
from pathlib import Path
import tarfile

import pytest

spec = importlib.util.spec_from_file_location("publish_frontend", Path(__file__).parents[1] / "publish_frontend.py")
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


def archive(path, name, kind=tarfile.REGTYPE):
    with tarfile.open(path, "w:gz") as bundle:
        member = tarfile.TarInfo(name)
        member.type = kind
        member.linkname = "/etc/passwd" if kind == tarfile.SYMTYPE else ""
        member.size = 2 if kind == tarfile.REGTYPE else 0
        bundle.addfile(member, io.BytesIO(b"ok") if member.size else None)


def test_valid_build(tmp_path):
    bundle, stage = tmp_path / "build.tgz", tmp_path / "stage"
    stage.mkdir()
    archive(bundle, "./index.html")
    publisher.extract_build(bundle, stage)
    assert (stage / "index.html").read_text() == "ok"


@pytest.mark.parametrize("name,kind", [
    ("../escape", tarfile.REGTYPE),
    ("/absolute", tarfile.REGTYPE),
    ("index.html", tarfile.SYMTYPE),
    ("index.html", tarfile.LNKTYPE),
    ("index.html", tarfile.FIFOTYPE),
])
def test_unsafe_archive_rejected(tmp_path, name, kind):
    bundle, stage = tmp_path / "build.tgz", tmp_path / "stage"
    stage.mkdir()
    archive(bundle, name, kind)
    with pytest.raises(ValueError):
        publisher.extract_build(bundle, stage)
    assert not (tmp_path / "escape").exists()


def test_missing_entrypoint_rejected(tmp_path):
    bundle, stage = tmp_path / "build.tgz", tmp_path / "stage"
    stage.mkdir()
    archive(bundle, "other.html")
    with pytest.raises(ValueError, match="index.html"):
        publisher.extract_build(bundle, stage)
