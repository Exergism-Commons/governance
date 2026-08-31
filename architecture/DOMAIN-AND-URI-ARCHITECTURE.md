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

The proposed hostname allocation is:

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

The following separation remains normative:

- **Exergism** owns its canonical philosophical corpus, formal analytical model, and Exergism ontology projection.
- **ECL** owns ECL-specific knowledge, governance criteria, release bundles, schedules, and copyright/software-license artifacts.
- **ECL-PL** owns any independently released patent-license instrument.
- **Organization governance** owns cross-project stewardship, contributor provenance, institutional process, and shared policy.
- **Registry infrastructure** may record and expose entities, evidence, dossiers, provenance, and review state, but MUST NOT silently convert registry membership into philosophical, governance, or legal conclusions.

A resource being published under `*.exergism.org` MUST NOT, by itself, imply endorsement, restriction, authorship, legal applicability, or canonical philosophical status.

## 4. Persistent identifier architecture

### 4.1 General rule

Persistent semantic identifiers SHOULD be minted under:

`https://id.exergism.org/`

These identifiers MUST NOT expose implementation details such as GitHub repository names, branch names, file extensions, static-site generators, or deployment providers.

### 4.2 Exergism vocabulary

Recommended namespace prefix:

```text
ex: https://id.exergism.org/exergism#
```

Examples:

```text
https://id.exergism.org/exergism#Autonomy
https://id.exergism.org/exergism#Exergy
https://id.exergism.org/exergism#Capture
```

The ontology document identifier SHOULD be distinct from its vocabulary terms:

```text
https://id.exergism.org/ontology/exergism
```

Version IRIs SHOULD be immutable:

```text
https://id.exergism.org/ontology/exergism/0.2.0
```

The unversioned ontology IRI identifies the ontology lineage; a version IRI identifies one immutable released version.

### 4.3 ECL vocabulary

Recommended namespace prefix:

```text
ecl: https://id.exergism.org/ecl#
```

The ECL ontology SHOULD use:

```text
https://id.exergism.org/ontology/ecl
```

with immutable version IRIs such as:

```text
https://id.exergism.org/ontology/ecl/0.2.0
```

Exergism and ECL MUST keep separate term namespaces even where ECL concepts derive from or reference Exergism concepts. Cross-project relationships MUST be explicit RDF/OWL assertions, imports, mappings, or documented dependencies rather than accidental identifier reuse.

### 4.4 Organization-level vocabulary

If Exergism Commons later requires machine-readable organization governance terms, they SHOULD use a separate namespace, for example:

```text
ec: https://id.exergism.org/commons#
```

This namespace SHOULD NOT be created until there is a real organization-level vocabulary to publish.

## 5. Entity and registry identifiers

Large, independently retrievable entity sets SHOULD use slash identifiers rather than one monolithic hash vocabulary.

Recommended form:

```text
https://id.exergism.org/entity/{stable-id}
```

The stable ID SHOULD be immutable and SHOULD NOT depend on a mutable display name. Human-readable aliases may be exposed separately.

Examples of representation URLs may include:

```text
https://registry.exergism.org/entity/{stable-id}
https://registry.exergism.org/dossier/{dossier-id}
```

The identifier and its representation are conceptually distinct. Where server capabilities permit, entity identifiers SHOULD resolve through HTTP redirection and/or content negotiation to an appropriate HTML, JSON-LD, Turtle, or other representation.

A dossier is a reviewable information artifact, not necessarily the identity of the entity it discusses. Entity IDs and dossier IDs therefore SHOULD remain separate.

## 6. Hash versus slash policy

For relatively small vocabularies whose terms are normally distributed together, hash namespaces are preferred:

```text
https://id.exergism.org/exergism#Term
https://id.exergism.org/ecl#Term
```

For potentially large entity sets, dossiers, releases, and independently retrieved records, slash identifiers are preferred:

```text
https://id.exergism.org/entity/...
https://registry.exergism.org/dossier/...
https://specs.exergism.org/ecl/...
```

This follows the general Semantic Web distinction between compact hash vocabularies and independently resolvable resources.

## 7. Released artifacts and mutability

Persistent semantic identity and downloadable release artifacts are different concerns.

Released specifications and legal artifacts SHOULD be published under immutable versioned paths, for example:

```text
https://specs.exergism.org/exergism/0.2.0/
https://specs.exergism.org/ecl/0.3.0/
https://specs.exergism.org/ecl-pl/0.1.0/
```

Machine artifacts may be exposed beneath those paths:

```text
https://specs.exergism.org/exergism/0.2.0/ontology.ttl
https://specs.exergism.org/exergism/0.2.0/ontology.rdf
https://specs.exergism.org/ecl/0.3.0/ecl.owl.ttl
https://specs.exergism.org/ecl/0.3.0/ecl-context.jsonld
```

Once a release path is declared immutable, its bytes MUST NOT be silently replaced. Corrections require a new version or an explicitly versioned erratum mechanism.

Mutable aliases such as `/latest/` MAY exist for convenience but MUST NOT be used where reproducibility or legal reliance requires an immutable artifact.

## 8. Current namespace migrations

### 8.1 Exergism

The current ontology generator uses:

```text
http://www.exergia.org/ns/
```

as its base IRI. That namespace is not aligned with the controlled `exergism.org` domain and SHOULD be replaced before the ontology is treated as stable external infrastructure.

Because Exergism is still on the `0.x` line, the migration SHOULD be made as an explicit breaking semantic change in the next suitable minor release, with release notes recording the old and new namespaces.

Recommended target:

```text
https://id.exergism.org/exergism#
```

The generator, generated ontology, validation tests, examples, documentation, and any serialized references MUST migrate together. The repository MUST NOT change only the generated file or only the generator.

If compatibility with already published old IRIs becomes necessary, a machine-readable mapping MAY be published. The project SHOULD avoid implying that Exergism Commons controls the old hostname if it does not.

### 8.2 ECL

The current ECL ontology uses:

```text
urn:ecl:
```

URNs are location-independent but are not directly Web-dereferenceable. While ECL remains a draft system, migration to the controlled HTTPS namespace SHOULD be evaluated before downstream consumers stabilize around the URN scheme.

Recommended target:

```text
https://id.exergism.org/ecl#
```

Any migration MUST be treated as an explicit ontology-version change and MUST update the JSON-LD context, SHACL shapes, examples, tests, generated data, and documentation consistently.

## 9. Website and hosting architecture

The public website SHOULD be decoupled from semantic identifiers.

A practical initial deployment is:

```text
exergism.org     -> redirect -> www.exergism.org
www.exergism.org -> public site
```

GitHub Pages MAY host the initial public site, but `id.exergism.org` SHOULD be treated as infrastructure whose persistence exceeds any single Pages deployment.

Repository names SHOULD therefore never appear in canonical semantic IDs.

For the identifier service:

- vocabulary hash roots can initially be served statically;
- independently retrievable entity identifiers may later use a redirect/content-negotiation layer;
- the implementation may move between GitHub Pages, a CDN, object storage, a Worker/function layer, or another host without changing issued IDs.

## 10. DNS and security requirements

Before connecting GitHub Pages or another hosting provider, the domain SHOULD be verified with the relevant platform account/organization where supported.

DNS SHOULD avoid broad wildcard records such as `*.exergism.org` unless there is a specific reviewed operational requirement.

Every public HTTP endpoint SHOULD support HTTPS. HSTS MAY be enabled once all required subdomains are confirmed HTTPS-capable.

DNS ownership, registrar recovery, platform verification, and deployment credentials SHOULD be treated as critical infrastructure governance concerns because loss of the domain could compromise persistent identifiers even if Git repositories remain intact.

## 11. Repository responsibilities

The current repositories map naturally to the domain architecture:

| Repository | Primary authority | Public surface |
| --- | --- | --- |
| `exergism` | Canonical Exergism corpus, analytical model, generated ontology | `docs`, `specs`, `id` |
| `exergic-commons-license` | ECL ontology, evidence/governance model, legal artifacts | `docs`, `specs`, `id` |
| `ecl-patent-license` | Separate patent-license architecture | `docs`, `specs` |
| `governance` | Organization-level institutional policy | `governance` |
| `.github` | GitHub organization presentation/defaults | GitHub only; not semantic authority |

A future cross-project registry SHOULD be implemented as a separate repository rather than remaining structurally embedded in ECL if its data model is intended to support Exergism Commons projects independently of ECL.

Suggested repository name:

```text
registry
```

Its scope would be entity identity, dossiers, provenance, source/evidence records, schemas, validation, and neutral reviewed state. ECL-specific governance outcomes would remain owned by ECL.

## 12. Governance versus democracy

The organization-level repository SHOULD remain named `governance`.

"Governance" includes contributor rights, IP provenance, stewardship, domain custody, security responsibilities, policy adoption, conflict handling, succession, and decision procedures. "Democracy" may describe one family of decision mechanisms but is too narrow to name the whole institutional layer.

If democratic decision mechanisms become formalized, they may live under a path such as:

```text
governance/decision-processes/
```

or an equivalent section within the governance repository.

## 13. Implementation order

Recommended sequence:

1. Adopt this architecture as a documented proposal.
2. Verify `exergism.org` at the hosting/platform level before delegating subdomains.
3. Establish the main public website at `www.exergism.org` and apex redirect.
4. Reserve and configure `id.exergism.org` before minting replacement ontology IRIs.
5. Migrate Exergism from `http://www.exergia.org/ns/` as one atomic semantic-version change.
6. Evaluate and, if accepted, migrate ECL from `urn:ecl:` while ECL remains pre-stable.
7. Publish immutable released artifacts under `specs.exergism.org`.
8. Add `docs.exergism.org` and `governance.exergism.org` as their content justifies dedicated sites.
9. Extract a cross-project `registry` only when its schema and ownership boundary are ready.
10. Reserve `api.exergism.org` without publishing an API until an actual supported contract exists.

## 14. Permanence rule

The most important constraint is simple:

> Once Exergism Commons publishes an identifier as persistent, changing hosting technology MUST be easier than changing the identifier.

The domain architecture is therefore a compatibility surface, not merely branding.
