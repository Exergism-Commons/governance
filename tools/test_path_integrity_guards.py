#!/usr/bin/env python3
"""Focused guards for repository path-integrity invariants."""

from __future__ import annotations

import tempfile
from pathlib import Path

import governance_path_integrity as path_integrity


def expect_failure(label: str, callback) -> None:
    try:
        callback()
    except SystemExit:
        return
    raise SystemExit(f"path-integrity guard failure: {label} unexpectedly validated")


def main() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / "records" / "evidence").mkdir(parents=True)
        (root / "mutable.json").write_text('{"value": 1}\n', encoding="utf-8")
        (root / "records" / "evidence" / "regular.json").write_text('{"value": 1}\n', encoding="utf-8")
        path_integrity.require_no_symlinks(root)

        (root / "records" / "evidence" / "linked.json").symlink_to(root / "mutable.json")
        expect_failure(
            "content-addressed record symlink",
            lambda: path_integrity.require_no_symlinks(root),
        )
        (root / "records" / "evidence" / "linked.json").unlink()

        (root / "real-dir").mkdir()
        (root / "real-dir" / "record.json").write_text('{"value": 1}\n', encoding="utf-8")
        (root / "records" / "linked-dir").symlink_to(root / "real-dir", target_is_directory=True)
        expect_failure(
            "symlinked parent directory",
            lambda: path_integrity.require_no_symlinks(root),
        )

    print("Path-integrity guards: PASS (3 cases)")


if __name__ == "__main__":
    main()
