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


def rewrite(path: Path, replacements: tuple[tuple[str, str], ...]) -> bool:
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
        ),
    ):
        changed.append(validator.relative_to(ROOT).as_posix())

    # The public explanatory page was still advertising commons# as the
    # Governance vocabulary. Only that exact presentation string moves.
    site = ROOT / "docs" / "index.html"
    if rewrite(
        site,
        (
            (
                "Governance vocabulary</span><code>https://id.exergism.org/commons#",
                "Governance vocabulary</span><code>https://id.exergism.org/governance#",
            ),
        ),
    ):
        changed.append(site.relative_to(ROOT).as_posix())

    print(f"migrated {len(changed)} Governance namespace files")
    for item in changed:
        print(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
