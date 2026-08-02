from pathlib import Path

import pytest

from econ_management_meta.project import initialize_project


@pytest.fixture
def initialized_project(tmp_path: Path) -> Path:
    return initialize_project(
        topic="AI and innovation",
        profile_dir=Path("profiles/ai-innovation"),
        output_dir=tmp_path / "project",
        schema_dir=Path("schemas"),
    )
