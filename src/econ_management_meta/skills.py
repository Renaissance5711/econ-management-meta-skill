"""Validation helpers for agent-facing SKILL.md contracts."""

from __future__ import annotations

from pathlib import Path

import yaml

from .errors import ErrorCode, WorkflowError

_REQUIRED_FIELDS = ("name", "description", "version", "license", "status")


def validate_skill_contract(path: Path) -> dict[str, str]:
    """Parse and validate YAML frontmatter from a skill file."""

    if not path.is_file():
        raise WorkflowError(
            ErrorCode.SKILL_CONTRACT_INVALID,
            "skill file does not exist",
            {"path": str(path)},
        )
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise WorkflowError(
            ErrorCode.SKILL_CONTRACT_INVALID,
            "skill file must begin with YAML frontmatter",
            {"path": str(path)},
        )
    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as exc:
        raise WorkflowError(
            ErrorCode.SKILL_CONTRACT_INVALID,
            "skill frontmatter is not terminated",
            {"path": str(path)},
        ) from exc

    raw = yaml.safe_load("\n".join(lines[1:end]))
    if not isinstance(raw, dict):
        raise WorkflowError(
            ErrorCode.SKILL_CONTRACT_INVALID,
            "skill frontmatter must be a mapping",
            {"path": str(path)},
        )
    missing = [field for field in _REQUIRED_FIELDS if not isinstance(raw.get(field), str) or not raw[field].strip()]
    if missing:
        raise WorkflowError(
            ErrorCode.SKILL_CONTRACT_INVALID,
            "skill frontmatter is missing required string fields",
            {"path": str(path), "missing": missing},
        )
    return {field: str(raw[field]) for field in _REQUIRED_FIELDS}
