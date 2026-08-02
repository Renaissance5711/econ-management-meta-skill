from pathlib import Path

import pytest

from econ_management_meta.errors import ErrorCode, WorkflowError
from econ_management_meta.io import read_yaml
from econ_management_meta.protocol import (
    create_amendment,
    create_protocol,
    list_protocol_versions,
    validate_protocol,
)


def valid_protocol() -> dict[str, object]:
    return {
        "research_question": "How is organizational AI related to innovation outcomes?",
        "unit_of_inference": "firm-level effect",
        "eligibility": {
            "populations": ["firms", "employees"],
            "exposures": ["AI adoption", "AI capability"],
            "outcomes": ["innovation quantity", "innovation quality"],
            "designs": ["observational", "experimental", "quasi-experimental"],
        },
        "evidence_lanes": ["marginal_association", "experimental_effect"],
        "search_plan": {"databases": ["Web of Science"], "grey_literature": True},
        "screening_plan": {
            "title_abstract_reviewers": 2,
            "fulltext_reviewers": 2,
            "independent": True,
            "ai_final_decision": False,
        },
        "extraction_plan": {
            "extractors": 2,
            "independent": True,
            "human_verification": True,
        },
        "ai_assistance": {
            "search_term_suggestion": True,
            "screening_recommendation": True,
            "final_screening_decision": False,
            "final_extraction_decision": False,
        },
        "analyses": {
            "primary": ["observed marginal association"],
            "secondary": [],
            "sensitivity": ["exclude high risk of bias"],
            "exploratory": [],
        },
    }


def test_protocol_is_versioned_validated_and_immutable(initialized_project: Path) -> None:
    path = create_protocol(
        initialized_project,
        "1.0",
        valid_protocol(),
        actor="principal-investigator",
        schema_dir=Path("schemas"),
    )

    assert path.name == "protocol-v1.0.yaml"
    result = validate_protocol(path, Path("schemas"))
    assert result == {"valid": True, "version": "1.0", "approved_by": "principal-investigator"}
    assert list_protocol_versions(initialized_project) == ["1.0"]

    with pytest.raises(WorkflowError) as caught:
        create_protocol(
            initialized_project,
            "1.0",
            valid_protocol(),
            actor="principal-investigator",
            schema_dir=Path("schemas"),
        )
    assert caught.value.code is ErrorCode.ARTIFACT_ALREADY_EXISTS


def test_protocol_rejects_ai_final_screening_authority(initialized_project: Path) -> None:
    protocol = valid_protocol()
    protocol["screening_plan"]["ai_final_decision"] = True

    with pytest.raises(WorkflowError) as caught:
        create_protocol(
            initialized_project,
            "1.0",
            protocol,
            actor="principal-investigator",
            schema_dir=Path("schemas"),
        )

    assert caught.value.code is ErrorCode.PROTOCOL_INVALID


def test_protocol_requires_named_human_actor(initialized_project: Path) -> None:
    with pytest.raises(WorkflowError) as caught:
        create_protocol(
            initialized_project,
            "1.0",
            valid_protocol(),
            actor="AI assistant",
            schema_dir=Path("schemas"),
        )

    assert caught.value.code is ErrorCode.HUMAN_ACTOR_REQUIRED


def test_prospective_amendment_records_information_seen(initialized_project: Path) -> None:
    create_protocol(
        initialized_project,
        "1.0",
        valid_protocol(),
        actor="principal-investigator",
        schema_dir=Path("schemas"),
    )
    amendment = {
        "from_version": "1.0",
        "to_version": "1.1",
        "change_type": "PROSPECTIVE_MAJOR_AMENDMENT",
        "original_rule": "Pool all innovation outcomes.",
        "new_rule": "Separate quantity and quality outcomes.",
        "rationale": "Construct coding indicates non-equivalence.",
        "outcome_information_seen": {
            "study_level_results": False,
            "pooled_results": False,
        },
        "affected_artifacts": ["eligibility.yaml", "analysis-plan.yaml"],
        "confirmatory_status_after_change": "AMENDED_PROSPECTIVELY",
    }

    path = create_amendment(
        initialized_project,
        amendment,
        actor="principal-investigator",
        schema_dir=Path("schemas"),
    )

    saved = read_yaml(path)
    assert saved["change_type"] == "PROSPECTIVE_MAJOR_AMENDMENT"
    assert saved["outcome_information_seen"]["pooled_results"] is False
    assert saved["approved_by"] == "principal-investigator"
