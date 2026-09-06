# Exergism Commons Intellectual-Property Policy

> **Status: 0.1-DRAFT — non-operative until adopted.** This policy is an organization-level framework, not legal advice and not a substitute for the exact license governing a file or release.

## 1. Objectives

Exergism Commons needs enough inbound rights to preserve, improve, release and defend long-lived collaborative projects without turning repository administration into ownership of contributors' work.

The organization therefore follows six design rules:

1. **rights follow actual rightsholders;**
2. **ordinary contribution does not require copyright assignment;**
3. **different project/material classes may have different outbound licenses;**
4. **patent rights are never inferred from copyright contribution or repository participation;**
5. **provenance and authority should be auditable without publishing unnecessary personal data;** and
6. **canonical stewardship must not be used to enclose public knowledge that EC has authority to keep open.**

## 2. Copyright ownership and stewardship

A contributor retains whatever copyright and related rights the contributor owns. If an employer, client, institution or other entity owns the relevant rights, that rightsholder must provide the necessary authorization or execute the applicable entity agreement.

Exergism Commons' role as repository administrator or canonical steward does not itself transfer copyright.

A covered CLA grants a non-exclusive license. It is not a copyright assignment and must not be described as one.

## 3. Target-material licensing controls outbound use

The license already governing the target file/material remains the first outbound rule. The Project Schedule records the applicable material classes and any expressly permitted successor/additional outbound terms.

The organization must not use a general CLA as a hidden mechanism to take CC BY-SA material proprietary, to convert ECL legal-development contributions into unrelated closed products, or to change a project's licensing boundary without the governance process and rights authority required for that change.

For a material class validly designated as EC Public Knowledge, the applicable outbound family must preserve the knowledge freedoms and anti-enclosure requirements in `OPEN-KNOWLEDGE-POLICY.md`. This requirement does not silently change an existing license: the project must have the actual rights and adopted authority needed to apply a compatible outbound license.

A later Project Schedule cannot retroactively add a new outbound licensing option for an earlier Contribution unless the CLA/version accepted for that Contribution already authorized that category of successor license.

## 4. Current mixed-license boundaries

### Exergism

Current repository policy states:

- `content/**`, `books/**`, `formal/**`, `examples/**`, `assets/**`, `ontology.owl`, `manifest.json`, core documentation and reviews: `CC-BY-SA-4.0` unless a file says otherwise;
- `scripts/**`, `.github/**`, and `canonical_content_schema.json`: `Apache-2.0`.

The CLA does not erase this boundary. The content/corpus side is the current reference implementation for EC's open/share-alike knowledge direction.

### ECL

ECL is a license-development and governance project with an existing draft contribution-rights term in `CONTRIBUTING.md`. The project also explicitly treats contributor chain of title and enforcement authority as a legal-review surface.

The organization-level CLA is intended to replace ambiguity with a signed, versioned inbound-rights record for future contributions once adopted. It does not retroactively bind historical contributors.

ECL's software/capability restrictions and the outbound copyright treatment of ECL's own public dossiers, evidence, ontologies, reviews and legal-development materials are distinct legal questions. Applying ECL to software must not be inferred to restrict access to the public evidence used by ECL governance.

### ECL-PL

ECL-PL's architecture requires patent grants to be express, attributable and independently versioned. The CLA therefore contains **no patent grant** and does not make a contributor a Patent Licensor.

Open licensing of ECL-PL architecture, specifications, schemas, legal-development material or provenance records would not itself grant any patent right.

### Funding

The Funding repository currently has no organization-level outbound policy established by this Governance draft. Public Funding governance records, ontologies and semantic state are intended candidates for the EC Open Knowledge family, but an exact project decision must identify the material classes, rights basis and outbound terms before that statement becomes legally operative.

### Identifier infrastructure

`id.exergism.org` is a resolver and persistence surface, not a relicensing authority. A representation served through the resolver retains the source project's license and semantic authority boundary.

Resolver code, deployment tooling, site assets and published semantic representations are different material classes and should not be collapsed into one inferred license.

### Governance and `.github`

This bootstrap does not invent a repository-wide outbound copyright license for these repositories. Any such policy should be adopted explicitly rather than inferred from neighboring projects.

Public Governance documents and community-health material are intended candidates for an EC open/share-alike knowledge family once rights and project-level adoption are resolved. Draft policy text does not retroactively relicense itself or historical contributions merely by expressing that target.

## 5. Patents

The organization-level CLA grants no patent rights.

Patent rights may nevertheless arise from a separate source, for example:

- a target/outbound software license that itself contains a contributor patent clause (such as Apache-2.0 for material actually governed by that license);
- an independently executed patent agreement; or
- a future exact ECL-PL PatentGrantBundle.

Those grants stand on their own terms. The CLA neither expands nor contracts them.

## 6. Trademarks, names and identity

No trademark, trade name, logo, certification mark or right of endorsement is granted by the CLA except the narrow permission reasonably necessary to preserve factual attribution and project history.

Use of the names `Exergism`, `Exergism Commons`, `Exergic Commons License`, `ECL` or related marks should be governed by a separate trademark/identity policy if and when the organization develops one.

Open knowledge rights do not authorize a fork to represent itself as an official EC artifact. Conversely, identity policy should not be used to prohibit truthful attribution, criticism, compatibility statements or lawful forks merely because they are not canonical.

## 7. Moral and personality rights

Where applicable law permits consent or waiver, contributors permit the ordinary editing, adaptation, translation, combination and technical transformation needed for covered project development. The policy does not purport to waive moral rights that applicable law makes non-waivable.

Attribution requirements remain governed by the applicable outbound license and project policy.

## 8. Third-party material

A contributor must not present third-party content as their own Contribution.

Third-party material should be:

1. clearly identified;
2. traceable to its source and rightsholder where reasonably possible;
3. accompanied by its exact license/permission basis;
4. segregated where that improves provenance; and
5. accepted only after compatibility review appropriate to the target material.

A CLA signed by the submitter cannot manufacture rights the submitter does not have.

Open licensing of an EC dossier, annotation, ontology or structured record does not imply that EC owns or relicenses every article, image, paper, report, dataset or other third-party work cited by that record.

## 9. AI-assisted contributions

AI assistance does not change the provenance standard. A contributor may grant only rights the contributor actually owns or controls and must not represent uncertain third-party or machine-generated provenance as settled human authorship.

The detailed policy is in `cla/AI-ASSISTED-CONTRIBUTIONS.md`.

## 10. Enforcement and administration

The CLA authorizes the legal steward to administer the licenses it is entitled to grant and, where applicable law permits, to act regarding compliance with those grants. It does **not** falsely represent that a non-exclusive CLA automatically transfers copyright standing, exclusive rights or every contributor's independent cause of action.

Where enforcement requires participation of an underlying rightsholder, the organization should request that cooperation and document authority before making a claim.

The Steward must not use administration authority to impose restrictions that are absent from the applicable outbound license or to present canonicality rules as if they were exclusive copyright rights.

## 11. Successor stewardship

CLA rights may move only through the agreement's controlled successor mechanism. A successor must be publicly identified, legally competent, assume the CLA's obligations in writing, and preserve the applicable outbound constraints.

For material validly designated as EC Public Knowledge, successor stewardship must also preserve the applicable open/share-alike and anti-enclosure constraints.

Repository transfer, account ownership, an organization rename or acquisition of an administrator account is not by itself a legal assignment of CLA rights.

## 12. Legacy contributions

Adopting a CLA cannot retroactively bind historical contributors. Historical rights must be supported by the license or contribution terms in force when the contribution was made, another valid grant, or a later voluntary confirmation from the actual rightsholder.

An Open Knowledge policy likewise cannot cure missing historical rights merely by declaring a preferred future license.

See `cla/LEGACY-CONTRIBUTIONS.md`.

## 13. Records and privacy

The organization should retain enough evidence to establish:

- who accepted which agreement version;
- in what legal capacity;
- which GitHub identities/emails were linked for contribution checks;
- when acceptance became effective; and
- which Project Schedule applied.

Public records should expose only what is operationally useful. Full legal names, addresses, signatures and similar identity evidence should not be placed in a public repository merely for convenience.

The Knowledge Commons principle does not require publication of private identity evidence, credentials, security secrets or other records validly protected by privacy, safety, privilege, confidentiality or mandatory law.

## 14. Open Knowledge and anti-enclosure

`OPEN-KNOWLEDGE-POLICY.md` defines the proposed detailed implementation of the constitutional Knowledge Commons principle.

The IP layer must preserve these distinctions:

```text
public knowledge freedom
        !=
canonical EC status
        !=
software/capability license
        !=
patent grant
        !=
trademark/endorsement right
```

Where EC has authority over Public Knowledge, the target is a genuine open/share-alike outbound regime that permits inspection, reproduction, modification, forks and redistribution and keeps EC's own practical Source Form available in open, reconstructable formats.

The Constitution mission-locks that anti-enclosure principle rather than a specific license brand. Project-level policy remains responsible for choosing exact legally compatible licenses and for proving the authority to apply them.
