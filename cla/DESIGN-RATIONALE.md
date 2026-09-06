# CLA Design Rationale

> **Status: design note, not operative legal text.**

## 1. Problem being solved

Exergism Commons has moved from a single-author/project-development setting toward a multi-repository institution with mixed philosophical, software, semantic, governance and legal artifacts.

The current repositories do not share one simple rights model:

- Exergism expressly preserves contributor ownership and uses CC BY-SA 4.0 / Apache-2.0 by material class.
- ECL has a draft inbound contribution term and an explicit legal-review requirement to test chain of title and contributor enforcement authority.
- ECL-PL requires patent rights to remain separate and express.
- organization-level repositories do not yet all have a repository-wide outbound license.

The design therefore needs **one contributor relationship without one fake universal outbound license**.

## 2. Why a license, not assignment

Exergism's existing governance says repository stewardship does not transfer contributor copyright and that copyright assignment is not required merely to participate.

The CLA follows that rule. Contributors retain ownership and grant a non-exclusive license sufficient for project continuity.

This also reduces capture risk: institutional continuity does not require making the organization the exclusive owner of community work.

## 3. Why the inbound grant is broader than a simple DCO-style certification

A provenance certification can establish that a submitter believes they have the right to contribute under an existing license. That is useful, but ECL has an additional problem: it is itself an evolving legal instrument and needs explicit permission to incorporate drafting contributions into future ECL versions and supporting legal/governance materials.

A signed, versioned copyright license makes that permission clearer than relying only on commit sign-offs.

The Linux Foundation's DCO 1.1 is also written around contribution under an `open source license`. ECL explicitly states that it is not OSI-approved Open Source, so copying the DCO model as the organization-wide legal basis would create unnecessary mismatch.

## 4. Why constrained outbound relicensing

Contributor agreements such as the Harmony templates distinguish the **inbound grant** from choices about the project's **outbound license**. That distinction is useful here.

An unlimited right to relicense every Contribution under any terms would be difficult to reconcile with Exergism's anti-capture governance. A grant that is too narrow, however, could make legitimate future ECL legal-version development impossible.

The selected compromise is:

- broad non-exclusive rights necessary to maintain the project;
- a Project Schedule that defines allowed outbound licenses/families by material class; and
- no retroactive expansion of that outbound family without rights already reserved or separate contributor consent.

## 5. Why separate individual and entity agreements

Employment and commissioned-work rules can place copyright in an employer or other entity even when an individual wrote the code/text. Major contributor-agreement systems therefore distinguish individual and corporate/entity coverage.

The Entity CLA grants only rights the entity owns or controls. Where rights are split, both individual and entity coverage may be required.

## 6. Why the CLA grants no patents

This is not an accidental omission.

ECL-PL architecture currently states that:

- ECL contributor status does not make a person a Patent Licensor;
- contribution to the ECL-PL repository does not itself grant patent rights; and
- patent grants must be express, attributable and bounded.

A universal CLA patent clause would collide with that architecture and risk turning an inbound copyright process into a shadow patent instrument.

Where Target Material is Apache-2.0 software, Apache-2.0's own patent provisions may apply according to that license. Where a contributor wants to make an ECL-PL grant, the contributor should execute the patent-specific instrument. The CLA stays out of the middle.

## 7. Why issue comments are not automatically Contributions

ECL governance depends on criticism, contrary evidence and public challenge. Treating every issue comment as a licensable authored Contribution would create unnecessary friction and could deter adversarial review.

The CLA therefore covers material intentionally offered for incorporation. Ordinary discussion/evidence remains ordinary public participation unless the author expressly offers text for inclusion.

## 8. Why legal-steward identity is an activation blocker

A GitHub organization is an account/namespace, not evidence of which natural or legal person is entering a contract.

The production CLA must name a competent receiving party. If Exergism Commons later operates through an association, foundation, company or another legal form, the adopted agreement should identify that exact legal steward and its authority.

The draft avoids pretending this unresolved institutional fact is already settled.

## 9. Why legacy contributions need a separate migration

A CLA adopted tomorrow cannot retroactively create consent yesterday. Existing commits must be supported by their historical license/contribution terms or later voluntary confirmation.

This is particularly important for ECL's LAR-10 chain-of-title review.

## 10. Reference models reviewed

This design was informed by established public contributor-rights approaches, especially:

- Apache Software Foundation individual/corporate CLAs — rights-retained contributor agreements and separate entity treatment;
- Project Harmony — explicit separation of inbound rights from outbound-license choices;
- Eclipse Contributor Agreement — provenance, target-project licensing and persistent contribution records; and
- Developer Certificate of Origin 1.1 — lightweight provenance certification and Git sign-off model.

These are references, not adopted text. The Exergism Commons agreements require independent legal review for the organization's actual jurisdictions and project model.
