# CLA Privacy and Agreement-Records Policy

> **Status: 0.1-DRAFT / non-operative.** This policy cannot become operative until the exact CLA legal Steward, data controller/record custodian, applicable law and production records system are identified in an adoption record.

## 1. Purpose

A Contributor License Agreement is useful only if Exergism Commons can later establish which person or entity accepted which exact agreement and which Contributions were covered. That need does **not** justify publishing or indefinitely collecting unrelated personal data.

The records system should therefore preserve a durable legal/provenance chain while applying purpose limitation, data minimization, access control, retention discipline and integrity/security appropriate to applicable privacy law.

## 2. Controller and custodian

The production policy must identify:

- the exact legal person/entity acting as data controller where applicable;
- the agreement-record custodian and authorized administrators;
- contact details for privacy/records requests;
- any processors or service providers used for signature, identity verification, storage or CLA automation; and
- the legal basis or bases relied upon for each material processing purpose where applicable law requires them.

The GitHub organization name `Exergism-Commons` is not by itself a sufficient controller identity.

Until the CLA adoption record identifies these items, this policy remains non-operative.

## 3. Processing purposes

CLA-related personal data may be processed only as reasonably necessary to:

1. establish that an individual or entity accepted an exact CLA version and Project Schedule;
2. verify that the accepting person had relevant identity/capacity or signatory authority;
3. associate covered GitHub identities, commit emails or equivalent contribution identifiers with that agreement record;
4. determine whether a proposed Contribution is covered by an individual agreement, Entity CLA or documented exception;
5. preserve evidence of the inbound-rights chain for project releases, audits, disputes and qualified legal review;
6. contact a contributor/rightsholder about rights, provenance, agreement changes or legacy confirmation where reasonably necessary; and
7. satisfy applicable legal, security and record-preservation obligations.

CLA records must not be repurposed by default for marketing, contributor profiling, unrelated analytics, public ranking or ideological screening.

## 4. Data minimization

The production system should normally require no more than:

- legal name or exact legal entity name in the private agreement record;
- verified contact information appropriate to the acceptance method;
- GitHub account(s), commit email(s) or other identifiers needed for contribution matching;
- exact CLA and Project Schedule versions;
- acceptance method, timestamp and immutable/adoption record identifiers;
- individual/entity coverage status;
- employer/entity authorization information only where ownership or authority makes it necessary; and
- evidence of signatory authority for an Entity CLA only to the extent reasonably necessary.

The following should **not** be collected merely because they might someday be useful:

- residential address;
- government identity number or full identity-document copy;
- date of birth;
- phone number;
- financial data;
- nationality;
- precise location; or
- unrelated employment/profile information.

If a signature or identity provider requires additional data, the production privacy review must document why, who receives it, how long it is retained and whether a less intrusive method can meet the same evidentiary need.

## 5. Public versus private records

Public repositories may expose the ordinary contribution history GitHub already makes part of the project record, such as commits, PRs, review history and public usernames.

A public CLA-status projection, if used, should be limited to operational fields such as:

```text
github_login
coverage: individual | entity | exception
agreement_version
project_schedule_version
effective_from
status: covered | expired-for-future-submissions | review-required
```

The public projection should not contain signatures, residential addresses, private contact details, identity documents, private employer evidence or other unnecessary verification material.

The private agreement record and the public status projection are separate layers. A public `covered` result is not a substitute for the underlying controlled evidence.

## 6. Records architecture

The production system should preserve exactness without leaking personal data into public content-addressed artifacts.

Recommended separation:

```text
public policy state
  -> exact adopted CLA/Schedule identifiers
  -> public-safe contributor coverage status

private controlled record
  -> legal identity / entity authority
  -> acceptance/signature evidence
  -> verified contribution identities
  -> exact agreement/adoption identifiers
```

If hashes, opaque IDs or commitments are published, the design must consider whether they can themselves be linked back to private identity data or enable dictionary attacks. Do not publish a simple unsalted hash of an email address or identity number as a supposed privacy measure.

## 7. Retention

Agreement evidence may need to outlive active contribution because public releases and inbound-rights questions can persist for many years. That does not justify retaining every verification artifact forever.

Before activation, the Steward must adopt a retention schedule that distinguishes at least:

- the core agreement record necessary to prove the grant and exact terms;
- identity/signatory verification evidence;
- obsolete GitHub/email mappings;
- failed or abandoned acceptance attempts;
- temporary verification logs; and
- legal-hold/dispute records.

Retention periods and review triggers should be reasoned from actual legal/provenance needs. Data no longer necessary for its documented purpose should be deleted, anonymized or reduced where applicable law permits, while preserving the minimum evidence required to establish already-granted rights.

## 8. Accuracy, correction and account changes

Contributors should have a documented method to:

- correct inaccurate private contact or identity-link data;
- add or retire GitHub identities used for future contribution checks;
- report an account takeover or mistaken identity association;
- update Entity Authorized Contributor status; and
- challenge an incorrect public coverage result.

Corrections must not silently rewrite historical legal facts. Where a historical record was wrong, preserve an auditable correction/supersession trail appropriate to the records system.

## 9. Access control and security

Private CLA records should be accessible only to persons whose role requires access for agreement administration, legal review, security, audit or dispute handling.

The production system should use controls appropriate to the sensitivity and volume of records, including where appropriate:

- strong authentication and least-privilege authorization;
- encryption in transit and at rest;
- protected backups and recovery testing;
- access/change logging;
- separation between public CLA automation and private identity evidence;
- credential/key rotation and administrator offboarding; and
- a documented security-incident response path.

No secret, signature file or identity document should be committed to a public Git repository.

## 10. Processors and external services

If the Steward uses an e-signature, identity-verification, CLA bot, hosting or storage provider, the adoption review must document:

- the provider and role;
- categories of data transferred;
- processing purpose;
- retention/deletion behavior;
- security and access model;
- relevant sub-processors;
- cross-border transfer implications where applicable; and
- the contractual/privacy basis required by applicable law.

Convenience is not a reason to give a GitHub bot access to full identity records if the bot only needs a `covered/not covered` answer.

## 11. Contributor rights and requests

The operative privacy notice must explain any rights available under applicable law, which may include access, correction, deletion, restriction, objection, portability or complaint rights, together with any lawful limitations arising from the need to preserve evidence of an already-executed agreement or legal claims.

A request to delete unnecessary account/contact data is not automatically the same as revoking an irrevocable copyright license already granted under the CLA. Privacy rights and intellectual-property grant effects must be analyzed separately under applicable law.

## 12. International contributors and transfers

Because Exergism Commons may receive Contributions internationally, the production design must identify where records are stored and whether cross-border data-transfer rules apply. The system must not assume that publication on GitHub or acceptance by an international contributor eliminates those obligations.

## 13. Security incidents and record integrity

The Steward should maintain a procedure for suspected loss, unauthorized access, alteration or disclosure of private CLA records. The process should distinguish:

- compromise of private identity/signature evidence;
- compromise of a public coverage projection;
- compromise of a contributor's GitHub account; and
- corruption or loss of an immutable policy/adoption artifact.

A compromised public `covered` flag must not be treated as conclusive evidence that a valid agreement exists.

## 14. Successor Steward

Transfer of CLA rights to a valid successor Steward does not automatically authorize uncontrolled transfer of all personal data. Any successor records transfer must have an appropriate legal basis, preserve the purposes and safeguards of the agreement-record system, and be disclosed as required by applicable law.

## 15. Adoption requirements

CLA blocker `CLA-05` is complete only when an adoption record identifies, at minimum:

```yaml
privacy_records_policy: <exact immutable version/hash>
controller_or_equivalent:
  legal_name: <exact>
  contact: <exact>
record_custodian: <exact>
private_records_system: <system/process identifier>
public_status_projection: <system/process identifier or null>
retention_schedule: <exact version/reference>
processors: <reviewed list/reference>
security_controls_review: <record/reference>
data_subject_request_process: <record/reference>
international_transfer_review: <record/reference or not-applicable with reason>
```

The exact production fields may change after qualified legal/privacy review. What matters is that the activation record makes the controller, purposes, data flows, retention and safeguards explicit rather than leaving them to an undocumented future implementation.
