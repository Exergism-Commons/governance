from __future__ import annotations

import validate_governance as core
import validate_governance_lifecycle as life
import governance_temporal_phase as phase


def validate_state_transition_history(item, membership, status, rules, founding) -> str:
    result = phase.validate_state_transition_history(item, membership, status, rules, founding)
    if status.get("operative") is not True:
        return result

    person_id = item["person_id"]
    governance_effective = core.parse_iso_date(status["effective_date"], "governance effective_date")
    for index, ref in enumerate(life.transition_records(item)):
        transition = life.load_transition(ref, person_id, index)
        transition_type = transition.get("transition_type")

        decision_date = core.parse_iso_date(
            transition.get("decision_date"),
            f"member {person_id} transition {index}.decision_date",
        )
        effective_date = core.parse_iso_date(
            transition.get("effective_date"),
            f"member {person_id} transition {index}.effective_date",
        )

        if transition_type == "resignation":
            payload_hash = transition.get("transition_payload_sha256")
            core.require(
                isinstance(payload_hash, str) and payload_hash,
                f"member {person_id} resignation transition payload hash required",
            )
            signature = core.validate_signature_ref(
                transition.get("signature_evidence"),
                f"member {person_id} resignation signature chronology",
                person_id,
                transition.get("decision_id"),
                payload_hash,
                "membership-state-transition",
                status["governance_version"],
                status["governance_version"],
            )
            signed_date = core.parse_iso_date(
                signature.get("signed_date"),
                f"member {person_id} resignation signature.signed_date",
            )
            core.require(
                governance_effective <= signed_date <= decision_date <= effective_date,
                f"member {person_id} resignation signature must exist no later than its decision/effective boundary",
            )
            continue

        if transition_type not in {"inactivity", "suspension", "reactivation"}:
            continue

        process, _ = core.validate_content_ref(
            transition.get("process_evidence"),
            f"member {person_id} {transition_type} process chronology",
            "records/evidence",
        )
        completed = core.parse_iso_date(
            process.get("completed_date"),
            f"member {person_id} {transition_type} process.completed_date",
        )
        core.require(
            governance_effective <= completed <= decision_date <= effective_date,
            f"member {person_id} {transition_type} process must be complete before its decision/effect",
        )
        supporting = process.get("supporting_evidence")
        core.require(
            isinstance(supporting, list) and supporting,
            f"member {person_id} {transition_type} process requires supporting evidence",
        )
        for support_index, support_ref in enumerate(supporting):
            support = core.validate_supporting_evidence_ref(
                support_ref,
                f"member {person_id} {transition_type} supporting evidence {support_index}",
                status["governance_version"],
            )
            captured = core.parse_iso_date(
                support.get("captured_date"),
                f"member {person_id} {transition_type} supporting evidence {support_index}.captured_date",
            )
            core.require(
                governance_effective <= captured <= completed,
                f"member {person_id} {transition_type} supporting evidence cannot be captured after process completion",
            )
    return result
