from pathlib import Path

import pytest

from econ_management_meta.errors import ErrorCode, WorkflowError
from econ_management_meta.locks import create_lock, verify_lock


def test_lock_verifies_unchanged_artifacts(initialized_project: Path) -> None:
    protocol = initialized_project / "01_protocol/protocol-v1.0.yaml"
    protocol.write_text("version: '1.0'\n", encoding="utf-8")

    lock_path = create_lock(
        initialized_project,
        kind="protocol",
        version="1.0",
        artifact_paths=[protocol],
        actor="researcher-1",
    )

    result = verify_lock(initialized_project, lock_path)
    assert result["valid"] is True


def test_lock_fails_closed_after_artifact_changes(initialized_project: Path) -> None:
    protocol = initialized_project / "01_protocol/protocol-v1.0.yaml"
    protocol.write_text("version: '1.0'\n", encoding="utf-8")
    lock_path = create_lock(
        initialized_project,
        "protocol",
        "1.0",
        [protocol],
        "researcher-1",
    )
    protocol.write_text("version: '1.1'\n", encoding="utf-8")

    with pytest.raises(WorkflowError) as caught:
        verify_lock(initialized_project, lock_path)

    assert caught.value.code is ErrorCode.LOCK_STALE


def test_lock_refuses_missing_artifact(initialized_project: Path) -> None:
    with pytest.raises(WorkflowError) as caught:
        create_lock(
            initialized_project,
            "protocol",
            "1.0",
            [initialized_project / "01_protocol/missing.yaml"],
            "researcher-1",
        )

    assert caught.value.code is ErrorCode.LOCK_SCHEMA_INVALID
