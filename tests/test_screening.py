from pathlib import Path

import pytest

from econ_management_meta.errors import ErrorCode, WorkflowError
from econ_management_meta.screening import (
    export_screening_consensus,
    record_screening_decision,
    resolve_screening_conflict,
    screening_agreement,
)
from econ_management_meta.tabular import read_csv_rows


def test_two_independent_title_abstract_decisions_produce_agreement(
    initialized_project: Path,
) -> None:
    for reviewer in ("reviewer-1", "reviewer-2"):
        record_screening_decision(
            initialized_project,
            "title-abstract",
            "REC-1",
            reviewer,
            "INCLUDE",
            None,
            None,
            "eligible topic",
            Path("schemas"),
        )

    summary = screening_agreement(initialized_project, "title-abstract")
    assert summary["records_with_two_decisions"] == 1
    assert summary["raw_agreement"] == 1.0
    assert summary["include_agreement"] == 1.0
    assert summary["conflict_count"] == 0


def test_same_reviewer_cannot_submit_twice(initialized_project: Path) -> None:
    kwargs = dict(
        project_dir=initialized_project,
        stage="title-abstract",
        record_id="REC-1",
        reviewer="reviewer-1",
        decision="INCLUDE",
        reason_code=None,
        source_page=None,
        note=None,
        schema_dir=Path("schemas"),
    )
    record_screening_decision(**kwargs)

    with pytest.raises(WorkflowError) as caught:
        record_screening_decision(**kwargs)
    assert caught.value.code is ErrorCode.DUPLICATE_DECISION


def test_fulltext_exclusion_requires_reason_and_page(initialized_project: Path) -> None:
    with pytest.raises(WorkflowError) as caught:
        record_screening_decision(
            initialized_project,
            "fulltext",
            "REC-1",
            "reviewer-1",
            "EXCLUDE",
            None,
            None,
            "not eligible",
            Path("schemas"),
        )

    assert caught.value.code is ErrorCode.SCREENING_INVALID


def test_disagreement_requires_distinct_human_adjudicator(initialized_project: Path) -> None:
    record_screening_decision(
        initialized_project, "title-abstract", "REC-1", "reviewer-1", "INCLUDE",
        None, None, None, Path("schemas")
    )
    record_screening_decision(
        initialized_project, "title-abstract", "REC-1", "reviewer-2", "EXCLUDE",
        "WRONG_TOPIC", None, None, Path("schemas")
    )

    with pytest.raises(WorkflowError) as caught:
        export_screening_consensus(initialized_project, "title-abstract")
    assert caught.value.code is ErrorCode.SCREENING_CONFLICT

    with pytest.raises(WorkflowError) as same_reviewer:
        resolve_screening_conflict(
            initialized_project, "title-abstract", "REC-1", "reviewer-1",
            "INCLUDE", None, None, "adjudication", Path("schemas")
        )
    assert same_reviewer.value.code is ErrorCode.SCREENING_INVALID

    resolve_screening_conflict(
        initialized_project, "title-abstract", "REC-1", "adjudicator-1",
        "INCLUDE", None, None, "the exposure is eligible", Path("schemas")
    )
    consensus_path = export_screening_consensus(initialized_project, "title-abstract")
    rows = read_csv_rows(consensus_path)
    assert rows[0]["final_decision"] == "INCLUDE"
    assert rows[0]["verified_by"] == "adjudicator-1"


def test_fulltext_consensus_requires_two_distinct_reviewers(initialized_project: Path) -> None:
    record_screening_decision(
        initialized_project, "fulltext", "REC-1", "reviewer-1", "INCLUDE",
        None, "p. 1", None, Path("schemas")
    )

    with pytest.raises(WorkflowError) as caught:
        export_screening_consensus(initialized_project, "fulltext")
    assert caught.value.code is ErrorCode.SCREENING_INVALID
