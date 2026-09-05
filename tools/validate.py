#!/usr/bin/env python3
"""Canonical complete Exergism Commons governance-integrity entrypoint.

Do not use validate_governance.py directly as an activation verdict: it is the
core validator extended here by temporal, release-history, lifecycle, strict
parsing, Open Knowledge, inter-release history, and other authority wrappers.
"""

import governance_interrelease_integrity as interrelease
import validate_governance_temporal as temporal


def main() -> None:
    # Install the inter-release wrappers before the temporal entry point binds
    # module callbacks into the core validator. Repository-history validation is
    # part of the same canonical verdict: once governance is operative, a caller
    # must supply the trusted merge/push base so committed records cannot be
    # silently rewritten or removed between releases.
    interrelease.install()
    interrelease.validate_repository_history()
    temporal.main()


if __name__ == "__main__":
    main()
