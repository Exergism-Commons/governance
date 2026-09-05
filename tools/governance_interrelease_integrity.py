from __future__ import annotations

import copy
import json
import os
import subprocess
from datetime import date
from pathlib import Path

import governance_adoption_chronology as adoption_chronology
import governance_delegation_lifecycle as delegation_lifecycle
import governance_release_history as release_history
import governance_release_proof as release_proof
import validate_governance as core


INTERRELEASE_AUTHORITY_CONTRACT = {
    "membership_records_repository_wide_and_append_only": True,
    "membership_registry_provenance_append_only": True,
    "delegation_policy_snapshot_bound_in_every_release": True,
    "delegation_creation_validated_against_creation_release_policy": True,
    "current_delegation_policy_matches_current_release_snapshot": True,
    "later_release_effective_date_strictly_after_completed_date": True,
}

MEMBERSHIP_HISTORY_CONTRACT = {
    "adopted_membership_records_discovered_repository_wide": True,
    "orphan_admission_or_transition_records_prohibited": True,
    "established_member_rows_cannot_be_pruned": True,
    "established_admission_provenance_is_immutable": True,
    "state_transition_history_is_append_only": True,
    "committed_content_addressed_records_are_append_only": True,
}

DELEGATION_INTERRELEASE_CONTRACT = {
    "policy_snapshot_bound_in_every_governance_release": True,
    "creation_uses_policy_snapshot_of_release_in_force": True,
    "retained_grant_bytes_never_rewritten_for_later_policy": True,
    "current_projection_matches_current_release_policy_snapshot": True,
    "later_policy_changes_apply_prospectively_without_reversioning_history": True,
}

DELEGATION_POLICY_SNAPSHOT_FIELDS = {
    "record_type",
    "status",
    "release_sequence",
    "governance_version",
    "source_authority_contract",
    "scope_vocabulary",
    "reserved_non_delegable_actions",
}

BASELINE_DELEGATION_SCOPES = {"treasury", "domain", "repository", "audit-review", "other"}
BASELINE_RESERVED_ACTIONS = {
    "constitutional-amendment",
    "membership-economic-distribution",
    "organization-wide-exclusive-ip-transfer",
    "endowment-principal-withdrawal-without-qualified-approval",
    "persistent-domain-transfer-without-qualified-approval",
    "identifier-authority-transfer-without-qualified-approval",
}

ORIG_VALIDATE_RELEASE_PROOF_CHAIN = release_proof.validate_release_proof_chain
ORIG_REQUIRE_ADOPTION_CHRONOLOGY = release_proof._require_adoption_chronology
ORIG_VALIDATE_DELEGATIONS = delegation_lifecycle.validate_delegations
ORIG_VALIDATE_DELEGATION_CREATION = delegation_lifecycle._validate_creation
ORIG_VALIDATE_ADOPTION_CHRONOLOGY = adoption_chronology.validate_governance_adoption_chronology

_INSTALLED = False


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        core.require(key not in result, f"duplicate JSON object name in repository history: {key}")
        result[key] = value
    return result


def _strict_json_text(text: str, label: str) -> dict:
    try:
        value = json.loads(text, object_pairs_hook=_strict_object)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"governance integrity failure: {label} must be valid JSON") from exc
    core.require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def _require_interrelease_contract(status: dict) -> None:
    core.require(
        status.get("interrelease_authority_contract") == INTERRELEASE_AUTHORITY_CONTRACT,
        "inter-release authority contract missing/weakened",
    )


def _require_membership_history_contract(membership: dict) -> None:
    core.require(
        membership.get("registry_history_contract") == MEMBERSHIP_HISTORY_CONTRACT,
        "membership registry-history contract missing/weakened",
    )


def _require_delegation_interrelease_contract(delegations: dict) -> None:
    core.require(
        delegations.get("interrelease_policy_contract") == DELEGATION_INTERRELEASE_CONTRACT,
        "delegation inter-release policy contract missing/weakened",
    )


def _exact_ref(path: Path) -> dict:
    return {
        "path": path.relative_to(core.ROOT).as_posix(),
        "sha256": core.sha256_file(path),
    }


def discover_membership_records() -> tuple[list[tuple[str, dict]], list[tuple[str, dict]]]:
    """Discover every adopted membership event in the canonical decision tree.

    Release checkpoints are not enough for the interval between releases. The
    repository therefore treats adopted admission/transition records as an
    append-only event corpus and requires the mutable Member Registry to retain
    an exact reference to every discovered event.
    """
    root = core.ROOT / "records" / "decisions"
    if not root.is_dir():
        return [], []

    admissions: list[tuple[str, dict]] = []
    transitions: list[tuple[str, dict]] = []
    for path in sorted(root.rglob("*.json")):
        relative = path.relative_to(core.ROOT).as_posix()
        data = core.load_json(relative)
        record_type = data.get("record_type")
        if data.get("status") != "adopted":
            continue
        if record_type not in {"membership-admission", "membership-state-transition"}:
            continue
        person_id = data.get("person_id")
        core.require(isinstance(person_id, str) and person_id.strip(), f"membership record person_id missing: {relative}")
        target = admissions if record_type == "membership-admission" else transitions
        target.append((person_id, _exact_ref(path)))
    return admissions, transitions


def _validate_membership_record_closure_sets(
    membership: dict,
    admissions: list[tuple[str, dict]],
    transitions: list[tuple[str, dict]],
    label: str,
) -> None:
    members = membership.get("members")
    core.require(isinstance(members, list), f"{label} members must be a list")
    by_person: dict[str, dict] = {}
    for index, item in enumerate(members):
        core.require(isinstance(item, dict), f"{label} member {index} must be an object")
        person_id = item.get("person_id")
        core.require(isinstance(person_id, str) and person_id and person_id not in by_person, f"{label} member identity invalid/duplicate")
        by_person[person_id] = item

    discovered_admissions = {(person_id, ref["path"], ref["sha256"]) for person_id, ref in admissions}
    discovered_transitions = {(person_id, ref["path"], ref["sha256"]) for person_id, ref in transitions}
    core.require(len(discovered_admissions) == len(admissions), f"{label} duplicate adopted membership-admission record")
    core.require(len(discovered_transitions) == len(transitions), f"{label} duplicate adopted membership-state-transition record")

    for person_id, ref in admissions:
        member = by_person.get(person_id)
        core.require(member is not None, f"{label} orphan adopted membership admission: {person_id}")
        core.require(member.get("admission_record") == ref, f"{label} admission record is not retained exactly for {person_id}")

    for person_id, ref in transitions:
        member = by_person.get(person_id)
        core.require(member is not None, f"{label} orphan adopted membership transition: {person_id}")
        refs = member.get("state_transition_records")
        core.require(isinstance(refs, list) and ref in refs, f"{label} transition record is not retained exactly for {person_id}")

    for person_id, member in by_person.items():
        admission_ref = member.get("admission_record")
        admission_mode = member.get("admission_mode")
        if isinstance(admission_ref, dict) and admission_mode != "constitutive-initial-member":
            key = (person_id, admission_ref.get("path"), admission_ref.get("sha256"))
            core.require(key in discovered_admissions, f"{label} registry references undiscovered admission record for {person_id}")
        transition_refs = member.get("state_transition_records")
        core.require(isinstance(transition_refs, list), f"{label} transition history must be a list for {person_id}")
        for ref in transition_refs:
            core.require(isinstance(ref, dict), f"{label} transition reference invalid for {person_id}")
            key = (person_id, ref.get("path"), ref.get("sha256"))
            core.require(key in discovered_transitions, f"{label} registry references undiscovered transition record for {person_id}")


def validate_membership_record_closure(membership: dict, label: str = "membership registry") -> None:
    _require_membership_history_contract(membership)
    admissions, transitions = discover_membership_records()
    _validate_membership_record_closure_sets(membership, admissions, transitions, label)


def _validate_delegation_policy_snapshot_data(snapshot: dict, adoption: dict, label: str) -> dict:
    core.require(set(snapshot) == DELEGATION_POLICY_SNAPSHOT_FIELDS, f"{label} delegation-policy snapshot fields incomplete/unexpected")
    core.require(
        snapshot.get("record_type") == "governance-delegation-policy-snapshot" and snapshot.get("status") == "final",
        f"{label} delegation-policy snapshot type/status invalid",
    )
    core.require(snapshot.get("release_sequence") == adoption.get("release_sequence"), f"{label} delegation-policy release sequence mismatch")
    core.require(snapshot.get("governance_version") == adoption.get("governance_version"), f"{label} delegation-policy governance version mismatch")
    expected_source = {
        "type": "governance-decision",
        "required_fields": ["type", "decision_id", "constitutional_basis"],
        "constitutional_basis": core.RESERVED_CONSTITUTIONAL_BASIS,
    }
    core.require(snapshot.get("source_authority_contract") == expected_source, f"{label} delegation source-authority contract weakened")
    scopes = snapshot.get("scope_vocabulary")
    reserved = snapshot.get("reserved_non_delegable_actions")
    core.require(
        isinstance(scopes, list)
        and len(scopes) == len(set(scopes))
        and BASELINE_DELEGATION_SCOPES.issubset(set(scopes)),
        f"{label} delegation scope vocabulary invalid/weakened",
    )
    core.require(
        isinstance(reserved, list)
        and len(reserved) == len(set(reserved))
        and BASELINE_RESERVED_ACTIONS.issubset(set(reserved)),
        f"{label} reserved delegation action set invalid/weakened",
    )
    return snapshot


def validate_delegation_policy_snapshot(adoption: dict, label: str) -> dict:
    ref = adoption.get("delegation_policy_snapshot")
    core.require(
        isinstance(ref, dict) and set(ref) == {"path", "sha256"},
        f"{label} must bind a content-addressed delegation_policy_snapshot",
    )
    snapshot, _ = core.validate_content_ref(ref, f"{label} delegation policy snapshot", "records/snapshots")
    return _validate_delegation_policy_snapshot_data(snapshot, adoption, label)


def _validate_current_delegation_projection(status: dict, delegations: dict) -> None:
    if status.get("operative") is not True:
        return
    chain = release_history.release_chain(status)
    core.require(chain, "operative governance requires release chain for delegation policy")
    current, _ = chain[-1]
    snapshot = validate_delegation_policy_snapshot(current, "current governance release")
    core.require(delegations.get("scope_vocabulary") == snapshot["scope_vocabulary"], "current delegation scope vocabulary diverges from current release snapshot")
    core.require(
        delegations.get("reserved_non_delegable_actions") == snapshot["reserved_non_delegable_actions"],
        "current reserved delegation actions diverge from current release snapshot",
    )
    core.require(
        delegations.get("source_authority_contract") == snapshot["source_authority_contract"],
        "current delegation source-authority contract diverges from current release snapshot",
    )


def validate_delegation_creation(item: dict, delegations: dict, status: dict, rules: dict, membership: dict):
    if status.get("operative") is not True:
        return ORIG_VALIDATE_DELEGATION_CREATION(item, delegations, status, rules, membership)

    decision, _ = core.validate_content_ref(item.get("decision_record"), "delegation creation authority preflight", "records/decisions")
    decision_date = core.parse_iso_date(decision.get("decision_date"), "delegation creation authority decision_date")
    adoption, _ = release_history.release_as_of(status, decision_date)
    snapshot = validate_delegation_policy_snapshot(
        adoption,
        f"delegation {item.get('delegation_id')} creation release #{adoption.get('release_sequence')}",
    )
    event_policy = copy.deepcopy(delegations)
    event_policy["scope_vocabulary"] = copy.deepcopy(snapshot["scope_vocabulary"])
    event_policy["reserved_non_delegable_actions"] = copy.deepcopy(snapshot["reserved_non_delegable_actions"])
    event_policy["source_authority_contract"] = copy.deepcopy(snapshot["source_authority_contract"])
    return ORIG_VALIDATE_DELEGATION_CREATION(item, event_policy, status, rules, membership)


def validate_delegations(delegations: dict, status: dict, rules: dict, membership: dict):
    _require_delegation_interrelease_contract(delegations)
    _validate_current_delegation_projection(status, delegations)
    return ORIG_VALIDATE_DELEGATIONS(delegations, status, rules, membership)


def _require_adoption_chronology(record: dict, approval: dict, label: str):
    decision, completed, effective = ORIG_REQUIRE_ADOPTION_CHRONOLOGY(record, approval, label)
    sequence = record.get("release_sequence")
    if isinstance(sequence, int) and sequence >= 2:
        core.require(
            completed < effective,
            f"{label} amendment effective_date must be strictly after adoption completion to avoid same-day authority ambiguity",
        )
    return decision, completed, effective


def validate_governance_adoption_chronology(status: dict) -> None:
    ORIG_VALIDATE_ADOPTION_CHRONOLOGY(status)
    _require_interrelease_contract(status)
    if status.get("operative") is not True:
        return
    contract = status.get("governance_release_contract")
    if not isinstance(contract, dict) or not isinstance(contract.get("current_release_sequence"), int):
        return
    if contract["current_release_sequence"] < 2:
        return
    adoption, _ = core.validate_content_ref(status.get("adoption_record"), "current amendment chronology", "records/adoptions")
    completed = core.parse_iso_date(adoption.get("completed_date"), "current amendment completed_date")
    effective = core.parse_iso_date(adoption.get("effective_date"), "current amendment effective_date")
    core.require(
        completed < effective,
        "later governance release effective_date must be strictly after completed_date",
    )


def validate_release_proof_chain(status: dict, membership: dict) -> None:
    _require_interrelease_contract(status)
    _require_membership_history_contract(membership)
    if status.get("operative") is True:
        validate_membership_record_closure(membership, "operative membership registry")
        chain = release_history.release_chain(status)
        for adoption, _ in chain:
            validate_delegation_policy_snapshot(
                adoption,
                f"governance release #{adoption.get('release_sequence')}",
            )
    ORIG_VALIDATE_RELEASE_PROOF_CHAIN(status, membership)


def _git(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=core.ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=check,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        if isinstance(exc, subprocess.CalledProcessError):
            detail = exc.stderr.strip() or exc.stdout.strip()
        else:
            detail = str(exc)
        raise SystemExit(f"governance integrity failure: repository-history git command failed: {detail}") from exc


def _git_show_json(base: str, path: str) -> dict | None:
    probe = _git(["cat-file", "-e", f"{base}:{path}"], check=False)
    if probe.returncode != 0:
        return None
    shown = _git(["show", f"{base}:{path}"])
    return _strict_json_text(shown.stdout, f"historical {path}")


def _validate_membership_registry_extension(previous: dict, current: dict) -> None:
    previous_members = previous.get("members")
    current_members = current.get("members")
    core.require(isinstance(previous_members, list) and isinstance(current_members, list), "membership history comparison requires member lists")
    current_by_person = {
        item.get("person_id"): item
        for item in current_members
        if isinstance(item, dict) and isinstance(item.get("person_id"), str)
    }
    for old in previous_members:
        if not isinstance(old, dict):
            continue
        person_id = old.get("person_id")
        established = (
            old.get("active_since") is not None
            or isinstance(old.get("admission_record"), dict)
            or old.get("admission_mode") in {"constitutive-initial-member", "f0-founding-steward-admission", "member-ordinary-approval"}
        )
        if not established:
            continue
        new = current_by_person.get(person_id)
        core.require(new is not None, f"established Member row pruned from repository history: {person_id}")
        for field in ("record_id", "person_id", "candidate_since", "active_since", "admission_mode", "admission_record"):
            core.require(new.get(field) == old.get(field), f"established Member provenance rewritten: {person_id}.{field}")
        old_transitions = old.get("state_transition_records")
        new_transitions = new.get("state_transition_records")
        core.require(isinstance(old_transitions, list) and isinstance(new_transitions, list), f"Member transition history invalid: {person_id}")
        core.require(
            new_transitions[: len(old_transitions)] == old_transitions,
            f"Member transition history is not append-only: {person_id}",
        )


def validate_repository_history() -> None:
    status = _strict_json_text((core.ROOT / "policy/governance-status.json").read_text(encoding="utf-8"), "policy/governance-status.json")
    membership = _strict_json_text((core.ROOT / "policy/membership-status.json").read_text(encoding="utf-8"), "policy/membership-status.json")
    delegations = _strict_json_text((core.ROOT / "policy/delegations.json").read_text(encoding="utf-8"), "policy/delegations.json")
    _require_interrelease_contract(status)
    _require_membership_history_contract(membership)
    _require_delegation_interrelease_contract(delegations)

    base = os.environ.get("EC_GOVERNANCE_HISTORY_BASE", "").strip()
    if not base or set(base) <= {"0"}:
        core.require(status.get("operative") is not True, "operative governance requires an explicit repository-history base")
        return

    core.require(_git(["cat-file", "-e", f"{base}^{{commit}}"], check=False).returncode == 0, "repository-history base commit is unavailable")

    diff = _git(["diff", "--name-status", "--find-renames", base, "HEAD", "--", "records/"])
    for raw in diff.stdout.splitlines():
        if not raw.strip():
            continue
        status_code = raw.split("\t", 1)[0]
        core.require(
            status_code == "A",
            f"committed content-addressed records are append-only; forbidden records/** change: {raw}",
        )

    previous_membership = _git_show_json(base, "policy/membership-status.json")
    if previous_membership is not None:
        _validate_membership_registry_extension(previous_membership, membership)


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    release_proof.validate_release_proof_chain = validate_release_proof_chain
    release_proof._require_adoption_chronology = _require_adoption_chronology
    delegation_lifecycle._validate_creation = validate_delegation_creation
    delegation_lifecycle.validate_delegations = validate_delegations
    adoption_chronology.validate_governance_adoption_chronology = validate_governance_adoption_chronology
    _INSTALLED = True
