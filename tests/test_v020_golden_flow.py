from pathlib import Path

from econ_management_meta import __version__
from econ_management_meta.extraction import export_verified_extraction, record_extraction
from econ_management_meta.io import read_yaml
from econ_management_meta.locks import create_lock, verify_lock
from econ_management_meta.protocol import create_amendment, create_protocol
from econ_management_meta.project import initialize_project, validate_project
from econ_management_meta.reports import assign_report_family, export_report_family_map
from econ_management_meta.screening import export_screening_consensus, record_screening_decision
from econ_management_meta.search import deduplicate_records, import_search_file, register_search_run
from econ_management_meta.tabular import read_csv_rows


def protocol_payload() -> dict[str, object]:
    return {
        "research_question": "How is organizational AI related to innovation outcomes?",
        "unit_of_inference": "firm-level effect",
        "eligibility": {
            "populations": ["firms"],
            "exposures": ["AI adoption"],
            "outcomes": ["innovation"],
            "designs": ["observational"],
        },
        "evidence_lanes": ["marginal_association"],
        "search_plan": {"databases": ["Test DB"], "grey_literature": True},
        "screening_plan": {
            "title_abstract_reviewers": 2,
            "fulltext_reviewers": 2,
            "independent": True,
            "ai_final_decision": False,
        },
        "extraction_plan": {"extractors": 2, "independent": True, "human_verification": True},
        "ai_assistance": {"final_screening_decision": False, "final_extraction_decision": False},
        "analyses": {"primary": ["observed effect"], "secondary": [], "sensitivity": [], "exploratory": []},
    }


def test_v020_golden_evidence_acquisition_and_coding_flow(tmp_path: Path) -> None:
    assert __version__ == "0.2.0"
    project = initialize_project(
        "AI and innovation",
        Path("profiles/ai-innovation"),
        tmp_path / "project",
        Path("schemas"),
    )

    protocol = create_protocol(project, "1.0", protocol_payload(), "principal-investigator", Path("schemas"))
    amendment = create_amendment(
        project,
        {
            "from_version": "1.0",
            "to_version": "1.1",
            "change_type": "CLARIFICATION",
            "original_rule": "Innovation outcomes",
            "new_rule": "Firm-level innovation outcomes",
            "rationale": "Clarify the analytical level without changing scope.",
            "outcome_information_seen": {"study_level_results": False, "pooled_results": False},
            "affected_artifacts": ["eligibility"],
            "confirmatory_status_after_change": "CONFIRMATORY",
        },
        "principal-investigator",
        Path("schemas"),
    )
    assert read_yaml(amendment)["change_type"] == "CLARIFICATION"
    protocol_lock = create_lock(project, "protocol", "1.0", [protocol, amendment], "principal-investigator")
    assert verify_lock(project, protocol_lock)["valid"] is True

    run_id = register_search_run(
        project,
        {
            "database": "Test DB",
            "platform": "Test Platform",
            "search_date": "2026-08-03",
            "query": "AI AND innovation",
            "hit_count": 1,
            "export_batch": "batch-1",
        },
        "information-specialist",
        Path("schemas"),
    )
    import_search_file(
        project,
        run_id,
        Path("tests/fixtures/search/sample.csv"),
        "csv",
        "information-specialist",
        Path("schemas"),
    )
    deduplicate_records(project, "review-lead")
    record_id = read_csv_rows(project / "02_search/deduplicated-records.csv")[0]["record_id"]

    for reviewer in ("reviewer-1", "reviewer-2"):
        record_screening_decision(
            project, "title-abstract", record_id, reviewer, "INCLUDE",
            None, None, "eligible", Path("schemas")
        )
    export_screening_consensus(project, "title-abstract")

    for reviewer in ("reviewer-1", "reviewer-2"):
        record_screening_decision(
            project, "fulltext", record_id, reviewer, "INCLUDE",
            None, "p. 1", "eligible", Path("schemas")
        )
    export_screening_consensus(project, "fulltext")

    assign_report_family(
        project, record_id, "RFAM-1", "STUDY-1", "JOURNAL_ARTICLE",
        "reviewer-1", "Single identified report for this study.", Path("schemas")
    )
    assert export_report_family_map(project).exists()

    for extractor in ("extractor-1", "extractor-2"):
        record_extraction(
            project, record_id, "STUDY-1", "sample-size", extractor, 240,
            "p. 12", "The final analytical sample contained 240 firms.", Path("schemas")
        )
    verified = export_verified_extraction(project)
    assert read_csv_rows(verified)[0]["verification_status"] == "VERIFIED"

    validation = validate_project(project, Path("schemas"))
    assert validation["valid"] is True
    assert validation["locks_verified"] == 1
