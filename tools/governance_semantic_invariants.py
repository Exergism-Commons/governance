from __future__ import annotations

"""Closed-world semantic invariants for governance-sensitive projections.

These constants deliberately sit outside the mutable human/machine projection pairs.
For a declared schema version, changing both sides of a projection in lockstep is
not enough to weaken the institutional invariant: the schema contract must also
be changed explicitly and reviewed as code.
"""

OPEN_KNOWLEDGE_TOP_LEVEL_KEYS_V1 = {
    "schema_version",
    "policy",
    "policy_version",
    "policy_artifact",
    "policy_sha256",
    "status",
    "operative",
    "effective_date",
    "rights_review_record",
    "adoption_record",
    "constitutional_principle",
    "core_rule",
    "protected_freedoms",
    "ec_publication_requirements",
    "anti_enclosure",
    "license_implementation",
    "authority_boundaries",
    "project_relationships",
    "excluded_or_protected_material",
    "adoption_requirements",
    "integrity_contract",
    "history_contract",
    "notes",
}

OPEN_KNOWLEDGE_PROTECTED_FREEDOMS_V1 = {
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

OPEN_KNOWLEDGE_PUBLICATION_REQUIREMENTS_V1 = {
    "source_form_available": True,
    "open_documented_format_preferred": True,
    "versioned_source": True,
    "clonable_or_exportable": True,
    "rendered_representation_alone_sufficient": False,
    "api_only_publication_sufficient": False,
}

OPEN_KNOWLEDGE_ANTI_ENCLOSURE_V1 = {
    "copyright_enclosure": False,
    "database_right_enclosure": False,
    "contractual_enclosure": False,
    "drm_enclosure": False,
    "repository_or_api_exclusivity": False,
    "legitimate_confidentiality_exceptions": True,
}

OPEN_KNOWLEDGE_LICENSE_IMPLEMENTATION_V1 = {
    "constitutional_lock_on_specific_license": False,
    "default_open_share_alike_content_candidate": "CC-BY-SA-4.0",
    "database_specific_candidate": "ODbL-1.0-for-project-specific-consideration",
    "software_license_inferred_from_content_policy": False,
    "explicit_file_terms_control": True,
    "historical_relicensing_by_governance_vote": False,
}

OPEN_KNOWLEDGE_AUTHORITY_BOUNDARIES_V1 = {
    "copying_transfers_canonicality": False,
    "copying_transfers_namespace_authority": False,
    "copying_grants_trademark_rights": False,
    "publication_or_contribution_grants_patent_rights": False,
    "id_resolver_relicenses_source_material": False,
}

OPEN_KNOWLEDGE_PROJECT_RELATIONSHIPS_V1 = {
    "exergism": "existing-cc-by-sa-content-apache-tooling-boundary-preserved",
    "ecl": "capability-license-separate-from-open-knowledge-supporting-records",
    "ecl_dossiers_and_evidence": "open-knowledge-target-after-valid-project-license-adoption",
    "ecl_pl": "public-knowledge-development-material-separate-from-express-patent-grants",
    "funding": "open-knowledge-target-after-valid-project-license-adoption",
    "governance": "open-knowledge-target-after-valid-project-license-adoption",
    "id_exergism_org": "resolver-and-persistence-surface-not-relicensing-authority",
}

OPEN_KNOWLEDGE_EXCLUDED_MATERIAL_V1 = {
    "unnecessary-or-unlawful-personal-data",
    "private-signatures-and-identity-evidence",
    "credentials-and-recovery-material",
    "temporarily-embargoed-security-details",
    "privileged-or-confidential-records",
    "third-party-material-without-relicensing-authority",
    "legally-restricted-material",
}

OPEN_KNOWLEDGE_ADOPTION_REQUIREMENTS_V1 = {
    "project_specific_material_classification": True,
    "exact_outbound_license_per_class": True,
    "rights_authority_or_chain_of_title_review": True,
    "third_party_material_treatment": True,
    "source_form_rule": True,
    "historical_vs_future_scope": True,
    "effective_release_or_decision_record": True,
    "qualified_legal_review_before_organization_level_operation": True,
}

OPEN_KNOWLEDGE_INTEGRITY_CONTRACT_V1 = {
    "human_policy_path_fixed": True,
    "operative_policy_requires_exact_sha256": True,
    "operative_policy_requires_rights_review": True,
    "operative_policy_requires_governance_adoption_binding": True,
    "governance_cannot_be_operative_while_policy_is_draft": True,
    "closed_world_schema_required": True,
    "release_history_binding_required": True,
    "paired_projection_edits_cannot_weaken_semantics": True,
}

OPEN_KNOWLEDGE_HISTORY_CONTRACT_V1 = {
    "founding_release_must_bind_open_knowledge": True,
    "every_operative_release_must_bind_open_knowledge": True,
    "later_release_cannot_repair_missing_founding_binding": True,
    "policy_change_requires_new_rights_review": True,
    "policy_change_effective_with_authorizing_release": True,
    "current_projection_must_equal_latest_release_binding": True,
    "historical_release_binding_cannot_be_rewritten_by_later_release": True,
}

MISSION_LOCKED_SUBJECTS_V1 = {
    "repurpose-exergism-commons-away-from-exergism",
    "remove-project-authority-separation",
    "create-membership-economic-ownership",
    "permit-funding-to-purchase-organization-governance",
    "permit-retroactive-fabrication-of-contributor-rights",
    "permit-silent-persistent-identifier-repurposing",
    "remove-structural-contestability-or-anti-capture-commitment",
    "permit-enclosure-of-established-ec-public-knowledge",
}

SCHEDULE_BINDING_CONTRACT_V2 = {
    "authoritative_schedule_artifact": "cla/PROJECT-SCHEDULE.md",
    "exact_repository_set_required": True,
    "exact_material_class_id_set_per_repository_required": True,
    "exact_repository_rights_fields_required": True,
    "exact_material_rights_fields_required": True,
}

COVERAGE_FINAL_STATES_V2 = {"covered", "excluded"}
COVERAGE_PROVISIONAL_STATES_V2 = {
    "proposed",
    "proposed-after-outbound-review",
    "bootstrap-not-retroactive",
}

COVERED_PROJECTS_NON_RETROACTIVITY_V2 = {
    "schedule_updates_may_expand_rights_for_prior_contributions": False,
    "exception": "only-if-prior-agreement-already-authorized-successor-category-or-contributor-separately-consents",
}

# Schema v1 is intentionally closed-world. A legitimate future change to these
# rights-sensitive semantics must bump the manifest schema and update this
# validator contract rather than editing both the Schedule and YAML projection
# to the same weakened value.
SCHEDULE_RIGHTS_MANIFEST_V1 = {
    "Exergism-Commons/exergism": {
        "cla_patent_grant": "none",
        "material_classes": {
            "corpus-and-documentation": {
                "cla_outbound_family": "target-license-and-permitted-successors-compatible-with-open-knowledge"
            },
            "software-and-tooling": {
                "cla_outbound_family": "target-license-and-permitted-successors"
            },
        },
    },
    "Exergism-Commons/exergic-commons-license": {
        "cla_patent_grant": "none",
        "material_classes": {
            "ecl-project-lineage": {
                "cla_outbound_family": "ECL-project-purpose-plus-open-knowledge-family",
                "knowledge_outbound_family": "EC-open-knowledge-family-after-valid-project-adoption",
                "capability_license_boundary": "exact-ECL-Bundle-is-separate-from-supporting-public-knowledge",
            }
        },
    },
    "Exergism-Commons/ecl-patent-license": {
        "cla_patent_grant": "none",
        "material_classes": {
            "ecl-pl-project-lineage": {
                "cla_outbound_family": "ECL-PL-development-plus-open-knowledge-family",
                "knowledge_outbound_family": "EC-open-knowledge-family-after-valid-project-adoption",
            }
        },
    },
    "Exergism-Commons/.github": {
        "cla_patent_grant": "none",
        "material_classes": {
            "organization-profile-and-community-health": {
                "cla_outbound_family": "EC-open-knowledge-family-after-valid-outbound-adoption"
            }
        },
    },
    "Exergism-Commons/governance": {
        "cla_patent_grant": "none",
        "material_classes": {
            "organization-governance-and-legal-templates": {
                "cla_outbound_family": "EC-open-knowledge-family-after-valid-outbound-adoption"
            }
        },
    },
    "Exergism-Commons/funding": {
        "cla_patent_grant": "none",
        "material_classes": {
            "funding-governance-and-semantic-records": {
                "cla_outbound_family": "EC-open-knowledge-family-for-public-knowledge-with-explicit-software-license-for-tooling"
            }
        },
    },
    "Exergism-Commons/id.exergism-commons.github.io": {
        "cla_patent_grant": "none",
        "material_classes": {
            "identifier-resolver-software-and-site": {
                "cla_outbound_family": "explicit-software-tooling-license-plus-open-knowledge-family-for-public-documentation"
            },
            "identifier-published-representation-metadata": {
                "cla_outbound_family": "source-project-terms-plus-EC-open-knowledge-for-resolver-local-provenance-metadata"
            },
        },
    },
}
