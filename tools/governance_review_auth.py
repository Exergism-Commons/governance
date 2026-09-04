from __future__ import annotations

from datetime import date

import validate_governance as core


REVIEWER_FIELDS = {"reviewer_id", "qualification_evidence", "signature_evidence"}


def require_authentication_shape(review: dict, label: str) -> tuple[str, str, list[dict]]:
    """Require an immutable signed-review envelope before dereferencing evidence.

    The payload digest deliberately excludes only the reviewer signatures and
    the digest field itself. Reviewers therefore sign the exact substantive
    review conclusion and bindings, while their signatures cannot create a
    self-referential hash.
    """
    core.require(isinstance(review, dict), f"{label} review object required")
    review_id = review.get("review_id")
    core.require(isinstance(review_id, str) and review_id.strip(), f"{label} review_id required")
    version = review.get("governance_version")
    core.require(isinstance(version, str) and version.strip(), f"{label} governance_version required")

    payload = {key: value for key, value in review.items() if key not in {"reviewers", "review_payload_sha256"}}
    payload_hash = core.sha256_json(payload)
    core.require(review.get("review_payload_sha256") == payload_hash, f"{label} review payload hash mismatch")

    reviewers = review.get("reviewers")
    core.require(isinstance(reviewers, list) and reviewers, f"{label} requires authenticated qualified reviewers")
    seen: set[str] = set()
    for index, reviewer in enumerate(reviewers):
        core.require(isinstance(reviewer, dict) and set(reviewer) == REVIEWER_FIELDS, f"{label} reviewer {index} fields invalid")
        reviewer_id = reviewer.get("reviewer_id")
        core.require(
            isinstance(reviewer_id, str) and reviewer_id.strip() and reviewer_id not in seen,
            f"{label} reviewer identity invalid/duplicate",
        )
        seen.add(reviewer_id)
    return review_id, payload_hash, reviewers


def validate_authenticated_qualified_review(
    review: dict,
    label: str,
    *,
    completed_no_later_than: date,
    expected_governance_version: str | None = None,
    forbidden_reviewer_ids: set[str] | None = None,
) -> None:
    """Authenticate a qualified legal review and bind its chronology.

    This is intentionally generic: any governance subsystem that treats a
    qualified review as authority can use the same reviewer/qualification/
    payload/signature contract rather than trusting an unsigned `approved`
    envelope.
    """
    review_id, payload_hash, reviewers = require_authentication_shape(review, label)
    review_version = review["governance_version"]
    if expected_governance_version is not None:
        core.require(review_version == expected_governance_version, f"{label} governance version mismatch")

    completed = core.parse_iso_date(review.get("completed_date"), f"{label} completed_date")
    core.require(completed <= completed_no_later_than, f"{label} completed after the authority/effective boundary")

    forbidden = forbidden_reviewer_ids or set()
    for index, reviewer in enumerate(reviewers):
        reviewer_id = reviewer["reviewer_id"]
        core.require(reviewer_id not in forbidden, f"{label} reviewer is not independent: {reviewer_id}")

        qualification = core.validate_supporting_evidence_ref(
            reviewer["qualification_evidence"],
            f"{label} reviewer qualification {index}",
            review_version,
        )
        captured = core.parse_iso_date(
            qualification.get("captured_date"),
            f"{label} reviewer qualification {index}.captured_date",
        )
        core.require(captured <= completed, f"{label} reviewer qualification postdates review completion")

        signature = core.validate_signature_ref(
            reviewer["signature_evidence"],
            f"{label} reviewer signature {index}",
            reviewer_id,
            review_id,
            payload_hash,
            "governance-legal-review",
            review_version,
            review_version,
        )
        signed = core.parse_iso_date(signature.get("signed_date"), f"{label} reviewer signature {index}.signed_date")
        core.require(signed <= completed, f"{label} reviewer signed after review completion")
