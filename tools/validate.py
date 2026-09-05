#!/usr/bin/env python3
"""Canonical complete Exergism Commons governance-integrity entrypoint.

Do not use validate_governance.py or validate_governance_temporal.py directly as
an activation verdict: they are internal components extended here by temporal,
release-history, lifecycle, strict parsing, Open Knowledge, inter-release
history, prospective delegation-policy, repository path integrity, and other
authority wrappers.
"""

import governance_path_integrity as path_integrity


def main() -> None:
    # Authority-bearing repository paths must be literal repository files, not
    # working-tree aliases. Reject symlink files and symlink parent directories
    # before importing/decoding any governance projection or content-addressed
    # evidence. This makes path identity part of the canonical verdict instead
    # of relying on individual call sites to remember not to follow links.
    path_integrity.validate_repository_paths()

    import governance_interrelease_integrity as interrelease
    import validate_governance_temporal as temporal

    # Install the first inter-release wrappers before importing the final
    # hardening layer: it deliberately composes on top of the historical
    # creation-policy validator installed here.
    interrelease.install()

    import governance_interrelease_hardening as interrelease_hardening

    interrelease_hardening.install()

    # Repository-history validation is part of the same canonical verdict.
    # It walks every committed transition after the trusted merge/push base,
    # rather than trusting only the base..HEAD endpoint diff, so an add-then-
    # delete/rewrite sequence cannot disappear inside a multi-commit range.
    interrelease_hardening.validate_repository_history()

    # temporal.main() installs the remaining release/lifecycle wrappers. It
    # consumes the hardened delegation callbacks above, including prospective
    # policy reservation of actions granted by older releases.
    temporal.main()


if __name__ == "__main__":
    main()
