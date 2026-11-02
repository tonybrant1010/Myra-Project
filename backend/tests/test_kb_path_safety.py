import io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException, Request, UploadFile

import server


@pytest.fixture
def kb_root(tmp_path, monkeypatch):
    root = tmp_path / "backend"
    (root / "data/kb_pdfs").mkdir(parents=True)
    monkeypatch.setattr(server, "ROOT_DIR", root)
    return root


def make_symlink(link, target, *, directory=False):
    try:
        link.symlink_to(target, target_is_directory=directory)
    except (OSError, NotImplementedError):
        pytest.skip("Creating symlinks is unavailable on this platform")


@pytest.mark.parametrize("name", [
    "../outside.pdf", "/outside.pdf", "nested/file.pdf", r"nested\file.pdf",
    "C:outside.pdf", ".hidden.pdf", "notes.txt", "bad\x00name.pdf", "",
])
def test_kb_pdf_path_rejects_unsafe_or_non_pdf_names(kb_root, name):
    with pytest.raises(HTTPException) as error:
        server._kb_pdf_path(name)
    assert error.value.status_code == 400


def test_kb_pdf_path_preserves_unicode_and_uppercase_extension(kb_root):
    name = "Árvíztűrő tükörfúrógép.PDF"
    path = server._kb_pdf_path(name)
    assert path.name == name
    assert path.parent == (kb_root / "data/kb_pdfs").resolve()
    server._write_kb_pdf(name, b"%PDF-1.7\noriginal")
    assert path.read_bytes() == b"%PDF-1.7\noriginal"


@pytest.mark.parametrize("operation", ["resolve", "upload"])
def test_kb_pdf_operations_reject_existing_symlink_without_touching_target(kb_root, tmp_path, operation):
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"private outside data")
    link = kb_root / "data/kb_pdfs/linked.pdf"
    make_symlink(link, outside)
    with pytest.raises(HTTPException) as error:
        if operation == "upload":
            server._write_kb_pdf(link.name, b"%PDF-1.7\nreplacement")
        else:
            server._kb_pdf_path(link.name)
    assert error.value.status_code == 400
    assert outside.read_bytes() == b"private outside data"
    assert link.is_symlink()


@pytest.mark.parametrize("component", ["data", "data/kb_pdfs"])
def test_kb_rejects_symlinked_storage_directories(tmp_path, monkeypatch, component):
    root = tmp_path / "backend"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    link = root / component
    link.parent.mkdir(parents=True, exist_ok=True)
    make_symlink(link, outside, directory=True)
    monkeypatch.setattr(server, "ROOT_DIR", root)
    with pytest.raises(HTTPException) as error:
        server._write_kb_pdf("notes.pdf", b"%PDF-1.7\nnew")
    assert error.value.status_code == 400
    assert list(outside.iterdir()) == []


def test_atomic_upload_does_not_follow_a_destination_symlink_created_after_validation(
        kb_root, tmp_path, monkeypatch):
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"private outside data")
    destination = kb_root / "data/kb_pdfs/notes.pdf"
    real_replace = Path.replace

    def replace_after_link_appears(source, target):
        if source.name.startswith(".kb-upload-"):
            make_symlink(destination, outside)
        return real_replace(source, target)

    monkeypatch.setattr(Path, "replace", replace_after_link_appears)
    server._write_kb_pdf(destination.name, b"%PDF-1.7\nnew")
    assert outside.read_bytes() == b"private outside data"
    assert not destination.is_symlink()
    assert destination.read_bytes() == b"%PDF-1.7\nnew"
    assert not list(destination.parent.glob(".kb-upload-*"))


def test_failed_upload_publication_keeps_old_pdf_and_cleans_temporary_file(kb_root, monkeypatch):
    destination = kb_root / "data/kb_pdfs/notes.pdf"
    destination.write_bytes(b"%PDF-1.7\nold")

    def fail_replace(*_args):
        raise OSError("Publication failed")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="Publication failed"):
        server._write_kb_pdf(destination.name, b"%PDF-1.7\nnew")
    assert destination.read_bytes() == b"%PDF-1.7\nold"
    assert not list(destination.parent.glob(".kb-upload-*"))


@pytest.mark.anyio
async def test_delete_rejects_symlink_and_does_not_change_database(kb_root, tmp_path, monkeypatch):
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"private outside data")
    link = kb_root / "data/kb_pdfs/linked.pdf"
    make_symlink(link, outside)
    db = SimpleNamespace(execute=AsyncMock())
    audit = AsyncMock()
    monkeypatch.setattr(server, "_admin_audit", audit)
    with pytest.raises(HTTPException) as error:
        await server.admin_delete_kb_file(link.name, Request({"type": "http"}),
                                          SimpleNamespace(id=1), db)
    assert error.value.status_code == 400
    db.execute.assert_not_awaited()
    audit.assert_not_awaited()
    assert outside.read_bytes() == b"private outside data"


@pytest.mark.anyio
async def test_valid_pdf_delete_keeps_outside_file_and_updates_index(kb_root, tmp_path, monkeypatch):
    name = "Árvíztűrő.PDF"
    pdf = kb_root / "data/kb_pdfs" / name
    pdf.write_bytes(b"%PDF-1.7\nknowledge")
    outside = tmp_path / name
    outside.write_bytes(b"outside")
    db = SimpleNamespace(execute=AsyncMock())
    audit = AsyncMock()
    monkeypatch.setattr(server, "_admin_audit", audit)
    result = await server.admin_delete_kb_file(name, Request({"type": "http"}),
                                                SimpleNamespace(id=1), db)
    assert result == {"ok": True}
    assert not pdf.exists()
    assert outside.read_bytes() == b"outside"
    db.execute.assert_awaited_once()
    assert audit.await_args.args[3:] == ("admin.kb.delete_file", f"filename={name}")


@pytest.mark.anyio
async def test_pdf_list_does_not_follow_links_and_includes_uppercase_extension(kb_root, tmp_path):
    pdf_dir = kb_root / "data/kb_pdfs"
    (pdf_dir / "Árvíztűrő.PDF").write_bytes(b"%PDF-1.7\nknowledge")
    (pdf_dir / "not-a-file.pdf").mkdir()
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"private outside data")
    make_symlink(pdf_dir / "linked.pdf", outside)
    result = await server.admin_list_kb_files(SimpleNamespace(id=1))
    assert [item["name"] for item in result["files"]] == ["Árvíztűrő.PDF"]


@pytest.mark.anyio
async def test_invalid_pdf_upload_does_not_publish_file(kb_root, monkeypatch):
    audit = AsyncMock()
    monkeypatch.setattr(server, "_admin_audit", audit)
    upload = UploadFile(filename="notes.pdf", file=io.BytesIO(b"not a PDF"))
    try:
        with pytest.raises(HTTPException) as error:
            await server.admin_upload_kb_file(Request({"type": "http"}), upload,
                                               SimpleNamespace(id=1), SimpleNamespace())
        assert error.value.status_code == 400
        assert list((kb_root / "data/kb_pdfs").iterdir()) == []
        audit.assert_not_awaited()
    finally:
        await upload.close()
