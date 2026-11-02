#!/usr/bin/env python3
import argparse
import ctypes
import os
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile


def extract_build(archive: Path, stage: Path) -> None:
    total = 0
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle:
            name = PurePosixPath(member.name)
            if name.is_absolute() or ".." in name.parts or "\\" in member.name:
                raise ValueError("Unsafe archive path")
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError("Only regular build files are allowed")
            total += member.size
            if total > 512 * 1024 * 1024:
                raise ValueError("Build exceeds 512 MiB")
            destination = stage.joinpath(*name.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with bundle.extractfile(member) as source, destination.open("xb") as output:
                shutil.copyfileobj(source, output)
            destination.chmod(0o644)
    if not (stage / "index.html").is_file():
        raise ValueError("Build must contain index.html")
    stage.chmod(0o755)
    for folder in stage.rglob("*"):
        if folder.is_dir():
            folder.chmod(0o755)


def exchange(left: Path, right: Path) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    rename = libc.renameat2
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(-100, os.fsencode(left), -100, os.fsencode(right), 2) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))


def main():
    import fcntl

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", nargs="?", type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--rollback", type=Path)
    args = parser.parse_args()
    target = args.target.absolute()
    if target.is_symlink() or not target.is_dir() or target == Path("/"):
        parser.error("Target must be an existing real frontend directory")
    with (target.parent / ".frontend-publish.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if args.rollback:
            previous = args.rollback.absolute()
            if previous.parent != target.parent or previous.is_symlink() or not (previous / "index.html").is_file():
                parser.error("Rollback must be a release directory beside target")
            exchange(target, previous)
            print("Restored previous frontend release")
            return
        if not args.archive:
            parser.error("An archive or --rollback is required")
        stage = Path(tempfile.mkdtemp(prefix=".frontend-release-", dir=target.parent))
        try:
            extract_build(args.archive, stage)
            exchange(target, stage)
        except Exception:
            shutil.rmtree(stage)
            raise
        print(f"Published: {target}")
        print(f"Previous release retained: {stage}")
        print(f"Rollback: python3 {Path(__file__).absolute()} --target {target} --rollback {stage}")


if __name__ == "__main__":
    main()
