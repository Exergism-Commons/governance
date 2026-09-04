from __future__ import annotations

import governance_review_auth as review_auth
import governance_temporal_roles as roles
import validate_governance as core


ORIG_VALIDATE_CLA_STATUS = roles.validate_cla_status


def _manifest_ref(status_text: str) -> dict:
    return {
        "path": core.yaml_scalar(status_text, "legal_review_manifest_artifact"),
        "sha256": core.yaml_scalar(status_text, "legal_review_manifest_sha256"),
    }


def _steward_ref(status_text: str) -> dict:
    return {
        "path": core.yaml_scalar(status_text, "legal_steward_authority_artifact"),
        "sha256": core.yaml_scalar(status_text, "legal_steward_authority_sha256"),
    }


def _adoption_ref(status_text: str) -> dict:
    return {
        "path": core.yaml_scalar(status_text, "adoption_record_artifact"),
        "sha256": core.yaml_scalar(status_text, "adoption_record_sha256"),
    }


def _competent_steward_signatories(steward: dict, label: str) -> set[str]:
    legal_identity = steward.get("legal_identity")
    core.require(isinstance(legal_identity, dict), f"{label} legal identity missing")
    signatories = legal_identity.get("competent_signatories")
    core.require(
        isinstance(signatories, list)
        and signatories
        and len(signatories) == len(set(signatories))
        and all(isinstance(person_id, str) and person_id.strip() for person_id in signatories),
        f"{label} competent-signatory set invalid",
    )
    return set(signatories)


def require_adopters_authorized_by_steward(adopters: object, steward: dict, label: str = "CLA adoption") -> None:
    """Require every adopter to be a competent signatory of the receiving Steward.

    Signature authenticity is not institutional authority. The CLA receiving
    party is the adopted Legal Steward, so an operative adoption must be signed
    by identities that the content-addressed Steward authority record already
    recognizes as competent signatories. A future delegated-adopter mechanism
    would need its own explicit content-addressed authority schema; it must not
    be inferred from a valid signature alone.
    """
    competent = _competent_steward_signatories(steward, f"{label} Legal Steward")
    core.require(
        isinstance(adopters, list)
        and adopters
        and len(adopters) == len(set(adopters))
        and all(isinstance(person_id, str) and person_id.strip() for person_id in adopters),
        f"{label} adopter identities invalid",
    )
    unauthorized = set(adopters) - competent
    core.require(not unauthorized, f"{label} contains adopter without Legal Steward authority: {sorted(unauthorized)}")


def validate_cla_reviewer_binding() -> None:
    """Close reviewer/qualification replay in the legacy CLA review envelope.

    The base CLA manifest historically hashes all substantive fields except the
    reviewer list. We keep that stable envelope but require it to contain a
    `reviewer_authentication_sha256` field computed from reviewer identities and
    exact qualification-evidence references. Because that field is inside the
    base review payload, every existing reviewer signature authenticates the
    reviewer/qualification binding indirectly while signature references remain
    excluded and non-self-referential.
    """
    status_text = (core.ROOT / "policy/cla-status.yaml").read_text(encoding="utf-8")
    if core.yaml_scalar(status_text, "operative") is not True:
        return

    manifest, _ = core.validate_content_ref(_manifest_ref(status_text), "CLA reviewer-binding manifest", "records/reviews")
    core.require(
        manifest.get("record_type") == "qualified-legal-review"
        and manifest.get("status") == "final",
        "CLA reviewer-binding manifest invalid",
    )
    review_auth.require_reviewer_binding_digest(manifest, "CLA legal review")
    reviewers = manifest["reviewers"]

    # Prove that the binding field itself is inside the already-signed base
    # review payload rather than an unsigned sidecar.
    base_payload = {key: value for key, value in manifest.items() if key not in {"reviewers", "review_payload_sha256"}}
    core.require(
        "reviewer_authentication_sha256" in base_payload,
        "CLA reviewer authentication digest is outside the signed review payload",
    )
    core.require(
        manifest.get("review_payload_sha256") == core.sha256_json(base_payload),
        "CLA base review payload does not authenticate reviewer binding digest",
    )

    completed = core.parse_iso_date(manifest.get("completed_date"), "CLA legal review completed_date")
    steward, _ = core.validate_content_ref(_steward_ref(status_text), "CLA reviewer-binding Steward authority", "records/decisions")
    forbidden = _competent_steward_signatories(steward, "CLA reviewer-binding Steward")

    for index, reviewer in enumerate(reviewers):
        reviewer_id = reviewer["reviewer_id"]
        core.require(reviewer_id not in forbidden, "CLA legal reviewer must be independent of Steward competent signatories")
        qualification = core.validate_supporting_evidence_ref(
            reviewer["qualification_evidence"],
            f"CLA reviewer-binding qualification {index}",
        )
        captured = core.parse_iso_date(
            qualification.get("captured_date"),
            f"CLA reviewer-binding qualification {index}.captured_date",
        )
        core.require(captured <= completed, "CLA reviewer qualification postdates legal-review completion")


def validate_cla_adopter_authority() -> None:
    """Bind operative CLA adoption identities to the adopted Legal Steward."""
    status_text = (core.ROOT / "policy/cla-status.yaml").read_text(encoding="utf-8")
    if core.yaml_scalar(status_text, "operative") is not True:
        return

    steward, _ = core.validate_content_ref(_steward_ref(status_text), "CLA adopter-authority Steward", "records/decisions")
    adoption, _ = core.validate_content_ref(_adoption_ref(status_text), "CLA adopter-authority adoption", "records/adoptions")
    core.require(
        adoption.get("record_type") == "cla-adoption" and adoption.get("status") == "adopted",
        "CLA adopter-authority adoption record invalid",
    )
    require_adopters_authorized_by_steward(adoption.get("adopters"), steward)


def validate_cla_status() -> None:
    ORIG_VALIDATE_CLA_STATUS()
    validate_cla_reviewer_binding()
    validate_cla_adopter_authority()
