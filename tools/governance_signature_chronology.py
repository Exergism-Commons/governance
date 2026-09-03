from __future__ import annotations

import validate_governance as core


BASE_VALIDATE_SIGNATURE_REF = core.validate_signature_ref


def validate_signature_ref(
    ref,
    label: str,
    expected_person_id: str,
    expected_decision_id: str,
    expected_payload_sha256: str,
    context_type: str,
    context_version: str,
    governance_version: str | None = None,
) -> dict:
    data = BASE_VALIDATE_SIGNATURE_REF(
        ref,
        label,
        expected_person_id,
        expected_decision_id,
        expected_payload_sha256,
        context_type,
        context_version,
        governance_version,
    )
    signed = core.parse_iso_date(data.get("signed_date"), f"{label}.signed_date")
    verification, _ = core.validate_content_ref(
        data.get("verification_evidence"),
        f"{label} verification chronology",
        "records/evidence",
    )
    captured = core.parse_iso_date(
        verification.get("captured_date"),
        f"{label} verification.captured_date",
    )
    core.require(
        captured <= signed,
        f"{label} verification evidence cannot be captured after signed_date",
    )
    return data


def install() -> None:
    core.validate_signature_ref = validate_signature_ref
