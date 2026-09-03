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
content-addressed evidence + signatures where required
        ↓
SHACL + deterministic integrity checks
        ↓
derived RDF / query views
        ↓
implementation in Funding, ID, repositories and other domains
```

A SHACL-conforming graph is not proof that a decision was legally valid. It is proof only that the encoded record satisfies the declared machine-checkable constraints.

Likewise, a SHA-256 digest proves which bytes are referenced; it does not by itself prove that the human event described by those bytes occurred. Where authority depends on a human act, the machine contract must bind the claimed act to substantive evidence, the relevant decision/payload and, where required, signature or verification evidence.

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

Transition to `operative: true` requires a separately reviewed adoption change. The validator has an explicit operative branch and must reject activation unless legal/adoption metadata, exact normative artifacts, substantive activation evidence and aligned operative projections are present.

Changing only the `operative` boolean is therefore insufficient by design.

## 5. Normative adoption versus mutable state

The constitutional adoption record and mutable institutional state serve different purposes and must not be conflated.

The adoption record binds the exact adopted human governance artifacts, the governing rule version, legal identity, governing law, activation evidence and the exact constitutive payload. It may bind immutable normative machine artifacts such as `policy/decision-rules.json`.

It must **not freeze mutable state forever**. In particular, the current Member Registry, delegation registry, Founding-role state and phase evidence evolve after adoption. Those later changes require their own immutable decision records and evidence rather than rewriting the original constitutive signatures or pretending every routine state transition is a new constitutional adoption.

A new constitutional/governance release may have a new adoption record. A routine Member admission or delegation does not silently replace the constitutional adoption record.

## 6. Decision rules and exact arithmetic

`policy/decision-rules.json` defines named approval classes and thresholds. Domain policies may require stricter rules but must not silently weaken a named organization-level approval class.

Thresholds are represented as exact integer ratios rather than rounded floating-point values. A two-thirds threshold is encoded as numerator `2`, denominator `3`, not as an approximate decimal.

The draft classes are:

- Ordinary Approval: quorum `> 1/2`; more votes for than against;
- Qualified Approval: quorum `>= 2/3`; approval `>= 2/3`;
- Constitutional Amendment: quorum `>= 2/3`; approval `>= 3/4`;
- Mission-Locked Amendment: quorum `>= 3/4`; approval `>= 9/10`, two successful votes separated by at least 60 days plus Founding Period guardian consent and independent review.

For vote-based rules, records distinguish at least:

- total eligible voters before conflicts;
- conflicted/recused voters;
- effective eligible voters;
- voting-class seasoning eligibility;
- quorum requirement;
- votes in favour;
- votes against;
- abstentions; and
- resulting approval state.

The validator recomputes the electorate from the operative Member Registry and decision date, verifies unique ballots and recomputes quorum and approval. A stored `result: approved` field is not trusted by itself.

A beneficiary recused from their own compensation decision is excluded from the effective eligible-voter denominator under the proposed constitutional rule. Founder status does not override this recusal.

### Recusal evidence

A recusal that changes a denominator must resolve to a content-addressed conflict determination for the **same decision and person**. The determination must identify its basis, method, date, responsible identity or identities and supporting evidence. A vote envelope cannot remove an eligible opponent merely by listing that person's identifier.

## 7. Membership projection and admission provenance

`policy/membership-status.json` is a repository-safe projection of the Member Registry design.

The canonical operative registry may contain private identity evidence outside public Git. Public projections should expose only stable record IDs, membership state, effective dates and public role references needed for audit.

Automation must **not** infer membership from:

- GitHub organization membership;
- repository collaboration or permissions;
- CLA signature;
- employment or contracting;
- donations or grants;
- contribution count; or
- RDF graph connectivity.

The registry enforces one-person-one-vote and natural-person voting membership.

Every operative admission must prove its authority and effective date:

- an initial formation Member must be expressly included in the exact competent constitutive adoption and use that adoption record as the admission authority;
- a later F0 admission must satisfy the Candidate period and bind a Founding Steward signed admission payload; and
- an F1+ admission must satisfy the Candidate period and bind a valid Ordinary Approval decision.

`active_since` is not a free-standing assertion. It must equal the effective date in the validated admission record. Voting seasoning is computed from that date, preventing a coordinated registry edit from backdating a new Member into immediate protected-vote eligibility.

Historical state changes should remain attributable rather than retroactively rewriting prior decision eligibility.

## 8. Founding Stewardship projection

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
- phase transition cannot be self-declared by the founder alone;
- F1/F2 transition uses Qualified Approval plus evidence; and
- Mission Veto cannot be used merely to prevent a maturity transition that validly satisfies the objective adopted criteria.

## 9. Phase-transition evidence

A phase label or boolean is not evidence of maturity.

F1/F2 transition records must bind:

- exact source and target phases;
- exact decision and phase-effective dates;
- the adopted governance version;
- a canonical transition-payload digest computed **without including that digest field itself**;
- Qualified Approval evidence for that exact transition payload; and
- the objective evidence required by `FOUNDING-STEWARDSHIP.md`.

The F2 time clock is anchored to the governance effective date.

Delegations used to prove F1/F2 capacity count only if they are actually effective and unexpired on the target phase-effective date. Future-dated or expired technical assignments cannot manufacture institutional maturity.

## 10. Delegations

A delegation record must identify:

- stable ID;
- delegated role/actor;
- structured source authority resolving to the adopted decision that created it;
- exact scope types and resources;
- allowed actions;
- explicit prohibitions where material;
- governing rule version;
- effective and expiry state;
- revocation mechanism and authority; and
- immutable decision record.

A delegation may not grant authority that the source does not possess. Technical repository/admin access is never automatically converted into a delegation.

Reserved constitutional actions cannot be smuggled into `allowed_actions`. The decision record must bind the exact delegation payload and the applicable approval evidence.

## 11. Evidence and signature binding

Content-addressed records use repository-relative `path` plus SHA-256. That identifies exact bytes but is only one layer of the proof chain.

A signature record used to establish constitutive, admission, legal-review or CLA authority must identify at least:

- signer identity;
- decision/review identity;
- signature context and version;
- exact `signed_payload_sha256`;
- signature method; and
- independent verification/supporting evidence.

The signed payload digest is computed from the substantive record while excluding the signature references and the digest field itself. This prevents circular self-hashing and prevents old signatures from being replayed over rewritten governance bytes.

Process evidence must identify the exact subject, successful completion state, reviewers and substantive supporting evidence. Generic four-field envelopes do not satisfy an activation blocker.

## 12. Cross-domain consumption

Downstream repositories may reference EC governance terms without copying their definitions.

Examples:

- Funding may state that a >50% concentration decision `requiresApprovalClass ec:QualifiedApproval`.
- The identifier service may state that permanent domain transfer `requiresApprovalClass ec:QualifiedApproval`.
- A future registry may record that a decision was `authorizedBy` a specific adopted EC decision.

The downstream repository remains authoritative for its domain facts and implementation; Governance remains authoritative for the organization-level approval concept it references.

## 13. Decision identity and immutability

A material decision should receive a stable identifier such as:

```text
https://id.exergism.org/governance/decision/{stable-id}
```

Released decision records should be content-addressable or otherwise bound to immutable bytes. Mutable current-state views may point to the latest effective decision but do not replace historical records.

A Mission Veto or Mission Guardian concurrence required by the governing rule should be represented explicitly rather than inferred from the identity of a committer or merger.

## 14. SHACL boundary

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

## 15. CLA activation boundary

The governance integrity workflow also checks `policy/cla-status.yaml` because a fail-closed institutional control plane must not allow the CLA to become `operative: true` while its own activation blockers remain unresolved.

An operative CLA projection must include a legally identified Steward with a content-addressed authority record, governing law, forum, effective date, privacy/records policy, accepted signature methods, completed qualified legal review, non-draft agreement/schedule versions, final covered-project projection and no remaining activation blockers.

The legal-review manifest must bind the exact ICLA, ECLA, Project Schedule and covered-project bytes and the same Steward/law/forum/privacy/acceptance terms. Reviewer signatures bind the exact review payload. The CLA adoption record must bind those same terms and bytes, the approving review manifest and adopter signatures over the exact adoption payload.

This remains an integrity check, not legal advice or legal review.

## 16. Validation and CI

`tools/validate_governance.py` performs deterministic fail-closed checks over committed governance, Membership, Founding Stewardship, CLA-status and ontology artifacts.

CI runs it on changes to constitutional policy, founding/membership policy, CLA material, machine records, ontology, specifications or validator code. Validator diagnostics are persisted as workflow artifacts so a failed integrity gate is auditable.

The validator intentionally does not claim to perform legal review.

## 17. Versioning

Every operative machine-readable policy release must identify an exact governance version. Breaking changes to decision semantics, thresholds, membership eligibility, Mission Lock, identifiers or authority relationships require a new version and explicit migration analysis.

Historical decision, membership and contribution-rights records are not silently rewritten to conform to a later rule version.
