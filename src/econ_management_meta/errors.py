"""Stable fail-closed error types used by the CLI and workflow services."""

from __future__ import annotations

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """Stable machine-readable workflow error codes."""

    PROFILE_SCHEMA_INVALID = "PROFILE_SCHEMA_INVALID"
    PROFILE_WEAKENS_CORE = "PROFILE_WEAKENS_CORE"
    PROJECT_SCHEMA_INVALID = "PROJECT_SCHEMA_INVALID"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"
    PREREQUISITE_NOT_LOCKED = "PREREQUISITE_NOT_LOCKED"
    LOCK_STALE = "LOCK_STALE"
    LOCK_SCHEMA_INVALID = "LOCK_SCHEMA_INVALID"
    SKILL_CONTRACT_INVALID = "SKILL_CONTRACT_INVALID"
    PATH_NOT_EMPTY = "PATH_NOT_EMPTY"
    UNAVAILABLE_IN_VERSION = "UNAVAILABLE_IN_VERSION"


class WorkflowError(Exception):
    """Expected workflow failure that must stop downstream execution."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def as_dict(self) -> dict[str, object]:
        return {
            "error": self.code.value,
            "message": self.message,
            "details": self.details,
        }
