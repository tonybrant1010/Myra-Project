import io
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile


def main():
    publisher = Path(__file__).parents[1] / "publish_frontend.py"
    with tempfile.TemporaryDirectory(prefix="myra-publish-test-") as temporary:
        root = Path(temporary)
        target = root / "dist"
        target.mkdir()
        (target / "index.html").write_text("previous", encoding="utf-8")
        (target / "obsolete.js").write_text("old", encoding="utf-8")
        archive = root / "build.tgz"
        with tarfile.open(archive, "w:gz") as bundle:
            info = tarfile.TarInfo("index.html")
            info.size = len(b"candidate")
            bundle.addfile(info, io.BytesIO(b"candidate"))
        result = subprocess.run([sys.executable, str(publisher), str(archive), "--target", str(target)],
                                check=True, capture_output=True, text=True)
        assert (target / "index.html").read_text() == "candidate"
        assert not (target / "obsolete.js").exists()
        previous = next(line.split(": ", 1)[1] for line in result.stdout.splitlines()
                        if line.startswith("Previous release retained:"))
        assert Path(previous).parent == root
        assert (Path(previous) / "obsolete.js").is_file()
        subprocess.run([sys.executable, str(publisher), "--target", str(target), "--rollback", previous], check=True)
        assert (target / "index.html").read_text() == "previous"
        assert (target / "obsolete.js").is_file()
    print("FRONTEND_PUBLISH_ROLLBACK_OK")


if __name__ == "__main__":
    main()
