from __future__ import annotations

from datetime import date

import governance_release_authority as authority
import governance_release_lifecycle as lifecycle
import governance_review_auth as review_auth
import governance_semantic_invariants as invariants
import validate_governance as core


ORIG_VALIDATE_AUTHORITY_SNAPSHOT = authority.validate_authority_snapshot

ACTIVATION_EVIDENCE_CONTRACT = {
    "conflict_process": ("conflict-process-evidence", "conflict-of-interest-process"),
    "records_privacy_process": ("records-privacy-process-evidence", "records-and-privacy-process"),
    "treasury_controls": ("treasury-controls-evidence", "treasury-and-accounting-controls"),
    "succession_process": ("succession-process-evidence", "succession-process"),
    "qualified_legal_review": ("qualified-legal-review-evidence", "governance-activation"),
}

MANDATORY_QUALIFIED_SUBJECTS_FLOOR = {
    "endowment-principal-withdrawal",
    "persistent-domain-transfer",
    "identifier-authority-transfer",
    "legal-steward-appointment-or-removal",
    "organization-wide-exclusive-ip-transfer",
    "institutional-merger-dissolution-or-succession",
}

MEMBERSHIP_POLICY_BASELINE = {
    "voting_window_contract": {
        "eligibility_fixed_at_window_open": True,
        "content_addressed_open_record_required": True,
        "late_admissions_cannot_join_open_vote": True,
    },
    "voting_window_authenticity_contract": {
        "opening_recorded_on_opened_date": True,
        "active_member_opener_required": True,
        "exact_opening_payload_signature_required": True,
        "opening_signature_must_be_on_opened_date": True,
        "supporting_evidence_captured_no_later_than_opened_date": True,
    },
    "ballot_authentication_contract": {
        "content_addressed_authentication_required": True,
        "member_signature_required": True,
        "signature_context_type": "member-ballot",
        "ballot_payload_fields": {
            "decision_id",
            "decision_class",
            "voting_window_open_date",
            "person_id",
            "vote",
        },
        "authentication_must_occur_within_voting_window": True,
    },
    "ballot_proposal_binding_contract": {
        "exact_artifact_bindings_required": True,
        "artifact_bindings_sha256_in_signed_ballot_payload": True,
        "ballot_reuse_across_rewritten_proposals_prohibited": True,
    },
    "conflict_determination_contract": {
        "content_addressed_record_required": True,
        "self_recusal_requires_subject_signature": True,
        "independent_determination_requires_adopted_conflict_process": True,
        "independent_determiners_must_be_active_members": True,
        "independent_determiners_must_exclude_subject": True,
        "independent_determiners_must_sign_exact_payload": True,
        "signatures_must_not_postdate_determination": True,
        "determination_must_not_postdate_decision": True,
    },
    "f0_signature_chronology_contract": {
        "signed_date_required": True,
        "signature_no_later_than_action_decision_date": True,
        "founding_steward_must_be_operative_on_signed_date": True,
        "founding_steward_must_be_operative_on_action_date": True,
    },
    "admission_modes": {
        "constitutive-initial-member": {
            "allowed_only_at_initial_governance_adoption": True,
            "candidate_period_applies": False,
            "authority": "competent-constitutive-adoption",
        },
        "f0-founding-steward-admission": {
            "candidate_period_applies": True,
            "authority": "operative-founding-steward",
            "signed_decision_required": True,
        },
        "member-ordinary-approval": {
            "candidate_period_applies": True,
            "authority": "ordinary-approval",
            "approval_evidence_required": True,
            "allowed_from_phase": "F1-early-institution",
        },
    },
    "state_transition_contract": {
        "content_addressed_records_required": True,
        "registry_edit_alone_cannot_change_voting_state": True,
        "historical_state_must_be_reconstructable": True,
        "historical_phase_authority_required": True,
        "process_evidence_must_bind_exact_transition_payload": True,
        "process_evidence_completed_no_later_than_decision_date": True,
        "process_supporting_evidence_captured_no_later_than_completion": True,
        "resignation_signature_no_later_than_decision_date": True,
        "approval_backed_removal_effective_after_voting_window_open": True,
        "supported_transition_types": {
            "resignation",
            "inactivity",
            "suspension",
            "reactivation",
            "termination",
        },
        "f1_plus_termination_authority": "qualified-approval",
        "f0_termination_authority": "founding-steward-signed-decision",
    },
}


def _require_baseline(actual, baseline, label: str) -> None:
    """Require every baseline semantic without forbidding future strengthening."""
    if isinstance(baseline, dict):
        core.require(isinstance(actual, dict), f"{label} must be an object")
        for key, expected in baseline.items():
            core.require(key in actual, f"{label} missing protected field: {key}")
            _require_baseline(actual[key], expected, f"{label}.{key}")
        return
    if isinstance(baseline, set):
        core.require(isinstance(actual, (list, tuple, set)), f"{label} must be a collection")
        core.require(baseline.issubset(set(actual)), f"{label} removes protected values")
        return
    core.require(actual == baseline, f"{label} protected value changed")


def _require_fraction_floor(spec: object, *, field_type: str, numerator: int, denominator: int, label: str) -> None:
    core.require(isinstance(spec, dict), f"{label} ratio missing")
    core.require(spec.get("type") == field_type, f"{label} ratio type changed")
    comparison = spec.get("comparison")
    core.require(comparison in {"at_least", "strictly_greater_than"}, f"{label} comparison invalid")
    value_num = spec.get("numerator")
    value_den = spec.get("denominator")
    core.require(
        isinstance(value_num, int)
        and isinstance(value_den, int)
        and value_num >= 0
        and value_den > 0,
        f"{label} ratio must use positive integer denominator",
    )
    core.require(value_num * denominator >= numerator * value_den, f"{label} falls below constitutional floor")


def validate_historical_rule_semantics(rules: object, label: str) -> None:
    """Apply constitutional/anti-capture floors to every immutable rule snapshot.

    A content-addressed predecessor is not authority merely because its JSON is
    structurally valid. Descendant releases may consume it only if the snapshot
    preserves the same minimum democratic and Mission-Lock safeguards enforced
    for the current projection. Stronger later rules are allowed, but a release
    cannot smuggle a weak historical snapshot into the ancestry and restore the
    current values after the weak vote has already authorized a descendant.
    """
    core.require(isinstance(rules, dict), f"{label} rules snapshot must be an object")
    by_id = core.rule_by_id(rules)
    expected_ids = {
        "ordinary-approval",
        "qualified-approval",
        "constitutional-amendment",
        "mission-locked-amendment",
    }
    core.require(set(by_id) == expected_ids, f"{label} decision-rule set incomplete/unexpected")

    ordinary = by_id["ordinary-approval"]
    qualified = by_id["qualified-approval"]
    constitutional = by_id["constitutional-amendment"]
    mission = by_id["mission-locked-amendment"]

    core.require(
        ordinary.get("quorum")
        == {
            "type": "fraction_of_effective_eligible",
            "comparison": "strictly_greater_than",
            "numerator": 1,
            "denominator": 2,
        },
        f"{label} Ordinary Approval quorum changed",
    )
    core.require(
        ordinary.get("approval") == {"type": "votes_for_vs_against", "comparison": "strictly_greater_than"},
        f"{label} Ordinary Approval rule changed",
    )
    _require_fraction_floor(
        qualified.get("quorum"),
        field_type="fraction_of_effective_eligible",
        numerator=2,
        denominator=3,
        label=f"{label} Qualified quorum",
    )
    _require_fraction_floor(
        qualified.get("approval"),
        field_type="fraction_of_valid_for_against",
        numerator=2,
        denominator=3,
        label=f"{label} Qualified approval",
    )
    _require_fraction_floor(
        constitutional.get("quorum"),
        field_type="fraction_of_effective_eligible",
        numerator=2,
        denominator=3,
        label=f"{label} Constitutional quorum",
    )
    _require_fraction_floor(
        constitutional.get("approval"),
        field_type="fraction_of_valid_for_against",
        numerator=3,
        denominator=4,
        label=f"{label} Constitutional approval",
    )
    _require_fraction_floor(
        mission.get("quorum"),
        field_type="fraction_of_effective_eligible",
        numerator=3,
        denominator=4,
        label=f"{label} Mission-Locked quorum",
    )
    _require_fraction_floor(
        mission.get("approval"),
        field_type="fraction_of_valid_for_against",
        numerator=9,
        denominator=10,
        label=f"{label} Mission-Locked approval",
    )

    for rule_id, rule in by_id.items():
        core.require(rule.get("abstentions_count_toward_approval") is False, f"{label} {rule_id} abstention semantics weakened")
        core.require(rule.get("zero_valid_for_against_result") == "fail", f"{label} {rule_id} zero-vote result must fail closed")
        core.require(
            isinstance(rule.get("minimum_affirmative_votes"), int) and rule["minimum_affirmative_votes"] >= 1,
            f"{label} {rule_id} minimum affirmative-vote floor weakened",
        )

    classification = mission.get("classification")
    core.require(
        isinstance(classification, dict)
        and classification.get("trigger")
        == "any_operative_effect_alters_weakens_removes_excepts_or_bypasses_mission_lock_invariant"
        and classification.get("bundled_or_secondary_effects_included") is True
        and classification.get("proposal_label_cannot_downgrade") is True,
        f"{label} Mission-Lock classification weakened",
    )
    core.require(
        isinstance(mission.get("successful_votes_required"), int) and mission["successful_votes_required"] >= 2,
        f"{label} Mission-Locked repeated-vote count weakened",
    )
    core.require(
        isinstance(mission.get("minimum_days_between_successful_votes"), int)
        and mission["minimum_days_between_successful_votes"] >= 60,
        f"{label} Mission-Locked vote-separation floor weakened",
    )
    phases = mission.get("guardian_consent_required_in_phases")
    core.require(
        isinstance(phases, list)
        and {"F0-founder-led-bootstrap", "F1-early-institution"}.issubset(set(phases)),
        f"{label} Founding-Period guardian-consent scope weakened",
    )
    core.require(
        mission.get("founding_period_ends_on_valid_transition_to_phase") == "F2-distributed-institution"
        and mission.get("independent_review_required") is True,
        f"{label} Mission-Locked Founding-Period/review safeguards weakened",
    )

    mandatory = rules.get("mandatory_qualified_subjects")
    core.require(
        isinstance(mandatory, list) and MANDATORY_QUALIFIED_SUBJECTS_FLOOR.issubset(set(mandatory)),
        f"{label} mandatory Qualified Approval subject set weakened",
    )
    mission_subjects = rules.get("mission_locked_subjects")
    core.require(
        isinstance(mission_subjects, list)
        and invariants.MISSION_LOCKED_SUBJECTS_V1.issubset(set(mission_subjects)),
        f"{label} Mission-Lock subject set weakened",
    )
    conflicts = rules.get("conflict_rules")
    _require_baseline(
        conflicts,
        {
            "self_compensation_recusal_required": True,
            "self_contract_approval_prohibited": True,
            "conflicted_voters_excluded_from_effective_eligible_denominator": True,
            "funding_does_not_create_governance_rights": True,
            "founder_status_does_not_override_conflict_recusal": True,
        },
        f"{label} conflict/anti-capture rules",
    )


def validate_historical_membership_semantics(policy: object, label: str) -> None:
    """Preserve anti-capture and authenticated-voting floors in every snapshot."""
    core.require(isinstance(policy, dict), f"{label} membership policy missing")
    core.require(policy.get("one_person_one_vote") is True, f"{label} cannot weaken one-person-one-vote")
    core.require(policy.get("natural_person_voting_members_only") is True, f"{label} cannot weaken natural-person voting membership")
    candidate_days = policy.get("candidate_period_days")
    core.require(isinstance(candidate_days, int) and candidate_days >= 30, f"{label} Candidate-period floor weakened")
    seasoning = policy.get("voting_seasoning_days")
    required_seasoning = {
        "ordinary-approval": 30,
        "qualified-approval": 90,
        "constitutional-amendment": 90,
        "mission-locked-amendment": 180,
    }
    core.require(isinstance(seasoning, dict) and set(seasoning) == set(required_seasoning), f"{label} voting seasoning policy incomplete/unexpected")
    for rule_id, floor in required_seasoning.items():
        value = seasoning.get(rule_id)
        core.require(isinstance(value, int) and value >= floor, f"{label} {rule_id} seasoning floor weakened")

    for contract_name, baseline in MEMBERSHIP_POLICY_BASELINE.items():
        _require_baseline(policy.get(contract_name), baseline, f"{label} {contract_name}")


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
    validate_historical_rule_semantics(rules, f"{label} decision rules")
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
    validate_historical_membership_semantics(snapshot.get("membership_policy"), f"{label} membership policy")
    validate_historical_rule_semantics(rules, f"{label} decision rules")
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
