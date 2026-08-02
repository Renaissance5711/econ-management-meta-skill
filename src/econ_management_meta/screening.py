"""Independent human screening decisions, agreement, and consensus."""

from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .errors import ErrorCode, WorkflowError
from .io import read_json
from .tabular import append_unique_row, read_csv_rows, require_human_actor, stable_id

_DECISION_HEADERS = (
    "decision_id", "timestamp", "stage", "record_id", "reviewer", "decision",
    "reason_code", "source_page", "note",
)
_RESOLUTION_HEADERS = (
    "resolution_id", "timestamp", "stage", "record_id", "adjudicator",
    "final_decision", "reason_code", "source_page", "rationale",
)
_CONSENSUS_HEADERS = (
    "record_id", "stage", "final_decision", "reason_code", "source_page",
    "verified_by", "resolution_type",
)


def _decision_path(project_dir: Path, stage: str) -> Path:
    if stage == "title-abstract":
        return project_dir / "03_screening/title-abstract-decisions.csv"
    if stage == "fulltext":
        return project_dir / "04_fulltext/fulltext-decisions.csv"
    raise WorkflowError(
        ErrorCode.SCREENING_INVALID,
        "unsupported screening stage",
        {"stage": stage},
    )


def _resolution_path(project_dir: Path, stage: str) -> Path:
    directory = "03_screening" if stage == "title-abstract" else "04_fulltext"
    return project_dir / directory / f"{stage}-resolutions.csv"


def _validate_decision(payload: Mapping[str, object], schema_dir: Path) -> None:
    validator = Draft202012Validator(
        read_json(schema_dir / "screening-decision.schema.json"),
        format_checker=FormatChecker(),
    )
    errors = sorted(validator.iter_errors(dict(payload)), key=lambda item: list(item.absolute_path))
    if errors:
        raise WorkflowError(
            ErrorCode.SCREENING_INVALID,
            "screening decision does not satisfy its schema",
            {"errors": [{"path": ".".join(map(str, error.absolute_path)), "message": error.message} for error in errors]},
        )


def record_screening_decision(
    project_dir: Path,
    stage: str,
    record_id: str,
    reviewer: str,
    decision: str,
    reason_code: str | None,
    source_page: str | None,
    note: str | None,
    schema_dir: Path,
) -> str:
    reviewer = require_human_actor(reviewer)
    decision = decision.upper()
    if stage == "fulltext" and decision == "EXCLUDE" and (not reason_code or not source_page):
        raise WorkflowError(
            ErrorCode.SCREENING_INVALID,
            "full-text exclusions require a reason code and source page",
            {"record_id": record_id},
        )
    timestamp = datetime.now(timezone.utc).isoformat()
    decision_id = stable_id("SCR", stage, record_id, reviewer)
    payload: dict[str, object] = {
        "decision_id": decision_id,
        "timestamp": timestamp,
        "stage": stage,
        "record_id": record_id,
        "reviewer": reviewer,
        "decision": decision,
        "reason_code": reason_code,
        "source_page": source_page,
        "note": note,
    }
    _validate_decision(payload, schema_dir)
    append_unique_row(
        _decision_path(project_dir, stage),
        _DECISION_HEADERS,
        payload,
        ("record_id", "reviewer"),
    )
    return decision_id


def _group_decisions(project_dir: Path, stage: str) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv_rows(_decision_path(project_dir, stage)):
        grouped[row["record_id"]].append(row)
    return grouped


def screening_agreement(project_dir: Path, stage: str) -> dict[str, object]:
    grouped = _group_decisions(project_dir, stage)
    pairs = [rows[:2] for rows in grouped.values() if len({row["reviewer"] for row in rows}) >= 2]
    n = len(pairs)
    if n == 0:
        return {
            "records_with_two_decisions": 0,
            "raw_agreement": None,
            "include_agreement": None,
            "exclude_agreement": None,
            "cohens_kappa": None,
            "conflict_count": 0,
        }

    labels = ("INCLUDE", "EXCLUDE", "UNCERTAIN")
    agreements = sum(pair[0]["decision"] == pair[1]["decision"] for pair in pairs)
    conflict_count = sum(pair[0]["decision"] != pair[1]["decision"] for pair in pairs)

    def specific(label: str) -> float | None:
        both = sum(pair[0]["decision"] == label and pair[1]["decision"] == label for pair in pairs)
        one = sum((pair[0]["decision"] == label) ^ (pair[1]["decision"] == label) for pair in pairs)
        denominator = 2 * both + one
        return None if denominator == 0 else round((2 * both) / denominator, 6)

    observed = agreements / n
    first_probs = {label: sum(pair[0]["decision"] == label for pair in pairs) / n for label in labels}
    second_probs = {label: sum(pair[1]["decision"] == label for pair in pairs) / n for label in labels}
    expected = sum(first_probs[label] * second_probs[label] for label in labels)
    kappa = None if expected == 1 else round((observed - expected) / (1 - expected), 6)
    return {
        "records_with_two_decisions": n,
        "raw_agreement": round(observed, 6),
        "include_agreement": specific("INCLUDE"),
        "exclude_agreement": specific("EXCLUDE"),
        "cohens_kappa": kappa,
        "conflict_count": conflict_count,
    }


def resolve_screening_conflict(
    project_dir: Path,
    stage: str,
    record_id: str,
    adjudicator: str,
    final_decision: str,
    reason_code: str | None,
    source_page: str | None,
    rationale: str,
    schema_dir: Path,
) -> str:
    del schema_dir  # resolution rules are enforced directly in v0.2.0
    adjudicator = require_human_actor(adjudicator)
    grouped = _group_decisions(project_dir, stage)
    rows = grouped.get(record_id, [])
    reviewers = {row["reviewer"] for row in rows}
    if len(reviewers) < 2 or len({row["decision"] for row in rows}) < 2:
        raise WorkflowError(
            ErrorCode.SCREENING_INVALID,
            "adjudication requires two independent conflicting decisions",
            {"record_id": record_id},
        )
    if adjudicator in reviewers:
        raise WorkflowError(
            ErrorCode.SCREENING_INVALID,
            "the conflict adjudicator must be distinct from the original reviewers",
            {"record_id": record_id, "adjudicator": adjudicator},
        )
    final_decision = final_decision.upper()
    if final_decision not in {"INCLUDE", "EXCLUDE"}:
        raise WorkflowError(
            ErrorCode.SCREENING_INVALID,
            "a final screening resolution must include or exclude",
            {"decision": final_decision},
        )
    if stage == "fulltext" and final_decision == "EXCLUDE" and (not reason_code or not source_page):
        raise WorkflowError(
            ErrorCode.SCREENING_INVALID,
            "full-text exclusion resolution requires reason and page",
            {"record_id": record_id},
        )
    resolution_id = stable_id("RES", stage, record_id, adjudicator, final_decision)
    append_unique_row(
        _resolution_path(project_dir, stage),
        _RESOLUTION_HEADERS,
        {
            "resolution_id": resolution_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": stage,
            "record_id": record_id,
            "adjudicator": adjudicator,
            "final_decision": final_decision,
            "reason_code": reason_code,
            "source_page": source_page,
            "rationale": rationale,
        },
        ("record_id",),
    )
    return resolution_id


def _write_csv(path: Path, headers: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(headers))
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})
    temporary.replace(path)


def export_screening_consensus(project_dir: Path, stage: str) -> Path:
    grouped = _group_decisions(project_dir, stage)
    resolutions = {
        row["record_id"]: row
        for row in read_csv_rows(_resolution_path(project_dir, stage))
    }
    consensus: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    for record_id, rows in sorted(grouped.items()):
        reviewers = sorted({row["reviewer"] for row in rows})
        if len(reviewers) < 2:
            errors.append({"record_id": record_id, "reason": "fewer_than_two_reviewers"})
            continue
        decisions = {row["decision"] for row in rows}
        if len(decisions) == 1 and "UNCERTAIN" not in decisions:
            decision = next(iter(decisions))
            source = next(row for row in rows if row["decision"] == decision)
            consensus.append({
                "record_id": record_id,
                "stage": stage,
                "final_decision": decision,
                "reason_code": source["reason_code"],
                "source_page": source["source_page"],
                "verified_by": "|".join(reviewers),
                "resolution_type": "REVIEWER_AGREEMENT",
            })
            continue
        resolution = resolutions.get(record_id)
        if resolution is None:
            errors.append({"record_id": record_id, "reason": "unresolved_conflict"})
            continue
        consensus.append({
            "record_id": record_id,
            "stage": stage,
            "final_decision": resolution["final_decision"],
            "reason_code": resolution["reason_code"],
            "source_page": resolution["source_page"],
            "verified_by": resolution["adjudicator"],
            "resolution_type": "HUMAN_ADJUDICATION",
        })

    if errors:
        code = ErrorCode.SCREENING_CONFLICT if any(item["reason"] == "unresolved_conflict" for item in errors) else ErrorCode.SCREENING_INVALID
        raise WorkflowError(code, "screening consensus is incomplete", {"records": errors})

    directory = "03_screening" if stage == "title-abstract" else "04_fulltext"
    path = project_dir / directory / f"{stage}-consensus.csv"
    _write_csv(path, _CONSENSUS_HEADERS, consensus)
    return path
