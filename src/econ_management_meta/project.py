"""Project initialization and structural validation."""

from __future__ import annotations

import csv
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from . import __version__
from .errors import ErrorCode, WorkflowError
from .io import read_json, read_yaml, write_json, write_yaml
from .profile import load_profile

STAGE_NAMES: tuple[str, ...] = (
    "00_intake",
    "01_protocol",
    "02_search",
    "03_screening",
    "04_fulltext",
    "05_extraction",
    "06_construct_alignment",
    "07_estimand_alignment",
    "08_effect_size",
    "09_analysis_spec",
    "10_synthesis",
    "11_heterogeneity",
    "12_missing_evidence",
    "13_evidence_appraisal",
    "14_reporting",
    "15_publication_qa",
)

_SUPPORT_DIRECTORIES: tuple[str, ...] = (
    "state",
    "locks",
    "data/raw",
    "data/interim",
    "data/verified",
    "analysis/results",
    "manuscript",
    "profiles/active",
)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "meta-analysis-project"


def _schema_errors(instance: object, schema: dict[str, Any]) -> list[dict[str, str]]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        {
            "path": ".".join(str(part) for part in error.absolute_path),
            "message": error.message,
        }
        for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path))
    ]


def initialize_project(
    topic: str,
    profile_dir: Path,
    output_dir: Path,
    schema_dir: Path,
) -> Path:
    """Create a deterministic file-first project without overwriting user data."""

    if output_dir.exists() and any(output_dir.iterdir()):
        raise WorkflowError(
            ErrorCode.PATH_NOT_EMPTY,
            "output directory is not empty",
            {"path": str(output_dir.resolve())},
        )

    profile = load_profile(profile_dir, schema_dir / "profile.schema.json")
    output_dir.mkdir(parents=True, exist_ok=True)

    for relative in (*STAGE_NAMES, *_SUPPORT_DIRECTORIES):
        (output_dir / relative).mkdir(parents=True, exist_ok=True)

    project_id = _slugify(topic)
    created_at = datetime.now(timezone.utc).isoformat()
    project_manifest: dict[str, object] = {
        "project_id": project_id,
        "topic": topic,
        "created_at": created_at,
        "core_version": __version__,
        "profile": {"id": profile.id, "version": profile.version},
        "normative_language": "en",
        "current_stage": "00_intake",
    }
    write_yaml(output_dir / "project.yaml", project_manifest)

    pipeline_state: dict[str, object] = {
        "schema_version": 1,
        "project_id": project_id,
        "stages": {name: {"status": "NOT_STARTED"} for name in STAGE_NAMES},
        "history": [],
    }
    write_yaml(output_dir / "state/pipeline-state.yaml", pipeline_state)
    write_json(
        output_dir / "state/artifact-manifest.json",
        {"schema_version": 1, "project_id": project_id, "artifacts": []},
    )

    with (output_dir / "state/decision-log.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "decision_id",
                "timestamp",
                "actor",
                "stage",
                "decision_type",
                "decision",
                "rationale",
                "human_verified",
            ]
        )

    active_profile = output_dir / "profiles/active"
    for source in profile_dir.rglob("*"):
        relative = source.relative_to(profile_dir)
        target = active_profile / relative
        if source.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    validate_project(output_dir, schema_dir)
    return output_dir


def validate_project(project_dir: Path, schema_dir: Path) -> dict[str, object]:
    """Validate the project manifest, pipeline state, and mandatory artifacts."""

    required = [
        project_dir / "project.yaml",
        project_dir / "state/pipeline-state.yaml",
        project_dir / "state/decision-log.csv",
        project_dir / "state/artifact-manifest.json",
        project_dir / "profiles/active/profile.yaml",
    ]
    missing = [str(path.relative_to(project_dir)) for path in required if not path.exists()]
    if missing:
        raise WorkflowError(
            ErrorCode.PROJECT_SCHEMA_INVALID,
            "project is missing mandatory artifacts",
            {"missing": missing},
        )

    manifest = read_yaml(project_dir / "project.yaml")
    state = read_yaml(project_dir / "state/pipeline-state.yaml")
    artifact_manifest = read_json(project_dir / "state/artifact-manifest.json")

    errors = {
        "project": _schema_errors(manifest, read_json(schema_dir / "project.schema.json")),
        "state": _schema_errors(state, read_json(schema_dir / "pipeline-state.schema.json")),
    }
    errors = {name: value for name, value in errors.items() if value}
    if errors:
        raise WorkflowError(
            ErrorCode.PROJECT_SCHEMA_INVALID,
            "project does not satisfy its schemas",
            {"errors": errors},
        )

    if artifact_manifest.get("project_id") != manifest.get("project_id"):
        raise WorkflowError(
            ErrorCode.PROJECT_SCHEMA_INVALID,
            "artifact manifest belongs to a different project",
            {"path": "state/artifact-manifest.json"},
        )

    active_profile = load_profile(
        project_dir / "profiles/active",
        schema_dir / "profile.schema.json",
    )
    expected_profile = manifest["profile"]
    if {"id": active_profile.id, "version": active_profile.version} != expected_profile:
        raise WorkflowError(
            ErrorCode.PROJECT_SCHEMA_INVALID,
            "active profile does not match the project manifest",
            {
                "expected": expected_profile,
                "actual": {"id": active_profile.id, "version": active_profile.version},
            },
        )

    from .locks import verify_lock

    lock_paths = sorted((project_dir / "locks").glob("*.lock.yaml"))
    for lock_path in lock_paths:
        verify_lock(project_dir, lock_path)

    return {
        "valid": True,
        "project_id": manifest["project_id"],
        "profile": manifest["profile"],
        "current_stage": manifest["current_stage"],
        "locks_verified": len(lock_paths),
    }
