from pathlib import Path

from econ_management_meta.search import (
    deduplicate_records,
    import_search_file,
    normalize_doi,
    normalize_title,
    register_search_run,
)
from econ_management_meta.tabular import read_csv_rows


def search_run(database: str, batch: str) -> dict[str, object]:
    return {
        "database": database,
        "platform": "Test Platform",
        "search_date": "2026-08-03",
        "query": "AI AND innovation",
        "hit_count": 1,
        "export_batch": batch,
    }


def test_normalization_for_doi_and_title() -> None:
    assert normalize_doi("https://doi.org/10.1000/ABC.1 ") == "10.1000/abc.1"
    assert normalize_title(" AI—and   Innovation! ") == "ai and innovation"


def test_imports_csv_ris_bibtex_and_endnote_xml(initialized_project: Path) -> None:
    fixtures = Path("tests/fixtures/search")
    cases = [
        ("csv", "sample.csv", "CSV-1", "10.1000/abc.1"),
        ("ris", "sample.ris", "RIS-1", "10.1000/abc.1"),
        ("bibtex", "sample.bib", "BIB1", "10.1000/xyz.2"),
        ("endnote-xml", "sample.xml", "XML-1", "10.1000/xml.3"),
    ]

    for index, (fmt, filename, source_id, doi) in enumerate(cases, start=1):
        run_id = register_search_run(
            initialized_project,
            search_run(f"Database {index}", f"batch-{index}"),
            actor="information-specialist",
            schema_dir=Path("schemas"),
        )
        result = import_search_file(
            initialized_project,
            run_id,
            fixtures / filename,
            fmt,
            actor="information-specialist",
            schema_dir=Path("schemas"),
        )
        assert result["imported"] == 1

    rows = read_csv_rows(initialized_project / "02_search/imported-records.csv")
    assert len(rows) == 4
    assert {row["source_record_id"] for row in rows} == {case[2] for case in cases}
    assert {row["doi"] for row in rows} == {case[3] for case in cases}
    assert all(row["source_file"] for row in rows)
    assert all(row["search_run_id"] for row in rows)


def test_deduplication_preserves_provenance_and_logs_metadata_conflicts(
    initialized_project: Path,
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.csv"
    first.write_text(
        "id,title,authors,year,doi,abstract,journal\n"
        "A1,AI and Innovation,Smith,2024,10.1000/abc.1,First abstract,J A\n",
        encoding="utf-8",
    )
    second = tmp_path / "second.csv"
    second.write_text(
        "id,title,authors,year,doi,abstract,journal\n"
        "B1,AI & Innovation,Smith,2025,https://doi.org/10.1000/ABC.1,Second abstract,J A\n",
        encoding="utf-8",
    )

    for index, source in enumerate((first, second), start=1):
        run_id = register_search_run(
            initialized_project,
            search_run(f"Database {index}", f"batch-{index}"),
            actor="information-specialist",
            schema_dir=Path("schemas"),
        )
        import_search_file(
            initialized_project,
            run_id,
            source,
            "csv",
            actor="information-specialist",
            schema_dir=Path("schemas"),
        )

    result = deduplicate_records(initialized_project, actor="review-lead")
    rows = read_csv_rows(initialized_project / "02_search/deduplicated-records.csv")
    conflicts = read_csv_rows(initialized_project / "02_search/deduplication-conflicts.csv")

    assert result == {"source_records": 2, "deduplicated_records": 1, "duplicates_merged": 1, "conflicts": 2}
    assert len(rows) == 1
    assert set(rows[0]["source_record_ids"].split("|")) == {"A1", "B1"}
    assert len(rows[0]["provenance_ids"].split("|")) == 2
    assert {row["field"] for row in conflicts} == {"title", "year"}
