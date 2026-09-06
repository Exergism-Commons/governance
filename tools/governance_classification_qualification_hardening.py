from __future__ import annotations

from datetime import date

import governance_release_authority as authority
import governance_review_auth as review_auth
import validate_governance as core


_INSTALLED = False
_ORIG_VALIDATE_CLASSIFICATION = None


def validate_classification(
    ref,
    status: dict,
    legal_entity: dict,
    human_hashes: dict[str, str],
    previous_ref: dict,
    release_kind: str,
    decision_id: str,
    amendment_payload_sha256: str,
    first_vote_date: date | None,
    final_vote_date: date,
) -> date:
    """Add semantic reviewer-qualification proof to amendment classification.

    The release-evidence layer already authenticates reviewer identity, exact
    qualification references, signatures, independence and chronology. This
    final wrapper additionally proves that each referenced qualification record
    actually qualifies that same reviewer for governance amendment
    classification rather than merely being arbitrary well-formed supporting
    evidence.
    """
    core.require(callable(_ORIG_VALIDATE_CLASSIFICATION), "classification qualification base validator missing")
    completed = _ORIG_VALIDATE_CLASSIFICATION(
        ref,
        status,
        legal_entity,
        human_hashes,
        previous_ref,
        release_kind,
        decision_id,
        amendment_payload_sha256,
        first_vote_date,
        final_vote_date,
    )

    data, _ = core.validate_content_ref(ref, "governance amendment classification qualification", "records/evidence")
    reviewers = data.get("reviewers")
    core.require(isinstance(reviewers, list) and reviewers, "governance amendment classification reviewers required")
    version = status.get("governance_version")
    core.require(isinstance(version, str) and version.strip(), "governance amendment classification version required")

    for index, reviewer in enumerate(reviewers):
        core.require(isinstance(reviewer, dict), f"governance amendment classification reviewer {index} invalid")
        reviewer_id = reviewer.get("reviewer_id")
        core.require(
            isinstance(reviewer_id, str) and reviewer_id.strip(),
            f"governance amendment classification reviewer {index} identity required",
        )
        qualification = review_auth.validate_reviewer_qualification_ref(
            reviewer.get("qualification_evidence"),
            f"governance amendment classification reviewer qualification {index}",
            version,
            reviewer_id,
            "governance-amendment-classification",
        )
        captured = core.parse_iso_date(
            qualification.get("captured_date"),
            f"governance amendment classification reviewer qualification {index}.captured_date",
        )
        core.require(
            captured <= completed,
            "governance amendment classification reviewer qualification postdates review completion",
        )
    return completed


def install() -> None:
    global _INSTALLED, _ORIG_VALIDATE_CLASSIFICATION
    if _INSTALLED:
        return
    _ORIG_VALIDATE_CLASSIFICATION = authority.ORIG_VALIDATE_CLASSIFICATION
    core.require(callable(_ORIG_VALIDATE_CLASSIFICATION), "classification qualification install missing base validator")
    authority.ORIG_VALIDATE_CLASSIFICATION = validate_classification
    _INSTALLED = True
