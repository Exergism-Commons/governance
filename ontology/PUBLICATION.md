# Governance semantic publication contract

This directory is the authoritative semantic source for the organization-level `commons#` and `governance#` vocabularies.

## Two independent version axes

The ontology serialization and the institutional governance release are deliberately versioned separately.

- `owl:versionInfo` / `owl:versionIRI` identify the **ontology projection**. The current pre-1.0 ontology version is `0.1-PRE2`.
- `ecg:governanceVersion` identifies the **institutional governance rules/release applicable to a governance record**. The current institutional version is `0.1-DRAFT`.

A downstream record MUST NOT place an ontology version such as `0.1-PRE2` in `ecg:governanceVersion` merely because it uses that ontology serialization.

## Versioned OWL closure

The current ontology IRIs are mutable discovery identifiers:

- `https://id.exergism.org/ontology/commons`
- `https://id.exergism.org/ontology/governance`

The `0.1-PRE2` immutable version IRIs are:

- `https://id.exergism.org/ontology/commons/0.1-PRE2`
- `https://id.exergism.org/ontology/governance/0.1-PRE2`

`governance.ttl` imports the versioned Commons IRI. Therefore the authoritative owning repository, rather than the identifier resolver, defines the frozen dependency closure. A resolver publication of a version IRI must serve the authoritative bytes from this repository without semantic rewriting.

## Downstream authority

`downstream-authority.json` is a fail-closed projection for consumers such as Funding and the identifier service. It exists because ontology membership and structural SHACL conformance do not prove institutional authority.

While `policy/governance-status.json` remains `operative: false`:

- downstream domains may model proposed records and approval requirements;
- they must not claim an approved or operative institutional decision merely because `decisionClass` names an approval class;
- `EmergencyAction` is unavailable unless an emergency policy/rule is actually adopted;
- a downstream must fail closed if it cannot validate the authority evidence required by the applicable Governance release.

The canonical Governance validator and human/adopted policy remain authoritative for institutional validity. `id.exergism.org` is a publication/dereferencing surface and must not rewrite these semantics.
