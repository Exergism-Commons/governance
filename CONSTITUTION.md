# Exergism Commons Constitutional Framework

> **Status: 0.1-DRAFT — non-operative.** This document defines the proposed organization-level constitutional model for Exergism Commons (EC). It does not create a legal entity, membership right, fiduciary authority, contractual power, or operative decision merely by being present in Git.

## 1. Purpose

Exergism Commons exists to steward a durable, contestable and anti-capture commons around Exergism and projects that explicitly depend on it, while preserving the authority boundaries of each canonical project.

Organization governance exists to answer questions that no project repository should answer for itself: institutional authority, membership, voting, conflicts, delegation, treasury authority, domain custody, contributor-rights administration, succession and adoption of shared policy.

## 2. Constitutional principles

EC governance is based on the following constraints:

1. **Mission before ownership.** Membership, contribution or administration does not create an economic ownership share in EC assets.
2. **No silent authority.** Repository access, maintainer status, RDF inference, funding, employment or contribution does not by itself create institutional authority.
3. **Rights remain attributable.** Copyright, patent and contractual rights remain with their actual rightsholders except where expressly granted.
4. **Anti-capture.** No donor, funder, employer, maintainer, founder, service provider or single project may obtain organization-wide control merely through resources or technical position.
5. **Conflict exclusion.** A person does not substantively vote on a decision whose primary purpose is to determine that person's own compensation, direct private benefit, claim or sanction.
6. **Reproducibility.** Material institutional decisions should be versioned, attributable and machine-readable where practical.
7. **Human authority controls machine enforcement.** Schemas, SHACL, CI and automation may enforce adopted rules but cannot create authority absent a valid institutional act.
8. **Non-retroactivity.** Later policies do not silently rewrite historical releases, grants, contribution terms or completed decisions.
9. **Subsidiarity.** Organization governance acts only on organization-level matters or authority explicitly delegated to it.
10. **Contestability.** Material decisions must preserve a documented route for objection, contrary evidence and correction.

## 3. Legal identity and bootstrap state

Until a legally competent EC entity is constituted and identified in an adopted institutional record:

- EC governance remains in **bootstrap / non-operative institutional status**;
- no repository document may falsely represent the GitHub organization itself as a legal person;
- no draft role may execute contracts merely by virtue of this document;
- draft votes may be used to test procedure but are not represented as legally binding institutional acts; and
- legally consequential instruments such as a CLA remain blocked by their own adoption requirements.

A future legal-entity adoption decision MUST identify at least the entity name, jurisdiction, registration identity where applicable, governing constitutional instrument, effective date, competent signatories and relationship between the legal entity and the public Exergism Commons project.

## 4. Membership

### 4.1 Membership is governance status, not property

Membership may confer participation and voting rights under adopted rules. It does not confer a transferable share, dividend right, claim on the Endowment, residual claim on Treasury assets or ownership interest in EC.

### 4.2 Member registry

Operative membership MUST be recorded in a controlled registry with stable identifiers and effective dates. Public projections may omit private identity evidence.

A GitHub organization member, repository collaborator, CLA signatory, donor, employee or contractor is not automatically an EC Member.

### 4.3 Admission and termination

Detailed admission, suspension, resignation and termination procedures require a separately adopted membership policy. Termination for cause must provide notice, reasons and a contestable process proportionate to the consequences.

## 5. Institutional roles

The constitutional vocabulary distinguishes at least:

- **Member** — person with the governance rights recorded by the membership policy;
- **Steward** — role responsible for institutional continuity and execution of valid decisions within delegated authority;
- **Treasurer** — role responsible for treasury administration and reporting, not unilateral ownership or appropriation;
- **Domain Custodian** — role entrusted with operational custody of `exergism.org`, registrar access and identifier infrastructure;
- **Repository Maintainer** — technical role over one or more repositories; technical permissions do not imply broader institutional power;
- **Auditor / Reviewer** — role that can independently review records, controls or decisions without acquiring executive authority.

One person may hold multiple roles only where conflicts and concentration rules allow it. Role assignments are revocable governance delegations, not personal property.

## 6. Decision classes

### 6.1 Delegated action

A delegated role may perform routine acts expressly within an adopted delegation. Delegated action may never be used to amend the Constitution, create new constitutional authority, distribute EC assets to members, transfer organization-wide IP ownership, dispose of Endowment principal, transfer persistent-domain control, or bypass an approval class required by policy.

### 6.2 Ordinary Approval

The proposed default for ordinary organization-level decisions is:

- quorum: more than 50% of non-conflicted eligible voters;
- approval: more votes in favour than against among valid votes cast;
- abstentions do not count as votes in favour or against.

A domain policy may require a stricter threshold.

### 6.3 Qualified Approval

The proposed default for materially consequential decisions is:

- quorum: at least two thirds of non-conflicted eligible voters; and
- approval: at least two thirds of valid votes cast are in favour.

Qualified Approval is required, at minimum, for:

- a post-award funding concentration above a threshold explicitly delegated to the Funding policy as requiring qualified approval;
- exceptional withdrawal of Endowment principal;
- transfer of `exergism.org`, registrar ownership/recovery control, or persistent identifier authority;
- appointment or removal of the legal Steward once such role is operative;
- organization-wide exclusive IP transfer or encumbrance;
- merger, dissolution or legal succession of the institutional entity; and
- any policy that expressly requires Qualified Approval.

### 6.4 Constitutional Amendment

The proposed default for amendment of this constitutional framework is:

- quorum: at least two thirds of non-conflicted eligible voters; and
- approval: at least three quarters of valid votes cast are in favour.

No amendment may retroactively manufacture contributor grants, patent rights, membership economic interests or authority over immutable project artifacts.

### 6.5 Emergency Action

An adopted emergency policy may permit narrow temporary action where delay would create immediate material risk to domain custody, funds, credentials, legal deadlines or service continuity.

Emergency authority MUST be time-limited, documented, minimally necessary and submitted for retrospective review. Emergency action cannot permanently amend the Constitution, distribute assets, create patent grants or permanently transfer persistent identifier control.

## 7. Conflicts of interest

A person is conflicted when a reasonable observer would conclude that the decision directly determines that person's material private economic interest, legal claim, sanction, appointment on uniquely preferential terms, or compensation.

At minimum:

- a compensation beneficiary cannot cast a substantive vote on their own compensation;
- a vendor cannot approve their own contract on behalf of EC;
- a funder does not obtain a governance vote merely by funding EC;
- conflicted voters are excluded from the eligible-voter denominator for that decision unless applicable law requires otherwise; and
- recusals and declared conflicts should be recorded in the decision record.

General participation in a class-wide policy does not automatically create a disqualifying conflict merely because a Member may be affected in the same way as the wider class.

## 8. Treasury, compensation and Endowment authority

Funding-domain strategy and detailed financial controls belong in the `funding` repository, but organization governance defines the authority vocabulary under which those controls operate.

The following constitutional boundaries apply:

- EC assets are institutional assets, not distributable membership property;
- compensation must correspond to genuine work, services, employment or another lawful basis and must follow conflict rules;
- no funder obtains governance, roadmap or organization-wide IP control merely in exchange for money;
- Strategic Reserve and Endowment assets remain institutionally owned;
- Endowment principal withdrawal requires the exceptional condition and approval class defined by adopted policy, never mere Treasurer discretion; and
- material treasury delegations must be explicit, revocable and auditable.

## 9. Project autonomy and cross-project authority

This Constitution does not make organization governance the substantive authority over every project.

In particular:

- Exergism remains authoritative for its canonical philosophical/formal source under its own change process;
- ECL remains authoritative for ECL evidence, governance and exact legal artifacts;
- ECL-PL remains authoritative for any separate patent-license architecture;
- Funding remains authoritative for its domain records and strategy subject to organization-level constitutional constraints; and
- `id.exergism.org` resolves identifiers but does not become semantic authority over the resources it resolves.

Organization-level decisions may establish shared infrastructure or constraints but MUST NOT silently mutate another repository's canonical artifact.

## 10. Domain and persistent identifier stewardship

The `exergism.org` domain and `id.exergism.org` persistence contract are constitutional infrastructure.

Operational custody may be delegated, but institutional authority over permanent transfer, abandonment or incompatible reassignment requires Qualified Approval. Persistent identifiers already issued must not be repurposed to mean a different resource.

The canonical infrastructure architecture is documented in `architecture/DOMAIN-AND-URI-ARCHITECTURE.md`.

## 11. Contributor rights and IP

Contributor-rights administration is governed by `IP-POLICY.md`, the exact CLA/version if adopted, Project Schedules and acceptance records.

Nothing in this Constitution creates a copyright assignment or patent grant. The CLA framework remains non-operative until its own activation requirements are satisfied.

## 12. Decision records

Every material operative governance decision SHOULD record:

- stable decision identifier;
- proposal and decision class;
- governing rule/version;
- eligible voters and recusals, subject to privacy constraints;
- quorum calculation;
- vote/result or other valid approval evidence;
- decision time and effective time;
- scope and delegated implementers;
- affected policies/resources;
- supersession relationship where applicable; and
- immutable source/hash for released decision artifacts.

GitHub merge state alone is not sufficient evidence of institutional adoption unless an adopted policy expressly makes it so.

## 13. Delegation and revocation

Delegations MUST identify the role or actor, scope, allowed actions, prohibited actions, start state and revocation mechanism. A delegation cannot grant greater authority than the delegating body possesses.

Repository permissions and infrastructure credentials SHOULD be reconciled against current delegations, but technical access is evidence of capability, not proof of institutional authority.

## 14. Succession and anti-capture

Legal or technical succession must preserve the mission, contributor-rights constraints, persistent-identifier commitments and project authority boundaries.

A change in GitHub ownership, domain registrar account, hosting provider, corporate control or maintainer personnel does not by itself rewrite EC governance or contributor grants.

## 15. Machine-readable projection

The canonical human constitutional text controls its machine-readable projection unless and until an adopted release expressly defines another hierarchy.

The `commons#` vocabulary, JSON-LD governance records and SHACL/CI constraints may encode a reviewable subset of these rules. If prose and executable constraints diverge, the divergence must fail visibly and be resolved through governance; code does not silently overrule the Constitution.

See `spec/MACHINE-READABLE-GOVERNANCE.md`.

## 16. Adoption

This 0.1 draft is intentionally **non-operative**. Before constitutional adoption, EC must at minimum resolve:

1. legal form and competent entity identity;
2. governing law and mandatory statutory requirements;
3. initial membership and voting registry;
4. legally competent adoption/signature process;
5. conflict, records and privacy implementation;
6. treasury/banking authority and accounting controls; and
7. qualified independent legal review appropriate to the chosen jurisdiction.

A merge of this file is architecture work, not constitutional ratification.
