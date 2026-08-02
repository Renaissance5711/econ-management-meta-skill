from pathlib import Path

import pytest
import yaml

from econ_management_meta.errors import ErrorCode, WorkflowError
from econ_management_meta.profile import load_profile, validate_profile_policy


def test_ai_innovation_profile_passes_schema_and_policy() -> None:
    profile = load_profile(
        Path("profiles/ai-innovation"),
        Path("schemas/profile.schema.json"),
    )

    assert profile.id == "ai-innovation"
    assert profile.version == "0.1.0"
    assert profile.extends == "core-management-meta"


def test_profile_cannot_enable_ai_final_decisions() -> None:
    raw = yaml.safe_load(
        """
profile:
  id: unsafe
requirements:
  ai_final_decision: true
"""
    )

    with pytest.raises(WorkflowError) as caught:
        validate_profile_policy(raw)

    assert caught.value.code is ErrorCode.PROFILE_WEAKENS_CORE
    assert caught.value.details["path"] == "requirements.ai_final_decision"
