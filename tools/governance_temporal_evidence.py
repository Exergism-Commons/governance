from __future__ import annotations

import validate_governance as core
import validate_governance_lifecycle as life


def require_voting_window_contract(membership: dict) -> None:
    contract = membership.get("voting_window_contract")
    core.require(
        isinstance(contract, dict)
        and contract.get("eligibility_fixed_at_window_open") is True
        and contract.get("content_addressed_open_record_required") is True,
        "Membership voting-window contract missing/weakened",
    )


def validate_conflict_determination(ref, label, status, expected_decision_id, expected_person_id, decision_date):
    data = life.ORIG_VALIDATE_CONFLICT_DETERMINATION(ref, label, status, expected_decision_id, expected_person_id, decision_date)
    if data.get("determination_method") != "self-recusal":
        return data
    core.require(expected_person_id in data.get("determined_by_person_ids", []), f"{label} self-recusal must be determined by the recused person")
    payload = {k: v for k, v in data.items() if k not in {"signature_evidence", "determination_payload_sha256"}}
    payload_hash = core.sha256_json(payload)
    core.require(data.get("determination_payload_sha256") == payload_hash, f"{label} self-recusal payload hash mismatch")
    core.validate_signature_ref(
        data.get("signature_evidence"),
        f"{label} self-recusal signature",
        expected_person_id,
        expected_decision_id,
        payload_hash,
        "conflict-determination",
        status["governance_version"],
        status["governance_version"],
    )
    return data


def validate_voting_window_open_record(data, label, expected_decision_id, expected_rule_id, status, membership):
    record, _ = core.validate_content_ref(data.get("voting_window_open_record"), f"{label} voting-window open record", "records/evidence")
    core.require(record.get("record_type") == "voting-window-open-evidence" and record.get("status") == "final", f"{label} voting-window record invalid")
    core.require(record.get("governance_version") == status["governance_version"], f"{label} voting-window version mismatch")
    core.require(record.get("decision_id") == expected_decision_id, f"{label} voting-window decision mismatch")
    core.require(record.get("decision_class") == expected_rule_id, f"{label} voting-window decision class mismatch")
    opened_text = record.get("opened_date")
    core.require(data.get("voting_window_open_date") == opened_text, f"{label} voting-window open date mismatch")
    opened = core.parse_iso_date(opened_text, f"{label}.voting_window_open_date")
    decision_date = core.parse_iso_date(data.get("decision_date"), f"{label}.decision_date")
    core.require(core.parse_iso_date(status["effective_date"], "governance effective_date") <= opened <= decision_date, f"{label} voting-window chronology invalid")
    expected = life.historical_active_members_as_of(membership, opened, expected_rule_id)
    recorded = record.get("eligible_person_ids")
    core.require(isinstance(recorded, list) and len(recorded) == len(set(recorded)), f"{label} voting-window electorate invalid")
    core.require(set(recorded) == expected, f"{label} voting-window electorate snapshot mismatch")
    supporting = record.get("supporting_evidence")
    core.require(isinstance(supporting, list) and supporting, f"{label} voting-window record requires supporting evidence")
    for index, item in enumerate(supporting):
        core.validate_supporting_evidence_ref(item, f"{label} voting-window supporting evidence {index}", status["governance_version"])
    return opened


def validate_vote_approval(data, label, expected_decision_id, expected_rule_id, status, rules, membership, expected_artifact_bindings=None, expected_decision_date=None) -> None:
    opened = validate_voting_window_open_record(data, label, expected_decision_id, expected_rule_id, status, membership)
    saved = core.active_members_as_of
    try:
        core.active_members_as_of = lambda membership_, _decision_date, rule_id_: life.historical_active_members_as_of(membership_, opened, rule_id_)
        life.ORIG_VALIDATE_VOTE_APPROVAL(
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
    finally:
        core.active_members_as_of = saved
