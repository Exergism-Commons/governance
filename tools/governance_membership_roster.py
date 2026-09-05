from __future__ import annotations

from datetime import date

import validate_governance as core


ROSTER_MEMBER_FIELDS = {
    "record_id",
    "person_id",
    "admission_mode",
    "candidate_since",
    "active_since",
    "admission_record",
    "state_transition_records",
}
ROSTER_SNAPSHOT_FIELDS = {
    "record_type",
    "status",
    "release_sequence",
    "governance_version",
    "as_of_date",
    "members",
}


def _transition_refs_as_of(item: dict, target: date, label: str) -> list[dict]:
    refs = item.get("state_transition_records")
    core.require(isinstance(refs, list), f"{label} state_transition_records must be a list")
    selected: list[dict] = []
    previous_effective: date | None = None
    for index, ref in enumerate(refs):
        transition, _ = core.validate_content_ref(
            ref,
            f"{label} transition {index}",
            "records/decisions",
        )
        core.require(
            transition.get("record_type") == "membership-state-transition"
            and transition.get("status") == "adopted"
            and transition.get("person_id") == item.get("person_id"),
            f"{label} transition {index} identity/type invalid",
        )
        effective = core.parse_iso_date(
            transition.get("effective_date"),
            f"{label} transition {index}.effective_date",
        )
        if previous_effective is not None:
            core.require(effective >= previous_effective, f"{label} transition chronology is not monotonic")
        previous_effective = effective
        if effective <= target:
            selected.append(ref)
    return selected


def roster_projection_as_of(membership: dict, target: date, label: str) -> list[dict]:
    """Project every historically admitted Member and its history as of target.

    This deliberately includes inactive/former Members: deleting a historical
    Member from the mutable current registry must not erase their existence from
    a predecessor electorate or release proof.
    """
    by_person = core.member_index(membership)
    projected: list[dict] = []
    for person_id in sorted(by_person):
        item = by_person[person_id]
        active_since_text = item.get("active_since")
        if active_since_text is None:
            continue
        active_since = core.parse_iso_date(active_since_text, f"{label} member {person_id}.active_since")
        if active_since > target:
            continue

        admission_mode = item.get("admission_mode")
        core.require(isinstance(admission_mode, str) and admission_mode.strip(), f"{label} member {person_id} admission_mode missing")
        admission_ref = item.get("admission_record")
        if admission_mode == "constitutive-initial-member":
            # The constitutive adoption contains this roster reference, so
            # embedding the adoption's own future SHA here would be circular.
            # Constitutive provenance is independently validated against release
            # #1; the roster therefore records a null admission ref only for this
            # one bootstrap admission mode.
            snapshot_admission = None
        else:
            core.require(
                isinstance(admission_ref, dict) and set(admission_ref) == {"path", "sha256"},
                f"{label} member {person_id} admission reference invalid",
            )
            core.require_sha256(admission_ref.get("sha256"), f"{label} member {person_id} admission sha256")
            snapshot_admission = admission_ref

        record_id = item.get("record_id")
        core.require(isinstance(record_id, str) and record_id.strip(), f"{label} member {person_id} record_id missing")
        projected.append(
            {
                "record_id": record_id,
                "person_id": person_id,
                "admission_mode": admission_mode,
                "candidate_since": item.get("candidate_since"),
                "active_since": active_since_text,
                "admission_record": snapshot_admission,
                "state_transition_records": _transition_refs_as_of(
                    item,
                    target,
                    f"{label} member {person_id}",
                ),
            }
        )
    return projected


def validate_roster_members(snapshot_members: object, membership: dict, target: date, label: str) -> list[dict]:
    core.require(isinstance(snapshot_members, list), f"{label} members must be a list")
    seen_people: set[str] = set()
    seen_records: set[str] = set()
    for index, item in enumerate(snapshot_members):
        core.require(isinstance(item, dict) and set(item) == ROSTER_MEMBER_FIELDS, f"{label} member {index} fields invalid")
        person_id = item.get("person_id")
        record_id = item.get("record_id")
        core.require(
            isinstance(person_id, str)
            and person_id.strip()
            and person_id not in seen_people,
            f"{label} member {index} person identity invalid/duplicate",
        )
        core.require(
            isinstance(record_id, str)
            and record_id.strip()
            and record_id not in seen_records,
            f"{label} member {index} record identity invalid/duplicate",
        )
        seen_people.add(person_id)
        seen_records.add(record_id)

    expected = roster_projection_as_of(membership, target, f"{label} current-registry projection")
    core.require(
        snapshot_members == expected,
        f"{label} does not exactly preserve every historical admission/transition present by its as_of_date",
    )
    return expected


def validate_release_roster_snapshot(adoption: dict, membership: dict, label: str) -> dict:
    """Validate the immutable roster checkpoint signed into a governance release.

    The reference lives in the governance-adoption record itself. Constitutive
    signatures or amendment ballots therefore authenticate its exact SHA as part
    of the release payload. Later validation requires the mutable Member Registry
    to remain an extension of that historical checkpoint; pruning a Member or a
    transition that existed by the release effective date fails closed.
    """
    ref = adoption.get("membership_roster_snapshot")
    core.require(
        isinstance(ref, dict) and set(ref) == {"path", "sha256"},
        f"{label} must bind a content-addressed membership_roster_snapshot",
    )
    snapshot, _ = core.validate_content_ref(ref, f"{label} membership roster snapshot", "records/snapshots")
    core.require(set(snapshot) == ROSTER_SNAPSHOT_FIELDS, f"{label} membership roster snapshot fields incomplete/unexpected")
    core.require(
        snapshot.get("record_type") == "governance-membership-roster-snapshot"
        and snapshot.get("status") == "final",
        f"{label} membership roster snapshot type/status invalid",
    )
    core.require(snapshot.get("release_sequence") == adoption.get("release_sequence"), f"{label} roster release sequence mismatch")
    core.require(snapshot.get("governance_version") == adoption.get("governance_version"), f"{label} roster governance version mismatch")
    core.require(snapshot.get("as_of_date") == adoption.get("effective_date"), f"{label} roster must be frozen at release effective_date")
    target = core.parse_iso_date(snapshot.get("as_of_date"), f"{label} roster as_of_date")
    validate_roster_members(snapshot.get("members"), membership, target, f"{label} membership roster")
    return snapshot
