"""Versioned integrity locks for immutable research decisions."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from . import __version__
from .errors import ErrorCode, WorkflowError
from .io import read_json, read_yaml, sha256_data, sha256_file, write_yaml

_SUPPORTED_KINDS = {"protocol", "study-pool", "effect-size-pool", "analysis-spec"}


def _relative_artifact(project_dir: Path, artifact: Path) -> Path:
    project_root = project_dir.resolve()
    candidate = artifact.resolve()
    try:
        return candidate.relative_to(project_root)
    except ValueError as exc:
        raise WorkflowError(
            ErrorCode.LOCK_SCHEMA_INVALID,
            "lock artifacts must be inside the project directory",
            {"path": str(candidate)},
        ) from exc


def _validate_lock_data(lock_data: dict[str, Any], schema_path: Path) -> None:
    schema = read_json(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(lock_data), key=lambda item: list(item.absolute_path))
    if errors:
        raise WorkflowError(
            ErrorCode.LOCK_SCHEMA_INVALID,
            "lock file does not satisfy the integrity-lock schema",
            {
                "errors": [
                    {
                        "path": ".".join(str(part) for part in error.absolute_path),
                        "message": error.message,
                    }
                    for error in errors
                ]
            },
        )


def create_lock(
    project_dir: Path,
    kind: str,
    version: str,
    artifact_paths: Sequence[Path],
    actor: str,
) -> Path:
    """Create a versioned lock over one or more project artifacts."""

    if kind not in _SUPPORTED_KINDS:
        raise WorkflowError(
            ErrorCode.LOCK_SCHEMA_INVALID,
            "unsupported lock kind",
            {"kind": kind, "supported": sorted(_SUPPORTED_KINDS)},
        )
    if not artifact_paths:
        raise WorkflowError(
            ErrorCode.LOCK_SCHEMA_INVALID,
            "a lock requires at least one artifact",
            {"kind": kind},
        )

    artifacts: list[dict[str, str]] = []
    for artifact in artifact_paths:
        if not artifact.is_file():
            raise WorkflowError(
                ErrorCode.LOCK_SCHEMA_INVALID,
                "lock artifact does not exist",
                {"path": str(artifact)},
            )
        relative = _relative_artifact(project_dir, artifact)
        artifacts.append({"path": relative.as_posix(), "sha256": sha256_file(artifact)})
    artifacts.sort(key=lambda item: item["path"])

    lock_data: dict[str, Any] = {
        "kind": kind,
        "version": version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": actor,
        "core_version": __version__,
        "artifacts": artifacts,
        "aggregate_sha256": sha256_data(artifacts),
    }
    schema_path = Path(__file__).resolve().parents[2] / "schemas/lock.schema.json"
    _validate_lock_data(lock_data, schema_path)

    lock_path = project_dir / "locks" / f"{kind}-v{version}.lock.yaml"
    if lock_path.exists():
        raise WorkflowError(
            ErrorCode.LOCK_SCHEMA_INVALID,
            "lock files are immutable and cannot be overwritten",
            {"path": str(lock_path)},
        )
    write_yaml(lock_path, lock_data)
    return lock_path


def verify_lock(project_dir: Path, lock_path: Path) -> dict[str, object]:
    """Verify that every locked artifact and the aggregate hash remain unchanged."""

    lock_data = read_yaml(lock_path)
    schema_path = Path(__file__).resolve().parents[2] / "schemas/lock.schema.json"
    _validate_lock_data(lock_data, schema_path)

    current: list[dict[str, str]] = []
    mismatches: list[dict[str, object]] = []
    for item in lock_data["artifacts"]:
        relative = Path(str(item["path"]))
        artifact = project_dir / relative
        if not artifact.is_file():
            mismatches.append({"path": relative.as_posix(), "reason": "missing"})
            continue
        actual_hash = sha256_file(artifact)
        current.append({"path": relative.as_posix(), "sha256": actual_hash})
        if actual_hash != item["sha256"]:
            mismatches.append(
                {
                    "path": relative.as_posix(),
                    "reason": "hash_changed",
                    "expected": item["sha256"],
                    "actual": actual_hash,
                }
            )

    current.sort(key=lambda item: item["path"])
    if not mismatches and sha256_data(current) != lock_data["aggregate_sha256"]:
        mismatches.append({"path": "<aggregate>", "reason": "aggregate_changed"})

    if mismatches:
        raise WorkflowError(
            ErrorCode.LOCK_STALE,
            "one or more locked artifacts changed after the lock was created",
            {"lock": str(lock_path), "mismatches": mismatches},
        )

    return {
        "valid": True,
        "kind": lock_data["kind"],
        "version": lock_data["version"],
        "aggregate_sha256": lock_data["aggregate_sha256"],
    }
