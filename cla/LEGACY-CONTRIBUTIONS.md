# Legacy Contributions and Chain-of-Title Migration

> **Status: draft migration policy.** A new CLA cannot retroactively bind historical contributors by declaration.

## 1. Why this matters

Exergism Commons already contains substantial authored material. Future CLA adoption can improve provenance for new Contributions, but it cannot erase the rights history of existing commits.

This is especially important for ECL because its legal-review model treats contributor chain of title and enforcement authority as a distinct release-gate surface.

## 2. No fake retroactivity

Do not mark a historical commit `CLA covered` merely because its author later appears in a contributor list.

Historical material may be supported by one or more independent rights bases:

1. an outbound/project license that the rightsholder validly applied at the time;
2. an inbound contribution term in force at the time of submission;
3. employment/assignment or other chain-of-title evidence;
4. a separate license or grant;
5. a later voluntary legacy-confirmation signed by the actual rightsholder; or
6. a determination that the material is not copyright-protectable or is not needed.

The basis should be recorded, not guessed.

## 3. Migration inventory

For each repository, produce an inventory containing at minimum:

- commit/PR or imported-source identifier;
- author/committer identity as recorded;
- material/path class;
- applicable outbound license at that time;
- applicable contribution/inbound terms at that time;
- known employer/entity ownership issue;
- third-party/imported status;
- rights basis confidence/status; and
- remediation needed, if any.

Large generated or mechanical commits may be grouped if the grouping method is reproducible.

## 4. Repository priorities

### ECL

Highest legal priority because the project intends to ship a public legal instrument and its own LAR-10 review requires a defensible contributor/inbound-rights model.

Review at least:

- root `LICENSE` authorship history;
- `spec/**` legal/governance text;
- exact historical license snapshots;
- material code/tooling contributions that may be distributed with ECL; and
- substantive third-party legal drafting, if any.

The existing draft grant in ECL `CONTRIBUTING.md` is evidence of an intended inbound model, but its legal effect must be evaluated against when and how contributors actually submitted material and whether they had notice/authority.

### Exergism

The current repository states that contributors retain rights and contribute under the target material's CC BY-SA 4.0 or Apache-2.0 license. Migration should verify imported/canonical source provenance and any contributions predating the current explicit boundary.

### ECL-PL

Review copyright provenance of architecture/specification text separately from patents. **Never infer a patent grant from a historical Git contribution.**

## 5. Voluntary legacy confirmation

The organization may offer a contributor an exact statement such as:

> I confirm that the Contributions identified in the attached immutable list/hash are also licensed under EC-ICLA 1.0 and Project Schedule X, effective on the date of this confirmation. This does not alter rights already granted to recipients under earlier licenses.

The actual production text must be legally reviewed and must identify the covered contributions precisely enough to avoid accidental capture of unrelated work.

## 6. Missing or unreachable contributors

If a material historical contribution lacks a defensible rights basis and the rightsholder cannot be reached, options include:

- rewrite/remove the material;
- obtain rights from another actual rightsholder where legally sufficient;
- isolate the material under its existing valid license rather than claim broader rights;
- preserve it only as historical evidence where legally permitted; or
- accept a documented limitation if qualified counsel concludes the project can lawfully do so.

Do not fabricate consent.

## 7. No rewriting released history

A provenance correction may change what a future release includes. It must not rewrite the license under which a historical public release was actually distributed or force-move immutable release tags.

## 8. Completion evidence

A legacy-rights migration should end with a versioned report identifying:

- scope reviewed;
- unresolved contributions;
- remediation performed;
- exact rights bases relied on; and
- limitations that remain.

For ECL 1.0, the qualified legal reviewers should receive this report as part of LAR-10 chain-of-title review.
