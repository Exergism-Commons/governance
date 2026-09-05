from __future__ import annotations

import os
from pathlib import Path

import validate_governance as core


def require_no_symlinks(root: Path) -> None:
    """Reject symlinks anywhere in the checked-out governance repository.

    Governance validation intentionally treats repository paths and their
    content-addressed SHA-256 values as authority-bearing bytes. Following a
    working-tree symlink would let an unchanged path under records/** resolve to
    mutable bytes elsewhere, outside the append-only path-history gate. A
    repository-wide no-symlink invariant is simpler and safer than trying to
    remember which individual path consumers are authority-sensitive.
    """
    root = root.resolve()
    for directory, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current = Path(directory)
        # Git's own administrative directory is not repository content and may
        # contain implementation-specific links/worktree indirections.
        if current == root:
            dirnames[:] = [name for name in dirnames if name != ".git"]

        for name in [*dirnames, *filenames]:
            candidate = current / name
            core.require(
                not candidate.is_symlink(),
                f"repository authority path must not be a symlink: {candidate.relative_to(root).as_posix()}",
            )


def validate_repository_paths() -> None:
    require_no_symlinks(core.ROOT)
