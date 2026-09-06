from __future__ import annotations

import validate_governance as core
import governance_release_history as history


BASE_VALIDATE_MEMBER_ADMISSION_RECORD = None


def validate_member_admission_record(item, membership, status, rules, founding) -> None:
    if status.get("operative") is True and item.get("admission_mode") == "constitutive-initial-member":
        history.validate_constitutive_initial_member(item, status)
        return

    core.require(callable(BASE_VALIDATE_MEMBER_ADMISSION_RECORD), "base Member admission validator missing")
    BASE_VALIDATE_MEMBER_ADMISSION_RECORD(item, membership, status, rules, founding)
