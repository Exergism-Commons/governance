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
import governance_delegation_lifecycle as delegation_lifecycle
import governance_founding_authority as founding_authority
import governance_cla_schedule_binding as cla_schedule_binding


def validate_saved_base_callbacks() -> None:
    callbacks = {
        "member admission": getattr(life, "ORIG_VALIDATE_MEMBER_ADMISSION_RECORD", None),
        "conflict determination": getattr(life, "ORIG_VALIDATE_CONFLICT_DETERMINATION", None),
        "vote approval": getattr(life, "ORIG_VALIDATE_VOTE_APPROVAL", None),
        "adoption record": getattr(life, "ORIG_VALIDATE_ADOPTION_RECORD", None),
        "phase evidence": getattr(life, "ORIG_VALIDATE_PHASE_EVIDENCE", None),
        "CLA status": getattr(life, "ORIG_VALIDATE_CLA_STATUS", None),
    }
    for label, callback in callbacks.items():
        core.require(callable(callback), f"saved base validator missing/not callable: {label}")


def validate_membership_registry(*args, **kwargs):
    membership = args[0]
    evidence.require_voting_window_contract(membership)
    return life.validate_membership_registry_lifecycle(*args, **kwargs)


def main() -> None:
    validate_saved_base_callbacks()
    # Schedule/projection consistency is checked even in the current draft state,
    # so CI exercises this integrity surface before CLA activation.
    cla_schedule_binding.validate_schedule_projection_manifest()

    life.validate_state_transition_history = phase.validate_state_transition_history
    life.validate_member_admission_record_historical = phase.validate_member_admission_record
    life.validate_mission_guardian_assignment = roles.validate_mission_guardian_assignment
    life.validate_cla_steward_authority = roles.validate_cla_steward_authority

    core.active_members_as_of = life.historical_active_members_as_of
    core.validate_member_admission_record = founding_authority.validate_member_admission_record
    core.validate_conflict_determination = evidence.validate_conflict_determination
    core.validate_vote_approval = evidence.validate_vote_approval
    core.validate_membership_registry = validate_membership_registry
    core.validate_delegations = delegation_lifecycle.validate_delegations
    core.delegation_active_on = delegation_lifecycle.delegation_active_on
    core.validate_adoption_record = life.validate_adoption_record_historical
    core.validate_phase_evidence = phase.validate_phase_evidence
    core.validate_covered_projects = cla_schedule_binding.validate_covered_projects
    core.validate_cla_status = roles.validate_cla_status

    core.main()

    status = core.load_json("policy/governance-status.json")
    rules = core.load_json("policy/decision-rules.json")
    membership = core.load_json("policy/membership-status.json")
    founding = core.load_json("policy/founding-stewardship.json")
    phase_evidence = core.load_json("policy/phase-evidence.json")
    founding_authority.validate_f0_signed_membership_actions(status, founding, rules, membership)
    roles.validate_mission_guardian_assignment(status, founding, rules, membership, phase_evidence)
    print("Exergism Commons temporal authority integrity: PASS")


if __name__ == "__main__":
    main()
