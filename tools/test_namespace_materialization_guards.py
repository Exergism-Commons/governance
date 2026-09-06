#!/usr/bin/env python3
"""Focused regressions for the pre-1.0 Governance namespace split."""

from __future__ import annotations

import tempfile
from pathlib import Path

import migrate_governance_namespace_v01 as migration


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"namespace-materialization guard failure: {message}")


def validate_synthetic_materialization() -> int:
    """Exercise the one-shot migration without a docs site being present."""

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / "policy").mkdir(parents=True)
        (root / "tools").mkdir(parents=True)

        (root / "policy" / "governance-status.json").write_text(
            '{"vocabulary_namespace":"https://id.exergism.org/commons#",'
            '"ontology_iri":"https://id.exergism.org/ontology/commons"}\n',
            encoding="utf-8",
        )
        (root / "tools" / "validate_governance.py").write_text(
            '\n'.join(
                [
                    'NS = "https://id.exergism.org/commons#"',
                    'ONTOLOGY_IRI = "https://id.exergism.org/ontology/commons"',
                    'context = load_json("ontology/commons-context.jsonld")',
                    'ontology = (ROOT / "ontology/commons.ttl").read_text(encoding="utf-8")',
                    'require(context["@context"]["ec"] == NS, "JSON-LD namespace mismatch")',
                    'require(f"ec:{term}" in ontology, f"ontology term missing: {term}")',
                    'require("ec:GovernanceDecisionShape" in shapes and "ec:MembershipRecordShape" in shapes, "governance SHACL shapes missing")',
                ]
            )
            + '\n',
            encoding="utf-8",
        )
        (root / "README.md").write_text(
            '\n'.join(
                [
                    '- [`ontology/commons.ttl`](ontology/commons.ttl) — organization governance vocabulary at `https://id.exergism.org/commons#`.',
                    '- [`ontology/commons-context.jsonld`](ontology/commons-context.jsonld) — JSON-LD context.',
                    '',
                    'Funding may require `ec:QualifiedApproval` for a protected decision.',
                    '',
                    'Persistent organization vocabulary:',
                    '',
                    '- vocabulary: `https://id.exergism.org/commons#`',
                    '- ontology: `https://id.exergism.org/ontology/commons`',
                ]
            )
            + '\n',
            encoding="utf-8",
        )
        # Deliberately do not create docs/index.html. The site is optional and
        # its absence was the original materialization failure.

        original_root = migration.ROOT
        try:
            migration.ROOT = root
            migration.main()
        finally:
            migration.ROOT = original_root

        validator = (root / "tools" / "validate_governance.py").read_text(encoding="utf-8")
        readme = (root / "README.md").read_text(encoding="utf-8")
        policy = (root / "policy" / "governance-status.json").read_text(encoding="utf-8")

        require('NS = "https://id.exergism.org/governance#"' in validator, "validator namespace not migrated")
        require('ONTOLOGY_IRI = "https://id.exergism.org/ontology/governance"' in validator, "validator ontology IRI not migrated")
        require('"ontology/governance-context.jsonld"' in validator, "Governance context path not migrated")
        require('context["@context"]["ecg"]["@id"] == NS' in validator, "Governance context assertion not migrated")
        require('f"ecg:{term}" in ontology' in validator, "Governance ontology term assertion not migrated")
        require('"ecg:GovernanceDecisionShape"' in validator, "Governance SHACL assertion not migrated")
        require("https://id.exergism.org/governance#" in policy, "policy namespace not migrated")
        require("https://id.exergism.org/ontology/governance" in policy, "policy ontology IRI not migrated")
        require("ontology/governance.ttl" in readme, "README Governance ontology entry missing")
        require("`ecg:QualifiedApproval`" in readme, "README decision-class prefix not migrated")
        require("Governance vocabulary: `https://id.exergism.org/governance#`" in readme, "README Governance namespace missing")
    return 11


def validate_materialized_repository_contract() -> int:
    shapes = (ROOT / "ontology" / "governance-shapes.ttl").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    context = (ROOT / "ontology" / "governance-context.jsonld").read_text(encoding="utf-8")

    require('sh:in ( "for" "against" "abstain" )' in shapes, "SHACL vote values differ from ballot values")
    require('sh:in ( "approve" "reject" "abstain" )' not in shapes, "legacy SHACL vote values remain")
    require("organization governance vocabulary at `https://id.exergism.org/commons#`" not in readme, "README still assigns Governance to Commons")
    require("`ec:QualifiedApproval`" not in readme, "README still mints QualifiedApproval in Commons")
    require('"ecg": {"@id": "https://id.exergism.org/governance#"' in context, "Governance context prefix missing")
    return 5


def main() -> None:
    total = validate_synthetic_materialization() + validate_materialized_repository_contract()
    print(f"Namespace-materialization guards: PASS ({total} cases)")


if __name__ == "__main__":
    main()
