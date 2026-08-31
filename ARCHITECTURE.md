# Exergism Commons Organization Architecture

> **Status: descriptive governance draft.** This document maps existing project boundaries. It does not change the legal effect of any project artifact.

## 1. Purpose

Exergism Commons is a connected but deliberately layered ecosystem. The organization should make relationships explicit without allowing repository proximity, maintainer control, semantic inference, or a shared name to collapse distinct philosophical, analytical, governance, copyright and patent layers into one another.

This document records the cross-project architecture that organization-level governance must preserve.

## 2. Project layers

### 2.1 Exergism — philosophical and formal source

Repository: `Exergism-Commons/exergism`

Exergism is the canonical public development lineage of the **Emergentist Metaphysics of Liberation**. Its source artifacts include the philosophical corpus, four-book architecture and the formal exergic-analysis model. The generated OWL representation is derivative infrastructure rather than an independent source of doctrine.

The repository currently separates licensing by material class:

- corpus, formal model, examples and documentation: `CC-BY-SA-4.0`;
- scripts/tooling and canonical schema: `Apache-2.0`.

Canonicality is procedural. Repository administration is stewardship, not a claim that the organization owns philosophical truth or automatically owns contributor copyrights.

### 2.2 Formal exergic analysis — diagnostic layer

Formal exergic analysis is part of the Exergism source lineage. Downstream projects may pin an exact Exergism release and apply the formal model to precisely attributed objects.

A formal result is a diagnostic/falsification input. It does not automatically create an ECL restriction, a legal conclusion, a patent rule or an organization-level governance decision.

### 2.3 ECL — copyright/software-rights licensing and evidence governance

Repository: `Exergism-Commons/exergic-commons-license`

The Exergic Commons License is an experimental source-available license project. It combines:

- operative/draft license text;
- exact immutable Schedules and ECL Bundles;
- evidence and counter-evidence records;
- a Git-native semantic knowledge model;
- formal Exergism analysis as an upstream diagnostic layer;
- public/adversarial review;
- versioned governance decisions; and
- release/legal-review gates.

ECL explicitly distinguishes living knowledge from immutable released legal artifacts. A mutable issue, dossier, registry view, ontology inference or current branch does not itself have licensing effect.

ECL 0.3-DRAFT currently grants copyright/software rights only from each actual Licensor and expressly grants no patent rights.

### 2.4 ECL-PL — separate patent track

Repository: `Exergism-Commons/ecl-patent-license`

ECL-PL is a separate architecture for optional, explicit, attributable and immutable patent grants. Its core separation rules include:

- ECL does not automatically apply ECL-PL;
- ECL-PL does not alter ECL copyright rights;
- contributor or maintainer status does not make someone a Patent Licensor;
- repository participation does not itself create a patent grant; and
- any operative patent grant must come from an identified person/entity with authority over the covered claims.

Organization-level contributor policy must not silently defeat these invariants.

### 2.5 `.github` — organization presentation and shared GitHub metadata

Repository: `Exergism-Commons/.github`

This repository provides the public organization profile and may later host shared GitHub community-health files. It is presentation/infrastructure, not the canonical home of Exergism doctrine, ECL legal text, ECL governance evidence, or ECL-PL patent grants.

### 2.6 `governance` — organization-level institutional layer

Repository: `Exergism-Commons/governance`

This repository is the appropriate home for cross-project rules that would otherwise be duplicated or become ambiguous, including:

- contributor inbound-rights policy;
- legal-steward identity and succession;
- organization-level intellectual-property provenance;
- shared contribution records and acceptance rules;
- cross-project governance principles; and
- institutional policies that are explicitly distinct from project-specific substantive governance.

It must not become a shortcut for changing canonical content in another repository.

## 3. Authority boundaries

The following must remain explicit:

| Question | Canonical layer |
| --- | --- |
| What does Exergism claim? | `exergism` canonical source |
| How is formal exergic analysis defined? | pinned `exergism` formal model |
| Does an actor/project meet ECL criteria? | ECL evidence + governance process |
| What restrictions govern a software release? | exact ECL License + exact Schedule/Bundle |
| Are patent rights granted? | exact ECL-PL PatentGrantBundle or another express patent instrument |
| Who may accept contributor rights for the organization? | organization `governance` adoption/steward records |
| What rights did a contributor grant? | signed CLA + exact project schedule/version + applicable target license |

No row inherits the authority of another merely because the same maintainers work on both.

## 4. Cross-project contributor-rights problem

The repositories currently have different inbound/outbound regimes:

- Exergism already uses target-file licenses and expressly preserves contributor ownership.
- ECL contains a draft broad inbound copyright permission in `CONTRIBUTING.md`, while its legal-review specification identifies chain of title and contributor enforcement authority as a material release-gate issue.
- ECL-PL intentionally refuses to infer patent grants from contribution.
- Some organization repositories do not yet state a repository-wide outbound content license.

A single unconditional CLA would therefore be structurally wrong. The organization-level CLA uses an exact **Project Schedule** so the same signature can support multiple repositories without pretending that all target materials have the same license or patent effect.

## 5. Exactness and non-retroactivity

Contributor policy follows the same architectural discipline used elsewhere in the ecosystem:

```text
CLA text version
    + Project Schedule version
    + legal Steward/adoption record
    + contributor acceptance record
    = exact inbound-rights state for a Contribution
```

A later schedule may govern later submissions. It cannot silently broaden the outbound licensing options applicable to an older Contribution unless the older agreement already expressly permitted that class of successor license.

## 6. Anti-capture constraint

Cross-project governance should make institutional continuity easier without converting stewardship into ownership.

Accordingly:

- no ordinary contribution requires copyright assignment;
- contributor copyright remains with the contributor or other actual rightsholder;
- the organization receives a non-exclusive license sufficient for project continuity;
- relicensing authority is constrained by the applicable Project Schedule;
- succession is permitted only to a disclosed legal steward that assumes the obligations of the CLA; and
- public releases remain governed by the terms under which they were actually released.
