"""Human-verified report-family and study-family reconciliation."""

from __future__ import annotations

import csv
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from .errors import ErrorCode, WorkflowError
from .io import read_json
from .tabular import append_unique_row, read_csv_rows, require_human_actor, stable_id

_ASSIGNMENT_HEADERS = (
    "assignment_id", "timestamp", "report_id", "report_family_id", "study_id",
    "version_role", "assigned_by", "evidence", "human_verified",
)
_MAP_HEADERS = (
    "report_id", "report_family_id", "study_id", "version_role", "assigned_by",
    "evidence", "human_verified",
)


def _assignment_path(project_dir: Path) -> Path:
    return project_dir / "04_fulltext/report-family-assignments.csv"


def _validate(payload: Mapping[str, object], schema_dir: Path) -> None:
    validator = Draft202012Validator(
        read_json(schema_dir / "report-family.schema.json"),
        format_checker=FormatChecker(),
    )
    errors = sorted(validator.iter_errors(dict(payload)), key=lambda item: list(item.absolute_path))
    if errors:
        raise WorkflowError(
            ErrorCode.REPORT_FAMILY_INVALID,
            "report-family assignment does not satisfy its schema",
            {"errors": [{"path": ".".join(map(str, error.absolute_path)), "message": error.message} for error in errors]},
        )


def assign_report_family(
    project_dir: Path,
    report_id: str,
    report_family_id: str,
    study_id: str,
    version_role: str,
    actor: str,
    evidence: str,
    schema_dir: Path,
) -> str:
    assigned_by = require_human_actor(actor)
    if len(evidence.strip()) < 5:
        raise WorkflowError(
            ErrorCode.REPORT_FAMILY_INVALID,
            "report-family assignments require explicit supporting evidence",
            {"report_id": report_id},
        )
    existing = read_csv_rows(_assignment_path(project_dir))
    prior = next((row for row in existing if row["report_id"] == report_id), None)
    if prior is not None:
        raise WorkflowError(
            ErrorCode.REPORT_FAMILY_INVALID,
            "a report can have only one active report-family and study assignment",
            {
                "report_id": report_id,
                "existing_report_family_id": prior["report_family_id"],
                "existing_study_id": prior["study_id"],
            },
        )

    payload: dict[str, object] = {
        "assignment_id": stable_id("RFA", report_id, report_family_id, study_id),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "report_id": report_id,
        "report_family_id": report_family_id,
        "study_id": study_id,
        "version_role": version_role.upper(),
        "assigned_by": assigned_by,
        "evidence": evidence.strip(),
        "human_verified": True,
    }
    _validate(payload, schema_dir)
    append_unique_row(
        _assignment_path(project_dir),
        _ASSIGNMENT_HEADERS,
        payload,
        ("report_id",),
    )
    return str(payload["assignment_id"])


def validate_report_families(project_dir: Path) -> dict[str, object]:
    rows = read_csv_rows(_assignment_path(project_dir))
    report_ids = [row["report_id"] for row in rows]
    if len(report_ids) != len(set(report_ids)):
        raise WorkflowError(
            ErrorCode.REPORT_FAMILY_INVALID,
            "a report appears in more than one assignment",
            {},
        )
    return {
        "valid": True,
        "reports": len(rows),
        "report_families": len({row["report_family_id"] for row in rows}),
        "studies": len({row["study_id"] for row in rows}),
    }


def export_report_family_map(project_dir: Path) -> Path:
    validate_report_families(project_dir)
    rows = sorted(read_csv_rows(_assignment_path(project_dir)), key=lambda row: row["report_id"])
    path = project_dir / "04_fulltext/report-family-map.csv"
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(_MAP_HEADERS))
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in _MAP_HEADERS})
    temporary.replace(path)
    return path
