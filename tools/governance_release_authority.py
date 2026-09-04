from __future__ import annotations

import copy

import validate_governance as core
import governance_release_lifecycle as release_lifecycle
import governance_guardian_consent as guardian_consent


AMENDMENT_KINDS = {"constitutional-amendment", "mission-locked-amendment"}
ORIG_VALIDATE_ADOPTION_RECORD = release_lifecycle.validate_adoption_record
ORIG_VALIDATE_CLASSIFICATION = release_lifecycle._validate_classification


def require_authority_provenance_contract(status: dict) -> None:
    contract = status.get("authority_provenance_contract")
    core.require(
        contract
        == {
            "release_authority_snapshot_required": True,
            "amendment_authorized_by_predecessor_release": True,
            "proposed_rules_cannot_authorize_their_own_adoption": True,
            "predecessor_activation_processes_control_amendment_vote": True,
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
    core.require(rules.get("operative") is True, f"{label} must represent operative predecessor rules")
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
        "activation_evidence",
    }
    core.require(set(snapshot) == required, f"{label} fields incomplete/unexpected")
    core.require(
        snapshot["record_type"] == "governance-authority-snapshot" and snapshot["status"] == "final",
        f"{label} must be a final governance-authority-snapshot",
    )
    core.require(snapshot["governance_version"] == adoption.get("governance_version"), f"{label} version mismatch")
    core.require(snapshot["effective_date"] == adoption.get("effective_date"), f"{label} effective-date mismatch")

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


def current_authority_snapshot(status: dict) -> tuple[dict, dict, dict]:
    require_authority_provenance_contract(status)
    core.require(status.get("operative") is True, "authority snapshot exists only for operative governance")
    adoption = _load_adoption(status.get("adoption_record"), "current governance authority adoption")
    ref = adoption.get("authority_snapshot")
    core.require(isinstance(ref, dict), "every operative governance release must bind an authority snapshot")
    snapshot, rules = validate_authority_snapshot(ref, adoption, "current governance authority snapshot")
    return adoption, snapshot, rules


def predecessor_authority_context(status: dict) -> tuple[dict, dict, dict, dict]:
    require_authority_provenance_contract(status)
    release = status.get("governance_release_contract")
    core.require(isinstance(release, dict), "governance release contract required")
    sequence = release.get("current_release_sequence")
    core.require(isinstance(sequence, int) and sequence >= 2, "predecessor authority exists only for later releases")
    previous_ref = release.get("previous_adoption_record")
    core.require(isinstance(previous_ref, dict), "later governance release requires predecessor adoption")
    predecessor = _load_adoption(previous_ref, "predecessor governance authority adoption")
    core.require(predecessor.get("release_sequence") == sequence - 1, "predecessor authority release sequence mismatch")
    snapshot_ref = predecessor.get("authority_snapshot")
    core.require(isinstance(snapshot_ref, dict), "predecessor release lacks immutable authority snapshot")
    snapshot, rules = validate_authority_snapshot(snapshot_ref, predecessor, "predecessor governance authority snapshot")

    authority_status = copy.deepcopy(status)
    authority_status["governance_version"] = predecessor.get("governance_version")
    authority_status["effective_date"] = predecessor.get("effective_date")
    authority_status["activation_evidence"] = snapshot["activation_evidence"]
    return authority_status, rules, predecessor, previous_ref


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

    # Resolve both proposed machine artifacts now. This prevents ballots from
    # authenticating a human-text-only proposal while the machine authority
    # package is swapped before adoption.
    validate_authority_snapshot(snapshot_ref, adoption, "proposed governance authority snapshot")

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
    release = status.get("governance_release_contract")
    sequence = release.get("current_release_sequence") if isinstance(release, dict) else None
    later_governance_adoption = label == "governance adoption approval" and isinstance(sequence, int) and sequence >= 2
    protected_amendment_vote = expected_rule_id in AMENDMENT_KINDS and isinstance(sequence, int) and sequence >= 2

    if later_governance_adoption or protected_amendment_vote:
        authority_status, authority_rules, _, _ = predecessor_authority_context(status)
        rule_id = release.get("current_release_kind") if later_governance_adoption else expected_rule_id
        core.require(rule_id in AMENDMENT_KINDS, "later governance adoption must use predecessor amendment authority")
        bound_artifacts = _authority_bound_artifacts(status, expected_artifact_bindings)
        return release_lifecycle.ORIG_VALIDATE_APPROVAL_EVIDENCE(
            ref,
            label,
            expected_decision_id,
            authority_status,
            authority_rules,
            membership,
            expected_rule_id=rule_id,
            expected_artifact_bindings=bound_artifacts,
            expected_decision_date=expected_decision_date,
            allow_constitutive=False,
            legal_entity=legal_entity,
            expected_signed_payload_sha256=expected_signed_payload_sha256,
        )

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

    adoption, _, current_rules = current_authority_snapshot(status)
    core.require(
        current_rules.get("governance_version") == status.get("governance_version"),
        "current authority snapshot must establish the current governance version",
    )
    sequence = status["governance_release_contract"]["current_release_sequence"]
    if sequence == 1:
        core.require(adoption.get("previous_adoption_record") is None, "release #1 authority cannot have a predecessor")
    else:
        _, _, predecessor, previous_ref = predecessor_authority_context(status)
        core.require(adoption.get("previous_adoption_record") == previous_ref, "current release authority predecessor mismatch")
        core.require(
            core.parse_iso_date(predecessor.get("effective_date"), "predecessor governance effective_date")
            < core.parse_iso_date(status.get("effective_date"), "current governance effective_date"),
            "later governance release must become effective after its predecessor",
        )
    return result
