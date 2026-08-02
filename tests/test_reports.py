from pathlib import Path

import pytest

from econ_management_meta.errors import ErrorCode, WorkflowError
from econ_management_meta.reports import (
    assign_report_family,
    export_report_family_map,
    validate_report_families,
)
from econ_management_meta.tabular import read_csv_rows


def test_valid_report_family_assignment_exports_map(initialized_project: Path) -> None:
    assignment_id = assign_report_family(
        initialized_project,
        report_id="REP-1",
        report_family_id="RFAM-1",
        study_id="STUDY-1",
        version_role="WORKING_PAPER",
        actor="reviewer-1",
        evidence="Same title, authors, sample, and project description.",
        schema_dir=Path("schemas"),
    )

    assert assignment_id.startswith("RFA-")
    assert validate_report_families(initialized_project) == {
        "valid": True,
        "reports": 1,
        "report_families": 1,
        "studies": 1,
    }
    exported = export_report_family_map(initialized_project)
    rows = read_csv_rows(exported)
    assert rows[0]["report_id"] == "REP-1"
    assert rows[0]["study_id"] == "STUDY-1"


def test_report_family_assignment_requires_evidence(initialized_project: Path) -> None:
    with pytest.raises(WorkflowError) as caught:
        assign_report_family(
            initialized_project,
            "REP-1",
            "RFAM-1",
            "STUDY-1",
            "JOURNAL_ARTICLE",
            "reviewer-1",
            "",
            Path("schemas"),
        )
    assert caught.value.code is ErrorCode.REPORT_FAMILY_INVALID


def test_report_cannot_be_assigned_twice_or_to_two_studies(initialized_project: Path) -> None:
    assign_report_family(
        initialized_project,
        "REP-1",
        "RFAM-1",
        "STUDY-1",
        "WORKING_PAPER",
        "reviewer-1",
        "Same authors and sample.",
        Path("schemas"),
    )

    with pytest.raises(WorkflowError) as duplicate:
        assign_report_family(
            initialized_project,
            "REP-1",
            "RFAM-1",
            "STUDY-1",
            "JOURNAL_ARTICLE",
            "reviewer-2",
            "Later publication.",
            Path("schemas"),
        )
    assert duplicate.value.code is ErrorCode.REPORT_FAMILY_INVALID

    with pytest.raises(WorkflowError) as conflict:
        assign_report_family(
            initialized_project,
            "REP-1",
            "RFAM-2",
            "STUDY-2",
            "JOURNAL_ARTICLE",
            "reviewer-2",
            "Alternative assignment.",
            Path("schemas"),
        )
    assert conflict.value.code is ErrorCode.REPORT_FAMILY_INVALID
