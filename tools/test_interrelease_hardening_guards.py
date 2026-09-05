#!/usr/bin/env python3
"""Focused guards for per-commit history and prospective delegation policy."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import governance_delegation_lifecycle as delegation_lifecycle
import governance_interrelease_hardening as hardening
import governance_interrelease_integrity as interrelease
import governance_release_history as release_history


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
    ]
    item = _delegation()

    if not hardening.delegation_active_on(item, date(2026, 5, 31)):
        raise SystemExit("inter-release hardening guard failure: later policy applied retroactively")
    if hardening.delegation_active_on(item, date(2026, 6, 1)):
        raise SystemExit("inter-release hardening guard failure: newly reserved action remained delegated")
    return 2


def validate_current_release_conflict_gate() -> int:
    item = _delegation()
    status = {"operative": True}
    original_validate = hardening.ORIG_VALIDATE_DELEGATIONS
    original_build = hardening._build_delegation_policy_timeline
    original_chain = release_history.release_chain
    original_revocations = dict(delegation_lifecycle.REVOCATION_EFFECTIVE_DATES)
    try:
        hardening.ORIG_VALIDATE_DELEGATIONS = lambda *args, **kwargs: [item]

        def build(_status):
            hardening._DELEGATION_POLICY_TIMELINE[:] = [
                (date(2026, 6, 1), frozenset({"later-reserved-action"}))
            ]

        hardening._build_delegation_policy_timeline = build
        release_history.release_chain = lambda _status: [
            ({"release_sequence": 2, "effective_date": "2026-06-01"}, {"path": "unused", "sha256": "0" * 64})
        ]
        delegation_lifecycle.REVOCATION_EFFECTIVE_DATES.clear()

        expect_failure(
            "current release cannot leave a conflicting older delegation active",
            lambda: hardening.validate_delegations({}, status, {}, {}),
        )

        # Revocation effective exactly when the new policy takes effect is
        # sufficient: immutable grant bytes remain, but prospective authority is
        # gone before the action becomes reserved.
        delegation_lifecycle.REVOCATION_EFFECTIVE_DATES[item["delegation_id"]] = date(2026, 6, 1)
        hardening.validate_delegations({}, status, {}, {})
    finally:
        hardening.ORIG_VALIDATE_DELEGATIONS = original_validate
        hardening._build_delegation_policy_timeline = original_build
        release_history.release_chain = original_chain
        delegation_lifecycle.REVOCATION_EFFECTIVE_DATES.clear()
        delegation_lifecycle.REVOCATION_EFFECTIVE_DATES.update(original_revocations)
        hardening._DELEGATION_POLICY_TIMELINE.clear()
    return 2


def main() -> None:
    total = 0
    total += validate_per_commit_record_history_guards()
    total += validate_prospective_reserved_action_guards()
    total += validate_current_release_conflict_gate()
    print(f"Inter-release hardening guards: PASS ({total} cases)")


if __name__ == "__main__":
    main()
