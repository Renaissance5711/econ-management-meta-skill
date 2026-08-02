# Callable Core v0.1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a callable, testable v0.1.0 architecture prototype that can validate domain profiles, initialize a review project, enforce fail-closed state and lock rules, and expose the workflow through a root `SKILL.md` plus platform adapters.

**Architecture:** A small Python package named `econ_management_meta` provides schema validation, project initialization, state transitions, integrity locks, and a standard-library CLI. Declarative YAML/JSON files remain the source of truth. Agent-facing Markdown skills call the CLI and preserve the human-verification boundaries defined by the approved design specification.

**Tech Stack:** Python 3.11+, `uv`, `pytest`, PyYAML, `jsonschema`, JSON Schema Draft 2020-12, Markdown skill files, YAML profiles, GitHub Actions.

## Global Constraints

- License target: Apache License 2.0.
- English is normative; Chinese documentation is explanatory.
- Files are the source of truth; SQLite is not required in v0.1.0.
- AI suggestions must never become final eligibility, construct, estimand, effect-size, model, or causal-claim decisions.
- Unverified effects must be blocked from primary analysis.
- Profiles may add or strengthen requirements but may not weaken core gates.
- Protocol and analysis-specification locks are versioned and must be hash-verifiable.
- Stage failures are fail-closed: invalid, missing, stale, or incompatible artifacts stop the command with a non-zero exit code.
- Formal R synthesis, Quarto manuscript generation, automated search, screening, extraction, and bias-model execution are not implemented in v0.1.0; the callable core must label those stages as unavailable rather than simulate them.

---

## File Map

### Python package

- `src/econ_management_meta/__init__.py`: package version.
- `src/econ_management_meta/errors.py`: typed fail-closed exceptions and stable error codes.
- `src/econ_management_meta/io.py`: canonical YAML/JSON read/write and normalized hashing.
- `src/econ_management_meta/profile.py`: profile loading, schema validation, and core-gate policy validation.
- `src/econ_management_meta/project.py`: deterministic project initialization and project validation.
- `src/econ_management_meta/state.py`: stage definitions, transition rules, state persistence, and prerequisite checks.
- `src/econ_management_meta/locks.py`: lock creation and stale-lock verification.
- `src/econ_management_meta/skills.py`: skill frontmatter parsing and contract validation.
- `src/econ_management_meta/cli.py`: `emm` command-line interface.

### Schemas and profiles

- `schemas/profile.schema.json`: declarative profile contract.
- `schemas/project.schema.json`: project manifest contract.
- `schemas/pipeline-state.schema.json`: workflow state contract.
- `schemas/lock.schema.json`: integrity lock contract.
- `profiles/ai-innovation/profile.yaml`: initial profile manifest.
- `profiles/ai-innovation/ontology/constructs.yaml`: initial AI and innovation construct tree.
- `profiles/ai-innovation/coding/moderators.yaml`: initial theory-first moderator cards.
- `profiles/ai-innovation/tests/valid-cases.yaml`: valid profile fixtures.
- `profiles/ai-innovation/tests/invalid-cases.yaml`: forbidden weakening attempts.

### Skills and adapters

- `SKILL.md`: root callable orchestrator.
- `skills/*/SKILL.md`: bounded stage skills.
- `adapters/claude-code/INSTALL.md`: Claude Code installation and invocation.
- `adapters/codex/INSTALL.md`: Codex installation and invocation.
- `adapters/generic-agent/manifest.yaml`: platform-neutral discovery metadata.

### Tests and example

- `tests/test_profile.py`: profile schema and policy tests.
- `tests/conftest.py`: shared initialized-project fixture introduced with the initializer.
- `tests/test_project.py`: deterministic initializer tests.
- `tests/test_state.py`: transition and prerequisite tests.
- `tests/test_locks.py`: normalized hashing and stale-lock tests.
- `tests/test_skills.py`: skill contract tests.
- `tests/test_cli.py`: CLI behavior and exit-code tests.
- `tests/test_golden_project.py`: complete v0.1.0 integration test.
- `examples/golden-project/expected-tree.txt`: approved initialized tree.

### Repository metadata

- `pyproject.toml`: package, CLI, dependencies, pytest configuration.
- `.python-version`: Python 3.11 floor for `uv`.
- `.gitignore`: local environments, caches, generated projects, and worktrees.
- `README.md`: English quick start and v0.1.0 boundaries.
- `README.zh-CN.md`: Chinese quick start and limitations.
- `LICENSE`: Apache-2.0 text.
- `NOTICE`: project attribution notice.
- `CITATION.cff`: software citation metadata.
- `CHANGELOG.md`: v0.1.0 entry.
- `.github/workflows/ci.yml`: Python matrix and contract tests.

---

### Task 1: Package Skeleton and Typed Errors

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `src/econ_management_meta/__init__.py`
- Create: `src/econ_management_meta/errors.py`
- Test: `tests/test_errors.py`

**Interfaces:**
- Produces: `__version__: str`
- Produces: `ErrorCode(str, Enum)`
- Produces: `WorkflowError(code: ErrorCode, message: str, details: dict[str, object] | None = None)`
- Later tasks rely on `WorkflowError.as_dict() -> dict[str, object]` and process exit code `2` for validation failures.

- [ ] **Step 1: Write the failing error serialization test**

```python
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
```

- [ ] **Step 2: Run the test and verify RED**

Run: `uv run pytest tests/test_errors.py -v`

Expected: collection fails because `econ_management_meta.errors` does not exist.

- [ ] **Step 3: Add minimal package metadata and implementation**

`pyproject.toml` must declare:

```toml
[project]
name = "econ-management-meta-skill"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["PyYAML>=6.0", "jsonschema>=4.23"]

[project.scripts]
emm = "econ_management_meta.cli:main"

[dependency-groups]
dev = ["pytest>=8.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/econ_management_meta"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

`ErrorCode` must initially include:

```python
PROFILE_SCHEMA_INVALID = "PROFILE_SCHEMA_INVALID"
PROFILE_WEAKENS_CORE = "PROFILE_WEAKENS_CORE"
PROJECT_SCHEMA_INVALID = "PROJECT_SCHEMA_INVALID"
INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"
PREREQUISITE_NOT_LOCKED = "PREREQUISITE_NOT_LOCKED"
LOCK_STALE = "LOCK_STALE"
LOCK_SCHEMA_INVALID = "LOCK_SCHEMA_INVALID"
SKILL_CONTRACT_INVALID = "SKILL_CONTRACT_INVALID"
PATH_NOT_EMPTY = "PATH_NOT_EMPTY"
UNAVAILABLE_IN_VERSION = "UNAVAILABLE_IN_VERSION"
```

- [ ] **Step 4: Run the test and verify GREEN**

Run: `uv run pytest tests/test_errors.py -v`

Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .python-version src/econ_management_meta tests/test_errors.py
git commit -m "feat: add package skeleton and workflow errors"
```

---

### Task 2: Canonical I/O and Deterministic Hashing

**Files:**
- Create: `src/econ_management_meta/io.py`
- Test: `tests/test_io.py`

**Interfaces:**
- Produces: `read_yaml(path: Path) -> dict[str, object]`
- Produces: `write_yaml(path: Path, data: Mapping[str, object]) -> None`
- Produces: `read_json(path: Path) -> dict[str, object]`
- Produces: `write_json(path: Path, data: Mapping[str, object]) -> None`
- Produces: `canonical_json_bytes(data: object) -> bytes`
- Produces: `sha256_data(data: object) -> str`
- Produces: `sha256_file(path: Path) -> str`

- [ ] **Step 1: Write failing canonical-hash tests**

```python
from econ_management_meta.io import canonical_json_bytes, sha256_data


def test_canonical_hash_ignores_mapping_key_order() -> None:
    left = {"b": 2, "a": {"y": 1, "x": 0}}
    right = {"a": {"x": 0, "y": 1}, "b": 2}

    assert canonical_json_bytes(left) == canonical_json_bytes(right)
    assert sha256_data(left) == sha256_data(right)
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/test_io.py -v`

Expected: import failure for `econ_management_meta.io`.

- [ ] **Step 3: Implement canonical serialization**

Use `json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)` and append a trailing newline only when writing files, not when hashing.

- [ ] **Step 4: Run and verify GREEN**

Run: `uv run pytest tests/test_io.py -v`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/econ_management_meta/io.py tests/test_io.py
git commit -m "feat: add canonical project IO and hashing"
```

---

### Task 3: Schema-Governed Profile Validation

**Files:**
- Create: `schemas/profile.schema.json`
- Create: `src/econ_management_meta/profile.py`
- Create: `profiles/ai-innovation/profile.yaml`
- Create: `profiles/ai-innovation/ontology/constructs.yaml`
- Create: `profiles/ai-innovation/coding/moderators.yaml`
- Create: `profiles/ai-innovation/tests/valid-cases.yaml`
- Create: `profiles/ai-innovation/tests/invalid-cases.yaml`
- Test: `tests/test_profile.py`

**Interfaces:**
- Produces: `Profile(id: str, version: str, schema_version: int, core_compatibility: str, extends: str, path: Path, raw: dict[str, object])`
- Produces: `load_profile(profile_dir: Path, schema_path: Path) -> Profile`
- Produces: `validate_profile_policy(raw: Mapping[str, object]) -> None`
- The policy validator rejects a profile that changes any mandatory core gate from `true` to `false` or enables `ai_final_decision`.

- [ ] **Step 1: Write the failing safe-profile test**

```python
from pathlib import Path

from econ_management_meta.profile import load_profile


def test_ai_innovation_profile_passes_schema_and_policy() -> None:
    profile = load_profile(
        Path("profiles/ai-innovation"),
        Path("schemas/profile.schema.json"),
    )

    assert profile.id == "ai-innovation"
    assert profile.version == "0.1.0"
    assert profile.extends == "core-management-meta"
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/test_profile.py::test_ai_innovation_profile_passes_schema_and_policy -v`

Expected: import failure for `econ_management_meta.profile`.

- [ ] **Step 3: Write the schema, profile, and validator**

The profile schema requires this structure:

```yaml
profile:
  id: ai-innovation
  name: AI and Innovation
  version: 0.1.0
  schema_version: 1
  core_compatibility: ">=0.1.0,<1.0.0"
  extends: core-management-meta
  normative_language: en
  status: experimental
requirements:
  dual_human_fulltext: true
  human_effect_verification: true
  construct_alignment_gate: true
  estimand_alignment_gate: true
  dependency_check: true
  protocol_lock: true
  analysis_spec_lock: true
  claim_audit: true
  ai_final_decision: false
resources:
  constructs: ontology/constructs.yaml
  moderators: coding/moderators.yaml
```

- [ ] **Step 4: Run safe-profile test and verify GREEN**

Run: `uv run pytest tests/test_profile.py::test_ai_innovation_profile_passes_schema_and_policy -v`

Expected: pass.

- [ ] **Step 5: Write a failing policy test for a weakening profile**

```python
import pytest

from econ_management_meta.errors import ErrorCode, WorkflowError
from econ_management_meta.profile import validate_profile_policy


def test_profile_cannot_enable_ai_final_decisions() -> None:
    raw = {
        "profile": {"id": "unsafe"},
        "requirements": {"ai_final_decision": True},
    }

    with pytest.raises(WorkflowError) as caught:
        validate_profile_policy(raw)

    assert caught.value.code is ErrorCode.PROFILE_WEAKENS_CORE
    assert caught.value.details["path"] == "requirements.ai_final_decision"
```

- [ ] **Step 6: Run the policy test and verify RED**

Run: `uv run pytest tests/test_profile.py::test_profile_cannot_enable_ai_final_decisions -v`

Expected: test fails because the policy validator does not yet reject the setting.

- [ ] **Step 7: Implement mandatory gate policy and verify GREEN**

Mandatory `true` fields are exactly:

```text
dual_human_fulltext
human_effect_verification
construct_alignment_gate
estimand_alignment_gate
dependency_check
protocol_lock
analysis_spec_lock
claim_audit
```

`ai_final_decision` must be absent or `false`.

Run: `uv run pytest tests/test_profile.py -v`

Expected: all profile tests pass.

- [ ] **Step 8: Commit**

```bash
git add schemas/profile.schema.json profiles/ai-innovation src/econ_management_meta/profile.py tests/test_profile.py
git commit -m "feat: validate declarative domain profiles"
```

---

### Task 4: Deterministic Project Initializer

**Files:**
- Create: `schemas/project.schema.json`
- Create: `schemas/pipeline-state.schema.json`
- Create: `src/econ_management_meta/project.py`
- Create: `tests/conftest.py`
- Test: `tests/test_project.py`
- Create: `examples/golden-project/expected-tree.txt`

**Interfaces:**
- Produces: `initialize_project(topic: str, profile_dir: Path, output_dir: Path, schema_dir: Path) -> Path`
- Produces: `validate_project(project_dir: Path, schema_dir: Path) -> dict[str, object]`
- Writes `project.yaml`, `state/pipeline-state.yaml`, `state/decision-log.csv`, and `state/artifact-manifest.json`.
- Creates all numbered stage directories from `00_intake` through `15_publication_qa` plus `locks/`.

- [ ] **Step 1: Write the failing initializer test**

```python
from pathlib import Path

from econ_management_meta.project import initialize_project


def test_initializer_creates_canonical_project_tree(tmp_path: Path) -> None:
    project = initialize_project(
        topic="AI and innovation",
        profile_dir=Path("profiles/ai-innovation"),
        output_dir=tmp_path / "ai-innovation-meta",
        schema_dir=Path("schemas"),
    )

    assert (project / "project.yaml").exists()
    assert (project / "state/pipeline-state.yaml").exists()
    assert (project / "state/decision-log.csv").exists()
    assert (project / "state/artifact-manifest.json").exists()
    assert (project / "locks").is_dir()
    assert (project / "00_intake").is_dir()
    assert (project / "15_publication_qa").is_dir()
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/test_project.py::test_initializer_creates_canonical_project_tree -v`

Expected: import failure for `econ_management_meta.project`.

- [ ] **Step 3: Implement the minimal initializer**

Canonical stages:

```python
STAGE_DIRECTORIES = (
    "00_intake",
    "01_protocol",
    "02_search",
    "03_screening",
    "04_fulltext",
    "05_extraction",
    "06_sample_overlap",
    "07_construct_alignment",
    "08_estimand_alignment",
    "09_effect_size",
    "10_analysis_spec",
    "11_synthesis",
    "12_bias_robustness",
    "13_evidence_confidence",
    "14_manuscript",
    "15_publication_qa",
)
```

Reject a non-empty `output_dir` with `PATH_NOT_EMPTY`; never delete or overwrite user content.

- [ ] **Step 4: Run initializer test and verify GREEN**

Run: `uv run pytest tests/test_project.py::test_initializer_creates_canonical_project_tree -v`

Expected: pass.

- [ ] **Step 5: Add manifest and golden-tree tests**

Tests must validate manifests against the JSON Schemas and compare the generated paths to `examples/golden-project/expected-tree.txt`.

- [ ] **Step 6: Run complete project tests**

Run: `uv run pytest tests/test_project.py -v`

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add schemas/project.schema.json schemas/pipeline-state.schema.json src/econ_management_meta/project.py tests/conftest.py tests/test_project.py examples/golden-project/expected-tree.txt
git commit -m "feat: initialize deterministic meta-analysis projects"
```

---

### Task 5: Fail-Closed Stage State Machine

**Files:**
- Create: `src/econ_management_meta/state.py`
- Test: `tests/test_state.py`

**Interfaces:**
- Produces: `Stage(str, Enum)` with values matching canonical stage directory names.
- Produces: `StageStatus(str, Enum)` with `NOT_STARTED`, `IN_PROGRESS`, `READY_FOR_REVIEW`, `VERIFIED`, `LOCKED`, `BLOCKED`.
- Produces: `transition_stage(project_dir: Path, stage: Stage, target: StageStatus, actor: str, note: str) -> dict[str, object]`.
- `VERIFIED` and `LOCKED` require explicit human actor names; later stages require the immediately preceding stage to be `LOCKED`.

- [ ] **Step 1: Write failing happy-path state test**

```python
from econ_management_meta.state import Stage, StageStatus, transition_stage


def test_stage_moves_from_not_started_to_in_progress(initialized_project: Path) -> None:
    state = transition_stage(
        initialized_project,
        Stage.INTAKE,
        StageStatus.IN_PROGRESS,
        actor="researcher-1",
        note="begin feasibility scan",
    )

    assert state["stages"]["00_intake"]["status"] == "IN_PROGRESS"
    assert state["history"][-1]["actor"] == "researcher-1"
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/test_state.py::test_stage_moves_from_not_started_to_in_progress -v`

Expected: import failure for `econ_management_meta.state`.

- [ ] **Step 3: Implement transition table**

Allowed transitions:

```text
NOT_STARTED -> IN_PROGRESS | BLOCKED
IN_PROGRESS -> READY_FOR_REVIEW | BLOCKED
READY_FOR_REVIEW -> IN_PROGRESS | VERIFIED | BLOCKED
VERIFIED -> LOCKED | IN_PROGRESS | BLOCKED
BLOCKED -> IN_PROGRESS
LOCKED -> no transition
```

- [ ] **Step 4: Run happy-path test and verify GREEN**

Run: `uv run pytest tests/test_state.py::test_stage_moves_from_not_started_to_in_progress -v`

Expected: pass.

- [ ] **Step 5: Add failing prerequisite and lock tests**

Required tests:

```python
def test_stage_cannot_lock_before_verification(...): ...
def test_next_stage_cannot_start_until_previous_stage_locked(...): ...
def test_verified_stage_can_lock_and_unlocking_is_forbidden(...): ...
```

- [ ] **Step 6: Implement prerequisite checks and verify GREEN**

Run: `uv run pytest tests/test_state.py -v`

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add src/econ_management_meta/state.py tests/test_state.py
git commit -m "feat: enforce fail-closed workflow transitions"
```

---

### Task 6: Versioned Integrity Locks

**Files:**
- Create: `schemas/lock.schema.json`
- Create: `src/econ_management_meta/locks.py`
- Test: `tests/test_locks.py`

**Interfaces:**
- Produces: `create_lock(project_dir: Path, lock_type: str, version: str, artifacts: Sequence[Path], actor: str) -> Path`
- Produces: `verify_lock(project_dir: Path, lock_path: Path) -> dict[str, object]`
- Lock stores relative artifact paths and SHA-256 file hashes.
- Lock filenames follow `<lock-type>-v<version>.lock.yaml`.

- [ ] **Step 1: Write the failing unchanged-lock test**

```python
from econ_management_meta.locks import create_lock, verify_lock


def test_lock_verifies_unchanged_artifacts(initialized_project: Path) -> None:
    protocol = initialized_project / "01_protocol/protocol-v1.0.yaml"
    protocol.write_text("version: '1.0'\nquestion: AI and innovation\n", encoding="utf-8")

    lock_path = create_lock(
        initialized_project,
        "protocol",
        "1.0",
        [protocol],
        actor="researcher-1",
    )

    result = verify_lock(initialized_project, lock_path)
    assert result["valid"] is True
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/test_locks.py::test_lock_verifies_unchanged_artifacts -v`

Expected: import failure for `econ_management_meta.locks`.

- [ ] **Step 3: Implement lock creation and verification**

Store:

```yaml
lock:
  type: protocol
  version: "1.0"
  actor: researcher-1
  created_at: <UTC ISO-8601>
  artifacts:
    - path: 01_protocol/protocol-v1.0.yaml
      sha256: <64 hex chars>
```

- [ ] **Step 4: Run unchanged-lock test and verify GREEN**

Run: `uv run pytest tests/test_locks.py::test_lock_verifies_unchanged_artifacts -v`

Expected: pass.

- [ ] **Step 5: Add a failing stale-lock test**

```python
def test_lock_fails_closed_after_artifact_changes(initialized_project: Path) -> None:
    # Create and lock protocol, then modify it.
    # verify_lock must raise WorkflowError(ErrorCode.LOCK_STALE).
```

- [ ] **Step 6: Implement stale detection and verify GREEN**

Run: `uv run pytest tests/test_locks.py -v`

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add schemas/lock.schema.json src/econ_management_meta/locks.py tests/test_locks.py
git commit -m "feat: add versioned integrity locks"
```

---

### Task 7: Standard-Library CLI

**Files:**
- Create: `src/econ_management_meta/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Produces console script `emm`.
- Commands:
  - `emm version`
  - `emm validate-profile <profile-dir>`
  - `emm init <topic> --profile <profile-dir> --output <project-dir>`
  - `emm validate-project <project-dir>`
  - `emm transition <project-dir> <stage> <target> --actor <name> --note <text>`
  - `emm lock create <project-dir> <lock-type> <version> --actor <name> <artifacts...>`
  - `emm lock verify <project-dir> <lock-file>`
- All successful commands print JSON to stdout and exit `0`.
- Validation failures print `WorkflowError.as_dict()` to stderr and exit `2`.

- [ ] **Step 1: Write the failing version-command test**

```python
import json
import subprocess
import sys


def test_cli_version_returns_machine_readable_version() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "econ_management_meta.cli", "version"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout) == {"version": "0.1.0"}
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/test_cli.py::test_cli_version_returns_machine_readable_version -v`

Expected: module-not-found failure.

- [ ] **Step 3: Implement `version`, `validate-profile`, and error handling**

The CLI must derive the schema directory from the repository/package root by default and accept `--schema-dir` as an override for tests and installed deployments.

- [ ] **Step 4: Run version test and verify GREEN**

Run: `uv run pytest tests/test_cli.py::test_cli_version_returns_machine_readable_version -v`

Expected: pass.

- [ ] **Step 5: Add failing tests for all remaining commands**

Each test asserts JSON output, exit code, and filesystem side effects. At least one test must verify exit `2` and code `PREREQUISITE_NOT_LOCKED`.

- [ ] **Step 6: Implement remaining command routing**

Use `argparse`; do not introduce a CLI framework in v0.1.0.

- [ ] **Step 7: Run CLI tests**

Run: `uv run pytest tests/test_cli.py -v`

Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add src/econ_management_meta/cli.py tests/test_cli.py
git commit -m "feat: expose callable workflow CLI"
```

---

### Task 8: Root Orchestrator, Stage Skills, and Adapters

**Files:**
- Create: `SKILL.md`
- Create: `skills/econ-management-meta/SKILL.md`
- Create: `skills/meta-protocol/SKILL.md`
- Create: `skills/meta-search/SKILL.md`
- Create: `skills/meta-screening/SKILL.md`
- Create: `skills/meta-fulltext/SKILL.md`
- Create: `skills/meta-extraction/SKILL.md`
- Create: `skills/meta-sample-overlap/SKILL.md`
- Create: `skills/meta-construct-alignment/SKILL.md`
- Create: `skills/meta-estimand-alignment/SKILL.md`
- Create: `skills/meta-effect-size/SKILL.md`
- Create: `skills/meta-analysis-r/SKILL.md`
- Create: `skills/meta-bias-robustness/SKILL.md`
- Create: `skills/meta-evidence-confidence/SKILL.md`
- Create: `skills/meta-manuscript/SKILL.md`
- Create: `skills/meta-publication-qa/SKILL.md`
- Create: `adapters/claude-code/INSTALL.md`
- Create: `adapters/codex/INSTALL.md`
- Create: `adapters/generic-agent/manifest.yaml`
- Create: `src/econ_management_meta/skills.py`
- Test: `tests/test_skills.py`

**Interfaces:**
- Produces: `validate_skill_contract(path: Path) -> dict[str, str]`.
- Every `SKILL.md` has YAML frontmatter fields `name`, `description`, `version`, `license`, and `status`.
- The root skill directs agents to use the CLI for validation and locking and explicitly marks statistical execution stages unavailable in v0.1.0.

- [ ] **Step 1: Write the failing root-skill contract test**

```python
from pathlib import Path

from econ_management_meta.skills import validate_skill_contract


def test_root_skill_has_required_frontmatter_and_safety_rules() -> None:
    metadata = validate_skill_contract(Path("SKILL.md"))
    body = Path("SKILL.md").read_text(encoding="utf-8")

    assert metadata["name"] == "econ-management-meta"
    assert metadata["version"] == "0.1.0"
    assert "AI may not make final eligibility decisions" in body
    assert "UNAVAILABLE_IN_VERSION" in body
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/test_skills.py::test_root_skill_has_required_frontmatter_and_safety_rules -v`

Expected: import or file-not-found failure.

- [ ] **Step 3: Implement frontmatter parser and root skill**

The root skill must define this invocation sequence:

```text
1. Run `emm validate-profile`.
2. Run `emm init` for a new project or `emm validate-project` for an existing project.
3. Inspect `state/pipeline-state.yaml`.
4. Invoke only the stage skill corresponding to the current unlocked stage.
5. Require human verification before `VERIFIED` and lock creation.
6. Stop with `UNAVAILABLE_IN_VERSION` for statistical, search, screening, extraction, or manuscript execution not implemented in v0.1.0.
```

- [ ] **Step 4: Run and verify root skill GREEN**

Run: `uv run pytest tests/test_skills.py::test_root_skill_has_required_frontmatter_and_safety_rules -v`

Expected: pass.

- [ ] **Step 5: Add all stage skills and adapter contract tests**

Every stage skill must state:

- accepted inputs;
- required human decisions;
- artifacts it may create;
- artifacts it may not overwrite;
- blocking error conditions;
- v0.1.0 availability status.

The adapter test must verify all three adapters point to the same root skill and do not redefine weaker safety rules.

- [ ] **Step 6: Run complete skill tests**

Run: `uv run pytest tests/test_skills.py -v`

Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add SKILL.md skills adapters src/econ_management_meta/skills.py tests/test_skills.py
git commit -m "feat: add callable skill and platform adapters"
```

---

### Task 9: Golden Project Integration and QA

**Files:**
- Modify: `tests/conftest.py`
- Create: `tests/test_golden_project.py`
- Create: `examples/golden-project/README.md`
- Create: `examples/golden-project/fixtures/protocol-v1.0.yaml`
- Create: `examples/golden-project/fixtures/unsafe-profile.yaml`

**Interfaces:**
- Produces a complete v0.1.0 smoke path: validate profile → initialize project → lock intake → start protocol → create protocol lock → verify lock → validate project.
- The planted unsafe profile must fail with `PROFILE_WEAKENS_CORE`.
- A modified protocol after locking must fail with `LOCK_STALE`.

- [ ] **Step 1: Write the failing golden-path test**

```python
def test_golden_project_completes_callable_core_flow(tmp_path: Path) -> None:
    project = initialize_project(
        "AI and innovation",
        Path("profiles/ai-innovation"),
        tmp_path / "project",
        Path("schemas"),
    )
    transition_stage(project, Stage.INTAKE, StageStatus.IN_PROGRESS, "r1", "start")
    transition_stage(project, Stage.INTAKE, StageStatus.READY_FOR_REVIEW, "r1", "ready")
    transition_stage(project, Stage.INTAKE, StageStatus.VERIFIED, "r2", "verified")
    transition_stage(project, Stage.INTAKE, StageStatus.LOCKED, "r2", "locked")
    transition_stage(project, Stage.PROTOCOL, StageStatus.IN_PROGRESS, "r1", "start protocol")

    protocol = project / "01_protocol/protocol-v1.0.yaml"
    protocol.write_text("version: '1.0'\n", encoding="utf-8")
    lock_path = create_lock(project, "protocol", "1.0", [protocol], "r2")

    assert verify_lock(project, lock_path)["valid"] is True
    assert validate_project(project, Path("schemas"))["valid"] is True
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/test_golden_project.py -v`

Expected: fail on the first incomplete integration point.

- [ ] **Step 3: Fix only integration defects exposed by the test**

Do not add new workflow features. Align path handling, fixtures, schema references, and serialization until the test passes.

- [ ] **Step 4: Add planted-error tests and verify detection**

Add one test for the unsafe profile and one for stale protocol lock. Both must assert the stable error code.

- [ ] **Step 5: Run the complete test suite**

Run: `uv run pytest -v`

Expected: all tests pass with no warnings.

- [ ] **Step 6: Commit**

```bash
git add tests/conftest.py tests/test_golden_project.py examples/golden-project
git commit -m "test: add golden callable-core workflow"
```

---

### Task 10: Documentation, Licensing, CI, and Release Metadata

**Files:**
- Create: `README.md`
- Create: `README.zh-CN.md`
- Create: `LICENSE`
- Create: `NOTICE`
- Create: `CITATION.cff`
- Create: `CHANGELOG.md`
- Create: `.gitignore`
- Create: `.github/workflows/ci.yml`
- Modify: `docs/superpowers/specs/2026-08-03-econ-management-meta-skill-design.md` only to add a link to this plan; do not alter approved requirements.
- Test: `tests/test_repository_metadata.py`

**Interfaces:**
- README quick start uses only commands implemented by Task 7.
- Documentation clearly labels v0.1.0 as architecture/schema prototype, not publication-grade completion.
- CI runs `uv sync --dev` and `uv run pytest -v` on Python 3.11, 3.12, and 3.13.

- [ ] **Step 1: Write failing metadata tests**

```python
from pathlib import Path


def test_readmes_do_not_claim_unimplemented_publication_pipeline() -> None:
    english = Path("README.md").read_text(encoding="utf-8")
    chinese = Path("README.zh-CN.md").read_text(encoding="utf-8")

    assert "architecture and schema prototype" in english
    assert "架构与Schema原型" in chinese
    assert "publication-grade workflow is not yet implemented" in english


def test_license_and_citation_metadata_exist() -> None:
    assert "Apache License" in Path("LICENSE").read_text(encoding="utf-8")
    assert "version: 0.1.0" in Path("CITATION.cff").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run and verify RED**

Run: `uv run pytest tests/test_repository_metadata.py -v`

Expected: file-not-found failures.

- [ ] **Step 3: Add exact quick-start commands and limitations**

English and Chinese READMEs must show:

```bash
uv sync --dev
uv run emm validate-profile profiles/ai-innovation
uv run emm init "AI and innovation" --profile profiles/ai-innovation --output demo-project
uv run emm validate-project demo-project
```

They must state that R synthesis, screening automation, extraction, publication-bias modeling, and Quarto submission output are future phases.

- [ ] **Step 4: Run metadata tests and full suite**

Run: `uv run pytest tests/test_repository_metadata.py -v`

Then: `uv run pytest -v`

Expected: all tests pass.

- [ ] **Step 5: Run package and CLI verification**

Run:

```bash
uv sync --dev
uv run emm version
uv run emm validate-profile profiles/ai-innovation
rm -rf /tmp/emm-v010-smoke
uv run emm init "AI and innovation" --profile profiles/ai-innovation --output /tmp/emm-v010-smoke
uv run emm validate-project /tmp/emm-v010-smoke
```

Expected: every command exits `0` and returns valid JSON.

- [ ] **Step 6: Commit**

```bash
git add README.md README.zh-CN.md LICENSE NOTICE CITATION.cff CHANGELOG.md .gitignore .github tests/test_repository_metadata.py docs/superpowers/specs/2026-08-03-econ-management-meta-skill-design.md
git commit -m "docs: prepare callable core v0.1.0"
```

---

## Self-Review Checklist

- [ ] Every v0.1.0 requirement maps to a task and test.
- [ ] No task implements formal R statistics, Quarto rendering, autonomous screening, extraction, or causal interpretation.
- [ ] All production Python behavior has a failing test before implementation.
- [ ] Profile policy prevents every weakening key named in the approved specification.
- [ ] Stage locking and prerequisite checks are fail-closed.
- [ ] Locks detect changed artifacts and return a stable error code.
- [ ] Skill and adapters expose the same safety boundaries.
- [ ] English and Chinese documentation make no publication-grade completion claim.
- [ ] The complete suite and smoke commands pass in a clean environment.

## Follow-On Plans

After v0.1.0 is reviewed, create separate implementation plans for:

1. protocol, amendments, and search provenance;
2. screening, report-family reconciliation, and dual extraction;
3. construct/estimand gates and effect-size R engine;
4. dependency-aware synthesis, heterogeneity, and missing-evidence analysis;
5. evidence appraisal, Quarto reporting, claim audit, and clean-room release.
