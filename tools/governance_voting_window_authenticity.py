from __future__ import annotations

import validate_governance as core
import validate_governance_lifecycle as life
import governance_ballot_proposal_binding as ballot_binding


def validate_opening_record(data, label: str, expected_decision_id: str, expected_rule_id: str, status: dict, membership: dict) -> None:
    record, _ = core.validate_content_ref(
        data.get("voting_window_open_record"),
        f"{label} voting-window opening authenticity",
        "records/evidence",
    )
    required = {
        "record_type",
        "status",
        "governance_version",
        "decision_id",
        "decision_class",
        "opened_date",
        "recorded_date",
        "opened_by_person_id",
        "eligible_person_ids",
        "supporting_evidence",
        "opening_payload_sha256",
        "signature_evidence",
    }
    core.require(set(record) == required, f"{label} voting-window opening fields incomplete/unexpected")
    core.require(record["record_type"] == "voting-window-open-evidence" and record["status"] == "final", f"{label} voting-window opening invalid")
    core.require(record["governance_version"] == status["governance_version"], f"{label} voting-window opening governance version mismatch")
    core.require(record["decision_id"] == expected_decision_id and record["decision_class"] == expected_rule_id, f"{label} voting-window opening decision mismatch")

    opened = core.parse_iso_date(record["opened_date"], f"{label}.opened_date")
    recorded = core.parse_iso_date(record["recorded_date"], f"{label}.recorded_date")
    governance_effective = core.parse_iso_date(status["effective_date"], "governance effective_date")
    decision_date = core.parse_iso_date(data.get("decision_date"), f"{label}.decision_date")
    core.require(governance_effective <= opened == recorded <= decision_date, f"{label} voting-window opening must be recorded on the opening date")
    core.require(data.get("voting_window_open_date") == record["opened_date"], f"{label} voting-window opening date mismatch")

    opener = record.get("opened_by_person_id")
    core.require(isinstance(opener, str) and opener.strip(), f"{label} voting-window opener required")
    core.require(opener in life.active_members_on(membership, opened), f"{label} voting-window opener must be an Active Member on opening date")

    expected_electorate = life.historical_active_members_as_of(membership, opened, expected_rule_id)
    electorate = record.get("eligible_person_ids")
    core.require(isinstance(electorate, list) and len(electorate) == len(set(electorate)), f"{label} voting-window electorate invalid")
    core.require(set(electorate) == expected_electorate, f"{label} voting-window electorate snapshot mismatch")

    supporting = record.get("supporting_evidence")
    core.require(isinstance(supporting, list) and supporting, f"{label} voting-window opening requires supporting evidence")
    for index, support_ref in enumerate(supporting):
        support = core.validate_supporting_evidence_ref(
            support_ref,
            f"{label} voting-window opening supporting evidence {index}",
            status["governance_version"],
        )
        captured = core.parse_iso_date(
            support.get("captured_date"),
            f"{label} voting-window opening supporting evidence {index}.captured_date",
        )
        core.require(
            governance_effective <= captured <= opened,
            f"{label} voting-window supporting evidence cannot be captured after opening",
        )

    payload = {
        key: value
        for key, value in record.items()
        if key not in {"signature_evidence", "opening_payload_sha256"}
    }
    payload_hash = core.sha256_json(payload)
    core.require(record.get("opening_payload_sha256") == payload_hash, f"{label} voting-window opening payload hash mismatch")
    signature = core.validate_signature_ref(
        record.get("signature_evidence"),
        f"{label} voting-window opening signature",
        opener,
        expected_decision_id,
        payload_hash,
        "voting-window-open",
        status["governance_version"],
        status["governance_version"],
    )
    signed = core.parse_iso_date(signature.get("signed_date"), f"{label} voting-window opening signature.signed_date")
    core.require(signed == opened, f"{label} voting-window opening must be signed on opened_date")


def validate_vote_approval(data, label, expected_decision_id, expected_rule_id, status, rules, membership, expected_artifact_bindings=None, expected_decision_date=None) -> None:
    validate_opening_record(data, label, expected_decision_id, expected_rule_id, status, membership)
    ballot_binding.validate_vote_approval(
        data,
        label,
        expected_decision_id,
        expected_rule_id,
        status,
        rules,
        membership,
        expected_artifact_bindings,
        expected_decision_date,
    )
