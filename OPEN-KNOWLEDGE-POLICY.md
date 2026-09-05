# Exergism Commons Open Knowledge Policy

> **Status: 0.1-DRAFT — non-operative until adopted.** This policy defines the proposed organization-level treatment of public knowledge stewarded by Exergism Commons (EC). It does not itself relicense historical material, override an existing file/release license, create a patent grant, create trademark rights, or manufacture rights EC does not possess.

## 1. Purpose

Exergism Commons exists to steward a commons, not to manufacture artificial scarcity over knowledge.

The policy therefore separates four things that must not be conflated:

1. **knowledge freedom** — the ability to inspect, study, reproduce, modify, fork and redistribute public knowledge;
2. **canonicality** — whether an artifact belongs to the official EC-maintained lineage;
3. **capability licensing** — the legal conditions governing software, implementations or other operational capabilities; and
4. **institutional identity** — names, marks, domains and representations of endorsement or official status.

The governing principle is:

> **Canonicality is not exclusivity.**

A work may be freely copied and forked without the fork becoming an official EC artifact. Conversely, EC's stewardship of a canonical artifact does not create a right to prevent others from studying or continuing the underlying public knowledge where the relevant rights permit EC to license that freedom.

## 2. Public Knowledge

For this policy, **EC Public Knowledge** means knowledge material that EC or an EC project intentionally publishes as part of the commons and for which the relevant rightsholders have granted, or are legally able to grant, the permissions required by the applicable outbound terms.

It may include, depending on the project and exact file-level policy:

- philosophical and formal corpus material;
- governance policies and public decision records;
- ontologies, vocabularies, schemas and semantic models;
- RDF, JSON-LD, Turtle, JSON, YAML and other structured knowledge representations;
- dossiers, evidence records, claims, reviews and public analytical records;
- public Funding governance records;
- specifications and explanatory documentation;
- public legal-development materials, including draft license architecture and rationale; and
- public metadata needed to reconstruct provenance, versions and canonical relationships.

A repository location alone does not classify every byte in that repository as Public Knowledge.

## 3. Exclusions and protected material

The Public Knowledge rule does not require publication or relicensing of material that EC cannot or should not lawfully expose, including:

- personal data whose publication is unnecessary or unlawful;
- private signatures, identity evidence, addresses, credentials, recovery material or security secrets;
- embargoed vulnerability details where temporary restriction is reasonably necessary to prevent concrete harm;
- privileged, confidential or legally protected records;
- third-party material that EC lacks authority to relicense;
- material subject to a binding legal restriction; and
- internal records whose confidentiality is justified by an adopted privacy, security, employment, procurement or legal process.

An exclusion must not be used as a pretext to privatize the public knowledge layer. Where only part of a record is protected, EC should publish the separable public portion with provenance and an intelligible explanation of the omission where lawful and safe.

## 4. Protected knowledge freedoms

Where EC or the relevant rightsholders possess the necessary rights, EC Public Knowledge should be published under terms that permit anyone, including critics, competitors and entities affected by EC decisions, to:

- access and inspect it;
- reproduce it;
- study and analyze it;
- transform, annotate and modify it;
- create independent forks and competing interpretations;
- redistribute original and modified versions;
- combine it with other compatible material; and
- use it for commercial or non-commercial purposes, subject only to the applicable attribution, provenance and share-alike/open-knowledge conditions.

EC must not condition these knowledge freedoms merely on nationality, ideology, political alignment, membership, donation, employment, institutional affiliation or agreement with EC conclusions.

This rule is deliberately distinct from ECL capability restrictions. A party or project may be restricted under an exact ECL Bundle while remaining fully entitled to inspect, copy, challenge and redistribute the public evidence and knowledge used to reach that governance outcome under the applicable knowledge license.

## 5. Anti-enclosure

To the extent EC controls the relevant rights or infrastructure, EC must not use copyright, sui generis database rights, contract, access control, digital-rights-management measures, repository administration, API exclusivity or technical obscurity to create artificial scarcity over EC Public Knowledge.

EC may charge for genuine services, physical media, hosting, certification, support or other lawful value-added activity. Such charging must not be used to withdraw an otherwise public canonical source merely to create exclusive access to the knowledge itself.

A future decision to make an established Public Knowledge class materially less copyable, less forkable or less redistributable is a Mission-Lock matter under the Constitution when it would weaken the constitutional anti-enclosure invariant.

## 6. Source Form Availability

For EC's own publication of Public Knowledge, a rendered page, PDF, visualization or API response is not enough when a practical editable source form exists.

EC should publish the **Source Form**: the preferred or canonical form for editing, validating and reconstructing the material. Depending on the artifact, that may include Markdown, Turtle, JSON-LD, JSON, YAML, OWL, CSV, source schemas, source code or another documented open format.

The source form should be:

- versioned;
- retrievable without proprietary software where reasonably possible;
- documented sufficiently for independent reconstruction;
- linked to rendered or convenience representations;
- attributable to an exact release, commit or content identity where the project uses immutable publication; and
- clonable/exportable rather than available only through an opaque hosted interface.

This is an institutional publication duty imposed on EC. It does not by itself create an obligation on third parties beyond the obligations of the exact outbound license governing their copy. If EC wants downstream publication of preferred source form to be legally mandatory for a particular material class, the applicable outbound license must actually impose that requirement.

## 7. Canonicality, forks and provenance

Copying or modifying an EC artifact does not make the copy canonical.

A canonical EC artifact is one whose status is established by the competent project's adopted release/governance process. Canonicality may be evidenced by repository lineage, immutable releases, hashes, signed/adopted records and persistent identifiers.

Forks are legitimate and should be technically possible. A fork may describe its provenance and relationship to EC but must not falsely represent itself as an official EC release or decision.

Persistent identifiers under `id.exergism.org` identify resources according to the EC persistence contract. The ability to copy the representation of a resource does not transfer control of the canonical namespace or authorize another party to mint identifiers on behalf of EC.

## 8. Licensing implementation

The Constitution protects the **open-knowledge and anti-enclosure principle**, not a particular license brand or version.

The proposed default implementation is:

- copyrightable public corpus, ontology documentation, governance documentation and comparable knowledge material: a genuine open/share-alike content license, with **CC BY-SA 4.0** as the current baseline candidate where compatible with the material and rights history;
- structured databases or database-heavy corpora: an explicit open-data/share-alike license where needed, with **ODbL** available for project-specific consideration when database-source obligations are materially important;
- software and technical tooling: the project's explicit software license, not a content license inferred from neighboring knowledge material;
- third-party content: its own exact license or permission basis; and
- files with explicit notices: the exact file-level terms control.

No organization-level policy may silently replace an already applicable outbound license or relicense historical contributions without sufficient authority from the actual rightsholders.

## 9. Exergism

Exergism already implements the intended separation:

- its corpus/documentation layer is published under `CC-BY-SA-4.0` unless a file states otherwise; and
- its software/technical tooling layer is published under `Apache-2.0` according to its repository policy.

The Open Knowledge Policy does not make ECL inherit into Exergism and does not change Exergism's project-level canonical authority.

## 10. ECL, dossiers and governance evidence

ECL is a capability-oriented software-license project. The exact ECL License and exact Restricted Parties Schedule contained in an exact ECL Bundle govern the rights granted in ECL-covered software/material to the extent the relevant Licensor controls those rights.

That legal effect is separate from the public-knowledge status of ECL's supporting knowledge system.

In particular:

- dossiers, evidence records, claims, public reviews, ontologies and public Exergism analyses should be treated as Public Knowledge once an exact compatible outbound license is validly applied;
- a dossier, evidence item, ontology inference or current registry view has no licensing effect merely because it exists;
- an entity affected by an ECL decision must remain able to inspect, copy and challenge the public evidence under the applicable knowledge license;
- exact Schedules and ECL legal texts may be copied and analyzed as documents under whatever explicit outbound terms are validly adopted for those artifacts; and
- copying or modifying an ECL legal/governance artifact does not make the modified artifact an EC-canonical ECL release or give it legal effect in an existing ECL Bundle.

The project must preserve the existing separation between mutable knowledge/governance and immutable operative legal artifacts.

## 11. ECL-PL and patent rights

ECL-PL architecture, specifications, schemas, legal-development material and public provenance records may be treated as Public Knowledge under an adopted outbound policy.

No such publication grants a patent right.

Patent rights remain separate and may arise only from an express, attributable and authorized patent instrument such as a future exact ECL-PL `PatentGrantBundle`, or from another independent legal basis. Publication, contribution, source availability, copying a manifest or operating a mirror must never be used to infer patent authority.

## 12. Funding, Governance and identifier infrastructure

Public Funding governance records, public organization-governance records and their semantic projections should follow this policy once their project-specific outbound terms are validly adopted.

`id.exergism.org` is a resolver and persistence surface, not a relicensing authority. Serving a representation through the resolver does not replace the source project's license, provenance or semantic authority.

Resolver software, deployment tooling and website code remain software/material classes requiring their own explicit outbound license. Published semantic representations retain the license and authority boundary of the source material they represent.

## 13. Third-party evidence and quotations

Open publication of an EC dossier does not imply that EC owns every source cited by the dossier.

EC-authored synthesis, annotations, structured records and database rights may be licensed under EC's outbound terms only to the extent the relevant rightsholders possess those rights. External articles, photographs, papers, reports, datasets and other third-party works retain their independent rights.

Public knowledge records should therefore preserve machine-readable provenance where practical, including source identity, locator, retrieval/as-of information, license/permission basis where known, and a distinction between EC-authored assertions and externally authored source material.

## 14. Contributor rights and the CLA

Contributors retain the rights they own unless an express valid transfer says otherwise.

The organization-level CLA is an inbound-rights instrument, not a mechanism for enclosure. For project/material classes designated for the EC Open Knowledge family, the CLA and Project Schedule should give the Steward enough non-exclusive authority to publish, preserve, modify and relicense within a defined open/share-alike successor family while preventing unrelated proprietary conversion.

The CLA does not create a patent grant. It cannot manufacture rights in third-party material, bind historical contributors retroactively, or erase an existing share-alike obligation.

## 15. Marks and institutional identity

Open knowledge rights do not grant trademark rights or a right of endorsement.

EC may protect names, logos, certification indicators and other source-identifying marks against confusion while still allowing unrestricted truthful reference, attribution, criticism and compatibility statements to the extent permitted by law.

Trademark/identity policy must not be used as a disguised prohibition on lawful forks or factual statements that a fork derives from EC material.

## 16. Non-retroactivity and adoption

This draft does not itself change the license of any current repository or historical artifact.

Project adoption must identify:

- the material classes being placed in the Open Knowledge family;
- the exact outbound license for each class;
- the rightsholder/chain-of-title basis sufficient for that grant;
- treatment of third-party material;
- source-form publication requirements;
- whether historical material can be covered or only future contributions/releases; and
- the effective release or decision record.

Where historical rights are uncertain, EC should preserve public availability under the rights already granted and seek voluntary confirmation rather than pretending a later governance vote can create missing permissions.

## 17. Machine-readable projection

The draft machine projection is `policy/open-knowledge-status.json`.

Machine state may describe scope, candidate license families and publication requirements, but it cannot itself relicense a work, create a patent grant, transfer a trademark or establish canonical authority. Those effects require the applicable rightsholder grants, project release rules and adopted governance records.
