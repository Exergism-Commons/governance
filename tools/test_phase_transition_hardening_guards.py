#!/usr/bin/env python3
"""Focused guards for phase-transition evidence binding and F2 role replacement."""

from __future__ import annotations

import copy
from datetime import date

import governance_phase_transition_hardening as hardening
import governance_temporal_phase as phase
import validate_governance as core


def expect_failure(label: str, callback) -> None:
    try:
        callback()
    except SystemExit:
        return
    raise SystemExit(f"phase-transition hardening guard failure: {label} unexpectedly validated")


def _ref(name: str, digest_char: str) -> dict:
    return {"path": f"records/evidence/{name}.json", "sha256": digest_char * 64}


def validate_transition_binds_exact_maturity_refs() -> int:
    phase_evidence = {
        "f1": {
            "independent_role_holder_evidence": _ref("f1-independent", "1"),
            "delegation_evidence": _ref("f1-delegations", "2"),
        },
        "f2": {
            "control_separation_evidence": _ref("f2-separation", "3"),
            "audit_review_evidence": _ref("f2-audit", "4"),
            "role_replacement_evidence": _ref("f2-replacement", "5"),
        },
    }
    transition_ref = {"path": "records/decisions/f2-transition.json", "sha256": "6" * 64}
    transition = {
        "record_type": "phase-transition",
        "status": "adopted",
        "to_phase": "F2-distributed-institution",
        "maturity_evidence": hardening._expected_maturity_evidence(phase_evidence, "F2-distributed-institution"),
    }

    saved_content = core.validate_content_ref
    try:
        core.validate_content_ref = lambda ref, label, prefix: (transition, None)
        hardening.require_transition_maturity_binding(
            transition_ref,
            phase_evidence,
            "F2-distributed-institution",
            "synthetic F2 transition",
        )
        cases = 1

        swapped = copy.deepcopy(phase_evidence)
        swapped["f2"]["role_replacement_evidence"] = _ref("post-vote-substitute", "7")
        expect_failure(
            "post-vote maturity evidence substitution",
            lambda: hardening.require_transition_maturity_binding(
                transition_ref,
                swapped,
                "F2-distributed-institution",
                "synthetic F2 transition",
            ),
        )
        cases += 1
        return cases
    finally:
        core.validate_content_ref = saved_content


def _delegations() -> list[dict]:
    replaced_decision = {"path": "records/decisions/old-grant.json", "sha256": "a" * 64}
    revocation = {"path": "records/decisions/old-revocation.json", "sha256": "b" * 64}
    replacement_decision = {"path": "records/decisions/new-grant.json", "sha256": "c" * 64}
    common = {
        "scope_types": ["repository"],
        "scope_resources": {"repository": ["canonical-repo"]},
        "allowed_actions": ["maintain-repository"],
    }
    return [
        {
            "delegation_id": "old-role",
            "holder_person_id": "person-old",
            "effective_date": "2026-02-01",
            "operative": False,
            "decision_record": replaced_decision,
            "revocation_record": revocation,
            **copy.deepcopy(common),
        },
        {
            "delegation_id": "new-role",
            "holder_person_id": "person-new",
            "effective_date": "2026-08-01",
            "operative": True,
            "decision_record": replacement_decision,
            "revocation_record": None,
            **copy.deepcopy(common),
        },
    ]


def _replacement_evidence(items: list[dict]) -> dict:
    old, new = items
    return {
        "record_type": "role-replacement-evidence",
        "status": "final",
        "complete": True,
        "result": "satisfied",
        "as_of_date": "2026-12-01",
        "role_replacement_binding": {
            "replaced_delegation_id": old["delegation_id"],
            "replacement_delegation_id": new["delegation_id"],
            "replaced_holder_person_id": old["holder_person_id"],
            "replacement_holder_person_id": new["holder_person_id"],
            "replaced_decision_record": old["decision_record"],
            "replaced_revocation_record": old["revocation_record"],
            "replacement_decision_record": new["decision_record"],
            "scope_types": copy.deepcopy(old["scope_types"]),
            "scope_resources": copy.deepcopy(old["scope_resources"]),
            "allowed_actions": copy.deepcopy(old["allowed_actions"]),
        },
    }


def validate_real_role_replacement_required() -> int:
    items = _delegations()
    evidence = _replacement_evidence(items)
    ref = _ref("f2-replacement", "d")
    phase_date = date.fromisoformat("2026-12-01")
    founding = {"founding_steward": {"person_id": "founder"}}

    creation = {
        "record_type": "delegation-decision",
        "status": "adopted",
        "delegation_id": "new-role",
        "decision_date": "2026-07-20",
    }
    revocation = {
        "record_type": "delegation-revocation",
        "status": "adopted",
        "delegation_id": "old-role",
        "decision_date": "2026-07-15",
        "effective_date": "2026-08-01",
    }

    saved_process = core.validate_process_evidence_ref
    saved_content = core.validate_content_ref
    saved_active = core.delegation_active_on
    saved_phase = phase.phase_as_of
    current = evidence
    try:
        core.validate_process_evidence_ref = lambda *args, **kwargs: current

        def fake_content(content_ref, label, prefix):
            if content_ref == items[1]["decision_record"]:
                return creation, None
            if content_ref == items[0]["revocation_record"]:
                return revocation, None
            raise SystemExit(f"unexpected synthetic role-replacement reference: {content_ref}")

        core.validate_content_ref = fake_content
        core.delegation_active_on = lambda item, target: item["delegation_id"] == "new-role"
        phase.phase_as_of = lambda status, phase_evidence, target: "F1-early-institution"

        hardening.validate_role_replacement_demonstration(
            ref,
            {"operative": True},
            {},
            founding,
            items,
            phase_date,
            "EC-GOV-1.0",
        )
        cases = 1

        current = {
            "record_type": "role-replacement-evidence",
            "status": "final",
            "complete": True,
            "result": "satisfied",
            "as_of_date": "2026-12-01",
        }
        expect_failure(
            "generic process assertion without delegation lifecycle binding",
            lambda: hardening.validate_role_replacement_demonstration(
                ref,
                {"operative": True},
                {},
                founding,
                items,
                phase_date,
                "EC-GOV-1.0",
            ),
        )
        cases += 1

        same_holder_items = _delegations()
        same_holder_items[1]["holder_person_id"] = same_holder_items[0]["holder_person_id"]
        current = _replacement_evidence(same_holder_items)
        expect_failure(
            "same holder cannot demonstrate role replacement",
            lambda: hardening.validate_role_replacement_demonstration(
                ref,
                {"operative": True},
                {},
                founding,
                same_holder_items,
                phase_date,
                "EC-GOV-1.0",
            ),
        )
        cases += 1
        return cases
    finally:
        core.validate_process_evidence_ref = saved_process
        core.validate_content_ref = saved_content
        core.delegation_active_on = saved_active
        phase.phase_as_of = saved_phase


def main() -> None:
    total = 0
    total += validate_transition_binds_exact_maturity_refs()
    total += validate_real_role_replacement_required()
    print(f"Phase-transition hardening guards: PASS ({total} cases)")


if __name__ == "__main__":
    main()
