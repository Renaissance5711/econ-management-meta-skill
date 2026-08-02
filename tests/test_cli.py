from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    source = str((Path.cwd() / "src").resolve())
    env["PYTHONPATH"] = source + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "econ_management_meta.cli", *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )


def test_cli_version_returns_machine_readable_version() -> None:
    result = run_cli("version")

    assert result.returncode == 0
    assert json.loads(result.stdout) == {"version": "0.1.0"}


def test_cli_validates_safe_profile() -> None:
    result = run_cli("validate-profile", "profiles/ai-innovation")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["valid"] is True
    assert payload["profile"]["id"] == "ai-innovation"


def test_cli_rejects_profile_that_weakens_core(tmp_path: Path) -> None:
    profile = tmp_path / "unsafe"
    profile.mkdir()
    (profile / "profile.yaml").write_text(
        "profile:\n  id: unsafe\nrequirements:\n  ai_final_decision: true\n",
        encoding="utf-8",
    )

    result = run_cli("validate-profile", str(profile))

    assert result.returncode == 2
    assert json.loads(result.stderr)["error"] == "PROFILE_WEAKENS_CORE"


def test_cli_initializes_and_validates_project(tmp_path: Path) -> None:
    output = tmp_path / "project"
    initialized = run_cli(
        "init",
        "AI and innovation",
        "--profile",
        "profiles/ai-innovation",
        "--output",
        str(output),
    )
    validated = run_cli("validate-project", str(output))

    assert initialized.returncode == 0
    assert json.loads(initialized.stdout)["project"] == str(output.resolve())
    assert validated.returncode == 0
    assert json.loads(validated.stdout)["valid"] is True


def test_cli_transition_fails_when_prerequisite_is_not_locked(tmp_path: Path) -> None:
    output = tmp_path / "project"
    init_result = run_cli(
        "init",
        "AI and innovation",
        "--profile",
        "profiles/ai-innovation",
        "--output",
        str(output),
    )
    assert init_result.returncode == 0

    result = run_cli(
        "transition",
        str(output),
        "01_protocol",
        "IN_PROGRESS",
        "--actor",
        "r1",
        "--note",
        "start protocol",
    )

    assert result.returncode == 2
    assert json.loads(result.stderr)["error"] == "PREREQUISITE_NOT_LOCKED"
