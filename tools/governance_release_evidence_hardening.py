from __future__ import annotations

from datetime import date

import governance_release_authority as authority
import governance_release_lifecycle as lifecycle
import governance_review_auth as review_auth
import validate_governance as core


ORIG_VALIDATE_AUTHORITY_SNAPSHOT = authority.validate_authority_snapshot

ACTIVATION_EVIDENCE_CONTRACT = {
    "conflict_process": ("conflict-process-evidence", "conflict-of-interest-process"),
    "records_privacy_process": ("records-privacy-process-evidence", "records-and-privacy-process"),
    "treasury_controls": ("treasury-controls-evidence", "treasury-and-accounting-controls"),
    "succession_process": ("succession-process-evidence", "succession-process"),
    "qualified_legal_review": ("qualified-legal-review-evidence", "governance-activation"),
}


def _review_forbidden_ids(legal_entity: dict) -> set[str]:
    signatories = legal_entity.get("competent_signatories", [])
    core.require(isinstance(signatories, list), "governance legal-review competent-signatory set invalid")
    return {person_id for person_id in signatories if isinstance(person_id, str) and person_id}


def validate_governance_legal_review(
    ref,
    status: dict,
    legal_entity: dict,
    human_hashes: dict[str, str],
    rules_hash: str,
) -> dict:
    """Validate a governance legal review as a signed, qualification-bound review.

    Reviewer identity and the exact qualification-evidence references are part of
    the signed review payload. Only signature references are excluded from that
    digest, so qualification/reviewer substitution cannot replay an old review.
    """
    data, _ = core.validate_content_ref(ref, "governance qualified legal review", "records/evidence")
    core.require(data.get("record_type") == "qualified-legal-review-evidence", "governance legal review type mismatch")
    core.require(
        data.get("status") == "final" and data.get("complete") is True and data.get("result") == "approved",
        "governance legal review must be final/complete/approved",
    )
    core.require(data.get("governance_version") == status["governance_version"], "governance legal review version mismatch")
    core.require(data.get("subject") == "governance-activation", "governance legal review subject mismatch")
    core.require(data.get("reviewed_artifact_hashes") == human_hashes, "governance legal review does not bind exact human artifacts")
    core.require(data.get("reviewed_decision_rules_sha256") == rules_hash, "governance legal review does not bind decision rules")
    core.require(
        data.get("reviewed_legal_entity") == {key: value for key, value in legal_entity.items() if key != "evidence"},
        "governance legal review legal entity mismatch",
    )
    core.require(data.get("reviewed_governing_law") == status["governing_law"], "governance legal review law mismatch")

    effective = core.parse_iso_date(status["effective_date"], "governance legal-review authority effective_date")
    review_auth.validate_authenticated_qualified_review(
        data,
        "governance qualified legal review",
        completed_no_later_than=effective,
        expected_governance_version=status["governance_version"],
        forbidden_reviewer_ids=_review_forbidden_ids(legal_entity),
    )
    return data


def _validate_activation_process_chronology(process: dict, release_effective: date, label: str) -> None:
    completed = core.parse_iso_date(process.get("completed_date"), f"{label}.completed_date")
    core.require(completed <= release_effective, f"{label} completed after release effective date")
    supporting = process.get("supporting_evidence")
    core.require(isinstance(supporting, list) and supporting, f"{label} supporting evidence required")
    for index, support_ref in enumerate(supporting):
        support = core.validate_supporting_evidence_ref(
            support_ref,
            f"{label} supporting evidence {index}",
            process["governance_version"],
        )
        captured = core.parse_iso_date(support.get("captured_date"), f"{label} supporting evidence {index}.captured_date")
        core.require(captured <= completed, f"{label} supporting evidence postdates completion")


def _load_adoption(ref: dict, label: str) -> dict:
    data, _ = core.validate_content_ref(ref, label, "records/adoptions")
    core.require(
        data.get("record_type") == "governance-adoption"
        and data.get("status") == "adopted"
        and isinstance(data.get("release_sequence"), int)
        and data["release_sequence"] >= 1,
        f"{label} must be an adopted governance release",
    )
    return data


def _raw_authority_snapshot(adoption: dict, label: str) -> dict:
    snapshot, _ = core.validate_content_ref(adoption.get("authority_snapshot"), label, "records/snapshots")
    core.require(
        snapshot.get("record_type") == "governance-authority-snapshot"
        and snapshot.get("status") == "final"
        and snapshot.get("governance_version") == adoption.get("governance_version")
        and snapshot.get("effective_date") == adoption.get("effective_date"),
        f"{label} identity/version invalid",
    )
    activation = snapshot.get("activation_evidence")
    core.require(
        isinstance(activation, dict) and set(activation) == set(ACTIVATION_EVIDENCE_CONTRACT),
        f"{label} activation evidence set invalid",
    )
    return snapshot


def _activation_origin(adoption: dict, key: str, ref: dict, label: str) -> tuple[dict, dict]:
    """Find the release that introduced the exact activation record.

    Later releases may inherit an already-proved activation record without
    pretending it was created under the newer governance version. If a release
    changes a record, that release becomes the new origin and the changed record
    must pass the full semantic gate under that release's authority.
    """
    current = adoption
    current_snapshot = _raw_authority_snapshot(current, f"{label} current authority snapshot")
    core.require(current_snapshot["activation_evidence"].get(key) == ref, f"{label} current activation reference mismatch")
    seen: set[str] = set()
    while current.get("release_sequence", 0) > 1:
        previous_ref = current.get("previous_adoption_record")
        core.require(isinstance(previous_ref, dict), f"{label} predecessor reference missing")
        digest = core.require_sha256(previous_ref.get("sha256"), f"{label} predecessor sha256")
        core.require(digest not in seen, f"{label} predecessor cycle detected")
        seen.add(digest)
        previous = _load_adoption(previous_ref, f"{label} predecessor adoption")
        core.require(
            previous.get("release_sequence") == current["release_sequence"] - 1,
            f"{label} predecessor sequence is not contiguous",
        )
        previous_snapshot = _raw_authority_snapshot(previous, f"{label} predecessor authority snapshot")
        if previous_snapshot["activation_evidence"].get(key) != ref:
            break
        current = previous
        current_snapshot = previous_snapshot
    return current, current_snapshot


def _rules_for_origin(adoption: dict, snapshot: dict, label: str) -> tuple[dict, str]:
    normative = adoption.get("normative_machine_bindings")
    core.require(isinstance(normative, dict), f"{label} normative machine bindings missing")
    rules_hash = core.require_sha256(normative.get("policy/decision-rules.json"), f"{label} decision-rules hash")
    rules_ref = snapshot.get("decision_rules_snapshot")
    core.require(
        isinstance(rules_ref, dict) and rules_ref.get("sha256") == rules_hash,
        f"{label} decision-rules snapshot/hash mismatch",
    )
    rules, _ = core.validate_content_ref(rules_ref, f"{label} decision-rules snapshot", "records/snapshots")
    core.require(rules.get("governance_version") == adoption.get("governance_version"), f"{label} rules version mismatch")
    core.require(rules.get("operative") is True, f"{label} rules snapshot must be operative")
    return rules, rules_hash


def _validate_activation_at_origin(key: str, ref: dict, origin: dict, origin_snapshot: dict, label: str) -> None:
    version = origin.get("governance_version")
    effective_text = origin.get("effective_date")
    effective = core.parse_iso_date(effective_text, f"{label} origin effective_date")
    human_hashes = origin.get("artifact_bindings")
    legal_entity = origin.get("legal_entity")
    governing_law = origin.get("governing_law")
    core.require(isinstance(version, str) and version, f"{label} origin governance version missing")
    core.require(isinstance(human_hashes, dict) and human_hashes, f"{label} origin human artifact bindings missing")
    core.require(isinstance(legal_entity, dict) and legal_entity, f"{label} origin legal entity missing")
    core.require(isinstance(governing_law, str) and governing_law.strip(), f"{label} origin governing law missing")
    _, rules_hash = _rules_for_origin(origin, origin_snapshot, label)

    record_type, subject = ACTIVATION_EVIDENCE_CONTRACT[key]
    if key == "qualified_legal_review":
        validate_governance_legal_review(
            ref,
            {
                "operative": True,
                "governance_version": version,
                "effective_date": effective_text,
                "governing_law": governing_law,
            },
            legal_entity,
            human_hashes,
            rules_hash,
        )
        return

    process = core.validate_process_evidence_ref(
        ref,
        f"{label} activation evidence {key}",
        record_type,
        version,
        subject,
    )
    _validate_activation_process_chronology(process, effective, f"{label} activation evidence {key}")


def validate_release_activation_semantics(snapshot: dict, adoption: dict, rules: dict, label: str) -> None:
    """Semantically prove every activation record before a release can be authority.

    Hash equality proves identity, not success. Each activation record is traced
    backwards to the release that introduced those exact bytes, and it is then
    validated against that release's artifacts, rules, legal identity, version
    and chronology. Unchanged records may be inherited; changed records cannot
    borrow an older review or masquerade as having been completed under a newer
    release.
    """
    activation = snapshot.get("activation_evidence")
    core.require(
        isinstance(activation, dict) and set(activation) == set(ACTIVATION_EVIDENCE_CONTRACT),
        f"{label} activation evidence contract mismatch",
    )
    core.require(rules.get("governance_version") == adoption.get("governance_version"), f"{label} rules version mismatch")

    for key in ACTIVATION_EVIDENCE_CONTRACT:
        ref = activation[key]
        core.require(isinstance(ref, dict), f"{label} activation reference missing: {key}")
        origin, origin_snapshot = _activation_origin(adoption, key, ref, f"{label} {key}")
        _validate_activation_at_origin(key, ref, origin, origin_snapshot, f"{label} {key}")


def validate_authority_snapshot(ref, adoption: dict, label: str) -> tuple[dict, dict]:
    snapshot, rules = ORIG_VALIDATE_AUTHORITY_SNAPSHOT(ref, adoption, label)
    validate_release_activation_semantics(snapshot, adoption, rules, label)
    return snapshot, rules


def validate_classification_base(
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
    """Validate amendment classification with reviewer identity/qualification binding."""
    data, _ = core.validate_content_ref(ref, "governance amendment classification", "records/evidence")
    core.require(
        data.get("record_type") == "governance-amendment-classification-evidence"
        and data.get("status") == "final"
        and data.get("complete") is True,
        "governance amendment classification evidence invalid",
    )
    core.require(data.get("governance_version") == status["governance_version"], "amendment classification governance version mismatch")
    core.require(data.get("decision_id") == decision_id, "amendment classification decision mismatch")
    core.require(data.get("classification") == release_kind, "amendment classification does not match release kind")
    core.require(
        data.get("mission_lock_affected") is (release_kind == lifecycle.MISSION_KIND),
        "amendment classification Mission Lock result inconsistent with release kind",
    )
    core.require(data.get("previous_adoption_sha256") == previous_ref["sha256"], "amendment classification does not bind exact predecessor")
    core.require(data.get("reviewed_artifact_hashes") == human_hashes, "amendment classification does not bind exact proposed governance bytes")
    core.require(data.get("amendment_payload_sha256") == amendment_payload_sha256, "amendment classification does not bind exact amendment payload")
    analysis = data.get("compatibility_and_consequences_analysis")
    core.require(isinstance(analysis, str) and analysis.strip(), "amendment classification requires written compatibility/consequences analysis")
    core.require(data.get("qualified_independent_review") is True, "amendment classification requires qualified independent review")

    completed = core.parse_iso_date(data.get("completed_date"), "governance amendment classification completed_date")
    governance_effective = core.parse_iso_date(status["effective_date"], "governance effective_date")
    core.require(governance_effective <= completed <= final_vote_date, "amendment classification review chronology invalid")
    if first_vote_date is not None:
        core.require(first_vote_date <= completed, "Mission-Locked review must be complete after the first successful vote and before ratification")

    payload, reviewers = review_auth.signed_review_payload(data, "governance amendment classification")
    payload_hash = core.sha256_json(payload)
    core.require(data.get("review_payload_sha256") == payload_hash, "amendment classification review payload hash mismatch")

    competent_signatories = set(legal_entity.get("competent_signatories", []))
    for index, reviewer in enumerate(reviewers):
        reviewer_id = reviewer["reviewer_id"]
        core.require(reviewer_id not in competent_signatories, "amendment classification reviewer must be independent of competent adopters")
        qualification = core.validate_supporting_evidence_ref(
            reviewer["qualification_evidence"],
            f"amendment classification reviewer qualification {index}",
            status["governance_version"],
        )
        captured = core.parse_iso_date(qualification.get("captured_date"), f"amendment classification reviewer qualification {index}.captured_date")
        core.require(captured <= completed, "amendment classification reviewer qualification postdates review completion")
        signature = core.validate_signature_ref(
            reviewer["signature_evidence"],
            f"amendment classification reviewer signature {index}",
            reviewer_id,
            decision_id,
            payload_hash,
            "governance-amendment-classification",
            status["governance_version"],
            status["governance_version"],
        )
        signed = core.parse_iso_date(signature.get("signed_date"), f"amendment classification reviewer signature {index}.signed_date")
        core.require(signed <= completed, "amendment classification reviewer signed after review completion")
    return completed


def install() -> None:
    """Install release-evidence hardening at the shared authority boundaries."""
    core.validate_governance_legal_review = validate_governance_legal_review
    authority.validate_authority_snapshot = validate_authority_snapshot
    # release_authority.validate_classification delegates through this saved
    # base callback, so replacing it hardens both current and historical
    # amendment-classification paths without adding a second verdict route.
    authority.ORIG_VALIDATE_CLASSIFICATION = validate_classification_base
