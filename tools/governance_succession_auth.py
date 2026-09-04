from __future__ import annotations

from datetime import date

import validate_governance as core
import governance_founding_lifecycle as founding_lifecycle
import governance_temporal_roles as temporal_roles
import governance_release_authority as release_authority
import governance_release_history as release_history


ORIG_VALIDATE_FOUNDING_STEWARD_LIFECYCLE = founding_lifecycle.validate_founding_steward_lifecycle
ORIG_VALIDATE_MISSION_GUARDIAN_ASSIGNMENT = temporal_roles.validate_mission_guardian_assignment


def _require_contract(founding: dict) -> None:
    contract = founding.get("succession_authentication_contract")
    core.require(
        contract == {
            "adopted_process_reference": "operative-release-authority-snapshot#activation_evidence.succession_process",
            "adopted_process_requires_authenticated_authorized_reviewers": True,
            "cessation_event_must_bind_exact_adopted_process": True,
            "guardian_assignment_event_must_bind_exact_adopted_process": True,
            "event_reviewers_must_be_authorized_by_adopted_process": True,
            "event_requires_signature_from_every_participating_reviewer": True,
            "event_signatures_bind_exact_process_payload": True,
        },
        "succession authentication contract missing/weakened",
    )


def _adopted_process(status: dict, target: date) -> tuple[dict, dict, set[str], dict]:
    authority_status, _, _, _ = release_authority.authority_context_as_of(status, target)
    activation = authority_status.get("activation_evidence")
    core.require(isinstance(activation, dict), "historical governance activation_evidence missing")
    ref = activation.get("succession_process")
    core.require(isinstance(ref, dict), "succession authority requires adopted succession_process reference in release authority snapshot")
    process = core.validate_process_evidence_ref(
        ref,
        "adopted succession process",
        "succession-process-evidence",
        authority_status["governance_version"],
        "succession-process",
    )
    process_id = process.get("process_id")
    core.require(isinstance(process_id, str) and process_id.strip(), "adopted succession process_id required")
    completed = core.parse_iso_date(process.get("completed_date"), "adopted succession process completed_date")
    authority_effective = core.parse_iso_date(authority_status["effective_date"], "succession authority release effective_date")
    core.require(completed <= authority_effective, "adopted succession process must be complete by the release effective date that activates it")

    authorized = process.get("authorized_reviewer_person_ids")
    core.require(
        isinstance(authorized, list)
        and authorized
        and len(authorized) == len(set(authorized))
        and all(isinstance(person_id, str) and person_id.strip() for person_id in authorized),
        "adopted succession process requires distinct authorized reviewer identities",
    )
    payload = {
        key: value
        for key, value in process.items()
        if key not in {"authorization_signatures", "authorization_payload_sha256"}
    }
    payload_hash = core.sha256_json(payload)
    core.require(
        process.get("authorization_payload_sha256") == payload_hash,
        "adopted succession process authorization payload hash mismatch",
    )
    signatures = process.get("authorization_signatures")
    core.require(
        isinstance(signatures, list) and len(signatures) == len(authorized),
        "adopted succession process requires one signature per authorized reviewer",
    )
    seen: set[str] = set()
    for index, sig_ref in enumerate(signatures):
        envelope, _ = core.validate_content_ref(
            sig_ref,
            f"adopted succession process signature envelope {index}",
            "records/evidence",
        )
        person_id = envelope.get("person_id")
        core.require(
            person_id in authorized and person_id not in seen,
            "adopted succession process signer mismatch/duplicate",
        )
        signature = core.validate_signature_ref(
            sig_ref,
            f"adopted succession process signature {index}",
            person_id,
            process_id,
            payload_hash,
            "succession-process-authority",
            authority_status["governance_version"],
            authority_status["governance_version"],
        )
        signed = core.parse_iso_date(
            signature.get("signed_date"),
            f"adopted succession process signature {index}.signed_date",
        )
        core.require(signed <= completed, "adopted succession process signature postdates process completion")
        seen.add(person_id)
    core.require(seen == set(authorized), "adopted succession process missing authorized reviewer signature")
    return process, ref, set(authorized), authority_status


def _validate_event(
    status: dict,
    process: dict,
    label: str,
    decision_id: str,
    decision_date: date,
    completed: date,
    earliest: date,
) -> None:
    adopted, adopted_ref, authorized, authority_status = _adopted_process(status, decision_date)
    event_version = authority_status["governance_version"]
    authority_effective = core.parse_iso_date(authority_status["effective_date"], f"{label} authority effective_date")
    core.require(
        process.get("adopted_succession_process") == adopted_ref,
        f"{label} must bind the exact succession process of the release operative on decision_date",
    )
    core.require(
        process.get("adopted_succession_process_id") == adopted.get("process_id"),
        f"{label} adopted succession process identity mismatch",
    )
    core.require(process.get("governance_version") == event_version, f"{label} must use governance version operative on decision_date")
    reviewers = process.get("reviewer_ids")
    core.require(
        isinstance(reviewers, list)
        and reviewers
        and len(reviewers) == len(set(reviewers))
        and set(reviewers).issubset(authorized),
        f"{label} reviewers must be authorized participants of the succession process then in force",
    )

    payload = {
        key: value
        for key, value in process.items()
        if key not in {"reviewer_signatures", "process_payload_sha256"}
    }
    payload_hash = core.sha256_json(payload)
    core.require(process.get("process_payload_sha256") == payload_hash, f"{label} process payload hash mismatch")

    signatures = process.get("reviewer_signatures")
    core.require(
        isinstance(signatures, list) and len(signatures) == len(reviewers),
        f"{label} requires one signature per participating reviewer",
    )
    seen: set[str] = set()
    lower_bound = max(earliest, authority_effective)
    for index, sig_ref in enumerate(signatures):
        envelope, _ = core.validate_content_ref(
            sig_ref,
            f"{label} reviewer signature envelope {index}",
            "records/evidence",
        )
        person_id = envelope.get("person_id")
        core.require(person_id in reviewers and person_id not in seen, f"{label} reviewer signature identity mismatch/duplicate")
        signature = core.validate_signature_ref(
            sig_ref,
            f"{label} reviewer signature {index}",
            person_id,
            decision_id,
            payload_hash,
            "succession-process-event",
            event_version,
            event_version,
        )
        signed = core.parse_iso_date(signature.get("signed_date"), f"{label} reviewer signature {index}.signed_date")
        core.require(lower_bound <= signed <= completed, f"{label} reviewer signature chronology invalid")
        core.require(
            release_history.governance_version_as_of(status, signed) == event_version,
            f"{label} reviewer signature crosses a governance release boundary",
        )
        seen.add(person_id)
    core.require(seen == set(reviewers), f"{label} missing authenticated reviewer signature")


def validate_founding_steward_lifecycle(status: dict, founding: dict, rules: dict, membership: dict) -> date | None:
    result = ORIG_VALIDATE_FOUNDING_STEWARD_LIFECYCLE(status, founding, rules, membership)
    _require_contract(founding)
    if status.get("operative") is not True:
        return result

    ref = founding.get("founding_steward", {}).get("cessation_record")
    if not isinstance(ref, dict):
        return result
    record, _ = core.validate_content_ref(ref, "authenticated Founding Steward cessation", "records/decisions")
    if record.get("authority_mode") != "succession-process":
        return result

    decision_date = core.parse_iso_date(record.get("decision_date"), "Founding Steward succession decision_date")
    event_version = release_history.governance_version_as_of(status, decision_date)
    process = core.validate_process_evidence_ref(
        record.get("process_evidence"),
        "authenticated Founding Steward succession trigger",
        "founding-steward-succession-evidence",
        event_version,
        f"founding-steward-cessation:{record.get('founding_steward_person_id')}",
    )
    completed = core.parse_iso_date(process.get("completed_date"), "Founding Steward succession process completed_date")
    assignment_effective = release_history.founding_effective_date(status)
    _validate_event(
        status,
        process,
        "Founding Steward succession trigger",
        record["decision_id"],
        decision_date,
        completed,
        assignment_effective,
    )
    return result


def validate_mission_guardian_assignment(status, founding, rules, membership, phase_evidence) -> None:
    ORIG_VALIDATE_MISSION_GUARDIAN_ASSIGNMENT(status, founding, rules, membership, phase_evidence)
    _require_contract(founding)
    if status.get("operative") is not True:
        return

    guardian = founding.get("mission_guardian", {})
    ref = guardian.get("assignment_record")
    if guardian.get("operative_assignment") is not True or not isinstance(ref, dict):
        return
    record, _ = core.validate_content_ref(ref, "authenticated Mission Guardian assignment", "records/decisions")
    if record.get("authority_mode") != "succession-process":
        return

    decision_date = core.parse_iso_date(record.get("decision_date"), "Mission Guardian succession decision_date")
    event_version = release_history.governance_version_as_of(status, decision_date)
    process = core.validate_process_evidence_ref(
        record.get("process_evidence"),
        "authenticated Mission Guardian succession event",
        "mission-guardian-succession-evidence",
        event_version,
        f"mission-guardian-assignment:{record.get('guardian_person_id')}",
    )
    completed = core.parse_iso_date(process.get("completed_date"), "Mission Guardian succession process completed_date")
    cessation_effective = core.parse_iso_date(
        process.get("founding_steward_cessation_effective_date"),
        "Mission Guardian linked Founding Steward cessation effective date",
    )
    _validate_event(
        status,
        process,
        "Mission Guardian succession event",
        record["decision_id"],
        decision_date,
        completed,
        cessation_effective,
    )
