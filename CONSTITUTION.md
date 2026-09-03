# Exergism Commons Constitutional Framework

> **Status: 0.1-DRAFT — non-operative.** This document defines the proposed organization-level constitutional model for Exergism Commons (EC). It does not create a legal entity, membership right, fiduciary authority, contractual power, or operative decision merely by being present in Git.

## 1. Purpose

Exergism Commons exists to steward a durable, contestable and anti-capture commons around Exergism and projects that explicitly depend on, implement or extend that ecosystem, while preserving the authority boundaries of each canonical project.

Organization governance exists to answer questions that no project repository should answer for itself: institutional authority, membership, voting, conflicts, delegation, treasury authority, domain custody, contributor-rights administration, succession and adoption of shared policy.

EC is not constitutionally neutral about its own identity. Members may govern EC, but they do not receive an ordinary power to repurpose EC into an unrelated organization.

## 2. Constitutional principles

EC governance is based on the following constraints:

1. **Mission before ownership.** Membership, contribution, founding status or administration does not create an economic ownership share in EC assets.
2. **No silent authority.** Repository access, maintainer status, RDF inference, funding, employment or contribution does not by itself create institutional authority.
3. **Rights remain attributable.** Copyright, patent and contractual rights remain with their actual rightsholders except where expressly granted.
4. **Anti-capture.** No donor, funder, employer, maintainer, founder, service provider or single project may convert resources or technical position into unlimited organization-wide control.
5. **Explicit founding stewardship.** Founder-led authority during bootstrap is recorded and bounded rather than hidden in credentials or informal practice.
6. **Conflict exclusion.** A person does not substantively vote on a decision whose primary purpose is to determine that person's own compensation, direct private benefit, claim or sanction.
7. **Reproducibility.** Material institutional decisions should be versioned, attributable and machine-readable where practical.
8. **Human authority controls machine enforcement.** Schemas, SHACL, CI and automation may enforce adopted rules but cannot create authority absent a valid institutional act.
9. **Non-retroactivity.** Later policies do not silently rewrite historical releases, grants, contribution terms or completed decisions.
10. **Subsidiarity.** Organization governance acts only on organization-level matters or authority explicitly delegated to it.
11. **Contestability.** Material decisions must preserve a documented route for objection, contrary evidence and correction.
12. **Power should become distributed as capacity becomes real.** Bootstrap concentration is tolerated only as an explicit transitional condition, not as hidden permanent ownership.

## 3. Legal identity and bootstrap state

Until a legally competent EC entity is constituted and identified in an adopted institutional record:

- EC governance remains in **bootstrap / non-operative institutional status**;
- no repository document may falsely represent the GitHub organization itself as a legal person;
- no draft role may execute contracts merely by virtue of this document;
- draft votes may be used to test procedure but are not represented as legally binding institutional acts; and
- legally consequential instruments such as a CLA remain blocked by their own adoption requirements.

A future legal-entity adoption decision MUST identify at least the entity name, jurisdiction, registration identity where applicable, governing constitutional instrument, effective date, competent signatories and relationship between the legal entity and the public Exergism Commons project.

The proposed institutional bootstrap phase is `F0-founder-led-bootstrap` as defined in `FOUNDING-STEWARDSHIP.md`.

## 4. Mission Lock

### 4.1 Protected institutional identity

The constitutional Mission Lock protects EC from ordinary majoritarian repurposing.

At minimum, it protects these invariants:

- EC remains institutionally centered on Exergism and the stewardship of its commons ecosystem;
- Exergism remains authoritative for its own canonical philosophical/formal evolution;
- ECL, ECL-PL, Funding and other projects retain their explicit authority boundaries;
- membership, funding, employment, contribution, founder status and technical administration do not create economic ownership of EC;
- funding cannot purchase organization-wide governance authority merely through money;
- contributor rights, copyright rights and patent rights cannot be fabricated or expanded retroactively by organizational vote;
- persistent identifiers and immutable released artifacts cannot be silently repurposed; and
- contestability and resistance to capture remain structural governance commitments.

The Mission Lock protects **what EC is**, not every current implementation, roadmap decision or philosophical proposition. Exergism itself may evolve through its own canonical process.

### 4.2 Mission-Locked Amendment

A proposal whose primary effect is to alter a Mission Lock invariant is a **Mission-Locked Amendment**.

During the Founding Period it requires, at minimum:

- quorum of at least three quarters of non-conflicted Members eligible for mission-locked voting;
- at least 90% approval among valid votes cast for/against;
- two successful votes separated by at least 60 days;
- written compatibility and consequences analysis;
- qualified independent review appropriate to the subject; and
- affirmative consent of the Founding Steward or valid successor Mission Guardian.

The machine-readable exact rule is in `policy/decision-rules.json`.

Mandatory law prevails where an internal constitutional lock cannot lawfully prevent a required change.

## 5. Founding Stewardship

The proposed initial **Founding Steward** is **Daniel Molinero Lucas**.

Founding Stewardship is a constitutional bootstrap role, not property, equity, hereditary office or a residual claim on EC assets.

The exact powers, prohibitions, phase transitions and succession requirements are defined in `FOUNDING-STEWARDSHIP.md`.

### 5.1 Bootstrap executive authority

During F0, the Founding Steward may provide strong strategic and institutional direction, including roadmap coordination, initial appointments, admission of initial Members under adopted criteria, draft-policy formation and reversible continuity actions.

This authority exists because EC is materially founder-dependent during bootstrap. It must not be disguised as ordinary Member voting power.

### 5.2 Mission Veto

During the Founding Period the Founding Steward may exercise a **negative Mission Veto** against a proposal that reasonably violates the Mission Lock or attempts a protected irreversible action through an insufficient approval path.

The veto cannot enact an alternative proposal and must cite the protected invariant or action at issue.

### 5.3 Founder power limits

Founding status does not permit the Founding Steward to:

- approve their own compensation or private contract while conflicted;
- distribute Treasury, Reserve or Endowment assets to themselves as a membership/founder entitlement;
- withdraw Endowment principal unilaterally;
- transfer `exergism.org` or persistent identifier authority unilaterally once governance is operative;
- create copyright or patent rights EC does not possess;
- rewrite contributor grants or immutable releases retroactively; or
- use the Mission Veto merely to override lawful ordinary-policy disagreement within the protected mission.

Founder authority is designed to reduce as institutional capacity becomes demonstrably distributed.

## 6. Membership

### 6.1 Membership is governance status, not property

Membership may confer participation and voting rights under adopted rules. It does not confer a transferable share, dividend right, claim on the Endowment, residual claim on Treasury assets or ownership interest in EC.

### 6.2 One person, one Member, one vote

Voting Members are natural persons.

The default constitutional rule is **one person = one Member = one vote**. Voting weight is not increased by donations, grants, employment, founder status, GitHub permissions, commit count, seniority or compensation.

Founding constitutional authority is recorded separately from the Founding Steward's ordinary Member vote; it is not a hidden weighted vote.

### 6.3 Member registry

Operative membership MUST be recorded in a controlled registry with stable identifiers, state and effective dates. Public projections may omit private identity evidence.

A GitHub organization member, repository collaborator, CLA signatory, donor, employee or contractor is not automatically an EC Member.

### 6.4 Admission, activity and termination

The detailed Candidate, admission, voting-seasoning, activity, inactivity, suspension, resignation and termination rules are defined in `MEMBERSHIP.md`.

Membership admission must be observable and resistant to bulk capture. Protected voting rights may require longer membership seasoning than ordinary participation.

Termination for cause must provide notice, reasons and a contestable process proportionate to the consequences.

## 7. Institutional roles

The constitutional vocabulary distinguishes at least:

- **Member** — person with governance rights recorded by the Membership Policy;
- **Founding Steward** — explicit founder-led bootstrap and mission-protection role;
- **Mission Guardian** — future narrow successor to mission-protection authority after general founder executive primacy recedes;
- **Steward** — role responsible for institutional continuity and execution of valid decisions within delegated authority;
- **Treasurer** — role responsible for treasury administration and reporting, not unilateral ownership or appropriation;
- **Domain Custodian** — role entrusted with operational custody of `exergism.org`, registrar access and identifier infrastructure;
- **Repository Maintainer** — technical role over one or more repositories; technical permissions do not imply broader institutional power;
- **Auditor / Reviewer** — role that can independently review records, controls or decisions without acquiring executive authority.

One person may hold multiple roles only where conflicts and concentration rules allow it. Role assignments are revocable governance delegations, not personal property.

## 8. Decision classes

### 8.1 Delegated action

A delegated role may perform routine acts expressly within an adopted delegation. Delegated action may never be used to amend the Constitution, create new constitutional authority, distribute EC assets to Members, transfer organization-wide IP ownership, dispose of Endowment principal, transfer persistent-domain control, alter the Mission Lock, or bypass an approval class required by policy.

### 8.2 Ordinary Approval

The proposed default for ordinary organization-level decisions is:

- quorum: more than one half of non-conflicted eligible voters;
- approval: more votes in favour than against among valid votes cast;
- abstentions do not count as votes in favour or against.

A domain policy may require a stricter threshold.

### 8.3 Qualified Approval

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

### 8.4 Constitutional Amendment

The proposed default for amendment of constitutional provisions outside the Mission Lock is:

- quorum: at least two thirds of non-conflicted eligible voters; and
- approval: at least three quarters of valid votes cast are in favour.

No amendment may retroactively manufacture contributor grants, patent rights, membership economic interests or authority over immutable project artifacts.

### 8.5 Mission-Locked Amendment

Mission-Locked Amendments use the stricter process in Section 4 and `FOUNDING-STEWARDSHIP.md`.

### 8.6 Emergency Action

An adopted emergency policy may permit narrow temporary action where delay would create immediate material risk to domain custody, funds, credentials, legal deadlines or service continuity.

Emergency authority MUST be time-limited, documented, minimally necessary and submitted for retrospective review. Emergency action cannot permanently amend the Constitution, alter the Mission Lock, distribute assets, create patent grants or permanently transfer persistent identifier control.

## 9. Conflicts of interest

A person is conflicted when a reasonable observer would conclude that the decision directly determines that person's material private economic interest, legal claim, sanction, appointment on uniquely preferential terms, or compensation.

At minimum:

- a compensation beneficiary cannot cast a substantive vote on their own compensation;
- a vendor cannot approve their own contract on behalf of EC;
- a funder does not obtain a governance vote merely by funding EC;
- founder status does not override a required recusal;
- conflicted voters are excluded from the eligible-voter denominator for that decision unless applicable law requires otherwise; and
- recusals and declared conflicts should be recorded in the decision record.

General participation in a class-wide policy does not automatically create a disqualifying conflict merely because a Member may be affected in the same way as the wider class.

## 10. Treasury, compensation and Endowment authority

Funding-domain strategy and detailed financial controls belong in the `funding` repository, but organization governance defines the authority vocabulary under which those controls operate.

The following constitutional boundaries apply:

- EC assets are institutional assets, not distributable membership or founder property;
- compensation must correspond to genuine work, services, employment or another lawful basis and must follow conflict rules;
- no funder obtains governance, roadmap or organization-wide IP control merely in exchange for money;
- Strategic Reserve and Endowment assets remain institutionally owned;
- Endowment principal withdrawal requires the exceptional condition and approval class defined by adopted policy, never mere Treasurer or founder discretion; and
- material treasury delegations must be explicit, revocable and auditable.

## 11. Project autonomy and cross-project authority

This Constitution does not make organization governance the substantive authority over every project.

In particular:

- Exergism remains authoritative for its canonical philosophical/formal source under its own change process;
- ECL remains authoritative for ECL evidence, governance and exact legal artifacts;
- ECL-PL remains authoritative for any separate patent-license architecture;
- Funding remains authoritative for its domain records and strategy subject to organization-level constitutional constraints; and
- `id.exergism.org` resolves identifiers but does not become semantic authority over the resources it resolves.

Organization-level decisions may establish shared infrastructure or constraints but MUST NOT silently mutate another repository's canonical artifact.

## 12. Domain and persistent identifier stewardship

The `exergism.org` domain and `id.exergism.org` persistence contract are constitutional infrastructure.

Operational custody may be delegated, but institutional authority over permanent transfer, abandonment or incompatible reassignment requires Qualified Approval. Persistent identifiers already issued must not be repurposed to mean a different resource.

The Founding Steward may perform reversible bootstrap technical administration while governance is non-operative, but technical control is not treated as institutional ownership.

The canonical infrastructure architecture is documented in `architecture/DOMAIN-AND-URI-ARCHITECTURE.md`.

## 13. Contributor rights and IP

Contributor-rights administration is governed by `IP-POLICY.md`, the exact CLA/version if adopted, Project Schedules and acceptance records.

Nothing in this Constitution creates a copyright assignment or patent grant. The CLA framework remains non-operative until its own activation requirements are satisfied.

Neither a Member majority nor the Founding Steward may manufacture rights that actual rightsholders did not grant.

## 14. Decision records

Every material operative governance decision SHOULD record:

- stable decision identifier;
- proposal and decision class;
- governing rule/version;
- eligible voters and recusals, subject to privacy constraints;
- quorum calculation;
- vote/result or other valid approval evidence;
- any Founding Steward Mission Veto or Mission Guardian concurrence required by the applicable rule;
- decision time and effective time;
- scope and delegated implementers;
- affected policies/resources;
- supersession relationship where applicable; and
- immutable source/hash for released decision artifacts.

GitHub merge state alone is not sufficient evidence of institutional adoption unless an adopted policy expressly makes it so.

## 15. Delegation, distribution and succession

Delegations MUST identify the role or actor, scope, allowed actions, prohibited actions, start state and revocation mechanism. A delegation cannot grant greater authority than the delegating body possesses.

Repository permissions and infrastructure credentials SHOULD be reconciled against current delegations, but technical access is evidence of capability, not proof of institutional authority.

Founder executive authority is expected to reduce through the F0 → F1 → F2 maturity process in `FOUNDING-STEWARDSHIP.md`. Phase transitions require evidence and valid institutional records; they cannot be fabricated by editing machine state.

Legal or technical succession must preserve the mission, contributor-rights constraints, persistent-identifier commitments and project authority boundaries.

A change in GitHub ownership, domain registrar account, hosting provider, corporate control or maintainer personnel does not by itself rewrite EC governance or contributor grants.

EC must define succession for death, incapacity, prolonged unavailability or retirement of the Founding Steward so that mission protection does not become a single point of institutional failure.

## 16. Machine-readable projection

The canonical human constitutional text controls its machine-readable projection unless and until an adopted release expressly defines another hierarchy.

The `commons#` vocabulary, JSON-LD governance records and SHACL/CI constraints may encode a reviewable subset of these rules. If prose and executable constraints diverge, the divergence must fail visibly and be resolved through governance; code does not silently overrule the Constitution.

Automation must not infer membership or founder authority from GitHub access, funding, employment, contributions or graph connectivity.

See `spec/MACHINE-READABLE-GOVERNANCE.md`.

## 17. Adoption

This 0.1 draft is intentionally **non-operative**. Before constitutional adoption, EC must at minimum resolve:

1. legal form and competent entity identity;
2. governing law and mandatory statutory requirements;
3. initial membership and voting registry;
4. legally competent adoption/signature process;
5. conflict, records and privacy implementation;
6. treasury/banking authority and accounting controls;
7. exact operative Founding Steward assignment and succession triggers;
8. compatibility of Mission Lock/founder provisions with mandatory law in the chosen jurisdiction; and
9. qualified independent legal review appropriate to that jurisdiction.

A merge of this file is architecture work, not constitutional ratification.