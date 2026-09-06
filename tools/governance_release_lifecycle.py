from __future__ import annotations

from datetime import date

import validate_governance as core
import validate_governance_lifecycle as life


ORIG_VALIDATE_APPROVAL_EVIDENCE = core.validate_approval_evidence

INITIAL_KIND = "initial-constitutive-adoption"
CONSTITUTIONAL_KIND = "constitutional-amendment"
MISSION_KIND = "mission-locked-amendment"
AMENDMENT_KINDS = {CONSTITUTIONAL_KIND, MISSION_KIND}


def _release_contract(status: dict) -> dict:
    contract = status.get("governance_release_contract")
    required = {
        "initial_operative_version",
        "current_release_sequence",
        "current_release_kind",
        "founding_adoption_record",
        "previous_adoption_record",
        "constitutive_adoption_reserved_for_initial_release",
        "later_release_classes",
        "later_release_requires_predecessor",
        "amendment_classification_requires_independent_signed_review",
        "mission_locked_requires_two_successful_votes",
        "mission_locked_requires_minimum_vote_separation_days",
        "mission_locked_requires_guardian_consent_during_founding_period",
    }
    core.require(isinstance(contract, dict) and set(contract) == required, "governance release contract missing/incomplete")
    core.require(
        isinstance(contract["initial_operative_version"], str)
        and contract["initial_operative_version"].strip()
        and "-DRAFT" not in contract["initial_operative_version"],
        "initial operative governance version must be fixed and non-draft",
    )
    core.require(
        contract["constitutive_adoption_reserved_for_initial_release"] is True
        and contract["later_release_requires_predecessor"] is True
        and contract["amendment_classification_requires_independent_signed_review"] is True
        and contract["mission_locked_requires_two_successful_votes"] is True
        and contract["mission_locked_requires_minimum_vote_separation_days"] >= 60
        and contract["mission_locked_requires_guardian_consent_during_founding_period"] is True,
        "governance release safeguards weakened",
    )
    core.require(
        contract["later_release_classes"] == [CONSTITUTIONAL_KIND, MISSION_KIND],
        "unexpected later governance release classes",
    )
    return contract


def _load_release(ref, label: str) -> dict:
    data, _ = core.validate_content_ref(ref, label, "records/adoptions")
    core.require(
        data.get("record_type") == "governance-adoption" and data.get("status") == "adopted",
        f"{label} must be an adopted governance-adoption record",
    )
    core.require(
        isinstance(data.get("release_sequence"), int) and data["release_sequence"] >= 1,
        f"{label} release_sequence invalid",
    )
    core.require(
        data.get("release_kind") in {INITIAL_KIND, CONSTITUTIONAL_KIND, MISSION_KIND},
        f"{label} release_kind invalid",
    )
    return data


def _validate_release_chain(ref, expected_sequence: int, initial_version: str, seen: set[str] | None = None) -> dict:
    core.require(isinstance(ref, dict), "governance release predecessor reference required")
    seen = set() if seen is None else seen
    digest = core.require_sha256(ref.get("sha256"), "governance release predecessor sha256")
    core.require(digest not in seen, "governance release chain contains a cycle")
    seen.add(digest)

    record = _load_release(ref, f"governance release #{expected_sequence}")
    core.require(record["release_sequence"] == expected_sequence, "governance release sequence is not contiguous")

    approval, _ = core.validate_content_ref(
        record.get("approval_evidence"),
        f"governance release #{expected_sequence} approval",
        "records/evidence",
    )
    core.require(
        approval.get("record_type") == "approval-evidence" and approval.get("status") == "final",
        f"governance release #{expected_sequence} approval evidence invalid",
    )
    if expected_sequence == 1:
        core.require(record["release_kind"] == INITIAL_KIND, "release #1 must be the constitutive governance adoption")
        core.require(record.get("governance_version") == initial_version, "release #1 governance version changed")
        core.require(record.get("previous_adoption_record") is None, "release #1 cannot claim a predecessor")
        core.require(approval.get("approval_mode") == "constitutive-adoption", "release #1 must use constitutive adoption")
        return record

    core.require(record["release_kind"] in AMENDMENT_KINDS, "later governance release must be an amendment")
    core.require(record.get("decision_class") == record["release_kind"], "release decision class does not match release kind")
    core.require(approval.get("approval_mode") == "member-vote", "later governance release cannot use constitutive adoption")
    core.require(approval.get("decision_class") == record["release_kind"], "release approval decision class mismatch")
    previous_ref = record.get("previous_adoption_record")
    core.require(isinstance(previous_ref, dict), "later governance release must reference its predecessor")
    _validate_release_chain(previous_ref, expected_sequence - 1, initial_version, seen)
    return record


def validate_approval_evidence(
    ref,
    label: str,
    expected_decision_id: str,
    status: dict,
    rules: dict,
    membership: dict,
    expected_rule_id: str | None = None,
    expected_artifact_bindings: dict | None = None,
    expected_decision_date: str | None = None,
    allow_constitutive: bool = False,
    legal_entity: dict | None = None,
    expected_signed_payload_sha256: str | None = None,
) -> dict:
    if label == "governance adoption approval" and allow_constitutive:
        contract = _release_contract(status)
        kind = contract["current_release_kind"]
        data, _ = core.validate_content_ref(ref, label, "records/evidence")
        if kind == INITIAL_KIND:
            core.require(data.get("approval_mode") == "constitutive-adoption", "initial governance release requires constitutive adoption")
        elif kind in AMENDMENT_KINDS:
            core.require(data.get("approval_mode") == "member-vote", "later governance release cannot use constitutive adoption")
            expected_rule_id = kind
            allow_constitutive = False
        else:
            core.require(False, "operative governance cannot use draft release kind")

    return ORIG_VALIDATE_APPROVAL_EVIDENCE(
        ref,
        label,
        expected_decision_id,
        status,
        rules,
        membership,
        expected_rule_id=expected_rule_id,
        expected_artifact_bindings=expected_artifact_bindings,
        expected_decision_date=expected_decision_date,
        allow_constitutive=allow_constitutive,
        legal_entity=legal_entity,
        expected_signed_payload_sha256=expected_signed_payload_sha256,
    )


def _amendment_payload(record: dict) -> tuple[dict, str]:
    excluded = {
        "approval_evidence",
        "first_vote_approval_evidence",
        "amendment_classification_evidence",
        "guardian_consent_evidence",
        "amendment_payload_sha256",
        "constitutive_payload_sha256",
    }
    payload = {key: value for key, value in record.items() if key not in excluded}
    return payload, core.sha256_json(payload)


def _validate_classification(
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
        data.get("mission_lock_affected") is (release_kind == MISSION_KIND),
        "amendment classification Mission Lock result inconsistent with release kind",
    )
    core.require(
        data.get("previous_adoption_sha256") == previous_ref["sha256"],
        "amendment classification does not bind exact predecessor",
    )
    core.require(data.get("reviewed_artifact_hashes") == human_hashes, "amendment classification does not bind exact proposed governance bytes")
    core.require(
        data.get("amendment_payload_sha256") == amendment_payload_sha256,
        "amendment classification does not bind exact amendment payload",
    )
    analysis = data.get("compatibility_and_consequences_analysis")
    core.require(isinstance(analysis, str) and analysis.strip(), "amendment classification requires written compatibility/consequences analysis")
    core.require(data.get("qualified_independent_review") is True, "amendment classification requires qualified independent review")

    completed = core.parse_iso_date(data.get("completed_date"), "governance amendment classification completed_date")
    governance_effective = core.parse_iso_date(status["effective_date"], "governance effective_date")
    core.require(governance_effective <= completed <= final_vote_date, "amendment classification review chronology invalid")
    if first_vote_date is not None:
        core.require(first_vote_date <= completed, "Mission-Locked review must be complete after the first successful vote and before ratification")

    payload = {key: value for key, value in data.items() if key not in {"reviewers", "review_payload_sha256"}}
    payload_hash = core.sha256_json(payload)
    core.require(data.get("review_payload_sha256") == payload_hash, "amendment classification review payload hash mismatch")
    reviewers = data.get("reviewers")
    core.require(isinstance(reviewers, list) and reviewers, "amendment classification requires reviewer records")
    seen: set[str] = set()
    competent_signatories = set(legal_entity.get("competent_signatories", []))
    for index, reviewer in enumerate(reviewers):
        core.require(
            isinstance(reviewer, dict)
            and set(reviewer) == {"reviewer_id", "qualification_evidence", "signature_evidence"},
            f"amendment classification reviewer {index} invalid",
        )
        reviewer_id = reviewer["reviewer_id"]
        core.require(
            isinstance(reviewer_id, str)
            and reviewer_id
            and reviewer_id not in seen
            and reviewer_id not in competent_signatories,
            "amendment classification reviewer must be distinct and independent of competent adopters",
        )
        seen.add(reviewer_id)
        core.validate_supporting_evidence_ref(
            reviewer["qualification_evidence"],
            f"amendment classification reviewer qualification {index}",
            status["governance_version"],
        )
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


def _validate_guardian_consent(
    ref,
    status: dict,
    decision_id: str,
    amendment_payload_sha256: str,
    first_vote_date: date,
    final_vote_date: date,
) -> None:
    founding = core.load_json("policy/founding-stewardship.json")
    founder = founding["founding_steward"]
    guardian = founding["mission_guardian"]
    if founder.get("operative_assignment") is True:
        signer = founder.get("person_id")
    else:
        core.require(guardian.get("operative_assignment") is True, "Mission-Locked amendment requires an operative successor Mission Guardian")
        signer = guardian.get("person_id")
    core.require(isinstance(signer, str) and signer, "Mission-Locked amendment guardian identity missing")
    signature = core.validate_signature_ref(
        ref,
        "Mission-Locked amendment guardian consent",
        signer,
        decision_id,
        amendment_payload_sha256,
        "mission-locked-amendment-consent",
        status["governance_version"],
        status["governance_version"],
    )
    signed = core.parse_iso_date(signature.get("signed_date"), "Mission-Locked amendment guardian consent signed_date")
    core.require(first_vote_date <= signed <= final_vote_date, "Mission-Locked guardian consent must be recorded between the first and final successful votes")


def _validate_later_release(
    status: dict,
    rules: dict,
    membership: dict,
    legal_entity: dict,
    human_hashes: dict[str, str],
    record: dict,
    contract: dict,
) -> None:
    sequence = contract["current_release_sequence"]
    kind = contract["current_release_kind"]
    previous_ref = contract["previous_adoption_record"]
    founding_ref = contract["founding_adoption_record"]

    core.require(sequence >= 2 and kind in AMENDMENT_KINDS, "later governance release metadata invalid")
    core.require(isinstance(previous_ref, dict) and isinstance(founding_ref, dict), "later governance release requires predecessor and founding anchors")
    core.require(status["governance_version"] != contract["initial_operative_version"], "later governance release cannot reuse the constitutive version")
    core.require(record.get("release_sequence") == sequence, "current adoption release sequence mismatch")
    core.require(record.get("release_kind") == kind and record.get("adoption_method") == kind, "current adoption release kind/method mismatch")
    core.require(record.get("decision_class") == kind, "current adoption decision class mismatch")
    core.require(record.get("previous_adoption_record") == previous_ref, "current adoption does not bind exact predecessor")
    core.require(record.get("founding_adoption_record") == founding_ref, "current adoption does not bind constitutive anchor")
    core.require(
        record.get("first_vote_approval_evidence") is None
        if kind == CONSTITUTIONAL_KIND
        else isinstance(record.get("first_vote_approval_evidence"), dict),
        "amendment repeated-vote shape invalid",
    )

    founding_record = _validate_release_chain(founding_ref, 1, contract["initial_operative_version"])
    core.require(founding_record.get("governance_version") == contract["initial_operative_version"], "constitutive anchor version mismatch")
    predecessor = _validate_release_chain(previous_ref, sequence - 1, contract["initial_operative_version"])
    core.require(predecessor["release_sequence"] == sequence - 1, "current predecessor sequence mismatch")

    _, amendment_hash = _amendment_payload(record)
    core.require(record.get("amendment_payload_sha256") == amendment_hash, "governance amendment payload hash mismatch")

    final_approval, _ = core.validate_content_ref(record.get("approval_evidence"), "governance amendment final approval", "records/evidence")
    final_date = core.parse_iso_date(final_approval.get("decision_date"), "governance amendment final vote date")
    core.require(final_approval.get("decision_id") == record.get("decision_id"), "governance amendment final vote decision mismatch")
    core.require(final_approval.get("decision_class") == kind, "governance amendment final vote class mismatch")

    first_date: date | None = None
    if kind == MISSION_KIND:
        first_ref = record["first_vote_approval_evidence"]
        first, _ = core.validate_content_ref(first_ref, "Mission-Locked amendment first approval", "records/evidence")
        first_decision_id = first.get("decision_id")
        core.require(
            isinstance(first_decision_id, str)
            and first_decision_id
            and first_decision_id != record.get("decision_id"),
            "Mission-Locked amendment requires two distinct successful vote decisions",
        )
        core.validate_approval_evidence(
            first_ref,
            "Mission-Locked amendment first approval",
            first_decision_id,
            status,
            rules,
            membership,
            expected_rule_id=MISSION_KIND,
            expected_artifact_bindings=human_hashes,
            expected_decision_date=first.get("decision_date"),
        )
        first_date = core.parse_iso_date(first.get("decision_date"), "Mission-Locked amendment first vote date")
        mission_rule = core.rule_by_id(rules)[MISSION_KIND]
        minimum_days = max(
            mission_rule["minimum_days_between_successful_votes"],
            contract["mission_locked_requires_minimum_vote_separation_days"],
        )
        core.require((final_date - first_date).days >= minimum_days, "Mission-Locked successful votes are not separated by the required minimum interval")

    review_completed = _validate_classification(
        record.get("amendment_classification_evidence"),
        status,
        legal_entity,
        human_hashes,
        previous_ref,
        kind,
        record["decision_id"],
        amendment_hash,
        first_date,
        final_date,
    )

    if kind == MISSION_KIND:
        core.require(first_date is not None and first_date <= review_completed <= final_date, "Mission-Locked independent review chronology invalid")
        required_phases = set(core.rule_by_id(rules)[MISSION_KIND]["guardian_consent_required_in_phases"])
        if status["institutional_phase"] in required_phases:
            core.require(isinstance(record.get("guardian_consent_evidence"), dict), "Mission-Locked amendment requires guardian consent during the Founding Period")
            _validate_guardian_consent(
                record["guardian_consent_evidence"],
                status,
                record["decision_id"],
                amendment_hash,
                first_date,
                final_date,
            )
        else:
            core.require(record.get("guardian_consent_evidence") is None, "post-Founding-period release cannot fabricate a founding-period guardian-consent requirement")
    else:
        core.require(record.get("guardian_consent_evidence") is None, "ordinary Constitutional Amendment cannot claim Mission-Locked guardian consent")


def validate_adoption_record(
    status: dict,
    activation_hashes: dict[str, str],
    rules: dict,
    membership: dict,
    legal_entity: dict | None,
    human_hashes: dict[str, str],
) -> None:
    contract = _release_contract(status)
    sequence = contract["current_release_sequence"]
    kind = contract["current_release_kind"]

    if status["operative"] is False:
        core.require(sequence == 0 and kind == "draft", "draft governance release metadata must remain sequence 0/draft")
        core.require(contract["founding_adoption_record"] is None and contract["previous_adoption_record"] is None, "draft governance cannot fabricate release lineage")
        return life.validate_adoption_record_historical(status, activation_hashes, rules, membership, legal_entity, human_hashes)

    core.require(legal_entity is not None, "operative governance release requires legal entity")
    record, _ = core.validate_content_ref(status.get("adoption_record"), "governance adoption record", "records/adoptions")

    if sequence == 1:
        core.require(kind == INITIAL_KIND, "release #1 must use initial constitutive adoption")
        core.require(status["governance_version"] == contract["initial_operative_version"], "initial operative governance version mismatch")
        core.require(contract["founding_adoption_record"] == status["adoption_record"], "release #1 must become the permanent constitutive anchor")
        core.require(contract["previous_adoption_record"] is None, "release #1 cannot have a predecessor")
        core.require(record.get("release_sequence") == 1 and record.get("release_kind") == INITIAL_KIND, "initial adoption release metadata mismatch")
        core.require(record.get("adoption_method") == INITIAL_KIND, "initial adoption method must be constitutive")
        core.require(record.get("previous_adoption_record") is None, "initial adoption record cannot claim predecessor")
        core.require(record.get("founding_adoption_record") is None, "initial adoption cannot self-reference its content-addressed anchor")
        core.require(record.get("decision_class") is None, "initial constitutive adoption cannot masquerade as a Member amendment")
        core.require(
            record.get("first_vote_approval_evidence") is None
            and record.get("amendment_classification_evidence") is None
            and record.get("guardian_consent_evidence") is None
            and record.get("amendment_payload_sha256") is None,
            "initial constitutive adoption cannot fabricate amendment process evidence",
        )
        result = life.validate_adoption_record_historical(status, activation_hashes, rules, membership, legal_entity, human_hashes)
        approval, _ = core.validate_content_ref(record.get("approval_evidence"), "initial governance adoption approval", "records/evidence")
        core.require(approval.get("approval_mode") == "constitutive-adoption", "release #1 must be authenticated by constitutive adoption evidence")
        return result

    core.require(sequence >= 2, "operative governance release sequence must be >= 1")
    core.require(kind in AMENDMENT_KINDS, "later operative governance release must be an amendment")
    result = life.validate_adoption_record_historical(status, activation_hashes, rules, membership, legal_entity, human_hashes)
    _validate_later_release(status, rules, membership, legal_entity, human_hashes, record, contract)
    return result
