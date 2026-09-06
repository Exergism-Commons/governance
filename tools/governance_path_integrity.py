from __future__ import annotations

import os
import subprocess
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


def _git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise SystemExit(f"governance integrity failure: git unavailable for repository path integrity: {exc}") from exc


def _require_literal_index_entries(root: Path) -> None:
    """Reject index flags that can make worktree changes invisible to status.

    `assume-unchanged` and `skip-worktree` are useful Git performance/sparse
    checkout mechanisms, but they are incompatible with an authority validator
    whose security boundary is "the bytes in HEAD". `git ls-files -v` renders
    ordinary tracked entries as `H`; assume-unchanged uses a lowercase tag and
    skip-worktree uses `S`. Requiring ordinary entries prevents those flags from
    manufacturing a falsely clean checkout.
    """
    listed = _git(root, ["ls-files", "-v"])
    core.require(listed.returncode == 0, "cannot inspect governance Git index flags")
    nonliteral = [
        line
        for line in listed.stdout.splitlines()
        if line.strip() and not line.startswith("H ")
    ]
    core.require(
        not nonliteral,
        "canonical governance validation forbids Git index shortcuts such as "
        f"assume-unchanged/skip-worktree: {'; '.join(nonliteral[:10])}",
    )


def require_clean_git_checkout(root: Path) -> None:
    """Require every repository byte consumed by the canonical verdict to be in HEAD.

    The history validator reasons about committed Git objects. Letting the final
    verdict read staged, modified, deleted, or untracked worktree bytes would
    create a second authority state that is absent from repository history and
    may disappear on a clean checkout. Requiring a clean checkout is stronger
    and easier to audit than maintaining a partial allow-list of authority paths.
    """
    root = root.resolve()
    head = _git(root, ["rev-parse", "--verify", "HEAD^{commit}"])
    core.require(
        head.returncode == 0 and bool(head.stdout.strip()),
        "canonical governance validation requires a Git checkout with a committed HEAD",
    )
    _require_literal_index_entries(root)
    status = _git(
        root,
        ["status", "--porcelain=v1", "--untracked-files=all", "--ignore-submodules=none"],
    )
    core.require(status.returncode == 0, "cannot inspect governance Git worktree state")
    dirty = [line for line in status.stdout.splitlines() if line.strip()]
    core.require(
        not dirty,
        "canonical governance validation requires an exact clean HEAD checkout; "
        f"uncommitted/untracked repository bytes detected: {'; '.join(dirty[:10])}",
    )


def validate_repository_paths() -> None:
    require_no_symlinks(core.ROOT)
    require_clean_git_checkout(core.ROOT)
