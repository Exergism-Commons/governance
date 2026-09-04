from __future__ import annotations

import json

import validate_governance as core


_ORIGINAL_LOAD = json.load
_ORIGINAL_LOADS = json.loads
_INSTALLED = False


def _reject_duplicate_names(pairs):
    result = {}
    for key, value in pairs:
        core.require(key not in result, f"duplicate JSON object name rejected: {key}")
        result[key] = value
    return result


def strict_loads(source, *args, **kwargs):
    """Decode JSON with one interpretation only.

    Duplicate object names are rejected at every nesting level. A caller may
    not replace the object-pairs hook because doing so would re-introduce a
    first-wins/last-wins ambiguity into a content-addressed governance input.
    """
    supplied = kwargs.get("object_pairs_hook")
    core.require(supplied in (None, _reject_duplicate_names), "custom JSON object_pairs_hook is not permitted by governance integrity")
    kwargs["object_pairs_hook"] = _reject_duplicate_names
    return _ORIGINAL_LOADS(source, *args, **kwargs)


def strict_load(handle, *args, **kwargs):
    return strict_loads(handle.read(), *args, **kwargs)


def install() -> None:
    """Install duplicate-name rejection process-wide for the canonical verdict.

    The governance validator has JSON entry points in repository projections,
    content-addressed records and embedded machine manifests. Installing at the
    stdlib module boundary means a newly added json.load/json.loads call cannot
    silently become a weaker decoder than the existing paths.
    """
    global _INSTALLED
    if _INSTALLED:
        return
    json.load = strict_load
    json.loads = strict_loads
    _INSTALLED = True
