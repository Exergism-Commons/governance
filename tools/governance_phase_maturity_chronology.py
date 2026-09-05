from __future__ import annotations

from datetime import date

import validate_governance as core
import governance_release_history as release_history


def validate_evidence_as_of(ref, label: str, record_type: str, subject: str, governance_version: str, phase_date: date) -> dict:
    data = core.validate_process_evidence_ref(ref, label, record_type, governance_version, subject)
    phase_text = phase_date.isoformat()
    core.require(data.get("as_of_date") == phase_text, f"{label} must bind exact phase_effective_date")
    completed = core.parse_iso_date(data.get("completed_date"), f"{label}.completed_date")
    core.require(completed <= phase_date, f"{label} cannot be completed after phase_effective_date")
    supporting = data.get("supporting_evidence")
    core.require(isinstance(supporting, list) and supporting, f"{label} requires supporting evidence")
    for index, support_ref in enumerate(supporting):
        support, _ = core.validate_content_ref(support_ref, f"{label} supporting evidence {index}", "records/evidence")
        captured = core.parse_iso_date(support.get("captured_date"), f"{label} supporting evidence {index}.captured_date")
        core.require(captured <= phase_date, f"{label} supporting evidence cannot postdate phase_effective_date")
    return data


def historical_f1_effective_date(status: dict, phase_evidence: dict) -> date:
    phase = status.get("institutional_phase")
    if phase == "F1-early-institution":
        return core.parse_iso_date(phase_evidence.get("phase_effective_date"), "F1 phase_effective_date")
    core.require(phase == "F2-distributed-institution", "historical F1 date requested outside F1/F2")
    prior, _ = core.validate_content_ref(
        phase_evidence.get("prior_transition_decision_record"),
        "historical F0→F1 transition for maturity chronology",
        "records/decisions",
    )
    core.require(
        prior.get("record_type") == "phase-transition"
        and prior.get("status") == "adopted"
        and prior.get("from_phase") == "F0-founder-led-bootstrap"
        and prior.get("to_phase") == "F1-early-institution",
        "historical F1 chronology requires adopted F0→F1 transition",
    )
    return core.parse_iso_date(prior.get("effective_date"), "historical F1 effective_date")


def validate_phase_maturity_chronology(status: dict, phase_evidence: dict) -> None:
    if status.get("operative") is not True:
        return
    phase = status.get("institutional_phase")
    if phase == "F0-founder-led-bootstrap":
        return

    contract = phase_evidence.get("maturity_evidence_chronology_contract")
    core.require(
        isinstance(contract, dict)
        and contract.get("evidence_as_of_date_must_equal_phase_effective_date") is True
        and contract.get("evidence_completed_no_later_than_phase_effective_date") is True
        and contract.get("supporting_evidence_captured_no_later_than_phase_effective_date") is True,
        "phase maturity evidence chronology contract missing/weakened",
    )

    current_phase_date = core.parse_iso_date(phase_evidence.get("phase_effective_date"), "phase_effective_date")
    f1_date = historical_f1_effective_date(status, phase_evidence)
    core.require(f1_date <= current_phase_date, "historical F1 evidence cannot postdate current phase")
    f1_version = release_history.governance_version_as_of(status, f1_date)
    f1 = phase_evidence["f1"]
    validate_evidence_as_of(
        f1["independent_role_holder_evidence"],
        "F1 independent role evidence chronology",
        "independent-role-holder-evidence",
        "f1-independent-role-holder",
        f1_version,
        f1_date,
    )
    validate_evidence_as_of(
        f1["delegation_evidence"],
        "F1 delegation evidence chronology",
        "delegation-coverage-evidence",
        "f1-critical-delegation-coverage",
        f1_version,
        f1_date,
    )

    if phase != "F2-distributed-institution":
        return
    f2_version = release_history.governance_version_as_of(status, current_phase_date)
    f2 = phase_evidence["f2"]
    for key, record_type, subject, label in (
        ("control_separation_evidence", "control-separation-evidence", "f2-control-separation", "F2 control separation evidence chronology"),
        ("audit_review_evidence", "audit-review-capacity-evidence", "f2-audit-review-capacity", "F2 audit/review evidence chronology"),
        ("role_replacement_evidence", "role-replacement-evidence", "f2-role-replacement", "F2 role replacement evidence chronology"),
    ):
        validate_evidence_as_of(f2[key], label, record_type, subject, f2_version, current_phase_date)
