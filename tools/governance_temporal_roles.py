from __future__ import annotations

import validate_governance as core
import validate_governance_lifecycle as life


def validate_mission_guardian_assignment(status, founding, rules, membership, phase_evidence) -> None:
    guardian = founding.get("mission_guardian")
    core.require(isinstance(guardian, dict), "mission_guardian projection missing")
    if guardian.get("operative_assignment") is not True:
        core.require(guardian.get("assignment_record") is None, "inactive Mission Guardian cannot claim assignment record")
        return
    person_id = guardian.get("person_id")
    record_id = guardian.get("record_id")
    core.require(all(isinstance(x, str) and x.strip() for x in (person_id, record_id, guardian.get("display_name"))), "operative Mission Guardian requires identified holder")
    record, _ = core.validate_content_ref(guardian.get("assignment_record"), "Mission Guardian assignment", "records/decisions")
    core.require(record.get("record_type") == "mission-guardian-assignment" and record.get("status") == "adopted", "Mission Guardian assignment invalid")
    core.require(record.get("governance_version") == status["governance_version"], "Mission Guardian assignment version mismatch")
    core.require(record.get("guardian_person_id") == person_id and record.get("guardian_record_id") == record_id, "Mission Guardian assignment identity mismatch")
    decision_id = record.get("decision_id")
    decision_date_text = record.get("decision_date")
    effective = core.parse_iso_date(record.get("effective_date"), "Mission Guardian assignment effective_date")
    core.require(core.parse_iso_date(decision_date_text, "Mission Guardian assignment decision_date") <= effective, "Mission Guardian assignment decision postdates effective date")
    if status["institutional_phase"] == "F2-distributed-institution":
        core.require(effective <= core.parse_iso_date(phase_evidence["phase_effective_date"], "phase_effective_date"), "F2 Mission Guardian must be assigned by F2 effective date")
    payload = {k: v for k, v in record.items() if k not in {"approval_evidence", "process_evidence", "assignment_payload_sha256"}}
    payload_hash = core.sha256_json(payload)
    core.require(record.get("assignment_payload_sha256") == payload_hash, "Mission Guardian assignment payload hash mismatch")
    mode = record.get("authority_mode")
    if mode == "qualified-approval":
        core.require(record.get("decision_class") == "qualified-approval", "Mission Guardian appointment requires Qualified Approval")
        core.validate_approval_evidence(
            record.get("approval_evidence"),
            "Mission Guardian appointment approval",
            decision_id,
            status,
            rules,
            membership,
            expected_rule_id="qualified-approval",
            expected_artifact_bindings={"assignment_payload_sha256": payload_hash},
            expected_decision_date=decision_date_text,
        )
    elif mode == "succession-process":
        process = core.validate_process_evidence_ref(
            record.get("process_evidence"),
            "Mission Guardian succession evidence",
            "mission-guardian-succession-evidence",
            status["governance_version"],
            f"mission-guardian-assignment:{person_id}",
        )
        core.require(process.get("decision_id") == decision_id, "Mission Guardian succession evidence decision mismatch")
        core.require(process.get("assignment_payload_sha256") == payload_hash, "Mission Guardian succession evidence does not bind exact assignment payload")
        core.require(process.get("guardian_person_id") == person_id and process.get("guardian_record_id") == record_id, "Mission Guardian succession evidence identity mismatch")
        core.require(process.get("effective_date") == record.get("effective_date"), "Mission Guardian succession evidence effective date mismatch")
    else:
        raise SystemExit("governance integrity failure: Mission Guardian authority_mode unsupported")


def validate_cla_steward_authority() -> None:
    status_text = (core.ROOT / "policy/cla-status.yaml").read_text(encoding="utf-8")
    if core.yaml_scalar(status_text, "operative") is not True:
        return
    life.validate_cla_steward_authority()
    cla_effective = core.parse_iso_date(core.yaml_scalar(status_text, "effective_date"), "CLA effective_date")
    ref = {
        "path": core.yaml_scalar(status_text, "legal_steward_authority_artifact"),
        "sha256": core.yaml_scalar(status_text, "legal_steward_authority_sha256"),
    }
    record, _ = core.validate_content_ref(ref, "CLA legal Steward authority", "records/decisions")
    decision_date = core.parse_iso_date(record.get("decision_date"), "CLA Steward authority decision_date")
    authority_effective = core.parse_iso_date(record.get("effective_date"), "CLA Steward authority effective_date")
    core.require(decision_date <= authority_effective <= cla_effective, "CLA Steward authority must be approved before becoming effective and before CLA activation")
    signatories = record.get("legal_identity", {}).get("competent_signatories")
    signatures = record.get("signatory_evidence")
    core.require(isinstance(signatories, list) and isinstance(signatures, list), "CLA Steward signatory records missing")
    for index, sig_ref in enumerate(signatures):
        sig, _ = core.validate_content_ref(sig_ref, f"CLA Steward competent signature envelope {index}", "records/evidence")
        signed_date = core.parse_iso_date(sig.get("signed_date"), f"CLA Steward competent signature {index}.signed_date")
        core.require(signed_date <= authority_effective, "CLA Steward competent signature cannot postdate authority effective date")


def validate_cla_status() -> None:
    life.ORIG_VALIDATE_CLA_STATUS()
    validate_cla_steward_authority()
