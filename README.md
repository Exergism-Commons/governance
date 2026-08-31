# Exergism Commons Governance

> **Status: bootstrap / draft policy repository.** No Contributor License Agreement or other legally consequential instrument in this repository is operative unless its adoption record expressly says so.

This repository is the organization-level home for governance, contributor-rights, intellectual-property provenance, stewardship, and other cross-project institutional policies of **Exergism Commons**.

Project-specific legal, philosophical, analytical, and technical authority remains in the repository that owns that layer. Nothing here silently changes an existing Exergism release, ECL Bundle, ECL Schedule, ECL-PL patent grant, or other immutable project artifact.

## Repository map

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — organization-level architecture and authority boundaries.
- [`IP-POLICY.md`](IP-POLICY.md) — cross-project intellectual-property and inbound-rights policy.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to propose organization-level governance changes.
- [`cla/CLA-1.0-DRAFT.md`](cla/CLA-1.0-DRAFT.md) — proposed individual Contributor License Agreement.
- [`cla/ENTITY-CLA-1.0-DRAFT.md`](cla/ENTITY-CLA-1.0-DRAFT.md) — proposed entity/corporate Contributor License Agreement.
- [`cla/PROJECT-SCHEDULE.md`](cla/PROJECT-SCHEDULE.md) — repository-by-repository scope and outbound constraints.
- [`cla/PROCESS.md`](cla/PROCESS.md) — proposed acceptance, verification, records and exception process.
- [`cla/LEGACY-CONTRIBUTIONS.md`](cla/LEGACY-CONTRIBUTIONS.md) — treatment of contributions made before CLA adoption.
- [`cla/AI-ASSISTED-CONTRIBUTIONS.md`](cla/AI-ASSISTED-CONTRIBUTIONS.md) — provenance rules for AI-assisted work.
- [`cla/DESIGN-RATIONALE.md`](cla/DESIGN-RATIONALE.md) — why this model was selected and what it deliberately does not do.
- [`cla/FAQ.md`](cla/FAQ.md) — contributor-facing explanation.
- [`cla/ADOPTION.md`](cla/ADOPTION.md) — release/adoption gates that must be satisfied before the CLA can become operative.
- [`policy/cla-status.yaml`](policy/cla-status.yaml) — machine-readable CLA adoption state.
- [`policy/covered-projects.yaml`](policy/covered-projects.yaml) — machine-readable project scope projection.

## Design constraints

Organization-level governance preserves the ecosystem's existing separation of concerns:

```text
Exergism
  └─ philosophical corpus + formal exergic-analysis model
             │ declared/pinned dependency
             ▼
ECL
  └─ evidence/governance + copyright/software-rights licensing

ECL-PL
  └─ separate optional patent-licensing architecture

Exergism Commons governance
  └─ cross-project stewardship + contributor provenance + institutional policy
```

The arrows are dependency or stewardship relationships, not automatic transfers of legal authority.

## Contributor-rights position

The proposed model is **license-in, rights-retained**:

- contributors keep the copyright they own;
- Exergism Commons receives only the non-exclusive rights required to maintain and publish covered projects;
- outbound relicensing is constrained by the project schedule rather than left unlimited;
- the CLA itself grants **no patent rights**;
- repository administration does not create ownership; and
- a future institutional successor may receive CLA rights only through the controlled succession mechanism in the agreement.

## Current legal status

The CLA package is intentionally **not operative** at bootstrap. The public GitHub organization name alone does not establish the identity or capacity of the legal person that would enter into contributor agreements. `cla/ADOPTION.md` therefore blocks activation until a competent legal steward, governing law, acceptance mechanism, records/privacy process, and legal review are recorded.

For automation, `policy/cla-status.yaml` is the machine-readable status projection. The signed legal instrument and its immutable adoption record control legal interpretation; automation must fail closed rather than infer an operative CLA from a branch name or file presence.
