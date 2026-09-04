# CLA Project Schedule

**Version: 0.1-DRAFT**  
**Status: non-operative**

The CLA is intentionally not repository-agnostic. This Schedule records how the proposed organization-level inbound license maps onto the current Exergism Commons repositories without erasing their different legal boundaries.

A machine-readable projection is maintained at `../policy/covered-projects.yaml`.

For deterministic integrity checking, every scheduled repository declares explicit **Schedule material class IDs**. These IDs are part of the Schedule-to-projection binding contract: an operative `covered-projects.yaml` must contain exactly the same repository set and, for every repository, exactly the same material-class ID set. A projection may not silently omit a scheduled repository or scheduled material class merely by recomputing its own hash.

## Open Knowledge family

For this Schedule, the proposed **EC Open Knowledge family** means an outbound family that preserves the freedoms and anti-enclosure constraints in `../OPEN-KNOWLEDGE-POLICY.md`: public knowledge remains inspectable, reproducible, modifiable, forkable and redistributable, with attribution/provenance and share-alike obligations permitted, and EC's own practical Source Form kept available.

The family is a constraint on permitted outbound licensing, not itself an operative copyright license. Each project/material class still requires an exact adopted outbound license and sufficient rights from the actual rightsholders. A Project Schedule cannot retroactively relicense historical material merely by naming the family.

The Open Knowledge family never implies a patent grant, trademark grant, canonical status for a fork, or authority over `id.exergism.org`.

## 1. Exergism

Repository: `Exergism-Commons/exergism`

Schedule material classes:
- `corpus-and-documentation`
- `software-and-tooling`

| Material class | Current target/outbound rule | CLA outbound family |
| --- | --- | --- |
| `content/**`, `books/**`, `formal/**`, `examples/**`, `assets/**`, `ontology.owl`, `manifest.json`, docs/reviews listed in `LICENSE.md` | `CC-BY-SA-4.0` unless file says otherwise | exact target license and successor versions only where that license/project policy permits; this is already compatible with the EC Open Knowledge direction |
| `scripts/**`, `.github/**`, `canonical_content_schema.json` | `Apache-2.0` | exact target license and successor versions permitted by the target license/project policy |
| file with explicit override | file-specific | exact declared target terms; separate review if unclear |

The CLA does not assign copyright and does not authorize the Steward to take the CC BY-SA corpus proprietary.

Patent effect: **none from the CLA**. Any patent license that arises for Apache-2.0 Contributions arises from Apache-2.0 itself according to its terms, not from this CLA.

## 2. Exergic Commons License (ECL)

Repository: `Exergism-Commons/exergic-commons-license`

Schedule material classes:
- `ecl-project-lineage`

Current state relevant to inbound rights:

- `CONTRIBUTING.md` contains a draft contribution-rights grant intended to permit reproduction, modification, publication, distribution, sublicensing and incorporation into current/future ECL versions and related documentation.
- ECL's legal-review specification separately treats chain of title, contribution rights and enforcement authority as a mandatory attack surface.
- the repository is developing a legal instrument and governance/evidence system; this Schedule does not pretend the ECL legal text is itself automatically licensed under ECL.

Proposed CLA outbound family for ECL Contributions:

> **ECL project-purpose + Open Knowledge family** — incorporation, modification, publication and distribution as part of current or future ECL license texts, exact ECL legal artifacts, ECL specifications, governance/evidence records, schemas, tooling, documentation and historical archives that remain part of the ECL project lineage, plus any explicit file-level license already governing Target Material. Public knowledge classes such as dossiers, evidence/claim records, public reviews, ontologies, public Exergism analyses and comparable governance records must remain inside an EC Open Knowledge-compatible outbound family once exact project licensing is adopted.

This family does **not** authorize unrelated proprietary exploitation of a Contribution outside the ECL project lineage, and it does not make ECL itself the outbound license for ECL's public knowledge records.

A key boundary is mandatory:

```text
ECL public evidence / dossiers / ontology / reviews
        -> open, inspectable, contestable knowledge

exact ECL License + exact Schedule + exact Bundle
        -> capability-oriented legal effect for covered software/material
```

A dossier or evidence item has no licensing effect by itself. A Restricted Party under an exact ECL Bundle must not lose the ability, merely because of that restriction, to inspect and challenge the public evidence under the applicable knowledge license.

Patent effect: **none from the CLA**. ECL 0.3-DRAFT itself expressly grants no patent license.

## 3. ECL Patent License (ECL-PL)

Repository: `Exergism-Commons/ecl-patent-license`

Schedule material classes:
- `ecl-pl-project-lineage`

Proposed CLA outbound family:

> **ECL-PL development + Open Knowledge family** — incorporation, modification, publication and distribution as part of current/future ECL-PL architecture, specifications, schemas, compatibility analyses, legal-drafting candidates, validation tooling, evidence/provenance records and historical archives within the ECL-PL project lineage, plus any explicit file-level license already governing Target Material. Public architecture, specification and provenance material should remain in an EC Open Knowledge-compatible family once exact project licensing is adopted.

**Patent effect: none.** This is mandatory. ECL-PL architecture currently requires that contribution to the repository does not itself grant patent rights and that patent grants be separate, express, attributable and immutable.

A future ECL-PL patent grant must use an independently authorized patent instrument. The CLA must never be treated as that instrument. Open licensing of the ECL-PL documentation, schemas or source material does not imply permission to practice any patent claim.

## 4. Organization `.github`

Repository: `Exergism-Commons/.github`

Schedule material classes:
- `organization-profile-and-community-health`

Current repository-wide outbound content license: **not established by this Schedule**.

Proposed CLA coverage, once operative, is limited to organization profile/community-health material intentionally submitted for inclusion. The intended outbound direction for public documentation is the **EC Open Knowledge family**, but until a separate outbound policy is adopted this Schedule must not be read to create one by inference.

## 5. Organization `governance`

Repository: `Exergism-Commons/governance`

Schedule material classes:
- `organization-governance-and-legal-templates`

Current repository-wide outbound content license: **not established by this bootstrap**.

The intended outbound direction for public governance, policy, ontology, machine-readable governance and legal-development documentation is the **EC Open Knowledge family**. `OPEN-KNOWLEDGE-POLICY.md` is itself a draft policy proposal and does not retroactively relicense this repository.

CLA/governance text may be reviewed, forked or reused only to the extent applicable copyright law, an express later license, or other permission currently allows. Before 1.0, Governance should adopt an exact outbound policy that preserves the constitutional anti-enclosure principle while respecting historical rights.

Contributions to this repository made before the CLA itself is operative are governed by the terms/permissions actually applicable at the time; the draft CLA cannot bind itself retroactively.

Patent effect: **none from the CLA**.

## 6. Funding

Repository: `Exergism-Commons/funding`

Schedule material classes:
- `funding-governance-and-semantic-records`

Current repository-wide outbound content license: **unresolved / not established by this Schedule**.

Proposed CLA outbound family:

> **EC Open Knowledge family** for public Funding governance documents, ontologies, schemas, semantic state, machine-readable records and public analytical/documentation material, subject to an exact Funding project decision and rights review. Software/tooling paths must use an explicit software license rather than inheriting a content license by implication.

Funding facts and governance records remain authoritative in the Funding project according to its own adopted process. Open copying of a Funding representation does not transfer authority to make canonical Funding decisions.

Patent effect: **none from the CLA**.

## 7. Identifier resolver / `id.exergism.org`

Repository: `Exergism-Commons/id.exergism-commons.github.io`

Schedule material classes:
- `identifier-resolver-software-and-site`
- `identifier-published-representation-metadata`

The resolver has two different rights surfaces and they must remain separate.

### `identifier-resolver-software-and-site`

Current repository-wide outbound software/content license: **not normalized by this Schedule**.

Proposed CLA outbound family: an explicit software/tooling license for resolver code and deployment material, plus an EC Open Knowledge-compatible family for public explanatory/site documentation where applicable. No content license is inferred for software merely because the resolver serves open knowledge.

### `identifier-published-representation-metadata`

The resolver does not become the copyright or semantic owner of a representation merely by serving it.

Source-project licenses and authority boundaries control the underlying representations. Resolver-local provenance, routing metadata and public explanatory metadata may be placed in the EC Open Knowledge family where EC has the rights to do so.

A mirror or fork may reproduce resolver software/metadata only under the exact applicable licenses. Doing so does not transfer the canonical `id.exergism.org` namespace, EC trademark rights or authority to mint identifiers on behalf of EC.

Patent effect: **none from the CLA**.

## 8. Adding a Covered Project

Adding another repository requires a versioned Schedule update that identifies:

- repository identity;
- material classes/paths where relevant;
- current target/outbound licenses or unresolved status;
- any permitted project-purpose or Open Knowledge family;
- patent effect;
- known third-party/IP constraints; and
- effective date for **future** submissions.

The Schedule material-class IDs for the repository must be updated in the same adopted Schedule version. The machine projection must match those IDs exactly; a missing or extra repository/material class is an integrity failure rather than an editorial difference.

Adding a project does not retroactively expand rights in older Contributions.

## 9. Conflict rule

If this Schedule conflicts with an explicit license notice governing Target Material, maintainers must stop and resolve the conflict rather than silently choosing whichever term is broader.

No automation may infer a patent grant, copyright assignment, trademark grant, canonical authority or new outbound license from this Schedule.
