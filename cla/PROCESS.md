# CLA Acceptance, Verification and Records Process

> **Status: process draft.** It must not be enabled until the adoption gates in `ADOPTION.md` are complete.

## 1. Goals

The process should establish a defensible link between:

```text
human/entity identity
    -> accepted exact CLA version
    -> exact Project Schedule version
    -> GitHub contribution identity
    -> Contribution / commit / PR
```

while collecting as little non-public personal data as reasonably necessary.

## 2. Before activation

Do not enforce a CLA check until `../policy/cla-status.yaml` records `operative: true` and identifies:

- legal Steward;
- governing law;
- exact adopted CLA versions;
- exact Project Schedule version;
- effective date;
- accepted signature/acceptance method(s);
- controlled records location/process; and
- legal-review completion.

File presence is not activation.

## 3. Individual acceptance

The production workflow should:

1. display the exact immutable EC-ICLA text and Project Schedule;
2. identify the legal Steward;
3. require affirmative acceptance using a legally reviewed electronic-signature or clickwrap process;
4. verify a contact/identity link sufficient for recordkeeping;
5. allow the contributor to associate one or more GitHub identities/emails used for contribution checks;
6. record employer/entity implications; and
7. return a public-safe status such as `covered`, without exposing private identity documents.

A bare `Signed-off-by` line should not be treated as acceptance of a legally different CLA unless counsel has reviewed that exact mechanism and the contributor is clearly presented with the agreement being accepted.

## 4. Entity acceptance

For an entity:

1. verify exact legal entity name;
2. record jurisdiction/registration identifier where appropriate;
3. verify signatory authority;
4. execute EC-ECLA through the approved method;
5. maintain a controlled Authorized Contributor list; and
6. define how employees are added/removed without rewriting historical coverage.

An Entity CLA covers only rights the Entity actually owns or controls. If an individual owns relevant rights personally, the individual agreement or another valid grant may also be required.

## 5. Contribution check

A future automated check should resolve, in order:

1. repository and material class;
2. whether CLA coverage is required for that class;
3. exact contribution timestamp/base policy version;
4. contributor identity mapped to a valid individual or entity agreement;
5. exact CLA version accepted;
6. exact Project Schedule version applicable; and
7. any recorded exception or third-party review requirement.

The check should fail with a human-readable reason. It should never claim that missing CLA acceptance transfers rights, blocks ordinary issue discussion, or creates a patent problem.

## 6. What should require a CLA

Default proposed rule after activation:

- pull requests/commits/patches intended for incorporation: yes;
- direct maintainer commits: yes, through contributor/committer coverage;
- substantive legal text proposed for merge: yes;
- ordinary issue reports, criticism, questions and external evidence links: no;
- third-party material submitted only for review: handled by third-party process, not by pretending the submitter owns it.

A repository may define narrower exceptions for trivial contributions after legal review.

## 7. Minors and legal incapacity

If the contributor cannot legally enter the Agreement alone, do not improvise. The records process must require an authorized parent/guardian or other legally sufficient representative process reviewed for the applicable jurisdiction.

## 8. Employer and client rights

A contributor should be prompted to consider whether an employer, client, university or sponsor owns the relevant work product.

Where ownership is uncertain, maintainers should pause acceptance of the affected Contribution rather than assume that an individual's CLA defeats employment or commissioned-work rules.

## 9. Third-party material

Third-party content should use a separate provenance path. The record should identify:

- source;
- rightsholder where known;
- exact license/permission;
- version/hash where material;
- compatibility decision; and
- any attribution/notice obligations.

## 10. Public registry versus private evidence

A public CLA-status registry may contain only operational data, for example:

```text
github_login
coverage: individual | entity
agreement_version
project_schedule_version
effective_from
status
```

Do not publicly commit residential addresses, government IDs, signatures, private emails or employer documents solely to prove acceptance.

## 11. Record durability

Agreement and adoption records should be immutable or content-addressed once effective. Corrections should append a superseding record rather than rewrite history silently.

The organization should be able to reconstruct why a particular Contribution was accepted years later even if automation vendors, repositories or GitHub account names change.

## 12. Exceptions

Any exception that allows a Contribution to merge without ordinary CLA coverage should state its rights basis, for example:

- material is uncopyrightable/trivial;
- valid upstream license already provides sufficient rights;
- actual rightsholder executed a separate grant;
- contribution predates CLA and is covered by a legacy rights basis; or
- qualified legal review approved another route.

`Maintainer knows the person` is not a rights basis.
