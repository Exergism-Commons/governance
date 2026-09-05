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

    # A generic supporting-evidence envelope is not enough to authenticate an
    # authority-bearing signature. The verification record must itself identify
    # the signer, decision, exact payload and signature context it verified.
    # This prevents unrelated/replayed evidence from being attached to a new
    # signature-evidence record that merely repeats the expected metadata.
    core.require(
        verification.get("evidence_purpose") == "signature-verification",
        f"{label} verification evidence purpose mismatch",
    )
    core.require(
        verification.get("subject_person_id") == expected_person_id,
        f"{label} verification signer mismatch",
    )
    core.require(
        verification.get("decision_id") == expected_decision_id,
        f"{label} verification decision mismatch",
    )
    core.require(
        verification.get("verified_payload_sha256") == expected_payload_sha256,
        f"{label} verification does not bind exact signed payload",
    )
    core.require(
        verification.get("context_type") == context_type
        and verification.get("context_version") == context_version,
        f"{label} verification context mismatch",
    )
    core.require(
        verification.get("verification_result") == "valid",
        f"{label} verification must conclude valid",
    )
    verification_method = verification.get("verification_method")
    core.require(
        isinstance(verification_method, str) and verification_method.strip(),
        f"{label} verification_method required",
    )
    core.require(
        verification.get("signature_method") == data.get("signature_method"),
        f"{label} verification/signature method mismatch",
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
