from __future__ import annotations

from datetime import date

import validate_governance as core
import validate_governance_lifecycle as life
import governance_release_history as release_history
import governance_release_authority as release_authority


def phase_timeline(status: dict, phase_evidence: dict) -> list[tuple[date, str]]:
    return release_history.phase_timeline(status, phase_evidence)


def phase_as_of(status: dict, phase_evidence: dict, target: date) -> str | None:
    result = None
    for effective, phase in phase_timeline(status, phase_evidence):
        if target < effective:
            break
        result = phase
    return result


def _authority_for_date(status: dict, membership: dict, target: date):
    authority_status, authority_rules, _, _ = release_authority.authority_context_as_of(status, target)
    authority_membership = release_authority.membership_context_as_of(status, membership, target)
    return authority_status, authority_rules, authority_membership


def validate_member_admission_record(item, membership, status, rules, founding) -> None:
    mode = item.get("admission_mode")
    if status.get("operative") is not True or mode == "constitutive-initial-member":
        life.ORIG_VALIDATE_MEMBER_ADMISSION_RECORD(item, membership, status, rules, founding)
        return

    person_id = item["person_id"]
    record, _ = core.validate_content_ref(item.get("admission_record"), f"member admission {person_id}", "records/decisions")
    decision_date = core.parse_iso_date(record.get("decision_date"), f"member admission {person_id}.decision_date")
    authority_status, authority_rules, authority_membership = _authority_for_date(status, membership, decision_date)

    # The immutable admission is validated under the governance release that
    # was actually in force when the admission decision was made. Current
    # releases may change policy prospectively but may not rewrite history.
    life.ORIG_VALIDATE_MEMBER_ADMISSION_RECORD(
        item,
        authority_membership,
        authority_status,
        authority_rules,
        founding,
    )

    actual = phase_as_of(status, core.load_json("policy/phase-evidence.json"), decision_date)
    core.require(actual is not None, f"member admission {person_id} predates operative governance")
    core.require(record.get("institutional_phase_at_decision") == actual, f"member admission {person_id} phase label does not match historical phase")
    expected_mode = "f0-founding-steward-admission" if actual == "F0-founder-led-bootstrap" else "member-ordinary-approval"
    core.require(mode == expected_mode, f"member admission {person_id} uses authority unavailable in historical phase")


def validate_state_transition_history(item, membership, status, rules, founding) -> str:
    person_id = item["person_id"]
    current_state = "active"
    previous_effective = core.parse_iso_date(item.get("active_since"), f"member {person_id}.active_since")
    seen = set()
    phase_evidence = core.load_json("policy/phase-evidence.json")
    for index, ref in enumerate(life.transition_records(item)):
        data = life.load_transition(ref, person_id, index)
        decision_id = data.get("decision_id")
        core.require(isinstance(decision_id, str) and decision_id and decision_id not in seen, f"member {person_id} transition decision_id invalid/duplicate")
        seen.add(decision_id)
        decision_date_text = data.get("decision_date")
        decision_date = core.parse_iso_date(decision_date_text, f"member {person_id} transition {index}.decision_date")
        effective = core.parse_iso_date(data.get("effective_date"), f"member {person_id} transition {index}.effective_date")
        authority_status, authority_rules, authority_membership = _authority_for_date(status, membership, decision_date)
        event_version = authority_status["governance_version"]
        core.require(data.get("governance_version") == event_version, f"member {person_id} transition must retain the governance version operative on its decision date")
        core.require(effective >= previous_effective and decision_date <= effective, f"member {person_id} transition chronology invalid")
        core.require(data.get("from_state") == current_state, f"member {person_id} transition from_state mismatch")
        to_state = data.get("to_state")
        core.require(to_state in {"active", "inactive", "suspended", "former"}, f"member {person_id} transition to_state invalid")
        transition_type = data.get("transition_type")
        core.require(isinstance(data.get("reason"), str) and data["reason"].strip(), f"member {person_id} transition reason required")
        actual = phase_as_of(status, phase_evidence, decision_date)
        core.require(actual is not None, f"member {person_id} transition predates governance")
        core.require(data.get("institutional_phase_at_decision") == actual, f"member {person_id} transition phase label does not match historical phase")
        payload = {k: v for k, v in data.items() if k not in {"approval_evidence", "signature_evidence", "process_evidence", "transition_payload_sha256"}}
        payload_hash = core.sha256_json(payload)
        core.require(data.get("transition_payload_sha256") == payload_hash, f"member {person_id} transition payload hash mismatch")

        if transition_type == "resignation":
            core.require(current_state in {"active", "inactive", "suspended"} and to_state == "former", f"member {person_id} resignation state invalid")
            core.validate_signature_ref(data.get("signature_evidence"), f"member {person_id} resignation signature", person_id, decision_id, payload_hash, "membership-state-transition", event_version, event_version)
        elif transition_type in {"inactivity", "suspension", "reactivation"}:
            expected_to = {"inactivity": "inactive", "suspension": "suspended", "reactivation": "active"}[transition_type]
            core.require(to_state == expected_to, f"member {person_id} {transition_type} target invalid")
            if transition_type == "reactivation":
                core.require(current_state in {"inactive", "suspended"}, f"member {person_id} reactivation source invalid")
            else:
                core.require(current_state in {"active", "inactive"}, f"member {person_id} {transition_type} source invalid")
            process = core.validate_process_evidence_ref(data.get("process_evidence"), f"member {person_id} {transition_type} process", f"membership-{transition_type}-process-evidence", event_version, f"membership-{transition_type}:{person_id}")
            core.require(process.get("decision_id") == decision_id, f"member {person_id} {transition_type} process decision mismatch")
            core.require(process.get("transition_payload_sha256") == payload_hash, f"member {person_id} {transition_type} process payload mismatch")
            core.require(process.get("decision_date") == decision_date_text and process.get("effective_date") == data.get("effective_date"), f"member {person_id} {transition_type} process chronology binding mismatch")
            core.require(process.get("from_state") == current_state and process.get("to_state") == to_state, f"member {person_id} {transition_type} process state binding mismatch")
            core.require(process.get("reason") == data.get("reason"), f"member {person_id} {transition_type} process reason mismatch")
        elif transition_type == "termination":
            core.require(to_state == "former", f"member {person_id} termination must end membership")
            if actual == "F0-founder-led-bootstrap":
                founder_id = founding["founding_steward"]["person_id"]
                core.validate_signature_ref(data.get("signature_evidence"), f"member {person_id} F0 termination signature", founder_id, decision_id, payload_hash, "membership-state-transition", event_version, event_version)
            else:
                core.require(data.get("decision_class") == "qualified-approval", f"member {person_id} F1+ termination requires Qualified Approval")
                approval, _ = core.validate_content_ref(data.get("approval_evidence"), f"member {person_id} termination approval envelope", "records/evidence")
                opened = core.parse_iso_date(approval.get("voting_window_open_date"), f"member {person_id} termination voting_window_open_date")
                core.require(effective > opened, f"member {person_id} approval-backed termination must become effective after its frozen electorate snapshot")
                core.validate_approval_evidence(
                    data.get("approval_evidence"),
                    f"member {person_id} termination approval",
                    decision_id,
                    status,
                    authority_rules,
                    authority_membership,
                    expected_rule_id="qualified-approval",
                    expected_artifact_bindings={"transition_payload_sha256": payload_hash},
                    expected_decision_date=decision_date_text,
                )
        else:
            raise SystemExit(f"governance integrity failure: member {person_id} unsupported transition_type: {transition_type}")
        current_state = to_state
        previous_effective = effective
    return current_state


def _validate_phase_transition_record(ref, status, phase_evidence, membership, expected_to: str) -> dict:
    record, _ = core.validate_content_ref(ref, f"historical transition to {expected_to}", "records/decisions")
    core.require(record.get("record_type") == "phase-transition" and record.get("status") == "adopted", "phase transition record invalid")
    core.require(record.get("to_phase") == expected_to, "phase transition target mismatch")
    decision_id = record.get("decision_id")
    decision_date_text = record.get("decision_date")
    decision_date = core.parse_iso_date(decision_date_text, "phase transition decision_date")
    effective = core.parse_iso_date(record.get("effective_date"), "phase transition effective_date")
    authority_status, authority_rules, authority_membership = _authority_for_date(status, membership, decision_date)
    event_version = authority_status["governance_version"]
    core.require(record.get("governance_version") == event_version, "phase transition must retain governance version operative on decision date")
    core.require(release_history.governance_version_as_of(status, effective) == event_version, "phase transition cannot cross a governance release boundary")
    core.require(decision_date <= effective, "phase transition decision cannot postdate phase effective date")
    core.require(record.get("decision_class") == "qualified-approval", "F1/F2 phase transition must use Qualified Approval")
    expected_from = {"F1-early-institution": "F0-founder-led-bootstrap", "F2-distributed-institution": "F1-early-institution"}
    core.require(record.get("from_phase") == expected_from[expected_to], "phase transition source mismatch")
    payload = {k: v for k, v in record.items() if k not in {"approval_evidence", "transition_payload_sha256"}}
    payload_hash = core.sha256_json(payload)
    core.require(record.get("transition_payload_sha256") == payload_hash, "phase transition payload hash mismatch")
    core.validate_approval_evidence(
        record.get("approval_evidence"),
        f"{expected_to} phase transition approval",
        decision_id,
        status,
        authority_rules,
        authority_membership,
        expected_rule_id="qualified-approval",
        expected_artifact_bindings={"transition_payload_sha256": payload_hash},
        expected_decision_date=decision_date_text,
    )
    return record


def validate_f1_maturity_as_of(status, phase_evidence, founding, membership, operative_delegations, f1_effective: date) -> None:
    f1 = phase_evidence["f1"]
    active = life.active_members_on(membership, f1_effective)
    core.require(len(active) >= f1["minimum_active_members"], "prior F0→F1 transition lacked minimum Active Members")
    active_delegations = [d for d in operative_delegations if core.delegation_active_on(d, f1_effective)]
    founder = founding["founding_steward"]["person_id"]
    core.require(any(d["holder_person_id"] != founder for d in active_delegations), "prior F0→F1 transition lacked independent role holder")
    scopes = {scope for d in active_delegations for scope in d["scope_types"]}
    core.require(core.CRITICAL_DELEGATION_SCOPES.issubset(scopes), "prior F0→F1 transition lacked effective critical delegations")
    version = release_history.governance_version_as_of(status, f1_effective)
    independent = core.validate_process_evidence_ref(f1["independent_role_holder_evidence"], "historical F1 independent role evidence", "independent-role-holder-evidence", version, "f1-independent-role-holder")
    delegation = core.validate_process_evidence_ref(f1["delegation_evidence"], "historical F1 delegation evidence", "delegation-coverage-evidence", version, "f1-critical-delegation-coverage")
    as_of = f1_effective.isoformat()
    core.require(independent.get("as_of_date") == as_of and delegation.get("as_of_date") == as_of, "F1 maturity evidence must bind F1 effective date")
    core.require(set(independent.get("active_member_person_ids", [])) == active, "F1 maturity Member snapshot mismatch")
    core.require(set(delegation.get("active_delegation_ids", [])) == {d["delegation_id"] for d in active_delegations}, "F1 maturity delegation snapshot mismatch")


def validate_prior_f1_transition(status, phase_evidence, rules, membership, founding, operative_delegations) -> None:
    if status["operative"] is False or status["institutional_phase"] in {"F0-founder-led-bootstrap", "F1-early-institution"}:
        core.require(phase_evidence.get("prior_transition_decision_record") is None, "F0/F1 cannot claim prior transition")
        return
    prior_ref = phase_evidence.get("prior_transition_decision_record")
    core.require(isinstance(prior_ref, dict), "F2 requires prior F0→F1 transition")
    prior = _validate_phase_transition_record(prior_ref, status, phase_evidence, membership, "F1-early-institution")
    effective = core.parse_iso_date(prior.get("effective_date"), "prior F1 effective_date")
    current, _ = core.validate_content_ref(phase_evidence["transition_decision_record"], "current F2 transition", "records/decisions")
    core.require(effective < core.parse_iso_date(current.get("effective_date"), "current F2 effective_date"), "F2 must follow established F1")
    core.require(current.get("prior_transition_sha256") == prior_ref["sha256"], "F2 transition must bind exact F1 transition")
    validate_f1_maturity_as_of(status, phase_evidence, founding, membership, operative_delegations, effective)


def validate_phase_evidence(status, membership, founding, phase_evidence, operative_delegations, active_members, rules) -> None:
    core.require(phase_evidence["schema_version"] == 2, "unsupported phase-evidence schema")
    core.require(phase_evidence["governance_version"] == status["governance_version"], "phase-evidence projection must identify current governance version")
    core.require(phase_evidence["current_phase"] == status["institutional_phase"], "phase-evidence/current phase mismatch")
    core.require(phase_evidence.get("evidence_reference_contract") == {"type": "content-addressed-json", "required_fields": ["path", "sha256"]}, "phase evidence reference contract mismatch")
    if status["operative"] is False:
        life.ORIG_VALIDATE_PHASE_EVIDENCE(status, membership, founding, phase_evidence, operative_delegations, active_members, rules)
        return

    founding_effective = release_history.founding_effective_date(status)
    operative_since = core.parse_iso_date(phase_evidence["governance_operative_since"], "governance_operative_since")
    phase_date = core.parse_iso_date(phase_evidence["phase_effective_date"], "phase_effective_date")
    core.require(phase_evidence["operative"] is True, "operative governance requires operative phase evidence")
    core.require(operative_since == founding_effective, "governance_operative_since must remain anchored to release #1")
    core.require(phase_date >= founding_effective, "phase effective date cannot predate founding governance")

    f1 = phase_evidence["f1"]
    f2 = phase_evidence["f2"]
    core.require(f1["minimum_active_members"] == founding["phase_transition"]["f1_min_active_members"], "F1 member threshold mismatch")
    core.require(f2["minimum_active_members"] == founding["phase_transition"]["f2_min_active_members"], "F2 member threshold mismatch")
    core.require(f2["minimum_operational_months"] == founding["phase_transition"]["f2_min_operational_months"], "F2 time threshold mismatch")

    phase = status["institutional_phase"]
    if phase == "F0-founder-led-bootstrap":
        core.require(phase_evidence["transition_decision_record"] is None and phase_evidence.get("prior_transition_decision_record") is None, "F0 cannot fabricate phase transitions")
        core.require(phase_date == founding_effective, "operative F0 phase date must remain the founding release effective date")
        return

    current_transition = _validate_phase_transition_record(phase_evidence["transition_decision_record"], status, phase_evidence, membership, phase)
    core.require(current_transition.get("effective_date") == phase_evidence["phase_effective_date"], "current phase transition effective date mismatch")
    historical_active = life.active_members_on(membership, phase_date)
    core.require(len(historical_active) >= f1["minimum_active_members"], "F1/F2 requires minimum distinct Active Members on phase date")
    active_at_phase = [item for item in operative_delegations if core.delegation_active_on(item, phase_date)]
    founder_person = founding["founding_steward"]["person_id"]
    independent_holders = {d["holder_person_id"] for d in active_at_phase if d["holder_person_id"] != founder_person}
    core.require(independent_holders, "F1/F2 requires independent delegated role holder effective on phase date")
    phase_version = release_history.governance_version_as_of(status, phase_date)
    core.validate_process_evidence_ref(f1["independent_role_holder_evidence"], "F1 independent role evidence", "independent-role-holder-evidence", phase_version if phase == "F1-early-institution" else release_history.governance_version_as_of(status, core.parse_iso_date(_validate_phase_transition_record(phase_evidence["prior_transition_decision_record"], status, phase_evidence, membership, "F1-early-institution")["effective_date"], "historical F1 effective_date")), "f1-independent-role-holder")
    scopes = {scope for d in active_at_phase for scope in d["scope_types"]}
    core.require(core.CRITICAL_DELEGATION_SCOPES.issubset(scopes), "F1/F2 requires effective, unexpired treasury/domain/repository delegations")

    if phase == "F1-early-institution":
        core.require(phase_evidence.get("prior_transition_decision_record") is None, "F1 cannot claim a prior transition")
        core.validate_process_evidence_ref(f1["delegation_evidence"], "F1 delegation evidence", "delegation-coverage-evidence", phase_version, "f1-critical-delegation-coverage")
        return

    validate_prior_f1_transition(status, phase_evidence, rules, membership, founding, operative_delegations)
    f1_transition, _ = core.validate_content_ref(phase_evidence["prior_transition_decision_record"], "historical F1 transition", "records/decisions")
    f1_date = core.parse_iso_date(f1_transition["effective_date"], "historical F1 effective_date")
    f1_version = release_history.governance_version_as_of(status, f1_date)
    core.validate_process_evidence_ref(f1["delegation_evidence"], "historical F1 delegation evidence", "delegation-coverage-evidence", f1_version, "f1-critical-delegation-coverage")

    core.require(len(historical_active) >= f2["minimum_active_members"], "F2 requires minimum distinct Active Members on phase date")
    core.require(core.elapsed_complete_months(founding_effective, phase_date) >= f2["minimum_operational_months"], "F2 minimum operational months must be measured from founding release")
    by_holder: dict[str, set[str]] = {}
    for delegation in active_at_phase:
        by_holder.setdefault(delegation["holder_person_id"], set()).update(delegation["scope_types"])
    core.require(not any(core.CRITICAL_DELEGATION_SCOPES.issubset(scopes_) for scopes_ in by_holder.values()), "F2 prohibits one person controlling treasury/domain/repository")
    core.require(any("audit-review" in d["scope_types"] and d["holder_person_id"] != founder_person for d in active_at_phase), "F2 requires effective independent audit/review delegation")
    for key, rtype, subject, label in (
        ("control_separation_evidence", "control-separation-evidence", "f2-control-separation", "F2 control separation"),
        ("audit_review_evidence", "audit-review-capacity-evidence", "f2-audit-review-capacity", "F2 audit/review capacity"),
        ("role_replacement_evidence", "role-replacement-evidence", "f2-role-replacement", "F2 role replacement"),
    ):
        core.validate_process_evidence_ref(f2[key], label, rtype, phase_version, subject)
    core.require(
        f2["single_person_cross_domain_control_removed"] is True
        and f2["independent_audit_review_capacity"] is True
        and f2["delegated_role_replacement_demonstrated"] is True,
        "F2 maturity flags must match verified evidence",
    )
