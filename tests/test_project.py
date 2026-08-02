from pathlib import Path

import pytest

from econ_management_meta.errors import ErrorCode, WorkflowError
from econ_management_meta.io import read_json, read_yaml
from econ_management_meta.project import initialize_project, validate_project


def test_initializer_creates_canonical_project_tree(tmp_path: Path) -> None:
    project = initialize_project(
        topic="AI and innovation",
        profile_dir=Path("profiles/ai-innovation"),
        output_dir=tmp_path / "ai-innovation-meta",
        schema_dir=Path("schemas"),
    )

    assert (project / "project.yaml").exists()
    assert (project / "state/pipeline-state.yaml").exists()
    assert (project / "state/decision-log.csv").exists()
    assert (project / "state/artifact-manifest.json").exists()
    assert (project / "locks").is_dir()
    assert (project / "00_intake").is_dir()
    assert (project / "15_publication_qa").is_dir()
    assert validate_project(project, Path("schemas"))["valid"] is True


def test_initializer_records_profile_and_initial_stage(tmp_path: Path) -> None:
    project = initialize_project(
        "AI and innovation",
        Path("profiles/ai-innovation"),
        tmp_path / "project",
        Path("schemas"),
    )

    manifest = read_yaml(project / "project.yaml")
    state = read_yaml(project / "state/pipeline-state.yaml")
    artifacts = read_json(project / "state/artifact-manifest.json")

    assert manifest["profile"] == {"id": "ai-innovation", "version": "0.1.0"}
    assert manifest["current_stage"] == "00_intake"
    assert state["stages"]["00_intake"]["status"] == "NOT_STARTED"
    assert artifacts["artifacts"] == []


def test_initializer_refuses_non_empty_output(tmp_path: Path) -> None:
    output = tmp_path / "existing"
    output.mkdir()
    notes = output / "notes.txt"
    notes.write_text("keep", encoding="utf-8")

    with pytest.raises(WorkflowError) as caught:
        initialize_project(
            "AI and innovation",
            Path("profiles/ai-innovation"),
            output,
            Path("schemas"),
        )

    assert caught.value.code is ErrorCode.PATH_NOT_EMPTY
    assert notes.read_text(encoding="utf-8") == "keep"


def test_initializer_tree_matches_golden_fixture(tmp_path: Path) -> None:
    project = initialize_project(
        "AI and innovation",
        Path("profiles/ai-innovation"),
        tmp_path / "project",
        Path("schemas"),
    )
    actual = sorted(
        str(path.relative_to(project)) + ("/" if path.is_dir() else "")
        for path in project.rglob("*")
    )
    expected = Path("examples/golden-project/expected-tree.txt").read_text(
        encoding="utf-8"
    ).splitlines()

    assert actual == expected
