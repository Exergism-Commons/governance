from __future__ import annotations

import copy
from datetime import date

import governance_guardian_consent as guardian_consent
import governance_membership_roster as membership_roster
import governance_release_authority as authority
import governance_release_history as history
import governance_release_lifecycle as lifecycle
import validate_governance as core


INITIAL_KIND = "initial-constitutive-adoption"
CONSTITUTIONAL_KIND = "constitutional-amendment"
MISSION_KIND = "mission-locked-amendment"
AMENDMENT_KINDS = {CONSTITUTIONAL_KIND, MISSION_KIND}
MISSION_VOTE_SEPARATION_FLOOR_DAYS = 60
SUPPORTED_MISSION_SUCCESSFUL_VOTES = 2


def _status_at_release(status: dict, chain: list[tuple[dict, dict]], index: int) -> dict:
    """Project a self-consistent release prefix instead of mixing current/history.

    Historical authority helpers frequently consult both status.adoption_record
    and governance_release_contract. Changing only one creates exactly the kind
    of current-state leakage that adversarial sequence-3 fixtures exploit.
    """
    record, ref = chain[index]
    projected = copy.deepcopy(status)
    contract = copy.deepcopy(status["governance_release_contract"])
    contract["current_release_sequence"] = record["release_sequence"]
    contract["current_release_kind"] = record["release_kind"]
    contract["founding_adoption_record"] = chain[0][1]
    contract["previous_adoption_record"] = None if index == 0 else chain[index - 1][1]
    projected["governance_release_contract"] = contract
    projected["governance_version"] = record["governance_version"]
    projected["effective_date"] = record["effective_date"]
    projected["adoption_record"] = ref
    if isinstance(record.get("governing_law"), str):
        projected["governing_law"] = record["governing_law"]
    if isinstance(record.get("legal_entity"), dict):
        projected["legal_entity"] = copy.deepcopy(record["legal_entity"])
    return projected


def _phase_as_of(status: dict, target: date) -> str:
    phase_evidence = core.load_json("policy/phase-evidence.json")
    timeline = history.phase_timeline(status, phase_evidence)
    core.require(timeline, "historical release proof requires an institutional phase timeline")
    selected = timeline[0][1]
    for effective, phase in timeline:
        if effective > target:
            break
        selected = phase
    return selected


def _require_adoption_chronology(record: dict, approval: dict, label: str) -> tuple[date, date, date]:
    decision = core.parse_iso_date(record.get("decision_date"), f"{label} decision_date")
    completed = core.parse_iso_date(record.get("completed_date"), f"{label} completed_date")
    effective = core.parse_iso_date(record.get("effective_date"), f"{label} effective_date")
    core.require(decision <= completed <= effective, f"{label} adoption chronology invalid")
    core.require(approval.get("decision_date") == record.get("decision_date"), f"{label} approval/adoption decision date mismatch")
    return decision, completed, effective


def historical_mission_vote_separation_days(authority_rules: dict, label: str) -> int:
    """Resolve repeated-vote semantics from the predecessor authority itself.

    The current v1 release-record schema represents exactly two successful
    Mission-Locked votes: one `first_vote_approval_evidence` plus the final
    `approval_evidence`. A future rule that legitimately requires three or more
    votes must therefore bump the release-record schema and add an authenticated
    vote-sequence representation before such a rule can become authority. This
    avoids accepting a stronger declarative rule that the proof format cannot
    actually prove.

    The separation interval itself may be strengthened prospectively. Re-proving
    an older release uses the predecessor's own interval, while retaining the
    immutable 60-day constitutional floor.
    """
    mission = core.rule_by_id(authority_rules).get(MISSION_KIND)
    core.require(isinstance(mission, dict), f"{label} Mission-Locked rule missing")
    core.require(
        mission.get("successful_votes_required") == SUPPORTED_MISSION_SUCCESSFUL_VOTES,
        f"{label} Mission-Locked successful-vote count is unsupported by release-record schema; schema upgrade required",
    )
    days = mission.get("minimum_days_between_successful_votes")
    core.require(
        isinstance(days, int) and days >= MISSION_VOTE_SEPARATION_FLOOR_DAYS,
        f"{label} Mission-Locked vote-separation authority weakened",
    )
    return days


def _validate_constitutive_release(
    status: dict,
    chain: list[tuple[dict, dict]],
    membership: dict,
) -> None:
    record, _ = chain[0]
    label = "governance release #1"
    core.require(record.get("release_kind") == INITIAL_KIND, "release #1 must remain constitutive")
    core.require(record.get("previous_adoption_record") is None, "release #1 cannot have a predecessor")
    core.require(record.get("founding_adoption_record") is None, "release #1 cannot self-reference its future content address")

    projected = _status_at_release(status, chain, 0)
    legal_entity = record.get("legal_entity")
    human_hashes = record.get("artifact_bindings")
    core.require(isinstance(legal_entity, dict) and legal_entity, f"{label} legal entity missing")
    core.require(isinstance(human_hashes, dict) and human_hashes, f"{label} artifact bindings missing")

    payload = {key: value for key, value in record.items() if key not in {"approval_evidence", "constitutive_payload_sha256"}}
    payload_hash = core.sha256_json(payload)
    core.require(record.get("constitutive_payload_sha256") == payload_hash, f"{label} constitutive payload hash mismatch")

    approval, _ = core.validate_content_ref(record.get("approval_evidence"), f"{label} approval", "records/evidence")
    core.require(approval.get("approval_mode") == "constitutive-adoption", f"{label} must use constitutive adoption")
    _, completed, effective = _require_adoption_chronology(record, approval, label)
    core.require(approval.get("completed_date") == record.get("completed_date"), f"{label} constitutive approval completion mismatch")

    lifecycle.ORIG_VALIDATE_APPROVAL_EVIDENCE(
        record.get("approval_evidence"),
        f"{label} full approval proof",
        record.get("decision_id"),
        projected,
        {},
        membership,
        expected_artifact_bindings=human_hashes,
        allow_constitutive=True,
        legal_entity=legal_entity,
        expected_signed_payload_sha256=payload_hash,
    )

    signatures = approval.get("signature_evidence")
    core.require(isinstance(signatures, list) and signatures, f"{label} constitutive signatures required")
    for index, ref in enumerate(signatures):
        signature, _ = core.validate_content_ref(ref, f"{label} signature chronology {index}", "records/evidence")
        signed = core.parse_iso_date(signature.get("signed_date"), f"{label} signature {index}.signed_date")
        core.require(signed <= completed <= effective, f"{label} constitutive signature postdates adoption")

    # The immutable release payload also checkpoints the complete Member roster
    # and transition history existing by its effective date. A later mutable
    # projection may append Members/transitions but cannot prune this checkpoint.
    membership_roster.validate_release_roster_snapshot(record, membership, label)

    # A descendant may use this release only after its signed adoption and its
    # exact authority snapshot have both validated.
    authority.validate_authority_snapshot(record.get("authority_snapshot"), record, f"{label} authority snapshot")


def _authority_bound_artifacts(record: dict, predecessor: dict, previous_ref: dict) -> dict:
    human = record.get("artifact_bindings")
    core.require(isinstance(human, dict) and human, "historical governance amendment artifact bindings missing")
    _, amendment_hash = lifecycle._amendment_payload(record)
    core.require(record.get("amendment_payload_sha256") == amendment_hash, "historical governance amendment payload hash mismatch")

    predecessor_snapshot = predecessor.get("authority_snapshot")
    proposed_snapshot = record.get("authority_snapshot")
    normative = record.get("normative_machine_bindings")
    core.require(isinstance(predecessor_snapshot, dict), "historical predecessor authority snapshot missing")
    core.require(isinstance(proposed_snapshot, dict), "historical proposed authority snapshot missing")
    core.require(isinstance(normative, dict), "historical proposed normative bindings missing")

    result = dict(human)
    result["authority_predecessor_adoption_sha256"] = core.require_sha256(previous_ref.get("sha256"), "historical predecessor adoption sha256")
    result["authority_predecessor_snapshot_sha256"] = core.require_sha256(predecessor_snapshot.get("sha256"), "historical predecessor snapshot sha256")
    result["governance_amendment_payload_sha256"] = amendment_hash
    result["proposed_authority_snapshot_sha256"] = core.require_sha256(proposed_snapshot.get("sha256"), "historical proposed snapshot sha256")
    result["proposed_decision_rules_sha256"] = core.require_sha256(normative.get("policy/decision-rules.json"), "historical proposed decision-rules sha256")
    return result


def _validate_amendment_release(
    status: dict,
    chain: list[tuple[dict, dict]],
    index: int,
    membership: dict,
) -> None:
    record, ref = chain[index]
    predecessor, previous_ref = chain[index - 1]
    sequence = record["release_sequence"]
    kind = record.get("release_kind")
    label = f"governance release #{sequence}"

    core.require(sequence == index + 1 and kind in AMENDMENT_KINDS, f"{label} amendment metadata invalid")
    core.require(record.get("decision_class") == kind and record.get("adoption_method") == kind, f"{label} amendment class/method mismatch")
    core.require(record.get("previous_adoption_record") == previous_ref, f"{label} does not bind exact predecessor")
    core.require(record.get("founding_adoption_record") == chain[0][1], f"{label} does not bind permanent founding anchor")
    core.require(
        record.get("first_vote_approval_evidence") is None if kind == CONSTITUTIONAL_KIND else isinstance(record.get("first_vote_approval_evidence"), dict),
        f"{label} repeated-vote shape invalid",
    )

    # Before reconstructing any predecessor electorate, prove that the current
    # mutable registry still contains every Member/admission/transition that the
    # predecessor release immutably checkpointed. This closes roster pruning in
    # sequence-3+ proofs.
    membership_roster.validate_release_roster_snapshot(
        predecessor,
        membership,
        f"{label} predecessor release #{predecessor['release_sequence']}",
    )

    predecessor_status = _status_at_release(status, chain, index - 1)
    authority_status, authority_rules, _, authority_ref = authority.authority_context_for_release(
        predecessor_status,
        predecessor,
        previous_ref,
        f"{label} predecessor authority",
    )
    core.require(authority_ref == previous_ref, f"{label} predecessor authority reference mismatch")
    predecessor_snapshot, _ = authority.validate_authority_snapshot(
        predecessor.get("authority_snapshot"),
        predecessor,
        f"{label} predecessor membership authority",
    )
    authority_membership = authority.membership_under_snapshot(
        membership,
        predecessor_snapshot,
        f"{label} predecessor membership policy",
    )
    authority_membership["governance_version"] = authority_status["governance_version"]

    # Validate both the proposed authority snapshot and the proposed immutable
    # roster checkpoint before allowing this release to authorize descendants.
    authority.validate_authority_snapshot(record.get("authority_snapshot"), record, f"{label} proposed authority snapshot")
    membership_roster.validate_release_roster_snapshot(record, membership, label)

    expected_bindings = _authority_bound_artifacts(record, predecessor, previous_ref)
    human_hashes = record["artifact_bindings"]
    _, amendment_hash = lifecycle._amendment_payload(record)
    legal_entity = record.get("legal_entity")
    core.require(isinstance(legal_entity, dict) and legal_entity, f"{label} legal entity missing")

    final_ref = record.get("approval_evidence")
    final, _ = core.validate_content_ref(final_ref, f"{label} final approval", "records/evidence")
    decision, completed, effective = _require_adoption_chronology(record, final, label)
    final_date = core.parse_iso_date(final.get("decision_date"), f"{label} final vote date")
    core.require(final_date == decision, f"{label} final vote/adoption decision mismatch")
    core.require(final.get("decision_id") == record.get("decision_id"), f"{label} final vote decision mismatch")
    core.require(final.get("decision_class") == kind, f"{label} final vote class mismatch")

    lifecycle.ORIG_VALIDATE_APPROVAL_EVIDENCE(
        final_ref,
        f"{label} full final approval proof",
        record.get("decision_id"),
        authority_status,
        authority_rules,
        authority_membership,
        expected_rule_id=kind,
        expected_artifact_bindings=expected_bindings,
        expected_decision_date=record.get("decision_date"),
    )

    first_date: date | None = None
    if kind == MISSION_KIND:
        minimum_days = historical_mission_vote_separation_days(authority_rules, label)
        first_ref = record["first_vote_approval_evidence"]
        first, _ = core.validate_content_ref(first_ref, f"{label} first Mission-Locked approval", "records/evidence")
        first_id = first.get("decision_id")
        core.require(isinstance(first_id, str) and first_id and first_id != record.get("decision_id"), f"{label} requires two distinct Mission-Locked decisions")
        lifecycle.ORIG_VALIDATE_APPROVAL_EVIDENCE(
            first_ref,
            f"{label} full first approval proof",
            first_id,
            authority_status,
            authority_rules,
            authority_membership,
            expected_rule_id=MISSION_KIND,
            expected_artifact_bindings=expected_bindings,
            expected_decision_date=first.get("decision_date"),
        )
        first_date = core.parse_iso_date(first.get("decision_date"), f"{label} first vote date")
        core.require((final_date - first_date).days >= minimum_days, f"{label} Mission-Locked vote separation insufficient")

    review_completed = authority.ORIG_VALIDATE_CLASSIFICATION(
        record.get("amendment_classification_evidence"),
        authority_status,
        legal_entity,
        human_hashes,
        previous_ref,
        kind,
        record.get("decision_id"),
        amendment_hash,
        first_date,
        final_date,
    )

    if kind == MISSION_KIND:
        core.require(first_date is not None and first_date <= review_completed <= final_date, f"{label} independent review chronology invalid")
        historical_phase = _phase_as_of(status, final_date)
        required_phases = set(core.rule_by_id(authority_rules)[MISSION_KIND]["guardian_consent_required_in_phases"])
        if historical_phase in required_phases:
            consent_ref = record.get("guardian_consent_evidence")
            core.require(isinstance(consent_ref, dict), f"{label} requires Founding-Period guardian consent")
            guardian_consent.validate_guardian_consent(
                consent_ref,
                authority_status,
                record.get("decision_id"),
                amendment_hash,
                first_date,
                final_date,
            )
        else:
            core.require(record.get("guardian_consent_evidence") is None, f"{label} cannot fabricate post-Founding guardian consent")
    else:
        core.require(record.get("guardian_consent_evidence") is None, f"{label} Constitutional Amendment cannot claim Mission-Locked consent")

    core.require(final_date <= completed <= effective, f"{label} cannot become effective before ratification")


def validate_release_proof_chain(status: dict, membership: dict) -> None:
    """Inductively prove every release before trusting descendant authority.

    Structural ancestry is necessary but insufficient. Release N+1 may consume
    N's snapshot only after release N's own approval path, activation semantics,
    and immutable Member-roster checkpoint have been fully authenticated under
    release N-1. This defeats fabricated intermediate releases and historical
    roster pruning even when their hashes form a contiguous chain.
    """
    if status.get("operative") is not True:
        return
    chain = history.release_chain(status)
    core.require(chain, "operative governance requires a release proof chain")

    _validate_constitutive_release(status, chain, membership)
    validated_ref = chain[0][1]
    for index in range(1, len(chain)):
        core.require(chain[index][0].get("previous_adoption_record") == validated_ref, "release proof must advance from the last fully validated predecessor")
        _validate_amendment_release(status, chain, index, membership)
        validated_ref = chain[index][1]

    core.require(validated_ref == status.get("adoption_record"), "release proof chain does not terminate at current governance adoption")
