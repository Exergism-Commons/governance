from __future__ import annotations

from datetime import date

import governance_temporal_phase as phase
import validate_governance as core


TRANSITION_EVIDENCE_BINDING_CONTRACT = {
    "f1_transition_binds_exact_f1_maturity_evidence_refs": True,
    "f2_transition_binds_exact_f2_maturity_evidence_refs": True,
    "maturity_evidence_refs_are_inside_approved_transition_payload": True,
    "role_replacement_evidence_binds_validated_delegation_lifecycle": True,
}

ROLE_REPLACEMENT_BINDING_FIELDS = {
    "replaced_delegation_id",
    "replacement_delegation_id",
    "replaced_holder_person_id",
    "replacement_holder_person_id",
    "replaced_decision_record",
    "replaced_revocation_record",
    "replacement_decision_record",
    "scope_types",
    "scope_resources",
    "allowed_actions",
}

ORIG_VALIDATE_PHASE_EVIDENCE = phase.validate_phase_evidence
_INSTALLED = False


def _expected_maturity_evidence(phase_evidence: dict, target_phase: str) -> dict:
    if target_phase == "F1-early-institution":
        f1 = phase_evidence.get("f1")
        core.require(isinstance(f1, dict), "F1 maturity projection missing")
        return {
            "independent_role_holder_evidence": f1.get("independent_role_holder_evidence"),
            "delegation_evidence": f1.get("delegation_evidence"),
        }
    if target_phase == "F2-distributed-institution":
        f2 = phase_evidence.get("f2")
        core.require(isinstance(f2, dict), "F2 maturity projection missing")
        return {
            "control_separation_evidence": f2.get("control_separation_evidence"),
            "audit_review_evidence": f2.get("audit_review_evidence"),
            "role_replacement_evidence": f2.get("role_replacement_evidence"),
        }
    raise SystemExit(f"governance integrity failure: unsupported maturity transition target: {target_phase}")


def require_transition_maturity_binding(ref: dict, phase_evidence: dict, target_phase: str, label: str) -> dict:
    """Require the approved phase-transition payload to bind exact maturity evidence.

    Chronologically valid evidence is still mutable selection unless the Member
    vote authenticates the exact content-addressed references.  The transition
    record itself is inside the approval payload, so requiring this mapping
    makes evidence substitution after the vote change the transition digest and
    invalidate the approval.
    """
    record, _ = core.validate_content_ref(ref, label, "records/decisions")
    core.require(
        record.get("record_type") == "phase-transition"
        and record.get("status") == "adopted"
        and record.get("to_phase") == target_phase,
        f"{label} is not the expected adopted phase transition",
    )
    expected = _expected_maturity_evidence(phase_evidence, target_phase)
    core.require(
        all(isinstance(value, dict) and set(value) == {"path", "sha256"} for value in expected.values()),
        f"{label} requires complete content-addressed maturity evidence references",
    )
    core.require(
        record.get("maturity_evidence") == expected,
        f"{label} approved payload does not bind the exact maturity evidence references",
    )
    return record


def _delegation_index(validated_delegations: list[dict]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for item in validated_delegations:
        core.require(isinstance(item, dict), "validated delegation row must be an object")
        delegation_id = item.get("delegation_id")
        core.require(
            isinstance(delegation_id, str) and delegation_id and delegation_id not in result,
            "validated delegation IDs must be non-empty and unique",
        )
        result[delegation_id] = item
    return result


def _load_delegation_event(ref: dict, label: str, expected_type: str) -> dict:
    record, _ = core.validate_content_ref(ref, label, "records/decisions")
    core.require(
        record.get("record_type") == expected_type and record.get("status") == "adopted",
        f"{label} type/status invalid",
    )
    return record


def validate_role_replacement_demonstration(
    ref: dict,
    status: dict,
    phase_evidence: dict,
    founding: dict,
    validated_delegations: list[dict],
    phase_date: date,
    governance_version: str,
) -> dict:
    """Prove that F2 contains a real post-F1 delegated-role replacement.

    A generic process record saying "replacement demonstrated" cannot end the
    Founding Period.  The evidence must bind an immutable grant, its validated
    revocation, and a different validated successor grant for the same role.
    Both lifecycle decisions must occur after F1 has actually begun, so the
    demonstration uses normal Member-governed delegation authority rather than
    obsolete F0 founder-only bootstrap authority.
    """
    evidence = core.validate_process_evidence_ref(
        ref,
        "F2 role replacement",
        "role-replacement-evidence",
        governance_version,
        "f2-role-replacement",
    )
    core.require(
        evidence.get("as_of_date") == phase_date.isoformat(),
        "F2 role replacement evidence must bind exact F2 phase-effective date",
    )
    binding = evidence.get("role_replacement_binding")
    core.require(
        isinstance(binding, dict) and set(binding) == ROLE_REPLACEMENT_BINDING_FIELDS,
        "F2 role replacement evidence binding fields incomplete/unexpected",
    )

    by_id = _delegation_index(validated_delegations)
    replaced_id = binding.get("replaced_delegation_id")
    replacement_id = binding.get("replacement_delegation_id")
    core.require(
        isinstance(replaced_id, str)
        and isinstance(replacement_id, str)
        and replaced_id != replacement_id,
        "F2 role replacement requires two distinct delegation IDs",
    )
    replaced = by_id.get(replaced_id)
    replacement = by_id.get(replacement_id)
    core.require(replaced is not None and replacement is not None, "F2 role replacement references unknown delegation")

    replaced_holder = replaced.get("holder_person_id")
    replacement_holder = replacement.get("holder_person_id")
    founder_id = founding.get("founding_steward", {}).get("person_id")
    core.require(
        binding.get("replaced_holder_person_id") == replaced_holder
        and binding.get("replacement_holder_person_id") == replacement_holder,
        "F2 role replacement holder binding mismatch",
    )
    core.require(
        isinstance(replaced_holder, str)
        and isinstance(replacement_holder, str)
        and replaced_holder != replacement_holder,
        "F2 role replacement must transfer the delegated role to a different holder",
    )
    core.require(
        isinstance(founder_id, str) and replacement_holder != founder_id,
        "F2 role replacement cannot demonstrate founder-independent replacement by assigning the successor role to the Founding Steward",
    )

    core.require(replaced.get("operative") is False, "F2 replaced delegation must have completed a validated revocation")
    core.require(isinstance(replaced.get("revocation_record"), dict), "F2 replaced delegation requires a content-addressed revocation")
    core.require(
        binding.get("replaced_decision_record") == replaced.get("decision_record")
        and binding.get("replaced_revocation_record") == replaced.get("revocation_record")
        and binding.get("replacement_decision_record") == replacement.get("decision_record"),
        "F2 role replacement evidence does not bind the exact delegation lifecycle records",
    )

    replaced_scopes = replaced.get("scope_types")
    replacement_scopes = replacement.get("scope_types")
    replaced_resources = replaced.get("scope_resources")
    replacement_resources = replacement.get("scope_resources")
    replaced_actions = replaced.get("allowed_actions")
    replacement_actions = replacement.get("allowed_actions")
    core.require(
        isinstance(replaced_scopes, list)
        and isinstance(replacement_scopes, list)
        and set(replaced_scopes) == set(replacement_scopes) == set(binding.get("scope_types") or []),
        "F2 role replacement must preserve the delegated role scope",
    )
    core.require(
        isinstance(replaced_resources, dict)
        and replaced_resources == replacement_resources == binding.get("scope_resources"),
        "F2 role replacement must preserve the delegated role resources",
    )
    core.require(
        isinstance(replaced_actions, list)
        and isinstance(replacement_actions, list)
        and set(replaced_actions) == set(replacement_actions) == set(binding.get("allowed_actions") or []),
        "F2 role replacement must preserve the delegated role action set",
    )

    replacement_effective = core.parse_iso_date(
        replacement.get("effective_date"),
        "F2 replacement delegation effective_date",
    )
    replaced_effective = core.parse_iso_date(
        replaced.get("effective_date"),
        "F2 replaced delegation effective_date",
    )
    core.require(replaced_effective < replacement_effective <= phase_date, "F2 replacement delegation chronology invalid")
    core.require(core.delegation_active_on(replacement, phase_date), "F2 replacement delegation is not active on the F2 effective date")
    core.require(not core.delegation_active_on(replaced, phase_date), "F2 replaced delegation remains active on the F2 effective date")

    creation = _load_delegation_event(
        replacement.get("decision_record"),
        "F2 replacement delegation creation",
        "delegation-decision",
    )
    revocation = _load_delegation_event(
        replaced.get("revocation_record"),
        "F2 replaced delegation revocation",
        "delegation-revocation",
    )
    core.require(
        creation.get("delegation_id") == replacement_id and revocation.get("delegation_id") == replaced_id,
        "F2 role replacement lifecycle decision identity mismatch",
    )
    replacement_decision_date = core.parse_iso_date(
        creation.get("decision_date"),
        "F2 replacement delegation decision_date",
    )
    revocation_decision_date = core.parse_iso_date(
        revocation.get("decision_date"),
        "F2 replaced delegation revocation decision_date",
    )
    revocation_effective = core.parse_iso_date(
        revocation.get("effective_date"),
        "F2 replaced delegation revocation effective_date",
    )
    core.require(revocation_effective <= phase_date, "F2 replaced delegation revocation postdates F2 effectiveness")

    # Post-F1 delegation creation/revocation is Member-governed by the already
    # validated delegation lifecycle.  Requiring both events in F1/F2 excludes
    # a supposed demonstration that merely reuses an F0 founder-era grant.
    for event_date, label in (
        (replacement_decision_date, "replacement creation"),
        (revocation_decision_date, "replaced delegation revocation"),
    ):
        event_phase = phase.phase_as_of(status, phase_evidence, event_date)
        core.require(
            event_phase in {"F1-early-institution", "F2-distributed-institution"},
            f"F2 role replacement {label} must occur after F1 is validly established",
        )

    return evidence


def validate_phase_evidence(
    status: dict,
    membership: dict,
    founding: dict,
    phase_evidence: dict,
    operative_delegations: list[dict],
    active_members: set[str],
    rules: dict,
) -> None:
    result = ORIG_VALIDATE_PHASE_EVIDENCE(
        status,
        membership,
        founding,
        phase_evidence,
        operative_delegations,
        active_members,
        rules,
    )
    if status.get("operative") is not True:
        return result

    core.require(
        phase_evidence.get("transition_evidence_binding_contract") == TRANSITION_EVIDENCE_BINDING_CONTRACT,
        "phase transition evidence-binding contract missing/weakened",
    )
    current_phase = status.get("institutional_phase")
    if current_phase == "F0-founder-led-bootstrap":
        return result

    require_transition_maturity_binding(
        phase_evidence.get("transition_decision_record"),
        phase_evidence,
        current_phase,
        f"current {current_phase} transition",
    )

    if current_phase != "F2-distributed-institution":
        return result

    require_transition_maturity_binding(
        phase_evidence.get("prior_transition_decision_record"),
        phase_evidence,
        "F1-early-institution",
        "historical F1 transition",
    )
    phase_date = core.parse_iso_date(phase_evidence.get("phase_effective_date"), "F2 phase_effective_date")
    governance_version = phase.phase_as_of(status, phase_evidence, phase_date)
    core.require(governance_version == "F2-distributed-institution", "F2 phase timeline mismatch while validating role replacement")
    # The evidence record itself must use the Governance release effective on
    # the F2 date, not the phase label returned above.
    import governance_release_history as release_history

    event_version = release_history.governance_version_as_of(status, phase_date)
    validate_role_replacement_demonstration(
        phase_evidence["f2"]["role_replacement_evidence"],
        status,
        phase_evidence,
        founding,
        operative_delegations,
        phase_date,
        event_version,
    )
    return result


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    phase.validate_phase_evidence = validate_phase_evidence
    _INSTALLED = True
