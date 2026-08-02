"""Append-oriented CSV helpers for auditable research decisions."""

from __future__ import annotations

import csv
import hashlib
from collections.abc import Mapping, Sequence
from pathlib import Path

from .errors import ErrorCode, WorkflowError


def stable_id(prefix: str, *parts: object) -> str:
    """Return a deterministic short identifier from normalized parts."""

    payload = "\x1f".join(str(part).strip() for part in parts).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()[:16].upper()
    return f"{prefix.upper()}-{digest}"


def ensure_csv(path: Path, headers: Sequence[str]) -> None:
    """Create a CSV with exact headers, or validate an existing header."""

    path.parent.mkdir(parents=True, exist_ok=True)
    expected = list(headers)
    if not path.exists():
        with path.open("w", encoding="utf-8", newline="") as handle:
            csv.writer(handle).writerow(expected)
        return

    with path.open("r", encoding="utf-8", newline="") as handle:
        actual = next(csv.reader(handle), [])
    if actual != expected:
        raise WorkflowError(
            ErrorCode.ARTIFACT_ALREADY_EXISTS,
            "existing CSV header does not match the required contract",
            {"path": str(path), "expected": expected, "actual": actual},
        )


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def append_unique_row(
    path: Path,
    headers: Sequence[str],
    row: Mapping[str, object],
    unique_fields: Sequence[str],
) -> None:
    """Append one row after checking a composite uniqueness constraint."""

    ensure_csv(path, headers)
    normalized = {header: "" if row.get(header) is None else str(row.get(header)) for header in headers}
    existing = read_csv_rows(path)
    duplicate = next(
        (
            candidate
            for candidate in existing
            if all(candidate.get(field, "") == normalized.get(field, "") for field in unique_fields)
        ),
        None,
    )
    if duplicate is not None:
        raise WorkflowError(
            ErrorCode.DUPLICATE_DECISION,
            "a row with the same composite key already exists",
            {
                "path": str(path),
                "unique_fields": list(unique_fields),
                "key": {field: normalized.get(field, "") for field in unique_fields},
            },
        )

    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(headers))
        writer.writerow(normalized)


def require_human_actor(actor: str) -> str:
    """Reject blank or machine-labelled actors for consequential decisions."""

    normalized = actor.strip()
    lowered = normalized.casefold()
    words = {word for word in __import__("re").split(r"[^a-z0-9]+", lowered) if word}
    machine_tokens = {"ai", "assistant", "chatgpt", "claude", "codex", "bot", "model"}
    machine_label = bool(words & machine_tokens) or "artificial intelligence" in lowered
    if len(normalized) < 2 or machine_label:
        raise WorkflowError(
            ErrorCode.HUMAN_ACTOR_REQUIRED,
            "a named human actor is required for this decision",
            {"actor": actor},
        )
    return normalized
