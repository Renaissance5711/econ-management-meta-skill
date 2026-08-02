from pathlib import Path

import pytest

from econ_management_meta.errors import ErrorCode, WorkflowError
from econ_management_meta.state import Stage, StageStatus, transition_stage


def test_stage_moves_from_not_started_to_in_progress(initialized_project: Path) -> None:
    state = transition_stage(
        initialized_project,
        Stage.INTAKE,
        StageStatus.IN_PROGRESS,
        actor="researcher-1",
        note="begin feasibility scan",
    )

    assert state["stages"]["00_intake"]["status"] == "IN_PROGRESS"
    assert state["history"][-1]["actor"] == "researcher-1"


def test_stage_cannot_lock_before_verification(initialized_project: Path) -> None:
    with pytest.raises(WorkflowError) as caught:
        transition_stage(
            initialized_project,
            Stage.INTAKE,
            StageStatus.LOCKED,
            actor="researcher-1",
            note="skip review",
        )

    assert caught.value.code is ErrorCode.INVALID_STATE_TRANSITION


def test_next_stage_cannot_start_until_previous_stage_locked(
    initialized_project: Path,
) -> None:
    with pytest.raises(WorkflowError) as caught:
        transition_stage(
            initialized_project,
            Stage.PROTOCOL,
            StageStatus.IN_PROGRESS,
            actor="researcher-1",
            note="start protocol",
        )

    assert caught.value.code is ErrorCode.PREREQUISITE_NOT_LOCKED


def test_verified_stage_can_lock_and_unlocking_is_forbidden(
    initialized_project: Path,
) -> None:
    for target in (
        StageStatus.IN_PROGRESS,
        StageStatus.READY_FOR_REVIEW,
        StageStatus.VERIFIED,
        StageStatus.LOCKED,
    ):
        transition_stage(initialized_project, Stage.INTAKE, target, "r1", target.value)

    with pytest.raises(WorkflowError) as caught:
        transition_stage(
            initialized_project,
            Stage.INTAKE,
            StageStatus.IN_PROGRESS,
            "r1",
            "attempt unlock",
        )

    assert caught.value.code is ErrorCode.INVALID_STATE_TRANSITION
