from pathlib import Path

from econ_management_meta.skills import validate_skill_contract


STAGE_SKILLS = [
    "econ-management-meta",
    "meta-protocol",
    "meta-search",
    "meta-screening",
    "meta-fulltext",
    "meta-extraction",
    "meta-sample-overlap",
    "meta-construct-alignment",
    "meta-estimand-alignment",
    "meta-effect-size",
    "meta-analysis-r",
    "meta-bias-robustness",
    "meta-evidence-confidence",
    "meta-manuscript",
    "meta-publication-qa",
]


def test_root_skill_has_required_frontmatter_and_safety_rules() -> None:
    metadata = validate_skill_contract(Path("SKILL.md"))
    body = Path("SKILL.md").read_text(encoding="utf-8")

    assert metadata["name"] == "econ-management-meta"
    assert metadata["version"] == "0.2.0"
    assert metadata["license"] == "Apache-2.0"
    assert "AI may not make final eligibility decisions" in body
    assert "UNAVAILABLE_IN_VERSION" in body
    assert "emm validate-profile" in body


def test_all_stage_skills_have_contracts_and_human_boundaries() -> None:
    for name in STAGE_SKILLS:
        path = Path("skills") / name / "SKILL.md"
        metadata = validate_skill_contract(path)
        body = path.read_text(encoding="utf-8")
        assert metadata["name"] == name
        assert "## Accepted inputs" in body
        assert "## Human-only decisions" in body
        assert "## Blocking conditions" in body
        assert "## v0.2.0 availability" in body


def test_adapters_reference_the_same_root_skill() -> None:
    claude = Path("adapters/claude-code/INSTALL.md").read_text(encoding="utf-8")
    codex = Path("adapters/codex/INSTALL.md").read_text(encoding="utf-8")
    generic = Path("adapters/generic-agent/manifest.yaml").read_text(encoding="utf-8")

    assert "SKILL.md" in claude
    assert "SKILL.md" in codex
    assert "root_skill: SKILL.md" in generic
    assert "Do not weaken" in claude
    assert "Do not weaken" in codex


def test_v020_stage_skills_mark_only_implemented_actions_available() -> None:
    implemented = {
        "meta-protocol": "Schema-validated protocol creation",
        "meta-search": "CSV/RIS/BibTeX/EndNote XML import",
        "meta-screening": "Independent human decisions",
        "meta-fulltext": "report-family and study-family assignments",
        "meta-extraction": "Manual dual extraction",
    }
    for name, phrase in implemented.items():
        body = (Path("skills") / name / "SKILL.md").read_text(encoding="utf-8")
        assert phrase in body
        assert "AVAILABLE_IN_VERSION" in body
        assert "UNAVAILABLE_IN_VERSION" in body
