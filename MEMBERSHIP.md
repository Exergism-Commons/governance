# Exergism Commons Membership Policy

> **Status: 0.1-DRAFT — non-operative.** This policy defines a proposed membership system for EC. It creates no operative membership merely by existing in Git.

## 1. Membership model

EC voting membership is held by natural persons.

The default principle is:

> **one person = one Member = one vote**.

Votes are not weighted by donations, grants, employment, founder status, GitHub permissions, commit count, seniority or compensation.

Organizations may later be recognized as institutional participants, partners or rightsholders, but they do not receive a human governance vote merely because they fund or contract with EC.

## 2. Membership is not ownership

Membership creates no transferable share, dividend, claim on the Endowment, residual claim on Treasury assets or ownership interest in EC.

A Member may be compensated for genuine work under a lawful basis, but compensation is not a distribution of membership ownership.

## 3. Membership states

The Member Registry distinguishes at least:

- **Candidate** — application accepted for evaluation; no governance vote;
- **Active Member** — admitted Member with participation rights;
- **Inactive Member** — membership retained but excluded from ordinary voting denominators until reactivation;
- **Suspended Member** — temporarily restricted under a documented process;
- **Former Member** — resigned or membership validly terminated.

## 4. Admission criteria

Admission should require at least:

1. verified identity sufficient to enforce one-person-one-membership;
2. explicit acceptance of the EC constitutional framework and Mission Lock;
3. acceptance of conflict-of-interest and records/privacy rules;
4. evidence of meaningful good-faith participation in EC or an EC project;
5. no known unresolved conduct or rights-provenance issue incompatible with institutional participation; and
6. completion of the Candidate period where that period is applicable.

No payment, donation or purchase is required to become a Member.

A CLA signature alone is insufficient. Repository collaboration alone is insufficient. Funding EC is insufficient.

## 5. Candidate period

The default Candidate period is at least 30 days.

The Candidate period exists to make admission observable and contestable rather than instantaneous. It should include public or Member-visible notice of the candidacy, subject to privacy constraints.

A Candidate may contribute, participate in discussion and receive delegated technical roles, but Candidate status itself carries no institutional vote.

The Candidate period applies to every **post-formation** admission. Initial natural-person Members expressly identified in the legally competent constitutive adoption are a formation exception because no operative Member body exists before the institution is constituted. That exception cannot be reused after initial governance adoption and cannot be created later by relabelling an admission as “initial”.

## 6. Admission authority during institutional phases

### Initial constitutive registry

The first operative Member Registry may seat only the initial natural persons expressly identified by the legally competent governance-adoption record. Their membership effective date must equal the constitutive effective date, and the admission record must resolve to that exact content-addressed adoption record.

This formation mechanism is not an ordinary admission power. Once governance is operative, every additional Member follows the phase-specific process below.

### F0 — founder-led bootstrap

During operative F0, the Founding Steward may admit an additional Member who satisfies the admission criteria and has completed the Candidate period.

Each such admission must be individually recorded with:

- stable admission and person identifiers;
- Candidate start date and effective Active-Membership date;
- reasons and evidence addressing the admission criteria;
- the exact operative Founding Steward identity and authority used;
- a signature/acceptance record bound to the exact admission payload; and
- an immutable content-addressed decision record.

Batch admission for the purpose of controlling a known vote is prohibited.

### F1 and later

At F1 and later, admission requires Ordinary Approval of eligible non-conflicted Members after the Candidate period.

The admission decision must bind the Candidate start date, effective date, person identity and exact approval evidence. The approval evidence must be evaluated against the electorate that existed for that decision; the person being admitted cannot become part of that electorate merely because the same change also writes their future Active-Membership row.

The Founding Steward may raise a documented Mission Lock or integrity objection during the Founding Period. Such an objection must state specific grounds; it may not be based merely on disagreement with a Candidate's lawful position on an ordinary policy question.

## 7. Voting seasoning

Admission does not immediately unlock every voting class.

Unless a stricter domain rule applies:

- an Active Member may vote on Ordinary Approval after 30 days of Active Membership;
- an Active Member may vote on Qualified Approval after 90 days of Active Membership;
- an Active Member may vote on Constitutional Amendment after 90 days of Active Membership; and
- an Active Member may vote on a Mission-Locked Amendment after 180 days of Active Membership.

This rule reduces the risk of capture through rapid mass admission immediately before a consequential vote.

The relevant eligibility date is fixed when the formal voting window opens. Later admissions do not retroactively join that vote. `active_since` must be the effective date proved by the admission record; it cannot be independently backdated to manufacture seasoning.

## 8. Activity and inactivity

An Active Member should show at least one meaningful participation event during each rolling 12-month period. Participation may include governance work, project contribution, review, institutional operations, documented research, financial/administrative work or another substantive EC activity.

A Member with no qualifying activity for 12 months may be moved to Inactive status after notice.

Inactive status:

- does not terminate membership;
- removes the person from ordinary eligible-voter denominators while inactive;
- may be reversed through a documented reactivation process; and
- must not be used selectively to manipulate a pending vote.

Historical decision validation must use the Member state effective at the decision date rather than silently applying a later state change retroactively.

## 9. Conflicts and voting eligibility

Membership alone does not guarantee eligibility on every decision.

A Member is excluded from the effective eligible denominator only when the applicable conflict policy requires recusal, including decisions primarily determining that Member's own compensation, direct contract, sanction, claim or uniquely preferential private benefit.

Every machine-readable recusal used to change a voting denominator must resolve to a content-addressed conflict determination for the same person and decision. A vote envelope cannot manufacture a recusal merely by listing an opponent's identifier.

Recusal does not terminate membership.

## 10. Resignation, suspension and termination

A Member may resign at any time.

Temporary suspension may be used only for a documented integrity, safety, legal, provenance or process risk where delay would create material harm. Emergency suspension must be narrow, time-limited and reviewable.

Termination for cause requires:

- notice of the grounds;
- reasonable opportunity to respond;
- a recorded decision;
- Qualified Approval by non-conflicted eligible Members once F1 is operative; and
- a route to contest material factual errors.

During F0, the Founding Steward may terminate an initial membership only for documented cause and must preserve the record for later institutional review. Founder disagreement with ordinary policy preferences is not cause.

## 11. Anti-Sybil and anti-capture controls

The Member Registry should support one-person-one-membership without publishing unnecessary identity evidence.

The system should reject or flag:

- duplicate identities;
- fabricated or controlled proxy identities;
- coordinated bulk admissions intended to alter a known protected vote;
- funding-conditioned membership;
- employer-controlled voting instructions that convert institutional membership into a purchased voting bloc; and
- any representation that a GitHub account alone proves a unique legal person.

Reasonable privacy-preserving verification may be used. Full identity evidence should remain in controlled records rather than public Git.

## 12. Initial membership bootstrap

The proposed initial Founding Steward, Daniel Molinero Lucas, is the initial designated Member for bootstrap design purposes.

This designation is **not operative membership** until a legally competent adoption record creates the initial Member Registry and identifies the initial Member(s) expressly.

The first operative registry must record each initial Member individually rather than treating all repository collaborators or organization members as Members. The constitutive exception in Section 5 ends with that initial adoption.

## 13. Membership and roles are separate

Member status does not itself grant access to:

- Treasury or bank accounts;
- domain registrar or DNS recovery;
- repository administration;
- CLA records;
- private contributor identity data; or
- any other delegated operational capability.

Those authorities require separate role/delegation records.

Likewise, a Treasurer, maintainer, contractor or Domain Custodian is not automatically a Member.

## 14. Machine-readable registry

The canonical private Member Registry may contain identity evidence that is not public.

A public or repository-safe projection should expose only what is needed for governance audit, such as:

- stable Member record ID and stable natural-person identity key;
- membership state;
- Candidate and Active-Membership effective dates;
- admission mode and immutable admission record;
- voting-eligibility dates by class derived from `active_since`;
- role references where public;
- inactivity/suspension state; and
- hashes or references to controlled evidence rather than unnecessary personal data.

Automation may compute eligibility from adopted records. It must not infer membership from GitHub organization membership, repository permissions, funding records or CLA status.

A mutable current registry is not itself the authority for a historical change. Each admission, suspension, reactivation or termination must be supported by its own immutable decision record so the constitutional adoption record does not need to be rewritten whenever membership evolves.

## 15. Review and change

Changes to admission, termination, voting seasoning or anti-capture controls are Policy changes and must not be hidden inside editorial refactors.

A change that materially weakens protected-vote seasoning or enables funding/property-based voting should be treated as at least Qualified Approval once governance is operative.
