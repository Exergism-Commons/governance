#!/usr/bin/env python3
"""Focused guards for historical authority and CLA-adopter integrity classes."""

from __future__ import annotations

import copy
from datetime import date

import governance_activation_origin as activation_origin
import governance_cla_review_hardening as cla_hardening
import governance_membership_roster as membership_roster
import governance_release_authority as authority
import governance_release_evidence_hardening as historical
import governance_release_proof as release_proof
import validate_governance as core


def expect_failure(label: str, callback) -> None:
    try:
        callback()
    except SystemExit:
        return
    raise SystemExit(f"historical authority guard failure: {label} unexpectedly validated")


def _rules() -> dict:
    return core.load_json("policy/decision-rules.json")


def _membership_policy() -> dict:
    membership = core.load_json("policy/membership-status.json")
    return {
        key: copy.deepcopy(membership[key])
        for key in authority.MEMBERSHIP_POLICY_KEYS
    }


def validate_historical_rule_guards() -> int:
    baseline = _rules()
    historical.validate_historical_rule_semantics(baseline, "baseline historical rules")
    cases = 0

    weakened = copy.deepcopy(baseline)
    rule = next(item for item in weakened["rules"] if item["id"] == "constitutional-amendment")
    rule["quorum"] = {
        "type": "fraction_of_effective_eligible",
        "comparison": "at_least",
        "numerator": 1,
        "denominator": 10,
    }
    expect_failure(
        "historical constitutional quorum cannot be weakened",
        lambda: historical.validate_historical_rule_semantics(weakened, "weakened constitutional snapshot"),
    )
    cases += 1

    weakened = copy.deepcopy(baseline)
    rule = next(item for item in weakened["rules"] if item["id"] == "mission-locked-amendment")
    rule["approval"] = {
        "type": "fraction_of_valid_for_against",
        "comparison": "at_least",
        "numerator": 1,
        "denominator": 2,
    }
    expect_failure(
        "historical Mission-Locked approval cannot be weakened",
        lambda: historical.validate_historical_rule_semantics(weakened, "weakened Mission-Lock snapshot"),
    )
    cases += 1

    weakened = copy.deepcopy(baseline)
    rule = next(item for item in weakened["rules"] if item["id"] == "mission-locked-amendment")
    rule["minimum_days_between_successful_votes"] = 1
    expect_failure(
        "historical repeated-vote separation cannot be weakened",
        lambda: historical.validate_historical_rule_semantics(weakened, "weakened separation snapshot"),
    )
    cases += 1

    weakened = copy.deepcopy(baseline)
    weakened["mission_locked_subjects"].remove("permit-enclosure-of-established-ec-public-knowledge")
    expect_failure(
        "historical Mission-Lock taxonomy cannot drop anti-enclosure",
        lambda: historical.validate_historical_rule_semantics(weakened, "weakened Mission-Lock taxonomy"),
    )
    cases += 1

    weakened = copy.deepcopy(baseline)
    weakened["conflict_rules"]["funding_does_not_create_governance_rights"] = False
    expect_failure(
        "historical anti-capture rule cannot let funding create governance rights",
        lambda: historical.validate_historical_rule_semantics(weakened, "weakened anti-capture snapshot"),
    )
    cases += 1

    return cases


def validate_historical_membership_guards() -> int:
    baseline = _membership_policy()
    historical.validate_historical_membership_semantics(baseline, "baseline historical membership")
    cases = 0

    weakened = copy.deepcopy(baseline)
    weakened["candidate_period_days"] = 0
    expect_failure(
        "historical Candidate period cannot be zeroed",
        lambda: historical.validate_historical_membership_semantics(weakened, "zero Candidate period"),
    )
    cases += 1

    for rule_id in (
        "ordinary-approval",
        "qualified-approval",
        "constitutional-amendment",
        "mission-locked-amendment",
    ):
        weakened = copy.deepcopy(baseline)
        weakened["voting_seasoning_days"][rule_id] = 0
        expect_failure(
            f"historical {rule_id} seasoning floor cannot be zeroed",
            lambda m=weakened, rid=rule_id: historical.validate_historical_membership_semantics(m, f"zero {rid} seasoning"),
        )
        cases += 1

    weakened = copy.deepcopy(baseline)
    weakened["voting_window_contract"]["eligibility_fixed_at_window_open"] = False
    expect_failure(
        "historical electorate freeze cannot be disabled",
        lambda: historical.validate_historical_membership_semantics(weakened, "disabled electorate freeze"),
    )
    cases += 1

    weakened = copy.deepcopy(baseline)
    weakened["ballot_proposal_binding_contract"]["artifact_bindings_sha256_in_signed_ballot_payload"] = False
    expect_failure(
        "historical ballots must keep exact proposal binding",
        lambda: historical.validate_historical_membership_semantics(weakened, "disabled proposal binding"),
    )
    cases += 1

    weakened = copy.deepcopy(baseline)
    weakened["admission_modes"]["member-ordinary-approval"]["authority"] = "founding-steward"
    expect_failure(
        "historical F1+ admission authority cannot be downgraded",
        lambda: historical.validate_historical_membership_semantics(weakened, "weakened admission authority"),
    )
    cases += 1

    weakened = copy.deepcopy(baseline)
    weakened["state_transition_contract"]["f1_plus_termination_authority"] = "ordinary-approval"
    expect_failure(
        "historical F1+ termination authority cannot be downgraded",
        lambda: historical.validate_historical_membership_semantics(weakened, "weakened termination authority"),
    )
    cases += 1

    return cases


def validate_historical_separation_semantics() -> int:
    baseline = _rules()
    days = release_proof.historical_mission_vote_separation_days(baseline, "baseline predecessor")
    core.require(days == 60, "baseline predecessor separation should be 60 days")

    stronger = copy.deepcopy(baseline)
    mission = next(item for item in stronger["rules"] if item["id"] == "mission-locked-amendment")
    mission["minimum_days_between_successful_votes"] = 90
    days = release_proof.historical_mission_vote_separation_days(stronger, "stronger predecessor")
    core.require(days == 90, "historical proof must use the predecessor's stronger separation rule")

    weakened = copy.deepcopy(baseline)
    mission = next(item for item in weakened["rules"] if item["id"] == "mission-locked-amendment")
    mission["minimum_days_between_successful_votes"] = 30
    expect_failure(
        "historical vote separation cannot fall below constitutional floor",
        lambda: release_proof.historical_mission_vote_separation_days(weakened, "weakened predecessor"),
    )

    unsupported_count = copy.deepcopy(baseline)
    mission = next(item for item in unsupported_count["rules"] if item["id"] == "mission-locked-amendment")
    mission["successful_votes_required"] = 3
    # A declarative strengthening is not enough if the current release-record
    # schema can authenticate only first+final. Fail closed until the schema has
    # an explicit authenticated vote-sequence representation.
    expect_failure(
        "historical three-vote rule cannot be accepted by a two-vote proof schema",
        lambda: release_proof.historical_mission_vote_separation_days(unsupported_count, "unsupported three-vote predecessor"),
    )
    return 4


def _synthetic_roster_membership() -> dict:
    return {
        "members": [
            {
                "record_id": "member-record-a",
                "person_id": "person-a",
                "admission_mode": "member-ordinary-approval",
                "candidate_since": "2026-01-01",
                "active_since": "2026-02-01",
                "admission_record": {"path": "records/decisions/admission-a.json", "sha256": "a" * 64},
                "state_transition_records": [],
            },
            {
                "record_id": "member-record-b",
                "person_id": "person-b",
                "admission_mode": "member-ordinary-approval",
                "candidate_since": "2026-01-02",
                "active_since": "2026-02-02",
                "admission_record": {"path": "records/decisions/admission-b.json", "sha256": "b" * 64},
                "state_transition_records": [],
            },
        ]
    }


def validate_historical_roster_guards() -> int:
    target = date.fromisoformat("2026-06-01")
    membership = _synthetic_roster_membership()
    frozen = membership_roster.roster_projection_as_of(membership, target, "synthetic release roster")
    membership_roster.validate_roster_members(frozen, membership, target, "synthetic release roster")

    pruned = copy.deepcopy(membership)
    pruned["members"] = [pruned["members"][0]]
    expect_failure(
        "current registry cannot prune a Member frozen into predecessor release roster",
        lambda: membership_roster.validate_roster_members(frozen, pruned, target, "pruned predecessor roster"),
    )

    rewritten = copy.deepcopy(membership)
    rewritten["members"][1]["active_since"] = "2026-05-31"
    expect_failure(
        "current registry cannot rewrite historical admission epoch frozen into predecessor roster",
        lambda: membership_roster.validate_roster_members(frozen, rewritten, target, "rewritten predecessor roster"),
    )
    return 3


def validate_activation_origin_guards() -> int:
    """Keep current-state and historical activation validation on one origin rule."""
    evidence = {
        key: {
            "path": f"records/evidence/{key}.json",
            "sha256": format(index + 1, "x") * 64,
        }
        for index, key in enumerate(historical.ACTIVATION_EVIDENCE_CONTRACT)
    }
    human_hashes = {"CONSTITUTION.md": "a" * 64}
    rules_hash = "b" * 64
    legal_entity = {"legal_name": "Exergism Commons", "evidence": {"path": "ignored", "sha256": "c" * 64}}
    status = {
        "operative": True,
        "governance_version": "EC-GOV-2.0",
        "effective_date": "2026-06-01",
        "governing_law": "synthetic-law",
        "adoption_record": {"path": "records/adoptions/release-2.json", "sha256": "d" * 64},
        "activation_evidence": evidence,
    }
    current_adoption = {
        "governance_version": "EC-GOV-2.0",
        "effective_date": "2026-06-01",
        "artifact_bindings": human_hashes,
        "legal_entity": {"legal_name": "Exergism Commons"},
        "governing_law": "synthetic-law",
        "normative_machine_bindings": {"policy/decision-rules.json": rules_hash},
    }
    current_snapshot = {"activation_evidence": evidence}
    origin_adoption = {"governance_version": "EC-GOV-1.0", "effective_date": "2026-01-01"}
    origin_snapshot = {"governance_version": "EC-GOV-1.0"}

    saved = {
        "load": historical._load_adoption,
        "snapshot": historical._raw_authority_snapshot,
        "origin": historical._activation_origin,
        "validate": historical._validate_activation_at_origin,
    }
    calls: list[tuple[str, str]] = []
    try:
        historical._load_adoption = lambda ref, label: current_adoption
        historical._raw_authority_snapshot = lambda adoption, label: current_snapshot
        historical._activation_origin = lambda adoption, key, ref, label: (origin_adoption, origin_snapshot)
        historical._validate_activation_at_origin = (
            lambda key, ref, origin, snapshot, label: calls.append((key, origin["governance_version"]))
        )

        hashes = activation_origin.validate_activation_evidence(
            status,
            legal_entity,
            human_hashes,
            rules_hash,
        )
        core.require(set(hashes) == set(evidence), "activation-origin guard lost evidence keys")
        core.require(
            len(calls) == len(evidence)
            and all(version == "EC-GOV-1.0" for _, version in calls),
            "current activation gate did not validate inherited records at release of origin",
        )

        mismatched_snapshot = {"activation_evidence": copy.deepcopy(evidence)}
        mismatched_snapshot["activation_evidence"]["conflict_process"] = {
            "path": "records/evidence/decoy.json",
            "sha256": "f" * 64,
        }
        historical._raw_authority_snapshot = lambda adoption, label: mismatched_snapshot
        expect_failure(
            "current status cannot substitute activation evidence outside its authority snapshot",
            lambda: activation_origin.validate_activation_evidence(
                status,
                legal_entity,
                human_hashes,
                rules_hash,
            ),
        )
    finally:
        historical._load_adoption = saved["load"]
        historical._raw_authority_snapshot = saved["snapshot"]
        historical._activation_origin = saved["origin"]
        historical._validate_activation_at_origin = saved["validate"]

    return 2


def validate_cla_adopter_authority_guards() -> int:
    steward = {
        "legal_identity": {
            "competent_signatories": ["steward-signatory-a", "steward-signatory-b"],
        }
    }
    cla_hardening.require_adopters_authorized_by_steward(
        ["steward-signatory-a"],
        steward,
        "synthetic CLA adoption",
    )

    expect_failure(
        "authenticated outsider cannot adopt CLA for Legal Steward",
        lambda: cla_hardening.require_adopters_authorized_by_steward(
            ["outsider-reviewer"],
            steward,
            "synthetic unauthorized CLA adoption",
        ),
    )
    expect_failure(
        "mixed authorized/unauthorized CLA adopter set must fail closed",
        lambda: cla_hardening.require_adopters_authorized_by_steward(
            ["steward-signatory-a", "outsider-reviewer"],
            steward,
            "synthetic mixed CLA adoption",
        ),
    )
    return 3


def main() -> None:
    total = 0
    total += validate_historical_rule_guards()
    total += validate_historical_membership_guards()
    total += validate_historical_separation_semantics()
    total += validate_historical_roster_guards()
    total += validate_activation_origin_guards()
    total += validate_cla_adopter_authority_guards()
    print(f"Historical authority hardening guards: PASS ({total} cases)")


if __name__ == "__main__":
    main()
