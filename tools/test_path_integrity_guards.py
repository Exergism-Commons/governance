#!/usr/bin/env python3
"""Focused guards for repository path-integrity invariants."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import governance_path_integrity as path_integrity


def expect_failure(label: str, callback) -> None:
    try:
        callback()
    except SystemExit:
        return
    raise SystemExit(f"path-integrity guard failure: {label} unexpectedly validated")


def git(root: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"path-integrity guard git failure: {result.stderr.strip() or result.stdout.strip()}")


def validate_symlink_guards() -> int:
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
    return 3


def validate_clean_checkout_guards() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        git(root, "init", "-q")
        git(root, "config", "user.email", "governance-guard@example.invalid")
        git(root, "config", "user.name", "Governance Guard")
        tracked = root / "policy.json"
        tracked.write_text('{"operative": false}\n', encoding="utf-8")
        git(root, "add", "policy.json")
        git(root, "commit", "-qm", "initial")

        path_integrity.require_clean_git_checkout(root)

        tracked.write_text('{"operative": true}\n', encoding="utf-8")
        expect_failure(
            "dirty tracked authority bytes",
            lambda: path_integrity.require_clean_git_checkout(root),
        )
        git(root, "restore", "policy.json")

        (root / "records.json").write_text('{"record_type": "evidence"}\n', encoding="utf-8")
        expect_failure(
            "untracked authority bytes",
            lambda: path_integrity.require_clean_git_checkout(root),
        )
    return 3


def main() -> None:
    total = validate_symlink_guards() + validate_clean_checkout_guards()
    print(f"Path-integrity guards: PASS ({total} cases)")


if __name__ == "__main__":
    main()
