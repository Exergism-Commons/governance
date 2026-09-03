# Exergism Commons Governance

> **Status: bootstrap / draft institutional repository.** Organization governance, Founding Stewardship, Membership, the constitutional framework and the Contributor License Agreement are non-operative unless an exact adoption record expressly states otherwise.

This repository is the organization-level control plane for **Exergism Commons (EC)**: constitutional rules, institutional authority, founder-led bootstrap, membership, contributor rights, intellectual-property provenance, stewardship, delegations, decision classes, domain custody and other cross-project policies.

Project-specific philosophical, analytical, evidentiary, legal and technical authority remains in the repository that owns that layer. Nothing here silently changes an Exergism release, ECL Bundle, ECL Schedule, ECL-PL patent grant, Funding record or other immutable project artifact.

## Architecture

```text
Mission / Constitution / adopted organization policy
        ↓
Founding phase + Membership + explicit roles
        ↓
versioned decision rule
        ↓
machine-readable governance state
        ↓
SHACL / deterministic integrity checks
        ↓
GovernanceDecision / Delegation
        ↓
domain implementations
   ├── Funding
   ├── id.exergism.org
   ├── repositories
   ├── contributor rights / CLA
   └── future registry
```

The machine layer enforces a reviewable subset of adopted rules. It cannot manufacture legal or institutional authority.

## Repository map

### Institutional architecture

- [`CONSTITUTION.md`](CONSTITUTION.md) — proposed constitutional framework and Mission Lock.
- [`FOUNDING-STEWARDSHIP.md`](FOUNDING-STEWARDSHIP.md) — founder-led bootstrap, Founding Steward powers/limits, Mission Veto, F0→F1→F2 transition and succession.
- [`MEMBERSHIP.md`](MEMBERSHIP.md) — one-person-one-vote membership, admission, Candidate period, voting seasoning, inactivity, suspension and anti-Sybil controls.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — cross-project authority boundaries.
- [`architecture/DOMAIN-AND-URI-ARCHITECTURE.md`](architecture/DOMAIN-AND-URI-ARCHITECTURE.md) — `exergism.org`, persistent identifiers and infrastructure custody.
- [`IP-POLICY.md`](IP-POLICY.md) — cross-project intellectual-property and inbound-rights policy.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to propose organization-level governance changes.

### Machine-readable governance

- [`spec/MACHINE-READABLE-GOVERNANCE.md`](spec/MACHINE-READABLE-GOVERNANCE.md) — authority hierarchy, exact threshold arithmetic, Membership/Founding projections and validation boundary.
- [`policy/governance-status.json`](policy/governance-status.json) — top-level institutional/adoption state. Bootstrap is fail-closed with `operative: false`.
- [`policy/decision-rules.json`](policy/decision-rules.json) — exact rational rules for `OrdinaryApproval`, `QualifiedApproval`, `ConstitutionalAmendment` and `MissionLockedAmendment`.
- [`policy/membership-status.json`](policy/membership-status.json) — draft repository-safe Member Registry projection.
- [`policy/founding-stewardship.json`](policy/founding-stewardship.json) — draft Founding Steward, Mission Lock and maturity-phase projection.
- [`policy/delegations.json`](policy/delegations.json) — explicit delegation registry; currently empty/non-operative.
- [`ontology/commons.ttl`](ontology/commons.ttl) — organization governance vocabulary at `https://id.exergism.org/commons#`.
- [`ontology/commons-context.jsonld`](ontology/commons-context.jsonld) — JSON-LD context.
- [`ontology/governance-shapes.ttl`](ontology/governance-shapes.ttl) — structural SHACL constraints.
- [`tools/validate_governance.py`](tools/validate_governance.py) — deterministic fail-closed integrity checks, including governance and CLA activation gates.

### Contributor rights / CLA

- [`cla/CLA-1.0-DRAFT.md`](cla/CLA-1.0-DRAFT.md) — proposed individual Contributor License Agreement.
- [`cla/ENTITY-CLA-1.0-DRAFT.md`](cla/ENTITY-CLA-1.0-DRAFT.md) — proposed entity/corporate Contributor License Agreement.
- [`cla/PROJECT-SCHEDULE.md`](cla/PROJECT-SCHEDULE.md) — repository-by-repository scope and outbound constraints.
- [`cla/PROCESS.md`](cla/PROCESS.md) — proposed acceptance, verification, records and exception process.
- [`cla/PRIVACY-AND-RECORDS.md`](cla/PRIVACY-AND-RECORDS.md) — privacy, data minimization, retention and agreement-record architecture.
- [`cla/LEGACY-CONTRIBUTIONS.md`](cla/LEGACY-CONTRIBUTIONS.md) — treatment of contributions made before CLA adoption.
- [`cla/AI-ASSISTED-CONTRIBUTIONS.md`](cla/AI-ASSISTED-CONTRIBUTIONS.md) — provenance rules for AI-assisted work.
- [`cla/DESIGN-RATIONALE.md`](cla/DESIGN-RATIONALE.md) — design rationale and rejected alternatives.
- [`cla/FAQ.md`](cla/FAQ.md) — contributor-facing explanation.
- [`cla/ADOPTION.md`](cla/ADOPTION.md) — activation gates.
- [`policy/cla-status.yaml`](policy/cla-status.yaml) — machine-readable CLA adoption state.
- [`policy/covered-projects.yaml`](policy/covered-projects.yaml) — machine-readable CLA project scope projection.

## Project authority boundaries

```text
Exergism
  └─ canonical philosophy + formal analytical model

ECL
  └─ ECL evidence/governance + copyright/software-rights legal artifacts

ECL-PL
  └─ separate optional patent-licensing architecture

Funding
  └─ funding strategy, records and executable funding-policy subset

id.exergism.org
  └─ persistent identifier resolution, not semantic authority

www.exergism.org
  └─ public presentation, not canonical authority

Exergism Commons governance
  └─ organization-level institutional authority and shared constraints
```

No arrow, repository membership, funding relationship, semantic edge or technical permission transfers authority automatically.

## Founder-led constitutional bootstrap

EC currently depends materially on its founder. This repository makes that concentration explicit instead of pretending that a mature democratic institution already exists.

The proposed initial **Founding Steward is Daniel Molinero Lucas**.

The principle is:

> **strong stewardship without ownership**.

During F0 the Founding Steward has strong strategic/bootstrap authority, but founder status creates no automatic salary, grant percentage, Endowment claim, Treasury ownership or IP ownership.

The Founding Steward also has a narrow **negative Mission Veto** during the Founding Period. It can block a proposal that violates the protected Mission Lock or attempts a protected irreversible action through the wrong approval path. It cannot enact an alternative decision or override conflict rules for the founder's own private benefit.

Founder executive power is designed to recede through evidence-based maturity phases:

```text
F0 founder-led bootstrap
        ↓
F1 early institution
        ↓
F2 distributed institution
```

At F2 the founder is expected to cease having general executive primacy and retain, if still applicable, a narrower Mission Guardian function.

## Mission Lock

Membership governs **Exergism Commons**, not an arbitrary organization that happens to inherit its assets and name.

The Mission Lock protects EC's institutional identity: stewardship around Exergism, project-authority separation, non-ownership membership, no governance-for-money, contributor-rights attribution, persistent-ID integrity, contestability and anti-capture.

It does not freeze every philosophical claim, roadmap item or implementation decision.

A `MissionLockedAmendment` is deliberately harder than an ordinary constitutional amendment: during the Founding Period it requires at least 3/4 quorum, 90% approval, two successful votes at least 60 days apart, independent review and Founding Steward/Mission Guardian consent.

## Membership

Voting membership is for natural persons and follows:

> **one person = one Member = one vote**.

Founder status, funding, employment, GitHub permissions, commit count or donations do not increase voting weight.

The draft lifecycle is:

```text
participant
   ↓
Candidate (>=30 days)
   ↓
Active Member
   ↓
class-specific voting seasoning
```

Default minimum Active-Membership age before voting:

- Ordinary Approval: 30 days;
- Qualified Approval: 90 days;
- Constitutional Amendment: 90 days;
- Mission-Locked Amendment: 180 days.

This reduces capture through mass admission immediately before consequential votes.

The proposed bootstrap record designates Daniel Molinero Lucas as the initial Member for formation purposes, but that projection remains `operative_membership: false` until a competent institutional adoption creates the actual Member Registry.

Member status does not grant bank, DNS, repository-admin, CLA-record or other operational access; roles and delegations are separate.

## Approval classes

Thresholds are encoded as exact integer ratios rather than rounded decimals:

- **Ordinary Approval** — quorum >1/2 of non-conflicted eligible voters; more votes for than against.
- **Qualified Approval** — quorum ≥2/3; approval ≥2/3.
- **Constitutional Amendment** — quorum ≥2/3; approval ≥3/4.
- **Mission-Locked Amendment** — quorum ≥3/4; approval ≥9/10 plus the additional Mission Lock process.

Domain policies may require stricter thresholds but must not silently weaken a named organization-level approval class.

The conflict model expressly prevents a compensation beneficiary from substantively voting on their own compensation. Founder status does not bypass recusal. Funding cannot purchase governance rights.

## Funding and persistent-infrastructure integration

Organization governance defines shared authority concepts; domain repositories implement them.

Funding may require `ec:QualifiedApproval` for a concentration or Endowment decision while remaining authoritative for the funding facts and records that trigger that requirement. Likewise, `id.exergism.org` may consume the organization rule that permanent domain/identifier-authority transfer requires Qualified Approval while remaining only the resolver implementation.

Persistent organization vocabulary:

- vocabulary: `https://id.exergism.org/commons#`
- ontology: `https://id.exergism.org/ontology/commons`

Minting a term does not make a policy operative.

## Contributor-rights position

The proposed model is **license-in, rights-retained**:

- contributors keep the copyright they own;
- EC receives limited review/archive rights while an unaccepted proposal is under review;
- the full perpetual project grant vests only for an Accepted Contribution;
- outbound relicensing is constrained rather than unlimited;
- the CLA itself grants **no patent rights**;
- repository administration does not create ownership; and
- institutional succession cannot silently rewrite earlier grants.

The same acceptance boundary now applies to both the Individual and Entity CLA drafts.

## Current legal and institutional status

The constitutional, Founding Stewardship, Membership and CLA packages are intentionally **non-operative** at bootstrap.

`tools/validate_governance.py` now contains explicit fail-closed checks for both non-operative and future operative states. Merely flipping an `operative` boolean must fail unless the associated legal entity/adoption metadata, Member Registry, founder assignment, conflict/records/treasury controls, legal review and aligned policy flags are present.

Before organization governance can become operative, EC must resolve at least the legal entity/form, governing law, initial membership/voter registry, valid adoption mechanism, records/privacy controls, treasury authority, Founding Steward assignment/succession compatibility and appropriate independent legal review. The CLA has additional activation gates in `cla/ADOPTION.md`.

A merge of draft architecture into Git is not ratification, incorporation, signature, delegation or legal advice.
