# AI-Assisted Contribution Provenance

> **Status: draft companion policy.** This document addresses provenance, not whether any particular AI system is lawful or whether machine output is copyrightable in a specific jurisdiction.

## 1. Principle

Using AI assistance does not reduce the standard for rights, attribution, review or reproducibility. A contributor can grant only rights the contributor actually owns or controls.

## 2. Assistance versus provenance risk

Low-risk assistance may include spelling correction, formatting, test generation subsequently verified by the contributor, or suggestions that the contributor substantially rewrites and validates.

Higher provenance risk can arise when a submission contains substantial generated text/code, close reproduction of an identified source, generated images/media, output prompted to imitate a living author's distinctive work, or content whose source/rights cannot be reasonably assessed.

Risk classification concerns provenance and project reliability, not moral blame.

## 3. Disclosure

For a material AI-assisted Contribution, the contributor should disclose in the PR when AI materially generated or transformed substantive content.

The disclosure should identify, where useful:

- tool/system used;
- what portion was materially assisted;
- whether the output was independently reviewed/reworked;
- any known source-attribution concern; and
- reproducibility limitations relevant to generated artifacts.

Projects may exempt trivial editor/autocomplete use from disclosure.

## 4. Rights representation

The CLA representation is limited to rights the contributor can actually grant. A contributor must not state or imply that signing the CLA makes machine-generated material exclusively theirs where applicable law says otherwise.

If copyright status is uncertain but the material is useful and apparently safe to include, maintainers should record the uncertainty rather than invent ownership. If the project needs an exclusive or relicensable right that cannot be established, replace or rewrite the material.

## 5. Third-party similarity

If an AI-assisted output appears substantially similar to identifiable third-party code, text, image, data or another protected work, treat it as a third-party provenance issue. Investigate the source/license or do not merge the material.

A model provider's terms of service do not by themselves prove that output is free of third-party rights.

## 6. Legal and governance drafting

AI may assist with ECL, ECL-PL or CLA drafting, but:

- machine output is not qualified legal review;
- citations/authorities must be independently verified;
- invented cases, statutes or license language must not enter legal records as real authority;
- a legal instrument should preserve the human/reviewer decision record for material choices; and
- legal-review gates remain exactly as defined by the relevant project.

## 7. Formal Exergism and semantic artifacts

AI-generated summaries or inferred ontology relations must not silently replace canonical philosophical source text or create ECL designations. Derived artifacts should remain reproducible and subordinate to their declared canonical inputs.

## 8. Confidentiality

Do not place confidential, personal, embargoed or legally privileged material into an external AI system unless authorized and consistent with the project's data/security policy.

## 9. Maintainer response

When provenance is unclear, maintainers may request:

- a human rewrite;
- source references;
- narrower changes;
- removal of generated media;
- independent verification; or
- third-party-license review.

The goal is a defensible project record, not a ritual `AI-free` label.
