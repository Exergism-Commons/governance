from __future__ import annotations

from datetime import date
import validate_governance as core

REVOCATION_EFFECTIVE_DATES: dict[str, date] = {}


def _rule_ids(rules: dict) -> set[str]:
    items = rules.get("rules")
    core.require(isinstance(items, list), "decision rules list required for delegation lifecycle")
    return {item.get("id") for item in items if isinstance(item, dict) and isinstance(item.get("id"), str)}


def _event_authority(status: dict, rules: dict, membership: dict, decision_date: date, label: str) -> tuple[dict, dict, dict]:
    """Resolve the governance authority that was operative for one delegation event."""
    if status.get("operative") is not True:
        return status, rules, membership

    # Imported lazily to avoid turning delegation lifecycle import order into a
    # module cycle in the canonical temporal entry point.
    import governance_release_authority as release_authority

    event_status, event_rules, _, _ = release_authority.authority_context_as_of(status, decision_date)
    event_membership = release_authority.membership_context_as_of(status, membership, decision_date)
    core.require(
        event_membership.get("governance_version") == event_status.get("governance_version"),
        f"{label} membership authority version mismatch",
    )
    return event_status, event_rules, event_membership


def _base_required_fields() -> set[str]:
    return {
        "delegation_id", "holder_person_id", "source_authority", "scope_types", "scope_resources",
        "allowed_actions", "prohibited_actions", "governing_rule_version", "effective_date", "expires_at",
        "revocation", "operative", "decision_record", "revocation_record",
    }


def _grant_payload(item: dict) -> dict:
    payload = {k: v for k, v in item.items() if k not in {"decision_record", "revocation_record"}}
    # A revocation cannot rewrite the immutable grant that created the delegation.
    payload["operative"] = True
    return payload


def _validate_creation(item: dict, delegations: dict, status: dict, rules: dict, membership: dict) -> tuple[date, str]:
    delegation_id = item["delegation_id"]
    holder = item["holder_person_id"]
    core.require(isinstance(holder, str) and holder, f"delegation {delegation_id} holder required")
    scopes = item["scope_types"]
    core.require(isinstance(scopes, list) and scopes and len(scopes) == len(set(scopes)), f"delegation {delegation_id} scopes invalid")
    core.require(set(scopes).issubset(set(delegations["scope_vocabulary"])), f"delegation {delegation_id} unknown scope")
    resources = item["scope_resources"]
    core.require(isinstance(resources, dict) and set(resources) == set(scopes), f"delegation {delegation_id} scope_resources must cover exact scopes")
    for scope, vals in resources.items():
        core.require(isinstance(vals, list) and vals and all(isinstance(v, str) and v.strip() for v in vals), f"delegation {delegation_id} resources invalid for {scope}")

    allowed, prohibited = item["allowed_actions"], item["prohibited_actions"]
    reserved = set(delegations.get("reserved_non_delegable_actions", []))
    core.require(isinstance(allowed, list) and allowed and len(allowed) == len(set(allowed)), f"delegation {delegation_id} allowed_actions invalid")
    core.require(isinstance(prohibited, list) and prohibited and len(prohibited) == len(set(prohibited)), f"delegation {delegation_id} prohibited_actions invalid")
    core.require(not reserved.intersection(allowed), f"delegation {delegation_id} grants reserved action")
    core.require(reserved.issubset(set(prohibited)), f"delegation {delegation_id} must explicitly prohibit reserved actions")

    effective = core.parse_iso_date(item["effective_date"], f"delegation {delegation_id}.effective_date")
    if item["expires_at"] is not None:
        core.require(core.parse_iso_date(item["expires_at"], f"delegation {delegation_id}.expires_at") >= effective, f"delegation {delegation_id} expires before effective date")

    decision, _ = core.validate_content_ref(item["decision_record"], f"delegation decision {delegation_id}", "records/decisions")
    core.require(decision.get("record_type") == "delegation-decision" and decision.get("status") == "adopted", f"delegation decision invalid: {delegation_id}")
    decision_id, decision_class, decision_date_text = decision.get("decision_id"), decision.get("decision_class"), decision.get("decision_date")
    core.require(isinstance(decision_id, str) and decision_id, f"delegation decision_id required: {delegation_id}")
    core.require(decision_class in {"ordinary-approval", "qualified-approval"}, f"delegation decision class invalid: {delegation_id}")
    decision_date = core.parse_iso_date(decision_date_text, f"delegation {delegation_id}.decision_date")
    core.require(decision_date <= effective, f"delegation decision occurs after effective date: {delegation_id}")

    event_status, event_rules, _ = _event_authority(
        status,
        rules,
        membership,
        decision_date,
        f"delegation creation {delegation_id}",
    )
    event_version = event_status["governance_version"]
    core.require(item["governing_rule_version"] == event_version, f"delegation {delegation_id} governing rule mismatch")
    core.require(decision.get("governance_version") == event_version, f"delegation decision version mismatch: {delegation_id}")
    core.require(decision_class in _rule_ids(event_rules), f"delegation decision rule unavailable at creation: {delegation_id}")
    if status.get("operative") is True:
        event_effective = core.parse_iso_date(event_status["effective_date"], f"delegation {delegation_id} authority release effective_date")
        core.require(event_effective <= decision_date <= effective, f"delegation {delegation_id} creation chronology crosses its authority boundary")

    revocation = item["revocation"]
    core.require(
        isinstance(revocation, dict)
        and set(revocation) == {"revocable", "mechanism", "authority"}
        and revocation.get("revocable") is True
        and isinstance(revocation.get("mechanism"), str)
        and revocation["mechanism"].strip()
        and revocation.get("authority") in _rule_ids(event_rules),
        f"delegation {delegation_id} revocation contract invalid under creation release",
    )

    for field in (
        "delegation_id", "holder_person_id", "source_authority", "scope_types", "scope_resources",
        "allowed_actions", "prohibited_actions", "governing_rule_version", "effective_date", "expires_at", "revocation",
    ):
        core.require(decision.get(field) == item[field], f"delegation decision field mismatch: {delegation_id}.{field}")

    source = item["source_authority"]
    core.require(isinstance(source, dict) and set(source) == {"type", "decision_id", "constitutional_basis"}, f"delegation {delegation_id} source authority shape invalid")
    core.require(source == {"type": "governance-decision", "decision_id": decision_id, "constitutional_basis": core.RESERVED_CONSTITUTIONAL_BASIS}, f"delegation {delegation_id} source authority does not resolve to creating decision")

    grant_hash = core.sha256_json(_grant_payload(item))
    core.require(decision.get("delegation_payload_sha256") == grant_hash, f"delegation decision payload hash mismatch: {delegation_id}")
    # The installed approval validator independently resolves the release in
    # force on decision_date and reconstructs that release's electorate/policy.
    core.validate_approval_evidence(
        decision.get("approval_evidence"),
        f"delegation approval {delegation_id}",
        decision_id,
        status,
        rules,
        membership,
        expected_rule_id=decision_class,
        expected_artifact_bindings={"delegation_payload_sha256": grant_hash},
        expected_decision_date=decision_date_text,
    )
    return effective, grant_hash


def _validate_revocation(item: dict, effective: date, grant_hash: str, status: dict, rules: dict, membership: dict) -> date:
    delegation_id = item["delegation_id"]
    record, _ = core.validate_content_ref(item.get("revocation_record"), f"delegation revocation {delegation_id}", "records/decisions")
    required = {
        "record_type", "status", "governance_version", "delegation_id", "decision_id", "decision_class",
        "decision_date", "effective_date", "reason", "delegation_payload_sha256", "revocation_payload_sha256", "approval_evidence",
    }
    core.require(set(record) == required, f"delegation revocation {delegation_id} fields incomplete/unexpected")
    core.require(record["record_type"] == "delegation-revocation" and record["status"] == "adopted", f"delegation revocation invalid: {delegation_id}")
    core.require(record["delegation_id"] == delegation_id, f"delegation revocation identity mismatch: {delegation_id}")
    core.require(record["delegation_payload_sha256"] == grant_hash, f"delegation revocation does not bind immutable grant: {delegation_id}")

    decision_id, decision_class = record["decision_id"], record["decision_class"]
    core.require(isinstance(decision_id, str) and decision_id, f"delegation revocation decision_id required: {delegation_id}")
    decision_date_text = record["decision_date"]
    decision_date = core.parse_iso_date(decision_date_text, f"delegation revocation {delegation_id}.decision_date")
    revoked_effective = core.parse_iso_date(record["effective_date"], f"delegation revocation {delegation_id}.effective_date")
    core.require(effective <= decision_date <= revoked_effective, f"delegation revocation chronology invalid: {delegation_id}")

    event_status, event_rules, _ = _event_authority(
        status,
        rules,
        membership,
        decision_date,
        f"delegation revocation {delegation_id}",
    )
    event_version = event_status["governance_version"]
    core.require(record["governance_version"] == event_version, f"delegation revocation governance version mismatch: {delegation_id}")
    core.require(decision_class == item["revocation"]["authority"], f"delegation revocation authority mismatch: {delegation_id}")
    core.require(decision_class in _rule_ids(event_rules), f"delegation revocation rule unavailable on decision date: {delegation_id}")
    if status.get("operative") is True:
        event_effective = core.parse_iso_date(event_status["effective_date"], f"delegation revocation {delegation_id} authority release effective_date")
        core.require(event_effective <= decision_date, f"delegation revocation {delegation_id} predates its authority release")

    if item["expires_at"] is not None:
        expiry = core.parse_iso_date(item["expires_at"], f"delegation {delegation_id}.expires_at")
        core.require(revoked_effective <= expiry, f"delegation revocation effective date occurs after natural expiry: {delegation_id}")
    core.require(isinstance(record["reason"], str) and record["reason"].strip(), f"delegation revocation reason required: {delegation_id}")

    payload = {k: v for k, v in record.items() if k not in {"approval_evidence", "revocation_payload_sha256"}}
    payload_hash = core.sha256_json(payload)
    core.require(record["revocation_payload_sha256"] == payload_hash, f"delegation revocation payload hash mismatch: {delegation_id}")
    core.validate_approval_evidence(
        record["approval_evidence"],
        f"delegation revocation approval {delegation_id}",
        decision_id,
        status,
        rules,
        membership,
        expected_rule_id=decision_class,
        expected_artifact_bindings={
            "revocation_payload_sha256": payload_hash,
            "delegation_payload_sha256": grant_hash,
        },
        expected_decision_date=decision_date_text,
    )
    return revoked_effective


def validate_delegations(delegations: dict, status: dict, rules: dict, membership: dict) -> list[dict]:
    core.require(delegations["schema_version"] == 4, "unsupported delegations schema")
    core.require(core.CRITICAL_DELEGATION_SCOPES.issubset(set(delegations.get("scope_vocabulary", []))), "delegation scope vocabulary missing critical scopes")
    core.require(
        delegations.get("source_authority_contract") == {
            "type": "governance-decision",
            "required_fields": ["type", "decision_id", "constitutional_basis"],
            "constitutional_basis": core.RESERVED_CONSTITUTIONAL_BASIS,
        },
        "delegation source-authority contract mismatch",
    )
    core.require(
        delegations.get("lifecycle_contract") == {
            "content_addressed_revocation_required": True,
            "registry_edit_alone_cannot_deactivate": True,
            "historical_effective_period_must_be_reconstructable": True,
            "revoked_delegations_remain_in_registry": True,
            "creation_validated_under_release_in_force_on_decision_date": True,
            "revocation_validated_under_release_in_force_on_decision_date": True,
            "governing_rule_version_is_creation_release": True,
        },
        "delegation lifecycle contract missing/weakened",
    )
    items = delegations.get("delegations")
    core.require(isinstance(items, list), "delegations must be a list")

    REVOCATION_EFFECTIVE_DATES.clear()
    ids, validated, required = set(), [], _base_required_fields()
    for item in items:
        core.require(isinstance(item, dict), "delegation row must be an object")
        delegation_id = item.get("delegation_id")
        core.require(isinstance(delegation_id, str) and delegation_id and delegation_id not in ids, "delegation_id required/unique")
        ids.add(delegation_id)
        core.require(set(item) == required, f"delegation {delegation_id} fields incomplete/unexpected")
        effective, grant_hash = _validate_creation(item, delegations, status, rules, membership)
        if item["operative"] is True:
            core.require(item["revocation_record"] is None, f"operative delegation {delegation_id} cannot claim revocation record")
        else:
            core.require(item["operative"] is False, f"delegation {delegation_id} operative must be boolean")
            REVOCATION_EFFECTIVE_DATES[delegation_id] = _validate_revocation(item, effective, grant_hash, status, rules, membership)
        validated.append(item)
    return validated


def delegation_active_on(item: dict, target: date) -> bool:
    start = core.parse_iso_date(item["effective_date"], f"delegation {item['delegation_id']}.effective_date")
    if target < start:
        return False
    if item.get("expires_at") is not None:
        expiry = core.parse_iso_date(item["expires_at"], f"delegation {item['delegation_id']}.expires_at")
        if target > expiry:
            return False
    revoked = REVOCATION_EFFECTIVE_DATES.get(item["delegation_id"])
    return revoked is None or target < revoked
