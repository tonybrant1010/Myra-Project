import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("build_release", Path(__file__).parents[1] / "build_release.py")
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


def test_linux_scripts_packaged_without_bom_or_crlf(tmp_path):
    source = tmp_path / "test.sh"
    source.write_bytes(b"\xef\xbb\xbf#!/bin/bash\r\necho ok\r\n")
    assert release.release_bytes(source) == b"#!/bin/bash\necho ok\n"


def test_binary_assets_are_unchanged(tmp_path):
    source = tmp_path / "asset.png"
    original = b"\x89PNG\r\n\x00\xff"
    source.write_bytes(original)
    assert release.release_bytes(source) == original
