#!/usr/bin/env python3
"""Mutation guards for recurring adversarial governance-validation bug classes.

These are not examples of reachable production workflows. They deliberately
exercise the attack classes that repeatedly appear in adversarial review:
closed-world key deletion, paired-source weakening, taxonomy redefinition,
parser ambiguity, unsigned authority envelopes and semantic values changed
while local hashes/equality would still agree.
"""

from __future__ import annotations

import copy
import io
import json

import governance_cla_schedule_binding as schedule
import governance_open_knowledge as open_knowledge
import governance_review_auth as review_auth
import governance_semantic_invariants as invariants
import governance_strict_json as strict_json
import governance_strict_yaml as strict_yaml
import validate_governance as core


def expect_failure(label: str, callback) -> None:
    try:
        callback()
    except SystemExit:
        return
    raise SystemExit(f"governance mutation guard failure: {label} unexpectedly validated")


def mutated_value(value):
    if isinstance(value, bool):
        return not value
    if isinstance(value, str):
        return value + "-MUTATED"
    if isinstance(value, int):
        return value + 1
    if value is None:
        return "MUTATED"
    return "MUTATED"


def validate_json_ambiguity_matrix() -> int:
    """Prove duplicate names fail regardless of nesting/decoder entry point."""
    cases = 0
    expect_failure(
        "duplicate JSON top-level object name",
        lambda: json.loads('{"mission_locked_subjects": ["weakened"], "mission_locked_subjects": ["canonical"]}'),
    )
    cases += 1
    expect_failure(
        "duplicate JSON nested object name",
        lambda: json.loads('{"authority": {"operative": false, "operative": true}}'),
    )
    cases += 1
    expect_failure(
        "duplicate JSON through file decoder",
        lambda: json.load(io.StringIO('{"review": {"result": "rejected", "result": "approved"}}')),
    )
    cases += 1
    return cases


def _synthetic_review() -> dict:
    review = {
        "record_type": "qualified-legal-review-evidence",
        "status": "final",
        "complete": True,
        "result": "approved",
        "governance_version": "1.0",
        "review_id": "review-test-001",
        "completed_date": "2026-01-01",
        "reviewed_open_knowledge_policy": {
            "path": "OPEN-KNOWLEDGE-POLICY.md",
            "version": "1.0",
            "sha256": "0" * 64,
        },
        "reviewers": [
            {
                "reviewer_id": "reviewer-1",
                "qualification_evidence": {"path": "records/evidence/q.json", "sha256": "1" * 64},
                "signature_evidence": {"path": "records/evidence/s.json", "sha256": "2" * 64},
            }
        ],
    }
    payload = {key: value for key, value in review.items() if key != "reviewers"}
    review["review_payload_sha256"] = core.sha256_json(payload)
    return review


def validate_review_auth_mutation_matrix() -> int:
    baseline = _synthetic_review()
    review_auth.require_authentication_shape(baseline, "synthetic qualified review")
    cases = 0

    missing_reviewers = copy.deepcopy(baseline)
    del missing_reviewers["reviewers"]
    expect_failure(
        "qualified review cannot delete reviewer authentication",
        lambda: review_auth.require_authentication_shape(missing_reviewers, "synthetic qualified review"),
    )
    cases += 1

    empty_reviewers = copy.deepcopy(baseline)
    empty_reviewers["reviewers"] = []
    expect_failure(
        "qualified review cannot use an empty reviewer set",
        lambda: review_auth.require_authentication_shape(empty_reviewers, "synthetic qualified review"),
    )
    cases += 1

    missing_digest = copy.deepcopy(baseline)
    del missing_digest["review_payload_sha256"]
    expect_failure(
        "qualified review cannot omit exact payload digest",
        lambda: review_auth.require_authentication_shape(missing_digest, "synthetic qualified review"),
    )
    cases += 1

    replayed_conclusion = copy.deepcopy(baseline)
    replayed_conclusion["result"] = "rejected"
    expect_failure(
        "qualified review signatures cannot be replayed after payload mutation",
        lambda: review_auth.require_authentication_shape(replayed_conclusion, "synthetic qualified review"),
    )
    cases += 1

    duplicate_reviewer = copy.deepcopy(baseline)
    duplicate_reviewer["reviewers"].append(copy.deepcopy(duplicate_reviewer["reviewers"][0]))
    expect_failure(
        "qualified review cannot duplicate reviewer identity",
        lambda: review_auth.require_authentication_shape(duplicate_reviewer, "synthetic qualified review"),
    )
    cases += 1

    return cases


def validate_open_knowledge_mutation_matrix() -> int:
    rules = core.load_json("policy/decision-rules.json")
    projection = core.load_json("policy/open-knowledge-status.json")
    open_knowledge._validate_projection_invariants(projection, rules)
    cases = 0

    # Closed-world top-level schema: deleting or adding any authoritative field
    # must fail rather than degrade into a permissive subset check.
    for key in sorted(invariants.OPEN_KNOWLEDGE_TOP_LEVEL_KEYS_V1):
        mutated = copy.deepcopy(projection)
        del mutated[key]
        expect_failure(f"Open Knowledge delete top-level {key}", lambda m=mutated: open_knowledge._validate_projection_invariants(m, rules))
        cases += 1
    mutated = copy.deepcopy(projection)
    mutated["unexpected_authority_field"] = True
    expect_failure("Open Knowledge add undeclared top-level field", lambda: open_knowledge._validate_projection_invariants(mutated, rules))
    cases += 1

    mappings = (
        "ec_publication_requirements",
        "anti_enclosure",
        "license_implementation",
        "authority_boundaries",
        "project_relationships",
        "adoption_requirements",
        "integrity_contract",
        "history_contract",
    )
    for field in mappings:
        baseline = projection[field]
        for key, value in baseline.items():
            deleted = copy.deepcopy(projection)
            del deleted[field][key]
            expect_failure(
                f"Open Knowledge delete {field}.{key}",
                lambda m=deleted: open_knowledge._validate_projection_invariants(m, rules),
            )
            cases += 1

            changed = copy.deepcopy(projection)
            changed[field][key] = mutated_value(value)
            expect_failure(
                f"Open Knowledge mutate {field}.{key}",
                lambda m=changed: open_knowledge._validate_projection_invariants(m, rules),
            )
            cases += 1

        added = copy.deepcopy(projection)
        added[field]["unexpected_semantic_field"] = True
        expect_failure(
            f"Open Knowledge extend closed mapping {field}",
            lambda m=added: open_knowledge._validate_projection_invariants(m, rules),
        )
        cases += 1

    for field in ("protected_freedoms", "excluded_or_protected_material"):
        removed = copy.deepcopy(projection)
        removed[field] = removed[field][1:]
        expect_failure(f"Open Knowledge shrink {field}", lambda m=removed: open_knowledge._validate_projection_invariants(m, rules))
        cases += 1
        added = copy.deepcopy(projection)
        added[field].append("unexpected-semantic-value")
        expect_failure(f"Open Knowledge extend {field}", lambda m=added: open_knowledge._validate_projection_invariants(m, rules))
        cases += 1

    weakened_rules = copy.deepcopy(rules)
    weakened_rules["mission_locked_subjects"] = [
        item for item in weakened_rules["mission_locked_subjects"] if item != "permit-enclosure-of-established-ec-public-knowledge"
    ]
    expect_failure(
        "Mission Lock omit anti-enclosure subject",
        lambda: open_knowledge._validate_projection_invariants(projection, weakened_rules),
    )
    cases += 1

    return cases


def validate_schedule_mutation_matrix() -> int:
    strict_yaml.install()
    schedule_text = (core.ROOT / "cla/PROJECT-SCHEDULE.md").read_text(encoding="utf-8")
    status_text = (core.ROOT / "policy/cla-status.yaml").read_text(encoding="utf-8")
    projects_text = (core.ROOT / "policy/covered-projects.yaml").read_text(encoding="utf-8")

    rights = schedule.parse_schedule_rights_manifest(schedule_text)
    projection = schedule.parse_projection_repositories(projects_text)
    normalized = schedule.normalized_projection_rights(projection)
    schedule.validate_rights_semantic_invariants(normalized, "baseline covered-projects projection")
    schedule.validate_schedule_projection_manifest(status_text, projects_text)
    cases = 0

    # This models the recurring paired-edit attack directly: even if both the
    # human manifest and YAML projection were changed to the same value, the
    # independent closed-world schema must reject the semantic mutation.
    for repository, repo_data in invariants.SCHEDULE_RIGHTS_MANIFEST_V1.items():
        changed = copy.deepcopy(invariants.SCHEDULE_RIGHTS_MANIFEST_V1)
        changed[repository]["cla_patent_grant"] = "implied-by-contribution"
        expect_failure(
            f"paired Schedule/YAML patent mutation {repository}",
            lambda m=changed: schedule.validate_rights_semantic_invariants(m, "mutated paired projection"),
        )
        cases += 1

        for material_id, rights_fields in repo_data["material_classes"].items():
            for key, value in rights_fields.items():
                deleted = copy.deepcopy(invariants.SCHEDULE_RIGHTS_MANIFEST_V1)
                del deleted[repository]["material_classes"][material_id][key]
                expect_failure(
                    f"paired Schedule/YAML delete {repository}/{material_id}/{key}",
                    lambda m=deleted: schedule.validate_rights_semantic_invariants(m, "mutated paired projection"),
                )
                cases += 1

                changed = copy.deepcopy(invariants.SCHEDULE_RIGHTS_MANIFEST_V1)
                changed[repository]["material_classes"][material_id][key] = value + "-MUTATED"
                expect_failure(
                    f"paired Schedule/YAML mutate {repository}/{material_id}/{key}",
                    lambda m=changed: schedule.validate_rights_semantic_invariants(m, "mutated paired projection"),
                )
                cases += 1

            extra = copy.deepcopy(invariants.SCHEDULE_RIGHTS_MANIFEST_V1)
            extra[repository]["material_classes"][material_id]["capability_license_boundary"] = "unexpected-added-boundary"
            if "capability_license_boundary" not in rights_fields:
                expect_failure(
                    f"paired Schedule/YAML add sensitive field {repository}/{material_id}",
                    lambda m=extra: schedule.validate_rights_semantic_invariants(m, "mutated paired projection"),
                )
                cases += 1

    taxonomy_weakened = projects_text.replace(
        "  final_states:\n    - covered\n    - excluded",
        "  final_states:\n    - proposed\n    - excluded",
        1,
    )
    expect_failure("redefine provisional coverage as final", lambda: schedule.validate_coverage_state_contract(taxonomy_weakened))
    cases += 1

    binding_weakened = projects_text.replace(
        "  exact_repository_rights_fields_required: true",
        "  exact_repository_rights_fields_required: false",
        1,
    )
    expect_failure(
        "disable exact repository rights binding",
        lambda: schedule.validate_schedule_projection_manifest(status_text, binding_weakened),
    )
    cases += 1

    retroactive = projects_text.replace(
        "  schedule_updates_may_expand_rights_for_prior_contributions: false",
        "  schedule_updates_may_expand_rights_for_prior_contributions: true",
        1,
    )
    expect_failure(
        "enable retroactive Schedule rights expansion",
        lambda: schedule.validate_schedule_projection_manifest(status_text, retroactive),
    )
    cases += 1

    return cases


def main() -> None:
    strict_json.install()
    json_cases = validate_json_ambiguity_matrix()
    review_cases = validate_review_auth_mutation_matrix()
    open_knowledge_cases = validate_open_knowledge_mutation_matrix()
    schedule_cases = validate_schedule_mutation_matrix()
    total = json_cases + review_cases + open_knowledge_cases + schedule_cases
    print(
        "Exergism Commons adversarial mutation guards: PASS "
        f"({total} generalized mutations; JSON ambiguity={json_cases}, review auth={review_cases}, "
        f"Open Knowledge={open_knowledge_cases}, Schedule/rights={schedule_cases})"
    )


if __name__ == "__main__":
    main()