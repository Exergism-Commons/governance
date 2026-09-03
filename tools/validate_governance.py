#!/usr/bin/env python3
"""Deterministic integrity checks for EC draft organization governance.

This validates machine-readable consistency. It does not determine legal validity.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NS = "https://id.exergism.org/commons#"
ONTOLOGY_IRI = "https://id.exergism.org/ontology/commons"


def load_json(path: str):
    p = ROOT / path
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def require(condition: bool, message: str):
    if not condition:
        raise SystemExit(f"governance integrity failure: {message}")


def main() -> None:
    status = load_json("policy/governance-status.json")
    rules = load_json("policy/decision-rules.json")
    delegations = load_json("policy/delegations.json")
    context = load_json("ontology/commons-context.jsonld")

    require(status["schema_version"] == 1, "unsupported governance status schema")
    require(status["vocabulary_namespace"] == NS, "unexpected commons namespace")
    require(status["ontology_iri"] == ONTOLOGY_IRI, "unexpected commons ontology IRI")
    require(status["governance_version"] == rules["governance_version"], "status/rules version mismatch")
    require(status["governance_version"] == delegations["governance_version"], "status/delegations version mismatch")

    if not status["operative"]:
        require(status["institutional_state"] == "bootstrap", "non-operative status must remain bootstrap")
        require(status["legal_entity"] is None, "bootstrap must not fabricate a legal entity")
        require(status["effective_date"] is None, "bootstrap must not fabricate an effective date")
        require(status["adoption_record"] is None, "bootstrap must not fabricate an adoption record")
        require(rules["operative"] is False, "draft decision rules cannot be operative")
        require(delegations["operative"] is False, "draft delegations cannot be operative")
        require(delegations["delegations"] == [], "bootstrap cannot contain operative-looking delegations")

    by_id = {r["id"]: r for r in rules["rules"]}
    require(set(by_id) == {"ordinary-approval", "qualified-approval", "constitutional-amendment"}, "unexpected decision rule set")

    ordinary = by_id["ordinary-approval"]
    qualified = by_id["qualified-approval"]
    constitutional = by_id["constitutional-amendment"]

    require(ordinary["iri"] == NS + "OrdinaryApproval", "ordinary approval IRI mismatch")
    require(qualified["iri"] == NS + "QualifiedApproval", "qualified approval IRI mismatch")
    require(constitutional["iri"] == NS + "ConstitutionalAmendment", "constitutional amendment IRI mismatch")

    require(ordinary["quorum"]["operator"] == ">" and ordinary["quorum"]["value"] == 0.5, "ordinary quorum changed unexpectedly")
    require(qualified["quorum"]["operator"] == ">=" and qualified["quorum"]["value"] >= 2 / 3, "qualified quorum below two thirds")
    require(qualified["approval"]["operator"] == ">=" and qualified["approval"]["value"] >= 2 / 3, "qualified approval below two thirds")
    require(constitutional["approval"]["operator"] == ">=" and constitutional["approval"]["value"] >= 0.75, "constitutional approval below three quarters")

    conflicts = rules["conflict_rules"]
    require(conflicts["self_compensation_recusal_required"] is True, "self-compensation recusal must remain required")
    require(conflicts["self_contract_approval_prohibited"] is True, "self-contract approval must remain prohibited")
    require(conflicts["funding_does_not_create_governance_rights"] is True, "funding must not create governance rights")

    qualified_subjects = set(rules["mandatory_qualified_subjects"])
    for subject in {
        "endowment-principal-withdrawal",
        "persistent-domain-transfer",
        "identifier-authority-transfer",
        "organization-wide-exclusive-ip-transfer",
        "institutional-merger-dissolution-or-succession",
    }:
        require(subject in qualified_subjects, f"qualified-approval subject missing: {subject}")

    ctx = context["@context"]
    require(ctx["ec"] == NS, "JSON-LD context namespace mismatch")

    ontology = (ROOT / "ontology/commons.ttl").read_text(encoding="utf-8")
    shapes = (ROOT / "ontology/governance-shapes.ttl").read_text(encoding="utf-8")
    constitution = (ROOT / "CONSTITUTION.md").read_text(encoding="utf-8")
    machine_spec = (ROOT / "spec/MACHINE-READABLE-GOVERNANCE.md").read_text(encoding="utf-8")

    require(ONTOLOGY_IRI in ontology, "ontology document IRI missing")
    for term in ("OrdinaryApproval", "QualifiedApproval", "ConstitutionalAmendment", "Delegation", "PersistentIdentifierAuthority"):
        require(f"ec:{term}" in ontology, f"ontology term missing: {term}")
    require("owl:propertyChainAxiom" not in ontology, "property-chain authority inference is forbidden")
    require("ec:GovernanceDecisionShape" in shapes, "governance decision SHACL shape missing")
    require("non-operative" in constitution.lower(), "constitution must state non-operative status")
    require("conforming graph is not proof" in machine_spec.lower(), "machine/legal authority boundary missing")

    print("Exergism Commons governance integrity: PASS")
    print(f"governance_version={status['governance_version']} operative={status['operative']} state={status['institutional_state']}")
    print(f"decision_rules={len(rules['rules'])} delegations={len(delegations['delegations'])}")


if __name__ == "__main__":
    main()
