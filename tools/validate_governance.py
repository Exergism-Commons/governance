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
CANONICAL_GOVERNANCE_PATHS = {
    "constitution": "CONSTITUTION.md",
    "membership_policy": "MEMBERSHIP.md",
    "founding_stewardship_policy": "FOUNDING-STEWARDSHIP.md",
}
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
    require(match is not None, f"YAML missing key: {key}")
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
            for child in lines[index + 1:]:
                if not child.strip():
                    children.append("")
                    continue
                child_indent = len(child) - len(child.lstrip())
                if child_indent <= indent:
                    break
                children.append(child[min(len(child), indent + 2):])
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
    require(match is not None, f"YAML missing {parent}.{key}")
    return match.group(1) == "true"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def require_sha256(value, label: str) -> str:
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
            f"{label} must be lowercase SHA-256")
    return value


def repo_file(value, label: str, prefix: str | None = None) -> Path:
    require(isinstance(value, str) and value.strip(), f"{label} path is required")
    relative = Path(value)
    require(not relative.is_absolute() and ".." not in relative.parts,
            f"{label} must be repository-relative")
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
    months = (end.year - start.year) * 12 + end.month - start.month
    if end.day < start.day:
        months -= 1
    return months


def exact_fraction(spec: dict, numerator: int, denominator: int, comparison: str) -> bool:
    return (
        isinstance(spec, dict)
        and spec.get("numerator") == numerator
        and spec.get("denominator") == denominator
        and spec.get("comparison") == comparison
    )


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


def validate_supporting_evidence_ref(ref, label: str, governance_version: str) -> dict:
    data, _ = validate_content_ref(ref, label, "records/evidence")
    require(data.get("record_type") == "supporting-evidence", f"{label} must be supporting-evidence")
    require(data.get("status") == "final", f"{label} must be final")
    require(data.get("governance_version") == governance_version, f"{label} governance version mismatch")
    require(isinstance(data.get("evidence_id"), str) and data["evidence_id"].strip(),
            f"{label} evidence_id required")
    require(isinstance(data.get("claim"), str) and data["claim"].strip(), f"{label} claim required")
    source = data.get("source")
    require(isinstance(source, dict) and isinstance(source.get("type"), str) and source["type"].strip(),
            f"{label} source.type required")
    require(isinstance(source.get("identifier"), str) and source["identifier"].strip(),
            f"{label} source.identifier required")
    parse_iso_date(data.get("captured_date"), f"{label}.captured_date")
    return data


def validate_process_evidence_ref(ref, label: str, expected_type: str, governance_version: str) -> dict:
    data, _ = validate_content_ref(ref, label, "records/evidence")
    require(data.get("record_type") == expected_type, f"{label} record_type mismatch")
    require(data.get("status") == "final", f"{label} must be final")
    require(data.get("governance_version") == governance_version, f"{label} governance version mismatch")
    require(isinstance(data.get("evidence_id"), str) and data["evidence_id"].strip(), f"{label} evidence_id required")
    require(isinstance(data.get("subject"), str) and data["subject"].strip(), f"{label} subject required")
    require(data.get("complete") is True, f"{label} must record complete=true")
    require(data.get("result") in {"implemented", "satisfied", "pass", "complete"},
            f"{label} must record a successful substantive result")
    reviewers = data.get("reviewer_ids")
    require(isinstance(reviewers, list) and reviewers and len(reviewers) == len(set(reviewers)),
            f"{label} requires distinct reviewer_ids")
    supporting = data.get("supporting_evidence")
    require(isinstance(supporting, list) and supporting, f"{label} requires supporting evidence")
    for index, item in enumerate(supporting):
        validate_supporting_evidence_ref(item, f"{label} supporting evidence {index}", governance_version)
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


def rule_by_id(rules: dict) -> dict[str, dict]:
    values = rules.get("rules")
    require(isinstance(values, list), "decision rules must be a list")
    result = {}
    for rule in values:
        rule_id = rule.get("id")
        require(isinstance(rule_id, str) and rule_id and rule_id not in result, "invalid/duplicate decision rule id")
        result[rule_id] = rule
    return result


def member_index(membership: dict) -> dict[str, dict]:
    members = membership.get("members")
    require(isinstance(members, list), "membership members must be a list")
    by_person: dict[str, dict] = {}
    record_ids: set[str] = set()
    for item in members:
        record_id = item.get("record_id")
        person_id = item.get("person_id")
        require(isinstance(record_id, str) and record_id, "member record_id required")
        require(isinstance(person_id, str) and person_id, "member person_id required")
        require(record_id not in record_ids, f"duplicate member record_id: {record_id}")
        require(person_id not in by_person, f"duplicate member person_id: {person_id}")
        record_ids.add(record_id)
        by_person[person_id] = item
    return by_person


def active_members_as_of(membership: dict, decision_date: date, rule_id: str) -> set[str]:
    seasoning = membership["voting_seasoning_days"][rule_id]
    result = set()
    for person_id, item in member_index(membership).items():
        if item.get("operative_membership") is not True or item.get("state") != "active":
            continue
        active_since = parse_iso_date(item.get("active_since"), f"member {person_id}.active_since")
        days = (decision_date - active_since).days
        if days >= seasoning:
            result.add(person_id)
    return result


def compare_ratio(lhs: int, rhs: int, spec: dict) -> bool:
    numerator = spec["numerator"]
    denominator = spec["denominator"]
    comparison = spec["comparison"]
    left = lhs * denominator
    right = rhs * numerator
    if comparison == "at_least":
        return left >= right
    if comparison == "strictly_greater_than":
        return left > right
    raise SystemExit(f"governance integrity failure: unsupported ratio comparison: {comparison}")


def validate_vote_approval(
    data: dict,
    label: str,
    expected_decision_id: str,
    expected_rule_id: str,
    status: dict,
    rules: dict,
    membership: dict,
    expected_artifact_bindings: dict | None = None,
) -> None:
    require(data.get("approval_mode") == "member-vote", f"{label} must use member-vote approval")
    require(data.get("decision_id") == expected_decision_id, f"{label} decision_id mismatch")
    require(data.get("decision_class") == expected_rule_id, f"{label} decision class mismatch")
    require(data.get("rule_version") == status["governance_version"], f"{label} rule version mismatch")
    decision_date = parse_iso_date(data.get("decision_date"), f"{label}.decision_date")
    rule = rule_by_id(rules).get(expected_rule_id)
    require(rule is not None, f"{label} references unknown decision class")

    electorate = data.get("electorate")
    require(isinstance(electorate, dict), f"{label} electorate required")
    eligible = electorate.get("eligible_person_ids")
    recused = electorate.get("recused_person_ids")
    require(isinstance(eligible, list) and len(eligible) == len(set(eligible)), f"{label} eligible electorate invalid")
    require(isinstance(recused, list) and len(recused) == len(set(recused)), f"{label} recusals invalid")
    require(set(recused).issubset(set(eligible)), f"{label} recused voters must be eligible")
    derived_eligible = active_members_as_of(membership, decision_date, expected_rule_id)
    require(set(eligible) == derived_eligible, f"{label} electorate does not match active seasoned Member Registry")
    effective = set(eligible) - set(recused)
    require(effective, f"{label} has empty effective electorate")

    ballots = data.get("ballots")
    require(isinstance(ballots, list), f"{label} ballots must be a list")
    seen: set[str] = set()
    counts = {"for": 0, "against": 0, "abstain": 0}
    for ballot in ballots:
        person_id = ballot.get("person_id")
        vote = ballot.get("vote")
        require(person_id in effective, f"{label} ballot by ineligible/recused voter: {person_id}")
        require(person_id not in seen, f"{label} duplicate ballot: {person_id}")
        require(vote in counts, f"{label} invalid vote value")
        seen.add(person_id)
        counts[vote] += 1

    tally = data.get("tally")
    expected_tally = {
        "eligible": len(eligible),
        "recused": len(recused),
        "effective_eligible": len(effective),
        "votes_for": counts["for"],
        "votes_against": counts["against"],
        "abstentions": counts["abstain"],
    }
    require(tally == expected_tally, f"{label} recorded tally does not match ballots/electorate")

    participation = len(ballots)
    quorum = rule["quorum"]
    require(compare_ratio(participation, len(effective), quorum), f"{label} quorum not satisfied")
    valid = counts["for"] + counts["against"]
    require(valid > 0, f"{label} zero for/against denominator must fail")
    require(counts["for"] >= rule.get("minimum_affirmative_votes", 1), f"{label} minimum affirmative votes not met")
    approval = rule["approval"]
    if approval["type"] == "votes_for_vs_against":
        approved = counts["for"] > counts["against"]
    else:
        approved = compare_ratio(counts["for"], valid, approval)
    require(approved, f"{label} approval threshold not satisfied")
    require(data.get("result") == "approved", f"{label} must record result=approved")
    if expected_artifact_bindings is not None:
        require(data.get("artifact_bindings") == expected_artifact_bindings,
                f"{label} artifact bindings mismatch")


def validate_constitutive_approval(
    data: dict,
    label: str,
    expected_decision_id: str,
    status: dict,
    legal_entity: dict,
    expected_artifact_bindings: dict,
) -> None:
    require(data.get("approval_mode") == "constitutive-adoption", f"{label} must use constitutive-adoption")
    require(data.get("decision_id") == expected_decision_id, f"{label} decision_id mismatch")
    require(data.get("result") == "approved", f"{label} must record result=approved")
    require(data.get("artifact_bindings") == expected_artifact_bindings, f"{label} artifact bindings mismatch")
    basis_ref = data.get("competence_basis")
    basis, _ = validate_content_ref(basis_ref, f"{label} competence basis", "records/evidence")
    require(basis.get("record_type") == "constitutive-authority-evidence", f"{label} competence basis type mismatch")
    require(basis.get("status") == "final", f"{label} competence basis must be final")
    require(basis.get("governance_version") == status["governance_version"], f"{label} competence basis version mismatch")
    require(basis.get("legal_entity_identity") == {k: v for k, v in legal_entity.items() if k != "evidence"},
            f"{label} competence basis legal entity mismatch")
    signatories = data.get("competent_signatory_ids")
    require(isinstance(signatories, list) and signatories and len(signatories) == len(set(signatories)),
            f"{label} competent signatories invalid")
    require(signatories == legal_entity["competent_signatories"], f"{label} competent signatories mismatch")
    signatures = data.get("signature_evidence")
    require(isinstance(signatures, list) and len(signatures) == len(signatories),
            f"{label} signature evidence incomplete")
    signed_ids = set()
    for index, ref in enumerate(signatures):
        sig, _ = validate_content_ref(ref, f"{label} signature {index}", "records/evidence")
        require(sig.get("record_type") == "signature-evidence" and sig.get("status") == "final",
                f"{label} invalid signature evidence")
        require(sig.get("decision_id") == expected_decision_id and sig.get("result") == "signed",
                f"{label} signature decision/result mismatch")
        person_id = sig.get("person_id")
        require(person_id in signatories and person_id not in signed_ids, f"{label} signature identity mismatch")
        signed_ids.add(person_id)
    require(signed_ids == set(signatories), f"{label} missing competent signature")


def validate_approval_evidence(
    ref,
    label: str,
    expected_decision_id: str,
    status: dict,
    rules: dict,
    membership: dict,
    expected_rule_id: str | None = None,
    expected_artifact_bindings: dict | None = None,
    allow_constitutive: bool = False,
    legal_entity: dict | None = None,
) -> dict:
    data, _ = validate_content_ref(ref, label, "records/evidence")
    require(data.get("record_type") == "approval-evidence", f"{label} record_type mismatch")
    require(data.get("status") == "final", f"{label} must be final")
    require(data.get("governance_version") == status["governance_version"], f"{label} governance version mismatch")
    require(isinstance(data.get("evidence_id"), str) and data["evidence_id"].strip(), f"{label} evidence_id required")
    if allow_constitutive and data.get("approval_mode") == "constitutive-adoption":
        require(legal_entity is not None and expected_artifact_bindings is not None,
                f"{label} constitutive validation context missing")
        validate_constitutive_approval(
            data, label, expected_decision_id, status, legal_entity, expected_artifact_bindings
        )
    else:
        require(expected_rule_id is not None, f"{label} expected decision rule missing")
        validate_vote_approval(
            data, label, expected_decision_id, expected_rule_id, status, rules, membership,
            expected_artifact_bindings
        )
    return data


def validate_governance_artifacts(status: dict) -> None:
    for key, path in CANONICAL_GOVERNANCE_PATHS.items():
        require(status.get(key) == path, f"{key} canonical path must remain fixed to {path}")
    artifacts = status.get("governance_artifacts")
    require(isinstance(artifacts, dict) and set(artifacts) == set(CANONICAL_GOVERNANCE_PATHS),
            "unexpected governance artifact set")
    for name, canonical_path in CANONICAL_GOVERNANCE_PATHS.items():
        item = artifacts[name]
        require(item.get("path") == canonical_path, f"{name} path cannot be redirected")
        path = repo_file(canonical_path, name)
        if status["operative"] is False:
            require(item.get("status") == "draft", f"draft {name} must be marked draft")
            require("-DRAFT" in str(item.get("version")), f"draft {name} version must be DRAFT")
            require(item.get("sha256") is None, f"draft {name} must not claim adopted-byte digest")
            continue
        require(item.get("status") in {"adopted", "operative"}, f"operative {name} must be adopted")
        version = str(item.get("version"))
        require(version and "-DRAFT" not in version, f"operative {name} version cannot be draft")
        require(sha256_file(path) == require_sha256(item.get("sha256"), f"{name}.sha256"),
                f"{name} bytes do not match recorded SHA-256")
        text = path.read_text(encoding="utf-8")
        require(not contradictory_status_declaration(text),
                f"operative {name} contains contradictory draft/non-operative declaration")
        require_version_header(text, version, name)

    constitution = repo_file(CANONICAL_GOVERNANCE_PATHS["constitution"], "constitution").read_text(encoding="utf-8")
    membership_doc = repo_file(CANONICAL_GOVERNANCE_PATHS["membership_policy"], "membership policy").read_text(encoding="utf-8")
    founding_doc = repo_file(CANONICAL_GOVERNANCE_PATHS["founding_stewardship_policy"], "founding stewardship").read_text(encoding="utf-8")
    require("one person = one member = one vote" in membership_doc.lower(), "canonical Membership equality rule missing")
    require("any operative effect" in constitution.lower() and "founding period" in constitution.lower(),
            "canonical Constitution Mission Lock/founding boundary missing")
    require("strong stewardship without ownership" in founding_doc.lower()
            and "ends only upon a valid" in founding_doc.lower(),
            "canonical Founding Stewardship boundary missing")


def validate_legal_entity(status: dict) -> dict | None:
    entity = status.get("legal_entity")
    if status["operative"] is False:
        require(entity is None, "bootstrap cannot fabricate legal entity")
        return None
    require(isinstance(entity, dict), "operative legal_entity must be structured")
    required = {
        "legal_name", "jurisdiction", "registration_identity", "governing_instrument",
        "relationship_to_public_project", "competent_signatories", "evidence",
    }
    require(set(entity) == required, "operative legal_entity fields incomplete/unexpected")
    for key in required - {"competent_signatories", "evidence"}:
        require(isinstance(entity[key], str) and entity[key].strip(), f"legal_entity.{key} required")
    signatories = entity["competent_signatories"]
    require(isinstance(signatories, list) and signatories and len(signatories) == len(set(signatories)),
            "legal_entity competent_signatories invalid")
    require(all(isinstance(x, str) and x.strip() for x in signatories),
            "legal_entity competent_signatories must be stable IDs")
    evidence, _ = validate_content_ref(entity["evidence"], "legal entity identity evidence", "records/evidence")
    require(evidence.get("record_type") == "legal-entity-identity-evidence"
            and evidence.get("status") == "final", "legal entity evidence invalid")
    require(evidence.get("governance_version") == status["governance_version"],
            "legal entity evidence version mismatch")
    require(evidence.get("entity_identity") == {k: v for k, v in entity.items() if k != "evidence"},
            "legal entity evidence does not bind exact entity identity")
    return entity


def validate_activation_evidence(status: dict) -> dict[str, str]:
    evidence = status.get("activation_evidence")
    expected = {
        "conflict_process": "conflict-process-evidence",
        "records_privacy_process": "records-privacy-process-evidence",
        "treasury_controls": "treasury-controls-evidence",
        "succession_process": "succession-process-evidence",
        "qualified_legal_review": "qualified-legal-review-evidence",
    }
    require(isinstance(evidence, dict) and set(evidence) == set(expected),
            "unexpected activation_evidence set")
    if status["operative"] is False:
        require(all(value is None for value in evidence.values()), "draft governance cannot claim activation evidence")
        return {}
    hashes = {}
    for key, record_type in expected.items():
        validate_process_evidence_ref(
            evidence[key], f"activation evidence {key}", record_type, status["governance_version"]
        )
        hashes[key] = evidence[key]["sha256"]
    return hashes


def validate_adoption_record(
    status: dict,
    activation_hashes: dict[str, str],
    rules: dict,
    membership: dict,
    legal_entity: dict | None,
) -> None:
    if status["operative"] is False:
        require(status.get("adoption_record") is None, "draft governance cannot claim adoption record")
        return
    require(legal_entity is not None, "operative adoption requires validated legal entity")
    record, _ = validate_content_ref(status.get("adoption_record"), "governance adoption record", "records/adoptions")
    require(record.get("record_type") == "governance-adoption" and record.get("status") == "adopted",
            "governance adoption record invalid")
    require(record.get("governance_version") == status["governance_version"], "adoption governance version mismatch")
    require(record.get("effective_date") == status["effective_date"], "adoption effective date mismatch")
    require(record.get("legal_entity") == {k: v for k, v in legal_entity.items() if k != "evidence"},
            "adoption legal entity identity mismatch")
    require(record.get("governing_law") == status["governing_law"], "adoption governing law mismatch")
    decision_id = record.get("decision_id")
    require(isinstance(decision_id, str) and decision_id.strip(), "adoption decision_id required")
    require(isinstance(record.get("adoption_method"), str) and record["adoption_method"].strip(),
            "adoption_method required")
    expected_bindings = {name: item["sha256"] for name, item in status["governance_artifacts"].items()}
    require(record.get("artifact_bindings") == expected_bindings,
            "adoption record does not bind exact governance artifacts")
    validate_approval_evidence(
        record.get("approval_evidence"), "governance adoption approval", decision_id, status,
        rules, membership, expected_artifact_bindings=expected_bindings,
        allow_constitutive=True, legal_entity=legal_entity
    )
    expected_machine_paths = (
        "policy/decision-rules.json",
        "policy/membership-status.json",
        "policy/founding-stewardship.json",
        "policy/delegations.json",
        "policy/phase-evidence.json",
    )
    machine = record.get("machine_bindings")
    require(isinstance(machine, dict) and set(machine) == set(expected_machine_paths),
            "adoption machine_bindings incomplete")
    for path_value in expected_machine_paths:
        require(machine[path_value] == sha256_file(repo_file(path_value, f"adoption binding {path_value}")),
                f"adoption machine binding mismatch: {path_value}")
    require(record.get("activation_evidence_hashes") == activation_hashes,
            "adoption record does not bind activation evidence")


def parse_covered_project_states(text: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    current_repo = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- repository:"):
            current_repo = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("cla_coverage:") and current_repo is not None:
            rows.append((current_repo, stripped.split(":", 1)[1].strip()))
            current_repo = None
    return rows


def validate_covered_projects(status_text: str, projects_text: str) -> str:
    artifact = yaml_scalar(status_text, "covered_projects_artifact")
    require(artifact == "policy/covered-projects.yaml", "covered-projects canonical artifact path changed")
    path = repo_file(artifact, "covered_projects_artifact")
    recorded = require_sha256(yaml_scalar(status_text, "covered_projects_sha256"), "covered_projects_sha256")
    require(sha256_file(path) == recorded, "covered-projects bytes do not match recorded SHA-256")
    require(yaml_scalar(projects_text, "schema_version") == "2", "unsupported covered-projects schema")
    schedule_version = str(yaml_scalar(status_text, "project_schedule_version"))
    require(yaml_scalar(projects_text, "schedule_version") == schedule_version,
            "covered-projects schedule version mismatch")
    require(yaml_scalar(projects_text, "operative") is True, "operative CLA requires operative covered-projects")
    require(yaml_scalar(projects_text, "status") in {"adopted", "operative"},
            "operative covered-projects must be adopted/operative")
    final_states = set(yaml_list(projects_text, "final_states"))
    provisional_states = set(yaml_list(projects_text, "provisional_states"))
    require(final_states and not final_states.intersection(provisional_states),
            "covered-projects state contract invalid")
    rows = parse_covered_project_states(projects_text)
    require(rows, "covered-projects must contain repositories")
    for repository, state in rows:
        require(state in final_states and state not in provisional_states,
                f"covered-projects repository not final: {repository}={state}")
    require("current_outbound: unresolved" not in projects_text
            and "cla_outbound_family: unresolved" not in projects_text,
            "operative covered-projects cannot retain unresolved outbound terms")
    return recorded


def validate_cla_artifact(status_text: str, version_key: str, artifact_key: str, hash_key: str, identity_prefix: str) -> str:
    version = str(yaml_scalar(status_text, version_key))
    artifact = yaml_scalar(status_text, artifact_key)
    require(isinstance(artifact, str) and artifact and "DRAFT" not in artifact.upper(),
            f"operative {artifact_key} cannot point to draft artifact")
    path = repo_file(artifact, artifact_key)
    recorded = require_sha256(yaml_scalar(status_text, hash_key), hash_key)
    require(sha256_file(path) == recorded, f"{artifact_key} bytes do not match recorded SHA-256")
    text = path.read_text(encoding="utf-8")
    require(not contradictory_status_declaration(text),
            f"operative {artifact_key} contains contradictory draft/non-operative declaration")
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
    require(not contradictory_status_declaration(text),
            "operative Project Schedule contains contradictory draft/non-operative declaration")
    require_version_header(text, version, "Project Schedule")
    return recorded


def validate_cla_status() -> None:
    status_text = (ROOT / "policy/cla-status.yaml").read_text(encoding="utf-8")
    projects_text = (ROOT / "policy/covered-projects.yaml").read_text(encoding="utf-8")
    require(yaml_scalar(status_text, "schema_version") == "4", "unsupported CLA status schema")
    operative = yaml_scalar(status_text, "operative")
    blockers = yaml_list(status_text, "activation_blockers")
    for key in ("individual_artifact", "entity_artifact", "project_schedule_artifact", "covered_projects_artifact"):
        repo_file(yaml_scalar(status_text, key), key)
    if operative is False:
        require(yaml_scalar(status_text, "status") == "draft", "non-operative CLA must remain draft")
        for key in ("legal_steward", "governing_law", "forum", "effective_date", "privacy_records_policy",
                    "privacy_records_policy_artifact", "privacy_records_policy_sha256",
                    "individual_sha256", "entity_sha256", "project_schedule_sha256",
                    "covered_projects_sha256", "legal_review_manifest_artifact",
                    "legal_review_manifest_sha256", "adoption_record_artifact", "adoption_record_sha256"):
            require(yaml_scalar(status_text, key) is None, f"draft CLA cannot claim {key}")
        require(len(blockers) > 0, "draft CLA must expose activation blockers")
        for key in ("individual_version", "entity_version", "project_schedule_version"):
            require("-DRAFT" in str(yaml_scalar(status_text, key)), f"draft {key} must remain DRAFT")
        return

    require(operative is True and yaml_scalar(status_text, "status") in {"adopted", "operative"},
            "operative CLA status invalid")
    legal_steward = yaml_scalar(status_text, "legal_steward")
    governing_law = yaml_scalar(status_text, "governing_law")
    forum = yaml_scalar(status_text, "forum")
    effective_date = yaml_scalar(status_text, "effective_date")
    privacy_policy = yaml_scalar(status_text, "privacy_records_policy")
    require(all(isinstance(x, str) and x.strip() for x in
                (legal_steward, governing_law, forum, effective_date, privacy_policy)),
            "operative CLA requires Steward, law, forum, effective date and privacy policy identifiers")
    parse_iso_date(effective_date, "CLA effective_date")
    acceptance_methods = yaml_list(status_text, "acceptance_methods")
    require(acceptance_methods and len(acceptance_methods) == len(set(acceptance_methods)),
            "operative CLA requires distinct acceptance methods")
    require(yaml_nested_bool(status_text, "legal_review", "complete") is True,
            "operative CLA requires completed legal review")
    require(blockers == [], "operative CLA cannot retain activation blockers")
    for key in ("individual_version", "entity_version", "project_schedule_version"):
        require("-DRAFT" not in str(yaml_scalar(status_text, key)), f"operative {key} cannot be draft")

    individual_hash = validate_cla_artifact(
        status_text, "individual_version", "individual_artifact", "individual_sha256", "EC-ICLA")
    entity_hash = validate_cla_artifact(
        status_text, "entity_version", "entity_artifact", "entity_sha256", "EC-ECLA")
    schedule_hash = validate_project_schedule_artifact(status_text)
    covered_hash = validate_covered_projects(status_text, projects_text)

    privacy_artifact = yaml_scalar(status_text, "privacy_records_policy_artifact")
    privacy_path = repo_file(privacy_artifact, "privacy_records_policy_artifact")
    privacy_hash = require_sha256(yaml_scalar(status_text, "privacy_records_policy_sha256"),
                                 "privacy_records_policy_sha256")
    require(sha256_file(privacy_path) == privacy_hash, "privacy records policy bytes mismatch")

    legal_terms = {
        "legal_steward": legal_steward,
        "governing_law": governing_law,
        "forum": forum,
        "privacy_records_policy": privacy_policy,
        "privacy_records_policy_sha256": privacy_hash,
        "acceptance_methods": sorted(acceptance_methods),
    }
    artifact_hashes = {
        "individual": individual_hash,
        "entity": entity_hash,
        "project_schedule": schedule_hash,
        "covered_projects": covered_hash,
    }

    manifest_ref = {
        "path": yaml_scalar(status_text, "legal_review_manifest_artifact"),
        "sha256": yaml_scalar(status_text, "legal_review_manifest_sha256"),
    }
    manifest, _ = validate_content_ref(manifest_ref, "CLA legal review manifest", "records/reviews")
    require(manifest.get("record_type") == "qualified-legal-review" and manifest.get("status") == "final",
            "CLA legal review manifest invalid")
    reviewers = manifest.get("reviewer_ids")
    require(isinstance(reviewers, list) and reviewers and len(reviewers) == len(set(reviewers)),
            "CLA legal review requires distinct reviewer ids")
    require(manifest.get("reviewed_artifact_hashes") == artifact_hashes,
            "CLA legal review does not bind exact operative artifacts")
    require(manifest.get("reviewed_legal_terms") == legal_terms,
            "CLA legal review does not bind operative Steward/law/forum/privacy/acceptance terms")
    require(manifest.get("conclusion") in {"approved", "approved-with-resolved-notes"},
            "CLA legal review conclusion not approving")

    adoption_ref = {
        "path": yaml_scalar(status_text, "adoption_record_artifact"),
        "sha256": yaml_scalar(status_text, "adoption_record_sha256"),
    }
    adoption, _ = validate_content_ref(adoption_ref, "CLA adoption record", "records/adoptions")
    require(adoption.get("record_type") == "cla-adoption" and adoption.get("status") == "adopted",
            "CLA adoption record invalid")
    require(adoption.get("effective_date") == effective_date, "CLA adoption effective date mismatch")
    require(adoption.get("legal_terms") == legal_terms,
            "CLA adoption does not bind operative Steward/law/forum/privacy/acceptance terms")
    require(adoption.get("versions") == {
        "individual": yaml_scalar(status_text, "individual_version"),
        "entity": yaml_scalar(status_text, "entity_version"),
        "project_schedule": yaml_scalar(status_text, "project_schedule_version"),
    }, "CLA adoption version bindings mismatch")
    require(adoption.get("artifact_hashes") == artifact_hashes,
            "CLA adoption artifact bindings mismatch")
    require(adoption.get("legal_review_manifest_sha256") == manifest_ref["sha256"],
            "CLA adoption does not bind legal-review manifest")
    require(isinstance(adoption.get("adopters"), list) and adoption["adopters"]
            and len(adoption["adopters"]) == len(set(adoption["adopters"])),
            "CLA adoption requires distinct adopter identities")


def validate_membership_registry(membership: dict) -> tuple[dict[str, dict], set[str]]:
    require(membership["schema_version"] == 3, "unsupported membership schema")
    by_person = member_index(membership)
    active = set()
    for person_id, item in by_person.items():
        if item.get("operative_membership") is True:
            require(item.get("state") == "active", f"operative member {person_id} must be active")
            parse_iso_date(item.get("active_since"), f"member {person_id}.active_since")
            require(item.get("admission_record") is not None, f"operative member {person_id} requires admission record")
            admission, _ = validate_content_ref(
                item["admission_record"], f"member admission {person_id}", "records/decisions")
            require(admission.get("record_type") == "membership-admission"
                    and admission.get("status") == "adopted", f"member admission invalid: {person_id}")
            require(admission.get("person_id") == person_id, f"member admission identity mismatch: {person_id}")
            active.add(person_id)
        else:
            require(item.get("state") != "active" or membership["operative"] is True,
                    f"non-operative member row cannot claim active state: {person_id}")
    return by_person, active


def validate_delegations(
    delegations: dict,
    status: dict,
    rules: dict,
    membership: dict,
) -> list[dict]:
    require(delegations["schema_version"] == 3, "unsupported delegations schema")
    require(CRITICAL_DELEGATION_SCOPES.issubset(set(delegations.get("scope_vocabulary", []))),
            "delegation scope vocabulary missing critical scopes")
    items = delegations.get("delegations")
    require(isinstance(items, list), "delegations must be a list")
    ids: set[str] = set()
    active = []
    reserved = set(delegations.get("reserved_non_delegable_actions", []))
    for item in items:
        delegation_id = item.get("delegation_id")
        require(isinstance(delegation_id, str) and delegation_id and delegation_id not in ids,
                "delegation_id required/unique")
        ids.add(delegation_id)
        if item.get("operative") is not True:
            continue

        required = {
            "delegation_id", "holder_person_id", "source_authority", "scope_types", "scope_resources",
            "allowed_actions", "prohibited_actions", "governing_rule_version", "effective_date",
            "expires_at", "revocation", "operative", "decision_record",
        }
        require(set(item) == required, f"operative delegation {delegation_id} fields incomplete/unexpected")
        holder = item["holder_person_id"]
        require(isinstance(holder, str) and holder, f"delegation {delegation_id} holder required")
        source = item["source_authority"]
        require(isinstance(source, str) and source.strip(), f"delegation {delegation_id} source_authority required")
        scopes = item["scope_types"]
        require(isinstance(scopes, list) and scopes and len(scopes) == len(set(scopes)),
                f"delegation {delegation_id} scopes invalid")
        require(set(scopes).issubset(set(delegations["scope_vocabulary"])),
                f"delegation {delegation_id} unknown scope")
        resources = item["scope_resources"]
        require(isinstance(resources, dict) and set(resources) == set(scopes),
                f"delegation {delegation_id} scope_resources must cover exact scopes")
        for scope, vals in resources.items():
            require(isinstance(vals, list) and vals and all(isinstance(v, str) and v.strip() for v in vals),
                    f"delegation {delegation_id} resources invalid for {scope}")
        allowed = item["allowed_actions"]
        prohibited = item["prohibited_actions"]
        require(isinstance(allowed, list) and allowed and len(allowed) == len(set(allowed)),
                f"delegation {delegation_id} allowed_actions invalid")
        require(isinstance(prohibited, list) and prohibited and len(prohibited) == len(set(prohibited)),
                f"delegation {delegation_id} prohibited_actions invalid")
        require(not reserved.intersection(allowed), f"delegation {delegation_id} grants reserved action")
        require(reserved.issubset(set(prohibited)), f"delegation {delegation_id} must explicitly prohibit reserved actions")
        require(item["governing_rule_version"] == status["governance_version"],
                f"delegation {delegation_id} governing rule mismatch")
        effective = parse_iso_date(item["effective_date"], f"delegation {delegation_id}.effective_date")
        if item["expires_at"] is not None:
            require(parse_iso_date(item["expires_at"], f"delegation {delegation_id}.expires_at") >= effective,
                    f"delegation {delegation_id} expires before effective date")
        revocation = item["revocation"]
        require(isinstance(revocation, dict)
                and revocation.get("revocable") is True
                and isinstance(revocation.get("mechanism"), str) and revocation["mechanism"].strip()
                and isinstance(revocation.get("authority"), str) and revocation["authority"].strip(),
                f"delegation {delegation_id} revocation contract invalid")

        decision, _ = validate_content_ref(
            item["decision_record"], f"delegation decision {delegation_id}", "records/decisions")
        require(decision.get("record_type") == "delegation-decision"
                and decision.get("status") == "adopted", f"delegation decision invalid: {delegation_id}")
        require(decision.get("governance_version") == status["governance_version"],
                f"delegation decision version mismatch: {delegation_id}")
        for field in ("delegation_id", "holder_person_id", "source_authority", "scope_types",
                      "scope_resources", "allowed_actions", "prohibited_actions",
                      "governing_rule_version", "effective_date", "expires_at", "revocation"):
            require(decision.get(field) == item[field], f"delegation decision field mismatch: {delegation_id}.{field}")
        decision_id = decision.get("decision_id")
        decision_class = decision.get("decision_class")
        require(isinstance(decision_id, str) and decision_id, f"delegation decision_id required: {delegation_id}")
        require(decision_class in rule_by_id(rules), f"delegation decision class invalid: {delegation_id}")
        delegation_payload = {k: v for k, v in item.items() if k != "decision_record"}
        payload_hash = sha256_json(delegation_payload)
        require(decision.get("delegation_payload_sha256") == payload_hash,
                f"delegation decision payload hash mismatch: {delegation_id}")
        validate_approval_evidence(
            decision.get("approval_evidence"), f"delegation approval {delegation_id}",
            decision_id, status, rules, membership, expected_rule_id=decision_class,
            expected_artifact_bindings={"delegation_payload_sha256": payload_hash}
        )
        active.append(item)
    return active


def validate_phase_transition_record(
    ref,
    status: dict,
    phase_evidence: dict,
    rules: dict,
    membership: dict,
) -> dict:
    record, _ = validate_content_ref(ref, "phase transition decision", "records/decisions")
    require(record.get("record_type") == "phase-transition" and record.get("status") == "adopted",
            "phase transition record invalid")
    require(record.get("governance_version") == status["governance_version"],
            "phase transition governance version mismatch")
    require(record.get("to_phase") == status["institutional_phase"], "phase transition target mismatch")
    require(record.get("effective_date") == phase_evidence["phase_effective_date"],
            "phase transition effective date mismatch")
    decision_id = record.get("decision_id")
    require(isinstance(decision_id, str) and decision_id.strip(), "phase transition decision_id required")
    require(record.get("decision_class") == "qualified-approval",
            "F1/F2 phase transition must use Qualified Approval")
    expected_from = {
        "F1-early-institution": "F0-founder-led-bootstrap",
        "F2-distributed-institution": "F1-early-institution",
    }
    require(record.get("from_phase") == expected_from[status["institutional_phase"]],
            "phase transition source mismatch")
    transition_payload = {k: v for k, v in record.items() if k != "approval_evidence"}
    payload_hash = sha256_json(transition_payload)
    require(record.get("transition_payload_sha256") == payload_hash,
            "phase transition payload hash mismatch")
    validate_approval_evidence(
        record.get("approval_evidence"), "phase transition approval", decision_id, status,
        rules, membership, expected_rule_id="qualified-approval",
        expected_artifact_bindings={"transition_payload_sha256": payload_hash}
    )
    return record


def validate_phase_evidence(
    status: dict,
    membership: dict,
    founding: dict,
    phase_evidence: dict,
    active_delegations: list[dict],
    active_members: set[str],
    rules: dict,
) -> None:
    require(phase_evidence["schema_version"] == 2, "unsupported phase-evidence schema")
    require(phase_evidence["governance_version"] == status["governance_version"],
            "phase-evidence governance version mismatch")
    require(phase_evidence["current_phase"] == status["institutional_phase"],
            "phase-evidence/current phase mismatch")
    require(phase_evidence.get("evidence_reference_contract") ==
            {"type": "content-addressed-json", "required_fields": ["path", "sha256"]},
            "phase evidence reference contract mismatch")
    f1 = phase_evidence["f1"]
    f2 = phase_evidence["f2"]

    if status["operative"] is False:
        require(phase_evidence["operative"] is False
                and phase_evidence["current_phase"] == "F0-founder-led-bootstrap",
                "draft phase evidence must remain non-operative F0")
        require(phase_evidence["governance_operative_since"] is None
                and phase_evidence["phase_effective_date"] is None
                and phase_evidence["transition_decision_record"] is None,
                "draft phase evidence cannot fabricate dates/decision")
        for value in (
            f1["independent_role_holder_evidence"], f1["delegation_evidence"],
            f2["control_separation_evidence"], f2["audit_review_evidence"],
            f2["role_replacement_evidence"],
        ):
            require(value is None, "draft phase evidence cannot claim evidence")
        return

    effective = parse_iso_date(status["effective_date"], "governance effective_date")
    operative_since = parse_iso_date(phase_evidence["governance_operative_since"], "governance_operative_since")
    phase_date = parse_iso_date(phase_evidence["phase_effective_date"], "phase_effective_date")
    require(phase_evidence["operative"] is True, "operative governance requires operative phase evidence")
    require(operative_since == effective, "governance_operative_since must equal governance effective_date")
    require(phase_date >= effective, "phase effective date cannot precede governance effective_date")
    require(f1["minimum_active_members"] == founding["phase_transition"]["f1_min_active_members"],
            "F1 member threshold mismatch")
    require(f2["minimum_active_members"] == founding["phase_transition"]["f2_min_active_members"],
            "F2 member threshold mismatch")
    require(f2["minimum_operational_months"] == founding["phase_transition"]["f2_min_operational_months"],
            "F2 time threshold mismatch")

    phase = status["institutional_phase"]
    if phase == "F0-founder-led-bootstrap":
        require(phase_evidence["transition_decision_record"] is None,
                "F0 initial adoption must not fabricate phase transition")
        require(phase_date == effective, "operative F0 phase date must equal governance effective date")
        return

    validate_phase_transition_record(
        phase_evidence["transition_decision_record"], status, phase_evidence, rules, membership
    )
    require(len(active_members) >= f1["minimum_active_members"],
            "F1/F2 requires minimum distinct Active Members")
    founder_person = founding["founding_steward"]["person_id"]
    independent_holders = {d["holder_person_id"] for d in active_delegations if d["holder_person_id"] != founder_person}
    require(independent_holders, "F1/F2 requires independent delegated role holder")
    validate_process_evidence_ref(
        f1["independent_role_holder_evidence"], "F1 independent role evidence",
        "independent-role-holder-evidence", status["governance_version"])
    scopes = {scope for d in active_delegations for scope in d["scope_types"]}
    require(CRITICAL_DELEGATION_SCOPES.issubset(scopes),
            "F1/F2 requires operative treasury/domain/repository delegations")
    validate_process_evidence_ref(
        f1["delegation_evidence"], "F1 delegation evidence",
        "delegation-coverage-evidence", status["governance_version"])

    if phase == "F1-early-institution":
        return

    require(len(active_members) >= f2["minimum_active_members"], "F2 requires minimum distinct Active Members")
    require(elapsed_complete_months(effective, phase_date) >= f2["minimum_operational_months"],
            "F2 minimum operational months not satisfied")
    by_holder: dict[str, set[str]] = {}
    for delegation in active_delegations:
        by_holder.setdefault(delegation["holder_person_id"], set()).update(delegation["scope_types"])
    require(not any(CRITICAL_DELEGATION_SCOPES.issubset(scopes_) for scopes_ in by_holder.values()),
            "F2 prohibits one person controlling treasury/domain/repository")
    require(any("audit-review" in d["scope_types"] and d["holder_person_id"] != founder_person
                for d in active_delegations),
            "F2 requires independent audit/review delegation")
    for key, rtype, label in (
        ("control_separation_evidence", "control-separation-evidence", "F2 control separation"),
        ("audit_review_evidence", "audit-review-capacity-evidence", "F2 audit/review capacity"),
        ("role_replacement_evidence", "role-replacement-evidence", "F2 role replacement"),
    ):
        validate_process_evidence_ref(f2[key], label, rtype, status["governance_version"])
    require(f2["single_person_cross_domain_control_removed"] is True
            and f2["independent_audit_review_capacity"] is True
            and f2["delegated_role_replacement_demonstrated"] is True,
            "F2 maturity flags must match verified evidence")


def validate_bootstrap_or_operativity(
    status: dict,
    rules: dict,
    delegations: dict,
    membership: dict,
    founding: dict,
    phase_evidence: dict,
) -> None:
    validate_governance_artifacts(status)
    _, active_members = validate_membership_registry(membership)
    active_delegations = validate_delegations(delegations, status, rules, membership)
    activation_hashes = validate_activation_evidence(status)
    legal_entity = validate_legal_entity(status)
    phase = status["institutional_phase"]

    if status["operative"] is False:
        require(status["institutional_state"] == "bootstrap" and phase == "F0-founder-led-bootstrap",
                "non-operative governance must remain bootstrap F0")
        require(status["governing_law"] is None and status["effective_date"] is None,
                "bootstrap cannot fabricate legal activation metadata")
        require(status["adoption_record"] is None, "bootstrap cannot fabricate adoption record")
        for flag in (
            "initial_member_registry_adopted", "conflict_process_adopted",
            "records_privacy_process_adopted", "treasury_controls_adopted",
            "founding_steward_assignment_adopted", "succession_process_adopted",
            "qualified_legal_review_complete",
        ):
            require(status[flag] is False, f"bootstrap adoption flag must be false: {flag}")
        require(rules["operative"] is False and delegations["operative"] is False
                and membership["operative"] is False and founding["operative"] is False,
                "draft machine projections cannot be operative")
        require(delegations["delegations"] == [], "bootstrap cannot contain delegations")
        require(membership["registry_state"] == "bootstrap" and not active_members,
                "bootstrap cannot contain Active Members")
        require(founding["founding_steward"]["operative_assignment"] is False
                and founding["mission_guardian"]["operative_assignment"] is False
                and founding["mission_lock"]["operative"] is False,
                "bootstrap cannot fabricate operative founding authority")
        validate_phase_evidence(
            status, membership, founding, phase_evidence, active_delegations, active_members, rules)
        validate_adoption_record(status, activation_hashes, rules, membership, legal_entity)
        return

    require(status["operative"] is True, "governance operative field must be boolean")
    require(status["institutional_state"] != "bootstrap", "operative governance cannot remain bootstrap")
    require("-DRAFT" not in status["governance_version"], "operative governance_version cannot remain draft")
    require(phase in {"F0-founder-led-bootstrap", "F1-early-institution", "F2-distributed-institution"},
            "invalid operative institutional phase")
    require(isinstance(status["governing_law"], str) and status["governing_law"].strip(),
            "operative governance requires governing law")
    parse_iso_date(status["effective_date"], "governance effective_date")
    for flag in (
        "initial_member_registry_adopted", "conflict_process_adopted",
        "records_privacy_process_adopted", "treasury_controls_adopted",
        "founding_steward_assignment_adopted", "succession_process_adopted",
        "qualified_legal_review_complete",
    ):
        require(status[flag] is True, f"operative governance requires adoption flag: {flag}")
    require(rules["operative"] is True and delegations["operative"] is True
            and membership["operative"] is True and founding["operative"] is True,
            "operative governance requires aligned operative projections")
    require(membership["registry_state"] == "operative" and active_members,
            "operative governance requires Active Member registry")
    require(founding["mission_lock"]["operative"] is True, "operative governance requires operative Mission Lock")
    founder_active = founding["founding_steward"]["operative_assignment"] is True
    guardian_active = founding["mission_guardian"]["operative_assignment"] is True
    if phase in {"F0-founder-led-bootstrap", "F1-early-institution"}:
        require(founder_active or guardian_active,
                "Founding Period requires Founding Steward or successor Mission Guardian")
    else:
        require(guardian_active, "operative F2 requires adopted Mission Guardian")

    validate_phase_evidence(
        status, membership, founding, phase_evidence, active_delegations, active_members, rules)
    validate_adoption_record(status, activation_hashes, rules, membership, legal_entity)


def main() -> None:
    status = load_json("policy/governance-status.json")
    rules = load_json("policy/decision-rules.json")
    delegations = load_json("policy/delegations.json")
    membership = load_json("policy/membership-status.json")
    founding = load_json("policy/founding-stewardship.json")
    phase_evidence = load_json("policy/phase-evidence.json")
    context = load_json("ontology/commons-context.jsonld")

    require(status["schema_version"] == 5, "unsupported governance status schema")
    require(rules["schema_version"] == 3, "unsupported decision rules schema")
    require(delegations["schema_version"] == 3, "unsupported delegations schema")
    require(membership["schema_version"] == 3, "unsupported membership schema")
    require(founding["schema_version"] == 4, "unsupported founding stewardship schema")
    require(phase_evidence["schema_version"] == 2, "unsupported phase-evidence schema")
    require(status["vocabulary_namespace"] == NS and status["ontology_iri"] == ONTOLOGY_IRI,
            "governance namespace/ontology mismatch")
    require(status["phase_evidence"] == "policy/phase-evidence.json", "unexpected phase-evidence path")
    version = status["governance_version"]
    for name, obj in {
        "rules": rules, "delegations": delegations, "membership": membership,
        "founding stewardship": founding, "phase evidence": phase_evidence,
    }.items():
        require(obj["governance_version"] == version, f"status/{name} version mismatch")

    validate_bootstrap_or_operativity(status, rules, delegations, membership, founding, phase_evidence)

    by_id = rule_by_id(rules)
    require(set(by_id) == {
        "ordinary-approval", "qualified-approval",
        "constitutional-amendment", "mission-locked-amendment",
    }, "unexpected decision-rule set")
    ordinary = by_id["ordinary-approval"]
    qualified = by_id["qualified-approval"]
    constitutional = by_id["constitutional-amendment"]
    mission = by_id["mission-locked-amendment"]

    require(ordinary["iri"] == NS + "OrdinaryApproval"
            and qualified["iri"] == NS + "QualifiedApproval"
            and constitutional["iri"] == NS + "ConstitutionalAmendment"
            and mission["iri"] == NS + "MissionLockedAmendment",
            "decision-rule IRI mismatch")
    require(exact_fraction(ordinary["quorum"], 1, 2, "strictly_greater_than"),
            "ordinary quorum must be exactly >1/2")
    require(exact_fraction(qualified["quorum"], 2, 3, "at_least")
            and exact_fraction(qualified["approval"], 2, 3, "at_least"),
            "Qualified Approval must be exact 2/3")
    require(exact_fraction(constitutional["quorum"], 2, 3, "at_least")
            and exact_fraction(constitutional["approval"], 3, 4, "at_least"),
            "Constitutional Amendment thresholds changed")
    require(exact_fraction(mission["quorum"], 3, 4, "at_least")
            and exact_fraction(mission["approval"], 9, 10, "at_least"),
            "Mission Lock thresholds changed")
    for rule_id, rule in by_id.items():
        require(rule["zero_valid_for_against_result"] == "fail"
                and rule["minimum_affirmative_votes"] >= 1,
                f"{rule_id} must fail closed on zero valid votes")

    classification = mission["classification"]
    require(classification["trigger"] ==
            "any_operative_effect_alters_weakens_removes_excepts_or_bypasses_mission_lock_invariant"
            and classification["bundled_or_secondary_effects_included"] is True
            and classification["proposal_label_cannot_downgrade"] is True,
            "Mission Lock effect-based classification weakened")
    require(mission["successful_votes_required"] == 2
            and mission["minimum_days_between_successful_votes"] >= 60,
            "Mission Lock repeated-vote safeguard weakened")
    require(mission["guardian_consent_required_in_phases"] ==
            ["F0-founder-led-bootstrap", "F1-early-institution"]
            and mission["founding_period_ends_on_valid_transition_to_phase"] ==
            "F2-distributed-institution",
            "Founding Period decision rule mismatch")

    founding_period = founding["founding_period"]
    require(founding_period["applies_in_phases"] ==
            ["F0-founder-led-bootstrap", "F1-early-institution"]
            and founding_period["ends_only_on_valid_transition_to_phase"] ==
            "F2-distributed-institution"
            and founding_period["valid_transition_requires_phase_evidence"] is True
            and founding_period["founder_vacancy_does_not_end_period"] is True,
            "Founding Period boundary weakened")
    require(founding["phase_transition"]["approval_rule_must_be_explicit_in_decision_record"] is True,
            "phase transition approval-rule binding weakened")

    conflicts = rules["conflict_rules"]
    require(conflicts["self_compensation_recusal_required"] is True
            and conflicts["self_contract_approval_prohibited"] is True
            and conflicts["funding_does_not_create_governance_rights"] is True
            and conflicts["founder_status_does_not_override_conflict_recusal"] is True,
            "conflict/anti-capture invariant weakened")
    require(membership["one_person_one_vote"] is True
            and membership["natural_person_voting_members_only"] is True,
            "Membership equality rule weakened")
    seasoning = membership["voting_seasoning_days"]
    require(membership["candidate_period_days"] >= 30
            and seasoning["ordinary-approval"] >= 30
            and seasoning["qualified-approval"] >= 90
            and seasoning["constitutional-amendment"] >= 90
            and seasoning["mission-locked-amendment"] >= 180,
            "Membership anti-capture seasoning weakened")
    require(founding["phase"] == status["institutional_phase"], "founding/status phase mismatch")
    require(founding["founding_steward"]["person_id"] == "ec-person-dml-001"
            and founding["founding_steward"]["display_name"] == "Daniel Molinero Lucas",
            "unexpected draft Founding Steward identity")
    require(founding["mission_lock"]["negative_veto_only"] is True
            and founding["mission_lock"]["founder_economic_privilege"] is False,
            "founder Mission Lock/economic boundary weakened")
    require(founding["phase_transition"]["self_declared_by_founder_prohibited"] is True
            and founding["phase_transition"]["requires_decision_record"] is True
            and founding["phase_transition"]["requires_evidence_record"] is True
            and founding["phase_transition"]["evidence_policy"] == "policy/phase-evidence.json",
            "phase-transition integrity weakened")

    mandatory_qualified = set(rules["mandatory_qualified_subjects"])
    for subject in {
        "endowment-principal-withdrawal", "persistent-domain-transfer",
        "identifier-authority-transfer", "organization-wide-exclusive-ip-transfer",
        "institutional-merger-dissolution-or-succession",
    }:
        require(subject in mandatory_qualified, f"qualified-approval subject missing: {subject}")
    require(len(rules["mission_locked_subjects"]) >= 7, "Mission Lock subject set incomplete")
    require(context["@context"]["ec"] == NS, "JSON-LD namespace mismatch")

    ontology = (ROOT / "ontology/commons.ttl").read_text(encoding="utf-8")
    shapes = (ROOT / "ontology/governance-shapes.ttl").read_text(encoding="utf-8")
    machine_spec = (ROOT / "spec/MACHINE-READABLE-GOVERNANCE.md").read_text(encoding="utf-8")
    individual_cla = (ROOT / "cla/CLA-1.0-DRAFT.md").read_text(encoding="utf-8")
    entity_cla = (ROOT / "cla/ENTITY-CLA-1.0-DRAFT.md").read_text(encoding="utf-8")
    require(ONTOLOGY_IRI in ontology and "owl:propertyChainAxiom" not in ontology,
            "ontology authority boundary invalid")
    for term in (
        "OrdinaryApproval", "QualifiedApproval", "ConstitutionalAmendment",
        "MissionLockedAmendment", "Delegation", "PersistentIdentifierAuthority",
        "FoundingSteward", "MissionGuardian", "MembershipRecord",
    ):
        require(f"ec:{term}" in ontology, f"ontology term missing: {term}")
    require("ec:GovernanceDecisionShape" in shapes and "ec:MembershipRecordShape" in shapes,
            "governance SHACL shapes missing")
    require("conforming graph is not proof" in machine_spec.lower(),
            "machine/legal authority boundary missing")
    require("accepted contribution" in individual_cla.lower()
            and "accepted contribution" in entity_cla.lower()
            and "limited pre-acceptance review rights" in entity_cla.lower(),
            "CLA acceptance gate missing")

    validate_cla_status()
    print("Exergism Commons governance integrity: PASS")
    print(f"governance_version={version} operative={status['operative']} "
          f"state={status['institutional_state']} phase={status['institutional_phase']}")
    print(f"decision_rules={len(rules['rules'])} delegations={len(delegations['delegations'])} "
          f"member_records={len(membership['members'])}")


if __name__ == "__main__":
    main()
