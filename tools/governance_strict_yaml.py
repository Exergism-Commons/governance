from __future__ import annotations

import re

import validate_governance as core


def _top_level_matches(text: str, key: str) -> list[tuple[int, str]]:
    matches: list[tuple[int, str]] = []
    for index, line in enumerate(text.splitlines()):
        if not line or line[0].isspace():
            continue
        if re.match(rf"^{re.escape(key)}\s*:", line):
            matches.append((index, line))
    core.require(len(matches) == 1, f"YAML top-level key must appear exactly once: {key}")
    return matches


def _direct_child_matches(block: str, key: str, label: str) -> list[str]:
    """Return exactly the direct mapping children named key.

    `yaml_block` preserves relative indentation, so a direct child of the
    selected parent begins at column zero while grandchildren remain indented.
    This prevents a nested decoy or duplicate first/last-wins interpretation
    from becoming authoritative.
    """
    matches: list[str] = []
    for line in block.splitlines():
        if not line or line[0].isspace():
            if re.match(rf"^{re.escape(key)}\s*:", line):
                matches.append(line)
    core.require(len(matches) == 1, f"YAML nested key must appear exactly once as a direct child: {label}.{key}")
    return matches


def yaml_scalar(text: str, key: str):
    (_, line), = _top_level_matches(text, key)
    raw = line.split(":", 1)[1].strip()
    if raw == "null":
        return None
    if raw == "true":
        return True
    if raw == "false":
        return False
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    return raw


def yaml_block(text: str, key: str) -> str:
    lines = text.splitlines()
    (index, line), = _top_level_matches(text, key)
    raw = line.split(":", 1)[1].strip()
    if raw:
        return raw

    children: list[str] = []
    for child in lines[index + 1 :]:
        if not child.strip():
            children.append("")
            continue
        if not child[0].isspace():
            break
        # A top-level block's direct YAML content begins after indentation.
        # Preserve relative indentation so nested consumers can distinguish
        # direct children from grandchildren.
        leading = len(child) - len(child.lstrip())
        core.require(leading >= 2, f"YAML block {key} child must be indented")
        children.append(child[2:])
    return "\n".join(children)


def yaml_nested_bool(text: str, parent: str, key: str) -> bool:
    block = yaml_block(text, parent)
    (line,) = _direct_child_matches(block, key, parent)
    raw = line.split(":", 1)[1].strip()
    core.require(raw in {"true", "false"}, f"YAML {parent}.{key} must be boolean")
    return raw == "true"


def install() -> None:
    core.yaml_scalar = yaml_scalar
    core.yaml_block = yaml_block
    core.yaml_nested_bool = yaml_nested_bool
