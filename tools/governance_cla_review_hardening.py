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
    reviewers = manifest.get("reviewers")
    core.require(isinstance(reviewers, list) and reviewers, "CLA reviewer-binding requires reviewers")
    binding_hash = review_auth.reviewer_binding_sha256(reviewers, "CLA legal review")
    core.require(
        manifest.get("reviewer_authentication_sha256") == binding_hash,
        "CLA legal review does not bind reviewer identities and qualification evidence",
    )

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
    competent_signatories = steward.get("legal_identity", {}).get("competent_signatories", [])
    core.require(isinstance(competent_signatories, list), "CLA Steward competent-signatory set invalid")
    forbidden = set(competent_signatories)

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


def validate_cla_status() -> None:
    ORIG_VALIDATE_CLA_STATUS()
    validate_cla_reviewer_binding()
