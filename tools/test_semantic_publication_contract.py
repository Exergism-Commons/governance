#!/usr/bin/env python3
"""Fail-closed checks for Governance semantic publication and downstream use."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "policy" / "governance-status.json"
RULES = ROOT / "policy" / "decision-rules.json"
DOWNSTREAM = ROOT / "ontology" / "downstream-authority.json"
COMMONS = ROOT / "ontology" / "commons.ttl"
GOVERNANCE = ROOT / "ontology" / "governance.ttl"

COMMONS_VERSION = "0.1-PRE2"
GOVERNANCE_ONTOLOGY_VERSION = "0.1-PRE2"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    rules = json.loads(RULES.read_text(encoding="utf-8"))
    downstream = json.loads(DOWNSTREAM.read_text(encoding="utf-8"))
    commons = COMMONS.read_text(encoding="utf-8")
    governance = GOVERNANCE.read_text(encoding="utf-8")

    governance_version = status["governance_version"]
    require(rules["governance_version"] == governance_version, "decision rules governance version drift")
    require(downstream["governance_version"] == governance_version, "downstream governance version drift")
    require(downstream["operative"] is status["operative"], "downstream operative state drift")
    require(downstream["institutional_state"] == status["institutional_state"], "downstream institutional state drift")
    require(downstream["effective_date"] == status["effective_date"], "downstream effective date drift")
    require(downstream["adoption_record"] == status["adoption_record"], "downstream adoption record drift")

    declared_rule_iris = [rule["iri"] for rule in rules["rules"]]
    require(
        downstream["declared_decision_rule_iris"] == declared_rule_iris,
        "downstream decision-rule IRIs must exactly match policy/decision-rules.json",
    )

    emergency_iri = "https://id.exergism.org/governance#EmergencyAction"
    require(emergency_iri not in declared_rule_iris, "EmergencyAction must not appear without an adopted rule")
    require(downstream["emergency_action_policy_adopted"] is False, "draft governance must not expose emergency authority")

    if not status["operative"]:
        contract = downstream["downstream_contract"]
        require(contract["approved_records_authoritative"] is False, "non-operative governance cannot authorize approved downstream records")
        require(contract["operative_records_allowed"] is False, "non-operative governance cannot authorize operative downstream records")
        require(downstream["operative_decision_validation_available"] is False, "no operative downstream validator may be advertised in bootstrap")

    commons_version_iri = f"https://id.exergism.org/ontology/commons/{COMMONS_VERSION}"
    governance_version_iri = f"https://id.exergism.org/ontology/governance/{GOVERNANCE_ONTOLOGY_VERSION}"
    require(f'owl:versionInfo "{COMMONS_VERSION}"' in commons, "Commons versionInfo drift")
    require(f"owl:versionIRI <{commons_version_iri}>" in commons, "Commons versionIRI missing")
    require(f'owl:versionInfo "{GOVERNANCE_ONTOLOGY_VERSION}"' in governance, "Governance ontology versionInfo drift")
    require(f"owl:versionIRI <{governance_version_iri}>" in governance, "Governance versionIRI missing")
    require(f"owl:imports <{commons_version_iri}>" in governance, "Governance must import the immutable Commons version IRI")
    require("owl:imports <https://id.exergism.org/ontology/commons>" not in governance, "Governance must not import mutable Commons current IRI")
    require(downstream["governance_ontology_version"] == GOVERNANCE_ONTOLOGY_VERSION, "downstream ontology version drift")

    print("semantic publication and downstream authority contract verified")


if __name__ == "__main__":
    main()
