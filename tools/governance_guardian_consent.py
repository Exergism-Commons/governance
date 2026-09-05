from __future__ import annotations

from datetime import date

import validate_governance as core
import governance_release_history as history


def validate_guardian_consent(
    ref,
    status: dict,
    decision_id: str,
    amendment_payload_sha256: str,
    first_vote_date: date,
    final_vote_date: date,
) -> None:
    founding = core.load_json("policy/founding-stewardship.json")
    founder = founding["founding_steward"]
    guardian = founding["mission_guardian"]

    envelope, _ = core.validate_content_ref(
        ref,
        "Mission-Locked amendment guardian consent envelope",
        "records/evidence",
    )
    signed = core.parse_iso_date(
        envelope.get("signed_date"),
        "Mission-Locked amendment guardian consent signed_date",
    )
    core.require(
        first_vote_date <= signed <= final_vote_date,
        "Mission-Locked guardian consent must be recorded between the first and final successful votes",
    )

    founder_active = history.founding_steward_active_on_projection(status, founding, signed)
    guardian_active = history.mission_guardian_active_on_projection(founding, signed)

    if founder_active:
        signer = founder.get("person_id")
    else:
        core.require(
            guardian_active,
            "Mission-Locked amendment requires a Mission Guardian whose assignment was already effective on the consent date",
        )
        signer = guardian.get("person_id")

    core.require(isinstance(signer, str) and signer, "Mission-Locked amendment guardian identity missing")
    core.require(
        envelope.get("person_id") == signer,
        "Mission-Locked amendment consent signer lacked the protected role on signed_date",
    )
    core.validate_signature_ref(
        ref,
        "Mission-Locked amendment guardian consent",
        signer,
        decision_id,
        amendment_payload_sha256,
        "mission-locked-amendment-consent",
        status["governance_version"],
        status["governance_version"],
    )
