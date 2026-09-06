#!/usr/bin/env python3
"""Migrate the draft organization-governance projection out of commons#.

The pre-1.0 governance branch originally used commons# for both shared EC
primitives and institutional governance. This script moves only the governance
machine/state surfaces to governance#, leaving ontology/commons.* as the shared
cross-project vocabulary.
"""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OLD_NAMESPACE = "https://id.exergism.org/commons#"
OLD_ONTOLOGY = "https://id.exergism.org/ontology/commons"
GOVERNANCE_NAMESPACE = "https://id.exergism.org/governance#"
GOVERNANCE_ONTOLOGY = "https://id.exergism.org/ontology/governance"


def rewrite(
    path: Path,
    replacements: tuple[tuple[str, str], ...],
    *,
    optional: bool = False,
) -> bool:
    if not path.exists():
        if optional:
            return False
        raise FileNotFoundError(f"required migration input is missing: {path.relative_to(ROOT)}")

    before = path.read_text(encoding="utf-8")
    after = before
    for old, new in replacements:
        after = after.replace(old, new)
    if after == before:
        return False
    path.write_text(after, encoding="utf-8")
    return True


def main() -> int:
    changed: list[str] = []

    # Versioned machine policy is entirely institutional Governance. Any EC IRI
    # in these current draft policy projections therefore moves to governance#.
    for path in sorted((ROOT / "policy").glob("*.json")):
        if rewrite(path, ((OLD_NAMESPACE, GOVERNANCE_NAMESPACE), (OLD_ONTOLOGY, GOVERNANCE_ONTOLOGY))):
            changed.append(path.relative_to(ROOT).as_posix())

    validator = ROOT / "tools" / "validate_governance.py"
    if rewrite(
        validator,
        (
            (f'NS = "{OLD_NAMESPACE}"', f'NS = "{GOVERNANCE_NAMESPACE}"'),
            (f'ONTOLOGY_IRI = "{OLD_ONTOLOGY}"', f'ONTOLOGY_IRI = "{GOVERNANCE_ONTOLOGY}"'),
            ('"ontology/commons.ttl"', '"ontology/governance.ttl"'),
            ('"ontology/commons-context.jsonld"', '"ontology/governance-context.jsonld"'),
            (
                'require(context["@context"]["ec"] == NS, "JSON-LD namespace mismatch")',
                'require(context["@context"]["ecg"]["@id"] == NS, "JSON-LD namespace mismatch")',
            ),
            (
                'require(f"ec:{term}" in ontology, f"ontology term missing: {term}")',
                'require(f"ecg:{term}" in ontology, f"ontology term missing: {term}")',
            ),
            (
                'require("ec:GovernanceDecisionShape" in shapes and "ec:MembershipRecordShape" in shapes, "governance SHACL shapes missing")',
                'require("ecg:GovernanceDecisionShape" in shapes and "ecg:MembershipRecordShape" in shapes, "governance SHACL shapes missing")',
            ),
        ),
    ):
        changed.append(validator.relative_to(ROOT).as_posix())

    # Human entry points must advertise the same namespace split as the machine
    # artifacts, while keeping Commons clearly identified as shared vocabulary.
    readme = ROOT / "README.md"
    if rewrite(
        readme,
        (
            (
                "- [`ontology/commons.ttl`](ontology/commons.ttl) — organization governance vocabulary at `https://id.exergism.org/commons#`.\n- [`ontology/commons-context.jsonld`](ontology/commons-context.jsonld) — JSON-LD context.",
                "- [`ontology/commons.ttl`](ontology/commons.ttl) — shared cross-project EC primitives at `https://id.exergism.org/commons#`.\n- [`ontology/governance.ttl`](ontology/governance.ttl) — organization governance vocabulary at `https://id.exergism.org/governance#`.\n- [`ontology/commons-context.jsonld`](ontology/commons-context.jsonld) — shared Commons JSON-LD context.\n- [`ontology/governance-context.jsonld`](ontology/governance-context.jsonld) — Governance JSON-LD context, with shared Commons primitives imported through the `ec` prefix.",
            ),
            ("Funding may require `ec:QualifiedApproval`", "Funding may require `ecg:QualifiedApproval`"),
            (
                "Persistent organization vocabulary:\n\n- vocabulary: `https://id.exergism.org/commons#`\n- ontology: `https://id.exergism.org/ontology/commons`",
                "Persistent vocabularies:\n\n- shared Commons vocabulary: `https://id.exergism.org/commons#`\n- shared Commons ontology: `https://id.exergism.org/ontology/commons`\n- Governance vocabulary: `https://id.exergism.org/governance#`\n- Governance ontology: `https://id.exergism.org/ontology/governance`",
            ),
        ),
    ):
        changed.append(readme.relative_to(ROOT).as_posix())

    # Some deployments may also carry a generated explanatory site. It is not
    # part of the repository contract, so absence must not make materialization
    # fail. If present, keep its advertised Governance namespace consistent.
    site = ROOT / "docs" / "index.html"
    if rewrite(
        site,
        (
            (
                "Governance vocabulary</span><code>https://id.exergism.org/commons#",
                "Governance vocabulary</span><code>https://id.exergism.org/governance#",
            ),
        ),
        optional=True,
    ):
        changed.append(site.relative_to(ROOT).as_posix())

    print(f"migrated {len(changed)} Governance namespace files")
    for item in changed:
        print(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
