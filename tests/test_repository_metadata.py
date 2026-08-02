from pathlib import Path

import yaml


def test_readmes_do_not_claim_unimplemented_publication_pipeline() -> None:
    english = Path("README.md").read_text(encoding="utf-8")
    chinese = Path("README.zh-CN.md").read_text(encoding="utf-8")

    assert "architecture and schema prototype" in english
    assert "架构与Schema原型" in chinese
    assert "publication-grade workflow is not yet implemented" in english
    assert "投稿级完整工作流尚未实现" in chinese


def test_license_and_citation_metadata_exist() -> None:
    assert "Apache License" in Path("LICENSE").read_text(encoding="utf-8")
    citation = yaml.safe_load(Path("CITATION.cff").read_text(encoding="utf-8"))
    assert citation["version"] == "0.1.0"
    assert citation["license"] == "Apache-2.0"


def test_ci_runs_supported_python_matrix() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert '"3.11"' in workflow
    assert '"3.12"' in workflow
    assert '"3.13"' in workflow
    assert "uv run pytest -v" in workflow


def test_design_spec_links_to_callable_core_plan() -> None:
    spec = Path(
        "docs/superpowers/specs/2026-08-03-econ-management-meta-skill-design.md"
    ).read_text(encoding="utf-8")
    assert "../plans/2026-08-03-callable-core-v0.1.0.md" in spec
