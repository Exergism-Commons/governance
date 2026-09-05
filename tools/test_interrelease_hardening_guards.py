#!/usr/bin/env python3
"""Focused guards for repository-DAG history and prospective delegation policy."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import governance_delegation_lifecycle as delegation_lifecycle
import governance_interrelease_hardening as hardening
import governance_interrelease_integrity as interrelease


def expect_failure(label: str, callback) -> None:
    try:
        callback()
    except SystemExit:
        return
    raise SystemExit(f"inter-release hardening guard failure: {label} unexpectedly validated")


def validate_per_commit_record_history_guards() -> int:
    original_git = interrelease._git
    try:
        # A record introduced at one committed edge is valid.
        interrelease._git = lambda *args, **kwargs: SimpleNamespace(
            stdout="A\trecords/decisions/member-a.json\n", returncode=0
        )
        hardening._require_records_transition_append_only("parent-a", "commit-a")

        # The same path disappearing on the next edge must fail even though an
        # endpoint base..HEAD diff could contain no trace of either operation.
        interrelease._git = lambda *args, **kwargs: SimpleNamespace(
            stdout="D\trecords/decisions/member-a.json\n", returncode=0
        )
        expect_failure(
            "add-then-delete cannot disappear inside a multi-commit range",
            lambda: hardening._require_records_transition_append_only("commit-a", "commit-b"),
        )

        interrelease._git = lambda *args, **kwargs: SimpleNamespace(
            stdout="M\trecords/decisions/member-a.json\n", returncode=0
        )
        expect_failure(
            "content-addressed record cannot be rewritten at an intermediate commit",
            lambda: hardening._require_records_transition_append_only("commit-a", "commit-c"),
        )
    finally:
        interrelease._git = original_git
    return 3


def validate_pre_base_side_branch_traversal_guard() -> int:
    """A side branch forked before base must still have every internal edge walked."""
    original_git = interrelease._git
    original_parents = hardening._commit_parents
    original_transition = hardening.validate_commit_transition
    calls: list[tuple[str, str]] = []
    commands: list[list[str]] = []
    try:
        def fake_git(args, **kwargs):
            commands.append(list(args))
            if args[:4] == ["rev-list", "--reverse", "--topo-order", "HEAD"]:
                # side-a forked from an older commit before trusted-base;
                # side-b follows it and merge-c later merges it into HEAD.
                return SimpleNamespace(stdout="side-a\nside-b\nmerge-c\n", returncode=0)
            raise AssertionError(f"unexpected git command in side-branch guard: {args}")

        parents = {
            "side-a": ["fork-before-trusted-base"],
            "side-b": ["side-a"],
            "merge-c": ["main-parent", "side-b"],
        }
        interrelease._git = fake_git
        hardening._commit_parents = lambda commit: parents[commit]
        hardening.validate_commit_transition = lambda parent, commit: calls.append((parent, commit))

        hardening.validate_every_commit_after_history_base("trusted-base")
        required = {
            ("fork-before-trusted-base", "side-a"),
            ("side-a", "side-b"),
            ("main-parent", "merge-c"),
            ("side-b", "merge-c"),
        }
        if set(calls) != required:
            raise SystemExit(
                f"inter-release hardening guard failure: pre-base side branch edges not fully traversed: {calls}"
            )
        if not commands or commands[0][-2:] != ["--not", "trusted-base"] or "--ancestry-path" in commands[0]:
            raise SystemExit(
                "inter-release hardening guard failure: traversal did not use HEAD --not trusted-base reachability"
            )
    finally:
        interrelease._git = original_git
        hardening._commit_parents = original_parents
        hardening.validate_commit_transition = original_transition
    return 1


def _delegation() -> dict:
    return {
        "delegation_id": "delegation-a",
        "effective_date": "2026-01-01",
        "expires_at": None,
        "allowed_actions": ["routine-action", "later-reserved-action"],
    }


def validate_prospective_reserved_action_guards() -> int:
    hardening._DELEGATION_POLICY_TIMELINE[:] = [
        (date(2026, 1, 1), frozenset({"constitutional-amendment"})),
        (date(2026, 6, 1), frozenset({"constitutional-amendment", "later-reserved-action"})),
        # A later release removes the extra reservation. That must not resurrect
        # an older grant which already crossed the conflicting R2 boundary.
        (date(2026, 9, 1), frozenset({"constitutional-amendment"})),
    ]
    item = _delegation()

    if not hardening.delegation_active_on(item, date(2026, 5, 31)):
        raise SystemExit("inter-release hardening guard failure: later policy applied retroactively")
    if hardening.delegation_active_on(item, date(2026, 6, 1)):
        raise SystemExit("inter-release hardening guard failure: newly reserved action remained delegated")
    if hardening.delegation_active_on(item, date(2026, 10, 1)):
        raise SystemExit("inter-release hardening guard failure: later policy removal resurrected an old grant")

    # A genuinely new grant beginning after the reservation was removed is not
    # tainted by a reservation that existed only before its own effective date.
    new_item = dict(item)
    new_item["delegation_id"] = "delegation-new"
    new_item["effective_date"] = "2026-10-01"
    if not hardening.delegation_active_on(new_item, date(2026, 10, 1)):
        raise SystemExit("inter-release hardening guard failure: historical reservation blocked a new post-removal grant")
    return 4


def validate_every_release_boundary_conflict_gate() -> int:
    item = _delegation()
    status = {"operative": True}
    original_validate = hardening.ORIG_VALIDATE_DELEGATIONS
    original_build = hardening._build_delegation_policy_timeline
    original_revocations = dict(delegation_lifecycle.REVOCATION_EFFECTIVE_DATES)
    try:
        hardening.ORIG_VALIDATE_DELEGATIONS = lambda *args, **kwargs: [item]

        def build(_status):
            hardening._DELEGATION_POLICY_TIMELINE[:] = [
                (date(2026, 1, 1), frozenset({"constitutional-amendment"})),
                (date(2026, 6, 1), frozenset({"constitutional-amendment", "later-reserved-action"})),
                # Current R3 no longer reserves the action. Validation must still
                # reject a grant that remained live at the earlier R2 boundary.
                (date(2026, 9, 1), frozenset({"constitutional-amendment"})),
            ]

        hardening._build_delegation_policy_timeline = build
        delegation_lifecycle.REVOCATION_EFFECTIVE_DATES.clear()

        expect_failure(
            "latest release cannot hide an unrevoked earlier reservation conflict",
            lambda: hardening.validate_delegations({}, status, {}, {}),
        )

        # Revoking only after the R2 boundary is too late; authority existed for
        # a period in which the action was already non-delegable.
        delegation_lifecycle.REVOCATION_EFFECTIVE_DATES[item["delegation_id"]] = date(2026, 7, 1)
        expect_failure(
            "post-boundary revocation cannot retroactively cure stale authority",
            lambda: hardening.validate_delegations({}, status, {}, {}),
        )

        # Revocation effective exactly when R2 takes effect is sufficient.
        delegation_lifecycle.REVOCATION_EFFECTIVE_DATES[item["delegation_id"]] = date(2026, 6, 1)
        hardening.validate_delegations({}, status, {}, {})
    finally:
        hardening.ORIG_VALIDATE_DELEGATIONS = original_validate
        hardening._build_delegation_policy_timeline = original_build
        delegation_lifecycle.REVOCATION_EFFECTIVE_DATES.clear()
        delegation_lifecycle.REVOCATION_EFFECTIVE_DATES.update(original_revocations)
        hardening._DELEGATION_POLICY_TIMELINE.clear()
    return 3


def main() -> None:
    total = 0
    total += validate_per_commit_record_history_guards()
    total += validate_pre_base_side_branch_traversal_guard()
    total += validate_prospective_reserved_action_guards()
    total += validate_every_release_boundary_conflict_gate()
    print(f"Inter-release hardening guards: PASS ({total} cases)")


if __name__ == "__main__":
    main()
