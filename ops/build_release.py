#!/usr/bin/env python3
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


def release_bytes(source):
    raw = source.read_bytes()
    if source.suffix.lower() in {".sh", ".py", ".service", ".timer", ".yml", ".yaml", ".ini", ".conf", ".md", ".js"}:
        return raw.decode("utf-8-sig").replace("\r\n", "\n").encode("utf-8")
    return raw


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=root / "release-candidate" / "myra-repair-source.tgz")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise ValueError("Candidate already exists; choose a new --output name to preserve the reviewed archive")
    output.parent.mkdir(parents=True, exist_ok=True)
    paths = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=root)
    documentation = {"docs/CURRENT-DEPLOYMENT.md", "docs/helyi-modell.md",
                     "docs/adatkezelesi-nyilvantartas.md", "docs/hatasvizsgalat-dpia.md",
                     "publication/README.md", "tests/README.md"}
    candidates = paths.decode("utf-8").split("\0")
    candidates.extend(name for name in documentation if (root / name).is_file())
    members = []
    for raw in sorted(set(candidates)):
        if not raw:
            continue
        relative = Path(raw)
        if relative.parts[0] in {"release-candidate", "_private"}:
            continue
        if any(part.startswith(".env") and part != ".env.example" for part in relative.parts):
            raise ValueError(f"Credential file must not be packaged: {raw}")
        root_files = {".env.example", ".gitattributes", ".gitignore", "LICENSE", "README.md",
                      "docker-compose.yml", "docker-compose.override.yml", "design_guidelines.json"} | documentation
        if relative.parts[0] not in {"backend", "frontend", "ops", "assets", ".github"} and raw not in root_files:
            continue
        source = root / relative
        if not source.exists() and not source.is_symlink():
            continue
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"Invalid source candidate member: {raw}")
        if source == output:
            continue
        members.append((raw, source))
    required = {"backend/seed/state_codes.json", "backend/server.py", "backend/game_validation.py",
                "backend/notification_outbox.py", "ops/verify-isolated.sh", "ops/publish_frontend.py"}
    if not required.issubset({name for name, _ in members}):
        raise ValueError("Release is missing required new runtime files")
    manifest = {}
    with tarfile.open(output, "w:gz") as bundle:
        for name, source in members:
            raw = release_bytes(source)
            manifest[name] = hashlib.sha256(raw).hexdigest()
            info = bundle.gettarinfo(str(source), arcname="source/" + name)
            info.size = len(raw)
            bundle.addfile(info, io.BytesIO(raw))
    result = {"archive": output.name, "sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "files": manifest}
    output.with_suffix(".manifest.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Source candidate: {output}")
    print(f"SHA256: {result['sha256']}")
    print(f"Files: {len(manifest)}; no frontend build is included")


if __name__ == "__main__":
    main()
