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

## 3. Signed review payloads

Where a review is authority-bearing, reviewer authentication covers more than the review conclusion.

The signed review payload includes:

- every substantive review field;
- each reviewer identity; and
- the exact content-addressed qualification-evidence reference for each reviewer.

Only signature references and the digest field itself are excluded to avoid self-reference. Swapping a reviewer, replacing qualification evidence or changing a substantive conclusion therefore changes the authenticated payload and invalidates a replayed signature.

Reviewer qualification evidence must exist no later than review completion. Where independence is required, a reviewer may not be one of the competent signatories/adopters whose act is being independently reviewed.

## 4. Legacy review envelopes

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

## 5. Canonical verdict

These requirements are components of the single complete verdict:

```bash
python tools/validate.py
```

Internal helpers and partial validators are not alternative activation verdicts. A consumer must not infer authority from an individual SHA check, parser result, projection field or partial validator succeeding in isolation.
