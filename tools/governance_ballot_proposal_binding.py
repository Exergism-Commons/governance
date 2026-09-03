from __future__ import annotations

import validate_governance as core
import governance_temporal_evidence as evidence


def require_ballot_proposal_binding_contract(membership: dict) -> None:
    core.require(
        membership.get("ballot_proposal_binding_contract")
        == {
            "exact_artifact_bindings_required": True,
            "artifact_bindings_sha256_in_signed_ballot_payload": True,
            "ballot_reuse_across_rewritten_proposals_prohibited": True,
        },
        "Membership ballot proposal-binding contract missing/weakened",
    )


def _validate_bound_ballot_authentication(
    ballot,
    label,
    index,
    expected_decision_id,
    expected_rule_id,
    status,
    opened,
    decision_date,
    artifact_bindings_sha256: str,
) -> None:
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
        "artifact_bindings_sha256": artifact_bindings_sha256,
        "person_id": person_id,
        "vote": vote,
    }
    payload_hash = core.sha256_json(payload)
    auth, _ = core.validate_content_ref(
        ballot.get("authentication_record"),
        f"{label} ballot {index} authentication",
        "records/evidence",
    )
    required = {
        "record_type",
        "status",
        "governance_version",
        "decision_id",
        "decision_class",
        "voting_window_open_date",
        "artifact_bindings_sha256",
        "person_id",
        "vote",
        "authenticated_date",
        "ballot_payload_sha256",
        "signature_evidence",
    }
    core.require(set(auth) == required, f"{label} ballot {index} authentication fields incomplete/unexpected")
    core.require(
        auth["record_type"] == "ballot-authentication-evidence" and auth["status"] == "final",
        f"{label} ballot {index} authentication record invalid",
    )
    core.require(
        auth["governance_version"] == status["governance_version"],
        f"{label} ballot {index} authentication governance version mismatch",
    )
    core.require(
        auth["decision_id"] == expected_decision_id and auth["decision_class"] == expected_rule_id,
        f"{label} ballot {index} authentication decision mismatch",
    )
    core.require(
        auth["voting_window_open_date"] == opened.isoformat(),
        f"{label} ballot {index} authentication voting-window mismatch",
    )
    core.require(
        auth["artifact_bindings_sha256"] == artifact_bindings_sha256,
        f"{label} ballot {index} does not bind exact proposal artifact bindings",
    )
    core.require(
        auth["person_id"] == person_id and auth["vote"] == vote,
        f"{label} ballot {index} authentication identity/vote mismatch",
    )
    core.require(
        auth["ballot_payload_sha256"] == payload_hash,
        f"{label} ballot {index} authentication payload hash mismatch",
    )
    authenticated = core.parse_iso_date(
        auth["authenticated_date"],
        f"{label} ballot {index}.authenticated_date",
    )
    core.require(
        opened <= authenticated <= decision_date,
        f"{label} ballot {index} authentication must occur within voting window",
    )
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
    core.require(
        signature.get("signed_date") == auth["authenticated_date"],
        f"{label} ballot {index} signature date must match authentication date",
    )


def validate_vote_approval(
    data,
    label,
    expected_decision_id,
    expected_rule_id,
    status,
    rules,
    membership,
    expected_artifact_bindings=None,
    expected_decision_date=None,
) -> None:
    core.require(
        isinstance(expected_artifact_bindings, dict) and expected_artifact_bindings,
        f"{label} member-vote approval requires exact proposal artifact bindings",
    )
    core.require(
        data.get("artifact_bindings") == expected_artifact_bindings,
        f"{label} artifact bindings mismatch before ballot authentication",
    )
    artifact_bindings_sha256 = core.sha256_json(expected_artifact_bindings)

    original = evidence.validate_ballot_authentication

    def bound_ballot_authentication(
        ballot,
        inner_label,
        index,
        inner_decision_id,
        inner_rule_id,
        inner_status,
        opened,
        decision_date,
    ) -> None:
        _validate_bound_ballot_authentication(
            ballot,
            inner_label,
            index,
            inner_decision_id,
            inner_rule_id,
            inner_status,
            opened,
            decision_date,
            artifact_bindings_sha256,
        )

    evidence.validate_ballot_authentication = bound_ballot_authentication
    try:
        evidence.validate_vote_approval(
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
        evidence.validate_ballot_authentication = original
