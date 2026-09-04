# CLA Adoption and Release Gate

> **Current status: BLOCKED / DRAFT.** EC-ICLA 1.0-DRAFT and EC-ECLA 1.0-DRAFT must not be presented for binding acceptance yet.

## 1. Why an adoption gate exists

A contributor agreement is not made valid or institutionally sound merely by merging Markdown into GitHub. The production system needs an identifiable contracting party, exact terms, a rights-compatible project schedule, an acceptance mechanism and durable records.

This gate separates drafting from legal activation.

## 2. Mandatory blockers

Every item below must be complete before `policy/cla-status.yaml` may set `operative: true`.

### CLA-01 — competent legal Steward

Record the exact legal person/entity that receives the CLA grant, including enough identity information to avoid confusion with the GitHub namespace.

The authority record must identify at least:

- exact legal name;
- legal form;
- jurisdiction;
- registration identity where applicable;
- relationship to Exergism Commons;
- competent signatories;
- immutable registration/identity evidence;
- the exact institutional decision establishing CLA-receiving/administration authority; and
- competent-signatory evidence bound to the exact authority payload.

For an operative EC governance regime, appointment/removal of the legal Steward is a protected institutional decision and the CLA authority record must resolve to the corresponding valid Qualified Approval. Repeating a Steward name in `cla-status.yaml`, a legal-review manifest or an adoption record is not itself evidence that the receiving party exists or has authority.

The Steward appointment is a historical governance act. If Governance is amended later, that appointment remains validated under the governance release, decision rules, Membership/electorate and governance version that were actually operative on the appointment decision date. A later governance release neither invalidates a valid historical appointment by version mismatch nor retroactively cures an invalid one.

The record must explain the Steward's relationship to Exergism Commons and authority to steward the Covered Projects.

**Current: open.**

### CLA-02 — governing law and forum model

Select and legally review governing law and, if used, forum/dispute terms. The choice should account for the Steward's actual legal form/location and the expected international contributor base.

**Current: open.**

### CLA-03 — qualified legal review

Obtain independent qualified review of at least:

- non-exclusive copyright grant and sublicensing language;
- outbound-license constraint and successor-version mechanism;
- moral-rights treatment, especially where non-waivable rights apply;
- individual/entity ownership and employment issues;
- no-patent-grant boundary and interaction with Apache-2.0/ECL/ECL-PL;
- electronic acceptance/e-signature validity;
- privacy/record retention;
- successor-Steward transfer; and
- enforcement/cooperation wording.

For ECL 1.0, the result should be supplied to the qualified reviewers handling ECL `LAR-10`; this CLA review does not replace the rest of ECL's legal-review gate.

**Current: open.**

### CLA-04 — exact Project Schedule ratification

Review every covered repository/material class against the actual outbound license and project governance. Resolve every `outbound unresolved` entry that would prevent knowing what rights the Steward may exercise.

A repository can remain outside CLA coverage until its scope is ready.

**Current: open.**

### CLA-05 — privacy and records system

Adopt an exact version of [`PRIVACY-AND-RECORDS.md`](PRIVACY-AND-RECORDS.md) or a qualified-review replacement and identify the data controller/record custodian, collection purposes, data fields, access controls, retention schedule, correction/request process, security controls, processors and international-transfer treatment appropriate to applicable law.

Public Git must not become the default store for signatures, addresses or identity documents.

**Current: open. Draft architecture exists; production controller/system/retention/legal basis remain unresolved.**

### CLA-06 — acceptance/signature mechanism

Choose and test a legally reviewed method (for example, an electronic-signature service or explicit authenticated clickwrap flow) that binds a human/entity to the exact immutable agreement and schedule.

A mutable web page or unexplained checkbox is insufficient.

**Current: open.**

### CLA-07 — contributor-status automation

If GitHub checks are automated, ensure the check:

- resolves exact versions;
- handles individual/entity coverage;
- has an auditable override path;
- fails without leaking private data; and
- does not block ordinary issues/criticism that are not Contributions.

Automation may launch after legal activation, but production repositories must not claim CLA enforcement is complete until checks are reliable.

**Current: open.**

### CLA-08 — legacy rights inventory

Start the repository-by-repository migration in `LEGACY-CONTRIBUTIONS.md`, with ECL legal text/spec history prioritized for LAR-10.

Legacy inventory need not necessarily be 100% complete before a prospective CLA starts accepting **new** Contributions, if qualified counsel agrees. It must not be falsely represented as retroactively cured by adoption.

**Current: open.**

## 3. Adoption artifact

When the blockers are resolved, create an immutable adoption record containing at minimum:

```yaml
agreement_family: EC-CLA
individual_version: EC-ICLA-1.0
entity_version: EC-ECLA-1.0
project_schedule_version: <exact version/hash>
legal_steward:
  stable_id: <exact>
  legal_name: <exact>
  legal_form: <exact>
  jurisdiction: <exact>
  registration_identity: <exact>
  relationship_to_exergism_commons: <exact>
legal_steward_authority: <content-addressed record/hash>
governing_law: <exact>
forum: <exact or null>
effective_date: <ISO-8601>
acceptance_methods:
  - <reviewed method>
privacy_records_policy: <exact version/hash>
legal_review_records:
  - <immutable reference/hash>
operative: true
```

The Steward authority, adopted CLA texts, Project Schedule and review inputs should be immutable/content-addressed. A convenience `current` pointer may exist but must not replace exact identity.

## 4. Adoption decision

Activation should occur through a dedicated PR whose sole substantive purpose is adoption. The PR must:

- identify every completed blocker;
- link immutable review evidence;
- include the final exact legal text;
- update machine-readable state;
- state the effective date prospectively; and
- explain transition rules for open PRs submitted before the effective date.

The legal review and adoption must be complete **before or on** the declared effective date. The legal-review manifest must record its completion date; every qualified-reviewer signature must be dated no later than that completion/effective date. The CLA adoption record must record its decision date after completed legal review and no later than the effective date, and every adopter signature must likewise exist no later than activation. An effective date cannot be backdated to make later review, adoption or signatures appear prospectively authoritative.

Authentication is not authority. Every adopter identity must already be a competent signatory in the exact content-addressed Legal Steward authority record. A valid signature from an outsider, reviewer or maintainer does not authorize that person to act for the receiving party. A future delegated-adopter mechanism, if ever introduced, must use its own explicit content-addressed authority record and validation contract; authority must never be inferred from signature validity alone.

The adoption record and legal-review manifest must bind the same exact legal Steward identity, Steward-authority digest, governing law, forum, privacy policy, acceptance methods and legal-artifact hashes. They cannot cure an unproven Steward merely by repeating the same string.

## 5. No accidental activation

None of the following makes the CLA operative:

- merging this bootstrap package;
- a maintainer saying `CLA required` in an issue;
- adding a badge;
- creating a GitHub branch named `stable`;
- a bot assuming the newest file is effective; or
- an organization rename/incorporation without a formal adoption record.

Until the exact adoption artifact says otherwise, the CLA remains a legal-review candidate.