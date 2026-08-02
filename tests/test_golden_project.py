from pathlib import Path

import pytest
import yaml

from econ_management_meta.errors import ErrorCode, WorkflowError
from econ_management_meta.locks import create_lock, verify_lock
from econ_management_meta.profile import validate_profile_policy
from econ_management_meta.project import initialize_project, validate_project
from econ_management_meta.state import Stage, StageStatus, transition_stage


def test_golden_project_completes_callable_core_flow(tmp_path: Path) -> None:
    project = initialize_project(
        "AI and innovation",
        Path("profiles/ai-innovation"),
        tmp_path / "project",
        Path("schemas"),
    )
    transition_stage(project, Stage.INTAKE, StageStatus.IN_PROGRESS, "r1", "start")
    transition_stage(project, Stage.INTAKE, StageStatus.READY_FOR_REVIEW, "r1", "ready")
    transition_stage(project, Stage.INTAKE, StageStatus.VERIFIED, "r2", "verified")
    transition_stage(project, Stage.INTAKE, StageStatus.LOCKED, "r2", "locked")
    transition_stage(project, Stage.PROTOCOL, StageStatus.IN_PROGRESS, "r1", "start protocol")

    protocol = project / "01_protocol/protocol-v1.0.yaml"
    protocol.write_text("version: '1.0'\n", encoding="utf-8")
    lock_path = create_lock(project, "protocol", "1.0", [protocol], "r2")

    assert verify_lock(project, lock_path)["valid"] is True
    validation = validate_project(project, Path("schemas"))
    assert validation["valid"] is True
    assert validation["locks_verified"] == 1


def test_project_validation_detects_planted_stale_lock(tmp_path: Path) -> None:
    project = initialize_project(
        "AI and innovation",
        Path("profiles/ai-innovation"),
        tmp_path / "project",
        Path("schemas"),
    )
    protocol = project / "01_protocol/protocol-v1.0.yaml"
    protocol.write_text("version: '1.0'\n", encoding="utf-8")
    create_lock(project, "protocol", "1.0", [protocol], "r2")
    protocol.write_text("version: '1.1'\n", encoding="utf-8")

    with pytest.raises(WorkflowError) as caught:
        validate_project(project, Path("schemas"))

    assert caught.value.code is ErrorCode.LOCK_STALE


def test_planted_unsafe_profile_is_rejected() -> None:
    raw = yaml.safe_load(
        Path("examples/golden-project/fixtures/unsafe-profile.yaml").read_text(
            encoding="utf-8"
        )
    )

    with pytest.raises(WorkflowError) as caught:
        validate_profile_policy(raw)

    assert caught.value.code is ErrorCode.PROFILE_WEAKENS_CORE
