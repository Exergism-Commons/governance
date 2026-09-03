#!/usr/bin/env python3
"""Deterministic integrity checks for Exergism Commons governance.

The validator rejects inconsistent machine projections and unsupported activation.
It does not determine legal validity or substitute for qualified human review.
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
CRITICAL_DELEGATION_SCOPES = {"treasury", "domain", "repository"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"governance integrity failure: {message}")


def load_json(path: str) -> dict:
    with (ROOT / path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    require(isinstance(value, dict), f"JSON object required: {path}")
    return value


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
                children.append(child[min(len(child), indent + 2) :])
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
        return bool(yaml_block(text, key).strip())
    except SystemExit:
        return False


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_sha256(value, label: str) -> str:
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None, f"{label} must be lowercase SHA-256")
    return value


def repo_file(value, label: str, prefix: str | None = None) -> Path:
    require(isinstance(value, str) and value.strip(), f"{label} path is required")
    relative = Path(value)
    require(not relative.is_absolute() and ".." not in relative.parts, f"{label} must be a repository-relative path")
    if prefix is not None:
        require(value.startswith(prefix.rstrip("/") + "/"), f"{label} must live under {prefix}/")
    resolved = (ROOT / relative).resolve()
    require(resolved.is_relative_to(ROOT.resolve()), f"{label} escapes repository root")
    require(resolved.is_file(), f"{label} artifact missing: {value}")
    return resolved


def parse_iso_date(value, label: str) -> date:
    require(isinstance(value, str) and value, f"{label} is required")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"governance integrity failure: {label} must be YYYY-MM-DD") from exc


def elapsed_complete_months(start: date, end: date) -> int:
    require(end >= start, "phase effective date cannot precede governance effective date")
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if end.day < start.day:
        months -= 1
    return months


def exact_fraction(spec: dict, numerator: int, denominator: int, comparison: str) -> bool:
    return spec.get("numerator") == numerator and spec.get("denominator") == denominator and spec.get("comparison") == comparison


def validate_content_ref(ref, label: str, prefix: str = "records") -> tuple[dict, Path]:
    require(isinstance(ref, dict), f"{label} must be a content-addressed reference object")
    require(set(ref) == {"path", "sha256"}, f"{label} reference must contain exactly path and sha256")
    path = repo_file(ref["path"], label, prefix)
    recorded = require_sha256(ref["sha256"], f"{label}.sha256")
    require(sha256_file(path) == recorded, f"{label} bytes do not match recorded SHA-256")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"governance integrity failure: {label} must reference UTF-8 JSON") from exc
    require(isinstance(data, dict), f"{label} JSON must be an object")
    return data, path


def validate_evidence_ref(ref, label: str, expected_type: str, governance_version: str) -> dict:
    data, _ = validate_content_ref(ref, label, "records/evidence")
    require(data.get("record_type") == expected_type, f"{label} record_type mismatch")
    require(data.get("status") == "final", f"{label} must be final")
    require(data.get("governance_version") == governance_version, f"{label} governance version mismatch")
    require(isinstance(data.get("evidence_id"), str) and data["evidence_id"].strip(), f"{label} evidence_id required")
    return data


def contradictory_status_declaration(text: str) -> bool:
    patterns = (
        r"(?im)^\s*>?\s*\*{0,2}\s*Status\s*:\s*[^\n]*(?:DRAFT|NON[- ]OPERATIVE)",
        r"(?im)^\s*>\s*\*\*\s*NOT\s+OPERATIVE\b",
        r"(?im)^\s*\*\*(?:EC-ICLA|EC-ECLA)\s+[^\n]*-DRAFT\*\*",
    )
    return any(re.search(pattern, text) is not None for pattern in patterns)


def require_version_header(text: str, version: str, label: str) -> None:
    nonempty = [line for line in text.splitlines() if line.strip()]
    header = "\n".join(nonempty[:40])
    require(version in header, f"{label} does not identify recorded version in authoritative header")


def validate_governance_artifacts(status: dict) -> None:
    artifacts = status.get("governance_artifacts")
    require(isinstance(artifacts, dict), "governance artifact registry missing")
    expected = {
        "constitution": status["constitution"],
        "membership_policy": status["membership_policy"],
        "founding_stewardship_policy": status["founding_stewardship_policy"],
    }
    require(set(artifacts) == set(expected), "unexpected governance artifact set")
    for name, canonical_path in expected.items():
        item = artifacts[name]
        require(item.get("path") == canonical_path, f"{name} path mismatch")
        path = repo_file(canonical_path, name)
        if status["operative"] is False:
            require(item.get("status") == "draft", f"draft {name} must be marked draft")
            require("-DRAFT" in str(item.get("version")), f"draft {name} version must be marked DRAFT")
            require(item.get("sha256") is None, f"draft {name} must not claim adopted-byte digest")
            continue
        require(item.get("status") in {"adopted", "operative"}, f"operative {name} must be adopted")
        version = str(item.get("version"))
        require(version and "-DRAFT" not in version, f"operative {name} version cannot be draft")
        require(sha256_file(path) == require_sha256(item.get("sha256"), f"{name}.sha256"), f"{name} bytes do not match recorded SHA-256")
        text = path.read_text(encoding="utf-8")
        require(not contradictory_status_declaration(text), f"operative {name} contains contradictory draft/non-operative declaration")
        require_version_header(text, version, name)


def validate_activation_evidence(status: dict) -> dict[str, str]:
    evidence = status.get("activation_evidence")
    require(isinstance(evidence, dict), "activation_evidence registry missing")
    expected = {
        "conflict_process": "conflict-process-evidence",
        "records_privacy_process": "records-privacy-process-evidence",
        "treasury_controls": "treasury-controls-evidence",
        "succession_process": "succession-process-evidence",
        "qualified_legal_review": "qualified-legal-review-evidence",
    }
    require(set(evidence) == set(expected), "unexpected activation_evidence set")
    if status["operative"] is False:
        require(all(value is None for value in evidence.values()), "draft governance cannot claim activation evidence")
        return {}
    hashes: dict[str, str] = {}
    for key, record_type in expected.items():
        validate_evidence_ref(evidence[key], f"activation evidence {key}", record_type, status["governance_version"])
        hashes[key] = evidence[key]["sha256"]
    return hashes


def validate_adoption_record(status: dict, activation_hashes: dict[str, str]) -> None:
    if status["operative"] is False:
        require(status.get("adoption_record") is None, "draft governance cannot claim adoption record")
        return
    record, _ = validate_content_ref(status.get("adoption_record"), "governance adoption record", "records/adoptions")
    require(record.get("record_type") == "governance-adoption", "governance adoption record_type mismatch")
    require(record.get("status") == "adopted", "governance adoption record must be adopted")
    require(record.get("governance_version") == status["governance_version"], "adoption governance version mismatch")
    require(record.get("effective_date") == status["effective_date"], "adoption effective date mismatch")
    require(record.get("legal_entity") == status["legal_entity"], "adoption legal entity mismatch")
    require(record.get("governing_law") == status["governing_law"], "adoption governing law mismatch")
    require(isinstance(record.get("decision_id"), str) and record["decision_id"].strip(), "adoption decision_id required")
    require(isinstance(record.get("adoption_method"), str) and record["adoption_method"].strip(), "adoption_method required")
    adopters = record.get("adopters")
    require(isinstance(adopters, list) and len(adopters) > 0, "adoption requires adopter identities")
    require(all(isinstance(item, str) and item.strip() for item in adopters), "invalid adopter identity")
    require(len(set(adopters)) == len(adopters), "duplicate adopter identity")
    approval = record.get("approval_evidence")
    validate_evidence_ref(approval, "governance adoption approval", "approval-evidence", status["governance_version"])
    bindings = record.get("artifact_bindings")
    require(isinstance(bindings, dict), "adoption artifact_bindings required")
    expected_bindings = {name: item["sha256"] for name, item in status["governance_artifacts"].items()}
    require(bindings == expected_bindings, "adoption record does not bind exact governance artifact hashes")
    machine = record.get("machine_bindings")
    expected_machine_paths = (
        "policy/decision-rules.json",
        "policy/membership-status.json",
        "policy/founding-stewardship.json",
        "policy/delegations.json",
        "policy/phase-evidence.json",
    )
    require(isinstance(machine, dict) and set(machine) == set(expected_machine_paths), "adoption machine_bindings incomplete")
    for path_value in expected_machine_paths:
        path = repo_file(path_value, f"adoption machine binding {path_value}")
        require(machine[path_value] == sha256_file(path), f"adoption machine binding mismatch: {path_value}")
    require(record.get("activation_evidence_hashes") == activation_hashes, "adoption record does not bind activation evidence")


def validate_cla_artifact(status_text: str, version_key: str, artifact_key: str, hash_key: str, identity_prefix: str) -> str:
    version = str(yaml_scalar(status_text, version_key))
    artifact = yaml_scalar(status_text, artifact_key)
    require(isinstance(artifact, str) and artifact, f"operative CLA missing {artifact_key}")
    require("DRAFT" not in artifact.upper(), f"operative {artifact_key} cannot point to draft artifact")
    path = repo_file(artifact, artifact_key)
    recorded = require_sha256(yaml_scalar(status_text, hash_key), hash_key)
    require(sha256_file(path) == recorded, f"{artifact_key} bytes do not match recorded SHA-256")
    text = path.read_text(encoding="utf-8")
    require(not contradictory_status_declaration(text), f"operative {artifact_key} contains contradictory draft/non-operative declaration")
    human_version = version.replace(identity_prefix + "-", identity_prefix + " ", 1)
    require_version_header(text, human_version, artifact_key)
    return recorded


def validate_project_schedule_artifact(status_text: str) -> str:
    version = str(yaml_scalar(status_text, "project_schedule_version"))
    artifact = yaml_scalar(status_text, "project_schedule_artifact")
    path = repo_file(artifact, "project_schedule_artifact")
    recorded = require_sha256(yaml_scalar(status_text, "project_schedule_sha256"), "project_schedule_sha256")
    require(sha256_file(path) == recorded, "Project Schedule bytes do not match recorded SHA-256")
    text = path.read_text(encoding="utf-8")
    require(not contradictory_status_declaration(text), "operative Project Schedule contains contradictory draft/non-operative declaration")
    require_version_header(text, version, "Project Schedule")
    return recorded


def validate_cla_status() -> None:
    status_text = (ROOT / "policy/cla-status.yaml").read_text(encoding="utf-8")
    projects_text = (ROOT / "policy/covered-projects.yaml").read_text(encoding="utf-8")
    require(yaml_scalar(status_text, "schema_version") == "3", "unsupported CLA status schema")
    operative = yaml_scalar(status_text, "operative")
    blockers = yaml_list(status_text, "activation_blockers")
    for key in ("individual_artifact", "entity_artifact", "project_schedule_artifact"):
        repo_file(yaml_scalar(status_text, key), key)
    if operative is False:
        require(yaml_scalar(status_text, "status") == "draft", "non-operative CLA must remain draft")
        require(yaml_scalar(status_text, "legal_steward") is None, "draft CLA must not fabricate legal steward")
        require(yaml_scalar(status_text, "governing_law") is None, "draft CLA must not fabricate governing law")
        require(yaml_scalar(status_text, "effective_date") is None, "draft CLA must not fabricate effective date")
        require(len(blockers) > 0, "draft CLA must expose activation blockers")
        for key in ("individual_version", "entity_version", "project_schedule_version"):
            require("-DRAFT" in str(yaml_scalar(status_text, key)), f"draft {key} must remain DRAFT")
        for key in ("individual_sha256", "entity_sha256", "project_schedule_sha256", "legal_review_manifest_artifact", "legal_review_manifest_sha256", "adoption_record_artifact", "adoption_record_sha256"):
            require(yaml_scalar(status_text, key) is None, f"draft CLA cannot claim {key}")
        return
    require(operative is True, "CLA operative field must be boolean")
    require(yaml_scalar(status_text, "status") in {"adopted", "operative"}, "operative CLA must have adopted/operative status")
    require(yaml_has_value_or_mapping(status_text, "legal_steward"), "operative CLA requires legal steward")
    governing_law = yaml_scalar(status_text, "governing_law")
    effective_date = yaml_scalar(status_text, "effective_date")
    require(bool(governing_law), "operative CLA requires governing law")
    parse_iso_date(effective_date, "CLA effective_date")
    require(bool(yaml_scalar(status_text, "privacy_records_policy")), "operative CLA requires privacy/records policy")
    acceptance_methods = yaml_list(status_text, "acceptance_methods")
    require(len(acceptance_methods) > 0, "operative CLA requires acceptance method")
    require(yaml_nested_bool(status_text, "legal_review", "complete") is True, "operative CLA requires completed legal review")
    require(blockers == [], "operative CLA cannot retain activation blockers")
    for key in ("individual_version", "entity_version", "project_schedule_version"):
        require("-DRAFT" not in str(yaml_scalar(status_text, key)), f"operative {key} cannot be draft")
    require("status: draft" not in projects_text and "operative: false" not in projects_text, "operative CLA requires operative covered-project projection")
    require("current_outbound: unresolved" not in projects_text and "cla_outbound_family: unresolved" not in projects_text, "operative CLA cannot use unresolved outbound terms")
    individual_hash = validate_cla_artifact(status_text, "individual_version", "individual_artifact", "individual_sha256", "EC-ICLA")
    entity_hash = validate_cla_artifact(status_text, "entity_version", "entity_artifact", "entity_sha256", "EC-ECLA")
    schedule_hash = validate_project_schedule_artifact(status_text)
    manifest_path = yaml_scalar(status_text, "legal_review_manifest_artifact")
    manifest_ref = {"path": manifest_path, "sha256": yaml_scalar(status_text, "legal_review_manifest_sha256")}
    manifest, _ = validate_content_ref(manifest_ref, "CLA legal review manifest", "records/reviews")
    require(manifest.get("record_type") == "qualified-legal-review", "CLA legal review record_type mismatch")
    require(manifest.get("status") == "final", "CLA legal review manifest must be final")
    reviewers = manifest.get("reviewer_ids")
    require(isinstance(reviewers, list) and reviewers and len(set(reviewers)) == len(reviewers), "CLA legal review requires distinct reviewer ids")
    require(manifest.get("reviewed_artifact_hashes") == {"individual": individual_hash, "entity": entity_hash, "project_schedule": schedule_hash}, "CLA legal review does not bind exact artifacts")
    adoption_ref = {"path": yaml_scalar(status_text, "adoption_record_artifact"), "sha256": yaml_scalar(status_text, "adoption_record_sha256")}
    adoption, _ = validate_content_ref(adoption_ref, "CLA adoption record", "records/adoptions")
    require(adoption.get("record_type") == "cla-adoption" and adoption.get("status") == "adopted", "CLA adoption record invalid")
    require(adoption.get("effective_date") == effective_date, "CLA adoption effective date mismatch")
    require(adoption.get("governing_law") == governing_law, "CLA adoption governing law mismatch")
    require(adoption.get("versions") == {"individual": yaml_scalar(status_text, "individual_version"), "entity": yaml_scalar(status_text, "entity_version"), "project_schedule": yaml_scalar(status_text, "project_schedule_version")}, "CLA adoption version bindings mismatch")
    require(adoption.get("artifact_hashes") == {"individual": individual_hash, "entity": entity_hash, "project_schedule": schedule_hash}, "CLA adoption artifact bindings mismatch")
    require(adoption.get("legal_review_manifest_sha256") == manifest_ref["sha256"], "CLA adoption does not bind legal-review manifest")
    require(set(adoption.get("acceptance_methods", [])) == set(acceptance_methods), "CLA adoption acceptance methods mismatch")
    require(isinstance(adoption.get("adopters"), list) and adoption["adopters"], "CLA adoption requires adopter identities")


def validate_membership_registry(membership: dict) -> set[str]:
    require(membership["schema_version"] == 2, "unsupported membership schema")
    members = membership.get("members")
    require(isinstance(members, list), "membership members must be a list")
    record_ids: set[str] = set()
    person_ids: set[str] = set()
    active: set[str] = set()
    for item in members:
        record_id = item.get("record_id")
        person_id = item.get("person_id")
        require(isinstance(record_id, str) and record_id, "member record_id required")
        require(isinstance(person_id, str) and person_id, "member person_id required")
        require(record_id not in record_ids, f"duplicate member record_id: {record_id}")
        require(person_id not in person_ids, f"duplicate member person_id: {person_id}")
        record_ids.add(record_id)
        person_ids.add(person_id)
        if item.get("operative_membership") is True and item.get("state") == "active":
            active.add(person_id)
    return active


def validate_delegations(delegations: dict, governance_version: str) -> list[dict]:
    require(delegations["schema_version"] == 2, "unsupported delegations schema")
    require(CRITICAL_DELEGATION_SCOPES.issubset(set(delegations.get("scope_vocabulary", []))), "delegation scope vocabulary missing critical scopes")
    items = delegations.get("delegations")
    require(isinstance(items, list), "delegations must be a list")
    ids: set[str] = set()
    active: list[dict] = []
    for item in items:
        delegation_id = item.get("delegation_id")
        require(isinstance(delegation_id, str) and delegation_id, "delegation_id required")
        require(delegation_id not in ids, f"duplicate delegation_id: {delegation_id}")
        ids.add(delegation_id)
        if item.get("operative") is not True:
            continue
        holder = item.get("holder_person_id")
        scopes = item.get("scope_types")
        require(isinstance(holder, str) and holder, f"operative delegation {delegation_id} requires holder_person_id")
        require(isinstance(scopes, list) and scopes and len(set(scopes)) == len(scopes), f"operative delegation {delegation_id} requires unique scopes")
        require(set(scopes).issubset(set(delegations["scope_vocabulary"])), f"delegation {delegation_id} uses unknown scope")
        decision, _ = validate_content_ref(item.get("decision_record"), f"delegation decision {delegation_id}", "records/decisions")
        require(decision.get("record_type") == "delegation-decision" and decision.get("status") == "adopted", f"delegation decision invalid: {delegation_id}")
        require(decision.get("governance_version") == governance_version, f"delegation decision version mismatch: {delegation_id}")
        require(decision.get("delegation_id") == delegation_id, f"delegation decision id mismatch: {delegation_id}")
        require(decision.get("holder_person_id") == holder, f"delegation decision holder mismatch: {delegation_id}")
        require(set(decision.get("scope_types", [])) == set(scopes), f"delegation decision scope mismatch: {delegation_id}")
        active.append(item)
    return active


def validate_phase_transition_record(ref, status: dict, phase_evidence: dict) -> dict:
    record, _ = validate_content_ref(ref, "phase transition decision", "records/decisions")
    require(record.get("record_type") == "phase-transition" and record.get("status") == "adopted", "phase transition record invalid")
    require(record.get("governance_version") == status["governance_version"], "phase transition governance version mismatch")
    require(record.get("to_phase") == status["institutional_phase"], "phase transition target mismatch")
    require(record.get("effective_date") == phase_evidence["phase_effective_date"], "phase transition effective date mismatch")
    require(isinstance(record.get("decision_id"), str) and record["decision_id"].strip(), "phase transition decision_id required")
    validate_evidence_ref(record.get("approval_evidence"), "phase transition approval", "approval-evidence", status["governance_version"])
    expected_from = {"F1-early-institution": "F0-founder-led-bootstrap", "F2-distributed-institution": "F1-early-institution"}
    require(record.get("from_phase") == expected_from[status["institutional_phase"]], "phase transition source mismatch")
    return record


def validate_phase_evidence(status: dict, membership: dict, founding: dict, phase_evidence: dict, active_delegations: list[dict], active_members: set[str]) -> None:
    require(phase_evidence["schema_version"] == 2, "unsupported phase-evidence schema")
    require(phase_evidence["governance_version"] == status["governance_version"], "phase-evidence governance version mismatch")
    require(phase_evidence["current_phase"] == status["institutional_phase"], "phase-evidence/current phase mismatch")
    contract = phase_evidence.get("evidence_reference_contract")
    require(contract == {"type": "content-addressed-json", "required_fields": ["path", "sha256"]}, "phase evidence reference contract mismatch")
    f1 = phase_evidence["f1"]
    f2 = phase_evidence["f2"]
    if status["operative"] is False:
        require(phase_evidence["operative"] is False and phase_evidence["current_phase"] == "F0-founder-led-bootstrap", "draft phase evidence must remain non-operative F0")
        require(phase_evidence["governance_operative_since"] is None and phase_evidence["phase_effective_date"] is None and phase_evidence["transition_decision_record"] is None, "draft phase evidence cannot fabricate dates/decision")
        for value in (f1["independent_role_holder_evidence"], f1["delegation_evidence"], f2["control_separation_evidence"], f2["audit_review_evidence"], f2["role_replacement_evidence"]):
            require(value is None, "draft phase evidence cannot claim content-addressed evidence")
        require(not f1["independent_role_holder_present"] and not f1["documented_treasury_domain_repository_delegations"], "draft F1 evidence flags must be false")
        require(not f2["single_person_cross_domain_control_removed"] and not f2["independent_audit_review_capacity"] and not f2["delegated_role_replacement_demonstrated"], "draft F2 evidence flags must be false")
        return
    require(phase_evidence["operative"] is True, "operative governance requires operative phase evidence")
    effective = parse_iso_date(status["effective_date"], "governance effective_date")
    operative_since = parse_iso_date(phase_evidence["governance_operative_since"], "governance_operative_since")
    phase_date = parse_iso_date(phase_evidence["phase_effective_date"], "phase_effective_date")
    require(operative_since == effective, "governance_operative_since must equal governance effective_date")
    require(phase_date >= effective, "phase effective date cannot precede governance effective_date")
    require(f1["minimum_active_members"] == founding["phase_transition"]["f1_min_active_members"], "F1 member threshold mismatch")
    require(f2["minimum_active_members"] == founding["phase_transition"]["f2_min_active_members"], "F2 member threshold mismatch")
    require(f2["minimum_operational_months"] == founding["phase_transition"]["f2_min_operational_months"], "F2 time threshold mismatch")
    phase = status["institutional_phase"]
    if phase == "F0-founder-led-bootstrap":
        require(phase_evidence["transition_decision_record"] is None, "F0 initial adoption must not fabricate phase transition")
        require(phase_date == effective, "operative F0 phase date must equal governance effective date")
        return
    validate_phase_transition_record(phase_evidence["transition_decision_record"], status, phase_evidence)
    require(len(active_members) >= f1["minimum_active_members"], "F1/F2 requires minimum distinct Active Members")
    founder_person = founding["founding_steward"]["person_id"]
    by_id = {item["delegation_id"]: item for item in active_delegations}
    require(f1["independent_role_holder_present"] is True, "F1/F2 requires independent role holder")
    independent = validate_evidence_ref(f1["independent_role_holder_evidence"], "F1 independent role holder", "independent-role-evidence", status["governance_version"])
    independent_person = independent.get("person_id")
    independent_delegation = independent.get("delegation_id")
    require(isinstance(independent_person, str) and independent_person != founder_person, "F1 independent role holder must differ from founder")
    require(independent_delegation in by_id and by_id[independent_delegation]["holder_person_id"] == independent_person, "F1 independent role evidence not backed by active delegation")
    require(f1["documented_treasury_domain_repository_delegations"] is True, "F1/F2 requires documented critical delegations")
    delegation_evidence = validate_evidence_ref(f1["delegation_evidence"], "F1 delegations", "delegation-evidence", status["governance_version"])
    evidence_ids = delegation_evidence.get("delegation_ids")
    require(isinstance(evidence_ids, list) and evidence_ids and len(set(evidence_ids)) == len(evidence_ids), "F1 delegation evidence requires unique delegation_ids")
    require(set(evidence_ids).issubset(set(by_id)), "F1 delegation evidence references non-operative delegation")
    covered = set()
    for delegation_id in evidence_ids:
        covered.update(by_id[delegation_id]["scope_types"])
    require(CRITICAL_DELEGATION_SCOPES.issubset(covered), "F1 requires operative treasury/domain/repository delegation scopes")
    if phase == "F1-early-institution":
        return
    require(phase == "F2-distributed-institution", "unsupported operative phase")
    require(len(active_members) >= f2["minimum_active_members"], "F2 requires seven distinct Active Members")
    require(elapsed_complete_months(effective, phase_date) >= f2["minimum_operational_months"], "F2 requires at least 12 complete months from governance effective date")
    critical_holders: dict[str, set[str]] = {scope: set() for scope in CRITICAL_DELEGATION_SCOPES}
    for item in active_delegations:
        for scope in CRITICAL_DELEGATION_SCOPES.intersection(item["scope_types"]):
            critical_holders[scope].add(item["holder_person_id"])
    require(all(critical_holders.values()), "F2 critical delegation scopes cannot be empty")
    require(not set.intersection(*critical_holders.values()), "F2 forbids one person controlling Treasury, domain and repositories simultaneously")
    require(f2["single_person_cross_domain_control_removed"] is True, "F2 control-separation flag required")
    separation = validate_evidence_ref(f2["control_separation_evidence"], "F2 control separation", "control-separation-evidence", status["governance_version"])
    checked = separation.get("checked_delegation_ids")
    critical_ids = {item["delegation_id"] for item in active_delegations if CRITICAL_DELEGATION_SCOPES.intersection(item["scope_types"])}
    require(isinstance(checked, list) and set(checked) == critical_ids, "F2 control-separation evidence must cover all critical active delegations")
    audit_delegations = [item for item in active_delegations if "audit-review" in item["scope_types"] and item["holder_person_id"] != founder_person]
    require(f2["independent_audit_review_capacity"] is True and audit_delegations, "F2 requires independent audit/review delegation")
    audit = validate_evidence_ref(f2["audit_review_evidence"], "F2 audit/review", "audit-review-capacity-evidence", status["governance_version"])
    require(audit.get("delegation_id") in {item["delegation_id"] for item in audit_delegations}, "F2 audit evidence not backed by independent audit delegation")
    require(f2["delegated_role_replacement_demonstrated"] is True, "F2 requires demonstrated role replacement")
    replacement = validate_evidence_ref(f2["role_replacement_evidence"], "F2 role replacement", "role-replacement-evidence", status["governance_version"])
    delegation_id = replacement.get("delegation_id")
    previous_holder = replacement.get("previous_holder_person_id")
    replacement_holder = replacement.get("replacement_holder_person_id")
    require(delegation_id in by_id, "F2 replacement evidence references inactive delegation")
    require(isinstance(previous_holder, str) and isinstance(replacement_holder, str) and previous_holder != replacement_holder, "F2 replacement evidence requires distinct holders")
    require(by_id[delegation_id]["holder_person_id"] == replacement_holder, "F2 replacement holder must match active delegation")
    decision, _ = validate_content_ref(replacement.get("replacement_decision_record"), "F2 replacement decision", "records/decisions")
    require(decision.get("record_type") == "delegation-decision" and decision.get("delegation_id") == delegation_id and decision.get("holder_person_id") == replacement_holder, "F2 replacement decision does not prove current holder")


def validate_bootstrap_or_operativity(status: dict, rules: dict, delegations: dict, membership: dict, founding: dict, phase_evidence: dict) -> None:
    validate_governance_artifacts(status)
    active_members = validate_membership_registry(membership)
    active_delegations = validate_delegations(delegations, status["governance_version"])
    activation_hashes = validate_activation_evidence(status)
    phase = status["institutional_phase"]
    if status["operative"] is False:
        require(status["institutional_state"] == "bootstrap" and phase == "F0-founder-led-bootstrap", "non-operative governance must remain bootstrap F0")
        require(status["legal_entity"] is None and status["governing_law"] is None and status["effective_date"] is None, "bootstrap cannot fabricate legal activation metadata")
        require(status["adoption_record"] is None, "bootstrap cannot fabricate adoption record")
        for flag in ("initial_member_registry_adopted", "conflict_process_adopted", "records_privacy_process_adopted", "treasury_controls_adopted", "founding_steward_assignment_adopted", "succession_process_adopted", "qualified_legal_review_complete"):
            require(status[flag] is False, f"bootstrap adoption flag must be false: {flag}")
        require(rules["operative"] is False and delegations["operative"] is False and membership["operative"] is False and founding["operative"] is False, "draft machine projections cannot be operative")
        require(delegations["delegations"] == [], "bootstrap cannot contain delegations")
        require(membership["registry_state"] == "bootstrap" and not active_members, "bootstrap cannot contain Active Members")
        require(founding["founding_steward"]["operative_assignment"] is False and founding["mission_guardian"]["operative_assignment"] is False and founding["mission_lock"]["operative"] is False, "bootstrap cannot fabricate operative founding authority")
        validate_phase_evidence(status, membership, founding, phase_evidence, active_delegations, active_members)
        validate_adoption_record(status, activation_hashes)
        return
    require(status["operative"] is True, "governance operative field must be boolean")
    require(status["institutional_state"] != "bootstrap", "operative governance cannot remain bootstrap")
    require("-DRAFT" not in status["governance_version"], "operative governance_version cannot remain draft")
    require(phase in {"F0-founder-led-bootstrap", "F1-early-institution", "F2-distributed-institution"}, "invalid operative institutional phase")
    require(bool(status["legal_entity"]) and bool(status["governing_law"]), "operative governance requires legal entity and governing law")
    parse_iso_date(status["effective_date"], "governance effective_date")
    for flag in ("initial_member_registry_adopted", "conflict_process_adopted", "records_privacy_process_adopted", "treasury_controls_adopted", "founding_steward_assignment_adopted", "succession_process_adopted", "qualified_legal_review_complete"):
        require(status[flag] is True, f"operative governance requires adoption flag: {flag}")
    require(rules["operative"] is True and delegations["operative"] is True and membership["operative"] is True and founding["operative"] is True, "operative governance requires aligned operative projections")
    require(membership["registry_state"] == "operative" and active_members, "operative governance requires Active Member registry")
    require(founding["mission_lock"]["operative"] is True, "operative governance requires operative Mission Lock")
    founder_active = founding["founding_steward"]["operative_assignment"] is True
    guardian_active = founding["mission_guardian"]["operative_assignment"] is True
    if phase in {"F0-founder-led-bootstrap", "F1-early-institution"}:
        require(founder_active or guardian_active, "Founding Period requires Founding Steward or successor Mission Guardian")
    else:
        require(guardian_active, "operative F2 requires adopted Mission Guardian")
    validate_phase_evidence(status, membership, founding, phase_evidence, active_delegations, active_members)
    validate_adoption_record(status, activation_hashes)


def main() -> None:
    status = load_json("policy/governance-status.json")
    rules = load_json("policy/decision-rules.json")
    delegations = load_json("policy/delegations.json")
    membership = load_json("policy/membership-status.json")
    founding = load_json("policy/founding-stewardship.json")
    phase_evidence = load_json("policy/phase-evidence.json")
    context = load_json("ontology/commons-context.jsonld")
    require(status["schema_version"] == 4, "unsupported governance status schema")
    require(rules["schema_version"] == 3, "unsupported decision rules schema")
    require(founding["schema_version"] == 3, "unsupported founding stewardship schema")
    require(status["vocabulary_namespace"] == NS and status["ontology_iri"] == ONTOLOGY_IRI, "governance namespace/ontology mismatch")
    require(status["phase_evidence"] == "policy/phase-evidence.json", "unexpected phase-evidence path")
    version = status["governance_version"]
    for name, obj in {"rules": rules, "delegations": delegations, "membership": membership, "founding stewardship": founding, "phase evidence": phase_evidence}.items():
        require(obj["governance_version"] == version, f"status/{name} version mismatch")
    validate_bootstrap_or_operativity(status, rules, delegations, membership, founding, phase_evidence)
    by_id = {rule["id"]: rule for rule in rules["rules"]}
    require(set(by_id) == {"ordinary-approval", "qualified-approval", "constitutional-amendment", "mission-locked-amendment"}, "unexpected decision-rule set")
    ordinary, qualified, constitutional, mission = by_id["ordinary-approval"], by_id["qualified-approval"], by_id["constitutional-amendment"], by_id["mission-locked-amendment"]
    require(ordinary["iri"] == NS + "OrdinaryApproval" and qualified["iri"] == NS + "QualifiedApproval" and constitutional["iri"] == NS + "ConstitutionalAmendment" and mission["iri"] == NS + "MissionLockedAmendment", "decision-rule IRI mismatch")
    require(exact_fraction(ordinary["quorum"], 1, 2, "strictly_greater_than"), "ordinary quorum must be exactly >1/2")
    require(exact_fraction(qualified["quorum"], 2, 3, "at_least") and exact_fraction(qualified["approval"], 2, 3, "at_least"), "Qualified Approval must be exact 2/3")
    require(exact_fraction(constitutional["quorum"], 2, 3, "at_least") and exact_fraction(constitutional["approval"], 3, 4, "at_least"), "Constitutional Amendment thresholds changed")
    require(exact_fraction(mission["quorum"], 3, 4, "at_least") and exact_fraction(mission["approval"], 9, 10, "at_least"), "Mission Lock thresholds changed")
    for rule_id, rule in by_id.items():
        require(rule["zero_valid_for_against_result"] == "fail" and rule["minimum_affirmative_votes"] >= 1, f"{rule_id} must fail closed on zero valid votes")
    classification = mission["classification"]
    require(classification["trigger"] == "any_operative_effect_alters_weakens_removes_excepts_or_bypasses_mission_lock_invariant" and classification["bundled_or_secondary_effects_included"] is True and classification["proposal_label_cannot_downgrade"] is True, "Mission Lock effect-based classification weakened")
    require(mission["successful_votes_required"] == 2 and mission["minimum_days_between_successful_votes"] >= 60, "Mission Lock repeated-vote safeguard weakened")
    require(mission["guardian_consent_required_in_phases"] == ["F0-founder-led-bootstrap", "F1-early-institution"] and mission["founding_period_ends_on_valid_transition_to_phase"] == "F2-distributed-institution", "Founding Period decision rule mismatch")
    founding_period = founding["founding_period"]
    require(founding_period["applies_in_phases"] == ["F0-founder-led-bootstrap", "F1-early-institution"] and founding_period["ends_only_on_valid_transition_to_phase"] == "F2-distributed-institution" and founding_period["valid_transition_requires_phase_evidence"] is True and founding_period["founder_vacancy_does_not_end_period"] is True, "Founding Period boundary weakened")
    conflicts = rules["conflict_rules"]
    require(conflicts["self_compensation_recusal_required"] is True and conflicts["self_contract_approval_prohibited"] is True and conflicts["funding_does_not_create_governance_rights"] is True and conflicts["founder_status_does_not_override_conflict_recusal"] is True, "conflict/anti-capture invariant weakened")
    require(membership["one_person_one_vote"] is True and membership["natural_person_voting_members_only"] is True, "Membership equality rule weakened")
    seasoning = membership["voting_seasoning_days"]
    require(membership["candidate_period_days"] >= 30 and seasoning["ordinary-approval"] >= 30 and seasoning["qualified-approval"] >= 90 and seasoning["constitutional-amendment"] >= 90 and seasoning["mission-locked-amendment"] >= 180, "Membership anti-capture seasoning weakened")
    require(founding["phase"] == status["institutional_phase"], "founding/status phase mismatch")
    require(founding["founding_steward"]["person_id"] == "ec-person-dml-001" and founding["founding_steward"]["display_name"] == "Daniel Molinero Lucas", "unexpected draft Founding Steward identity")
    require(founding["mission_lock"]["negative_veto_only"] is True and founding["mission_lock"]["founder_economic_privilege"] is False, "founder Mission Lock/economic boundary weakened")
    require(founding["phase_transition"]["self_declared_by_founder_prohibited"] is True and founding["phase_transition"]["requires_decision_record"] is True and founding["phase_transition"]["requires_evidence_record"] is True and founding["phase_transition"]["evidence_policy"] == "policy/phase-evidence.json", "phase-transition integrity weakened")
    mandatory_qualified = set(rules["mandatory_qualified_subjects"])
    for subject in {"endowment-principal-withdrawal", "persistent-domain-transfer", "identifier-authority-transfer", "organization-wide-exclusive-ip-transfer", "institutional-merger-dissolution-or-succession"}:
        require(subject in mandatory_qualified, f"qualified-approval subject missing: {subject}")
    require(len(rules["mission_locked_subjects"]) >= 7, "Mission Lock subject set incomplete")
    require(context["@context"]["ec"] == NS, "JSON-LD namespace mismatch")
    ontology = (ROOT / "ontology/commons.ttl").read_text(encoding="utf-8")
    shapes = (ROOT / "ontology/governance-shapes.ttl").read_text(encoding="utf-8")
    constitution = (ROOT / "CONSTITUTION.md").read_text(encoding="utf-8")
    founding_doc = (ROOT / "FOUNDING-STEWARDSHIP.md").read_text(encoding="utf-8")
    membership_doc = (ROOT / "MEMBERSHIP.md").read_text(encoding="utf-8")
    machine_spec = (ROOT / "spec/MACHINE-READABLE-GOVERNANCE.md").read_text(encoding="utf-8")
    individual_cla = (ROOT / "cla/CLA-1.0-DRAFT.md").read_text(encoding="utf-8")
    entity_cla = (ROOT / "cla/ENTITY-CLA-1.0-DRAFT.md").read_text(encoding="utf-8")
    require(ONTOLOGY_IRI in ontology and "owl:propertyChainAxiom" not in ontology, "ontology authority boundary invalid")
    for term in ("OrdinaryApproval", "QualifiedApproval", "ConstitutionalAmendment", "MissionLockedAmendment", "Delegation", "PersistentIdentifierAuthority", "FoundingSteward", "MissionGuardian", "MembershipRecord"):
        require(f"ec:{term}" in ontology, f"ontology term missing: {term}")
    require("ec:GovernanceDecisionShape" in shapes and "ec:MembershipRecordShape" in shapes, "governance SHACL shapes missing")
    require("non-operative" in constitution.lower() and "any operative effect" in constitution.lower() and "founding period" in constitution.lower(), "Constitution bootstrap/Mission Lock declarations missing")
    require("strong stewardship without ownership" in founding_doc.lower() and "ends only upon a valid" in founding_doc.lower(), "Founding Stewardship boundary missing")
    require("one person = one member = one vote" in membership_doc.lower(), "Membership equality prose missing")
    require("conforming graph is not proof" in machine_spec.lower(), "machine/legal authority boundary missing")
    require("accepted contribution" in individual_cla.lower() and "accepted contribution" in entity_cla.lower() and "limited pre-acceptance review rights" in entity_cla.lower(), "CLA acceptance gate missing")
    validate_cla_status()
    print("Exergism Commons governance integrity: PASS")
    print(f"governance_version={version} operative={status['operative']} state={status['institutional_state']} phase={status['institutional_phase']}")
    print(f"decision_rules={len(rules['rules'])} delegations={len(delegations['delegations'])} member_records={len(membership['members'])}")


if __name__ == "__main__":
    main()
