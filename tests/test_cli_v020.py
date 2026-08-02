from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import yaml


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str((Path.cwd() / "src").resolve()) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "econ_management_meta.cli", *args],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def protocol_payload() -> dict[str, object]:
    return {
        "research_question": "How is organizational AI related to innovation outcomes?",
        "unit_of_inference": "firm-level effect",
        "eligibility": {
            "populations": ["firms"], "exposures": ["AI adoption"],
            "outcomes": ["innovation"], "designs": ["observational"],
        },
        "evidence_lanes": ["marginal_association"],
        "search_plan": {"databases": ["Web of Science"]},
        "screening_plan": {"title_abstract_reviewers": 2, "fulltext_reviewers": 2, "independent": True, "ai_final_decision": False},
        "extraction_plan": {"extractors": 2, "independent": True, "human_verification": True},
        "ai_assistance": {"final_screening_decision": False, "final_extraction_decision": False},
        "analyses": {"primary": ["observed effect"], "secondary": [], "sensitivity": [], "exploratory": []},
    }


def test_cli_protocol_create_and_validate(initialized_project: Path, tmp_path: Path) -> None:
    source = tmp_path / "protocol.yaml"
    source.write_text(yaml.safe_dump(protocol_payload()), encoding="utf-8")

    created = run_cli("protocol", "create", str(initialized_project), "1.0", str(source), "--actor", "principal-investigator")
    validated = run_cli("protocol", "validate", str(initialized_project / "01_protocol/protocol-v1.0.yaml"))

    assert created.returncode == 0
    assert json.loads(created.stdout)["version"] == "1.0"
    assert validated.returncode == 0
    assert json.loads(validated.stdout)["valid"] is True


def test_cli_search_register_import_and_deduplicate(initialized_project: Path, tmp_path: Path) -> None:
    run_file = tmp_path / "search-run.yaml"
    run_file.write_text(yaml.safe_dump({
        "database": "Test DB", "platform": "Test", "search_date": "2026-08-03",
        "query": "AI AND innovation", "hit_count": 1, "export_batch": "batch-1",
    }), encoding="utf-8")
    registered = run_cli("search", "register", str(initialized_project), str(run_file), "--actor", "information-specialist")
    run_id = json.loads(registered.stdout)["search_run_id"]
    imported = run_cli("search", "import", str(initialized_project), run_id, "tests/fixtures/search/sample.csv", "--format", "csv", "--actor", "information-specialist")
    deduped = run_cli("search", "deduplicate", str(initialized_project), "--actor", "review-lead")

    assert registered.returncode == 0
    assert imported.returncode == 0
    assert json.loads(imported.stdout)["imported"] == 1
    assert deduped.returncode == 0
    assert json.loads(deduped.stdout)["deduplicated_records"] == 1


def test_cli_screening_conflict_returns_stable_error(initialized_project: Path) -> None:
    for reviewer, decision in (("reviewer-1", "INCLUDE"), ("reviewer-2", "EXCLUDE")):
        result = run_cli(
            "screen", "decide", str(initialized_project), "title-abstract", "REC-1", reviewer, decision,
            "--reason", "WRONG_TOPIC" if decision == "EXCLUDE" else "",
        )
        assert result.returncode == 0

    consensus = run_cli("screen", "consensus", str(initialized_project), "title-abstract")
    assert consensus.returncode == 2
    assert json.loads(consensus.stderr)["error"] == "SCREENING_CONFLICT"


def test_cli_report_family_assign_and_export(initialized_project: Path) -> None:
    assigned = run_cli(
        "report-family", "assign", str(initialized_project), "REP-1", "RFAM-1", "STUDY-1", "JOURNAL_ARTICLE",
        "--actor", "reviewer-1", "--evidence", "Same title authors and sample",
    )
    exported = run_cli("report-family", "export", str(initialized_project))

    assert assigned.returncode == 0
    assert json.loads(assigned.stdout)["assignment_id"].startswith("RFA-")
    assert exported.returncode == 0
    assert Path(json.loads(exported.stdout)["path"]).exists()


def test_cli_dual_extraction_and_export(initialized_project: Path) -> None:
    for extractor in ("extractor-1", "extractor-2"):
        result = run_cli(
            "extract", "record", str(initialized_project), "REP-1", "STUDY-1", "sample-size", extractor, "240",
            "--page", "p. 12", "--quote", "The sample contained 240 firms.",
        )
        assert result.returncode == 0

    exported = run_cli("extract", "export", str(initialized_project))
    assert exported.returncode == 0
    assert Path(json.loads(exported.stdout)["path"]).exists()
