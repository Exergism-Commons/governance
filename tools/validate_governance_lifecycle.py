#!/usr/bin/env python3
"""Lifecycle/authority hardening layer for Exergism Commons governance validation.

This module patches the base validator with historical Membership semantics and then
adds checks whose purpose is to prevent authority from being created or removed by
mutable state edits alone.
"""
from __future__ import annotations

import copy
from datetime import date

import validate_governance as core


ORIG_VALIDATE_ADOPTION_RECORD = core.validate_adoption_record
ORIG_VALIDATE_PHASE_EVIDENCE = core.validate_phase_evidence
ORIG_VALIDATE_CLA_STATUS = core.validate_cla_status


def transition_records(item: dict) -> list[dict]:
    refs = item.get("state_transition_records")
    core.require(isinstance(refs, list), f"member {item.get('person_id')} state_transition_records must be a list")
    return refs


def load_transition(ref, person_id: str, index: int) -> dict:
    data, _ = core.validate_content_ref(ref, f"member {person_id} state transition {index}", "records/decisions")
    core.require(data.get("record_type") == "membership-state-transition", f"member {person_id} transition record_type mismatch")
    core.require(data.get("status") == "adopted", f"member {person_id} transition must be adopted")
    core.require(data.get("person_id") == person_id, f"member {person_id} transition identity mismatch")
    return data


def historical_state_as_of(item: dict, target: date) -> str | None:
    active_since_text = item.get("active_since")
    if active_since_text is None:
        return None
    active_since = core.parse_iso_date(active_since_text, f"member {item['person_id']}.active_since")
    if target < active_since:
        return None
    state = "active"
    for index, ref in enumerate(transition_records(item)):
        data = load_transition(ref, item["person_id"], index)
        effective = core.parse_iso_date(data.get("effective_date"), f"member {item['person_id']} transition {index}.effective_date")
        if effective > target:
            break
        core.require(data.get("from_state") == state, f"member {item['person_id']} historical transition chain broken")
        state = data.get("to_state")
    return state


def historical_active_members_as_of(membership: dict, decision_date: date, rule_id: str) -> set[str]:
    seasoning = membership["voting_seasoning_days"][rule_id]
    result: set[str] = set()
    for person_id, item in core.member_index(membership).items():
        if historical_state_as_of(item, decision_date) != "active":
            continue
        active_since = core.parse_iso_date(item.get("active_since"), f"member {person_id}.active_since")
        if (decision_date - active_since).days >= seasoning:
            result.add(person_id)
    return result


def active_members_on(membership: dict, target: date) -> set[str]:
    result: set[str] = set()
    for person_id, item in core.member_index(membership).items():
        if historical_state_as_of(item, target) == "active":
            result.add(person_id)
    return result


def validate_state_transition_history(item: dict, membership: dict, status: dict, rules: dict, founding: dict) -> str:
    person_id = item["person_id"]
    active_since = core.parse_iso_date(item.get("active_since"), f"member {person_id}.active_since")
    current_state = "active"
    previous_effective = active_since
    seen_decisions: set[str] = set()

    for index, ref in enumerate(transition_records(item)):
        data = load_transition(ref, person_id, index)
        core.require(data.get("governance_version") == status["governance_version"], f"member {person_id} transition version mismatch")
        decision_id = data.get("decision_id")
        core.require(isinstance(decision_id, str) and decision_id and decision_id not in seen_decisions, f"member {person_id} transition decision_id invalid/duplicate")
        seen_decisions.add(decision_id)
        decision_date_text = data.get("decision_date")
        decision_date = core.parse_iso_date(decision_date_text, f"member {person_id} transition {index}.decision_date")
        effective = core.parse_iso_date(data.get("effective_date"), f"member {person_id} transition {index}.effective_date")
        core.require(effective >= previous_effective, f"member {person_id} transition chronology invalid")
        core.require(decision_date <= effective, f"member {person_id} transition decision postdates effective date")
        core.require(data.get("from_state") == current_state, f"member {person_id} transition from_state mismatch")
        to_state = data.get("to_state")
        core.require(to_state in {"active", "inactive", "suspended", "former"}, f"member {person_id} transition to_state invalid")
        transition_type = data.get("transition_type")
        core.require(isinstance(data.get("reason"), str) and data["reason"].strip(), f"member {person_id} transition reason required")
        phase = data.get("institutional_phase_at_decision")
        core.require(phase in {"F0-founder-led-bootstrap", "F1-early-institution", "F2-distributed-institution"}, f"member {person_id} transition phase invalid")

        payload = {
            k: v
            for k, v in data.items()
            if k not in {"approval_evidence", "signature_evidence", "process_evidence", "transition_payload_sha256"}
        }
        payload_hash = core.sha256_json(payload)
        core.require(data.get("transition_payload_sha256") == payload_hash, f"member {person_id} transition payload hash mismatch")

        if transition_type == "resignation":
            core.require(current_state in {"active", "inactive", "suspended"} and to_state == "former", f"member {person_id} resignation state invalid")
            core.validate_signature_ref(
                data.get("signature_evidence"),
                f"member {person_id} resignation signature",
                person_id,
                decision_id,
                payload_hash,
                "membership-state-transition",
                status["governance_version"],
                status["governance_version"],
            )
        elif transition_type in {"inactivity", "suspension", "reactivation"}:
            expected_to = {"inactivity": "inactive", "suspension": "suspended", "reactivation": "active"}[transition_type]
            core.require(to_state == expected_to, f"member {person_id} {transition_type} target state invalid")
            if transition_type == "reactivation":
                core.require(current_state in {"inactive", "suspended"}, f"member {person_id} reactivation source state invalid")
            else:
                core.require(current_state in {"active", "inactive"}, f"member {person_id} {transition_type} source state invalid")
            core.validate_process_evidence_ref(
                data.get("process_evidence"),
                f"member {person_id} {transition_type} process",
                f"membership-{transition_type}-process-evidence",
                status["governance_version"],
                f"membership-{transition_type}:{person_id}",
            )
        elif transition_type == "termination":
            core.require(to_state == "former", f"member {person_id} termination must end membership")
            if phase == "F0-founder-led-bootstrap":
                founder_id = founding["founding_steward"]["person_id"]
                core.validate_signature_ref(
                    data.get("signature_evidence"),
                    f"member {person_id} F0 termination signature",
                    founder_id,
                    decision_id,
                    payload_hash,
                    "membership-state-transition",
                    status["governance_version"],
                    status["governance_version"],
                )
            else:
                core.require(data.get("decision_class") == "qualified-approval", f"member {person_id} F1+ termination requires Qualified Approval")
                core.validate_approval_evidence(
                    data.get("approval_evidence"),
                    f"member {person_id} termination approval",
                    decision_id,
                    status,
                    rules,
                    membership,
                    expected_rule_id="qualified-approval",
                    expected_artifact_bindings={"transition_payload_sha256": payload_hash},
                    expected_decision_date=decision_date_text,
                )
        else:
            raise SystemExit(f"governance integrity failure: member {person_id} unsupported transition_type: {transition_type}")

        current_state = to_state
        previous_effective = effective

    return current_state


def validate_membership_registry_lifecycle(membership: dict, status: dict, rules: dict, founding: dict) -> tuple[dict[str, dict], set[str]]:
    core.require(membership["schema_version"] == 4, "unsupported membership schema")
    contract = membership.get("state_transition_contract")
    core.require(
        isinstance(contract, dict)
        and contract.get("content_addressed_records_required") is True
        and contract.get("registry_edit_alone_cannot_change_voting_state") is True,
        "membership state-transition authority contract missing/weakened",
    )
    by_person = core.member_index(membership)
    active: set[str] = set()

    for person_id, item in by_person.items():
        refs = transition_records(item)
        if status["operative"] is False:
            core.require(refs == [], f"bootstrap Member {person_id} cannot fabricate state-transition history")
            core.require(item.get("operative_membership") is False, f"bootstrap Member {person_id} cannot be operative")
            core.require(item.get("candidate_since") is None and item.get("active_since") is None and item.get("admission_record") is None, f"bootstrap Member {person_id} cannot fabricate admission history")
            continue

        state = item.get("state")
        if state == "candidate":
            core.require(item.get("operative_membership") is False, f"Candidate {person_id} cannot vote")
            core.parse_iso_date(item.get("candidate_since"), f"Candidate {person_id}.candidate_since")
            core.require(item.get("active_since") is None and item.get("admission_record") is None and refs == [], f"Candidate {person_id} cannot fabricate active/admission history")
            continue

        core.require(item.get("admission_mode") in membership["admission_modes"], f"operative registry row {person_id} lacks valid admission mode")
        core.validate_member_admission_record(item, membership, status, rules, founding)
        derived_state = validate_state_transition_history(item, membership, status, rules, founding)
        core.require(state == derived_state, f"member {person_id} current state does not match validated transition history")
        core.require(item.get("operative_membership") is (derived_state == "active"), f"member {person_id} operative_membership inconsistent with validated state")
        if derived_state == "active":
            active.add(person_id)

    return by_person, active


def validate_adoption_record_historical(status: dict, activation_hashes: dict[str, str], rules: dict, membership: dict, legal_entity: dict | None, human_hashes: dict[str, str]) -> None:
    if status["operative"] is False:
        return ORIG_VALIDATE_ADOPTION_RECORD(status, activation_hashes, rules, membership, legal_entity, human_hashes)

    adjusted = copy.deepcopy(membership)
    for item in adjusted.get("members", []):
        if item.get("admission_mode") == "constitutive-initial-member":
            item["operative_membership"] = True
            item["state"] = "active"
    ORIG_VALIDATE_ADOPTION_RECORD(status, activation_hashes, rules, adjusted, legal_entity, human_hashes)

    record, _ = core.validate_content_ref(status.get("adoption_record"), "governance adoption record", "records/adoptions")
    historical = {
        item["person_id"]
        for item in membership.get("members", [])
        if item.get("admission_mode") == "constitutive-initial-member"
    }
    core.require(set(record.get("initial_member_person_ids", [])) == historical, "adoption initial Member set must match historical constitutive admissions, not current active status")


def validate_prior_f1_transition(status: dict, phase_evidence: dict, rules: dict, membership: dict) -> None:
    phase = status["institutional_phase"]
    prior_ref = phase_evidence.get("prior_transition_decision_record")
    if status["operative"] is False or phase in {"F0-founder-led-bootstrap", "F1-early-institution"}:
        core.require(prior_ref is None, "F0/F1 cannot fabricate a prior phase-transition record")
        return

    core.require(phase == "F2-distributed-institution", "prior transition check only defined for F2")
    core.require(isinstance(prior_ref, dict), "F2 requires content-addressed prior F0→F1 transition")
    prior, _ = core.validate_content_ref(prior_ref, "prior F1 phase transition", "records/decisions")
    core.require(prior.get("record_type") == "phase-transition" and prior.get("status") == "adopted", "prior F1 transition invalid")
    core.require(prior.get("governance_version") == status["governance_version"], "prior F1 transition version mismatch")
    core.require(prior.get("from_phase") == "F0-founder-led-bootstrap" and prior.get("to_phase") == "F1-early-institution", "prior transition must establish F1 from F0")
    core.require(prior.get("decision_class") == "qualified-approval", "prior F1 transition must use Qualified Approval")
    prior_decision_id = prior.get("decision_id")
    prior_decision_date = prior.get("decision_date")
    prior_effective = core.parse_iso_date(prior.get("effective_date"), "prior F1 transition effective_date")
    core.require(core.parse_iso_date(prior_decision_date, "prior F1 transition decision_date") <= prior_effective, "prior F1 transition decision postdates effective date")
    core.require(prior_effective >= core.parse_iso_date(status["effective_date"], "governance effective_date"), "prior F1 transition predates governance")
    current, _ = core.validate_content_ref(phase_evidence["transition_decision_record"], "current F2 phase transition", "records/decisions")
    core.require(prior_effective < core.parse_iso_date(current.get("effective_date"), "current F2 transition effective_date"), "F2 must occur after established F1")
    core.require(current.get("prior_transition_sha256") == prior_ref["sha256"], "F2 transition payload must bind the exact prior F0→F1 transition")
    payload = {k: v for k, v in prior.items() if k not in {"approval_evidence", "transition_payload_sha256"}}
    payload_hash = core.sha256_json(payload)
    core.require(prior.get("transition_payload_sha256") == payload_hash, "prior F1 transition payload hash mismatch")
    core.validate_approval_evidence(
        prior.get("approval_evidence"),
        "prior F1 transition approval",
        prior_decision_id,
        status,
        rules,
        membership,
        expected_rule_id="qualified-approval",
        expected_artifact_bindings={"transition_payload_sha256": payload_hash},
        expected_decision_date=prior_decision_date,
    )


def validate_phase_evidence_lifecycle(status: dict, membership: dict, founding: dict, phase_evidence: dict, operative_delegations: list[dict], active_members: set[str], rules: dict) -> None:
    historical_active = active_members
    if status["operative"] is True and status["institutional_phase"] != "F0-founder-led-bootstrap":
        phase_date = core.parse_iso_date(phase_evidence["phase_effective_date"], "phase_effective_date")
        historical_active = active_members_on(membership, phase_date)
    ORIG_VALIDATE_PHASE_EVIDENCE(status, membership, founding, phase_evidence, operative_delegations, historical_active, rules)
    validate_prior_f1_transition(status, phase_evidence, rules, membership)


def validate_mission_guardian_assignment(status: dict, founding: dict, rules: dict, membership: dict, phase_evidence: dict) -> None:
    guardian = founding.get("mission_guardian")
    core.require(isinstance(guardian, dict), "mission_guardian projection missing")
    active = guardian.get("operative_assignment") is True
    if not active:
        core.require(guardian.get("assignment_record") is None, "inactive Mission Guardian cannot claim assignment record")
        return

    person_id = guardian.get("person_id")
    record_id = guardian.get("record_id")
    core.require(all(isinstance(x, str) and x.strip() for x in (person_id, record_id, guardian.get("display_name"))), "operative Mission Guardian requires identified holder")
    ref = guardian.get("assignment_record")
    record, _ = core.validate_content_ref(ref, "Mission Guardian assignment", "records/decisions")
    core.require(record.get("record_type") == "mission-guardian-assignment" and record.get("status") == "adopted", "Mission Guardian assignment record invalid")
    core.require(record.get("governance_version") == status["governance_version"], "Mission Guardian assignment version mismatch")
    core.require(record.get("guardian_person_id") == person_id and record.get("guardian_record_id") == record_id, "Mission Guardian assignment identity mismatch")
    decision_id = record.get("decision_id")
    decision_date_text = record.get("decision_date")
    effective = core.parse_iso_date(record.get("effective_date"), "Mission Guardian assignment effective_date")
    core.require(core.parse_iso_date(decision_date_text, "Mission Guardian assignment decision_date") <= effective, "Mission Guardian assignment decision postdates effective date")
    if status["institutional_phase"] == "F2-distributed-institution":
        core.require(effective <= core.parse_iso_date(phase_evidence["phase_effective_date"], "phase_effective_date"), "F2 Mission Guardian must be assigned by F2 effective date")

    payload = {k: v for k, v in record.items() if k not in {"approval_evidence", "process_evidence", "assignment_payload_sha256"}}
    payload_hash = core.sha256_json(payload)
    core.require(record.get("assignment_payload_sha256") == payload_hash, "Mission Guardian assignment payload hash mismatch")
    mode = record.get("authority_mode")
    if mode == "qualified-approval":
        core.require(record.get("decision_class") == "qualified-approval", "Mission Guardian appointment decision class mismatch")
        core.validate_approval_evidence(
            record.get("approval_evidence"),
            "Mission Guardian appointment approval",
            decision_id,
            status,
            rules,
            membership,
            expected_rule_id="qualified-approval",
            expected_artifact_bindings={"assignment_payload_sha256": payload_hash},
            expected_decision_date=decision_date_text,
        )
    elif mode == "succession-process":
        core.validate_process_evidence_ref(
            record.get("process_evidence"),
            "Mission Guardian succession evidence",
            "mission-guardian-succession-evidence",
            status["governance_version"],
            f"mission-guardian-assignment:{person_id}",
        )
    else:
        raise SystemExit("governance integrity failure: Mission Guardian authority_mode unsupported")


def validate_cla_steward_authority() -> None:
    status_text = (core.ROOT / "policy/cla-status.yaml").read_text(encoding="utf-8")
    if core.yaml_scalar(status_text, "operative") is not True:
        return

    governance_status = core.load_json("policy/governance-status.json")
    rules = core.load_json("policy/decision-rules.json")
    membership = core.load_json("policy/membership-status.json")
    core.require(governance_status.get("operative") is True, "operative CLA requires operative organization governance")
    legal_steward = core.yaml_scalar(status_text, "legal_steward")
    ref = {
        "path": core.yaml_scalar(status_text, "legal_steward_authority_artifact"),
        "sha256": core.yaml_scalar(status_text, "legal_steward_authority_sha256"),
    }
    record, _ = core.validate_content_ref(ref, "CLA legal Steward authority", "records/decisions")
    identity = record.get("legal_identity")
    core.require(isinstance(identity, dict), "CLA Steward authority requires structured legal_identity")
    core.require(set(identity) == {"legal_name", "legal_form", "jurisdiction", "registration_identity", "relationship_to_exergism_commons", "competent_signatories"}, "CLA Steward legal_identity fields incomplete/unexpected")
    for key in ("legal_name", "legal_form", "jurisdiction", "registration_identity", "relationship_to_exergism_commons"):
        core.require(isinstance(identity[key], str) and identity[key].strip(), f"CLA Steward legal_identity.{key} required")
    signatories = identity["competent_signatories"]
    core.require(isinstance(signatories, list) and signatories and len(signatories) == len(set(signatories)), "CLA Steward competent signatories invalid")
    core.require(record.get("legal_steward") == legal_steward, "CLA Steward stable identifier mismatch")

    identity_evidence = record.get("identity_evidence")
    core.require(isinstance(identity_evidence, list) and identity_evidence, "CLA Steward legal identity requires registration/identity evidence")
    for index, item in enumerate(identity_evidence):
        core.validate_supporting_evidence_ref(item, f"CLA Steward identity evidence {index}", governance_status["governance_version"])

    decision_id = record.get("decision_id")
    decision_date_text = record.get("decision_date")
    core.parse_iso_date(decision_date_text, "CLA Steward authority decision_date")
    core.require(record.get("decision_class") == "qualified-approval", "CLA legal Steward appointment requires Qualified Approval")
    payload = {k: v for k, v in record.items() if k not in {"approval_evidence", "signatory_evidence", "authority_payload_sha256"}}
    payload_hash = core.sha256_json(payload)
    core.require(record.get("authority_payload_sha256") == payload_hash, "CLA Steward authority payload hash mismatch")
    core.validate_approval_evidence(
        record.get("approval_evidence"),
        "CLA legal Steward authority approval",
        decision_id,
        governance_status,
        rules,
        membership,
        expected_rule_id="qualified-approval",
        expected_artifact_bindings={"authority_payload_sha256": payload_hash},
        expected_decision_date=decision_date_text,
    )
    signatures = record.get("signatory_evidence")
    core.require(isinstance(signatures, list) and len(signatures) == len(signatories), "CLA Steward competent-signatory evidence incomplete")
    signed: set[str] = set()
    for index, sig_ref in enumerate(signatures):
        sig, _ = core.validate_content_ref(sig_ref, f"CLA Steward competent signature envelope {index}", "records/evidence")
        signer = sig.get("person_id")
        core.require(signer in signatories and signer not in signed, "CLA Steward competent signature identity mismatch")
        core.validate_signature_ref(
            sig_ref,
            f"CLA Steward competent signature {index}",
            signer,
            decision_id,
            payload_hash,
            "cla-legal-steward-authority",
            governance_status["governance_version"],
            governance_status["governance_version"],
        )
        signed.add(signer)
    core.require(signed == set(signatories), "CLA Steward authority missing competent signature")


def validate_cla_status_lifecycle() -> None:
    ORIG_VALIDATE_CLA_STATUS()
    validate_cla_steward_authority()


def main() -> None:
    core.active_members_as_of = historical_active_members_as_of
    core.validate_membership_registry = validate_membership_registry_lifecycle
    core.validate_adoption_record = validate_adoption_record_historical
    core.validate_phase_evidence = validate_phase_evidence_lifecycle
    core.validate_cla_status = validate_cla_status_lifecycle
    core.main()

    status = core.load_json("policy/governance-status.json")
    rules = core.load_json("policy/decision-rules.json")
    membership = core.load_json("policy/membership-status.json")
    founding = core.load_json("policy/founding-stewardship.json")
    phase_evidence = core.load_json("policy/phase-evidence.json")
    validate_mission_guardian_assignment(status, founding, rules, membership, phase_evidence)
    print("Exergism Commons lifecycle/authority integrity: PASS")


if __name__ == "__main__":
    main()
