# Exergism Commons Domain and Persistent URI Architecture

**Status:** Proposed / non-operative architecture

**Domain:** `exergism.org`

This document defines the proposed public-domain, identifier, namespace, and release-URL architecture for Exergism Commons. It is an infrastructure and governance boundary document. It does not transfer authority, copyright, patent rights, or legal effect between repositories or projects.

## 1. Goals

The architecture SHOULD:

1. keep public identifiers under a domain controlled by Exergism Commons;
2. keep philosophical, analytical, governance, copyright-license, patent-license, registry, and institutional layers distinguishable;
3. make machine identifiers dereferenceable where practical;
4. keep stable identifiers independent from GitHub repository names and hosting technology;
5. permit future migration away from GitHub Pages without changing published identifiers;
6. provide immutable URLs for released artifacts while allowing living documentation to evolve;
7. avoid assigning legal or philosophical authority merely because resources share the `exergism.org` domain.

## 2. Domain roles

| Hostname | Role | Stability expectation |
| --- | --- | --- |
| `www.exergism.org` | Main public/institutional website | Stable public entry point |
| `exergism.org` | Short apex entry point; redirect to the main public site | Stable |
| `id.exergism.org` | Persistent semantic identifiers and ontology namespace roots | Highest stability |
| `docs.exergism.org` | Living human-readable documentation | Stable hostname; content may evolve |
| `specs.exergism.org` | Versioned specifications, schemas, legal artifacts, and release documents | Released paths immutable |
| `governance.exergism.org` | Organization-level governance and institutional policies | Stable hostname; policy status explicit |
| `registry.exergism.org` | Cross-project public registry, dossiers, entity records, and provenance views | Stable record identifiers; mutable reviewed views allowed |
| `api.exergism.org` | Future programmatic API surface | Reserved until an API exists |

Additional hostnames SHOULD NOT be created merely to mirror repository names. A hostname exists for a stable public responsibility, not for every implementation component.

## 3. Authority follows the project, not the hostname

The common domain is infrastructure. It is not a common authority namespace.

- **Exergism** owns its canonical philosophical corpus, formal analytical model, and Exergism ontology projection.
- **ECL** owns ECL-specific knowledge, governance criteria, release bundles, schedules, and copyright/software-license artifacts.
- **ECL-PL** owns any independently released patent-license instrument.
- **Organization governance** owns cross-project stewardship, contributor provenance, institutional process, and shared policy.
- **Funding** owns funding-domain records and implementations while consuming organization-level governance concepts where declared.
- **Registry infrastructure** may record and expose entities, evidence, dossiers, provenance, and review state, but MUST NOT silently convert registry membership into philosophical, governance, or legal conclusions.

A resource being published under `*.exergism.org` MUST NOT, by itself, imply endorsement, restriction, authorship, legal applicability, or canonical philosophical status.

## 4. Persistent identifier architecture

Persistent semantic identifiers SHOULD be minted under `https://id.exergism.org/` and MUST NOT expose implementation details such as repository names, branches, file extensions, static-site generators, or deployment providers.

Reserved project vocabulary roots are:

```text
ex:  https://id.exergism.org/exergism#
ecl: https://id.exergism.org/ecl#
ec:  https://id.exergism.org/commons#
```

Ontology document identifiers are distinct from vocabulary terms:

```text
https://id.exergism.org/ontology/exergism
https://id.exergism.org/ontology/ecl
https://id.exergism.org/ontology/commons
https://id.exergism.org/ontology/funding
```

Version IRIs SHOULD be immutable. Cross-project relationships MUST be explicit assertions, mappings, imports, or documented dependencies rather than accidental identifier reuse.

The `commons#` namespace is the organization-level vocabulary. Minting a term there does not make a policy operative; operativity is governed by the applicable adoption/status record.

## 5. Entity and registry identifiers

Large independently retrievable entity sets SHOULD use slash identifiers rather than one monolithic hash vocabulary:

```text
https://id.exergism.org/entity/{stable-id}
```

Stable IDs SHOULD be immutable and SHOULD NOT depend on a mutable display name. Entity IDs and dossier IDs remain distinct because a dossier is a reviewable information artifact, not the entity itself.

## 6. Released artifacts and mutability

Released specifications and legal artifacts SHOULD be published under immutable versioned paths, for example:

```text
https://specs.exergism.org/exergism/0.2.0/
https://specs.exergism.org/ecl/0.3.0/
https://specs.exergism.org/ecl-pl/0.1.0/
https://specs.exergism.org/governance/0.1.0/
```

Once a release path is declared immutable, its bytes MUST NOT be silently replaced. Corrections require a new version or an explicitly versioned erratum mechanism. Mutable aliases such as `/latest/` MAY exist for convenience but MUST NOT be used where reproducibility or legal reliance requires an immutable artifact.

## 7. Namespace migrations

Exergism currently needs an explicit release migration away from its historical `http://www.exergia.org/ns/` namespace before the `exergism#` namespace becomes its canonical released namespace. ECL similarly must treat any migration from `urn:ecl:` as an explicit ontology-version change. Historical artifacts are not silently rewritten.

## 8. Website and hosting architecture

The public website is presentation infrastructure and SHOULD remain decoupled from semantic identifiers. Repository names SHOULD never appear in canonical semantic IDs.

`id.exergism.org` is infrastructure whose persistence must exceed any single hosting deployment. Vocabulary roots may be served statically; independently retrievable identifiers may use redirects or content negotiation.

## 9. DNS and security requirements

DNS ownership, registrar recovery, platform verification, deployment credentials, and identifier-service recovery are critical infrastructure governance concerns. Broad wildcard records SHOULD be avoided unless specifically reviewed. Public endpoints SHOULD support HTTPS.

Transfers of the apex domain, persistent identifier authority, registrar custody, or equivalent recovery control MUST require organization-level qualified approval once governance becomes operative.

## 10. Repository responsibilities

| Repository | Primary authority | Public surface |
| --- | --- | --- |
| `exergism` | Canonical Exergism corpus, analytical model, generated ontology | `docs`, `specs`, `id` |
| `exergic-commons-license` | ECL ontology, evidence/governance model, legal artifacts | `docs`, `specs`, `id` |
| `ecl-patent-license` | Separate patent-license architecture | `docs`, `specs` |
| `governance` | Organization-level institutional policy and authority vocabulary | `governance`, `id` |
| `funding` | Funding-domain strategy, records and executable policy subset | `funding`, `id` |
| `.github` | GitHub organization presentation/defaults | GitHub only; not semantic authority |

A future cross-project registry SHOULD remain separate from ECL if its data model is intended to serve multiple EC projects independently.

## 11. Governance versus democracy

The organization-level repository remains `governance`. Democratic mechanisms are one subset of governance alongside contributor rights, IP provenance, stewardship, domain custody, security, policy adoption, conflicts, succession, delegation, and decision procedures.

## 12. Permanence rule

> Once Exergism Commons publishes an identifier as persistent, changing hosting technology MUST be easier than changing the identifier.

The domain architecture is therefore a compatibility and institutional-custody surface, not merely branding.
