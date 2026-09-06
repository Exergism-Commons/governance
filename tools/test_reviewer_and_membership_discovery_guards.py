#!/usr/bin/env python3
"""Focused guards for reviewer qualification and membership-record discovery."""

from __future__ import annotations

import json
import tempfile
from datetime import date
from pathlib import Path

import governance_classification_qualification_hardening as classification
import governance_membership_record_discovery as discovery
import governance_review_auth as review_auth
import validate_governance as core


def expect_failure(label: str, callback) -> None:
    try:
        callback()
    except SystemExit:
        return
    raise SystemExit(f"review/discovery guard failure: {label} unexpectedly validated")


def _qualification(*, purpose: str, subject: str, scopes: list[str]) -> dict:
    return {
        "record_type": "supporting-evidence",
        "status": "final",
        "evidence_id": "qualification-1",
        "claim": "Reviewer qualification",
        "captured_date": "2026-01-01",
        "evidence_purpose": purpose,
        "subject_person_id": subject,
        "qualification_kind": "professional-competence",
        "qualification_scope": scopes,
        "source": {
            "type": "external-record",
            "identifier": "qualification-registry:1",
            "immutable_digest": "a" * 64,
        },
    }


def validate_reviewer_qualification_guards() -> int:
    original = core.validate_supporting_evidence_ref
    current = _qualification(
        purpose="reviewer-qualification",
        subject="reviewer-1",
        scopes=["governance-amendment-classification", "cla-legal-review"],
    )

    def fake_supporting(ref, label, governance_version=None):
        return dict(current)

    core.validate_supporting_evidence_ref = fake_supporting
    try:
        ref = {"path": "records/evidence/q", "sha256": "b" * 64}
        review_auth.validate_reviewer_qualification_ref(
            ref,
            "classification qualification",
            "EC-GOV-1.0",
            "reviewer-1",
            "governance-amendment-classification",
        )
        review_auth.validate_reviewer_qualification_ref(
            ref,
            "CLA qualification",
            None,
            "reviewer-1",
            "cla-legal-review",
        )
        cases = 2

        current["evidence_purpose"] = "generic-support"
        expect_failure(
            "generic supporting evidence cannot qualify a reviewer",
            lambda: review_auth.validate_reviewer_qualification_ref(
                ref,
                "wrong-purpose qualification",
                None,
                "reviewer-1",
                "cla-legal-review",
            ),
        )
        cases += 1

        current.update(_qualification(
            purpose="reviewer-qualification",
            subject="someone-else",
            scopes=["governance-amendment-classification"],
        ))
        expect_failure(
            "qualification must name the reviewer",
            lambda: review_auth.validate_reviewer_qualification_ref(
                ref,
                "wrong-subject qualification",
                "EC-GOV-1.0",
                "reviewer-1",
                "governance-amendment-classification",
            ),
        )
        cases += 1

        current.update(_qualification(
            purpose="reviewer-qualification",
            subject="reviewer-1",
            scopes=["governance-legal-review"],
        ))
        expect_failure(
            "qualification must cover amendment-classification scope",
            lambda: review_auth.validate_reviewer_qualification_ref(
                ref,
                "wrong-scope qualification",
                "EC-GOV-1.0",
                "reviewer-1",
                "governance-amendment-classification",
            ),
        )
        cases += 1
        return cases
    finally:
        core.validate_supporting_evidence_ref = original


def validate_classification_scope_wiring() -> int:
    original_base = classification._ORIG_VALIDATE_CLASSIFICATION
    original_content = core.validate_content_ref
    original_qualification = review_auth.validate_reviewer_qualification_ref
    seen: list[tuple[str, str]] = []

    classification._ORIG_VALIDATE_CLASSIFICATION = lambda *args, **kwargs: date(2026, 2, 1)
    core.validate_content_ref = lambda *args, **kwargs: (
        {
            "reviewers": [
                {
                    "reviewer_id": "reviewer-1",
                    "qualification_evidence": {"path": "records/evidence/q", "sha256": "b" * 64},
                }
            ]
        },
        Path("records/evidence/classification"),
    )

    def fake_qualification(ref, label, review_version, reviewer_id, required_scope):
        seen.append((reviewer_id, required_scope))
        return {"captured_date": "2026-01-01"}

    review_auth.validate_reviewer_qualification_ref = fake_qualification
    try:
        classification.validate_classification(
            {"path": "records/evidence/classification", "sha256": "c" * 64},
            {"governance_version": "EC-GOV-1.0"},
            {},
            {},
            {"path": "records/adoptions/previous", "sha256": "d" * 64},
            "constitutional-amendment",
            "decision-1",
            "e" * 64,
            None,
            date(2026, 2, 1),
        )
        core.require(
            seen == [("reviewer-1", "governance-amendment-classification")],
            "classification wrapper did not require the amendment-classification qualification scope",
        )
        return 1
    finally:
        classification._ORIG_VALIDATE_CLASSIFICATION = original_base
        core.validate_content_ref = original_content
        review_auth.validate_reviewer_qualification_ref = original_qualification


def validate_suffix_independent_membership_discovery() -> int:
    original_root = core.ROOT
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        decisions = root / "records" / "decisions"
        decisions.mkdir(parents=True)

        admission = {
            "record_type": "membership-admission",
            "status": "adopted",
            "person_id": "person-a",
        }
        transition = {
            "record_type": "membership-state-transition",
            "status": "adopted",
            "person_id": "person-a",
        }
        (decisions / "admission-without-extension").write_text(json.dumps(admission), encoding="utf-8")
        (decisions / "transition.record").write_text(json.dumps(transition), encoding="utf-8")
        (decisions / "notes.txt").write_text("not JSON and intentionally ignored", encoding="utf-8")

        core.ROOT = root
        try:
            admissions, transitions = discovery.discover_membership_records()
        finally:
            core.ROOT = original_root

    core.require(len(admissions) == 1, "extensionless adopted admission was not discovered")
    core.require(len(transitions) == 1, "non-.json adopted transition was not discovered")
    core.require(admissions[0][1]["path"].endswith("admission-without-extension"), "extensionless admission path mismatch")
    core.require(transitions[0][1]["path"].endswith("transition.record"), "non-.json transition path mismatch")
    return 2


def main() -> None:
    total = 0
    total += validate_reviewer_qualification_guards()
    total += validate_classification_scope_wiring()
    total += validate_suffix_independent_membership_discovery()
    print(f"Reviewer qualification / membership discovery guards: PASS ({total} cases)")


if __name__ == "__main__":
    main()
