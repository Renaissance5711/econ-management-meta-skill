"""Dual extraction, conflict detection, and human-verified export."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .errors import ErrorCode, WorkflowError
from .io import read_json
from .tabular import append_unique_row, read_csv_rows, require_human_actor, stable_id

_ENTRY_HEADERS = (
    "extraction_id", "timestamp", "report_id", "study_id", "field_id", "extractor",
    "value_json", "source_page", "source_quote", "verification_status",
)
_RESOLUTION_HEADERS = (
    "resolution_id", "timestamp", "report_id", "study_id", "field_id", "resolver",
    "resolved_value_json", "rationale",
)
_VERIFIED_HEADERS = (
    "report_id", "study_id", "field_id", "resolved_value_json", "verification_status",
    "verified_by", "resolution_type", "source_pages", "source_quotes",
)


def _entry_path(project_dir: Path) -> Path:
    return project_dir / "05_extraction/extraction-entries.csv"


def _resolution_path(project_dir: Path) -> Path:
    return project_dir / "05_extraction/extraction-resolutions.csv"


def _key(row: Mapping[str, str]) -> tuple[str, str, str]:
    return row["report_id"], row["study_id"], row["field_id"]


def _canonical_value(value: object) -> str:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise WorkflowError(
            ErrorCode.EXTRACTION_INVALID,
            "extracted values must be JSON serializable",
            {"reason": str(exc)},
        ) from exc


def _validate(payload: Mapping[str, object], schema_dir: Path) -> None:
    validator = Draft202012Validator(
        read_json(schema_dir / "extraction-entry.schema.json"),
        format_checker=FormatChecker(),
    )
    errors = sorted(validator.iter_errors(dict(payload)), key=lambda item: list(item.absolute_path))
    if errors:
        raise WorkflowError(
            ErrorCode.EXTRACTION_INVALID,
            "extraction entry does not satisfy its schema",
            {"errors": [{"path": ".".join(map(str, error.absolute_path)), "message": error.message} for error in errors]},
        )


def record_extraction(
    project_dir: Path,
    report_id: str,
    study_id: str,
    field_id: str,
    extractor: str,
    value: object,
    source_page: str,
    source_quote: str,
    schema_dir: Path,
) -> str:
    extractor = require_human_actor(extractor)
    payload: dict[str, object] = {
        "extraction_id": stable_id("EXT", report_id, study_id, field_id, extractor),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "report_id": report_id,
        "study_id": study_id,
        "field_id": field_id,
        "extractor": extractor,
        "value": value,
        "source_page": source_page.strip(),
        "source_quote": source_quote.strip(),
        "verification_status": "HUMAN_RECORDED",
    }
    _validate(payload, schema_dir)
    append_unique_row(
        _entry_path(project_dir),
        _ENTRY_HEADERS,
        {
            **{key: value for key, value in payload.items() if key != "value"},
            "value_json": _canonical_value(value),
        },
        ("report_id", "study_id", "field_id", "extractor"),
    )
    return str(payload["extraction_id"])


def _group_entries(project_dir: Path) -> dict[tuple[str, str, str], list[dict[str, str]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in read_csv_rows(_entry_path(project_dir)):
        grouped[_key(row)].append(row)
    return grouped


def list_extraction_conflicts(project_dir: Path) -> list[dict[str, object]]:
    conflicts: list[dict[str, object]] = []
    for key, rows in sorted(_group_entries(project_dir).items()):
        if len({row["extractor"] for row in rows}) < 2:
            continue
        values_json = sorted({row["value_json"] for row in rows})
        if len(values_json) > 1:
            conflicts.append({
                "report_id": key[0],
                "study_id": key[1],
                "field_id": key[2],
                "extractors": sorted({row["extractor"] for row in rows}),
                "values": [json.loads(value) for value in values_json],
            })
    return conflicts


def resolve_extraction(
    project_dir: Path,
    report_id: str,
    study_id: str,
    field_id: str,
    resolver: str,
    resolved_value: object,
    rationale: str,
) -> str:
    resolver = require_human_actor(resolver)
    key = (report_id, study_id, field_id)
    rows = _group_entries(project_dir).get(key, [])
    extractors = {row["extractor"] for row in rows}
    values = {row["value_json"] for row in rows}
    if len(extractors) < 2 or len(values) < 2:
        raise WorkflowError(
            ErrorCode.EXTRACTION_INVALID,
            "human adjudication requires two conflicting independent extraction values",
            {"report_id": report_id, "study_id": study_id, "field_id": field_id},
        )
    if resolver in extractors:
        raise WorkflowError(
            ErrorCode.EXTRACTION_INVALID,
            "the extraction conflict resolver must be distinct from both extractors",
            {"resolver": resolver, "extractors": sorted(extractors)},
        )
    if len(rationale.strip()) < 5:
        raise WorkflowError(
            ErrorCode.EXTRACTION_INVALID,
            "extraction resolution requires an explicit rationale",
            {"field_id": field_id},
        )
    resolution_id = stable_id("EXR", report_id, study_id, field_id, resolver)
    append_unique_row(
        _resolution_path(project_dir),
        _RESOLUTION_HEADERS,
        {
            "resolution_id": resolution_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "report_id": report_id,
            "study_id": study_id,
            "field_id": field_id,
            "resolver": resolver,
            "resolved_value_json": _canonical_value(resolved_value),
            "rationale": rationale.strip(),
        },
        ("report_id", "study_id", "field_id"),
    )
    return resolution_id


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(_VERIFIED_HEADERS))
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in _VERIFIED_HEADERS})
    temporary.replace(path)


def export_verified_extraction(project_dir: Path) -> Path:
    resolutions = {
        _key(row): row
        for row in read_csv_rows(_resolution_path(project_dir))
    }
    verified: list[dict[str, object]] = []
    incomplete: list[dict[str, object]] = []
    conflicts: list[dict[str, object]] = []
    for key, rows in sorted(_group_entries(project_dir).items()):
        extractors = sorted({row["extractor"] for row in rows})
        if len(extractors) < 2:
            incomplete.append({"report_id": key[0], "study_id": key[1], "field_id": key[2]})
            continue
        values = {row["value_json"] for row in rows}
        if len(values) == 1:
            resolved_value = next(iter(values))
            verified_by = "|".join(extractors)
            resolution_type = "DUAL_AGREEMENT"
        else:
            resolution = resolutions.get(key)
            if resolution is None:
                conflicts.append({"report_id": key[0], "study_id": key[1], "field_id": key[2]})
                continue
            resolved_value = resolution["resolved_value_json"]
            verified_by = resolution["resolver"]
            resolution_type = "HUMAN_ADJUDICATION"
        verified.append({
            "report_id": key[0],
            "study_id": key[1],
            "field_id": key[2],
            "resolved_value_json": resolved_value,
            "verification_status": "VERIFIED",
            "verified_by": verified_by,
            "resolution_type": resolution_type,
            "source_pages": "|".join(sorted({row["source_page"] for row in rows})),
            "source_quotes": " || ".join(row["source_quote"] for row in rows),
        })

    if conflicts:
        raise WorkflowError(
            ErrorCode.EXTRACTION_CONFLICT,
            "extraction conflicts remain unresolved",
            {"fields": conflicts},
        )
    if incomplete:
        raise WorkflowError(
            ErrorCode.EXTRACTION_INVALID,
            "verified extraction requires two distinct human extractors per field",
            {"fields": incomplete},
        )
    path = project_dir / "05_extraction/verified-extraction.csv"
    _write_csv(path, verified)
    return path
