# Contributing to Exergism Commons Governance

This repository governs organization-level institutional rules. It is not the place to bypass the canonical change process of another Exergism Commons project.

## Change classes

Classify a proposal as one of:

1. **Editorial** — wording, links, formatting or metadata with no policy effect.
2. **Descriptive architecture** — documents an existing boundary without changing rights or authority.
3. **Policy** — changes an organization-level process or requirement.
4. **Constitutional** — changes membership, voting thresholds, institutional roles, conflicts, delegation boundaries, persistent-infrastructure authority, founder phase-transition rules or amendment rules.
5. **Mission-locked constitutional** — changes a protected Mission Lock invariant, the scope of the Mission Veto, the requirement for Founding Steward/Mission Guardian concurrence, or a rule whose primary effect is to weaken the protected identity of EC.
6. **Legal instrument** — changes CLA text, entity terms, succession, grants, representations, governing law, signature mechanics or another legally consequential term.
7. **Adoption state** — changes whether constitutional governance, Membership, Founding Stewardship or a legal instrument is operative, its legal entity/steward, effective date or accepted version.

When reasonable reviewers disagree, use the higher class.

A proposal cannot avoid the Mission-Locked Amendment process merely by describing itself as a normal Constitutional change.

## Pull-request requirements

A substantive PR should state:

- the exact problem being solved;
- affected documents and repositories;
- change class;
- whether Mission Lock, Founding Stewardship, Membership, voting, delegation, contributor rights, outbound licensing, patent separation, treasury, persistent infrastructure or privacy are affected;
- backward-compatibility/non-retroactivity consequences;
- known objections or alternative designs; and
- whether machine-readable policy projections also need to change.

Constitutional, mission-locked, legal-instrument and adoption-state changes must not be hidden inside refactors or bulk formatting.

## Human and machine layers change together

If a proposal changes a concept represented in `policy/**`, `ontology/**`, or `spec/MACHINE-READABLE-GOVERNANCE.md`, the PR must either update the machine projection in the same change or explain precisely why no machine change is required.

The inverse also applies: machine-readable policy must not silently broaden or weaken the human rule it projects.

`tools/validate_governance.py` checks deterministic integrity but does not decide whether a policy is wise, lawfully adopted or legally valid.

## No silent cross-project authority

A merge here does not automatically:

- modify canonical Exergism content;
- alter an ECL License or Schedule;
- create an ECL designation;
- create or modify an ECL-PL patent grant;
- change a Funding domain fact or opportunity record;
- relicense material in another repository;
- make a GitHub collaborator an EC Member;
- create an operative Founding Steward assignment; or
- make a draft constitutional or legal instrument operative.

Those changes must occur through the canonical process of the affected project or exact EC adoption process.

## Bootstrap governance rule

Until `policy/governance-status.json` records `operative: true` through a valid adoption change, no record may represent a draft EC decision, Member, Founding Steward assignment or delegation as legally operative merely because it was merged, approved on GitHub or validated by CI.

An adoption-state PR must be isolated enough for reviewers to see exactly what changes operativity. It must identify the legal entity, governing law, effective date and immutable adoption record required by the Constitution, plus the aligned Member Registry, founding/mission-protection record, conflicts, records/privacy, treasury controls, succession process and legal-review state.

## Membership changes

Changes to admission, Candidate duration, voting seasoning, inactivity, suspension, termination, one-person-one-vote or natural-person voting eligibility are substantive governance changes.

A proposal that materially weakens anti-capture seasoning or permits money/property-based voting must not be treated as editorial maintenance.

Membership must never be inferred from GitHub organization membership, repository access, contribution count, CLA acceptance, employment or funding.

## Founding Stewardship and Mission Lock

Founder authority must remain explicit rather than hidden in technical credentials.

Changes to F0/F1/F2 criteria, founder executive powers, Mission Veto scope, founder economic prohibitions, succession or Mission Guardian authority require corresponding updates to `FOUNDING-STEWARDSHIP.md`, `policy/founding-stewardship.json` and any affected constitutional/machine rules.

The Founding Steward's ordinary Member vote and founder constitutional authority are separate concepts. Do not encode founder authority as weighted voting.

## CLA bootstrap rule

Until `policy/cla-status.yaml` records `operative: true`, no maintainer or automation should reject a contribution merely for lacking acceptance of the draft CLA in this repository.

After adoption, contribution checks should resolve the exact CLA version, Project Schedule version and contributor/entity coverage rather than relying on a mutable `latest` document.

## Persistent infrastructure

Changes that permanently transfer or repurpose `exergism.org`, `id.exergism.org`, an issued persistent identifier, registrar recovery authority or the organization governance namespace are constitutional/infrastructure changes, not ordinary web administration.

Operational hosting changes that preserve identifiers and authority may be delegated under an adopted infrastructure policy.

## Conflict discipline

A contributor reviewing a proposal is not automatically conflicted merely because they participate in EC. A conflict exists where the decision directly determines that person's material private economic interest, own compensation, own contract, own sanction or uniquely preferential appointment.

A conflicted person should disclose and recuse in accordance with the applicable adopted rule.

Founder status does not override recusal.

## Legal review

Community, maintainer, automated or AI review can improve these documents but does not substitute for qualified legal review where `CONSTITUTION.md`, `FOUNDING-STEWARDSHIP.md` or `cla/ADOPTION.md` requires it.
