#!/usr/bin/env python3
"""Focused guards for inter-release membership, delegation and chronology invariants."""

from __future__ import annotations

import copy

import governance_interrelease_integrity as interrelease
import validate_governance as core


def expect_failure(label: str, callback) -> None:
    try:
        callback()
    except SystemExit:
        return
    raise SystemExit(f"inter-release integrity guard failure: {label} unexpectedly validated")


def _membership() -> dict:
    return {
        "members": [
            {
                "record_id": "member-a",
                "person_id": "person-a",
                "admission_mode": "member-ordinary-approval",
                "candidate_since": "2026-01-01",
                "active_since": "2026-02-01",
                "admission_record": {"path": "records/decisions/admission-a.json", "sha256": "a" * 64},
                "state_transition_records": [
                    {"path": "records/decisions/transition-a.json", "sha256": "b" * 64}
                ],
            }
        ]
    }


def validate_membership_record_closure_guards() -> int:
    membership = _membership()
    admissions = [("person-a", membership["members"][0]["admission_record"])]
    transitions = [("person-a", membership["members"][0]["state_transition_records"][0])]
    interrelease._validate_membership_record_closure_sets(
        membership,
        admissions,
        transitions,
        "synthetic membership closure",
    )

    pruned = {"members": []}
    expect_failure(
        "orphan admission cannot disappear between release checkpoints",
        lambda: interrelease._validate_membership_record_closure_sets(
            pruned,
            admissions,
            transitions,
            "pruned membership closure",
        ),
    )

    missing_transition = _membership()
    missing_transition["members"][0]["state_transition_records"] = []
    expect_failure(
        "adopted transition cannot become unreferenced",
        lambda: interrelease._validate_membership_record_closure_sets(
            missing_transition,
            admissions,
            transitions,
            "missing transition closure",
        ),
    )
    return 3


def _delegation_snapshot() -> tuple[dict, dict]:
    adoption = {"release_sequence": 2, "governance_version": "EC-GOV-2.0"}
    snapshot = {
        "record_type": "governance-delegation-policy-snapshot",
        "status": "final",
        "release_sequence": 2,
        "governance_version": "EC-GOV-2.0",
        "source_authority_contract": {
            "type": "governance-decision",
            "required_fields": ["type", "decision_id", "constitutional_basis"],
            "constitutional_basis": core.RESERVED_CONSTITUTIONAL_BASIS,
        },
        "scope_vocabulary": sorted(interrelease.BASELINE_DELEGATION_SCOPES),
        "reserved_non_delegable_actions": sorted(interrelease.BASELINE_RESERVED_ACTIONS),
    }
    return adoption, snapshot


def validate_delegation_policy_snapshot_guards() -> int:
    adoption, snapshot = _delegation_snapshot()
    interrelease._validate_delegation_policy_snapshot_data(snapshot, adoption, "synthetic delegation snapshot")

    weakened = copy.deepcopy(snapshot)
    weakened["reserved_non_delegable_actions"].remove("constitutional-amendment")
    expect_failure(
        "historical release cannot weaken reserved delegation actions",
        lambda: interrelease._validate_delegation_policy_snapshot_data(
            weakened,
            adoption,
            "weakened reserved actions",
        ),
    )

    weakened = copy.deepcopy(snapshot)
    weakened["scope_vocabulary"].remove("repository")
    expect_failure(
        "historical release cannot lose baseline delegation scopes",
        lambda: interrelease._validate_delegation_policy_snapshot_data(
            weakened,
            adoption,
            "weakened delegation vocabulary",
        ),
    )
    return 3


def validate_strict_amendment_chronology_guards() -> int:
    valid = {
        "release_sequence": 2,
        "decision_date": "2026-06-01",
        "completed_date": "2026-06-01",
        "effective_date": "2026-06-02",
    }
    approval = {"decision_date": "2026-06-01"}
    interrelease._require_adoption_chronology(valid, approval, "valid amendment chronology")

    same_day = dict(valid)
    same_day["effective_date"] = "2026-06-01"
    expect_failure(
        "amendment cannot become effective on its completion day",
        lambda: interrelease._require_adoption_chronology(
            same_day,
            approval,
            "same-day amendment chronology",
        ),
    )
    return 2


def validate_repository_membership_extension_guards() -> int:
    previous = _membership()
    appended = _membership()
    appended["members"][0]["state_transition_records"].append(
        {"path": "records/decisions/transition-b.json", "sha256": "c" * 64}
    )
    interrelease._validate_membership_registry_extension(previous, appended)

    pruned = {"members": []}
    expect_failure(
        "established Member row cannot be pruned from committed history",
        lambda: interrelease._validate_membership_registry_extension(previous, pruned),
    )

    rewritten = _membership()
    rewritten["members"][0]["active_since"] = "2026-03-01"
    expect_failure(
        "established admission epoch cannot be rewritten",
        lambda: interrelease._validate_membership_registry_extension(previous, rewritten),
    )
    return 3


def main() -> None:
    total = 0
    total += validate_membership_record_closure_guards()
    total += validate_delegation_policy_snapshot_guards()
    total += validate_strict_amendment_chronology_guards()
    total += validate_repository_membership_extension_guards()
    print(f"Inter-release integrity guards: PASS ({total} cases)")


if __name__ == "__main__":
    main()
