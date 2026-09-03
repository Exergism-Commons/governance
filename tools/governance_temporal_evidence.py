from __future__ import annotations

import validate_governance as core
import validate_governance_lifecycle as life


def require_voting_window_contract(membership: dict) -> None:
    contract = membership.get("voting_window_contract")
    core.require(
        isinstance(contract, dict)
        and contract.get("eligibility_fixed_at_window_open") is True
        and contract.get("content_addressed_open_record_required") is True
        and contract.get("late_admissions_cannot_join_open_vote") is True,
        "Membership voting-window contract missing/weakened",
    )
    ballot = membership.get("ballot_authentication_contract")
    core.require(
        ballot == {
            "content_addressed_authentication_required": True,
            "member_signature_required": True,
            "signature_context_type": "member-ballot",
            "ballot_payload_fields": [
                "decision_id",
                "decision_class",
                "voting_window_open_date",
                "person_id",
                "vote",
            ],
            "authentication_must_occur_within_voting_window": True,
        },
        "Membership ballot-authentication contract missing/weakened",
    )


def _validate_conflict_signature_date(signature: dict, label: str, status: dict, determination_date, decision_date) -> None:
    signed = core.parse_iso_date(signature.get("signed_date"), f"{label}.signed_date")
    governance_effective = core.parse_iso_date(status["effective_date"], "governance effective_date")
    core.require(
        governance_effective <= signed <= determination_date <= decision_date,
        f"{label} chronology invalid; conflict signature must exist no later than determination/decision",
    )


def validate_conflict_determination(ref, label, status, expected_decision_id, expected_person_id, decision_date):
    data = life.ORIG_VALIDATE_CONFLICT_DETERMINATION(ref, label, status, expected_decision_id, expected_person_id, decision_date)
    determination_date = core.parse_iso_date(data.get("determination_date"), f"{label}.determination_date")
    core.require(determination_date <= decision_date, f"{label} determination cannot postdate decision")
    method = data.get("determination_method")
    if method == "self-recusal":
        core.require(expected_person_id in data.get("determined_by_person_ids", []), f"{label} self-recusal must be determined by the recused person")
        payload = {k: v for k, v in data.items() if k not in {"signature_evidence", "determination_payload_sha256"}}
        payload_hash = core.sha256_json(payload)
        core.require(data.get("determination_payload_sha256") == payload_hash, f"{label} self-recusal payload hash mismatch")
        signature = core.validate_signature_ref(
            data.get("signature_evidence"),
            f"{label} self-recusal signature",
            expected_person_id,
            expected_decision_id,
            payload_hash,
            "conflict-determination",
            status["governance_version"],
            status["governance_version"],
        )
        _validate_conflict_signature_date(signature, f"{label} self-recusal signature", status, determination_date, decision_date)
        return data

    core.require(method == "independent-conflict-determination", f"{label} unsupported determination method")
    determiners = data.get("determined_by_person_ids")
    core.require(
        isinstance(determiners, list)
        and determiners
        and len(determiners) == len(set(determiners))
        and expected_person_id not in determiners,
        f"{label} independent determiners must be distinct from recused person",
    )
    membership = core.load_json("policy/membership-status.json")
    active = life.active_members_on(membership, determination_date)
    core.require(set(determiners).issubset(active), f"{label} independent determiners must be Active Members on determination date")

    conflict_process_ref = status.get("activation_evidence", {}).get("conflict_process")
    core.require(isinstance(conflict_process_ref, dict), f"{label} requires adopted conflict-process authority")
    core.require(
        data.get("source_conflict_process_sha256") == conflict_process_ref.get("sha256"),
        f"{label} independent determination must bind adopted conflict process",
    )

    payload = {
        k: v
        for k, v in data.items()
        if k not in {"determiner_signature_evidence", "determination_payload_sha256"}
    }
    payload_hash = core.sha256_json(payload)
    core.require(data.get("determination_payload_sha256") == payload_hash, f"{label} independent determination payload hash mismatch")
    signatures = data.get("determiner_signature_evidence")
    core.require(isinstance(signatures, list) and len(signatures) == len(determiners), f"{label} independent determiner signatures incomplete")
    signed: set[str] = set()
    for index, sig_ref in enumerate(signatures):
        sig_data, _ = core.validate_content_ref(sig_ref, f"{label} determiner signature envelope {index}", "records/evidence")
        signer = sig_data.get("person_id")
        core.require(signer in determiners and signer not in signed, f"{label} independent determiner signature identity mismatch")
        signature = core.validate_signature_ref(
            sig_ref,
            f"{label} independent determiner signature {index}",
            signer,
            expected_decision_id,
            payload_hash,
            "conflict-determination",
            status["governance_version"],
            status["governance_version"],
        )
        _validate_conflict_signature_date(signature, f"{label} independent determiner signature {index}", status, determination_date, decision_date)
        signed.add(signer)
    core.require(signed == set(determiners), f"{label} missing authenticated independent determiner")
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


def validate_ballot_authentication(ballot, label, index, expected_decision_id, expected_rule_id, status, opened, decision_date) -> None:
    core.require(
        isinstance(ballot, dict) and set(ballot) == {"person_id", "vote", "authentication_record"},
        f"{label} ballot {index} must include person_id, vote and authentication_record",
    )
    person_id = ballot.get("person_id")
    vote = ballot.get("vote")
    core.require(isinstance(person_id, str) and person_id.strip(), f"{label} ballot {index} person_id required")
    core.require(vote in {"for", "against", "abstain"}, f"{label} ballot {index} vote invalid")
    payload = {
        "decision_id": expected_decision_id,
        "decision_class": expected_rule_id,
        "voting_window_open_date": opened.isoformat(),
        "person_id": person_id,
        "vote": vote,
    }
    payload_hash = core.sha256_json(payload)
    auth, _ = core.validate_content_ref(ballot.get("authentication_record"), f"{label} ballot {index} authentication", "records/evidence")
    required = {
        "record_type",
        "status",
        "governance_version",
        "decision_id",
        "decision_class",
        "voting_window_open_date",
        "person_id",
        "vote",
        "authenticated_date",
        "ballot_payload_sha256",
        "signature_evidence",
    }
    core.require(set(auth) == required, f"{label} ballot {index} authentication fields incomplete/unexpected")
    core.require(auth["record_type"] == "ballot-authentication-evidence" and auth["status"] == "final", f"{label} ballot {index} authentication record invalid")
    core.require(auth["governance_version"] == status["governance_version"], f"{label} ballot {index} authentication governance version mismatch")
    core.require(auth["decision_id"] == expected_decision_id and auth["decision_class"] == expected_rule_id, f"{label} ballot {index} authentication decision mismatch")
    core.require(auth["voting_window_open_date"] == opened.isoformat(), f"{label} ballot {index} authentication voting-window mismatch")
    core.require(auth["person_id"] == person_id and auth["vote"] == vote, f"{label} ballot {index} authentication identity/vote mismatch")
    core.require(auth["ballot_payload_sha256"] == payload_hash, f"{label} ballot {index} authentication payload hash mismatch")
    authenticated = core.parse_iso_date(auth["authenticated_date"], f"{label} ballot {index}.authenticated_date")
    core.require(opened <= authenticated <= decision_date, f"{label} ballot {index} authentication must occur within voting window")
    signature = core.validate_signature_ref(
        auth["signature_evidence"],
        f"{label} ballot {index} member signature",
        person_id,
        expected_decision_id,
        payload_hash,
        "member-ballot",
        status["governance_version"],
        status["governance_version"],
    )
    core.require(signature.get("signed_date") == auth["authenticated_date"], f"{label} ballot {index} signature date must match authentication date")


def validate_vote_approval(data, label, expected_decision_id, expected_rule_id, status, rules, membership, expected_artifact_bindings=None, expected_decision_date=None) -> None:
    opened = validate_voting_window_open_record(data, label, expected_decision_id, expected_rule_id, status, membership)
    decision_date = core.parse_iso_date(data.get("decision_date"), f"{label}.decision_date")
    ballots = data.get("ballots")
    core.require(isinstance(ballots, list), f"{label} ballots must be a list")
    for index, ballot in enumerate(ballots):
        validate_ballot_authentication(ballot, label, index, expected_decision_id, expected_rule_id, status, opened, decision_date)

    # The base arithmetic validator intentionally understands only the semantic
    # voter/choice pair. Authentication references are validated above and then
    # removed from this transient view; the immutable approval record retains them.
    arithmetic_view = dict(data)
    arithmetic_view["ballots"] = [
        {"person_id": ballot["person_id"], "vote": ballot["vote"]}
        for ballot in ballots
    ]
    saved = core.active_members_as_of
    try:
        core.active_members_as_of = lambda membership_, _decision_date, rule_id_: life.historical_active_members_as_of(membership_, opened, rule_id_)
        life.ORIG_VALIDATE_VOTE_APPROVAL(
            arithmetic_view,
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
