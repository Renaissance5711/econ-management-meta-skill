from pathlib import Path

import pytest

from econ_management_meta.errors import ErrorCode, WorkflowError
from econ_management_meta.extraction import (
    export_verified_extraction,
    list_extraction_conflicts,
    record_extraction,
    resolve_extraction,
)
from econ_management_meta.tabular import read_csv_rows


def submit(
    project: Path,
    extractor: str,
    value: object,
    field_id: str = "sample-size",
) -> str:
    return record_extraction(
        project,
        report_id="REP-1",
        study_id="STUDY-1",
        field_id=field_id,
        extractor=extractor,
        value=value,
        source_page="p. 12",
        source_quote="The final sample contained 240 firms.",
        schema_dir=Path("schemas"),
    )


def test_matching_dual_extraction_exports_verified_value(initialized_project: Path) -> None:
    submit(initialized_project, "extractor-1", 240)
    submit(initialized_project, "extractor-2", 240)

    assert list_extraction_conflicts(initialized_project) == []
    path = export_verified_extraction(initialized_project)
    rows = read_csv_rows(path)
    assert rows[0]["verification_status"] == "VERIFIED"
    assert rows[0]["resolved_value_json"] == "240"
    assert rows[0]["resolution_type"] == "DUAL_AGREEMENT"


def test_conflicting_values_require_human_resolution(initialized_project: Path) -> None:
    submit(initialized_project, "extractor-1", 240)
    submit(initialized_project, "extractor-2", 242)

    conflicts = list_extraction_conflicts(initialized_project)
    assert conflicts[0]["field_id"] == "sample-size"
    assert set(conflicts[0]["values"]) == {240, 242}

    with pytest.raises(WorkflowError) as caught:
        export_verified_extraction(initialized_project)
    assert caught.value.code is ErrorCode.EXTRACTION_CONFLICT

    resolve_extraction(
        initialized_project,
        "REP-1",
        "STUDY-1",
        "sample-size",
        resolver="adjudicator-1",
        resolved_value=240,
        rationale="The flow diagram confirms the final analytical sample.",
    )
    rows = read_csv_rows(export_verified_extraction(initialized_project))
    assert rows[0]["resolved_value_json"] == "240"
    assert rows[0]["verified_by"] == "adjudicator-1"
    assert rows[0]["resolution_type"] == "HUMAN_ADJUDICATION"


def test_extraction_requires_source_provenance(initialized_project: Path) -> None:
    with pytest.raises(WorkflowError) as caught:
        record_extraction(
            initialized_project,
            "REP-1",
            "STUDY-1",
            "sample-size",
            "extractor-1",
            240,
            "",
            "",
            Path("schemas"),
        )
    assert caught.value.code is ErrorCode.EXTRACTION_INVALID


def test_same_extractor_cannot_submit_same_field_twice(initialized_project: Path) -> None:
    submit(initialized_project, "extractor-1", 240)

    with pytest.raises(WorkflowError) as caught:
        submit(initialized_project, "extractor-1", 241)
    assert caught.value.code is ErrorCode.DUPLICATE_DECISION


def test_verified_export_requires_two_distinct_extractors(initialized_project: Path) -> None:
    submit(initialized_project, "extractor-1", 240)

    with pytest.raises(WorkflowError) as caught:
        export_verified_extraction(initialized_project)
    assert caught.value.code is ErrorCode.EXTRACTION_INVALID
