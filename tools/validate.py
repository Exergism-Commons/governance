#!/usr/bin/env python3
"""Canonical complete Exergism Commons governance-integrity entrypoint.

Do not use validate_governance.py directly as an activation verdict: it is the
core validator extended here by temporal, release-history, lifecycle, strict
parsing, Open Knowledge, and other authority wrappers.
"""

from validate_governance_temporal import main


if __name__ == "__main__":
    main()
