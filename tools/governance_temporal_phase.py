from __future__ import annotations

from datetime import date

import validate_governance as core
import validate_governance_lifecycle as life


def phase_timeline(status: dict, phase_evidence: dict) -> list[tuple[date, str]]:
    if status.get("operative") is not True:
        return []
    effective = core.parse_iso_date(status["effective_date"], "governance effective_date")
    timeline = [(effective, "F0-founder-led-bootstrap")]
    phase = status["institutional_phase"]
    if phase == "F0-founder-led-bootstrap":
        return timeline
    if phase == "F1-early-institution":
        record, _ = core.validate_content_ref(phase_evidence.get("transition_decision_record"), "historical F0→F1 transition", "records/decisions")
        core.require(record.get("from_phase") == "F0-founder-led-bootstrap" and record.get("to_phase") == "F1-early-institution", "historical timeline requires F0→F1 transition")
        f1 = core.parse_iso_date(record.get("effective_date"), "F1 effective_date")
        core.require(f1 >= effective, "F1 cannot predate governance")
        return timeline + [(f1, "F1-early-institution")]
    core.require(phase == "F2-distributed-institution", "unsupported institutional phase")
    prior, _ = core.validate_content_ref(phase_evidence.get("prior_transition_decision_record"), "historical prior F0→F1 transition", "records/decisions")
    current, _ = core.validate_content_ref(phase_evidence.get("transition_decision_record"), "historical current F1→F2 transition", "records/decisions")
    core.require(prior.get("from_phase") == "F0-founder-led-bootstrap" and prior.get("to_phase") == "F1-early-institution", "historical timeline requires prior F0→F1 transition")
    core.require(current.get("from_phase") == "F1-early-institution" and current.get("to_phase") == "F2-distributed-institution", "historical timeline requires F1→F2 transition")
    f1 = core.parse_iso_date(prior.get("effective_date"), "prior F1 effective_date")
    f2 = core.parse_iso_date(current.get("effective_date"), "F2 effective_date")
    core.require(effective <= f1 < f2, "historical phase chronology invalid")
    return timeline + [(f1, "F1-early-institution"), (f2, "F2-distributed-institution")]


def phase_as_of(status: dict, phase_evidence: dict, target: date) -> str | None:
    result = None
    for effective, phase in phase_timeline(status, phase_evidence):
        if target < effective:
            break
        result = phase
    return result


def validate_member_admission_record(item, membership, status, rules, founding) -> None:
    life.ORIG_VALIDATE_MEMBER_ADMISSION_RECORD(item, membership, status, rules, founding)
    mode = item.get("admission_mode")
    if status.get("operative") is not True or mode == "constitutive-initial-member":
        return
    record, _ = core.validate_content_ref(item.get("admission_record"), f"member admission {item['person_id']}", "records/decisions")
    decision_date = core.parse_iso_date(record.get("decision_date"), f"member admission {item['person_id']}.decision_date")
    actual = phase_as_of(status, core.load_json("policy/phase-evidence.json"), decision_date)
    core.require(actual is not None, f"member admission {item['person_id']} predates operative governance")
    core.require(record.get("institutional_phase_at_decision") == actual, f"member admission {item['person_id']} phase label does not match historical phase")
    expected_mode = "f0-founding-steward-admission" if actual == "F0-founder-led-bootstrap" else "member-ordinary-approval"
    core.require(mode == expected_mode, f"member admission {item['person_id']} uses authority unavailable in historical phase")


def validate_state_transition_history(item, membership, status, rules, founding) -> str:
    person_id = item["person_id"]
    current_state = "active"
    previous_effective = core.parse_iso_date(item.get("active_since"), f"member {person_id}.active_since")
    seen = set()
    phase_evidence = core.load_json("policy/phase-evidence.json")
    for index, ref in enumerate(life.transition_records(item)):
        data = life.load_transition(ref, person_id, index)
        core.require(data.get("governance_version") == status["governance_version"], f"member {person_id} transition version mismatch")
        decision_id = data.get("decision_id")
        core.require(isinstance(decision_id, str) and decision_id and decision_id not in seen, f"member {person_id} transition decision_id invalid/duplicate")
        seen.add(decision_id)
        decision_date_text = data.get("decision_date")
        decision_date = core.parse_iso_date(decision_date_text, f"member {person_id} transition {index}.decision_date")
        effective = core.parse_iso_date(data.get("effective_date"), f"member {person_id} transition {index}.effective_date")
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
            core.validate_signature_ref(data.get("signature_evidence"), f"member {person_id} resignation signature", person_id, decision_id, payload_hash, "membership-state-transition", status["governance_version"], status["governance_version"])
        elif transition_type in {"inactivity", "suspension", "reactivation"}:
            expected_to = {"inactivity": "inactive", "suspension": "suspended", "reactivation": "active"}[transition_type]
            core.require(to_state == expected_to, f"member {person_id} {transition_type} target invalid")
            if transition_type == "reactivation":
                core.require(current_state in {"inactive", "suspended"}, f"member {person_id} reactivation source invalid")
            else:
                core.require(current_state in {"active", "inactive"}, f"member {person_id} {transition_type} source invalid")
            process = core.validate_process_evidence_ref(data.get("process_evidence"), f"member {person_id} {transition_type} process", f"membership-{transition_type}-process-evidence", status["governance_version"], f"membership-{transition_type}:{person_id}")
            core.require(process.get("decision_id") == decision_id, f"member {person_id} {transition_type} process decision mismatch")
            core.require(process.get("transition_payload_sha256") == payload_hash, f"member {person_id} {transition_type} process payload mismatch")
            core.require(process.get("decision_date") == decision_date_text and process.get("effective_date") == data.get("effective_date"), f"member {person_id} {transition_type} process chronology binding mismatch")
            core.require(process.get("from_state") == current_state and process.get("to_state") == to_state, f"member {person_id} {transition_type} process state binding mismatch")
            core.require(process.get("reason") == data.get("reason"), f"member {person_id} {transition_type} process reason mismatch")
        elif transition_type == "termination":
            core.require(to_state == "former", f"member {person_id} termination must end membership")
            if actual == "F0-founder-led-bootstrap":
                founder_id = founding["founding_steward"]["person_id"]
                core.validate_signature_ref(data.get("signature_evidence"), f"member {person_id} F0 termination signature", founder_id, decision_id, payload_hash, "membership-state-transition", status["governance_version"], status["governance_version"])
            else:
                core.require(data.get("decision_class") == "qualified-approval", f"member {person_id} F1+ termination requires Qualified Approval")
                approval, _ = core.validate_content_ref(data.get("approval_evidence"), f"member {person_id} termination approval envelope", "records/evidence")
                opened = core.parse_iso_date(approval.get("voting_window_open_date"), f"member {person_id} termination voting_window_open_date")
                core.require(
                    effective > opened,
                    f"member {person_id} approval-backed termination must become effective after its frozen electorate snapshot",
                )
                core.validate_approval_evidence(data.get("approval_evidence"), f"member {person_id} termination approval", decision_id, status, rules, membership, expected_rule_id="qualified-approval", expected_artifact_bindings={"transition_payload_sha256": payload_hash}, expected_decision_date=decision_date_text)
        else:
            raise SystemExit(f"governance integrity failure: member {person_id} unsupported transition_type: {transition_type}")
        current_state = to_state
        previous_effective = effective
    return current_state


def validate_f1_maturity_as_of(status, phase_evidence, founding, membership, operative_delegations, f1_effective: date) -> None:
    f1 = phase_evidence["f1"]
    active = life.active_members_on(membership, f1_effective)
    core.require(len(active) >= f1["minimum_active_members"], "prior F0→F1 transition lacked minimum Active Members")
    active_delegations = [d for d in operative_delegations if core.delegation_active_on(d, f1_effective)]
    founder = founding["founding_steward"]["person_id"]
    core.require(any(d["holder_person_id"] != founder for d in active_delegations), "prior F0→F1 transition lacked independent role holder")
    scopes = {scope for d in active_delegations for scope in d["scope_types"]}
    core.require(core.CRITICAL_DELEGATION_SCOPES.issubset(scopes), "prior F0→F1 transition lacked effective critical delegations")
    independent = core.validate_process_evidence_ref(f1["independent_role_holder_evidence"], "historical F1 independent role evidence", "independent-role-holder-evidence", status["governance_version"], "f1-independent-role-holder")
    delegation = core.validate_process_evidence_ref(f1["delegation_evidence"], "historical F1 delegation evidence", "delegation-coverage-evidence", status["governance_version"], "f1-critical-delegation-coverage")
    as_of = f1_effective.isoformat()
    core.require(independent.get("as_of_date") == as_of and delegation.get("as_of_date") == as_of, "F1 maturity evidence must bind F1 effective date")
    core.require(set(independent.get("active_member_person_ids", [])) == active, "F1 maturity Member snapshot mismatch")
    core.require(set(delegation.get("active_delegation_ids", [])) == {d["delegation_id"] for d in active_delegations}, "F1 maturity delegation snapshot mismatch")


def validate_prior_f1_transition(status, phase_evidence, rules, membership, founding, operative_delegations) -> None:
    if status["operative"] is False or status["institutional_phase"] in {"F0-founder-led-bootstrap", "F1-early-institution"}:
        core.require(phase_evidence.get("prior_transition_decision_record") is None, "F0/F1 cannot claim prior transition")
        return
    prior_ref = phase_evidence.get("prior_transition_decision_record")
    prior, _ = core.validate_content_ref(prior_ref, "prior F1 phase transition", "records/decisions")
    core.require(prior.get("record_type") == "phase-transition" and prior.get("status") == "adopted", "prior F1 transition invalid")
    core.require(prior.get("from_phase") == "F0-founder-led-bootstrap" and prior.get("to_phase") == "F1-early-institution", "prior transition must establish F1")
    core.require(prior.get("decision_class") == "qualified-approval", "prior F1 transition requires Qualified Approval")
    decision_id = prior.get("decision_id")
    decision_date = prior.get("decision_date")
    effective = core.parse_iso_date(prior.get("effective_date"), "prior F1 effective_date")
    core.require(core.parse_iso_date(decision_date, "prior F1 decision_date") <= effective, "prior F1 decision postdates effect")
    current, _ = core.validate_content_ref(phase_evidence["transition_decision_record"], "current F2 transition", "records/decisions")
    core.require(effective < core.parse_iso_date(current.get("effective_date"), "current F2 effective_date"), "F2 must follow established F1")
    core.require(current.get("prior_transition_sha256") == prior_ref["sha256"], "F2 transition must bind exact F1 transition")
    payload = {k: v for k, v in prior.items() if k not in {"approval_evidence", "transition_payload_sha256"}}
    payload_hash = core.sha256_json(payload)
    core.require(prior.get("transition_payload_sha256") == payload_hash, "prior F1 transition payload hash mismatch")
    core.validate_approval_evidence(prior.get("approval_evidence"), "prior F1 transition approval", decision_id, status, rules, membership, expected_rule_id="qualified-approval", expected_artifact_bindings={"transition_payload_sha256": payload_hash}, expected_decision_date=decision_date)
    validate_f1_maturity_as_of(status, phase_evidence, founding, membership, operative_delegations, effective)


def validate_phase_evidence(status, membership, founding, phase_evidence, operative_delegations, active_members, rules) -> None:
    historical_active = active_members
    if status["operative"] is True and status["institutional_phase"] != "F0-founder-led-bootstrap":
        historical_active = life.active_members_on(membership, core.parse_iso_date(phase_evidence["phase_effective_date"], "phase_effective_date"))
    life.ORIG_VALIDATE_PHASE_EVIDENCE(status, membership, founding, phase_evidence, operative_delegations, historical_active, rules)
    validate_prior_f1_transition(status, phase_evidence, rules, membership, founding, operative_delegations)
