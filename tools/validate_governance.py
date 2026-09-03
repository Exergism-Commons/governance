#!/usr/bin/env python3
"""Deterministic integrity checks for EC organization governance drafts.

The validator checks committed consistency and fail-closed activation gates.
It does not determine legal validity or substitute for qualified review.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NS = "https://id.exergism.org/commons#"
ONTOLOGY_IRI = "https://id.exergism.org/ontology/commons"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"governance integrity failure: {message}")


def load_json(path: str) -> dict:
    with (ROOT / path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def yaml_scalar(text: str, key: str):
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.*?)\s*$", text)
    require(match is not None, f"CLA status missing key: {key}")
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
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if stripped == f"{key}:":
            children: list[str] = []
            for child in lines[index + 1 :]:
                if not child.strip():
                    children.append("")
                    continue
                child_indent = len(child) - len(child.lstrip())
                if child_indent <= indent:
                    break
                cut = min(len(child), indent + 2)
                children.append(child[cut:])
            return "\n".join(children)
        if stripped.startswith(f"{key}:"):
            return stripped.split(":", 1)[1].strip()
    raise SystemExit(f"governance integrity failure: YAML block missing: {key}")


def yaml_list(text: str, key: str) -> list[str]:
    block = yaml_block(text, key)
    if block in ("", "[]"):
        return []
    if block.startswith("[") and block.endswith("]"):
        inner = block[1:-1].strip()
        return [] if not inner else [item.strip() for item in inner.split(",")]
    values: list[str] = []
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


def yaml_has_value_or_mapping(text: str, key: str) -> bool:
    scalar = yaml_scalar(text, key)
    if scalar not in (None, ""):
        return True
    try:
        block = yaml_block(text, key)
    except SystemExit:
        return False
    return bool(block.strip())


def exact_fraction(spec: dict, numerator: int, denominator: int, comparison: str) -> bool:
    return (
        spec.get("numerator") == numerator
        and spec.get("denominator") == denominator
        and spec.get("comparison") == comparison
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_sha256(value, label: str) -> str:
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None, f"{label} must be lowercase SHA-256")
    return value


def parse_iso_date(value, label: str) -> date:
    require(isinstance(value, str) and value, f"{label} is required")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"governance integrity failure: {label} must be YYYY-MM-DD") from exc


def elapsed_complete_months(start: date, end: date) -> int:
    require(end >= start, "phase effective date cannot precede governance operative date")
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        months -= 1
    return months


def require_nonempty_reference(value, label: str) -> None:
    require(isinstance(value, str) and value.strip() != "", f"{label} evidence reference is required")


def validate_governance_artifacts(status: dict) -> None:
    artifacts = status.get("governance_artifacts")
    require(isinstance(artifacts, dict), "governance artifact registry missing")
    expected = {
        "constitution": status["constitution"],
        "membership_policy": status["membership_policy"],
        "founding_stewardship_policy": status["founding_stewardship_policy"],
    }
    require(set(artifacts) == set(expected), "unexpected governance artifact set")

    if status["operative"] is False:
        for name, canonical_path in expected.items():
            item = artifacts[name]
            require(item.get("path") == canonical_path, f"draft {name} path mismatch")
            require(item.get("status") == "draft", f"draft {name} must be marked draft")
            require("-DRAFT" in str(item.get("version")), f"draft {name} version must remain marked DRAFT")
            require(item.get("sha256") is None, f"draft {name} must not claim adopted-byte digest")
            require((ROOT / canonical_path).is_file(), f"draft {name} artifact missing")
        return

    require("-DRAFT" not in status["governance_version"], "operative governance_version cannot remain draft")
    for name, canonical_path in expected.items():
        item = artifacts[name]
        require(item.get("path") == canonical_path, f"operative {name} path mismatch")
        require(item.get("status") in {"adopted", "operative"}, f"operative {name} must be adopted")
        version = str(item.get("version"))
        require(version and "-DRAFT" not in version, f"operative {name} version cannot be draft")
        artifact_path = ROOT / canonical_path
        require(artifact_path.is_file(), f"operative {name} artifact missing")
        recorded_hash = require_sha256(item.get("sha256"), f"{name}.sha256")
        require(sha256_file(artifact_path) == recorded_hash, f"{name} bytes do not match recorded SHA-256")
        head = artifact_path.read_text(encoding="utf-8")[:1200]
        require("DRAFT" not in head.upper(), f"operative {name} artifact still declares DRAFT")
        require("NON-OPERATIVE" not in head.upper(), f"operative {name} artifact still declares non-operative status")
        require(version in head, f"operative {name} artifact does not identify recorded version")


def validate_cla_artifact(status_text: str, version_key: str, artifact_key: str, hash_key: str, expected_identity_prefix: str) -> None:
    version = str(yaml_scalar(status_text, version_key))
    artifact = yaml_scalar(status_text, artifact_key)
    recorded_hash = yaml_scalar(status_text, hash_key)
    require(isinstance(artifact, str) and artifact, f"operative CLA missing {artifact_key}")
    require("DRAFT" not in artifact.upper(), f"operative {artifact_key} cannot point to draft artifact")
    path = ROOT / artifact
    require(path.is_file(), f"operative CLA artifact missing: {artifact}")
    recorded_hash = require_sha256(recorded_hash, hash_key)
    require(sha256_file(path) == recorded_hash, f"{artifact_key} bytes do not match recorded SHA-256")
    head = path.read_text(encoding="utf-8")[:1400]
    require("DRAFT" not in head.upper(), f"operative CLA artifact still declares DRAFT: {artifact}")
    require("NOT OPERATIVE" not in head.upper(), f"operative CLA artifact still declares NOT OPERATIVE: {artifact}")
    human_version = version.replace(expected_identity_prefix + "-", expected_identity_prefix + " ", 1)
    require(human_version in head, f"operative CLA artifact does not identify {version}")


def validate_project_schedule_artifact(status_text: str) -> None:
    version = str(yaml_scalar(status_text, "project_schedule_version"))
    artifact = yaml_scalar(status_text, "project_schedule_artifact")
    recorded_hash = yaml_scalar(status_text, "project_schedule_sha256")
    require(isinstance(artifact, str) and artifact, "operative CLA missing project_schedule_artifact")
    path = ROOT / artifact
    require(path.is_file(), f"operative Project Schedule artifact missing: {artifact}")
    recorded_hash = require_sha256(recorded_hash, "project_schedule_sha256")
    require(sha256_file(path) == recorded_hash, "Project Schedule bytes do not match recorded SHA-256")
    head = path.read_text(encoding="utf-8")[:1400]
    require("DRAFT" not in head.upper(), "operative Project Schedule still declares DRAFT")
    require("NON-OPERATIVE" not in head.upper(), "operative Project Schedule still declares non-operative status")
    require(version in head, "operative Project Schedule does not identify recorded version")


def validate_cla_status() -> None:
    status_text = (ROOT / "policy/cla-status.yaml").read_text(encoding="utf-8")
    projects_text = (ROOT / "policy/covered-projects.yaml").read_text(encoding="utf-8")
    require(yaml_scalar(status_text, "schema_version") == "2", "unsupported CLA status schema")
    operative = yaml_scalar(status_text, "operative")
    blockers = yaml_list(status_text, "activation_blockers")

    for key in ("individual_artifact", "entity_artifact", "project_schedule_artifact"):
        artifact = yaml_scalar(status_text, key)
        require(isinstance(artifact, str) and (ROOT / artifact).is_file(), f"CLA status references missing {key}")

    if operative is False:
        require(yaml_scalar(status_text, "status") == "draft", "non-operative CLA must remain draft")
        require(yaml_scalar(status_text, "legal_steward") is None, "draft CLA must not fabricate legal steward")
        require(yaml_scalar(status_text, "governing_law") is None, "draft CLA must not fabricate governing law")
        require(yaml_scalar(status_text, "effective_date") is None, "draft CLA must not fabricate effective date")
        require(len(blockers) > 0, "draft CLA must expose unresolved activation blockers")
        require("-DRAFT" in str(yaml_scalar(status_text, "individual_version")), "draft individual CLA version should remain marked DRAFT")
        require("-DRAFT" in str(yaml_scalar(status_text, "entity_version")), "draft entity CLA version should remain marked DRAFT")
        require("-DRAFT" in str(yaml_scalar(status_text, "project_schedule_version")), "draft Project Schedule version should remain marked DRAFT")
        require(yaml_scalar(status_text, "individual_sha256") is None, "draft individual CLA must not claim adopted-byte digest")
        require(yaml_scalar(status_text, "entity_sha256") is None, "draft entity CLA must not claim adopted-byte digest")
        require(yaml_scalar(status_text, "project_schedule_sha256") is None, "draft Project Schedule must not claim adopted-byte digest")
        return

    require(operative is True, "CLA operative field must be boolean")
    require(yaml_scalar(status_text, "status") in {"adopted", "operative"}, "operative CLA must have adopted/operative status")
    require(yaml_has_value_or_mapping(status_text, "legal_steward"), "operative CLA requires competent legal steward data")
    require(bool(yaml_scalar(status_text, "governing_law")), "operative CLA requires governing law")
    require(bool(yaml_scalar(status_text, "effective_date")), "operative CLA requires effective date")
    require(bool(yaml_scalar(status_text, "privacy_records_policy")), "operative CLA requires privacy/records policy")
    require(len(yaml_list(status_text, "acceptance_methods")) > 0, "operative CLA requires at least one acceptance method")
    require(yaml_nested_bool(status_text, "legal_review", "complete") is True, "operative CLA requires completed legal review")
    legal_review_block = yaml_block(status_text, "legal_review")
    require(len(yaml_list(legal_review_block, "records")) > 0, "operative CLA requires immutable legal-review record(s)")
    require(blockers == [], "operative CLA cannot retain activation blockers")
    require("-DRAFT" not in str(yaml_scalar(status_text, "individual_version")), "operative individual CLA version cannot be draft")
    require("-DRAFT" not in str(yaml_scalar(status_text, "entity_version")), "operative entity CLA version cannot be draft")
    require("-DRAFT" not in str(yaml_scalar(status_text, "project_schedule_version")), "operative Project Schedule cannot be draft")
    require("status: draft" not in projects_text, "operative CLA cannot use draft covered-project projection")
    require("operative: false" not in projects_text, "operative CLA requires operative covered-project projection")
    require("current_outbound: unresolved" not in projects_text, "operative CLA cannot cover unresolved outbound material")
    require("cla_outbound_family: unresolved" not in projects_text, "operative CLA cannot use unresolved outbound family")

    validate_cla_artifact(status_text, "individual_version", "individual_artifact", "individual_sha256", "EC-ICLA")
    validate_cla_artifact(status_text, "entity_version", "entity_artifact", "entity_sha256", "EC-ECLA")
    validate_project_schedule_artifact(status_text)


def active_member_count(membership: dict) -> int:
    return sum(1 for item in membership["members"] if item.get("operative_membership") is True and item.get("state") == "active")


def validate_phase_evidence(status: dict, membership: dict, founding: dict, phase_evidence: dict) -> None:
    require(phase_evidence["schema_version"] == 1, "unsupported phase-evidence schema")
    require(phase_evidence["governance_version"] == status["governance_version"], "phase-evidence governance version mismatch")
    require(phase_evidence["current_phase"] == status["institutional_phase"], "phase-evidence/current phase mismatch")

    if status["operative"] is False:
        require(phase_evidence["operative"] is False, "draft phase evidence cannot be operative")
        require(phase_evidence["current_phase"] == "F0-founder-led-bootstrap", "draft phase evidence must remain F0")
        require(phase_evidence["governance_operative_since"] is None, "draft phase evidence cannot fabricate operative date")
        require(phase_evidence["phase_effective_date"] is None, "draft phase evidence cannot fabricate phase date")
        require(phase_evidence["transition_decision_record"] is None, "draft phase evidence cannot fabricate transition record")
        require(phase_evidence["f1"]["independent_role_holder_present"] is False, "draft F1 independent-capacity evidence must be false")
        require(phase_evidence["f1"]["documented_treasury_domain_repository_delegations"] is False, "draft F1 delegation evidence must be false")
        require(phase_evidence["f2"]["single_person_cross_domain_control_removed"] is False, "draft F2 control-separation evidence must be false")
        require(phase_evidence["f2"]["independent_audit_review_capacity"] is False, "draft F2 audit evidence must be false")
        require(phase_evidence["f2"]["delegated_role_replacement_demonstrated"] is False, "draft F2 replacement evidence must be false")
        return

    require(phase_evidence["operative"] is True, "operative governance requires operative phase evidence")
    operative_since = parse_iso_date(phase_evidence["governance_operative_since"], "governance_operative_since")
    phase_date = parse_iso_date(phase_evidence["phase_effective_date"], "phase_effective_date")
    require(phase_date >= operative_since, "phase effective date cannot precede governance operative date")

    phase = status["institutional_phase"]
    members = active_member_count(membership)
    f1 = phase_evidence["f1"]
    f2 = phase_evidence["f2"]

    require(f1["minimum_active_members"] == founding["phase_transition"]["f1_min_active_members"], "F1 member threshold mismatch")
    require(f2["minimum_active_members"] == founding["phase_transition"]["f2_min_active_members"], "F2 member threshold mismatch")
    require(f2["minimum_operational_months"] == founding["phase_transition"]["f2_min_operational_months"], "F2 time threshold mismatch")

    if phase == "F0-founder-led-bootstrap":
        return

    require_nonempty_reference(phase_evidence["transition_decision_record"], "phase transition decision")
    require(members >= f1["minimum_active_members"], "F1/F2 requires minimum Active Members from operative registry")
    require(f1["independent_role_holder_present"] is True, "F1/F2 requires independent institutional role holder")
    require_nonempty_reference(f1["independent_role_holder_evidence"], "F1 independent role holder")
    require(f1["documented_treasury_domain_repository_delegations"] is True, "F1/F2 requires documented treasury/domain/repository delegations")
    require_nonempty_reference(f1["delegation_evidence"], "F1 delegations")

    if phase == "F1-early-institution":
        return

    require(phase == "F2-distributed-institution", "unsupported operative phase")
    require(members >= f2["minimum_active_members"], "F2 requires at least seven Active Members")
    require(elapsed_complete_months(operative_since, phase_date) >= f2["minimum_operational_months"], "F2 requires at least 12 complete months of operative governance")
    require(f2["single_person_cross_domain_control_removed"] is True, "F2 requires removal of single-person Treasury/domain/all-repositories control")
    require_nonempty_reference(f2["control_separation_evidence"], "F2 control separation")
    require(f2["independent_audit_review_capacity"] is True, "F2 requires independent audit/review capacity")
    require_nonempty_reference(f2["audit_review_evidence"], "F2 audit/review")
    require(f2["delegated_role_replacement_demonstrated"] is True, "F2 requires demonstrated delegated-role replacement")
    require_nonempty_reference(f2["role_replacement_evidence"], "F2 role replacement")


def validate_bootstrap_or_operativity(status: dict, rules: dict, delegations: dict, membership: dict, founding: dict, phase_evidence: dict) -> None:
    phase = status["institutional_phase"]
    validate_governance_artifacts(status)

    if status["operative"] is False:
        require(status["institutional_state"] == "bootstrap", "non-operative governance must remain bootstrap")
        require(phase == "F0-founder-led-bootstrap", "non-operative bootstrap must remain F0")
        require(status["legal_entity"] is None, "bootstrap must not fabricate legal entity")
        require(status["governing_law"] is None, "bootstrap must not fabricate governing law")
        require(status["effective_date"] is None, "bootstrap must not fabricate effective date")
        require(status["adoption_record"] is None, "bootstrap must not fabricate adoption record")
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
        require(delegations["operative"] is False, "draft delegation registry cannot be operative")
        require(delegations["delegations"] == [], "bootstrap cannot contain operative-looking delegations")
        require(membership["operative"] is False, "draft membership registry cannot be operative")
        require(membership["registry_state"] == "bootstrap", "draft membership registry must remain bootstrap")
        require(all(item.get("operative_membership") is False for item in membership["members"]), "bootstrap cannot contain operative Members")
        require(founding["operative"] is False, "draft founding stewardship cannot be operative")
        require(founding["founding_steward"]["operative_assignment"] is False, "bootstrap cannot fabricate operative Founding Steward assignment")
        require(founding["mission_guardian"]["operative_assignment"] is False, "bootstrap cannot fabricate operative Mission Guardian assignment")
        require(founding["mission_lock"]["operative"] is False, "draft Mission Lock cannot be operative")
        validate_phase_evidence(status, membership, founding, phase_evidence)
        return

    require(status["operative"] is True, "governance operative field must be boolean")
    require(status["institutional_state"] != "bootstrap", "operative governance cannot remain bootstrap")
    require("-DRAFT" not in status["governance_version"], "operative governance_version cannot remain draft")
    require(phase in {"F0-founder-led-bootstrap", "F1-early-institution", "F2-distributed-institution"}, "invalid operative institutional phase")
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
    require(membership["operative"] is True, "operative governance requires operative Member Registry")
    require(membership["registry_state"] == "operative", "operative Member Registry must say operative")
    require(active_member_count(membership) >= 1, "operative governance requires at least one Active Member")
    require(founding["operative"] is True, "operative governance requires operative founding/mission-protection record")
    require(founding["mission_lock"]["operative"] is True, "operative governance requires operative Mission Lock")

    founder_active = founding["founding_steward"]["operative_assignment"] is True
    guardian_active = founding["mission_guardian"]["operative_assignment"] is True
    if phase in {"F0-founder-led-bootstrap", "F1-early-institution"}:
        require(founder_active or guardian_active, "operative Founding Period requires Founding Steward or successor Mission Guardian")
    else:
        require(guardian_active, "operative F2 requires adopted Mission Guardian succession for mission protection")

    validate_phase_evidence(status, membership, founding, phase_evidence)


def main() -> None:
    status = load_json("policy/governance-status.json")
    rules = load_json("policy/decision-rules.json")
    delegations = load_json("policy/delegations.json")
    membership = load_json("policy/membership-status.json")
    founding = load_json("policy/founding-stewardship.json")
    phase_evidence = load_json("policy/phase-evidence.json")
    context = load_json("ontology/commons-context.jsonld")

    require(status["schema_version"] == 3, "unsupported governance status schema")
    require(rules["schema_version"] == 3, "unsupported decision rules schema")
    require(membership["schema_version"] == 1, "unsupported membership schema")
    require(founding["schema_version"] == 2, "unsupported founding stewardship schema")
    require(status["vocabulary_namespace"] == NS, "unexpected commons namespace")
    require(status["ontology_iri"] == ONTOLOGY_IRI, "unexpected commons ontology IRI")
    require(status["phase_evidence"] == "policy/phase-evidence.json", "unexpected phase-evidence path")

    version = status["governance_version"]
    for name, obj in {
        "rules": rules,
        "delegations": delegations,
        "membership": membership,
        "founding stewardship": founding,
        "phase evidence": phase_evidence,
    }.items():
        require(obj["governance_version"] == version, f"status/{name} version mismatch")

    validate_bootstrap_or_operativity(status, rules, delegations, membership, founding, phase_evidence)

    by_id = {rule["id"]: rule for rule in rules["rules"]}
    require(set(by_id) == {"ordinary-approval", "qualified-approval", "constitutional-amendment", "mission-locked-amendment"}, "unexpected decision-rule set")

    ordinary = by_id["ordinary-approval"]
    qualified = by_id["qualified-approval"]
    constitutional = by_id["constitutional-amendment"]
    mission = by_id["mission-locked-amendment"]

    require(ordinary["iri"] == NS + "OrdinaryApproval", "OrdinaryApproval IRI mismatch")
    require(qualified["iri"] == NS + "QualifiedApproval", "QualifiedApproval IRI mismatch")
    require(constitutional["iri"] == NS + "ConstitutionalAmendment", "ConstitutionalAmendment IRI mismatch")
    require(mission["iri"] == NS + "MissionLockedAmendment", "MissionLockedAmendment IRI mismatch")

    require(exact_fraction(ordinary["quorum"], 1, 2, "strictly_greater_than"), "ordinary quorum must be exactly > 1/2")
    require(ordinary["approval"]["comparison"] == "strictly_greater_than", "ordinary approval comparison changed")
    require(exact_fraction(qualified["quorum"], 2, 3, "at_least"), "qualified quorum must be exactly >= 2/3")
    require(exact_fraction(qualified["approval"], 2, 3, "at_least"), "qualified approval must be exactly >= 2/3")
    require(exact_fraction(constitutional["quorum"], 2, 3, "at_least"), "constitutional quorum must be exactly >= 2/3")
    require(exact_fraction(constitutional["approval"], 3, 4, "at_least"), "constitutional approval must be exactly >= 3/4")
    require(exact_fraction(mission["quorum"], 3, 4, "at_least"), "Mission Lock quorum must be exactly >= 3/4")
    require(exact_fraction(mission["approval"], 9, 10, "at_least"), "Mission Lock approval must be exactly >= 9/10")

    for rule_id, rule in by_id.items():
        require(rule["zero_valid_for_against_result"] == "fail", f"{rule_id} must fail on zero valid for/against denominator")
        require(rule["minimum_affirmative_votes"] >= 1, f"{rule_id} requires at least one affirmative vote")

    classification = mission["classification"]
    require(classification["trigger"] == "any_operative_effect_alters_weakens_removes_excepts_or_bypasses_mission_lock_invariant", "Mission Lock classification must trigger on any protected operative effect")
    require(classification["bundled_or_secondary_effects_included"] is True, "bundled/secondary Mission Lock effects must remain protected")
    require(classification["proposal_label_cannot_downgrade"] is True, "proposal label cannot downgrade Mission Lock class")
    require(mission["successful_votes_required"] == 2, "Mission Lock requires two successful votes")
    require(mission["minimum_days_between_successful_votes"] >= 60, "Mission Lock votes must be separated by at least 60 days")
    require(mission["guardian_consent_required_in_phases"] == ["F0-founder-led-bootstrap", "F1-early-institution"], "Founding Period guardian-consent phases changed")
    require(mission["founding_period_ends_on_valid_transition_to_phase"] == "F2-distributed-institution", "Founding Period must end only on valid F2 transition")
    require(mission["independent_review_required"] is True, "Mission-Locked Amendment requires independent review")

    founding_period = founding["founding_period"]
    require(founding_period["applies_in_phases"] == ["F0-founder-led-bootstrap", "F1-early-institution"], "Founding Period phases mismatch")
    require(founding_period["ends_only_on_valid_transition_to_phase"] == "F2-distributed-institution", "Founding Period end boundary mismatch")
    require(founding_period["valid_transition_requires_phase_evidence"] is True, "Founding Period end must require phase evidence")
    require(founding_period["founder_vacancy_does_not_end_period"] is True, "founder vacancy cannot silently end Founding Period")

    conflicts = rules["conflict_rules"]
    require(conflicts["self_compensation_recusal_required"] is True, "self-compensation recusal must remain required")
    require(conflicts["self_contract_approval_prohibited"] is True, "self-contract approval must remain prohibited")
    require(conflicts["funding_does_not_create_governance_rights"] is True, "funding must not create governance rights")
    require(conflicts["founder_status_does_not_override_conflict_recusal"] is True, "founder status cannot bypass conflict recusal")

    require(membership["one_person_one_vote"] is True, "Membership must remain one-person-one-vote")
    require(membership["natural_person_voting_members_only"] is True, "voting Members must remain natural persons")
    require(membership["candidate_period_days"] >= 30, "Candidate period weakened below 30 days")
    seasoning = membership["voting_seasoning_days"]
    require(seasoning["ordinary-approval"] >= 30, "ordinary voting seasoning weakened below 30 days")
    require(seasoning["qualified-approval"] >= 90, "qualified voting seasoning weakened below 90 days")
    require(seasoning["constitutional-amendment"] >= 90, "constitutional voting seasoning weakened below 90 days")
    require(seasoning["mission-locked-amendment"] >= 180, "mission voting seasoning weakened below 180 days")

    require(founding["phase"] == status["institutional_phase"], "founding/status phase mismatch")
    require(founding["founding_steward"]["display_name"] == "Daniel Molinero Lucas", "unexpected draft Founding Steward identity")
    require(founding["mission_lock"]["negative_veto_only"] is True, "Founder Mission Veto must remain negative-only")
    require(founding["mission_lock"]["founder_economic_privilege"] is False, "Founder economic privilege must remain false")
    require(founding["phase_transition"]["self_declared_by_founder_prohibited"] is True, "founder cannot self-declare maturity transition")
    require(founding["phase_transition"]["requires_decision_record"] is True, "phase transition must require decision record")
    require(founding["phase_transition"]["requires_evidence_record"] is True, "phase transition must require evidence record")
    require(founding["phase_transition"]["evidence_policy"] == "policy/phase-evidence.json", "phase evidence policy mismatch")

    mandatory_qualified = set(rules["mandatory_qualified_subjects"])
    for subject in {
        "endowment-principal-withdrawal",
        "persistent-domain-transfer",
        "identifier-authority-transfer",
        "organization-wide-exclusive-ip-transfer",
        "institutional-merger-dissolution-or-succession",
    }:
        require(subject in mandatory_qualified, f"qualified-approval subject missing: {subject}")

    require(len(rules["mission_locked_subjects"]) >= 7, "Mission Lock subject set unexpectedly incomplete")
    require(context["@context"]["ec"] == NS, "JSON-LD namespace mismatch")

    ontology = (ROOT / "ontology/commons.ttl").read_text(encoding="utf-8")
    shapes = (ROOT / "ontology/governance-shapes.ttl").read_text(encoding="utf-8")
    constitution = (ROOT / "CONSTITUTION.md").read_text(encoding="utf-8")
    founding_doc = (ROOT / "FOUNDING-STEWARDSHIP.md").read_text(encoding="utf-8")
    membership_doc = (ROOT / "MEMBERSHIP.md").read_text(encoding="utf-8")
    machine_spec = (ROOT / "spec/MACHINE-READABLE-GOVERNANCE.md").read_text(encoding="utf-8")
    individual_cla = (ROOT / "cla/CLA-1.0-DRAFT.md").read_text(encoding="utf-8")
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
    require("ec:GovernanceDecisionShape" in shapes, "GovernanceDecision SHACL shape missing")
    require("ec:MembershipRecordShape" in shapes, "MembershipRecord SHACL shape missing")
    require("non-operative" in constitution.lower(), "Constitution must state non-operative status")
    require("any operative effect" in constitution.lower(), "Constitution must classify Mission Lock by any operative effect")
    require("founding period" in constitution.lower(), "Constitution must define Founding Period")
    require("strong stewardship without ownership" in founding_doc.lower(), "founding-stewardship principle missing")
    require("ends only upon a valid" in founding_doc.lower(), "Founding Period end condition missing")
    require("one person = one member = one vote" in membership_doc.lower(), "Membership equality rule missing")
    require("conforming graph is not proof" in machine_spec.lower(), "machine/legal authority boundary missing")
    require("accepted contribution" in individual_cla.lower(), "Individual CLA acceptance gate missing")
    require("accepted contribution" in entity_cla.lower(), "Entity CLA acceptance gate missing")
    require("limited pre-acceptance review rights" in entity_cla.lower(), "Entity CLA pre-acceptance boundary missing")

    validate_cla_status()

    print("Exergism Commons governance integrity: PASS")
    print(f"governance_version={version} operative={status['operative']} state={status['institutional_state']} phase={status['institutional_phase']}")
    print(f"decision_rules={len(rules['rules'])} delegations={len(delegations['delegations'])} member_records={len(membership['members'])}")


if __name__ == "__main__":
    main()
