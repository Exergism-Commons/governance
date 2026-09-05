# Evidence Authentication and Historical Authority

> **Status: 0.1-DRAFT — non-operative validation contract.**

This document records the fail-closed evidence rules implemented by the canonical `tools/validate.py` verdict. It does not make Governance or the CLA operative and does not substitute for qualified legal review.

## 1. Hashes identify bytes; they do not establish authority

A content-addressed reference proves which bytes were selected. A release, process, review, signature or other record becomes usable as an authority input only after the validator also proves the semantic contract applicable to that record: type, subject, successful/final state, payload binding, chronology and authentication where required.

Consequently, a `governance-authority-snapshot` may not treat a matching activation-evidence SHA-256 as sufficient proof that the referenced activation process actually completed or that the referenced legal review approved the relevant material.

## 2. Historical release activation evidence

Every release that may authorize a descendant must have semantically valid activation evidence.

Activation records are traced to the release that introduced the exact content-addressed bytes:

- an unchanged record may be inherited by a later release without being falsely rewritten as a record created under the later governance version;
- the inherited record remains validated under the governance version, artifacts, rules, legal identity and effective-date boundary of its release of origin; and
- if a release changes an activation record, the changed bytes have that release as their new origin and must independently satisfy the full applicable semantic and chronology gate.

A later release therefore cannot cure an invalid founding/intermediate activation record merely by preserving its hash, and it cannot re-date old evidence to a newer version.

## 3. Historical rule and membership semantics

An immutable predecessor snapshot is not authoritative merely because its hashes are intact. Before it can authorize a descendant release, the validator applies the constitutional and anti-capture floors to the predecessor's own decision rules and Membership policy.

Historical rule snapshots must preserve, at minimum, the protected approval/quorum floors, fail-closed zero-vote semantics, Mission-Lock classification and protected subjects, repeated-vote/review/Guardian requirements, mandatory Qualified Approval subjects and conflict/funding anti-capture rules. Historical Membership snapshots must preserve one-person-one-vote, natural-person voting membership, the Candidate and seasoning floors, frozen electorates, authenticated proposal-bound ballots, conflict-determination safeguards and the protected admission/termination lifecycle authorities.

A later release may strengthen a rule prospectively. Historical events are still evaluated under the predecessor authority that actually governed them; a later strengthening is not applied retroactively to invalidate a previously valid release. Conversely, a weakened historical snapshot cannot authorize a descendant and then hide the weakness by restoring compliant current values.

The current release-record schema proves exactly two successful Mission-Locked votes: a first vote and the final ratifying vote. Therefore `successful_votes_required` must remain exactly `2` for this schema. A future rule requiring three or more successful votes requires a release-record schema upgrade with an authenticated complete vote-sequence representation before that stronger rule can become operative authority.

## 4. Immutable Membership roster checkpoints

Every operative governance release must bind a content-addressed `governance-membership-roster-snapshot` in its adoption payload. The snapshot is frozen at that release's effective date and contains every Member admitted by then, including inactive/former Members, together with the immutable admission provenance and every membership-state transition effective by that date.

The release's constitutive signatures or amendment ballots authenticate the exact roster-snapshot reference because it is part of the signed/voted release payload. When a descendant release is proved, the current mutable Member Registry must still reproduce every historical Member, admission epoch and transition contained in each predecessor checkpoint. Later Members and later transitions may be appended; historical rows or history already frozen into an operative release may not be pruned or rewritten.

This closes a sequence-3+ attack in which an opponent who participated in release N is deleted from the current registry before release N+1 is validated, causing the predecessor electorate to be recomputed without that person.

For the constitutive release, the roster may represent a `constitutive-initial-member` admission without embedding the adoption record's own future content hash; that founding provenance is separately established by the signed release-1 adoption itself. Later admissions must retain their exact content-addressed admission references.

## 5. Signed review payloads

Where a review is authority-bearing, reviewer authentication covers more than the review conclusion.

The signed review payload includes:

- every substantive review field;
- each reviewer identity; and
- the exact content-addressed qualification-evidence reference for each reviewer.

Only signature references and the digest field itself are excluded to avoid self-reference. Swapping a reviewer, replacing qualification evidence or changing a substantive conclusion therefore changes the authenticated payload and invalidates a replayed signature.

Qualification evidence is itself semantically bound. It must be final `supporting-evidence` whose `evidence_purpose` is `reviewer-qualification`, whose `subject_person_id` is the reviewer being qualified, and whose explicit `qualification_scope` covers the authority-bearing review being performed. A well-formed but unrelated evidence record cannot satisfy reviewer qualification merely because it has the right hash or date.

Reviewer qualification evidence must exist no later than review completion. Where independence is required, a reviewer may not be one of the competent signatories/adopters whose act is being independently reviewed.

## 6. Legacy review envelopes

A legacy review format whose primary digest historically excludes the `reviewers` array must carry a `reviewer_authentication_sha256` field inside that primary signed payload.

That digest is computed over the ordered reviewer projection containing only:

```json
[
  {
    "reviewer_id": "<stable reviewer id>",
    "qualification_evidence": {
      "path": "<content-addressed evidence path>",
      "sha256": "<exact sha256>"
    }
  }
]
```

Reviewer signature references are excluded from this projection. The canonical validator verifies both that the reviewer-authentication digest matches the reviewer list and that the digest field itself is part of the already-signed primary review payload.

The operative CLA legal-review manifest uses this compatibility rule. New governance/Open Knowledge qualified reviews and governance-amendment classification reviews use the direct signed-review-payload rule instead.

## 7. Signature verification evidence

A `signature-evidence` record cannot be authenticated by attaching arbitrary generic evidence. Its content-addressed verification record must explicitly describe the exact attestation that was verified.

The verification record must bind:

- `evidence_purpose: signature-verification`;
- the exact `subject_person_id`;
- the exact `decision_id`;
- the exact `verified_payload_sha256`;
- the exact signature context type and version;
- the same signature method claimed by the signature record; and
- `verification_result: valid` plus a non-empty verification method.

The verification evidence must already exist when the signature is treated as effective. This prevents an unrelated verification record, or one referring to another signer/decision/payload/context, from being replayed to manufacture an authority-bearing signature envelope.

This validation contract records and checks externally verifiable signature evidence; it does not claim that a repository hash by itself is a cryptographic identity system.

## 8. Historical CLA Steward authority

A CLA Legal Steward appointment is a governance act at a particular point in the release history. If Governance is later amended, the old Steward appointment must not be rewritten or re-approved under the new version merely to keep the CLA valid.

The validator resolves the governance release in force on the Steward appointment's decision date and uses that release's decision rules, Membership policy/electorate, governance version and effective boundary to validate the appointment, identity evidence, Qualified Approval and competent-signatory evidence. This preserves a legitimately adopted historical Steward appointment while preventing current rules from retroactively blessing an invalid old appointment.

CLA adoption signatures remain a separate authority question: an authenticated signer is not automatically competent to adopt for the Legal Steward. Every CLA adopter must be a competent signatory identified by the exact content-addressed Steward authority record unless a future explicit content-addressed delegation mechanism is separately specified and validated.

## 9. Canonical verdict

These requirements are components of the single complete verdict:

```bash
python tools/validate.py
```

Internal helpers and partial validators are not alternative activation verdicts. A consumer must not infer authority from an individual SHA check, parser result, projection field or partial validator succeeding in isolation.
