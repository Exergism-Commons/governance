from __future__ import annotations

import copy
from datetime import date

import validate_governance as core
import governance_release_lifecycle as release_lifecycle
import governance_release_history as release_history
import governance_guardian_consent as guardian_consent


AMENDMENT_KINDS = {"constitutional-amendment", "mission-locked-amendment"}
ORIG_VALIDATE_ADOPTION_RECORD = release_lifecycle.validate_adoption_record
ORIG_VALIDATE_CLASSIFICATION = release_lifecycle._validate_classification

MEMBERSHIP_POLICY_KEYS = (
    "one_person_one_vote",
    "natural_person_voting_members_only",
    "candidate_period_days",
    "voting_seasoning_days",
    "voting_window_contract",
    "voting_window_authenticity_contract",
    "ballot_authentication_contract",
    "ballot_proposal_binding_contract",
    "conflict_determination_contract",
    "f0_signature_chronology_contract",
    "admission_modes",
    "state_transition_contract",
)


def require_authority_provenance_contract(status: dict) -> None:
    contract = status.get("authority_provenance_contract")
    core.require(
        contract
        == {
            "release_authority_snapshot_required": True,
            "amendment_authorized_by_predecessor_release": True,
            "proposed_rules_cannot_authorize_their_own_adoption": True,
            "predecessor_activation_processes_control_amendment_vote": True,
            "membership_policy_frozen_in_release_snapshot": True,
            "historical_decisions_use_release_in_force": True,
            "approval_ballots_bind_predecessor_authority": True,
            "approval_ballots_bind_proposed_release_payload": True,
        },
        "governance authority-provenance contract missing/weakened",
    )


def _load_adoption(ref, label: str) -> dict:
    data, _ = core.validate_content_ref(ref, label, "records/adoptions")
    core.require(
        data.get("record_type") == "governance-adoption" and data.get("status") == "adopted",
        f"{label} must be an adopted governance-adoption",
    )
    return data


def membership_policy_projection(membership: dict) -> dict:
    policy: dict = {}
    for key in MEMBERSHIP_POLICY_KEYS:
        core.require(key in membership, f"membership policy field missing: {key}")
        policy[key] = copy.deepcopy(membership[key])
    return policy


def _validate_membership_policy(policy: object, label: str) -> dict:
    core.require(isinstance(policy, dict), f"{label} membership_policy missing")
    core.require(set(policy) == set(MEMBERSHIP_POLICY_KEYS), f"{label} membership_policy fields incomplete/unexpected")
    core.require(policy.get("one_person_one_vote") is True, f"{label} cannot weaken one-person-one-vote")
    core.require(policy.get("natural_person_voting_members_only") is True, f"{label} cannot weaken natural-person voting membership")
    candidate_days = policy.get("candidate_period_days")
    core.require(isinstance(candidate_days, int) and candidate_days >= 0, f"{label} candidate period invalid")
    seasoning = policy.get("voting_seasoning_days")
    core.require(isinstance(seasoning, dict), f"{label} voting seasoning policy invalid")
    core.require(
        set(seasoning) == {"ordinary-approval", "qualified-approval", "constitutional-amendment", "mission-locked-amendment"}
        and all(isinstance(value, int) and value >= 0 for value in seasoning.values()),
        f"{label} voting seasoning policy incomplete/invalid",
    )
    return policy


def membership_under_snapshot(membership: dict, snapshot: dict, label: str) -> dict:
    projected = copy.deepcopy(membership)
    policy = _validate_membership_policy(snapshot.get("membership_policy"), label)
    for key in MEMBERSHIP_POLICY_KEYS:
        projected[key] = copy.deepcopy(policy[key])
    return projected


def _validate_rules_snapshot(ref, adoption: dict, label: str) -> dict:
    rules, _ = core.validate_content_ref(ref, label, "records/snapshots")
    bindings = adoption.get("normative_machine_bindings")
    core.require(isinstance(bindings, dict), f"{label} authority adoption lacks normative bindings")
    expected_hash = bindings.get("policy/decision-rules.json")
    core.require(
        isinstance(ref, dict) and ref.get("sha256") == expected_hash,
        f"{label} must be the exact decision-rules bytes bound by its governance adoption",
    )
    core.require(rules.get("governance_version") == adoption.get("governance_version"), f"{label} governance version mismatch")
    core.require(rules.get("operative") is True, f"{label} must represent operative governance rules")
    by_id = core.rule_by_id(rules)
    core.require(AMENDMENT_KINDS.issubset(set(by_id)), f"{label} lacks protected amendment rules")
    return rules


def validate_authority_snapshot(ref, adoption: dict, label: str) -> tuple[dict, dict]:
    snapshot, _ = core.validate_content_ref(ref, label, "records/snapshots")
    required = {
        "record_type",
        "status",
        "governance_version",
        "effective_date",
        "decision_rules_snapshot",
        "membership_policy",
        "activation_evidence",
    }
    core.require(set(snapshot) == required, f"{label} fields incomplete/unexpected")
    core.require(
        snapshot["record_type"] == "governance-authority-snapshot" and snapshot["status"] == "final",
        f"{label} must be a final governance-authority-snapshot",
    )
    core.require(snapshot["governance_version"] == adoption.get("governance_version"), f"{label} version mismatch")
    core.require(snapshot["effective_date"] == adoption.get("effective_date"), f"{label} effective-date mismatch")
    _validate_membership_policy(snapshot.get("membership_policy"), label)

    rules = _validate_rules_snapshot(snapshot["decision_rules_snapshot"], adoption, f"{label} decision rules")

    activation = snapshot["activation_evidence"]
    adoption_hashes = adoption.get("activation_evidence_hashes")
    core.require(isinstance(activation, dict) and isinstance(adoption_hashes, dict), f"{label} activation authority missing")
    core.require(set(activation) == set(adoption_hashes), f"{label} activation authority set mismatch")
    for key, evidence_ref in activation.items():
        core.require(isinstance(evidence_ref, dict), f"{label} activation authority missing: {key}")
        core.require(
            evidence_ref.get("sha256") == adoption_hashes[key],
            f"{label} activation authority does not match adoption binding: {key}",
        )
        core.validate_content_ref(evidence_ref, f"{label} activation authority {key}", "records/evidence")
    return snapshot, rules


def authority_context_for_release(status: dict, adoption: dict, adoption_ref: dict, label: str) -> tuple[dict, dict, dict, dict]:
    snapshot_ref = adoption.get("authority_snapshot")
    core.require(isinstance(snapshot_ref, dict), f"{label} lacks immutable authority snapshot")
    snapshot, rules = validate_authority_snapshot(snapshot_ref, adoption, f"{label} authority snapshot")
    authority_status = copy.deepcopy(status)
    authority_status["governance_version"] = adoption["governance_version"]
    authority_status["effective_date"] = adoption["effective_date"]
    authority_status["adoption_record"] = adoption_ref
    authority_status["activation_evidence"] = snapshot["activation_evidence"]
    return authority_status, rules, adoption, adoption_ref


def authority_context_as_of(status: dict, target: date) -> tuple[dict, dict, dict, dict]:
    """Resolve the exact release and machine authority that was operative on target."""
    require_authority_provenance_contract(status)
    core.require(status.get("operative") is True, "historical authority requires operative governance")
    adoption, adoption_ref = release_history.release_as_of(status, target)
    return authority_context_for_release(
        status,
        adoption,
        adoption_ref,
        f"governance release #{adoption['release_sequence']} as of {target.isoformat()}",
    )


def membership_context_as_of(status: dict, membership: dict, target: date) -> dict:
    authority_status, _, adoption, _ = authority_context_as_of(status, target)
    snapshot, _ = validate_authority_snapshot(
        adoption["authority_snapshot"],
        adoption,
        f"membership authority as of {target.isoformat()}",
    )
    projected = membership_under_snapshot(membership, snapshot, f"membership authority as of {target.isoformat()}")
    projected["governance_version"] = authority_status["governance_version"]
    return projected


def current_authority_snapshot(status: dict) -> tuple[dict, dict, dict]:
    require_authority_provenance_contract(status)
    core.require(status.get("operative") is True, "authority snapshot exists only for operative governance")
    chain = release_history.release_chain(status)
    core.require(chain, "operative governance release chain required")
    adoption, ref = chain[-1]
    _, rules, _, _ = authority_context_for_release(status, adoption, ref, "current governance release")
    snapshot, _ = validate_authority_snapshot(adoption["authority_snapshot"], adoption, "current governance authority snapshot")
    return adoption, snapshot, rules


def predecessor_authority_context(status: dict) -> tuple[dict, dict, dict, dict]:
    require_authority_provenance_contract(status)
    chain = release_history.release_chain(status)
    core.require(len(chain) >= 2, "predecessor authority exists only for later releases")
    predecessor, previous_ref = chain[-2]
    contract = status["governance_release_contract"]
    core.require(contract.get("previous_adoption_record") == previous_ref, "release contract predecessor mismatch")
    return authority_context_for_release(status, predecessor, previous_ref, "predecessor governance release")


def _proposed_release_bindings(status: dict) -> dict[str, str]:
    adoption = _load_adoption(status.get("adoption_record"), "proposed governance amendment adoption")
    release = status.get("governance_release_contract")
    core.require(isinstance(release, dict), "governance release contract required")
    sequence = release.get("current_release_sequence")
    kind = release.get("current_release_kind")
    core.require(isinstance(sequence, int) and sequence >= 2 and kind in AMENDMENT_KINDS, "proposed release binding requires a later governance amendment")
    core.require(adoption.get("release_sequence") == sequence and adoption.get("release_kind") == kind, "proposed release metadata mismatch")

    _, amendment_hash = release_lifecycle._amendment_payload(adoption)
    core.require(
        adoption.get("amendment_payload_sha256") == amendment_hash,
        "proposed governance amendment payload hash mismatch before voting",
    )

    snapshot_ref = adoption.get("authority_snapshot")
    core.require(isinstance(snapshot_ref, dict), "proposed governance release must bind its authority snapshot before voting")
    proposed_snapshot_sha = core.require_sha256(snapshot_ref.get("sha256"), "proposed authority snapshot sha256")

    normative = adoption.get("normative_machine_bindings")
    core.require(isinstance(normative, dict), "proposed governance release normative machine bindings required")
    proposed_rules_sha = core.require_sha256(
        normative.get("policy/decision-rules.json"),
        "proposed decision-rules sha256",
    )

    snapshot, _ = validate_authority_snapshot(snapshot_ref, adoption, "proposed governance authority snapshot")
    proposed_membership = core.load_json("policy/membership-status.json")
    core.require(
        snapshot.get("membership_policy") == membership_policy_projection(proposed_membership),
        "proposed authority snapshot must bind the exact proposed membership policy",
    )

    return {
        "governance_amendment_payload_sha256": amendment_hash,
        "proposed_authority_snapshot_sha256": proposed_snapshot_sha,
        "proposed_decision_rules_sha256": proposed_rules_sha,
    }


def _authority_bound_artifacts(status: dict, bindings: dict | None) -> dict:
    core.require(isinstance(bindings, dict) and bindings, "amendment approval requires exact proposed artifact bindings")
    _, _, predecessor, previous_ref = predecessor_authority_context(status)
    snapshot_ref = predecessor.get("authority_snapshot")
    result = dict(bindings)
    result["authority_predecessor_adoption_sha256"] = previous_ref["sha256"]
    result["authority_predecessor_snapshot_sha256"] = snapshot_ref["sha256"]
    result.update(_proposed_release_bindings(status))
    return result


def _approval_decision_date(ref, expected_decision_date: str | None, label: str) -> date:
    if expected_decision_date is not None:
        return core.parse_iso_date(expected_decision_date, f"{label} expected decision_date")
    data, _ = core.validate_content_ref(ref, f"{label} authority-date envelope", "records/evidence")
    return core.parse_iso_date(data.get("decision_date"), f"{label} decision_date")


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
    if status.get("operative") is not True:
        return release_lifecycle.validate_approval_evidence(
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

    release = status.get("governance_release_contract")
    sequence = release.get("current_release_sequence") if isinstance(release, dict) else None
    initial_governance_adoption = label == "governance adoption approval" and sequence == 1
    if initial_governance_adoption:
        return release_lifecycle.validate_approval_evidence(
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

    decision_date = _approval_decision_date(ref, expected_decision_date, label)
    authority_status, authority_rules, authority_adoption, authority_ref = authority_context_as_of(status, decision_date)
    authority_snapshot, _ = validate_authority_snapshot(
        authority_adoption["authority_snapshot"],
        authority_adoption,
        f"{label} membership authority snapshot",
    )
    authority_membership = membership_under_snapshot(membership, authority_snapshot, f"{label} membership authority")
    authority_membership["governance_version"] = authority_status["governance_version"]

    protected_current_amendment = (
        isinstance(sequence, int)
        and sequence >= 2
        and expected_rule_id in AMENDMENT_KINDS
        and authority_adoption.get("release_sequence") == sequence - 1
    )
    later_governance_adoption = (
        label == "governance adoption approval"
        and isinstance(sequence, int)
        and sequence >= 2
    )

    rule_id = expected_rule_id
    bindings = expected_artifact_bindings
    if later_governance_adoption or protected_current_amendment:
        core.require(authority_ref == status["governance_release_contract"]["previous_adoption_record"], "governance amendment vote must be authorized by exact predecessor release")
        rule_id = release.get("current_release_kind") if later_governance_adoption else expected_rule_id
        core.require(rule_id in AMENDMENT_KINDS, "later governance adoption must use predecessor amendment authority")
        bindings = _authority_bound_artifacts(status, expected_artifact_bindings)

    return release_lifecycle.ORIG_VALIDATE_APPROVAL_EVIDENCE(
        ref,
        label,
        expected_decision_id,
        authority_status,
        authority_rules,
        authority_membership,
        expected_rule_id=rule_id,
        expected_artifact_bindings=bindings,
        expected_decision_date=expected_decision_date,
        allow_constitutive=False,
        legal_entity=legal_entity,
        expected_signed_payload_sha256=expected_signed_payload_sha256,
    )


def validate_classification(
    ref,
    status: dict,
    legal_entity: dict,
    human_hashes: dict[str, str],
    previous_ref: dict,
    release_kind: str,
    decision_id: str,
    amendment_payload_sha256: str,
    first_vote_date,
    final_vote_date,
):
    authority_status, _, _, authoritative_previous_ref = predecessor_authority_context(status)
    core.require(previous_ref == authoritative_previous_ref, "amendment classification predecessor authority mismatch")
    return ORIG_VALIDATE_CLASSIFICATION(
        ref,
        authority_status,
        legal_entity,
        human_hashes,
        previous_ref,
        release_kind,
        decision_id,
        amendment_payload_sha256,
        first_vote_date,
        final_vote_date,
    )


def validate_guardian_consent(
    ref,
    status: dict,
    decision_id: str,
    amendment_payload_sha256: str,
    first_vote_date,
    final_vote_date,
) -> None:
    authority_status, _, _, _ = predecessor_authority_context(status)
    guardian_consent.validate_guardian_consent(
        ref,
        authority_status,
        decision_id,
        amendment_payload_sha256,
        first_vote_date,
        final_vote_date,
    )


def validate_adoption_record(
    status: dict,
    activation_hashes: dict[str, str],
    rules: dict,
    membership: dict,
    legal_entity: dict | None,
    human_hashes: dict[str, str],
) -> None:
    require_authority_provenance_contract(status)
    result = ORIG_VALIDATE_ADOPTION_RECORD(status, activation_hashes, rules, membership, legal_entity, human_hashes)
    if status.get("operative") is not True:
        return result

    chain = release_history.release_chain(status)
    adoption, snapshot, current_rules = current_authority_snapshot(status)
    core.require(
        current_rules.get("governance_version") == status.get("governance_version"),
        "current authority snapshot must establish the current governance version",
    )
    core.require(
        snapshot.get("membership_policy") == membership_policy_projection(membership),
        "current authority snapshot must bind the exact current membership policy",
    )
    sequence = status["governance_release_contract"]["current_release_sequence"]
    if sequence == 1:
        core.require(adoption.get("previous_adoption_record") is None, "release #1 authority cannot have a predecessor")
    else:
        _, _, predecessor, previous_ref = predecessor_authority_context(status)
        core.require(adoption.get("previous_adoption_record") == previous_ref, "current release authority predecessor mismatch")
        core.require(chain[-2][0] == predecessor and chain[-2][1] == previous_ref, "predecessor authority diverges from release history")
        core.require(
            core.parse_iso_date(predecessor.get("effective_date"), "predecessor governance effective_date")
            < core.parse_iso_date(status.get("effective_date"), "current governance effective_date"),
            "later governance release must become effective after its predecessor",
        )
    return result
