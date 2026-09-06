from __future__ import annotations

from datetime import date

import validate_governance as core


INITIAL_KIND = "initial-constitutive-adoption"
AMENDMENT_KINDS = {"constitutional-amendment", "mission-locked-amendment"}


def _signature_date(ref, label: str) -> date:
    data, _ = core.validate_content_ref(ref, label, "records/evidence")
    core.require(data.get("record_type") == "signature-evidence", f"{label} must be signature-evidence")
    return core.parse_iso_date(data.get("signed_date"), f"{label}.signed_date")


def _supporting_captured_no_later_than(ref, label: str, boundary: date) -> None:
    data, _ = core.validate_content_ref(ref, label, "records/evidence")
    captured = core.parse_iso_date(data.get("captured_date"), f"{label}.captured_date")
    core.require(captured <= boundary, f"{label} cannot postdate its authoritative boundary")


def _completed_no_later_than(ref, label: str, effective: date) -> tuple[dict, date]:
    data, _ = core.validate_content_ref(ref, label, "records/evidence")
    completed = core.parse_iso_date(data.get("completed_date"), f"{label}.completed_date")
    core.require(completed <= effective, f"{label} cannot be completed after governance effective_date")
    supporting = data.get("supporting_evidence")
    if isinstance(supporting, list):
        for index, support_ref in enumerate(supporting):
            _supporting_captured_no_later_than(support_ref, f"{label} supporting evidence {index}", completed)
    return data, completed


def _validate_constitutive_chronology(approval: dict, adoption: dict, decision_date: date, completed_date: date, effective: date) -> None:
    core.require(approval.get("approval_mode") == "constitutive-adoption", "release #1 chronology requires constitutive adoption")
    core.require(approval.get("decision_date") == adoption.get("decision_date"), "constitutive approval decision_date mismatch")
    core.require(approval.get("completed_date") == adoption.get("completed_date"), "constitutive approval completed_date mismatch")

    competence, _ = core.validate_content_ref(approval.get("competence_basis"), "constitutive competence chronology", "records/evidence")
    competence_completed = core.parse_iso_date(competence.get("completed_date"), "constitutive competence completed_date")
    core.require(competence_completed <= decision_date, "constitutive competence evidence must exist before adoption decision")
    competence_supporting = competence.get("supporting_evidence")
    core.require(isinstance(competence_supporting, list) and competence_supporting, "constitutive competence supporting evidence required")
    for index, support_ref in enumerate(competence_supporting):
        _supporting_captured_no_later_than(support_ref, f"constitutive competence supporting evidence {index}", competence_completed)

    signatures = approval.get("signature_evidence")
    core.require(isinstance(signatures, list) and signatures, "constitutive adoption signatures required")
    for index, sig_ref in enumerate(signatures):
        signed = _signature_date(sig_ref, f"constitutive adoption signature {index}")
        core.require(signed <= completed_date, "constitutive adoption signature cannot postdate adoption completion")
        core.require(signed <= effective, "constitutive adoption signature cannot postdate governance effective_date")


def _validate_amendment_chronology(status: dict, approval: dict, adoption: dict, decision_date: date, completed_date: date, effective: date) -> None:
    contract = status.get("governance_release_contract")
    core.require(isinstance(contract, dict), "governance release contract required for amendment chronology")
    sequence = contract.get("current_release_sequence")
    kind = contract.get("current_release_kind")
    core.require(isinstance(sequence, int) and sequence >= 2, "amendment chronology requires release sequence >= 2")
    core.require(kind in AMENDMENT_KINDS, "later governance release must use an amendment class")
    core.require(adoption.get("release_sequence") == sequence and adoption.get("release_kind") == kind, "adoption chronology release metadata mismatch")
    core.require(approval.get("approval_mode") == "member-vote", "later governance release chronology must use Member approval")
    core.require(approval.get("decision_class") == kind, "later governance release approval class mismatch")
    core.require(approval.get("decision_id") == adoption.get("decision_id"), "later governance release approval decision mismatch")
    core.require(approval.get("decision_date") == adoption.get("decision_date"), "later governance release approval decision_date mismatch")
    core.require(decision_date <= completed_date <= effective, "later governance release must be ratified before becoming effective")

    rules = core.load_json("policy/decision-rules.json")
    membership = core.load_json("policy/membership-status.json")
    core.validate_approval_evidence(
        adoption.get("approval_evidence"),
        "governance amendment final approval chronology",
        adoption.get("decision_id"),
        status,
        rules,
        membership,
        expected_rule_id=kind,
        expected_artifact_bindings=adoption.get("artifact_bindings"),
        expected_decision_date=adoption.get("decision_date"),
    )


def validate_governance_adoption_chronology(status: dict) -> None:
    contract = status.get("adoption_chronology_contract")
    core.require(
        contract == {
            "prospective_effect_required": True,
            "legal_review_completed_no_later_than_adoption_decision": True,
            "all_activation_evidence_completed_no_later_than_effective_date": True,
            "all_reviewer_and_adopter_signatures_no_later_than_effective_date": True,
            "adoption_decision_no_later_than_effective_date": True,
        },
        "governance adoption chronology contract missing/weakened",
    )
    if status.get("operative") is not True:
        return

    effective = core.parse_iso_date(status.get("effective_date"), "governance effective_date")
    activation = status.get("activation_evidence")
    core.require(isinstance(activation, dict), "operative governance activation evidence required")

    completed_by_key: dict[str, date] = {}
    evidence_by_key: dict[str, dict] = {}
    for key, ref in activation.items():
        core.require(isinstance(ref, dict), f"operative activation evidence missing: {key}")
        evidence, completed = _completed_no_later_than(ref, f"activation evidence {key}", effective)
        evidence_by_key[key] = evidence
        completed_by_key[key] = completed

    review = evidence_by_key["qualified_legal_review"]
    review_completed = completed_by_key["qualified_legal_review"]
    reviewers = review.get("reviewers")
    core.require(isinstance(reviewers, list) and reviewers, "governance legal review reviewers required")
    for index, reviewer in enumerate(reviewers):
        core.require(isinstance(reviewer, dict), f"governance reviewer {index} invalid")
        signed = _signature_date(reviewer.get("signature_evidence"), f"governance reviewer signature {index}")
        core.require(signed <= review_completed, "governance reviewer signature cannot postdate legal-review completion")

    adoption, _ = core.validate_content_ref(status.get("adoption_record"), "governance adoption chronology record", "records/adoptions")
    decision_date = core.parse_iso_date(adoption.get("decision_date"), "governance adoption decision_date")
    completed_date = core.parse_iso_date(adoption.get("completed_date"), "governance adoption completed_date")
    core.require(decision_date <= completed_date <= effective, "governance adoption must be completed no later than effective_date")

    release_contract = status.get("governance_release_contract")
    core.require(isinstance(release_contract, dict), "governance release contract required for adoption chronology")
    sequence = release_contract.get("current_release_sequence")
    kind = release_contract.get("current_release_kind")
    approval, _ = core.validate_content_ref(adoption.get("approval_evidence"), "governance adoption approval chronology", "records/evidence")

    if sequence == 1:
        core.require(kind == INITIAL_KIND, "release #1 chronology must be constitutive")
        core.require(review_completed <= decision_date, "initial governance adoption must follow completed qualified legal review")
        _validate_constitutive_chronology(approval, adoption, decision_date, completed_date, effective)
    else:
        _validate_amendment_chronology(status, approval, adoption, decision_date, completed_date, effective)

    legal_entity = status.get("legal_entity")
    core.require(isinstance(legal_entity, dict), "operative legal entity required for adoption chronology")
    identity_ref = legal_entity.get("evidence")
    identity, _ = core.validate_content_ref(identity_ref, "legal entity identity chronology", "records/evidence")
    identity_completed = core.parse_iso_date(identity.get("completed_date"), "legal entity identity completed_date")
    core.require(identity_completed <= decision_date, "legal entity identity evidence must predate governance adoption")
    for index, support_ref in enumerate(identity.get("supporting_evidence", [])):
        _supporting_captured_no_later_than(support_ref, f"legal entity identity supporting evidence {index}", identity_completed)
