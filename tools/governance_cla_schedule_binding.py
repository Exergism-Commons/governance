from __future__ import annotations

import re

import validate_governance as core


BASE_VALIDATE_COVERED_PROJECTS = core.validate_covered_projects


def nested_yaml_scalar(text: str, key: str):
    pattern = re.compile(rf"^\s*{re.escape(key)}:\s*(.*?)\s*$")
    for raw in text.splitlines():
        match = pattern.match(raw)
        if not match:
            continue
        value = match.group(1)
        if value == "true":
            return True
        if value == "false":
            return False
        if value in {"null", "~"}:
            return None
        return value.strip("'\"")
    raise SystemExit(f"governance integrity failure: YAML missing nested key: {key}")


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


def parse_projection_coverage(text: str) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    current_repo: str | None = None
    for raw in text.splitlines():
        stripped = raw.strip()
        if stripped.startswith("- repository:"):
            repository = stripped.split(":", 1)[1].strip()
            core.require(repository and repository not in result, f"covered-projects duplicate/invalid repository: {repository}")
            current_repo = repository
            result[current_repo] = set()
            continue
        if current_repo is not None and stripped.startswith("- id:"):
            material_id = stripped.split(":", 1)[1].strip().strip("'\"")
            core.require(material_id and material_id not in result[current_repo], f"covered-projects duplicate/invalid material class: {current_repo}/{material_id}")
            result[current_repo].add(material_id)

    core.require(result, "covered-projects contains no repository coverage")
    for repository, material_ids in result.items():
        core.require(material_ids, f"covered-projects repository has no material classes: {repository}")
    return result


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

    contract = nested_yaml_scalar(projects_text, "authoritative_schedule_artifact")
    core.require(contract == schedule_artifact, "covered-projects schedule binding points to wrong artifact")
    core.require(nested_yaml_scalar(projects_text, "exact_repository_set_required") is True, "covered-projects exact repository-set binding disabled")
    core.require(nested_yaml_scalar(projects_text, "exact_material_class_id_set_per_repository_required") is True, "covered-projects exact material-class binding disabled")


def validate_covered_projects(status_text: str, projects_text: str) -> str:
    recorded = BASE_VALIDATE_COVERED_PROJECTS(status_text, projects_text)
    validate_schedule_projection_manifest(status_text, projects_text)
    return recorded
