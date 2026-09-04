from __future__ import annotations

import validate_governance as core


OPEN_KNOWLEDGE_STATUS_PATH = "policy/open-knowledge-status.json"
OPEN_KNOWLEDGE_POLICY_PATH = "OPEN-KNOWLEDGE-POLICY.md"

EXPECTED_MISSION_LOCKED_SUBJECTS = {
    "repurpose-exergism-commons-away-from-exergism",
    "remove-project-authority-separation",
    "create-membership-economic-ownership",
    "permit-funding-to-purchase-organization-governance",
    "permit-retroactive-fabrication-of-contributor-rights",
    "permit-silent-persistent-identifier-repurposing",
    "remove-structural-contestability-or-anti-capture-commitment",
    "permit-enclosure-of-established-ec-public-knowledge",
}

EXPECTED_FREEDOMS = {
    "access",
    "inspect",
    "reproduce",
    "study",
    "modify",
    "fork",
    "redistribute",
    "commercial-use",
    "non-commercial-use",
}

EXPECTED_AUTHORITY_BOUNDARIES = {
    "copying_transfers_canonicality": False,
    "copying_transfers_namespace_authority": False,
    "copying_grants_trademark_rights": False,
    "publication_or_contribution_grants_patent_rights": False,
    "id_resolver_relicenses_source_material": False,
}


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
    core.require(projection.get("policy") == "exergism-commons-open-knowledge", "unexpected Open Knowledge policy id")
    core.require(projection.get("policy_artifact") == OPEN_KNOWLEDGE_POLICY_PATH, "Open Knowledge policy path changed")
    core.require(projection.get("constitutional_principle") == "knowledge-commons-and-anti-enclosure", "Open Knowledge constitutional principle changed")
    core.require(projection.get("core_rule") == "canonicality-is-not-exclusivity", "Open Knowledge canonicality rule changed")
    core.require(set(projection.get("protected_freedoms") or []) == EXPECTED_FREEDOMS, "Open Knowledge protected-freedom set changed")

    publication = projection.get("ec_publication_requirements")
    core.require(
        publication == {
            "source_form_available": True,
            "open_documented_format_preferred": True,
            "versioned_source": True,
            "clonable_or_exportable": True,
            "rendered_representation_alone_sufficient": False,
            "api_only_publication_sufficient": False,
        },
        "Open Knowledge publication/source-form contract changed",
    )

    anti_enclosure = projection.get("anti_enclosure")
    core.require(
        anti_enclosure == {
            "copyright_enclosure": False,
            "database_right_enclosure": False,
            "contractual_enclosure": False,
            "drm_enclosure": False,
            "repository_or_api_exclusivity": False,
            "legitimate_confidentiality_exceptions": True,
        },
        "Open Knowledge anti-enclosure contract changed",
    )

    core.require(projection.get("authority_boundaries") == EXPECTED_AUTHORITY_BOUNDARIES, "Open Knowledge authority boundaries changed")

    licensing = projection.get("license_implementation")
    core.require(isinstance(licensing, dict), "Open Knowledge license implementation missing")
    core.require(licensing.get("constitutional_lock_on_specific_license") is False, "Constitution cannot be silently locked to one license brand")
    core.require(licensing.get("software_license_inferred_from_content_policy") is False, "Open Knowledge policy cannot infer a software license")
    core.require(licensing.get("explicit_file_terms_control") is True, "explicit file terms must retain precedence")
    core.require(licensing.get("historical_relicensing_by_governance_vote") is False, "governance cannot fabricate historical relicensing authority")

    relationships = projection.get("project_relationships")
    core.require(isinstance(relationships, dict), "Open Knowledge project relationships missing")
    core.require(relationships.get("ecl") == "capability-license-separate-from-open-knowledge-supporting-records", "ECL capability/knowledge boundary changed")
    core.require(relationships.get("ecl_pl") == "public-knowledge-development-material-separate-from-express-patent-grants", "ECL-PL patent boundary changed")
    core.require(relationships.get("id_exergism_org") == "resolver-and-persistence-surface-not-relicensing-authority", "id.exergism.org relicensing boundary changed")

    requirements = projection.get("adoption_requirements")
    core.require(isinstance(requirements, dict) and requirements, "Open Knowledge adoption requirements missing")
    core.require(all(value is True for value in requirements.values()), "Open Knowledge adoption requirements cannot be weakened")

    integrity = projection.get("integrity_contract")
    core.require(
        integrity == {
            "human_policy_path_fixed": True,
            "operative_policy_requires_exact_sha256": True,
            "operative_policy_requires_rights_review": True,
            "operative_policy_requires_governance_adoption_binding": True,
            "governance_cannot_be_operative_while_policy_is_draft": True,
        },
        "Open Knowledge integrity contract changed",
    )

    core.require(
        set(rules.get("mission_locked_subjects") or []) == EXPECTED_MISSION_LOCKED_SUBJECTS,
        "Mission Lock subject taxonomy does not exactly include the anti-enclosure invariant",
    )


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

    effective = core.parse_iso_date(projection.get("effective_date"), "Open Knowledge effective_date")
    governance_effective = core.parse_iso_date(governance.get("effective_date"), "governance effective_date")
    core.require(effective <= governance_effective, "Open Knowledge implementation must be effective no later than governance")

    activation = governance.get("activation_evidence")
    core.require(isinstance(activation, dict), "operative governance activation evidence missing")
    legal_review_ref = activation.get("qualified_legal_review")
    core.require(projection.get("rights_review_record") == legal_review_ref, "Open Knowledge rights review must be the governance-qualified legal review bound at activation")
    review, _ = core.validate_content_ref(legal_review_ref, "Open Knowledge rights review", "records/evidence")
    expected_review_binding = {
        "path": OPEN_KNOWLEDGE_POLICY_PATH,
        "version": version,
        "sha256": policy_sha,
    }
    core.require(review.get("reviewed_open_knowledge_policy") == expected_review_binding, "qualified legal review does not bind exact Open Knowledge policy bytes")

    adoption_ref = governance.get("adoption_record")
    core.require(projection.get("adoption_record") == adoption_ref, "Open Knowledge projection must bind the current validated governance adoption record")
    adoption, _ = core.validate_content_ref(adoption_ref, "Open Knowledge governance adoption binding", "records/adoptions")
    expected_adoption_binding = {
        "policy": expected_review_binding,
        "rights_review_record": legal_review_ref,
        "effective_date": projection.get("effective_date"),
        "core_rule": "canonicality-is-not-exclusivity",
        "anti_enclosure_mission_lock_subject": "permit-enclosure-of-established-ec-public-knowledge",
    }
    core.require(adoption.get("open_knowledge_binding") == expected_adoption_binding, "governance adoption does not bind the exact rights-reviewed Open Knowledge implementation")


if __name__ == "__main__":
    validate_open_knowledge()
    print("Exergism Commons Open Knowledge integrity: PASS")
