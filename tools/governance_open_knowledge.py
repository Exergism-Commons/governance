from __future__ import annotations

import validate_governance as core
import governance_release_history as release_history
import governance_semantic_invariants as invariants


OPEN_KNOWLEDGE_STATUS_PATH = "policy/open-knowledge-status.json"
OPEN_KNOWLEDGE_POLICY_PATH = "OPEN-KNOWLEDGE-POLICY.md"


def _validate_policy_semantics(text: str) -> None:
    lowered = text.lower()
    core.require("canonicality is not exclusivity" in lowered, "Open Knowledge canonicality invariant missing")
    core.require("anti-enclosure" in lowered, "Open Knowledge anti-enclosure rule missing")
    core.require("source form" in lowered, "Open Knowledge Source Form rule missing")
    core.require("no such publication grants a patent right" in lowered, "Open Knowledge patent non-inference rule missing")
    core.require("does not itself change the license" in lowered, "Open Knowledge non-retroactivity rule missing")
    core.require("id.exergism.org" in lowered and "not a relicensing authority" in lowered, "resolver authority boundary missing")


def _validate_projection_invariants(projection: dict, rules: dict) -> None:
    core.require(projection.get("schema_version") == 1, "unsupported Open Knowledge projection schema")
    core.require(set(projection) == invariants.OPEN_KNOWLEDGE_TOP_LEVEL_KEYS_V1, "Open Knowledge schema v1 top-level field set changed")
    core.require(projection.get("policy") == "exergism-commons-open-knowledge", "unexpected Open Knowledge policy id")
    core.require(projection.get("policy_artifact") == OPEN_KNOWLEDGE_POLICY_PATH, "Open Knowledge policy path changed")
    core.require(projection.get("constitutional_principle") == "knowledge-commons-and-anti-enclosure", "Open Knowledge constitutional principle changed")
    core.require(projection.get("core_rule") == "canonicality-is-not-exclusivity", "Open Knowledge canonicality rule changed")
    core.require(set(projection.get("protected_freedoms") or []) == invariants.OPEN_KNOWLEDGE_PROTECTED_FREEDOMS_V1, "Open Knowledge protected-freedom set changed")
    core.require(projection.get("ec_publication_requirements") == invariants.OPEN_KNOWLEDGE_PUBLICATION_REQUIREMENTS_V1, "Open Knowledge publication/source-form contract changed")
    core.require(projection.get("anti_enclosure") == invariants.OPEN_KNOWLEDGE_ANTI_ENCLOSURE_V1, "Open Knowledge anti-enclosure contract changed")
    core.require(projection.get("license_implementation") == invariants.OPEN_KNOWLEDGE_LICENSE_IMPLEMENTATION_V1, "Open Knowledge license-implementation contract changed")
    core.require(projection.get("authority_boundaries") == invariants.OPEN_KNOWLEDGE_AUTHORITY_BOUNDARIES_V1, "Open Knowledge authority boundaries changed")
    core.require(projection.get("project_relationships") == invariants.OPEN_KNOWLEDGE_PROJECT_RELATIONSHIPS_V1, "Open Knowledge project-authority relationships changed")
    core.require(set(projection.get("excluded_or_protected_material") or []) == invariants.OPEN_KNOWLEDGE_EXCLUDED_MATERIAL_V1, "Open Knowledge protected/excluded material taxonomy changed")
    core.require(projection.get("adoption_requirements") == invariants.OPEN_KNOWLEDGE_ADOPTION_REQUIREMENTS_V1, "Open Knowledge adoption contract changed")
    core.require(projection.get("integrity_contract") == invariants.OPEN_KNOWLEDGE_INTEGRITY_CONTRACT_V1, "Open Knowledge integrity contract changed")
    core.require(projection.get("history_contract") == invariants.OPEN_KNOWLEDGE_HISTORY_CONTRACT_V1, "Open Knowledge release-history contract changed")
    notes = projection.get("notes")
    core.require(isinstance(notes, list) and notes and all(isinstance(item, str) and item.strip() for item in notes), "Open Knowledge notes must remain a non-empty string list")
    core.require(set(rules.get("mission_locked_subjects") or []) == invariants.MISSION_LOCKED_SUBJECTS_V1, "Mission Lock subject taxonomy does not exactly include the anti-enclosure invariant")


def _validate_policy_binding_shape(binding: dict, label: str) -> tuple[dict, dict, object]:
    core.require(
        isinstance(binding, dict)
        and set(binding) == {
            "policy",
            "rights_review_record",
            "effective_date",
            "core_rule",
            "anti_enclosure_mission_lock_subject",
        },
        f"{label} Open Knowledge binding fields invalid",
    )
    policy = binding.get("policy")
    core.require(isinstance(policy, dict) and set(policy) == {"path", "version", "sha256"}, f"{label} Open Knowledge policy binding fields invalid")
    core.require(policy.get("path") == OPEN_KNOWLEDGE_POLICY_PATH, f"{label} Open Knowledge path changed")
    version = policy.get("version")
    core.require(isinstance(version, str) and version.strip() and "-DRAFT" not in version, f"{label} Open Knowledge version must be non-draft")
    core.require_sha256(policy.get("sha256"), f"{label} Open Knowledge policy sha256")
    core.require(binding.get("core_rule") == "canonicality-is-not-exclusivity", f"{label} Open Knowledge core rule changed")
    core.require(binding.get("anti_enclosure_mission_lock_subject") == "permit-enclosure-of-established-ec-public-knowledge", f"{label} anti-enclosure Mission-Lock binding changed")
    effective = core.parse_iso_date(binding.get("effective_date"), f"{label} Open Knowledge effective_date")
    review_ref = binding.get("rights_review_record")
    core.require(isinstance(review_ref, dict) and set(review_ref) == {"path", "sha256"}, f"{label} Open Knowledge rights-review reference invalid")
    return policy, review_ref, effective


def _validate_historical_rights_review(
    review_ref: dict,
    policy_binding: dict,
    binding_effective,
    label: str,
    expected_governance_version: str | None,
) -> None:
    review, _ = core.validate_content_ref(review_ref, f"{label} Open Knowledge rights review", "records/evidence")
    core.require(review.get("record_type") == "qualified-legal-review-evidence", f"{label} Open Knowledge review type mismatch")
    core.require(review.get("status") == "final" and review.get("complete") is True and review.get("result") == "approved", f"{label} Open Knowledge review must be final/complete/approved")
    if expected_governance_version is not None:
        core.require(review.get("governance_version") == expected_governance_version, f"{label} changed Open Knowledge binding must be reviewed under the authorizing governance release")
    core.require(review.get("reviewed_open_knowledge_policy") == policy_binding, f"{label} qualified legal review does not bind exact Open Knowledge policy bytes")
    completed = core.parse_iso_date(review.get("completed_date"), f"{label} Open Knowledge review completed_date")
    core.require(completed <= binding_effective, f"{label} Open Knowledge review completed after policy effective date")


def _validate_release_history(governance: dict) -> tuple[dict, dict]:
    """Validate Open Knowledge as a release-chain invariant, not a current-state add-on.

    Every operative release must carry the complete binding. Release #1 therefore
    cannot be repaired retroactively by release #2+. If a later release changes
    the binding, the changed policy/review becomes effective with that release;
    unchanged releases preserve the exact historical binding byte-for-byte.
    """

    chain = release_history.release_chain(governance)
    core.require(chain, "operative governance requires a release history")
    previous_binding: dict | None = None
    previous_release_effective = None

    for record, ref in chain:
        sequence = record.get("release_sequence")
        label = f"governance release #{sequence}"
        binding = record.get("open_knowledge_binding")
        policy_binding, review_ref, binding_effective = _validate_policy_binding_shape(binding, label)
        release_effective = core.parse_iso_date(record.get("effective_date"), f"{label} effective_date")
        core.require(binding_effective <= release_effective, f"{label} cannot claim Open Knowledge effective after the release")

        changed = previous_binding is None or binding != previous_binding
        if previous_binding is None:
            core.require(sequence == 1, "Open Knowledge history must begin at release #1")
        elif changed:
            core.require(binding_effective == release_effective, f"{label} changed Open Knowledge binding cannot be backdated before its authorizing release")
            core.require(previous_release_effective is not None and binding_effective > previous_release_effective, f"{label} changed Open Knowledge binding must postdate its predecessor release")

        _validate_historical_rights_review(
            review_ref,
            policy_binding,
            binding_effective,
            label,
            record.get("governance_version") if changed else None,
        )
        previous_binding = binding
        previous_release_effective = release_effective

    latest_record, latest_ref = chain[-1]
    core.require(latest_record.get("open_knowledge_binding") == previous_binding, "latest Open Knowledge release binding mismatch")
    return latest_record, latest_ref


def validate_open_knowledge() -> None:
    governance = core.load_json("policy/governance-status.json")
    rules = core.load_json("policy/decision-rules.json")
    projection = core.load_json(OPEN_KNOWLEDGE_STATUS_PATH)
    policy_path = core.repo_file(OPEN_KNOWLEDGE_POLICY_PATH, "Open Knowledge policy")
    policy_text = policy_path.read_text(encoding="utf-8")

    _validate_policy_semantics(policy_text)
    _validate_projection_invariants(projection, rules)
    core.require(projection.get("policy_version") in policy_text, "Open Knowledge projection version not identified by human policy")

    if governance.get("operative") is not True:
        core.require(projection.get("status") == "draft", "non-operative governance requires draft Open Knowledge projection")
        core.require(projection.get("operative") is False, "non-operative governance cannot expose operative Open Knowledge state")
        core.require("-DRAFT" in str(projection.get("policy_version")), "draft Open Knowledge projection must use a DRAFT version")
        core.require(projection.get("policy_sha256") is None, "draft Open Knowledge projection cannot claim adopted policy bytes")
        core.require(projection.get("effective_date") is None, "draft Open Knowledge projection cannot claim an effective date")
        core.require(projection.get("rights_review_record") is None, "draft Open Knowledge projection cannot claim rights review")
        core.require(projection.get("adoption_record") is None, "draft Open Knowledge projection cannot claim adoption")
        core.require(core.contradictory_status_declaration(policy_text), "draft Open Knowledge human policy must declare draft/non-operative status")
        return

    core.require(projection.get("operative") is True, "operative governance requires operative Open Knowledge implementation")
    core.require(projection.get("status") in {"adopted", "operative"}, "operative Open Knowledge implementation must be adopted")
    version = projection.get("policy_version")
    core.require(isinstance(version, str) and version and "-DRAFT" not in version, "operative Open Knowledge policy version cannot be draft")
    policy_sha = core.require_sha256(projection.get("policy_sha256"), "Open Knowledge policy_sha256")
    core.require(core.sha256_file(policy_path) == policy_sha, "Open Knowledge policy bytes do not match adopted SHA-256")
    core.require(not core.contradictory_status_declaration(policy_text), "operative Open Knowledge policy still declares draft/non-operative status")
    core.require_version_header(policy_text, version, "Open Knowledge policy")

    latest_release, latest_ref = _validate_release_history(governance)
    latest_binding = latest_release.get("open_knowledge_binding")
    expected_policy_binding = {
        "path": OPEN_KNOWLEDGE_POLICY_PATH,
        "version": version,
        "sha256": policy_sha,
    }
    expected_latest_binding = {
        "policy": expected_policy_binding,
        "rights_review_record": projection.get("rights_review_record"),
        "effective_date": projection.get("effective_date"),
        "core_rule": "canonicality-is-not-exclusivity",
        "anti_enclosure_mission_lock_subject": "permit-enclosure-of-established-ec-public-knowledge",
    }
    core.require(latest_binding == expected_latest_binding, "current Open Knowledge projection does not exactly equal the latest release binding")
    core.require(projection.get("adoption_record") == latest_ref, "Open Knowledge projection must bind the latest validated governance adoption record")

    effective = core.parse_iso_date(projection.get("effective_date"), "Open Knowledge effective_date")
    governance_effective = core.parse_iso_date(governance.get("effective_date"), "governance effective_date")
    core.require(effective <= governance_effective, "Open Knowledge implementation must be effective no later than current governance")


if __name__ == "__main__":
    validate_open_knowledge()
    print("Exergism Commons Open Knowledge integrity: PASS")
