from __future__ import annotations

import governance_release_authority as release_authority
import validate_governance as core


def validate_cla_steward_authority() -> None:
    """Validate the Legal Steward appointment under the release then in force.

    The CLA may become operative after later governance amendments. A historical
    Steward appointment therefore keeps the governance version, decision rules,
    membership policy/electorate and signatures of its own decision date; it is
    not rewritten to the current release merely because the CLA activates later.
    """
    status_text = (core.ROOT / "policy/cla-status.yaml").read_text(encoding="utf-8")
    if core.yaml_scalar(status_text, "operative") is not True:
        return

    governance_status = core.load_json("policy/governance-status.json")
    membership = core.load_json("policy/membership-status.json")
    core.require(governance_status.get("operative") is True, "operative CLA requires operative organization governance")

    legal_steward = core.yaml_scalar(status_text, "legal_steward")
    ref = {
        "path": core.yaml_scalar(status_text, "legal_steward_authority_artifact"),
        "sha256": core.yaml_scalar(status_text, "legal_steward_authority_sha256"),
    }
    record, _ = core.validate_content_ref(ref, "CLA legal Steward authority", "records/decisions")
    core.require(
        record.get("record_type") == "cla-legal-steward-authority"
        and record.get("status") == "adopted",
        "CLA Steward authority record type/status invalid",
    )

    decision_id = record.get("decision_id")
    core.require(isinstance(decision_id, str) and decision_id.strip(), "CLA Steward authority decision_id required")
    decision_date_text = record.get("decision_date")
    decision_date = core.parse_iso_date(decision_date_text, "CLA Steward authority decision_date")

    authority_status, authority_rules, authority_adoption, _ = release_authority.authority_context_as_of(
        governance_status,
        decision_date,
    )
    event_version = authority_status["governance_version"]
    authority_effective = core.parse_iso_date(
        authority_status["effective_date"],
        "CLA Steward historical governance release effective_date",
    )
    core.require(authority_effective <= decision_date, "CLA Steward appointment predates its governing release")
    core.require(
        record.get("governance_version") == event_version,
        "CLA Steward authority must retain the governance version operative on decision_date",
    )

    authority_membership = release_authority.membership_context_as_of(
        governance_status,
        membership,
        decision_date,
    )

    identity = record.get("legal_identity")
    core.require(isinstance(identity, dict), "CLA Steward authority requires structured legal_identity")
    core.require(
        set(identity)
        == {
            "legal_name",
            "legal_form",
            "jurisdiction",
            "registration_identity",
            "relationship_to_exergism_commons",
            "competent_signatories",
        },
        "CLA Steward legal_identity fields incomplete/unexpected",
    )
    for key in (
        "legal_name",
        "legal_form",
        "jurisdiction",
        "registration_identity",
        "relationship_to_exergism_commons",
    ):
        core.require(isinstance(identity[key], str) and identity[key].strip(), f"CLA Steward legal_identity.{key} required")
    signatories = identity["competent_signatories"]
    core.require(
        isinstance(signatories, list)
        and signatories
        and len(signatories) == len(set(signatories))
        and all(isinstance(person_id, str) and person_id.strip() for person_id in signatories),
        "CLA Steward competent signatories invalid",
    )
    core.require(record.get("legal_steward") == legal_steward, "CLA Steward stable identifier mismatch")

    identity_evidence = record.get("identity_evidence")
    core.require(isinstance(identity_evidence, list) and identity_evidence, "CLA Steward legal identity requires registration/identity evidence")
    for index, item in enumerate(identity_evidence):
        evidence = core.validate_supporting_evidence_ref(
            item,
            f"CLA Steward identity evidence {index}",
            event_version,
        )
        captured = core.parse_iso_date(
            evidence.get("captured_date"),
            f"CLA Steward identity evidence {index}.captured_date",
        )
        core.require(
            authority_effective <= captured <= decision_date,
            "CLA Steward identity evidence crosses the historical authority boundary",
        )

    core.require(record.get("decision_class") == "qualified-approval", "CLA legal Steward appointment requires Qualified Approval")
    payload = {
        key: value
        for key, value in record.items()
        if key not in {"approval_evidence", "signatory_evidence", "authority_payload_sha256"}
    }
    payload_hash = core.sha256_json(payload)
    core.require(record.get("authority_payload_sha256") == payload_hash, "CLA Steward authority payload hash mismatch")

    # Evaluate approval under the release/policy/electorate that was actually in
    # force on decision_date. This preserves valid historical appointments after
    # later amendments while preventing current rules from retroactively blessing
    # an old decision.
    core.validate_approval_evidence(
        record.get("approval_evidence"),
        "CLA legal Steward authority approval",
        decision_id,
        authority_status,
        authority_rules,
        authority_membership,
        expected_rule_id="qualified-approval",
        expected_artifact_bindings={"authority_payload_sha256": payload_hash},
        expected_decision_date=decision_date_text,
    )

    signatures = record.get("signatory_evidence")
    core.require(isinstance(signatures, list) and len(signatures) == len(signatories), "CLA Steward competent-signatory evidence incomplete")
    signed_people: set[str] = set()
    for index, sig_ref in enumerate(signatures):
        sig, _ = core.validate_content_ref(sig_ref, f"CLA Steward competent signature envelope {index}", "records/evidence")
        signer = sig.get("person_id")
        core.require(signer in signatories and signer not in signed_people, "CLA Steward competent signature identity mismatch")
        validated = core.validate_signature_ref(
            sig_ref,
            f"CLA Steward competent signature {index}",
            signer,
            decision_id,
            payload_hash,
            "cla-legal-steward-authority",
            event_version,
            event_version,
        )
        signed_date = core.parse_iso_date(
            validated.get("signed_date"),
            f"CLA Steward competent signature {index}.signed_date",
        )
        core.require(
            authority_effective <= signed_date <= decision_date,
            "CLA Steward competent signature lies outside the historical decision authority",
        )
        signed_people.add(signer)
    core.require(signed_people == set(signatories), "CLA Steward authority missing competent signature")

    # Prove that the release context used above is itself the release selected by
    # the validated historical chain, rather than a caller-supplied version shim.
    core.require(
        authority_adoption.get("governance_version") == event_version,
        "CLA Steward historical authority adoption/version mismatch",
    )
