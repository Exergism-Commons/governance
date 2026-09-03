from __future__ import annotations

from datetime import date

import validate_governance as core


def _assignment_payload(status: dict, founding: dict) -> dict:
    founder = founding["founding_steward"]
    return {
        "founding_steward_record_id": founder["record_id"],
        "founding_steward_person_id": founder["person_id"],
        "assignment_effective_date": founder["assignment_effective_date"],
        "assignment_authority_record": founder["assignment_authority_record"],
        "governance_version": status["governance_version"],
    }


def validate_founding_steward_lifecycle(status: dict, founding: dict, rules: dict, membership: dict) -> date | None:
    contract = founding.get("founding_steward_lifecycle_contract")
    core.require(
        contract == {
            "initial_assignment_authority": "governance-adoption",
            "assignment_effective_date_equals_governance_effective_date": True,
            "content_addressed_cessation_required": True,
            "registry_edit_alone_cannot_end_or_restore_authority": True,
            "historical_authority_must_be_reconstructable": True,
            "reactivation_after_cessation_prohibited": True,
            "allowed_cessation_authority_modes": [
                "self-resignation",
                "succession-process",
                "qualified-approval",
            ],
        },
        "Founding Steward lifecycle contract missing/weakened",
    )
    founder = founding.get("founding_steward")
    core.require(isinstance(founder, dict), "founding_steward projection missing")
    required = {
        "record_id",
        "person_id",
        "display_name",
        "github_identity",
        "operative_assignment",
        "assignment_effective_date",
        "assignment_authority_record",
        "cessation_record",
    }
    core.require(set(founder) == required, "founding_steward fields incomplete/unexpected")
    core.require(all(isinstance(founder.get(k), str) and founder[k].strip() for k in ("record_id", "person_id", "display_name")), "Founding Steward stable identity required")

    if status.get("operative") is False:
        core.require(founder["operative_assignment"] is False, "draft cannot fabricate operative Founding Steward")
        core.require(founder["assignment_effective_date"] is None and founder["assignment_authority_record"] is None and founder["cessation_record"] is None, "draft cannot fabricate Founding Steward lifecycle")
        return None

    core.require(founder["assignment_effective_date"] == status["effective_date"], "Founding Steward assignment must begin with operative governance")
    core.require(founder["assignment_authority_record"] == status["adoption_record"], "Founding Steward initial assignment must resolve to exact governance adoption")
    adoption, _ = core.validate_content_ref(founder["assignment_authority_record"], "Founding Steward assignment authority", "records/adoptions")
    core.require(adoption.get("record_type") == "governance-adoption" and adoption.get("status") == "adopted", "Founding Steward assignment authority must be adopted governance")
    core.require(adoption.get("governance_version") == status["governance_version"], "Founding Steward assignment governance version mismatch")
    core.require(adoption.get("effective_date") == founder["assignment_effective_date"], "Founding Steward assignment effective date mismatch")
    core.require(adoption.get("founding_steward_person_id") == founder["person_id"], "Founding Steward assignment identity mismatch")
    core.require(adoption.get("initial_phase") == "F0-founder-led-bootstrap", "Founding Steward assignment must originate in constitutive F0 adoption")
    assignment_hash = core.sha256_json(_assignment_payload(status, founding))

    ref = founder.get("cessation_record")
    if ref is None:
        core.require(founder["operative_assignment"] is True, "Founding Steward without cessation record must remain operative")
        return None

    core.require(founder["operative_assignment"] is False, "Founding Steward with adopted cessation cannot remain operative")
    record, _ = core.validate_content_ref(ref, "Founding Steward cessation", "records/decisions")
    common = {
        "record_type",
        "status",
        "governance_version",
        "founding_steward_person_id",
        "founding_steward_record_id",
        "decision_id",
        "decision_date",
        "effective_date",
        "cessation_type",
        "authority_mode",
        "reason",
        "founding_assignment_payload_sha256",
        "cessation_payload_sha256",
    }
    mode = record.get("authority_mode")
    if mode == "self-resignation":
        required_record = common | {"signature_evidence"}
    elif mode == "succession-process":
        required_record = common | {"process_evidence"}
    elif mode == "qualified-approval":
        required_record = common | {"decision_class", "approval_evidence"}
    else:
        raise SystemExit("governance integrity failure: unsupported Founding Steward cessation authority_mode")
    core.require(set(record) == required_record, "Founding Steward cessation fields incomplete/unexpected")
    core.require(record["record_type"] == "founding-steward-cessation" and record["status"] == "adopted", "Founding Steward cessation record invalid")
    core.require(record["governance_version"] == status["governance_version"], "Founding Steward cessation governance version mismatch")
    core.require(record["founding_steward_person_id"] == founder["person_id"] and record["founding_steward_record_id"] == founder["record_id"], "Founding Steward cessation identity mismatch")
    core.require(record["founding_assignment_payload_sha256"] == assignment_hash, "Founding Steward cessation does not bind exact initial assignment")
    decision_id = record["decision_id"]
    core.require(isinstance(decision_id, str) and decision_id.strip(), "Founding Steward cessation decision_id required")
    decision_date_text = record["decision_date"]
    decision_date = core.parse_iso_date(decision_date_text, "Founding Steward cessation decision_date")
    effective = core.parse_iso_date(record["effective_date"], "Founding Steward cessation effective_date")
    assignment_effective = core.parse_iso_date(founder["assignment_effective_date"], "Founding Steward assignment_effective_date")
    core.require(assignment_effective <= decision_date <= effective, "Founding Steward cessation chronology invalid")
    core.require(isinstance(record["reason"], str) and record["reason"].strip(), "Founding Steward cessation reason required")

    payload = {k: v for k, v in record.items() if k not in {"signature_evidence", "process_evidence", "approval_evidence", "cessation_payload_sha256"}}
    payload_hash = core.sha256_json(payload)
    core.require(record["cessation_payload_sha256"] == payload_hash, "Founding Steward cessation payload hash mismatch")

    if mode == "self-resignation":
        core.require(record["cessation_type"] == "resignation", "self-resignation must record cessation_type=resignation")
        signature = core.validate_signature_ref(
            record["signature_evidence"],
            "Founding Steward resignation signature",
            founder["person_id"],
            decision_id,
            payload_hash,
            "founding-steward-cessation",
            status["governance_version"],
            status["governance_version"],
        )
        core.require(signature.get("signed_date") == decision_date_text, "Founding Steward resignation signature must bind decision date")
    elif mode == "succession-process":
        core.require(record["cessation_type"] in {"death", "incapacity", "prolonged-unavailability", "voluntary-retirement"}, "succession-process cessation_type invalid")
        process = core.validate_process_evidence_ref(
            record["process_evidence"],
            "Founding Steward succession-trigger evidence",
            "founding-steward-succession-evidence",
            status["governance_version"],
            f"founding-steward-cessation:{founder['person_id']}",
        )
        core.require(process.get("decision_id") == decision_id, "Founding Steward succession evidence decision mismatch")
        core.require(process.get("decision_date") == decision_date_text, "Founding Steward succession evidence decision date mismatch")
        core.require(process.get("cessation_payload_sha256") == payload_hash, "Founding Steward succession evidence does not bind exact cessation")
        core.require(process.get("effective_date") == record["effective_date"] and process.get("cessation_type") == record["cessation_type"], "Founding Steward succession evidence chronology/type mismatch")
        completed = core.parse_iso_date(process.get("completed_date"), "Founding Steward succession evidence completed_date")
        core.require(
            assignment_effective <= completed <= decision_date <= effective,
            "Founding Steward succession evidence must be complete no later than the cessation decision/effective boundary",
        )
        supporting = process.get("supporting_evidence")
        core.require(isinstance(supporting, list) and supporting, "Founding Steward succession evidence requires supporting evidence")
        for index, support_ref in enumerate(supporting):
            support = core.validate_supporting_evidence_ref(
                support_ref,
                f"Founding Steward succession supporting evidence {index}",
                status["governance_version"],
            )
            captured = core.parse_iso_date(
                support.get("captured_date"),
                f"Founding Steward succession supporting evidence {index}.captured_date",
            )
            core.require(
                assignment_effective <= captured <= completed,
                "Founding Steward succession supporting evidence cannot be captured after process completion",
            )
    else:
        core.require(record["cessation_type"] == "removal-for-cause", "Qualified cessation must be removal-for-cause")
        core.require(record["decision_class"] == "qualified-approval", "Founding Steward removal requires Qualified Approval")
        core.validate_approval_evidence(
            record["approval_evidence"],
            "Founding Steward removal approval",
            decision_id,
            status,
            rules,
            membership,
            expected_rule_id="qualified-approval",
            expected_artifact_bindings={
                "cessation_payload_sha256": payload_hash,
                "founding_assignment_payload_sha256": assignment_hash,
            },
            expected_decision_date=decision_date_text,
        )
    return effective


def founding_steward_active_on(status: dict, founding: dict, rules: dict, membership: dict, target: date) -> bool:
    if status.get("operative") is not True:
        return False
    cessation = validate_founding_steward_lifecycle(status, founding, rules, membership)
    start = core.parse_iso_date(founding["founding_steward"]["assignment_effective_date"], "Founding Steward assignment_effective_date")
    if target < start:
        return False
    return cessation is None or target < cessation
