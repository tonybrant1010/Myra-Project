import io
from pathlib import Path

from pypdf import PdfReader


def extract_bytes(raw: bytes) -> str:
    reader = PdfReader(io.BytesIO(raw))
    return "\n".join((page.extract_text() or "") for page in reader.pages).strip()


def extract_file(path: Path) -> str:
    return extract_bytes(path.read_bytes())
