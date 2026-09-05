from __future__ import annotations

import validate_governance as core
import validate_governance_lifecycle as life
import governance_temporal_phase as phase
import governance_release_history as release_history


def validate_state_transition_history(item, membership, status, rules, founding) -> str:
    result = phase.validate_state_transition_history(item, membership, status, rules, founding)
    if status.get("operative") is not True:
        return result

    person_id = item["person_id"]
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

        # The first lifecycle pass already validates each transition under the
        # release that was operative when the action occurred. Preserve that
        # historical authority here as well: a later governance amendment must
        # not move the lower chronology bound or version expected by this
        # second, evidence-specific chronology pass.
        event_status = release_history.release_status_as_of(status, decision_date)
        event_version = event_status["governance_version"]
        event_governance_effective = core.parse_iso_date(
            event_status["effective_date"],
            f"member {person_id} transition {index} authorizing governance effective_date",
        )
        core.require(
            transition.get("governance_version") == event_version,
            f"member {person_id} transition {index} governance version does not match release in force",
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
                event_version,
                event_version,
            )
            signed_date = core.parse_iso_date(
                signature.get("signed_date"),
                f"member {person_id} resignation signature.signed_date",
            )
            core.require(
                event_governance_effective <= signed_date <= decision_date <= effective_date,
                f"member {person_id} resignation signature must exist no later than its decision/effective boundary under the release in force",
            )
            continue

        if transition_type not in {"inactivity", "suspension", "reactivation"}:
            continue

        process, _ = core.validate_content_ref(
            transition.get("process_evidence"),
            f"member {person_id} {transition_type} process chronology",
            "records/evidence",
        )
        core.require(
            process.get("governance_version") == event_version,
            f"member {person_id} {transition_type} process governance version does not match release in force",
        )
        completed = core.parse_iso_date(
            process.get("completed_date"),
            f"member {person_id} {transition_type} process.completed_date",
        )
        core.require(
            event_governance_effective <= completed <= decision_date <= effective_date,
            f"member {person_id} {transition_type} process must be complete before its decision/effect under the release in force",
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
                event_version,
            )
            captured = core.parse_iso_date(
                support.get("captured_date"),
                f"member {person_id} {transition_type} supporting evidence {support_index}.captured_date",
            )
            core.require(
                event_governance_effective <= captured <= completed,
                f"member {person_id} {transition_type} supporting evidence cannot be captured outside its authorizing release/process chronology",
            )
    return result
