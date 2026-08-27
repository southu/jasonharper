#!/usr/bin/env python3
"""Unpack HostGator uploads.zip into wp-content/uploads at locked public paths.

Reads the export from disk. Does not copy the zip into git.
Filenames and YYYY/MM paths are preserved exactly — no rename, hash, or restamp.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ZIP_CANDIDATES = [
    Path("/opt/projects/jasonharper/export/uploads.zip"),
    Path("/opt/projects/jasonharper/export/uploads/uploads.zip"),
]
DEST_PARENT = REPO / "wp-content"
DEST = DEST_PARENT / "uploads"


def zip_path() -> Path:
    for candidate in ZIP_CANDIDATES:
        if candidate.is_file():
            return candidate
    raise SystemExit(
        "missing uploads.zip (expected at /opt/projects/jasonharper/export/uploads.zip)"
    )


def main() -> None:
    src = zip_path()
    DEST_PARENT.mkdir(parents=True, exist_ok=True)
    # -o overwrite, -q quiet. Zip members are uploads/YYYY/MM/filename.
    result = subprocess.run(
        ["unzip", "-o", "-q", str(src), "-d", str(DEST_PARENT)],
        check=False,
    )
    if result.returncode not in (0, 1):
        # unzip returns 1 when warnings occurred (e.g. extra bytes) but files extracted.
        raise SystemExit(f"unzip failed with code {result.returncode}")
    if not DEST.is_dir():
        raise SystemExit(f"unpack produced no {DEST.relative_to(REPO)} directory")
    files = [p for p in DEST.rglob("*") if p.is_file()]
    print(f"unpacked {len(files)} files from {src} into {DEST.relative_to(REPO)}/", file=sys.stderr)


if __name__ == "__main__":
    main()
