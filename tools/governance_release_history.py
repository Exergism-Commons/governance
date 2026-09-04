from __future__ import annotations

from datetime import date

import validate_governance as core


INITIAL_KIND = "initial-constitutive-adoption"


def release_contract(status: dict) -> dict:
    contract = status.get("governance_release_contract")
    core.require(isinstance(contract, dict), "governance release contract required")
    sequence = contract.get("current_release_sequence")
    core.require(isinstance(sequence, int) and sequence >= 0, "governance release sequence invalid")
    return contract


def founding_adoption_ref(status: dict) -> dict:
    contract = release_contract(status)
    sequence = contract["current_release_sequence"]
    core.require(status.get("operative") is True and sequence >= 1, "founding governance anchor exists only for operative governance")
    ref = contract.get("founding_adoption_record")
    core.require(isinstance(ref, dict), "operative governance requires a content-addressed founding adoption anchor")
    if sequence == 1:
        core.require(ref == status.get("adoption_record"), "release #1 founding anchor must equal current adoption record")
    return ref


def founding_adoption(status: dict) -> tuple[dict, dict]:
    ref = founding_adoption_ref(status)
    record, _ = core.validate_content_ref(ref, "founding governance adoption", "records/adoptions")
    core.require(
        record.get("record_type") == "governance-adoption"
        and record.get("status") == "adopted"
        and record.get("release_sequence") == 1
        and record.get("release_kind") == INITIAL_KIND,
        "founding governance anchor must resolve to release #1 constitutive adoption",
    )
    contract = release_contract(status)
    core.require(
        record.get("governance_version") == contract.get("initial_operative_version"),
        "founding governance version does not match release contract",
    )
    return record, ref


def founding_effective_date(status: dict) -> date:
    record, _ = founding_adoption(status)
    return core.parse_iso_date(record.get("effective_date"), "founding governance effective_date")


def validate_constitutive_initial_member(item: dict, status: dict) -> None:
    person_id = item.get("person_id")
    core.require(isinstance(person_id, str) and person_id.strip(), "constitutive Member person_id required")
    core.require(item.get("candidate_since") is None, f"initial Member {person_id} cannot fabricate Candidate history")
    founding, founding_ref = founding_adoption(status)
    founding_effective = core.parse_iso_date(founding.get("effective_date"), "founding governance effective_date")
    active_since = core.parse_iso_date(item.get("active_since"), f"initial Member {person_id}.active_since")
    core.require(active_since == founding_effective, f"initial Member {person_id} effective date must remain anchored to release #1")
    core.require(item.get("admission_record") == founding_ref, f"initial Member {person_id} must retain the exact release #1 admission reference")
    core.require(
        person_id in set(founding.get("initial_member_person_ids", [])),
        f"initial Member absent from founding constitutive adoption: {person_id}",
    )


def phase_timeline(status: dict, phase_evidence: dict) -> list[tuple[date, str]]:
    if status.get("operative") is not True:
        return []
    effective = founding_effective_date(status)
    timeline = [(effective, "F0-founder-led-bootstrap")]
    phase = status["institutional_phase"]
    if phase == "F0-founder-led-bootstrap":
        return timeline
    if phase == "F1-early-institution":
        record, _ = core.validate_content_ref(
            phase_evidence.get("transition_decision_record"),
            "historical F0→F1 transition",
            "records/decisions",
        )
        core.require(
            record.get("from_phase") == "F0-founder-led-bootstrap"
            and record.get("to_phase") == "F1-early-institution",
            "historical timeline requires F0→F1 transition",
        )
        f1 = core.parse_iso_date(record.get("effective_date"), "F1 effective_date")
        core.require(f1 >= effective, "F1 cannot predate founding governance")
        return timeline + [(f1, "F1-early-institution")]

    core.require(phase == "F2-distributed-institution", "unsupported institutional phase")
    prior, _ = core.validate_content_ref(
        phase_evidence.get("prior_transition_decision_record"),
        "historical prior F0→F1 transition",
        "records/decisions",
    )
    current, _ = core.validate_content_ref(
        phase_evidence.get("transition_decision_record"),
        "historical current F1→F2 transition",
        "records/decisions",
    )
    core.require(
        prior.get("from_phase") == "F0-founder-led-bootstrap"
        and prior.get("to_phase") == "F1-early-institution",
        "historical timeline requires prior F0→F1 transition",
    )
    core.require(
        current.get("from_phase") == "F1-early-institution"
        and current.get("to_phase") == "F2-distributed-institution",
        "historical timeline requires F1→F2 transition",
    )
    f1 = core.parse_iso_date(prior.get("effective_date"), "prior F1 effective_date")
    f2 = core.parse_iso_date(current.get("effective_date"), "F2 effective_date")
    core.require(effective <= f1 < f2, "historical phase chronology invalid")
    return timeline + [(f1, "F1-early-institution"), (f2, "F2-distributed-institution")]


def founding_steward_active_on_projection(status: dict, founding: dict, target: date) -> bool:
    if status.get("operative") is not True:
        return False
    founder = founding.get("founding_steward")
    core.require(isinstance(founder, dict), "Founding Steward projection required")
    start_text = founder.get("assignment_effective_date")
    start = core.parse_iso_date(start_text, "Founding Steward assignment_effective_date")
    core.require(start == founding_effective_date(status), "Founding Steward assignment must remain anchored to release #1")
    if target < start:
        return False
    cessation_ref = founder.get("cessation_record")
    if cessation_ref is None:
        return True
    cessation, _ = core.validate_content_ref(cessation_ref, "Founding Steward historical cessation", "records/decisions")
    core.require(
        cessation.get("record_type") == "founding-steward-cessation"
        and cessation.get("status") == "adopted"
        and cessation.get("founding_steward_person_id") == founder.get("person_id"),
        "Founding Steward historical cessation invalid",
    )
    cessation_effective = core.parse_iso_date(cessation.get("effective_date"), "Founding Steward cessation effective_date")
    return target < cessation_effective


def mission_guardian_active_on_projection(founding: dict, target: date) -> bool:
    guardian = founding.get("mission_guardian")
    core.require(isinstance(guardian, dict), "Mission Guardian projection required")
    if guardian.get("operative_assignment") is not True:
        return False
    record, _ = core.validate_content_ref(guardian.get("assignment_record"), "Mission Guardian historical assignment", "records/decisions")
    core.require(
        record.get("record_type") == "mission-guardian-assignment"
        and record.get("status") == "adopted"
        and record.get("guardian_person_id") == guardian.get("person_id")
        and record.get("guardian_record_id") == guardian.get("record_id"),
        "Mission Guardian historical assignment invalid",
    )
    effective = core.parse_iso_date(record.get("effective_date"), "Mission Guardian assignment effective_date")
    return effective <= target
