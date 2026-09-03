from __future__ import annotations

import re

import validate_governance as core


def block_scalar(text: str, parent: str, key: str):
    """Read exactly one direct child scalar from a named top-level YAML mapping block."""
    block = core.yaml_block(text, parent)
    matches = []
    pattern = re.compile(rf"^{re.escape(key)}:\s*(.*?)\s*$")
    for raw in block.splitlines():
        if raw and raw[0].isspace():
            continue
        match = pattern.match(raw)
        if match:
            matches.append(match.group(1))
    core.require(len(matches) == 1, f"YAML requires exactly one direct {parent}.{key}")
    value = matches[0]
    if value == "true":
        return True
    if value == "false":
        return False
    if value in {"null", "~"}:
        return None
    return value.strip("'\"")


def block_list(text: str, parent: str, key: str) -> list[str]:
    """Read exactly one direct child sequence from a named top-level mapping block."""
    block = core.yaml_block(text, parent)
    lines = block.splitlines()
    roots = [
        index
        for index, raw in enumerate(lines)
        if raw == f"{key}:"
    ]
    core.require(len(roots) == 1, f"YAML requires exactly one direct {parent}.{key}")
    values: list[str] = []
    for raw in lines[roots[0] + 1 :]:
        if not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip())
        if indent == 0:
            break
        stripped = raw.strip()
        core.require(indent == 2 and stripped.startswith("- "), f"{parent}.{key} must contain only direct scalar items")
        value = stripped[2:].strip().strip("'\"")
        core.require(value and value not in values, f"{parent}.{key} contains duplicate/empty item")
        values.append(value)
    core.require(values, f"{parent}.{key} must not be empty")
    return values


def parse_schedule_coverage(text: str) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    current_repo: str | None = None
    reading_material_classes = False

    for raw in text.splitlines():
        stripped = raw.strip()
        repo_match = re.fullmatch(r"Repository:\s*`([^`]+)`", stripped)
        if repo_match:
            current_repo = repo_match.group(1)
            core.require(current_repo not in result, f"Project Schedule duplicate repository: {current_repo}")
            result[current_repo] = set()
            reading_material_classes = False
            continue

        if stripped == "Schedule material classes:":
            core.require(current_repo is not None, "Project Schedule material-class manifest appears before repository")
            reading_material_classes = True
            continue

        if reading_material_classes:
            material_match = re.fullmatch(r"-\s*`([^`]+)`", stripped)
            if material_match:
                material_id = material_match.group(1)
                core.require(material_id not in result[current_repo], f"Project Schedule duplicate material class: {current_repo}/{material_id}")
                result[current_repo].add(material_id)
                continue
            if stripped:
                reading_material_classes = False

    core.require(result, "Project Schedule contains no repository coverage manifest")
    for repository, material_ids in result.items():
        core.require(material_ids, f"Project Schedule repository has no material-class IDs: {repository}")
    return result


def parse_projection_repositories(text: str) -> dict[str, dict]:
    """Parse only authoritative direct fields beneath the top-level repositories sequence."""
    lines = text.splitlines()
    repository_roots = [index for index, raw in enumerate(lines) if raw == "repositories:"]
    core.require(len(repository_roots) == 1, "covered-projects requires exactly one top-level repositories block")

    result: dict[str, dict] = {}
    current_repo: str | None = None
    material_block_open = False
    material_block_seen: set[str] = set()

    for raw in lines[repository_roots[0] + 1 :]:
        if not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip())
        stripped = raw.strip()

        if indent == 0:
            break

        if stripped.startswith("- repository:"):
            core.require(indent == 2, "covered-projects repository entries must be direct items of repositories")
            repository = stripped.split(":", 1)[1].strip().strip("'\"")
            core.require(repository and repository not in result, f"covered-projects duplicate/invalid repository: {repository}")
            current_repo = repository
            result[current_repo] = {"cla_coverage": None, "material_ids": set()}
            material_block_open = False
            continue

        core.require(current_repo is not None, "covered-projects repositories block contains content before a repository entry")

        if stripped.startswith("cla_coverage:"):
            core.require(indent == 4, f"covered-projects {current_repo}.cla_coverage must be a direct repository child")
            core.require(result[current_repo]["cla_coverage"] is None, f"covered-projects duplicate cla_coverage: {current_repo}")
            state = stripped.split(":", 1)[1].strip().strip("'\"")
            core.require(state, f"covered-projects empty cla_coverage: {current_repo}")
            result[current_repo]["cla_coverage"] = state
            material_block_open = False
            continue

        if indent == 4 and stripped == "material_classes:":
            core.require(current_repo not in material_block_seen, f"covered-projects duplicate material_classes block: {current_repo}")
            material_block_seen.add(current_repo)
            material_block_open = True
            continue

        if indent <= 4:
            material_block_open = False

        if stripped.startswith("- id:"):
            core.require(
                material_block_open and indent == 6,
                f"covered-projects material id must be a direct item of {current_repo}.material_classes",
            )
            material_id = stripped.split(":", 1)[1].strip().strip("'\"")
            core.require(
                material_id and material_id not in result[current_repo]["material_ids"],
                f"covered-projects duplicate/invalid material class: {current_repo}/{material_id}",
            )
            result[current_repo]["material_ids"].add(material_id)

    core.require(result, "covered-projects contains no repository coverage")
    core.require(set(result) == material_block_seen, "every covered-projects repository requires exactly one material_classes block")
    for repository, data in result.items():
        core.require(data["cla_coverage"] is not None, f"covered-projects repository missing direct cla_coverage: {repository}")
        core.require(data["material_ids"], f"covered-projects repository has no material classes: {repository}")
    return result


def parse_projection_coverage(text: str) -> dict[str, set[str]]:
    return {
        repository: set(data["material_ids"])
        for repository, data in parse_projection_repositories(text).items()
    }


def validate_schedule_projection_manifest(status_text: str | None = None, projects_text: str | None = None) -> None:
    if status_text is None:
        status_text = (core.ROOT / "policy/cla-status.yaml").read_text(encoding="utf-8")
    if projects_text is None:
        projects_text = (core.ROOT / "policy/covered-projects.yaml").read_text(encoding="utf-8")

    schedule_artifact = core.yaml_scalar(status_text, "project_schedule_artifact")
    core.require(schedule_artifact == "cla/PROJECT-SCHEDULE.md", "Project Schedule canonical artifact path changed")
    schedule_text = core.repo_file(schedule_artifact, "project_schedule_artifact").read_text(encoding="utf-8")

    schedule = parse_schedule_coverage(schedule_text)
    projection = parse_projection_coverage(projects_text)
    core.require(set(projection) == set(schedule), "covered-projects repository set does not exactly match Project Schedule")
    for repository in sorted(schedule):
        core.require(
            projection[repository] == schedule[repository],
            f"covered-projects material-class set does not match Project Schedule for {repository}",
        )

    contract = block_scalar(projects_text, "schedule_binding_contract", "authoritative_schedule_artifact")
    core.require(contract == schedule_artifact, "covered-projects schedule binding points to wrong artifact")
    core.require(block_scalar(projects_text, "schedule_binding_contract", "exact_repository_set_required") is True, "covered-projects exact repository-set binding disabled")
    core.require(block_scalar(projects_text, "schedule_binding_contract", "exact_material_class_id_set_per_repository_required") is True, "covered-projects exact material-class binding disabled")


def validate_covered_projects(status_text: str, projects_text: str) -> str:
    artifact = core.yaml_scalar(status_text, "covered_projects_artifact")
    core.require(artifact == "policy/covered-projects.yaml", "covered-projects canonical artifact path changed")
    path = core.repo_file(artifact, "covered_projects_artifact")
    recorded = core.require_sha256(core.yaml_scalar(status_text, "covered_projects_sha256"), "covered_projects_sha256")
    core.require(core.sha256_file(path) == recorded, "covered-projects bytes do not match recorded SHA-256")
    core.require(core.yaml_scalar(projects_text, "schema_version") == "2", "unsupported covered-projects schema")
    schedule_version = str(core.yaml_scalar(status_text, "project_schedule_version"))
    core.require(core.yaml_scalar(projects_text, "schedule_version") == schedule_version, "covered-projects schedule version mismatch")
    core.require(core.yaml_scalar(projects_text, "operative") is True, "operative CLA requires operative covered-projects")
    core.require(core.yaml_scalar(projects_text, "status") in {"adopted", "operative"}, "operative covered-projects must be adopted/operative")

    final_states = set(block_list(projects_text, "coverage_state_contract", "final_states"))
    provisional_states = set(block_list(projects_text, "coverage_state_contract", "provisional_states"))
    core.require(final_states and not final_states.intersection(provisional_states), "covered-projects state contract invalid")

    repositories = parse_projection_repositories(projects_text)
    for repository, data in repositories.items():
        state = data["cla_coverage"]
        core.require(
            state in final_states and state not in provisional_states,
            f"covered-projects repository not final: {repository}={state}",
        )

    core.require(
        "current_outbound: unresolved" not in projects_text and "cla_outbound_family: unresolved" not in projects_text,
        "operative covered-projects cannot retain unresolved outbound terms",
    )
    validate_schedule_projection_manifest(status_text, projects_text)
    return recorded
