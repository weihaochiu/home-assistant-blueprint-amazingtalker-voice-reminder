"""Create and verify a source-only repository backup before each push."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = ROOT / "BACKUP"
KEEP_LATEST = 10
EXCLUDED_DIRS = {
    ".git",
    "BACKUP",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
}


def git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout.strip()


def source_files():
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if not path.is_file() or any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        if path.suffix.lower() == ".pyc" or path.name.endswith(".tmp"):
            continue
        yield path, relative


def create_backup() -> Path:
    timestamp = datetime.now().astimezone()
    repository = ROOT.name
    branch = git("branch", "--show-current") or "detached"
    head = git("rev-parse", "HEAD")
    status = git("status", "--short") or "clean"
    # Microseconds avoid overwriting a valid backup when pushes happen in the
    # same second while retaining a human-readable local timestamp.
    stamp = timestamp.strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{repository}_{stamp}_{head[:7]}.zip"
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    destination = BACKUP_DIR / filename
    temporary = BACKUP_DIR / f".{filename}.tmp"
    manifest = "\n".join(
        [
            f"timestamp: {timestamp.isoformat()}",
            f"repository: {repository}",
            f"branch: {branch}",
            f"HEAD SHA: {head}",
            "git status:",
            status,
            "",
        ]
    )

    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path, relative in source_files():
                archive.write(path, relative.as_posix())
            archive.writestr("BACKUP_MANIFEST.txt", manifest)
        with zipfile.ZipFile(temporary, "r") as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                raise RuntimeError(f"ZIP verification failed at {bad_member}")
            if "BACKUP_MANIFEST.txt" not in archive.namelist():
                raise RuntimeError("ZIP verification failed: manifest missing")
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()

    backups = sorted(
        BACKUP_DIR.glob(f"{repository}_*.zip"),
        key=lambda item: (item.stat().st_mtime_ns, item.name),
        reverse=True,
    )
    for old_backup in backups[KEEP_LATEST:]:
        old_backup.unlink()
    return destination


if __name__ == "__main__":
    backup = create_backup()
    print(f"Backup created and verified: {backup}")
    print(f"Retention: latest {KEEP_LATEST} backups")
