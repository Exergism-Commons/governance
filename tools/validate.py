#!/usr/bin/env python3
"""Canonical complete Exergism Commons governance-integrity entrypoint.

Do not use validate_governance.py or validate_governance_temporal.py directly as
an activation verdict: they are internal components extended here by temporal,
release-history, lifecycle, strict parsing, Open Knowledge, inter-release
history, prospective delegation-policy, and other authority wrappers.
"""

import governance_interrelease_integrity as interrelease
import validate_governance_temporal as temporal


def main() -> None:
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
    # current-policy reservation of actions granted by older releases.
    temporal.main()


if __name__ == "__main__":
    main()
