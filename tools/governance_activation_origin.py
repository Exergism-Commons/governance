from __future__ import annotations

import governance_release_evidence_hardening as hardening
import validate_governance as core


def validate_activation_evidence(
    status: dict,
    legal_entity: dict | None,
    human_hashes: dict[str, str],
    rules_hash: str,
) -> dict[str, str]:
    """Validate current activation evidence under the release that introduced it.

    The current projection may legitimately inherit unchanged content-addressed
    activation records from an earlier governance release. Those immutable bytes
    retain the governance version, artifacts, legal identity, rules and temporal
    boundary of their release of origin; a later release must not force them to
    masquerade as newly-created evidence.

    Conversely, current status cannot point at arbitrary historical evidence:
    every reference must be exactly the reference frozen in the current release's
    authority snapshot. If the bytes changed, origin resolution stops at the
    release that introduced the changed reference and the full semantic gate is
    applied there.
    """
    evidence = status.get("activation_evidence")
    core.require(
        isinstance(evidence, dict)
        and set(evidence) == set(hardening.ACTIVATION_EVIDENCE_CONTRACT),
        "unexpected activation_evidence set",
    )

    if status.get("operative") is False:
        core.require(
            all(value is None for value in evidence.values()),
            "draft governance cannot claim activation evidence",
        )
        return {}

    core.require(
        legal_entity is not None,
        "operative governance activation evidence requires legal entity",
    )

    current_adoption = hardening._load_adoption(
        status.get("adoption_record"),
        "current governance adoption",
    )
    core.require(
        current_adoption.get("governance_version") == status.get("governance_version"),
        "current adoption governance version mismatch",
    )
    core.require(
        current_adoption.get("effective_date") == status.get("effective_date"),
        "current adoption effective date mismatch",
    )

    # These checks deliberately duplicate a small part of the later adoption
    # validator. Origin resolution happens before that validator, so the release
    # used as the root of the evidence walk must already be tied to the current
    # machine/human projection rather than merely sharing a sequence number.
    core.require(
        current_adoption.get("artifact_bindings") == human_hashes,
        "current adoption does not bind current governance artifacts",
    )
    core.require(
        current_adoption.get("legal_entity")
        == {key: value for key, value in legal_entity.items() if key != "evidence"},
        "current adoption legal entity mismatch",
    )
    core.require(
        current_adoption.get("governing_law") == status.get("governing_law"),
        "current adoption governing law mismatch",
    )
    normative = current_adoption.get("normative_machine_bindings")
    core.require(
        isinstance(normative, dict)
        and normative.get("policy/decision-rules.json") == rules_hash,
        "current adoption decision-rules binding mismatch",
    )

    current_snapshot = hardening._raw_authority_snapshot(
        current_adoption,
        "current governance authority snapshot",
    )
    core.require(
        current_snapshot.get("activation_evidence") == evidence,
        "current status activation evidence does not match authority snapshot",
    )

    hashes: dict[str, str] = {}
    for key in hardening.ACTIVATION_EVIDENCE_CONTRACT:
        ref = evidence[key]
        core.require(isinstance(ref, dict), f"activation reference missing: {key}")
        origin, origin_snapshot = hardening._activation_origin(
            current_adoption,
            key,
            ref,
            f"current activation {key}",
        )
        hardening._validate_activation_at_origin(
            key,
            ref,
            origin,
            origin_snapshot,
            f"current activation {key}",
        )
        hashes[key] = core.require_sha256(
            ref.get("sha256"),
            f"activation evidence {key} sha256",
        )
    return hashes
