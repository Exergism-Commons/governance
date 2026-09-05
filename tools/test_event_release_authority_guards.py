#!/usr/bin/env python3
"""Focused guards for origin-vs-event release authority boundaries."""

from __future__ import annotations

from datetime import date

import governance_delegation_lifecycle as delegation_lifecycle
import governance_release_authority as release_authority
import governance_succession_auth as succession_auth
import validate_governance as core


def validate_inherited_succession_process_origin() -> int:
    process_ref = {"path": "records/evidence/succession-process.json", "sha256": "a" * 64}
    signature_ref = {"path": "records/evidence/succession-authorizer.json", "sha256": "b" * 64}
    process = {
        "record_type": "succession-process-evidence",
        "status": "final",
        "governance_version": "EC-GOV-1.0",
        "subject": "succession-process",
        "process_id": "succession-process-v1",
        "completed_date": "2026-01-01",
        "authorized_reviewer_person_ids": ["reviewer-a"],
        "authorization_signatures": [signature_ref],
    }
    payload = {key: value for key, value in process.items() if key != "authorization_signatures"}
    process["authorization_payload_sha256"] = core.sha256_json(payload)

    event_status = {
        "operative": True,
        "governance_version": "EC-GOV-3.0",
        "effective_date": "2026-05-01",
        "activation_evidence": {"succession_process": process_ref},
    }
    event_adoption = {"release_sequence": 3, "governance_version": "EC-GOV-3.0", "effective_date": "2026-05-01"}
    origin_adoption = {"release_sequence": 1, "governance_version": "EC-GOV-1.0", "effective_date": "2026-01-02"}
    origin_snapshot = {"governance_version": "EC-GOV-1.0"}

    saved_authority = succession_auth.release_authority.authority_context_as_of
    saved_origin = succession_auth.release_evidence_hardening._activation_origin
    saved_origin_validate = succession_auth.release_evidence_hardening._validate_activation_at_origin
    saved_content = core.validate_content_ref
    saved_signature = core.validate_signature_ref
    origin_calls: list[str] = []
    signature_versions: list[tuple[str, str]] = []
    try:
        succession_auth.release_authority.authority_context_as_of = (
            lambda status, target: (event_status, {}, event_adoption, {"path": "release-3", "sha256": "c" * 64})
        )
        succession_auth.release_evidence_hardening._activation_origin = (
            lambda adoption, key, ref, label: (origin_adoption, origin_snapshot)
        )
        succession_auth.release_evidence_hardening._validate_activation_at_origin = (
            lambda key, ref, origin, snapshot, label: origin_calls.append(origin["governance_version"])
        )

        def fake_content(ref, label, expected_dir):
            if ref == process_ref:
                return process, process_ref["sha256"]
            if ref == signature_ref:
                return {"person_id": "reviewer-a"}, signature_ref["sha256"]
            raise SystemExit(f"unexpected synthetic content reference: {ref}")

        core.validate_content_ref = fake_content

        def fake_signature(ref, label, person_id, decision_id, payload_hash, context_type, context_version, governance_version):
            core.require(person_id == "reviewer-a", "synthetic succession signer mismatch")
            core.require(decision_id == "succession-process-v1", "synthetic succession process ID mismatch")
            signature_versions.append((context_version, governance_version))
            return {"signed_date": "2026-01-01"}

        core.validate_signature_ref = fake_signature

        adopted, adopted_ref, authorized, returned_event_status = succession_auth._adopted_process(
            {"operative": True},
            date.fromisoformat("2026-06-01"),
        )
        core.require(adopted is process and adopted_ref == process_ref, "succession process origin guard lost adopted process")
        core.require(authorized == {"reviewer-a"}, "succession process origin guard lost authorized reviewers")
        core.require(returned_event_status["governance_version"] == "EC-GOV-3.0", "succession event authority must remain current to event date")
        core.require(origin_calls == ["EC-GOV-1.0"], "inherited succession process was not semantically validated at release of origin")
        core.require(signature_versions == [("EC-GOV-1.0", "EC-GOV-1.0")], "adopted process signatures were re-versioned to the later event release")
    finally:
        succession_auth.release_authority.authority_context_as_of = saved_authority
        succession_auth.release_evidence_hardening._activation_origin = saved_origin
        succession_auth.release_evidence_hardening._validate_activation_at_origin = saved_origin_validate
        core.validate_content_ref = saved_content
        core.validate_signature_ref = saved_signature
    return 1


def _synthetic_delegation(operative: bool) -> dict:
    item = {
        "delegation_id": "delegation-a",
        "holder_person_id": "person-a",
        "source_authority": {
            "type": "governance-decision",
            "decision_id": "create-delegation-a",
            "constitutional_basis": core.RESERVED_CONSTITUTIONAL_BASIS,
        },
        "scope_types": ["repository"],
        "scope_resources": {"repository": ["repo-a"]},
        "allowed_actions": ["maintain-repository"],
        "prohibited_actions": ["reserved-placeholder"],
        "governing_rule_version": "EC-GOV-1.0",
        "effective_date": "2026-02-02",
        "expires_at": "2027-12-31",
        "revocation": {"revocable": True, "mechanism": "governance decision", "authority": "ordinary-approval"},
        "operative": operative,
        "decision_record": {"path": "records/decisions/create-delegation-a.json", "sha256": "d" * 64},
        "revocation_record": None,
    }
    return item


def validate_delegation_event_release_split() -> int:
    item = _synthetic_delegation(False)
    grant_hash = core.sha256_json(delegation_lifecycle._grant_payload(item))
    creation = {
        "record_type": "delegation-decision",
        "status": "adopted",
        "governance_version": "EC-GOV-1.0",
        "decision_id": "create-delegation-a",
        "decision_class": "ordinary-approval",
        "decision_date": "2026-02-01",
        "delegation_payload_sha256": grant_hash,
        "approval_evidence": {"path": "create-approval", "sha256": "e" * 64},
    }
    for field in (
        "delegation_id", "holder_person_id", "source_authority", "scope_types", "scope_resources",
        "allowed_actions", "prohibited_actions", "governing_rule_version", "effective_date", "expires_at", "revocation",
    ):
        creation[field] = item[field]

    revocation_ref = {"path": "records/decisions/revoke-delegation-a.json", "sha256": "f" * 64}
    item["revocation_record"] = revocation_ref
    revocation = {
        "record_type": "delegation-revocation",
        "status": "adopted",
        "governance_version": "EC-GOV-2.0",
        "delegation_id": "delegation-a",
        "decision_id": "revoke-delegation-a",
        "decision_class": "ordinary-approval",
        "decision_date": "2026-07-01",
        "effective_date": "2026-07-02",
        "reason": "synthetic lifecycle guard",
        "delegation_payload_sha256": grant_hash,
        "approval_evidence": {"path": "revoke-approval", "sha256": "1" * 64},
    }
    revocation_payload = {key: value for key, value in revocation.items() if key != "approval_evidence"}
    revocation["revocation_payload_sha256"] = core.sha256_json(revocation_payload)

    current_status = {"operative": True, "governance_version": "EC-GOV-3.0", "effective_date": "2026-10-01"}
    current_rules = {"rules": [{"id": "ordinary-approval"}, {"id": "qualified-approval"}]}
    membership = {"members": []}
    delegations = {
        "scope_vocabulary": ["repository"],
        "reserved_non_delegable_actions": [],
    }

    saved_content = core.validate_content_ref
    saved_approval = core.validate_approval_evidence
    saved_event_authority = delegation_lifecycle._event_authority
    authority_dates: list[date] = []
    try:
        def fake_content(ref, label, expected_dir):
            if ref == item["decision_record"]:
                return creation, item["decision_record"]["sha256"]
            if ref == revocation_ref:
                return revocation, revocation_ref["sha256"]
            raise SystemExit(f"unexpected synthetic delegation reference: {ref}")

        core.validate_content_ref = fake_content
        core.validate_approval_evidence = lambda *args, **kwargs: {}

        def fake_event_authority(status, rules, membership_arg, decision_date, label):
            authority_dates.append(decision_date)
            if decision_date == date.fromisoformat("2026-02-01"):
                return (
                    {"operative": True, "governance_version": "EC-GOV-1.0", "effective_date": "2026-01-01"},
                    current_rules,
                    membership_arg,
                )
            if decision_date == date.fromisoformat("2026-07-01"):
                return (
                    {"operative": True, "governance_version": "EC-GOV-2.0", "effective_date": "2026-06-01"},
                    current_rules,
                    membership_arg,
                )
            raise SystemExit(f"unexpected synthetic delegation authority date: {decision_date}")

        delegation_lifecycle._event_authority = fake_event_authority
        effective, checked_grant_hash = delegation_lifecycle._validate_creation(
            item,
            delegations,
            current_status,
            current_rules,
            membership,
        )
        core.require(checked_grant_hash == grant_hash, "historical delegation creation changed immutable grant hash")
        revoked = delegation_lifecycle._validate_revocation(
            item,
            effective,
            grant_hash,
            current_status,
            current_rules,
            membership,
        )
        core.require(revoked == date.fromisoformat("2026-07-02"), "historical delegation revocation effective date mismatch")
        core.require(
            authority_dates == [date.fromisoformat("2026-02-01"), date.fromisoformat("2026-07-01")],
            "delegation creation/revocation were not resolved independently on their own decision dates",
        )
    finally:
        core.validate_content_ref = saved_content
        core.validate_approval_evidence = saved_approval
        delegation_lifecycle._event_authority = saved_event_authority
    return 1


def main() -> None:
    total = 0
    total += validate_inherited_succession_process_origin()
    total += validate_delegation_event_release_split()
    print(f"Event-release authority guards: PASS ({total} cases)")


if __name__ == "__main__":
    main()
