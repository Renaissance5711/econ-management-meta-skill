"""Versioned protocol and amendment management."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .errors import ErrorCode, WorkflowError
from .io import read_json, read_yaml, write_yaml
from .tabular import append_unique_row, require_human_actor, stable_id

_AMENDMENT_HEADERS = (
    "amendment_id",
    "created_at",
    "approved_by",
    "from_version",
    "to_version",
    "change_type",
    "confirmatory_status_after_change",
    "path",
)


def _validate(data: Mapping[str, object], schema_path: Path, code: ErrorCode) -> None:
    schema = read_json(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(dict(data)), key=lambda item: list(item.absolute_path))
    if errors:
        raise WorkflowError(
            code,
            "artifact does not satisfy its schema and safety contract",
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


def create_protocol(
    project_dir: Path,
    version: str,
    protocol: Mapping[str, object],
    actor: str,
    schema_dir: Path,
) -> Path:
    """Create one immutable approved protocol version."""

    approved_by = require_human_actor(actor)
    path = project_dir / "01_protocol" / f"protocol-v{version}.yaml"
    if path.exists():
        raise WorkflowError(
            ErrorCode.ARTIFACT_ALREADY_EXISTS,
            "protocol versions are immutable and cannot be overwritten",
            {"path": str(path)},
        )

    payload: dict[str, object] = {
        "version": version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "approved_by": approved_by,
        "status": "APPROVED",
        **dict(protocol),
    }
    _validate(payload, schema_dir / "protocol.schema.json", ErrorCode.PROTOCOL_INVALID)
    write_yaml(path, payload)
    return path


def validate_protocol(path: Path, schema_dir: Path) -> dict[str, object]:
    payload = read_yaml(path)
    _validate(payload, schema_dir / "protocol.schema.json", ErrorCode.PROTOCOL_INVALID)
    return {
        "valid": True,
        "version": payload["version"],
        "approved_by": payload["approved_by"],
    }


def list_protocol_versions(project_dir: Path) -> list[str]:
    versions = [path.stem.removeprefix("protocol-v") for path in (project_dir / "01_protocol").glob("protocol-v*.yaml")]
    return sorted(versions, key=lambda value: tuple(int(part) for part in value.split(".")))


def create_amendment(
    project_dir: Path,
    amendment: Mapping[str, object],
    actor: str,
    schema_dir: Path,
) -> Path:
    """Create an immutable, classified protocol amendment."""

    approved_by = require_human_actor(actor)
    from_version = str(amendment.get("from_version", ""))
    if from_version not in list_protocol_versions(project_dir):
        raise WorkflowError(
            ErrorCode.AMENDMENT_INVALID,
            "the amendment source protocol version does not exist",
            {"from_version": from_version},
        )

    amendment_id = stable_id(
        "AMD",
        from_version,
        amendment.get("to_version"),
        amendment.get("original_rule"),
        amendment.get("new_rule"),
    )
    payload: dict[str, object] = {
        "amendment_id": amendment_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "approved_by": approved_by,
        **dict(amendment),
    }
    _validate(
        payload,
        schema_dir / "protocol-amendment.schema.json",
        ErrorCode.AMENDMENT_INVALID,
    )

    amendment_dir = project_dir / "01_protocol" / "amendments"
    path = amendment_dir / f"{amendment_id}.yaml"
    if path.exists():
        raise WorkflowError(
            ErrorCode.ARTIFACT_ALREADY_EXISTS,
            "this amendment has already been recorded",
            {"path": str(path)},
        )
    write_yaml(path, payload)
    append_unique_row(
        amendment_dir / "amendment-index.csv",
        _AMENDMENT_HEADERS,
        {
            "amendment_id": amendment_id,
            "created_at": payload["created_at"],
            "approved_by": approved_by,
            "from_version": payload["from_version"],
            "to_version": payload["to_version"],
            "change_type": payload["change_type"],
            "confirmatory_status_after_change": payload["confirmatory_status_after_change"],
            "path": path.relative_to(project_dir).as_posix(),
        },
        ("amendment_id",),
    )
    return path
