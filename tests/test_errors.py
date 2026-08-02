from econ_management_meta.errors import ErrorCode, WorkflowError


def test_workflow_error_serializes_stable_code_and_details() -> None:
    error = WorkflowError(
        ErrorCode.PROFILE_WEAKENS_CORE,
        "profile disables a mandatory gate",
        {"path": "constraints.ai_final_decision"},
    )

    assert error.as_dict() == {
        "error": "PROFILE_WEAKENS_CORE",
        "message": "profile disables a mandatory gate",
        "details": {"path": "constraints.ai_final_decision"},
    }
