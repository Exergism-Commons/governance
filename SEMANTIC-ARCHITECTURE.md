# Exergism Commons Semantic Architecture

> **Status: pre-1.0 architecture draft.** This document does not make a vocabulary, governance policy, licence, funding decision, or identifier operative. It defines the intended ownership and reuse model before EC declares stable semantic releases.

## 1. Goal

Exergism Commons projects share one persistent identifier authority without becoming one monolithic ontology. The design separates:

1. **shared EC primitives** — concepts whose meaning is genuinely cross-project;
2. **domain vocabularies** — terms owned by Governance, Funding, Exergism, ECL, ECL-PL, and future domains;
3. **persistent resolution** — `id.exergism.org`, which publishes approved representations but does not own their semantics.

A project MUST reuse an existing EC term when it means the same thing. It MUST NOT mint a project-local synonym merely to avoid a dependency on another EC namespace.

## 2. Namespace ownership

| Namespace | Semantic owner | Scope |
| --- | --- | --- |
| `https://id.exergism.org/commons#` | Exergism Commons organization governance | Minimal cross-project primitives only |
| `https://id.exergism.org/governance#` | `Exergism-Commons/governance` | Institutional authority, membership, decisions, voting, roles, delegations, conflicts |
| `https://id.exergism.org/funding#` | `Exergism-Commons/funding` | Funding opportunities, treasury/funding state, concentration, compensation and Endowment-specific concepts |
| `https://id.exergism.org/exergism#` | `Exergism-Commons/exergism` | Canonical philosophical and exergic-analysis concepts |
| `https://id.exergism.org/ecl#` | `Exergism-Commons/exergic-commons-license` | ECL evidence, assessment, Schedule, restriction and release semantics |
| `https://id.exergism.org/ecl-pl#` | `Exergism-Commons/ecl-patent-license` | Patent-grant and patent-policy semantics |

`id.exergism.org` owns none of those meanings. It owns the persistence and dereferencing contract.

## 3. Shared vocabulary boundary

`commons#` is deliberately small. A term belongs there only when all of the following hold:

- at least two EC domains need the same semantic concept;
- the concept is not intrinsically owned by one domain;
- an established external vocabulary does not already provide an adequate term with acceptable semantics;
- sharing the term does not create unwanted inference across legal, philosophical or institutional boundaries.

Initial common candidates are:

- `Actor`
- `Person`
- `Organization`
- `Artifact`
- `ReleaseArtifact`
- `EvidenceRecord`
- `stableId`
- `operative`
- `effectiveDate`
- `provenance`
- `sha256`
- `supersedes`
- `reviewDue`

These are candidates, not permission to mint them blindly. Before the first stable Commons release, each candidate MUST be checked against relevant standards such as PROV-O, Dublin Core Terms, W3C ORG, FOAF and SKOS. EC SHOULD reuse external vocabulary directly when its semantics are sufficient.

## 4. Governance vocabulary

The following concepts are institutionally owned by Governance and MUST NOT be redefined by Funding, ECL, ECL-PL or another project:

- `GovernanceRule`
- `GovernanceRecord`
- `GovernanceDecision`
- `DecisionClass`
- `Vote` / `Ballot` (one canonical term to be selected before 1.0)
- `ConflictDeclaration`
- `Delegation`
- `Role`
- `Member`
- `MembershipRecord`
- Member lifecycle classes
- governance roles
- decision classes (`OrdinaryApproval`, `QualifiedApproval`, `ConstitutionalAmendment`, `MissionLockedAmendment`, `EmergencyAction`)
- `MissionLock`
- `FoundingPhase`
- `PersistentIdentifierAuthority`
- governance-specific authority and voting properties.

Funding decisions, ECL governance decisions and future domain-specific decisions SHOULD specialize or reference `governance#GovernanceDecision` rather than defining parallel roots.

## 5. Funding vocabulary

Funding owns only concepts whose semantics are funding-specific. Examples:

- `FundingOpportunity`
- `Funder`
- `FundingAcceptanceDecision`
- `CompensationDecision`
- `EndowmentPrincipalWithdrawalDecision`
- `DiversificationPlan`
- `InstitutionalFundingState`
- `FundingPhaseState`
- `FundingDependencyState`
- funding concentration states
- funding opportunity scoring dimensions
- funding amount/currency/restriction properties
- concentration, Endowment and compensation-specific properties.

Funding MUST reuse Governance for governance decisions, decision classes, ballots/votes and conflicts. Funding MUST reuse Commons or an external standard for shared actor/identity/provenance primitives.

## 6. Exergism and ECL

Exergism is authoritative for the canonical philosophical corpus and formal exergic-analysis model. If ECL uses the same analytical variables, it MUST reference the Exergism identities rather than minting independent ECL identities for the same concepts.

The current ECL terms `P`, `A`, `V_ep`, `L`, `O`, `U`, `C`, `S`, `R` and `Ecol` therefore require an explicit pre-1.0 migration decision:

- reuse the corresponding `exergism#` term if semantics are identical; or
- mint an ECL-specific assessment term and declare an explicit mapping if ECL narrows or operationalizes the philosophical concept.

Historical Exergism and ECL release artifacts are not rewritten in place. Namespace migration occurs through a new canonical release.

## 7. ECL-PL

Patent-specific legal concepts remain in `ecl-pl#`. ECL-PL may reuse Commons for shared identity/artifact primitives and reference exact ECL Bundles where its legal model requires it. Similar terminology MUST NOT silently equate copyright/software semantics with patent-law semantics.

## 8. Known pre-1.0 duplicate cleanup

The current draft architecture contains the following duplications or near-duplications that MUST be resolved before stable semantic releases:

| Current terms | Canonical direction |
| --- | --- |
| `funding#Actor`, `urn:ecl:Actor` | Commons/external shared actor primitive |
| `funding#Person`, `urn:ecl:Person` | Commons/external person primitive |
| `funding#Organization`, `urn:ecl:Organization` | Commons/external organization primitive |
| `funding#GovernanceDecision`, `urn:ecl:GovernanceDecision`, current `commons#GovernanceDecision` | `governance#GovernanceDecision` plus domain specializations |
| `funding#Vote` and Governance ballot machinery | one Governance voting concept |
| `funding#ConflictDisclosure`, current `commons#ConflictDeclaration` | `governance#ConflictDeclaration` unless a real semantic distinction is documented |
| Funding string `approvalClass` and Governance `DecisionClass` resources | Governance `DecisionClass` resource |
| `funding#stableId`, `urn:ecl:stableId` | Commons/external shared identity primitive |
| `funding#provenance`, `urn:ecl:provenance`, ECL-PL provenance structures | shared provenance primitives plus domain-specific provenance models |
| `funding#supersedes`, `urn:ecl:supersedes` | Commons/external replacement relation when semantics match |
| `funding#reviewDue`, `urn:ecl:reviewDue` | Commons/shared review scheduling term if semantics match |
| `funding#membershipEconomicShare` | Governance constitutional/membership domain; remove from Funding |
| ECL `P/A/V_ep/L/O/U/C/S/R/Ecol` and Exergism formal variables | Exergism canonical variables or explicit ECL mappings |

Same spelling is not sufficient evidence of equivalence. In particular, ECL `partOf` is direct institutional containment with deliberately constrained inference, while Exergism `partOf` is a structural relation in the philosophical projection; they MUST NOT be merged merely because the local name matches.

## 9. Dependency direction

The intended dependency graph is acyclic:

```text
external standards
       |
       v
   commons#
    /   |   \
   v    v    v
governance#  exergism#
   |  \          |
   v   v         v
funding# ecl# --->(references Exergism)
          |
          v
        ecl-pl#  (where an exact ECL reference is legally required)
```

Normative imports SHOULD remain minimal. Cross-domain references that do not require OWL import semantics MAY use ordinary RDF links instead of `owl:imports`.

## 10. Minting rule

Before minting a new EC term, a project MUST perform this decision sequence:

1. Search the EC term catalog and relevant external vocabularies.
2. Reuse an exact existing term when semantics match.
3. If an existing term is broader, create a domain-specific subclass/subproperty rather than a synonym.
4. If a similar term differs materially, document the distinction and, where useful, an explicit mapping.
5. If the concept is genuinely cross-project, propose it for Commons rather than minting independent project copies.
6. Only then mint a new domain term.

CI SHOULD require an explicit reuse/new-term decision for additions to published EC vocabularies.

## 11. Pre-1.0 compatibility policy

Until a project explicitly declares a semantic release stable, EC may rename, move or remove draft terms in order to normalize the architecture. Git history preserves those experiments; the resolver does not need to retain compatibility aliases for identifiers that were never declared stable.

After a stable IRI is issued:

- it MUST NOT be reassigned;
- incompatible meaning changes are prohibited;
- deprecated identifiers continue to resolve;
- replacement/deprecation relations are explicit;
- immutable versioned artifacts remain byte-stable.

## 12. Resolver publication contract

Each semantic owner defines its terms in its own repository. A future publication manifest SHOULD declare:

- namespace owned by the repository;
- ontology IRI and version;
- terms exported by the release;
- dependencies/imports;
- representations to publish;
- stable record identifiers, where applicable.

`Exergism-Commons/id` validates global namespace ownership, IRI collisions, persistence rules and representation integrity, then publishes the approved artifacts. The resolver MUST NOT be the place where project semantics are authored.

## 13. Catalog requirement

Before EC declares the normalized semantic architecture stable, `id.exergism.org` SHOULD expose a generated global term catalog containing at minimum:

- IRI;
- local name and label;
- RDF type;
- owning repository/namespace;
- description;
- status (`draft`, `stable`, `deprecated`);
- replacement/equivalence/mapping links;
- ontology version;
- declared dependencies.

The catalog is discovery infrastructure, not semantic authority.
