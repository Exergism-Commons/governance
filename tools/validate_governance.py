#!/usr/bin/env python3
"""Deterministic integrity checks for EC draft organization governance.

This validates machine-readable consistency and activation gates. It does not
itself determine legal validity.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NS = "https://id.exergism.org/commons#"
ONTOLOGY_IRI = "https://id.exergism.org/ontology/commons"


def load_json(path: str):
    with (ROOT / path).open("r", encoding="utf-8") as f:
        return json.load(f)


def require(condition: bool, message: str):
    if not condition:
        raise SystemExit(f"governance integrity failure: {message}")


def yaml_top_scalar(text: str, key: str):
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", text)
    require(match is not None, f"CLA status missing top-level key: {key}")
    raw = match.group(1)
    if raw == "null":
        return None
    if raw == "true":
        return True
    if raw == "false":
        return False
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    return raw


def yaml_block(text: str, key: str) -> str:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line == f"{key}:":
            out: list[str] = []
            for child in lines[i + 1 :]:
                if child and not child.startswith(" "):
                    break
                out.append(child)
            return "\n".join(out)
        if line.startswith(f"{key}:") and line != f"{key}:":
            return line.split(":", 1)[1].strip()
    raise SystemExit(f"governance integrity failure: CLA status missing block: {key}")


def yaml_block_list(text: str, key: str) -> list[str]:
    block = yaml_block(text, key)
    if block in ("[]", ""):
        return []
    values = []
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            values.append(stripped[2:].strip())
    return values


def yaml_nested_bool(text: str, parent: str, key: str) -> bool:
    block = yaml_block(text, parent)
    match = re.search(rf"(?m)^\s*{re.escape(key)}:\s*(true|false)\s*$", block)
    require(match is not None, f"CLA status missing {parent}.{key}")
    return match.group(1) == "true"


def exact_fraction(rule: dict, numerator: int, denominator: int, comparison: str) -> bool:
    return (
        rule.get("numerator") == numerator
        and rule.get("denominator") == denominator
        and rule.get("comparison") == comparison
    )


def validate_cla_status() -> None:
    text = (ROOT / "policy/cla-status.yaml").read_text(encoding="utf-8")
    operative = yaml_top_scalar(text, "operative")
    blockers = yaml_block_list(text, "activation_blockers")

    if operative is False:
        require(yaml_top_scalar(text, "status") == "draft", "non-operative CLA must remain draft")
        require(yaml_top_scalar(text, "legal_steward") is None, "draft CLA must not fabricate legal steward")
        require(yaml_top_scalar(text, "governing_law") is None, "draft CLA must not fabricate governing law")
        require(yaml_top_scalar(text, "effective_date") is None, "draft CLA must not fabricate effective date")
        require(len(blockers) > 0, "draft CLA must expose unresolved activation blockers")
        return

    require(operative is True, "CLA operative field must be boolean")
    require(yaml_top_scalar(text, "status") in {"adopted", "operative"}, "operative CLA must have adopted/operative status")
    require(bool(yaml_top_scalar(text, "legal_steward")), "operative CLA requires legal steward")
    require(bool(yaml_top_scalar(text, "governing_law")), "operative CLA requires governing law")
    require(bool(yaml_top_scalar(text, "effective_date")), "operative CLA requires effective date")
    require(bool(yaml_top_scalar(text, "privacy_records_policy")), "operative CLA requires privacy/records policy")
    require(len(yaml_block_list(text, "acceptance_methods")) > 0, "operative CLA requires acceptance method")
    require(yaml_nested_bool(text, "legal_review", "complete") is True, "operative CLA requires completed legal review")
    require(len(yaml_block_list(yaml_block(text, "legal_review"), "records")) > 0, "operative CLA requires legal review record")
    require(blockers == [], "operative CLA cannot retain activation blockers")
    require("-DRAFT" not in str(yaml_top_scalar(text, "individual_version")), "operative individual CLA version cannot be draft")
    require("-DRAFT" not in str(yaml_top_scalar(text, "entity_version")), "operative entity CLA version cannot be draft")
    require("-DRAFT" not in str(yaml_top_scalar(text, "project_schedule_version")), "operative project schedule cannot be draft")


def main() -> None:
    status = load_json("policy/governance-status.json")
    rules = load_json("policy/decision-rules.json")
    delegations = load_json("policy/delegations.json")
    membership = load_json("policy/membership-status.json")
    founding = load_json("policy/founding-stewardship.json")
    context = load_json("ontology/commons-context.jsonld")

    require(status["schema_version"] == 2, "unsupported governance status schema")
    require(rules["schema_version"] == 2, "unsupported decision rules schema")
    require(membership["schema_version"] == 1, "unsupported membership schema")
    require(founding["schema_version"] == 1, "unsupported founding stewardship schema")
    require(status["vocabulary_namespace"] == NS, "unexpected commons namespace")
    require(status["ontology_iri"] == ONTOLOGY_IRI, "unexpected commons ontology IRI")

    version = status["governance_version"]
    for name, obj in {
        "rules": rules,
        "delegations": delegations,
        "membership": membership,
        "founding stewardship": founding,
    }.items():
        require(obj["governance_version"] == version, f"status/{name} version mismatch")

    if status["operative"] is False:
        require(status["institutional_state"] == "bootstrap", "non-operative status must remain bootstrap")
        require(status["institutional_phase"] == "F0-founder-led-bootstrap", "draft bootstrap must remain F0")
        require(status["legal_entity"] is None, "bootstrap must not fabricate a legal entity")
        require(status["governing_law"] is None, "bootstrap must not fabricate governing law")
        require(status["effective_date"] is None, "bootstrap must not fabricate an effective date")
        require(status["adoption_record"] is None, "bootstrap must not fabricate an adoption record")
        for flag in (
            "initial_member_registry_adopted",
            "conflict_process_adopted",
            "records_privacy_process_adopted",
            "treasury_controls_adopted",
            "founding_steward_assignment_adopted",
            "succession_process_adopted",
            "qualified_legal_review_complete",
        ):
            require(status[flag] is False, f"bootstrap adoption flag must be false: {flag}")
        require(rules["operative"] is False, "draft decision rules cannot be operative")
        require(delegations["operative"] is False, "draft delegations cannot be operative")
        require(delegations["delegations"] == [], "bootstrap cannot contain operative-looking delegations")
        require(membership["operative"] is False, "draft membership registry cannot be operative")
        require(membership["registry_state"] == "bootstrap", "draft membership registry must remain bootstrap")
        require(all(m.get("operative_membership") is False for m in membership["members"]), "bootstrap cannot contain operative members")
        require(founding["operative"] is False, "draft founding stewardship cannot be operative")
        require(founding["founding_steward"]["operative_assignment"] is False, "bootstrap cannot fabricate operative founder assignment")
        require(founding["mission_lock"]["operative"] is False, "draft Mission Lock cannot be operative")
    else:
        require(status["operative"] is True, "governance operative field must be boolean")
        require(status["institutional_state"] != "bootstrap", "operative governance cannot remain bootstrap")
        require(status["institutional_phase"] in {"F0-founder-led-bootstrap", "F1-early-institution", "F2-distributed-institution"}, "invalid operative institutional phase")
        require(bool(status["legal_entity"]), "operative governance requires legal entity")
        require(bool(status["governing_law"]), "operative governance requires governing law")
        require(bool(status["effective_date"]), "operative governance requires effective date")
        require(bool(status["adoption_record"]), "operative governance requires adoption record")
        for flag in (
            "initial_member_registry_adopted",
            "conflict_process_adopted",
            "records_privacy_process_adopted",
            "treasury_controls_adopted",
            "founding_steward_assignment_adopted",
            "succession_process_adopted",
            "qualified_legal_review_complete",
        ):
            require(status[flag] is True, f"operative governance requires adoption flag: {flag}")
        require(rules["operative"] is True, "operative governance requires operative decision rules")
        require(delegations["operative"] is True, "operative governance requires operative delegation registry")
        require(membership["operative"] is True, "operative governance requires operative membership registry")
        require(membership["registry_state"] == "operative", "operative membership registry must say operative")
        require(any(m.get("operative_membership") is True for m in membership["members"]), "operative governance requires at least one operative member")
        require(founding["operative"] is True, "operative governance requires operative founding stewardship record")
        require(founding["founding_steward"]["operative_assignment"] is True, "operative F0/F1 governance requires adopted founder assignment")
        require(founding["mission_lock"]["operative"] is True, "operative governance requires operative Mission Lock")

    by_id = {r["id"]: r for r in rules["rules"]}
    require(set(by_id) == {"ordinary-approval", "qualified-approval", "constitutional-amendment", "mission-locked-amendment"}, "unexpected decision rule set")

    ordinary = by_id["ordinary-approval"]
    qualified = by_id["qualified-approval"]
    constitutional = by_id["constitutional-amendment"]
    mission = by_id["mission-locked-amendment"]

    require(ordinary["iri"] == NS + "OrdinaryApproval", "ordinary approval IRI mismatch")
    require(qualified["iri"] == NS + "QualifiedApproval", "qualified approval IRI mismatch")
    require(constitutional["iri"] == NS + "ConstitutionalAmendment", "constitutional amendment IRI mismatch")
    require(mission["iri"] == NS + "MissionLockedAmendment", "mission-locked amendment IRI mismatch")

    require(exact_fraction(ordinary["quorum"], 1, 2, "strictly_greater_than"), "ordinary quorum must be exactly > 1/2")
    require(ordinary["approval"]["comparison"] == "strictly_greater_than", "ordinary approval comparison changed")
    require(exact_fraction(qualified["quorum"], 2, 3, "at_least"), "qualified quorum must be exactly >= 2/3")
    require(exact_fraction(qualified["approval"], 2, 3, "at_least"), "qualified approval must be exactly >= 2/3")
    require(exact_fraction(constitutional["quorum"], 2, 3, "at_least"), "constitutional quorum must be exactly >= 2/3")
    require(exact_fraction(constitutional["approval"], 3, 4, "at_least"), "constitutional approval must be exactly >= 3/4")
    require(exact_fraction(mission["quorum"], 3, 4, "at_least"), "mission quorum must be exactly >= 3/4")
    require(exact_fraction(mission["approval"], 9, 10, "at_least"), "mission approval must be exactly >= 9/10")
    require(mission["successful_votes_required"] == 2, "Mission Lock must require two successful votes")
    require(mission["minimum_days_between_successful_votes"] >= 60, "Mission Lock votes must be separated by at least 60 days")
    require(mission["founding_period_guardian_consent_required"] is True, "Founding Period Mission Lock must require guardian consent")

    conflicts = rules["conflict_rules"]
    require(conflicts["self_compensation_recusal_required"] is True, "self-compensation recusal must remain required")
    require(conflicts["self_contract_approval_prohibited"] is True, "self-contract approval must remain prohibited")
    require(conflicts["funding_does_not_create_governance_rights"] is True, "funding must not create governance rights")
    require(conflicts["founder_status_does_not_override_conflict_recusal"] is True, "founder status cannot bypass conflict recusal")

    require(membership["one_person_one_vote"] is True, "membership must remain one-person-one-vote")
    require(membership["natural_person_voting_members_only"] is True, "voting membership must remain natural-person based")
    seasoning = membership["voting_seasoning_days"]
    require(seasoning["ordinary-approval"] >= 30, "ordinary voting seasoning weakened below 30 days")
    require(seasoning["qualified-approval"] >= 90, "qualified voting seasoning weakened below 90 days")
    require(seasoning["constitutional-amendment"] >= 90, "constitutional voting seasoning weakened below 90 days")
    require(seasoning["mission-locked-amendment"] >= 180, "mission voting seasoning weakened below 180 days")

    require(founding["founding_steward"]["display_name"] == "Daniel Molinero Lucas", "unexpected draft Founding Steward identity")
    require(founding["mission_lock"]["negative_veto_only"] is True, "founder Mission Veto must remain negative-only")
    require(founding["mission_lock"]["founder_economic_privilege"] is False, "founder economic privilege must remain false")
    require(founding["phase_transition"]["self_declared_by_founder_prohibited"] is True, "founder cannot self-declare maturity transition")

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
    founding_doc = (ROOT / "FOUNDING-STEWARDSHIP.md").read_text(encoding="utf-8")
    membership_doc = (ROOT / "MEMBERSHIP.md").read_text(encoding="utf-8")
    machine_spec = (ROOT / "spec/MACHINE-READABLE-GOVERNANCE.md").read_text(encoding="utf-8")
    entity_cla = (ROOT / "cla/ENTITY-CLA-1.0-DRAFT.md").read_text(encoding="utf-8")

    require(ONTOLOGY_IRI in ontology, "ontology document IRI missing")
    for term in (
        "OrdinaryApproval",
        "QualifiedApproval",
        "ConstitutionalAmendment",
        "MissionLockedAmendment",
        "Delegation",
        "PersistentIdentifierAuthority",
        "FoundingSteward",
        "MissionGuardian",
        "MembershipRecord",
    ):
        require(f"ec:{term}" in ontology, f"ontology term missing: {term}")
    require("owl:propertyChainAxiom" not in ontology, "property-chain authority inference is forbidden")
    require("ec:GovernanceDecisionShape" in shapes, "governance decision SHACL shape missing")
    require("ec:MembershipRecordShape" in shapes, "membership SHACL shape missing")
    require("non-operative" in constitution.lower(), "constitution must state non-operative status")
    require("mission lock" in constitution.lower(), "constitution must define Mission Lock")
    require("strong stewardship without ownership" in founding_doc.lower(), "founding stewardship principle missing")
    require("one person = one member = one vote" in membership_doc.lower(), "membership equality rule missing")
    require("conforming graph is not proof" in machine_spec.lower(), "machine/legal authority boundary missing")
    require("accepted contribution" in entity_cla.lower(), "Entity CLA must gate full grant on accepted contributions")
    require("limited pre-acceptance review rights" in entity_cla.lower(), "Entity CLA pre-acceptance boundary missing")

    validate_cla_status()

    print("Exergism Commons governance integrity: PASS")
    print(f"governance_version={version} operative={status['operative']} state={status['institutional_state']} phase={status['institutional_phase']}")
    print(f"decision_rules={len(rules['rules'])} delegations={len(delegations['delegations'])} members={len(membership['members'])}")


if __name__ == "__main__":
    main()
