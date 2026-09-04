#!/usr/bin/env python3
"""Final temporal authority validator for Exergism Commons governance."""

import validate_governance as core
import validate_governance_lifecycle as life

# Capture every base callback before importing/installing temporal wrappers.
# Operative-only branches rely on these saved implementations; the bootstrap
# snapshot must still prove that the callback chain is complete.
life.ORIG_VALIDATE_MEMBER_ADMISSION_RECORD = core.validate_member_admission_record
life.ORIG_VALIDATE_CONFLICT_DETERMINATION = core.validate_conflict_determination
life.ORIG_VALIDATE_VOTE_APPROVAL = core.validate_vote_approval

import governance_temporal_phase as phase
import governance_temporal_evidence as evidence
import governance_temporal_roles as roles
import governance_cla_review_hardening as cla_review_hardening
import governance_cla_steward_history as cla_steward_history
import governance_founding_lifecycle as founding_lifecycle
import governance_delegation_lifecycle as delegation_lifecycle
import governance_founding_authority as founding_authority
import governance_cla_schedule_binding as cla_schedule_binding
import governance_phase_maturity_chronology as maturity_chronology
import governance_adoption_chronology as adoption_chronology
import governance_strict_json as strict_json
import governance_strict_yaml as strict_yaml
import governance_signature_chronology as signature_chronology
import governance_membership_process_chronology as process_chronology
import governance_voting_window_authenticity as voting_window_authenticity
import governance_ballot_proposal_binding as ballot_binding
import governance_release_lifecycle as release_lifecycle
import governance_release_history as release_history
import governance_release_membership as release_membership
import governance_guardian_consent as guardian_consent
import governance_release_authority as release_authority
import governance_release_evidence_hardening as release_evidence_hardening
import governance_release_proof as release_proof
import governance_succession_auth as succession_auth
import governance_open_knowledge as open_knowledge

# Preserve the true pre-release base callback before redirecting historical
# constitutive Member validation through the release #1 anchor.
release_membership.BASE_VALIDATE_MEMBER_ADMISSION_RECORD = life.ORIG_VALIDATE_MEMBER_ADMISSION_RECORD
life.ORIG_VALIDATE_MEMBER_ADMISSION_RECORD = release_membership.validate_member_admission_record


def validate_saved_base_callbacks() -> None:
    callbacks = {
        "member admission": getattr(release_membership, "BASE_VALIDATE_MEMBER_ADMISSION_RECORD", None),
        "release-aware member admission": getattr(life, "ORIG_VALIDATE_MEMBER_ADMISSION_RECORD", None),
        "conflict determination": getattr(life, "ORIG_VALIDATE_CONFLICT_DETERMINATION", None),
        "vote approval": getattr(life, "ORIG_VALIDATE_VOTE_APPROVAL", None),
        "adoption record": getattr(life, "ORIG_VALIDATE_ADOPTION_RECORD", None),
        "phase evidence": getattr(life, "ORIG_VALIDATE_PHASE_EVIDENCE", None),
        "CLA status": getattr(life, "ORIG_VALIDATE_CLA_STATUS", None),
        "CLA reviewer binding": getattr(cla_review_hardening, "validate_cla_status", None),
        "historical CLA Steward authority": getattr(cla_steward_history, "validate_cla_steward_authority", None),
        "release approval evidence": getattr(release_lifecycle, "ORIG_VALIDATE_APPROVAL_EVIDENCE", None),
        "release adoption authority": getattr(release_authority, "ORIG_VALIDATE_ADOPTION_RECORD", None),
        "release classification authority": getattr(release_authority, "ORIG_VALIDATE_CLASSIFICATION", None),
        "release activation semantics": getattr(release_evidence_hardening, "validate_authority_snapshot", None),
        "review-bound amendment classification": getattr(release_evidence_hardening, "validate_classification_base", None),
        "release guardian consent": getattr(guardian_consent, "validate_guardian_consent", None),
        "founding succession lifecycle": getattr(succession_auth, "ORIG_VALIDATE_FOUNDING_STEWARD_LIFECYCLE", None),
        "guardian succession assignment": getattr(succession_auth, "ORIG_VALIDATE_MISSION_GUARDIAN_ASSIGNMENT", None),
    }
    for label, callback in callbacks.items():
        core.require(callable(callback), f"saved base validator missing/not callable: {label}")


def validate_membership_registry(*args, **kwargs):
    membership = args[0]
    evidence.require_voting_window_contract(membership)
    ballot_binding.require_ballot_proposal_binding_contract(membership)
    return life.validate_membership_registry_lifecycle(*args, **kwargs)


def main() -> None:
    # JSON ambiguity is a parser-level authority bug, so duplicate-name
    # rejection must be installed before *any* repository/record/embedded JSON
    # is decoded by the canonical verdict.
    strict_json.install()
    validate_saved_base_callbacks()
    strict_yaml.install()
    signature_chronology.install()

    # Historical release snapshots are authority only after their activation
    # records have passed the same semantic/type/result/chronology checks as a
    # current release. Qualified reviews and amendment classifications also use
    # one shared signed-review payload contract that includes reviewer identity
    # and exact qualification-evidence references.
    release_evidence_hardening.install()

    cla_schedule_binding.validate_schedule_projection_manifest()

    life.validate_state_transition_history = process_chronology.validate_state_transition_history
    life.validate_member_admission_record_historical = phase.validate_member_admission_record

    # Release history is a stable authority primitive: the current release can
    # change without moving the constitutive Member/phase epoch forward.
    phase.phase_timeline = release_history.phase_timeline

    # A governance amendment must be authorized by the release already in
    # force, never by the rules/processes it is proposing to replace. The
    # predecessor authority snapshot therefore controls classification,
    # protected votes, ballots and Founding-Period guardian consent.
    release_lifecycle._validate_classification = release_authority.validate_classification
    release_lifecycle._validate_guardian_consent = release_authority.validate_guardian_consent

    # Install authenticated succession before any authority wrapper can use the
    # Founding Steward or Mission Guardian lifecycle.
    founding_lifecycle.validate_founding_steward_lifecycle = succession_auth.validate_founding_steward_lifecycle
    roles.validate_mission_guardian_assignment = succession_auth.validate_mission_guardian_assignment
    life.validate_mission_guardian_assignment = succession_auth.validate_mission_guardian_assignment

    # CLA Steward appointments are historical governance acts. Do not route an
    # old appointment through current release/version state, and do not alias the
    # lifecycle callback back to roles.validate_cla_steward_authority (which
    # would recurse in operative mode). Both consumers use the same release-aware
    # implementation instead.
    roles.validate_cla_steward_authority = cla_steward_history.validate_cla_steward_authority
    life.validate_cla_steward_authority = cla_steward_history.validate_cla_steward_authority

    core.active_members_as_of = life.historical_active_members_as_of
    core.validate_member_admission_record = founding_authority.validate_member_admission_record
    core.validate_conflict_determination = evidence.validate_conflict_determination
    core.validate_vote_approval = voting_window_authenticity.validate_vote_approval
    core.validate_approval_evidence = release_authority.validate_approval_evidence
    core.validate_membership_registry = validate_membership_registry
    core.validate_delegations = delegation_lifecycle.validate_delegations
    core.delegation_active_on = delegation_lifecycle.delegation_active_on
    core.validate_adoption_record = release_authority.validate_adoption_record
    core.validate_phase_evidence = phase.validate_phase_evidence
    core.validate_covered_projects = cla_schedule_binding.validate_covered_projects
    core.validate_cla_status = cla_review_hardening.validate_cla_status

    core.main()

    status = core.load_json("policy/governance-status.json")
    membership = core.load_json("policy/membership-status.json")

    # A structurally contiguous hash chain is not enough. Prove release #1 and
    # then every amendment, in order, under its predecessor's frozen authority
    # before any descendant snapshot is accepted as an authority source.
    release_proof.validate_release_proof_chain(status, membership)

    # Open Knowledge is a constitutional activation dependency, not an optional
    # descriptive sidecar. Its draft/operative state, exact policy bytes,
    # authenticated rights-review binding, anti-enclosure taxonomy and full
    # release-history binding are checked after the core authority chain.
    open_knowledge.validate_open_knowledge()

    rules = core.load_json("policy/decision-rules.json")
    founding = core.load_json("policy/founding-stewardship.json")
    phase_evidence = core.load_json("policy/phase-evidence.json")
    adoption_chronology.validate_governance_adoption_chronology(status)
    maturity_chronology.validate_phase_maturity_chronology(status, phase_evidence)
    founding_authority.validate_f0_signed_membership_actions(status, founding, rules, membership)
    succession_auth.validate_mission_guardian_assignment(status, founding, rules, membership, phase_evidence)
    print("Exergism Commons temporal authority integrity: PASS")


if __name__ == "__main__":
    main()
