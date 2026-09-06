from __future__ import annotations

import validate_governance as core
import validate_governance_lifecycle as life
import governance_temporal_phase as phase
import governance_founding_lifecycle as founding_lifecycle
import governance_release_authority as release_authority


def _require_f0_signature_chronology(ref, label: str, status: dict, founding: dict, rules: dict, membership: dict, decision_id: str, payload_hash: str, context_type: str, decision_date) -> None:
    founder_id = founding["founding_steward"]["person_id"]
    authority_status, authority_rules, _, _ = release_authority.authority_context_as_of(status, decision_date)
    event_version = authority_status["governance_version"]
    authority_effective = core.parse_iso_date(authority_status["effective_date"], f"{label} authority release effective_date")
    signature = core.validate_signature_ref(
        ref,
        label,
        founder_id,
        decision_id,
        payload_hash,
        context_type,
        event_version,
        event_version,
    )
    signed_date = core.parse_iso_date(signature.get("signed_date"), f"{label}.signed_date")
    core.require(
        authority_effective <= signed_date <= decision_date,
        f"{label} must be signed under the same operative governance release and no later than the F0 action date",
    )
    core.require(
        founding_lifecycle.founding_steward_active_on(status, founding, authority_rules, membership, signed_date),
        f"{label} signer was not the operative Founding Steward on signed_date",
    )
    core.require(
        founding_lifecycle.founding_steward_active_on(status, founding, authority_rules, membership, decision_date),
        f"{label} action occurred outside the Founding Steward authority interval",
    )


def validate_member_admission_record(item, membership, status, rules, founding) -> None:
    phase.validate_member_admission_record(item, membership, status, rules, founding)
    if status.get("operative") is not True or item.get("admission_mode") != "f0-founding-steward-admission":
        return
    person_id = item["person_id"]
    record, _ = core.validate_content_ref(item.get("admission_record"), f"member admission {person_id}", "records/decisions")
    decision_id = record.get("decision_id")
    decision_date = core.parse_iso_date(record.get("decision_date"), f"member admission {person_id}.decision_date")
    payload_hash = record.get("admission_payload_sha256")
    core.require(isinstance(payload_hash, str) and payload_hash, f"member admission {person_id} payload hash required")
    _require_f0_signature_chronology(
        record.get("signature_evidence"),
        f"F0 admission signature {person_id}",
        status,
        founding,
        rules,
        membership,
        decision_id,
        payload_hash,
        "membership-admission",
        decision_date,
    )


def validate_f0_signed_membership_actions(status: dict, founding: dict, rules: dict, membership: dict) -> None:
    founding_lifecycle.validate_founding_steward_lifecycle(status, founding, rules, membership)
    if status.get("operative") is not True:
        return
    phase_evidence = core.load_json("policy/phase-evidence.json")
    for person_id, item in core.member_index(membership).items():
        if item.get("admission_mode") == "f0-founding-steward-admission":
            record, _ = core.validate_content_ref(item.get("admission_record"), f"member admission {person_id}", "records/decisions")
            decision_date = core.parse_iso_date(record.get("decision_date"), f"member admission {person_id}.decision_date")
            actual = phase.phase_as_of(status, phase_evidence, decision_date)
            if actual == "F0-founder-led-bootstrap":
                _require_f0_signature_chronology(
                    record.get("signature_evidence"),
                    f"F0 admission signature {person_id}",
                    status,
                    founding,
                    rules,
                    membership,
                    record.get("decision_id"),
                    record.get("admission_payload_sha256"),
                    "membership-admission",
                    decision_date,
                )
        for index, ref in enumerate(life.transition_records(item)):
            transition = life.load_transition(ref, person_id, index)
            if transition.get("transition_type") != "termination":
                continue
            decision_date = core.parse_iso_date(transition.get("decision_date"), f"member {person_id} transition {index}.decision_date")
            actual = phase.phase_as_of(status, phase_evidence, decision_date)
            if actual != "F0-founder-led-bootstrap":
                continue
            _require_f0_signature_chronology(
                transition.get("signature_evidence"),
                f"member {person_id} F0 termination signature",
                status,
                founding,
                rules,
                membership,
                transition.get("decision_id"),
                transition.get("transition_payload_sha256"),
                "membership-state-transition",
                decision_date,
            )
