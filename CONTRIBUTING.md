# Contributing to Exergism Commons Governance

This repository governs organization-level institutional rules. It is not the place to bypass the canonical change process of another Exergism Commons project.

## Change classes

Classify a proposal as one of:

1. **Editorial** — wording, links, formatting or metadata with no policy effect.
2. **Descriptive architecture** — documents an existing boundary without changing rights or authority.
3. **Policy** — changes an organization-level process or requirement.
4. **Constitutional** — changes membership, voting thresholds, institutional roles, conflicts, delegation boundaries, persistent-infrastructure authority or amendment rules.
5. **Legal instrument** — changes CLA text, entity terms, succession, grants, representations, governing law, signature mechanics or another legally consequential term.
6. **Adoption state** — changes whether constitutional governance or a legal instrument is operative, its legal entity/steward, effective date or accepted version.

When reasonable reviewers disagree, use the higher class.

## Pull-request requirements

A substantive PR should state:

- the exact problem being solved;
- affected documents and repositories;
- change class;
- whether membership, voting, delegation, contributor rights, outbound licensing, patent separation, stewardship, treasury, persistent infrastructure or privacy are affected;
- backward-compatibility/non-retroactivity consequences;
- known objections or alternative designs; and
- whether machine-readable policy projections also need to change.

Constitutional, legal-instrument and adoption-state changes must not be hidden inside refactors or bulk formatting.

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
- relicense material in another repository; or
- make a draft constitutional or legal instrument operative.

Those changes must occur through the canonical process of the affected project.

## Bootstrap governance rule

Until `policy/governance-status.json` records `operative: true` through a valid adoption change, no record may represent a draft EC decision or delegation as legally operative merely because it was merged, approved on GitHub or validated by CI.

An adoption-state PR must be isolated enough for reviewers to see exactly what changes operativity. It must identify the legal entity, governing law, effective date and immutable adoption record required by the Constitution.

## CLA bootstrap rule

Until `policy/cla-status.yaml` records `operative: true`, no maintainer or automation should reject a contribution merely for lacking acceptance of the draft CLA in this repository.

After adoption, contribution checks should resolve the exact CLA version, Project Schedule version and contributor/entity coverage rather than relying on a mutable `latest` document.

## Persistent infrastructure

Changes that permanently transfer or repurpose `exergism.org`, `id.exergism.org`, an issued persistent identifier, registrar recovery authority or the organization governance namespace are constitutional/infrastructure changes, not ordinary web administration.

Operational hosting changes that preserve identifiers and authority may be delegated under an adopted infrastructure policy.

## Conflict discipline

A contributor reviewing a proposal is not automatically conflicted merely because they participate in EC. A conflict exists where the decision directly determines that person's material private economic interest, own compensation, own contract, own sanction or uniquely preferential appointment.

A conflicted person should disclose and recuse in accordance with the applicable adopted rule.

## Legal review

Community, maintainer, automated or AI review can improve these documents but does not substitute for qualified legal review where `CONSTITUTION.md` or `cla/ADOPTION.md` requires it.
