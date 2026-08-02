from pathlib import Path

import pytest

from econ_management_meta.errors import ErrorCode, WorkflowError
from econ_management_meta.tabular import append_unique_row, ensure_csv, read_csv_rows, stable_id


HEADERS = ("decision_id", "record_id", "reviewer", "decision")


def test_ensure_csv_creates_exact_headers_once(tmp_path: Path) -> None:
    path = tmp_path / "decisions.csv"
    ensure_csv(path, HEADERS)
    ensure_csv(path, HEADERS)

    assert path.read_text(encoding="utf-8") == "decision_id,record_id,reviewer,decision\n"


def test_append_unique_row_blocks_duplicate_composite_key(tmp_path: Path) -> None:
    path = tmp_path / "decisions.csv"
    row = {
        "decision_id": "DEC-1",
        "record_id": "REC-1",
        "reviewer": "reviewer-1",
        "decision": "INCLUDE",
    }
    append_unique_row(path, HEADERS, row, ("record_id", "reviewer"))

    with pytest.raises(WorkflowError) as caught:
        append_unique_row(path, HEADERS, row, ("record_id", "reviewer"))

    assert caught.value.code is ErrorCode.DUPLICATE_DECISION
    assert read_csv_rows(path) == [row]


def test_stable_id_is_deterministic_and_prefixed() -> None:
    left = stable_id("REC", "A database", "source-17", 2026)
    right = stable_id("REC", "A database", "source-17", 2026)

    assert left == right
    assert left.startswith("REC-")
    assert len(left) == 20
