# Contributing to Exergism Commons Governance

This repository governs organization-level institutional rules. It is not the place to bypass the canonical change process of another Exergism Commons project.

## Change classes

Classify a proposal as one of:

1. **Editorial** — wording, links, formatting or metadata with no policy effect.
2. **Descriptive architecture** — documents an existing boundary without changing rights or authority.
3. **Policy** — changes an organization-level process or requirement.
4. **Legal instrument** — changes CLA text, entity terms, succession, grants, representations, governing law, signature mechanics or another legally consequential term.
5. **Adoption state** — changes whether a legal instrument is operative, its legal steward, effective date or accepted version.

When reasonable reviewers disagree, use the higher class.

## Pull-request requirements

A substantive PR should state:

- the exact problem being solved;
- affected documents and repositories;
- whether contributor rights, outbound licensing, patent separation, stewardship or privacy are affected;
- backward-compatibility/non-retroactivity consequences;
- known objections or alternative designs; and
- whether machine-readable policy projections also need to change.

Legal-instrument and adoption-state changes must not be hidden inside refactors or bulk formatting.

## No silent cross-project authority

A merge here does not automatically:

- modify canonical Exergism content;
- alter an ECL License or Schedule;
- create an ECL designation;
- create or modify an ECL-PL patent grant; or
- relicense material in another repository.

Those changes must occur through the canonical process of the affected project.

## CLA bootstrap rule

Until `policy/cla-status.yaml` records `operative: true`, no maintainer or automation should reject a contribution merely for lacking acceptance of the draft CLA in this repository.

After adoption, contribution checks should resolve the exact CLA version, Project Schedule version and contributor/entity coverage rather than relying on a mutable `latest` document.

## Legal review

Community, maintainer, automated or AI review can improve these documents but does not substitute for qualified legal review where `cla/ADOPTION.md` requires it.
