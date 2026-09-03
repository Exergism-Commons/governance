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
Membership / Founding Stewardship / Delegation state
        ↓
GovernanceDecision records
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
- `MembershipRecord`
- `FoundingSteward`
- `MissionGuardian`
- `MissionLock`
- `FoundingPhase`
- `ConflictDeclaration`
- `OrdinaryApproval`
- `QualifiedApproval`
- `ConstitutionalAmendment`
- `MissionLockedAmendment`
- `EmergencyAction`
- `InstitutionalAsset`
- `PersistentIdentifierAuthority`

The model distinguishes a **rule** from a **decision**, a **role** from the person holding it, a **Member** from repository or funding status, and a **technical capability** from institutional authority.

## 4. Bootstrap fail-closed rule

`policy/governance-status.json` is the top-level machine status record.

While `operative` is `false`:

- institutional state must remain `bootstrap`;
- the phase projection remains `F0-founder-led-bootstrap`;
- legal entity, governing law, effective date and adoption record remain unset;
- adoption-completion flags remain false;
- decision rules, delegations, Membership and Founding Steward assignments remain non-operative;
- no Member projection may claim operative voting authority;
- no decision record may declare `operative: true`; and
- downstream domains may consume the vocabulary and proposed thresholds only as draft governance dependencies.

Transition to `operative: true` requires a separately reviewed adoption change. The validator has an explicit operative branch and must reject activation unless legal/adoption metadata and aligned operative projections are present.

Changing only the `operative` boolean is therefore insufficient by design.

## 5. Decision rules and exact arithmetic

`policy/decision-rules.json` defines named approval classes and thresholds. Domain policies may require stricter rules but must not silently weaken a named organization-level approval class.

Thresholds are represented as exact integer ratios rather than rounded floating-point values. A two-thirds threshold is encoded as numerator `2`, denominator `3`, not as an approximate decimal.

The draft classes are:

- Ordinary Approval: quorum `> 1/2`; more votes for than against;
- Qualified Approval: quorum `>= 2/3`; approval `>= 2/3`;
- Constitutional Amendment: quorum `>= 2/3`; approval `>= 3/4`;
- Mission-Locked Amendment: quorum `>= 3/4`; approval `>= 9/10`, two successful votes separated by at least 60 days plus Founding Period guardian consent and independent review.

For vote-based rules, records should distinguish:

- total eligible voters before conflicts;
- conflicted/recused voters;
- effective eligible voters;
- voting-class seasoning eligibility;
- quorum requirement;
- votes in favour;
- votes against;
- abstentions; and
- resulting approval state.

A beneficiary recused from their own compensation decision is excluded from the effective eligible-voter denominator under the proposed constitutional rule. Founder status does not override this recusal.

## 6. Membership projection

`policy/membership-status.json` is a repository-safe projection of the Member Registry design.

The canonical operative registry may contain private identity evidence outside public Git. Public projections should expose only stable record IDs, membership state, effective/eligibility dates and public role references needed for audit.

Automation must **not** infer membership from:

- GitHub organization membership;
- repository collaboration or permissions;
- CLA signature;
- employment or contracting;
- donations or grants;
- contribution count; or
- RDF graph connectivity.

The draft registry enforces one-person-one-vote and natural-person voting membership.

Voting seasoning is represented by decision class so recently admitted Members cannot immediately control protected decisions.

## 7. Founding Stewardship projection

`policy/founding-stewardship.json` records the draft founder-led phase, Founding Steward identity, Mission Lock properties and maturity-transition constraints.

The projection deliberately separates:

- an ordinary Member vote;
- founder executive authority during F0;
- negative Mission Veto authority; and
- future Mission Guardian authority.

This prevents founder authority from appearing as an undocumented weighted vote.

The machine layer must preserve at least these invariants:

- Mission Veto is negative-only;
- Founding status creates no automatic economic privilege;
- phase transition cannot be self-declared by the founder alone; and
- a JSON phase string is not sufficient evidence that maturity criteria were met.

## 8. Delegations

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

## 9. Cross-domain consumption

Downstream repositories may reference EC governance terms without copying their definitions.

Examples:

- Funding may state that a >50% concentration decision `requiresApprovalClass ec:QualifiedApproval`.
- The identifier service may state that permanent domain transfer `requiresApprovalClass ec:QualifiedApproval`.
- A future registry may record that a decision was `authorizedBy` a specific adopted EC decision.

The downstream repository remains authoritative for its domain facts and implementation; Governance remains authoritative for the organization-level approval concept it references.

## 10. Decision identity and immutability

A material decision should receive a stable identifier such as:

```text
https://id.exergism.org/governance/decision/{stable-id}
```

Released decision records should be content-addressable or otherwise bound to immutable bytes. Mutable current-state views may point to the latest effective decision but do not replace historical records.

A Mission Veto or Mission Guardian concurrence required by the governing rule should be represented explicitly rather than inferred from the identity of a committer or merger.

## 11. SHACL boundary

SHACL should enforce structural and policy invariants that can be stated deterministically, including:

- operative decisions require operative organization governance;
- decision class must resolve to a declared rule;
- membership records have stable IDs and explicit operative state;
- qualified decisions cannot claim approval below the declared threshold;
- self-compensation decisions require beneficiary recusal;
- persistent-domain transfer requires Qualified Approval;
- Endowment-principal withdrawal requires Qualified Approval and an exceptional-condition marker;
- funding alone cannot create governance rights; and
- repository permission or technical credential is not sufficient evidence of Membership, Founding Stewardship or Delegation.

SHACL must not infer philosophical truth, legal validity, fiduciary status, membership or ECL restriction from graph reachability.

## 12. CLA activation boundary

The governance integrity workflow also checks `policy/cla-status.yaml` because a fail-closed institutional control plane must not allow the CLA to become `operative: true` while its own activation blockers remain unresolved.

An operative CLA projection must include a competent legal Steward, governing law, effective date, privacy/records policy, at least one accepted signature method, completed legal review with review records, a non-draft agreement/schedule version and no remaining activation blockers.

This remains an integrity check, not legal advice or legal review.

## 13. Validation and CI

`tools/validate_governance.py` performs deterministic fail-closed checks over committed governance, Membership, Founding Stewardship, CLA-status and ontology artifacts.

CI runs it on changes to constitutional policy, founding/membership policy, CLA material, machine records, ontology, specifications or validator code.

The validator intentionally does not claim to perform legal review.

## 14. Versioning

Every operative machine-readable policy release must identify an exact governance version. Breaking changes to decision semantics, thresholds, membership eligibility, Mission Lock, identifiers or authority relationships require a new version and explicit migration analysis.

Historical decision, membership and contribution-rights records are not silently rewritten to conform to a later rule version.
