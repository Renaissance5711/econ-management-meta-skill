"""Fail-closed workflow state transitions."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from .errors import ErrorCode, WorkflowError
from .io import read_yaml, write_yaml
from .project import STAGE_NAMES


class Stage(str, Enum):
    INTAKE = "00_intake"
    PROTOCOL = "01_protocol"
    SEARCH = "02_search"
    SCREENING = "03_screening"
    FULLTEXT = "04_fulltext"
    EXTRACTION = "05_extraction"
    CONSTRUCT_ALIGNMENT = "06_construct_alignment"
    ESTIMAND_ALIGNMENT = "07_estimand_alignment"
    EFFECT_SIZE = "08_effect_size"
    ANALYSIS_SPEC = "09_analysis_spec"
    SYNTHESIS = "10_synthesis"
    HETEROGENEITY = "11_heterogeneity"
    MISSING_EVIDENCE = "12_missing_evidence"
    EVIDENCE_APPRAISAL = "13_evidence_appraisal"
    REPORTING = "14_reporting"
    PUBLICATION_QA = "15_publication_qa"


class StageStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    VERIFIED = "VERIFIED"
    LOCKED = "LOCKED"


_ALLOWED: dict[StageStatus, set[StageStatus]] = {
    StageStatus.NOT_STARTED: {StageStatus.IN_PROGRESS},
    StageStatus.IN_PROGRESS: {StageStatus.BLOCKED, StageStatus.READY_FOR_REVIEW},
    StageStatus.BLOCKED: {StageStatus.IN_PROGRESS},
    StageStatus.READY_FOR_REVIEW: {StageStatus.IN_PROGRESS, StageStatus.VERIFIED},
    StageStatus.VERIFIED: {StageStatus.IN_PROGRESS, StageStatus.LOCKED},
    StageStatus.LOCKED: set(),
}


def _previous_stage(stage: Stage) -> str | None:
    index = STAGE_NAMES.index(stage.value)
    return None if index == 0 else STAGE_NAMES[index - 1]


def transition_stage(
    project_dir: Path,
    stage: Stage,
    target: StageStatus,
    actor: str,
    note: str,
) -> dict[str, Any]:
    """Apply one legal stage transition and persist append-only history."""

    state_path = project_dir / "state/pipeline-state.yaml"
    state = read_yaml(state_path)
    current_raw = state["stages"][stage.value]["status"]
    current = StageStatus(str(current_raw))

    if target is StageStatus.IN_PROGRESS and current is StageStatus.NOT_STARTED:
        previous = _previous_stage(stage)
        if previous is not None:
            previous_status = state["stages"][previous]["status"]
            if previous_status != StageStatus.LOCKED.value:
                raise WorkflowError(
                    ErrorCode.PREREQUISITE_NOT_LOCKED,
                    "the immediately preceding stage must be locked",
                    {
                        "stage": stage.value,
                        "prerequisite": previous,
                        "prerequisite_status": previous_status,
                    },
                )

    if target not in _ALLOWED[current]:
        raise WorkflowError(
            ErrorCode.INVALID_STATE_TRANSITION,
            "requested workflow transition is not allowed",
            {
                "stage": stage.value,
                "from": current.value,
                "to": target.value,
            },
        )

    state["stages"][stage.value]["status"] = target.value
    history = state.setdefault("history", [])
    history.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "stage": stage.value,
            "from": current.value,
            "to": target.value,
            "note": note,
        }
    )
    write_yaml(state_path, state)
    return state
