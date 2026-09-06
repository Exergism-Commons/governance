from __future__ import annotations

import json
from pathlib import Path

import governance_interrelease_integrity as interrelease
import validate_governance as core


_INSTALLED = False


def _json_object_if_any(path: Path) -> dict | None:
    """Read any valid JSON object regardless of filename suffix.

    Canonical ``*.json`` decision files retain the existing fail-closed parser:
    malformed JSON there is an integrity error. Other regular files are probed
    so a valid adopted membership record cannot evade closure merely by using a
    different suffix. Non-JSON auxiliary files are ignored.
    """
    relative = path.relative_to(core.ROOT).as_posix()
    if path.suffix.lower() == ".json":
        data = core.load_json(relative)
        core.require(isinstance(data, dict), f"decision record JSON must be an object: {relative}")
        return data

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def discover_membership_records() -> tuple[list[tuple[str, dict]], list[tuple[str, dict]]]:
    """Discover adopted membership events independently of filename suffix."""
    root = core.ROOT / "records" / "decisions"
    if not root.is_dir():
        return [], []

    admissions: list[tuple[str, dict]] = []
    transitions: list[tuple[str, dict]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        data = _json_object_if_any(path)
        if data is None or data.get("status") != "adopted":
            continue
        record_type = data.get("record_type")
        if record_type not in {"membership-admission", "membership-state-transition"}:
            continue
        relative = path.relative_to(core.ROOT).as_posix()
        person_id = data.get("person_id")
        core.require(
            isinstance(person_id, str) and person_id.strip(),
            f"membership record person_id missing: {relative}",
        )
        ref = {
            "path": relative,
            "sha256": core.sha256_file(path),
        }
        target = admissions if record_type == "membership-admission" else transitions
        target.append((person_id, ref))
    return admissions, transitions


def install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    interrelease.discover_membership_records = discover_membership_records
    _INSTALLED = True
