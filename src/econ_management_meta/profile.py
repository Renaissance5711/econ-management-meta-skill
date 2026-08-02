"""Schema and policy validation for declarative domain profiles."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .errors import ErrorCode, WorkflowError
from .io import read_json, read_yaml

_FORBIDDEN_REQUIREMENT_KEYS = {
    "ai_final_decision",
    "allow_unverified_effects",
    "disable_construct_gate",
    "disable_estimand_gate",
    "disable_dependency_check",
    "disable_protocol_lock",
    "disable_analysis_spec_lock",
    "single_reviewer_fulltext",
}

_REQUIRED_SAFE_VALUES: dict[str, object] = {
    "independent_fulltext_screening": True,
    "human_effect_verification": True,
    "construct_alignment_gate": True,
    "estimand_alignment_gate": True,
    "dependency_check": True,
    "protocol_lock": True,
    "analysis_spec_lock": True,
}


@dataclass(frozen=True, slots=True)
class Profile:
    id: str
    name: str
    version: str
    schema_version: int
    core_compatibility: str
    status: str
    extends: str
    path: Path


def validate_profile_policy(raw: Mapping[str, object]) -> None:
    """Reject attempts to weaken non-negotiable core safeguards."""

    requirements = raw.get("requirements", {})
    if not isinstance(requirements, Mapping):
        return

    for key in requirements:
        if key in _FORBIDDEN_REQUIREMENT_KEYS:
            raise WorkflowError(
                ErrorCode.PROFILE_WEAKENS_CORE,
                "profile attempts to weaken a mandatory core gate",
                {"path": f"requirements.{key}"},
            )

    reviewers = requirements.get("fulltext_reviewers")
    if isinstance(reviewers, int) and reviewers < 2:
        raise WorkflowError(
            ErrorCode.PROFILE_WEAKENS_CORE,
            "full-text screening requires at least two human reviewers",
            {"path": "requirements.fulltext_reviewers", "value": reviewers},
        )

    for key, expected in _REQUIRED_SAFE_VALUES.items():
        if key in requirements and requirements[key] != expected:
            raise WorkflowError(
                ErrorCode.PROFILE_WEAKENS_CORE,
                "profile attempts to weaken a mandatory core gate",
                {"path": f"requirements.{key}", "expected": expected},
            )


def _validation_error_details(errors: list[Any]) -> list[dict[str, object]]:
    return [
        {
            "path": ".".join(str(part) for part in error.absolute_path),
            "message": error.message,
        }
        for error in errors
    ]


def load_profile(path: Path, schema_path: Path) -> Profile:
    manifest_path = path / "profile.yaml"
    raw = read_yaml(manifest_path)
    validate_profile_policy(raw)

    schema = read_json(schema_path)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(raw),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        raise WorkflowError(
            ErrorCode.PROFILE_SCHEMA_INVALID,
            "profile does not satisfy the declarative contract",
            {"errors": _validation_error_details(errors)},
        )

    ontology_path = path / str(raw["ontology"]["constructs"])
    moderators_path = path / str(raw["coding"]["moderators"])
    missing = [
        str(candidate.relative_to(path))
        for candidate in (ontology_path, moderators_path)
        if not candidate.is_file()
    ]
    if missing:
        raise WorkflowError(
            ErrorCode.PROFILE_SCHEMA_INVALID,
            "profile references missing declarative resources",
            {"missing": missing},
        )

    metadata = raw["profile"]
    return Profile(
        id=str(metadata["id"]),
        name=str(metadata["name"]),
        version=str(metadata["version"]),
        schema_version=int(metadata["schema_version"]),
        core_compatibility=str(metadata["core_compatibility"]),
        status=str(metadata["status"]),
        extends=str(raw["extends"]),
        path=path.resolve(),
    )
