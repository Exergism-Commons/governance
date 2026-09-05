from __future__ import annotations

import os
from datetime import date

import governance_delegation_lifecycle as delegation_lifecycle
import governance_interrelease_integrity as interrelease
import governance_release_history as release_history
import validate_governance as core


# This module is imported by the canonical validator only after
# governance_interrelease_integrity.install() has installed its historical
# creation-policy wrapper. Capture that composed validator, then add the two
# invariants that require repository-DAG and prospective-policy context.
ORIG_VALIDATE_DELEGATIONS = delegation_lifecycle.validate_delegations
ORIG_DELEGATION_ACTIVE_ON = delegation_lifecycle.delegation_active_on

_DELEGATION_POLICY_TIMELINE: list[tuple[date, frozenset[str]]] = []
_INSTALLED = False


def _history_base() -> str | None:
    base = os.environ.get("EC_GOVERNANCE_HISTORY_BASE", "").strip()
    if not base or set(base) <= {"0"}:
        return None
    core.require(
        interrelease._git(["cat-file", "-e", f"{base}^{{commit}}"], check=False).returncode == 0,
        "repository-history base commit is unavailable",
    )
    merge_base = interrelease._git(["merge-base", base, "HEAD"]).stdout.strip()
    core.require(bool(merge_base), "repository-history base has no merge-base with HEAD")
    return merge_base


def _commit_parents(commit: str) -> list[str]:
    line = interrelease._git(["rev-list", "--parents", "-n", "1", commit]).stdout.strip().split()
    core.require(bool(line) and line[0] == commit, f"cannot resolve repository-history parents for {commit}")
    return line[1:]


def _is_descendant_or_equal(ancestor: str, commit: str) -> bool:
    if ancestor == commit:
        return True
    return interrelease._git(["merge-base", "--is-ancestor", ancestor, commit], check=False).returncode == 0


def _require_records_transition_append_only(parent: str, commit: str) -> None:
    """Reject any record rewrite/removal at one committed DAG edge.

    Endpoint diffs are insufficient: A->D or A->M sequences can disappear from
    base..HEAD. Checking every parent->child transition makes append-only a
    property of the committed history, not merely its final snapshot.
    """
    diff = interrelease._git(
        ["diff", "--name-status", "--find-renames", parent, commit, "--", "records/"]
    )
    for raw in diff.stdout.splitlines():
        if not raw.strip():
            continue
        status_code = raw.split("\t", 1)[0]
        core.require(
            status_code == "A",
            f"committed content-addressed records are append-only at {parent[:12]}->{commit[:12]}; forbidden change: {raw}",
        )


def _require_membership_transition_append_only(parent: str, commit: str) -> None:
    previous = interrelease._git_show_json(parent, "policy/membership-status.json")
    if previous is None:
        return
    current = interrelease._git_show_json(commit, "policy/membership-status.json")
    core.require(
        current is not None,
        f"membership registry removed from committed history at {parent[:12]}->{commit[:12]}",
    )
    interrelease._validate_membership_registry_extension(previous, current)


def validate_commit_transition(parent: str, commit: str) -> None:
    _require_records_transition_append_only(parent, commit)
    _require_membership_transition_append_only(parent, commit)


def validate_every_commit_after_history_base(base: str) -> None:
    commits = [
        value.strip()
        for value in interrelease._git(
            ["rev-list", "--reverse", "--topo-order", "--ancestry-path", f"{base}..HEAD"]
        ).stdout.splitlines()
        if value.strip()
    ]
    for commit in commits:
        parents = _commit_parents(commit)
        eligible = [parent for parent in parents if _is_descendant_or_equal(base, parent)]
        core.require(
            bool(eligible),
            f"repository-history commit {commit} has no parent inside the trusted ancestry",
        )
        # A merge must preserve the append-only history of every in-range parent,
        # not merely its first parent. This prevents a merge resolution from
        # dropping a record or established Member that existed on one side.
        for parent in eligible:
            validate_commit_transition(parent, commit)


def validate_repository_history() -> None:
    # Retain all endpoint/current-tree checks from the first inter-release gate.
    interrelease.validate_repository_history()
    base = _history_base()
    if base is None:
        return
    validate_every_commit_after_history_base(base)


def _build_delegation_policy_timeline(status: dict) -> None:
    _DELEGATION_POLICY_TIMELINE.clear()
    if status.get("operative") is not True:
        return
    previous: date | None = None
    for adoption, _ in release_history.release_chain(status):
        effective = core.parse_iso_date(
            adoption.get("effective_date"),
            f"governance release #{adoption.get('release_sequence')} delegation-policy effective_date",
        )
        if previous is not None:
            core.require(previous < effective, "delegation-policy release timeline must be strictly increasing")
        snapshot = interrelease.validate_delegation_policy_snapshot(
            adoption,
            f"governance release #{adoption.get('release_sequence')}",
        )
        reserved = snapshot.get("reserved_non_delegable_actions")
        core.require(isinstance(reserved, list), "delegation-policy snapshot reserved actions must be a list")
        _DELEGATION_POLICY_TIMELINE.append((effective, frozenset(reserved)))
        previous = effective


def _reserved_actions_as_of(target: date) -> frozenset[str]:
    result: frozenset[str] = frozenset()
    for effective, reserved in _DELEGATION_POLICY_TIMELINE:
        if effective > target:
            break
        result = reserved
    return result


def delegation_active_on(item: dict, target: date) -> bool:
    """Return whether a retained grant still supplies usable delegated authority.

    The immutable grant is interpreted under its creation release, but a later
    release may reserve an action prospectively. Once that release is effective,
    a still-unrevoked grant containing a now-reserved allowed action cannot be
    treated as an active delegation. Historical dates remain evaluated against
    the policy actually effective at those dates.
    """
    if not ORIG_DELEGATION_ACTIVE_ON(item, target):
        return False
    allowed = item.get("allowed_actions")
    core.require(isinstance(allowed, list), f"delegation {item.get('delegation_id')} allowed_actions invalid")
    return not bool(set(allowed).intersection(_reserved_actions_as_of(target)))


def validate_delegations(delegations: dict, status: dict, rules: dict, membership: dict):
    _build_delegation_policy_timeline(status)
    validated = ORIG_VALIDATE_DELEGATIONS(delegations, status, rules, membership)
    if status.get("operative") is not True:
        return validated

    chain = release_history.release_chain(status)
    core.require(bool(chain), "operative governance requires release chain for prospective delegation constraints")
    current, _ = chain[-1]
    current_effective = core.parse_iso_date(
        current.get("effective_date"),
        "current governance release delegation-policy effective_date",
    )
    current_reserved = _reserved_actions_as_of(current_effective)
    for item in validated:
        # Use the underlying grant lifecycle here so a revocation effective by
        # the new policy date satisfies the gate. If the grant would otherwise
        # still be active, no newly reserved action may remain exercisable.
        if not ORIG_DELEGATION_ACTIVE_ON(item, current_effective):
            continue
        conflict = sorted(set(item.get("allowed_actions", [])).intersection(current_reserved))
        core.require(
            not conflict,
            f"delegation {item.get('delegation_id')} remains active when current policy reserves allowed action(s): {', '.join(conflict)}; revoke it no later than the policy effective date",
        )
    return validated


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    delegation_lifecycle.validate_delegations = validate_delegations
    delegation_lifecycle.delegation_active_on = delegation_active_on
    _INSTALLED = True
