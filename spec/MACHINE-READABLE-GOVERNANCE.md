# Machine-Readable Governance

> **Status: 0.1-DRAFT — non-operative projection.**

This specification defines how Exergism Commons organization-level governance may be represented and validated in machine-readable form without allowing code, RDF inference, repository state or automation to manufacture institutional authority.

## 1. Authority model

Human constitutional and adopted policy text remains authoritative for organization-level governance. Machine-readable artifacts are projections and enforcement aids.

```text
Constitution / adopted policy
        ↓
versioned governance rule
        ↓
JSON-LD decision / role / delegation records
        ↓
SHACL + deterministic integrity checks
        ↓
derived RDF / query views
        ↓
implementation in Funding, ID, repositories and other domains
```

A SHACL-conforming graph is not proof that a decision was legally valid. It is proof only that the encoded record satisfies the declared machine-checkable constraints.

## 2. Namespace

Organization-level terms use:

```text
ec: https://id.exergism.org/commons#
```

Ontology document IRI:

```text
https://id.exergism.org/ontology/commons
```

The namespace is separate from Exergism, ECL and Funding. Cross-domain relationships must be explicit.

## 3. Core concepts

The initial vocabulary includes:

- `GovernanceRule`
- `GovernanceDecision`
- `DecisionClass`
- `Delegation`
- `Role`
- `Member`
- `ConflictDeclaration`
- `OrdinaryApproval`
- `QualifiedApproval`
- `ConstitutionalAmendment`
- `EmergencyAction`
- `InstitutionalAsset`
- `PersistentIdentifierAuthority`

The model distinguishes a **rule** from a **decision**, a **role** from the person holding it, and a **technical capability** from institutional authority.

## 4. Bootstrap fail-closed rule

`policy/governance-status.json` is the top-level machine status record.

While `operative` is `false`:

- no decision record may declare `operative: true`;
- no delegation may declare legally operative institutional authority;
- no machine record may identify an unspecified GitHub organization as the legal entity;
- downstream domains may consume the vocabulary and proposed thresholds only as draft governance dependencies.

Transition to `operative: true` requires a separately reviewed adoption change and must not be hidden inside an unrelated refactor.

## 5. Decision rules

`policy/decision-rules.json` defines named approval classes and thresholds. Domain policies may require stricter rules but must not silently weaken a named organization-level approval class.

For vote-based rules, records should distinguish:

- total eligible voters before conflicts;
- conflicted/recused voters;
- effective eligible voters;
- quorum requirement;
- votes in favour;
- votes against;
- abstentions; and
- resulting approval state.

A beneficiary recused from their own compensation decision is excluded from the effective eligible-voter denominator under the proposed constitutional rule.

## 6. Delegations

A delegation record must identify:

- stable ID;
- delegated role/actor;
- source authority;
- exact scope;
- allowed actions;
- explicit prohibitions where material;
- effective and expiry/revocation state; and
- governing rule version.

A delegation may not grant authority that the source does not possess. Technical repository/admin access is never automatically converted into a delegation.

## 7. Cross-domain consumption

Downstream repositories may reference EC governance terms without copying their definitions.

Examples:

- Funding may state that a >50% concentration decision `requiresApprovalClass ec:QualifiedApproval`.
- The identifier service may state that permanent domain transfer `requiresApprovalClass ec:QualifiedApproval`.
- A future registry may record that a decision was `authorizedBy` a specific adopted EC decision.

The downstream repository remains authoritative for its domain facts and implementation; Governance remains authoritative for the organization-level approval concept it references.

## 8. Decision identity and immutability

A material decision should receive a stable identifier such as:

```text
https://id.exergism.org/governance/decision/{stable-id}
```

Released decision records should be content-addressable or otherwise bound to immutable bytes. Mutable current-state views may point to the latest effective decision but do not replace historical records.

## 9. SHACL boundary

SHACL should enforce structural and policy invariants that can be stated deterministically, including:

- operative decisions require operative organization governance;
- decision class must resolve to a declared rule;
- qualified decisions cannot claim approval below the declared threshold;
- self-compensation decisions require beneficiary recusal;
- persistent-domain transfer requires Qualified Approval;
- Endowment-principal withdrawal requires Qualified Approval and an exceptional-condition marker;
- funding alone cannot create governance rights; and
- a repository permission or technical credential is not sufficient evidence of a Delegation.

SHACL must not infer philosophical truth, legal validity, fiduciary status or ECL restriction from graph reachability.

## 10. Validation and CI

`tools/validate_governance.py` performs deterministic fail-closed checks over the committed JSON records and the declared vocabulary. CI runs it on changes to governance policy, machine records, ontology, specification or validator code.

The validator intentionally does not claim to perform legal review.

## 11. Versioning

Every operative machine-readable policy release must identify an exact governance version. Breaking changes to decision semantics, thresholds, identifiers or authority relationships require a new version and explicit migration analysis.

Historical decision records are not silently rewritten to conform to a later rule version.
