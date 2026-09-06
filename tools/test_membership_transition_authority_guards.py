#!/usr/bin/env python3
"""Focused guards for authority over inactivity, suspension and reactivation."""

from __future__ import annotations

import copy

import governance_membership_transition_authority as hardening
import governance_release_history as release_history
import governance_temporal_phase as phase
import validate_governance as core


def expect_failure(label: str, callback) -> None:
    try:
        callback()
    except SystemExit:
        return
    raise SystemExit(f"membership transition authority guard failure: {label} unexpectedly validated")


def _membership() -> dict:
    return {
        "state_transition_contract": {
            **hardening.TRANSITION_AUTHORITY_FLOORS,
        }
    }


def _transition(transition_type: str, decision_class: str | None) -> dict:
    return {
        "transition_type": transition_type,
        "decision_id": f"{transition_type}-member-a",
        "decision_class": decision_class,
        "decision_date": "2026-06-15",
        "effective_date": "2026-06-16",
        "transition_payload_sha256": "a" * 64,
        "process_evidence": {
            "path": f"records/evidence/{transition_type}-process.json",
            "sha256": "b" * 64,
        },
        "signature_evidence": None,
        "approval_evidence": {
            "path": f"records/evidence/{transition_type}-approval.json",
            "sha256": "c" * 64,
        },
    }


def validate_f1_member_approval_authority() -> int:
    membership = _membership()
    status = {"operative": True}
    rules = {}
    founding = {"founding_steward": {"person_id": "founder"}}
    phase_evidence = {}
    process = {"completed_date": "2026-06-10"}
    approval = {"voting_window_open_date": "2026-06-01"}

    saved_content = core.validate_content_ref
    saved_approval = core.validate_approval_evidence
    saved_phase = phase.phase_as_of
    saved_version = release_history.governance_version_as_of
    calls: list[tuple[str, dict]] = []
    try:
        def fake_content(ref, label, prefix):
            if "process" in ref["path"]:
                return process, None
            if "approval" in ref["path"]:
                return approval, None
            raise SystemExit(f"unexpected synthetic membership transition ref: {ref}")

        core.validate_content_ref = fake_content
        core.validate_approval_evidence = lambda *args, **kwargs: calls.append(
            (kwargs.get("expected_rule_id"), kwargs.get("expected_artifact_bindings"))
        )
        phase.phase_as_of = lambda *args, **kwargs: "F1-early-institution"
        release_history.governance_version_as_of = lambda *args, **kwargs: "EC-GOV-1.0"

        inactivity = _transition("inactivity", "ordinary-approval")
        hardening.validate_transition_authority(
            inactivity,
            "member-a",
            membership,
            status,
            rules,
            founding,
            phase_evidence,
        )
        expected_process_ref_hash = core.sha256_json(inactivity["process_evidence"])
        core.require(
            calls[-1] == (
                "ordinary-approval",
                {
                    "transition_payload_sha256": "a" * 64,
                    "process_evidence_ref_sha256": expected_process_ref_hash,
                },
            ),
            "F1 inactivity approval did not bind transition + exact process reference",
        )
        cases = 1

        suspension = _transition("suspension", "qualified-approval")
        hardening.validate_transition_authority(
            suspension,
            "member-a",
            membership,
            status,
            rules,
            founding,
            phase_evidence,
        )
        core.require(calls[-1][0] == "qualified-approval", "F1 suspension did not require Qualified Approval")
        cases += 1

        unauthorised = _transition("inactivity", None)
        expect_failure(
            "generic process evidence cannot inactivate a Member without approval",
            lambda: hardening.validate_transition_authority(
                unauthorised,
                "member-a",
                membership,
                status,
                rules,
                founding,
                phase_evidence,
            ),
        )
        cases += 1
        return cases
    finally:
        core.validate_content_ref = saved_content
        core.validate_approval_evidence = saved_approval
        phase.phase_as_of = saved_phase
        release_history.governance_version_as_of = saved_version


def validate_f0_requires_live_founder_signature() -> int:
    membership = _membership()
    status = {"operative": True}
    rules = {}
    founding = {"founding_steward": {"person_id": "founder"}}
    transition = _transition("inactivity", None)
    transition["approval_evidence"] = None
    transition["signature_evidence"] = {"path": "records/evidence/founder-signature.json", "sha256": "d" * 64}

    saved_content = core.validate_content_ref
    saved_signature = core.validate_signature_ref
    saved_active = hardening.founding_lifecycle.founding_steward_active_on
    saved_phase = phase.phase_as_of
    saved_version = release_history.governance_version_as_of
    signed_payloads: list[str] = []
    founder_active = True
    try:
        core.validate_content_ref = lambda ref, label, prefix: ({"completed_date": "2026-06-10"}, None)

        def fake_signature(ref, label, person_id, decision_id, payload_hash, context_type, context_version, governance_version):
            core.require(person_id == "founder", "F0 process authority signer mismatch")
            core.require(context_type == "membership-state-process-authority", "F0 process authority signature context mismatch")
            signed_payloads.append(payload_hash)
            return {"signed_date": "2026-06-12"}

        core.validate_signature_ref = fake_signature
        hardening.founding_lifecycle.founding_steward_active_on = lambda *args, **kwargs: founder_active
        phase.phase_as_of = lambda *args, **kwargs: "F0-founder-led-bootstrap"
        release_history.governance_version_as_of = lambda *args, **kwargs: "EC-GOV-1.0"

        hardening.validate_transition_authority(
            transition,
            "member-a",
            membership,
            status,
            rules,
            founding,
            {},
        )
        expected_payload = core.sha256_json(
            {
                "transition_payload_sha256": transition["transition_payload_sha256"],
                "process_evidence": transition["process_evidence"],
            }
        )
        core.require(signed_payloads == [expected_payload], "F0 signature did not bind exact process-evidence reference")
        cases = 1

        founder_active = False
        expect_failure(
            "ceased Founding Steward cannot authorize process transition",
            lambda: hardening.validate_transition_authority(
                transition,
                "member-a",
                membership,
                status,
                rules,
                founding,
                {},
            ),
        )
        cases += 1
        return cases
    finally:
        core.validate_content_ref = saved_content
        core.validate_signature_ref = saved_signature
        hardening.founding_lifecycle.founding_steward_active_on = saved_active
        phase.phase_as_of = saved_phase
        release_history.governance_version_as_of = saved_version


def validate_historical_policy_floor() -> int:
    saved = hardening.ORIG_VALIDATE_HISTORICAL_MEMBERSHIP_SEMANTICS
    try:
        hardening.ORIG_VALIDATE_HISTORICAL_MEMBERSHIP_SEMANTICS = lambda policy, label: None
        hardening.validate_historical_membership_semantics(_membership(), "historical membership")
        cases = 1

        weakened = _membership()
        del weakened["state_transition_contract"]["f1_plus_suspension_authority"]
        expect_failure(
            "historical release cannot drop suspension authority floor",
            lambda: hardening.validate_historical_membership_semantics(weakened, "historical membership"),
        )
        cases += 1
        return cases
    finally:
        hardening.ORIG_VALIDATE_HISTORICAL_MEMBERSHIP_SEMANTICS = saved


def main() -> None:
    total = 0
    total += validate_f1_member_approval_authority()
    total += validate_f0_requires_live_founder_signature()
    total += validate_historical_policy_floor()
    print(f"Membership transition authority guards: PASS ({total} cases)")


if __name__ == "__main__":
    main()
