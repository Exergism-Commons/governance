# Exergism Commons Organization Architecture

> **Status: descriptive governance draft.** This document maps existing project boundaries. It does not change the legal effect of any project artifact.

## 1. Purpose

Exergism Commons is a connected but deliberately layered ecosystem. The organization should make relationships explicit without allowing repository proximity, maintainer control, semantic inference, funding, a shared domain, or a shared name to collapse distinct philosophical, analytical, governance, copyright, patent, funding and infrastructure layers into one another.

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

A formal result is a diagnostic/falsification input. It does not automatically create an ECL restriction, a legal conclusion, a patent rule, a Funding decision or an organization-level governance decision.

### 2.3 ECL — copyright/software-rights licensing and evidence governance

Repository: `Exergism-Commons/exergic-commons-license`

The Exergic Commons License is an experimental source-available license project. It combines versioned legal artifacts, evidence and counter-evidence records, a Git-native semantic knowledge model, formal Exergism analysis as an upstream diagnostic layer, public/adversarial review, governance decisions and release/legal-review gates.

ECL explicitly distinguishes living knowledge from immutable released legal artifacts. A mutable issue, dossier, registry view, ontology inference or current branch does not itself have licensing effect.

ECL remains authoritative for ECL-specific criteria, evidence, governance and exact legal artifacts.

### 2.4 ECL-PL — separate patent track

Repository: `Exergism-Commons/ecl-patent-license`

ECL-PL is a separate architecture for optional, explicit, attributable and immutable patent grants. Its core separation rules include:

- ECL does not automatically apply ECL-PL;
- ECL-PL does not alter ECL copyright rights;
- contributor or maintainer status does not make someone a Patent Licensor;
- repository participation does not itself create a patent grant; and
- any operative patent grant must come from an identified person/entity with authority over the covered claims.

Organization-level contributor policy must not silently defeat these invariants.

### 2.5 Funding — institutional-capacity and financial-governance domain

Repository: `Exergism-Commons/funding`

Funding owns funding-domain strategy, opportunity data, Endowment/Treasury policy implementations, funding concentration records and its executable governance subset.

Organization governance defines shared institutional concepts that Funding may consume, such as `QualifiedApproval`, conflict-recusal rules and the principle that funding does not purchase governance rights.

Funding remains authoritative for the domain facts and thresholds that trigger those concepts unless organization-level constitutional policy expressly defines the threshold itself.

### 2.6 Persistent identifier infrastructure

Repository: `Exergism-Commons/id.exergism-commons.github.io`

`id.exergism.org` is the persistent identifier authority and resolver implementation. It does not own the semantics of Exergism, ECL, Funding or organization governance merely because their identifiers use its host.

Organization governance controls the persistence contract, domain custody and authority for permanent transfer or reassignment of the identifier surface. Operational implementation may be delegated.

### 2.7 Public website

Repository: `Exergism-Commons/exergism-commons.github.io`

`www.exergism.org` is the public presentation layer. It is not a canonical philosophical, legal, semantic or governance source.

### 2.8 `.github` — organization presentation and shared GitHub metadata

Repository: `Exergism-Commons/.github`

This repository provides the public organization profile and may host shared GitHub community-health files. It is presentation/infrastructure, not the canonical home of substantive project authority.

### 2.9 `governance` — organization-level institutional layer

Repository: `Exergism-Commons/governance`

This repository is the organization-level control plane for cross-project rules that would otherwise be duplicated or ambiguous, including:

- constitutional framework and decision classes;
- membership and conflict rules;
- delegated authority and succession;
- contributor inbound-rights policy;
- legal-steward identity and succession;
- organization-level intellectual-property provenance;
- domain and persistent-identifier stewardship;
- treasury/Endowment authority vocabulary; and
- shared machine-readable institutional policy.

It must not become a shortcut for changing canonical content in another repository.

## 3. Authority boundaries

| Question | Canonical layer |
| --- | --- |
| What does Exergism claim? | `exergism` canonical source |
| How is formal exergic analysis defined? | pinned `exergism` formal model |
| Does an actor/project meet ECL criteria? | ECL evidence + governance process |
| What restrictions govern a software release? | exact ECL License + exact Schedule/Bundle |
| Are patent rights granted? | exact ECL-PL grant or another express patent instrument |
| What is a Funding opportunity/funder/concentration state? | `funding` domain records |
| What is `QualifiedApproval` at organization level? | `governance` constitutional/policy layer |
| What does a persistent EC identifier resolve to? | `id.exergism.org` resolver registry |
| What does the identifier mean? | repository/release that owns the semantic resource |
| Who may accept contributor rights for EC? | organization governance adoption/steward records |
| What rights did a contributor grant? | exact CLA + Project Schedule + acceptance record + target license |

No row inherits the authority of another merely because the same maintainers work on both or because two records are connected in RDF.

## 4. Institutional control-plane model

```text
Constitution / adopted organization policy
        ↓
versioned decision rule
        ↓
GovernanceDecision / Delegation
        ↓
machine-readable projection + integrity checks
        ↓
domain implementation
```

This is a control relationship only where an adopted organization-level rule actually applies. The downstream domain retains authority over its own facts and artifacts.

A machine-readable projection is not itself institutional authority. SHACL or CI can reject an invalid record; they cannot manufacture a legal entity, membership, vote, contract or delegation.

## 5. Contributor-rights problem

The repositories have different inbound/outbound regimes. Exergism uses mixed target-file licenses and preserves contributor ownership. ECL has its own legal-development contribution history and chain-of-title concerns. ECL-PL refuses to infer patent grants from contribution. Some organization repositories do not yet state a repository-wide outbound content license.

A single unconditional CLA would therefore be structurally wrong. The organization-level CLA uses an exact **Project Schedule** so the same signature can support multiple repositories without pretending that all target materials have the same license or patent effect.

## 6. Exactness and non-retroactivity

Contributor policy follows the same architectural discipline used elsewhere in the ecosystem:

```text
CLA text version
    + Project Schedule version
    + legal Steward/adoption record
    + contributor acceptance record
    = exact inbound-rights state for a Contribution
```

Organization governance follows the parallel discipline:

```text
Constitution/policy version
    + exact approval class
    + eligible-voter/conflict state
    + adoption/decision record
    + effective state
    = exact institutional governance state
```

A later policy cannot silently broaden an older contributor grant or rewrite a completed immutable decision.

## 7. Anti-capture constraint

Cross-project governance should make institutional continuity easier without converting stewardship, funding, employment or technical access into ownership.

Accordingly:

- no ordinary contribution requires copyright assignment;
- contributor copyright remains with the contributor or other actual rightsholder;
- funding does not purchase governance rights;
- repository permissions are not institutional delegations;
- EC assets are not membership shares;
- relicensing authority is constrained by the applicable Project Schedule;
- succession must preserve the obligations attached to the authority being transferred; and
- public releases remain governed by the terms under which they were actually released.

## 8. Domain architecture

The detailed domain, URI, namespace and persistence architecture is maintained in `architecture/DOMAIN-AND-URI-ARCHITECTURE.md`.

Organization-level vocabulary uses `https://id.exergism.org/commons#`. Minting or resolving a term does not make the associated draft policy operative.
