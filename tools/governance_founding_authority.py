from __future__ import annotations

import validate_governance as core
import validate_governance_lifecycle as life
import governance_temporal_phase as phase
import governance_founding_lifecycle as founding_lifecycle


def validate_member_admission_record(item, membership, status, rules, founding) -> None:
    phase.validate_member_admission_record(item, membership, status, rules, founding)
    if status.get("operative") is not True or item.get("admission_mode") != "f0-founding-steward-admission":
        return
    record, _ = core.validate_content_ref(item.get("admission_record"), f"member admission {item['person_id']}", "records/decisions")
    decision_date = core.parse_iso_date(record.get("decision_date"), f"member admission {item['person_id']}.decision_date")
    core.require(
        founding_lifecycle.founding_steward_active_on(status, founding, rules, membership, decision_date),
        f"member admission {item['person_id']} cannot use Founding Steward authority after that assignment ended",
    )


def validate_f0_signed_membership_actions(status: dict, founding: dict, rules: dict, membership: dict) -> None:
    # Validate the role projection even when no F0 action happens in this snapshot.
    founding_lifecycle.validate_founding_steward_lifecycle(status, founding, rules, membership)
    if status.get("operative") is not True:
        return
    phase_evidence = core.load_json("policy/phase-evidence.json")
    for person_id, item in core.member_index(membership).items():
        if item.get("admission_mode") == "f0-founding-steward-admission":
            record, _ = core.validate_content_ref(item.get("admission_record"), f"member admission {person_id}", "records/decisions")
            decision_date = core.parse_iso_date(record.get("decision_date"), f"member admission {person_id}.decision_date")
            actual = phase.phase_as_of(status, phase_evidence, decision_date)
            if actual == "F0-founder-led-bootstrap":
                core.require(
                    founding_lifecycle.founding_steward_active_on(status, founding, rules, membership, decision_date),
                    f"member admission {person_id} was signed outside the Founding Steward authority interval",
                )
        for index, ref in enumerate(life.transition_records(item)):
            transition = life.load_transition(ref, person_id, index)
            if transition.get("transition_type") != "termination":
                continue
            decision_date = core.parse_iso_date(transition.get("decision_date"), f"member {person_id} transition {index}.decision_date")
            actual = phase.phase_as_of(status, phase_evidence, decision_date)
            if actual != "F0-founder-led-bootstrap":
                continue
            core.require(
                founding_lifecycle.founding_steward_active_on(status, founding, rules, membership, decision_date),
                f"member {person_id} F0 termination was signed outside the Founding Steward authority interval",
            )
