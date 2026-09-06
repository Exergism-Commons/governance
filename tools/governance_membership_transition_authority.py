from __future__ import annotations

from datetime import date

import governance_founding_lifecycle as founding_lifecycle
import governance_membership_process_chronology as process_chronology
import governance_release_evidence_hardening as release_hardening
import governance_release_history as release_history
import governance_temporal_phase as phase
import validate_governance as core
import validate_governance_lifecycle as life


TRANSITION_AUTHORITY_FLOORS = {
    "f0_process_transition_authority": "operative-founding-steward-signature",
    "f1_plus_inactivity_authority": "ordinary-approval",
    "f1_plus_reactivation_authority": "ordinary-approval",
    "f1_plus_suspension_authority": "qualified-approval",
    "process_evidence_ref_bound_into_authority": True,
}

ORIG_VALIDATE_STATE_TRANSITION_HISTORY = process_chronology.validate_state_transition_history
ORIG_VALIDATE_HISTORICAL_MEMBERSHIP_SEMANTICS = release_hardening.validate_historical_membership_semantics
_INSTALLED = False


def _require_transition_authority_contract(membership: dict, label: str) -> None:
    contract = membership.get("state_transition_contract")
    core.require(isinstance(contract, dict), f"{label} state_transition_contract missing")
    for key, expected in TRANSITION_AUTHORITY_FLOORS.items():
        core.require(contract.get(key) == expected, f"{label} transition authority weakened: {key}")


def validate_historical_membership_semantics(policy: object, label: str) -> None:
    ORIG_VALIDATE_HISTORICAL_MEMBERSHIP_SEMANTICS(policy, label)
    core.require(isinstance(policy, dict), f"{label} membership policy must be an object")
    _require_transition_authority_contract(policy, label)


def _process_ref_binding(ref: dict) -> str:
    core.require(
        isinstance(ref, dict) and set(ref) == {"path", "sha256"},
        "membership process evidence must be an exact content-addressed reference",
    )
    core.require_sha256(ref.get("sha256"), "membership process evidence sha256")
    return core.sha256_json(ref)


def _process_completed_date(ref: dict, person_id: str, transition_type: str) -> date:
    process, _ = core.validate_content_ref(
        ref,
        f"member {person_id} {transition_type} authority process",
        "records/evidence",
    )
    return core.parse_iso_date(
        process.get("completed_date"),
        f"member {person_id} {transition_type} authority process.completed_date",
    )


def validate_transition_authority(
    transition: dict,
    person_id: str,
    membership: dict,
    status: dict,
    rules: dict,
    founding: dict,
    phase_evidence: dict,
) -> None:
    transition_type = transition.get("transition_type")
    if transition_type not in {"inactivity", "suspension", "reactivation"}:
        return

    _require_transition_authority_contract(membership, "membership policy")
    decision_id = transition.get("decision_id")
    decision_date_text = transition.get("decision_date")
    decision_date = core.parse_iso_date(decision_date_text, f"member {person_id} {transition_type} decision_date")
    effective_date = core.parse_iso_date(transition.get("effective_date"), f"member {person_id} {transition_type} effective_date")
    payload_hash = core.require_sha256(
        transition.get("transition_payload_sha256"),
        f"member {person_id} {transition_type} transition_payload_sha256",
    )
    process_ref = transition.get("process_evidence")
    process_ref_hash = _process_ref_binding(process_ref)
    process_completed = _process_completed_date(process_ref, person_id, transition_type)
    actual_phase = phase.phase_as_of(status, phase_evidence, decision_date)
    core.require(actual_phase is not None, f"member {person_id} {transition_type} predates operative governance")
    event_version = release_history.governance_version_as_of(status, decision_date)

    if actual_phase == "F0-founder-led-bootstrap":
        founder_id = founding.get("founding_steward", {}).get("person_id")
        core.require(isinstance(founder_id, str) and founder_id, "F0 membership transition requires Founding Steward identity")
        authority_payload_hash = core.sha256_json(
            {
                "transition_payload_sha256": payload_hash,
                "process_evidence": process_ref,
            }
        )
        signature = core.validate_signature_ref(
            transition.get("signature_evidence"),
            f"member {person_id} F0 {transition_type} authority signature",
            founder_id,
            decision_id,
            authority_payload_hash,
            "membership-state-process-authority",
            event_version,
            event_version,
        )
        signed_date = core.parse_iso_date(
            signature.get("signed_date"),
            f"member {person_id} F0 {transition_type} authority signature.signed_date",
        )
        core.require(
            process_completed <= signed_date <= decision_date <= effective_date,
            f"member {person_id} F0 {transition_type} authority chronology invalid",
        )
        core.require(
            founding_lifecycle.founding_steward_active_on(status, founding, rules, membership, signed_date)
            and founding_lifecycle.founding_steward_active_on(status, founding, rules, membership, decision_date),
            f"member {person_id} F0 {transition_type} requires then-operative Founding Steward authority",
        )
        core.require(
            transition.get("approval_evidence") is None,
            f"member {person_id} F0 {transition_type} cannot substitute Member approval for Founding Steward process authority",
        )
        return

    expected_rule = "qualified-approval" if transition_type == "suspension" else "ordinary-approval"
    core.require(
        transition.get("decision_class") == expected_rule,
        f"member {person_id} F1+ {transition_type} requires {expected_rule}",
    )
    expected_bindings = {
        "transition_payload_sha256": payload_hash,
        "process_evidence_ref_sha256": process_ref_hash,
    }
    core.validate_approval_evidence(
        transition.get("approval_evidence"),
        f"member {person_id} F1+ {transition_type} approval",
        decision_id,
        status,
        rules,
        membership,
        expected_rule_id=expected_rule,
        expected_artifact_bindings=expected_bindings,
        expected_decision_date=decision_date_text,
    )

    # A removal from voting state cannot alter the frozen electorate that is
    # authorizing that same removal.  Requiring effectiveness after window-open
    # keeps the subject in the denominator until the authorizing vote exists.
    if transition_type in {"inactivity", "suspension"}:
        approval, _ = core.validate_content_ref(
            transition.get("approval_evidence"),
            f"member {person_id} {transition_type} approval envelope",
            "records/evidence",
        )
        opened = core.parse_iso_date(
            approval.get("voting_window_open_date"),
            f"member {person_id} {transition_type} voting_window_open_date",
        )
        core.require(
            effective_date > opened,
            f"member {person_id} {transition_type} must become effective after its frozen electorate snapshot",
        )


def validate_state_transition_history(item, membership, status, rules, founding) -> str:
    result = ORIG_VALIDATE_STATE_TRANSITION_HISTORY(item, membership, status, rules, founding)
    if status.get("operative") is not True:
        return result

    _require_transition_authority_contract(membership, "operative membership policy")
    person_id = item["person_id"]
    phase_evidence = core.load_json("policy/phase-evidence.json")
    for index, ref in enumerate(life.transition_records(item)):
        transition = life.load_transition(ref, person_id, index)
        validate_transition_authority(
            transition,
            person_id,
            membership,
            status,
            rules,
            founding,
            phase_evidence,
        )
    return result


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    process_chronology.validate_state_transition_history = validate_state_transition_history
    release_hardening.validate_historical_membership_semantics = validate_historical_membership_semantics
    _INSTALLED = True
