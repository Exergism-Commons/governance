from __future__ import annotations

import copy
from datetime import date

import validate_governance as core


INITIAL_KIND = "initial-constitutive-adoption"
AMENDMENT_KINDS = {"constitutional-amendment", "mission-locked-amendment"}


def release_contract(status: dict) -> dict:
    contract = status.get("governance_release_contract")
    core.require(isinstance(contract, dict), "governance release contract required")
    sequence = contract.get("current_release_sequence")
    core.require(isinstance(sequence, int) and sequence >= 0, "governance release sequence invalid")
    return contract


def _load_adoption(ref: dict, label: str) -> dict:
    core.require(isinstance(ref, dict), f"{label} reference required")
    record, _ = core.validate_content_ref(ref, label, "records/adoptions")
    core.require(
        record.get("record_type") == "governance-adoption"
        and record.get("status") == "adopted"
        and isinstance(record.get("release_sequence"), int)
        and record["release_sequence"] >= 1,
        f"{label} must be an adopted governance release",
    )
    return record


def release_chain(status: dict) -> list[tuple[dict, dict]]:
    """Return the immutable governance release chain in ascending sequence order."""
    contract = release_contract(status)
    if status.get("operative") is not True:
        core.require(contract["current_release_sequence"] == 0, "non-operative governance cannot expose an operative release chain")
        return []

    expected = contract["current_release_sequence"]
    core.require(expected >= 1, "operative governance requires release sequence >= 1")
    current_ref = status.get("adoption_record")
    core.require(isinstance(current_ref, dict), "operative governance requires current adoption reference")

    descending: list[tuple[dict, dict]] = []
    seen: set[str] = set()
    ref = current_ref
    sequence = expected
    while True:
        digest = core.require_sha256(ref.get("sha256"), f"governance release #{sequence} sha256")
        core.require(digest not in seen, "governance release history contains a cycle")
        seen.add(digest)
        record = _load_adoption(ref, f"governance release #{sequence}")
        core.require(record["release_sequence"] == sequence, "governance release history is not contiguous")
        if sequence == 1:
            core.require(record.get("release_kind") == INITIAL_KIND, "release #1 must remain constitutive")
            core.require(record.get("previous_adoption_record") is None, "release #1 cannot have a predecessor")
            descending.append((record, ref))
            break
        core.require(record.get("release_kind") in AMENDMENT_KINDS, "later governance release must be an amendment")
        previous = record.get("previous_adoption_record")
        core.require(isinstance(previous, dict), "later governance release missing predecessor")
        descending.append((record, ref))
        ref = previous
        sequence -= 1

    chain = list(reversed(descending))
    core.require(len(chain) == expected, "governance release history length mismatch")
    founding_ref = contract.get("founding_adoption_record")
    core.require(isinstance(founding_ref, dict) and chain[0][1] == founding_ref, "release chain does not terminate at the founding anchor")
    if expected == 1:
        core.require(contract.get("previous_adoption_record") is None, "release #1 cannot expose a predecessor")
    else:
        core.require(contract.get("previous_adoption_record") == chain[-2][1], "release contract predecessor does not match release chain")

    previous_effective: date | None = None
    versions: set[str] = set()
    for index, (record, _) in enumerate(chain, start=1):
        version = record.get("governance_version")
        core.require(isinstance(version, str) and version.strip() and version not in versions, f"governance release #{index} version invalid/reused")
        versions.add(version)
        effective = core.parse_iso_date(record.get("effective_date"), f"governance release #{index} effective_date")
        if previous_effective is not None:
            core.require(previous_effective < effective, "governance releases must have strictly increasing effective dates")
        previous_effective = effective

    current, current_ref_checked = chain[-1]
    core.require(current_ref_checked == current_ref, "current governance release reference mismatch")
    core.require(current.get("governance_version") == status.get("governance_version"), "current governance version does not match release chain")
    core.require(current.get("effective_date") == status.get("effective_date"), "current governance effective date does not match release chain")
    return chain


def founding_adoption_ref(status: dict) -> dict:
    chain = release_chain(status)
    core.require(chain, "founding governance anchor exists only for operative governance")
    return chain[0][1]


def founding_adoption(status: dict) -> tuple[dict, dict]:
    chain = release_chain(status)
    core.require(chain, "founding governance anchor exists only for operative governance")
    record, ref = chain[0]
    contract = release_contract(status)
    core.require(
        record.get("governance_version") == contract.get("initial_operative_version"),
        "founding governance version does not match release contract",
    )
    return record, ref


def founding_effective_date(status: dict) -> date:
    record, _ = founding_adoption(status)
    return core.parse_iso_date(record.get("effective_date"), "founding governance effective_date")


def release_as_of(status: dict, target: date) -> tuple[dict, dict]:
    selected: tuple[dict, dict] | None = None
    for record, ref in release_chain(status):
        effective = core.parse_iso_date(record.get("effective_date"), f"governance release #{record['release_sequence']} effective_date")
        if effective > target:
            break
        selected = (record, ref)
    core.require(selected is not None, f"no operative governance release existed on {target.isoformat()}")
    return selected


def governance_version_as_of(status: dict, target: date) -> str:
    record, _ = release_as_of(status, target)
    version = record.get("governance_version")
    core.require(isinstance(version, str) and version.strip(), "historical governance version missing")
    return version


def release_status_as_of(status: dict, target: date) -> dict:
    """Project release identity fields as they existed on target date.

    Authority-specific machine state (rules/processes) is filled by
    governance_release_authority.authority_context_as_of; this helper only
    removes the accidental dependency on the current release identity.
    """
    record, ref = release_as_of(status, target)
    projected = copy.deepcopy(status)
    projected["governance_version"] = record["governance_version"]
    projected["effective_date"] = record["effective_date"]
    projected["adoption_record"] = ref
    return projected


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
