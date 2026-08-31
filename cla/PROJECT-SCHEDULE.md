# CLA Project Schedule

**Version: 0.1-DRAFT**  
**Status: non-operative**

The CLA is intentionally not repository-agnostic. This Schedule records how the proposed organization-level inbound license maps onto the current Exergism Commons repositories without erasing their different legal boundaries.

A machine-readable projection is maintained at `../policy/covered-projects.yaml`.

## 1. Exergism

Repository: `Exergism-Commons/exergism`

| Material class | Current target/outbound rule | CLA outbound family |
| --- | --- | --- |
| `content/**`, `books/**`, `formal/**`, `examples/**`, `assets/**`, `ontology.owl`, `manifest.json`, docs/reviews listed in `LICENSE.md` | `CC-BY-SA-4.0` unless file says otherwise | exact target license and successor versions only where that license/project policy permits |
| `scripts/**`, `.github/**`, `canonical_content_schema.json` | `Apache-2.0` | exact target license and successor versions permitted by the target license/project policy |
| file with explicit override | file-specific | exact declared target terms; separate review if unclear |

The CLA does not assign copyright and does not authorize the Steward to take the CC BY-SA corpus proprietary.

Patent effect: **none from the CLA**. Any patent license that arises for Apache-2.0 Contributions arises from Apache-2.0 itself according to its terms, not from this CLA.

## 2. Exergic Commons License (ECL)

Repository: `Exergism-Commons/exergic-commons-license`

Current state relevant to inbound rights:

- `CONTRIBUTING.md` contains a draft contribution-rights grant intended to permit reproduction, modification, publication, distribution, sublicensing and incorporation into current/future ECL versions and related documentation.
- ECL's legal-review specification separately treats chain of title, contribution rights and enforcement authority as a mandatory attack surface.
- the repository is developing a legal instrument and governance/evidence system; this Schedule does not pretend the ECL legal text is itself automatically licensed under ECL.

Proposed CLA outbound family for ECL Contributions:

> **ECL project-purpose family** — incorporation, modification, publication and distribution as part of current or future ECL license texts, exact ECL legal artifacts, ECL specifications, governance/evidence records, schemas, tooling, documentation and historical archives that remain part of the ECL project lineage, plus any explicit file-level license already governing Target Material.

This family does **not** authorize unrelated proprietary exploitation of a Contribution outside the ECL project lineage.

Patent effect: **none from the CLA**. ECL 0.3-DRAFT itself expressly grants no patent license.

## 3. ECL Patent License (ECL-PL)

Repository: `Exergism-Commons/ecl-patent-license`

Proposed CLA outbound family:

> **ECL-PL development family** — incorporation, modification, publication and distribution as part of current/future ECL-PL architecture, specifications, schemas, compatibility analyses, legal-drafting candidates, validation tooling, evidence/provenance records and historical archives within the ECL-PL project lineage, plus any explicit file-level license already governing Target Material.

**Patent effect: none.** This is mandatory. ECL-PL architecture currently requires that contribution to the repository does not itself grant patent rights and that patent grants be separate, express, attributable and immutable.

A future ECL-PL patent grant must use an independently authorized patent instrument. The CLA must never be treated as that instrument.

## 4. Organization `.github`

Repository: `Exergism-Commons/.github`

Current repository-wide outbound content license: **not established by this Schedule**.

Proposed CLA coverage, once operative, is limited to organization profile/community-health material intentionally submitted for inclusion. Until a separate outbound policy is adopted, this Schedule must not be read to create one by inference.

## 5. Organization `governance`

Repository: `Exergism-Commons/governance`

Current repository-wide outbound content license: **not established by this bootstrap**.

CLA/governance text may be reviewed, forked or reused only to the extent applicable copyright law, an express later license, or other permission allows. A separate decision should be made before 1.0 about whether governance documentation and legal templates should use a reuse license and, if so, which one.

Contributions to this repository made before the CLA itself is operative are governed by the terms/permissions actually applicable at the time; the draft CLA cannot bind itself retroactively.

## 6. Adding a Covered Project

Adding another repository requires a versioned Schedule update that identifies:

- repository identity;
- material classes/paths where relevant;
- current target/outbound licenses or unresolved status;
- any permitted project-purpose family;
- patent effect;
- known third-party/IP constraints; and
- effective date for **future** submissions.

Adding a project does not retroactively expand rights in older Contributions.

## 7. Conflict rule

If this Schedule conflicts with an explicit license notice governing Target Material, maintainers must stop and resolve the conflict rather than silently choosing whichever term is broader.

No automation may infer a patent grant, copyright assignment or new outbound license from this Schedule.
