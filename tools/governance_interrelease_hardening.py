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
    merge_base = interrelease._git(["merge-base", base, "HEAD"], check=False)
    core.require(
        merge_base.returncode == 0 and bool(merge_base.stdout.strip()),
        "repository-history base has no merge-base with HEAD",
    )
    # Keep the caller-supplied trusted commit as the exclusion boundary. Using
    # only its merge-base would lose side-branch commits that forked before the
    # trusted base but were merged into HEAD afterward.
    return base


def _commit_parents(commit: str) -> list[str]:
    line = interrelease._git(["rev-list", "--parents", "-n", "1", commit]).stdout.strip().split()
    core.require(bool(line) and line[0] == commit, f"cannot resolve repository-history parents for {commit}")
    return line[1:]


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
    """Validate every untrusted commit and every parent edge that introduced it.

    The relevant set is all commits reachable from HEAD but not reachable from
    the trusted base, not merely commits on an ancestry path from base to HEAD.
    This includes a side branch that forked before the trusted base and was
    merged later. Its internal add/rewrite/delete or Member-pruning edges are
    therefore still inspected before the merge result can hide them.
    """
    commits = [
        value.strip()
        for value in interrelease._git(
            ["rev-list", "--reverse", "--topo-order", "HEAD", "--not", base]
        ).stdout.splitlines()
        if value.strip()
    ]
    for commit in commits:
        parents = _commit_parents(commit)
        core.require(
            bool(parents),
            f"repository-history untrusted commit {commit} unexpectedly has no parent",
        )
        # Validate every parent edge, including an edge whose parent is already
        # reachable from the trusted base. That edge is precisely where the
        # first untrusted change on a pre-base side branch is introduced.
        for parent in parents:
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


def _reserved_actions_encountered_by(item: dict, target: date) -> frozenset[str]:
    """Return reservations that this retained grant has encountered by target.

    A reservation removed by a later release cannot resurrect an older grant:
    that older grant had to cease being usable at the first conflicting policy
    boundary. A genuinely new grant created after the reservation was removed is
    unaffected because the historical reservation predates its effective date.
    """
    start = core.parse_iso_date(
        item.get("effective_date"),
        f"delegation {item.get('delegation_id')} effective_date",
    )
    if target < start:
        return frozenset()

    encountered = set(_reserved_actions_as_of(start))
    for effective, reserved in _DELEGATION_POLICY_TIMELINE:
        if effective <= start:
            continue
        if effective > target:
            break
        encountered.update(reserved)
    return frozenset(encountered)


def delegation_active_on(item: dict, target: date) -> bool:
    """Return whether a retained grant still supplies usable delegated authority.

    The immutable grant is interpreted under its creation release, but a later
    release may reserve an action prospectively. Once this retained grant has
    encountered such a reservation, a still-unrevoked grant cannot regain that
    authority merely because an even later release removes the reservation.
    Historical dates before the first conflicting boundary remain evaluated
    under the policy then in force, while a new post-removal grant may be valid.
    """
    if not ORIG_DELEGATION_ACTIVE_ON(item, target):
        return False
    allowed = item.get("allowed_actions")
    core.require(isinstance(allowed, list), f"delegation {item.get('delegation_id')} allowed_actions invalid")
    return not bool(set(allowed).intersection(_reserved_actions_encountered_by(item, target)))


def _require_reservation_boundary_compliance(item: dict) -> None:
    allowed = item.get("allowed_actions")
    core.require(isinstance(allowed, list), f"delegation {item.get('delegation_id')} allowed_actions invalid")
    allowed_set = set(allowed)
    start = core.parse_iso_date(
        item.get("effective_date"),
        f"delegation {item.get('delegation_id')} effective_date",
    )

    # If the grant becomes effective while an action is already reserved, it
    # must not supply authority at its own start boundary. The historical
    # creation-policy validator should reject this independently; retaining the
    # check here keeps the prospective layer fail-closed as well.
    start_conflict = sorted(allowed_set.intersection(_reserved_actions_as_of(start)))
    if start_conflict and ORIG_DELEGATION_ACTIVE_ON(item, start):
        core.require(
            False,
            f"delegation {item.get('delegation_id')} is active while its effective-date policy already reserves allowed action(s): {', '.join(start_conflict)}",
        )

    # Check every later release boundary, not only the latest one. A revocation
    # after R2 cannot cure authority that remained live when R2 first reserved
    # the action, and R3 removing the reservation cannot resurrect the old grant.
    for effective, reserved in _DELEGATION_POLICY_TIMELINE:
        if effective <= start:
            continue
        conflict = sorted(allowed_set.intersection(reserved))
        if not conflict:
            continue
        core.require(
            not ORIG_DELEGATION_ACTIVE_ON(item, effective),
            f"delegation {item.get('delegation_id')} remained active at the first applicable policy boundary {effective.isoformat()} reserving allowed action(s): {', '.join(conflict)}; revoke it no later than that boundary",
        )


def validate_delegations(delegations: dict, status: dict, rules: dict, membership: dict):
    _build_delegation_policy_timeline(status)
    validated = ORIG_VALIDATE_DELEGATIONS(delegations, status, rules, membership)
    if status.get("operative") is not True:
        return validated

    core.require(
        bool(_DELEGATION_POLICY_TIMELINE),
        "operative governance requires release chain for prospective delegation constraints",
    )
    for item in validated:
        _require_reservation_boundary_compliance(item)
    return validated


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    delegation_lifecycle.validate_delegations = validate_delegations
    delegation_lifecycle.delegation_active_on = delegation_active_on
    _INSTALLED = True
