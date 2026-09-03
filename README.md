# Exergism Commons Governance

> **Status: bootstrap / draft institutional repository.** Organization governance, the constitutional framework, and the Contributor License Agreement are non-operative unless an exact adoption record expressly states otherwise.

This repository is the organization-level control plane for **Exergism Commons (EC)**: constitutional rules, institutional authority, contributor rights, intellectual-property provenance, stewardship, delegations, decision classes, domain custody and other cross-project policies.

Project-specific philosophical, analytical, evidentiary, legal and technical authority remains in the repository that owns that layer. Nothing here silently changes an Exergism release, ECL Bundle, ECL Schedule, ECL-PL patent grant, Funding record or other immutable project artifact.

## Architecture

```text
human constitutional authority
        ↓
versioned organization policy
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

- [`CONSTITUTION.md`](CONSTITUTION.md) — proposed constitutional framework: membership, roles, decision classes, conflicts, delegation, Treasury/Endowment authority, persistent infrastructure and succession.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — cross-project authority boundaries.
- [`architecture/DOMAIN-AND-URI-ARCHITECTURE.md`](architecture/DOMAIN-AND-URI-ARCHITECTURE.md) — `exergism.org`, persistent identifiers and infrastructure custody.
- [`IP-POLICY.md`](IP-POLICY.md) — cross-project intellectual-property and inbound-rights policy.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to propose organization-level governance changes.

### Machine-readable governance

- [`spec/MACHINE-READABLE-GOVERNANCE.md`](spec/MACHINE-READABLE-GOVERNANCE.md) — authority hierarchy, decision records, cross-domain consumption and validation boundary.
- [`policy/governance-status.json`](policy/governance-status.json) — top-level institutional/adoption state. Bootstrap is fail-closed with `operative: false`.
- [`policy/decision-rules.json`](policy/decision-rules.json) — proposed `OrdinaryApproval`, `QualifiedApproval` and `ConstitutionalAmendment` thresholds plus conflict invariants.
- [`policy/delegations.json`](policy/delegations.json) — explicit delegation registry; currently empty/non-operative.
- [`ontology/commons.ttl`](ontology/commons.ttl) — organization governance vocabulary at `https://id.exergism.org/commons#`.
- [`ontology/commons-context.jsonld`](ontology/commons-context.jsonld) — JSON-LD context.
- [`ontology/governance-shapes.ttl`](ontology/governance-shapes.ttl) — structural SHACL constraints.
- [`tools/validate_governance.py`](tools/validate_governance.py) — deterministic fail-closed integrity checks.

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

## Constitutional bootstrap

`CONSTITUTION.md` defines a proposed institutional model but is intentionally **non-operative**. In particular, EC has no legal entity fabricated by GitHub metadata, no machine-created legal Steward, no automatic membership from repository access and no operative delegation registry at bootstrap.

The proposed default approval classes are:

- **Ordinary Approval** — quorum >50% of non-conflicted eligible voters; more votes for than against.
- **Qualified Approval** — quorum ≥2/3; approval ≥2/3 of valid for/against votes.
- **Constitutional Amendment** — quorum ≥2/3; approval ≥3/4.

These thresholds remain draft until constitutionally adopted. Domain policies may require stricter thresholds but must not silently weaken a named organization-level approval class.

The conflict model expressly prevents a compensation beneficiary from substantively voting on their own compensation and prevents funding from purchasing governance rights.

## Funding and persistent-infrastructure integration

Organization governance defines shared authority concepts; domain repositories implement them.

For example, Funding may require `ec:QualifiedApproval` for a concentration or Endowment decision while remaining authoritative for the funding facts, thresholds and records that trigger that requirement. Likewise, `id.exergism.org` may consume the organization rule that permanent domain/identifier-authority transfer requires Qualified Approval while remaining only the resolver implementation.

Persistent organization vocabulary:

- vocabulary: `https://id.exergism.org/commons#`
- ontology: `https://id.exergism.org/ontology/commons`

Minting a term does not make a policy operative.

## Contributor-rights position

The proposed model is **license-in, rights-retained**:

- contributors keep the copyright they own;
- EC receives only the non-exclusive rights required by the exact adopted agreement and Project Schedule;
- outbound relicensing is constrained rather than unlimited;
- the CLA itself grants **no patent rights**;
- repository administration does not create ownership; and
- institutional succession cannot silently rewrite earlier grants.

## Current legal and institutional status

Both the constitutional package and CLA package are intentionally **non-operative** at bootstrap. `policy/governance-status.json` and `policy/cla-status.yaml` are fail-closed projections, not substitutes for competent adoption.

Before organization governance can become operative, EC must resolve at least the legal entity/form, governing law, initial membership/voter registry, valid adoption mechanism, records/privacy controls, treasury authority and appropriate independent legal review. The CLA has additional activation gates in `cla/ADOPTION.md`.

A merge of draft architecture into Git is not ratification, incorporation, signature, delegation or legal advice.
