# Protocol, Search, Screening, and Extraction v0.2.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Upgrade the callable core so a review team can create and amend a locked protocol, import and deduplicate bibliographic records with provenance, record independent screening decisions, reconcile report families, and complete dual extraction with human-verified resolutions.

**Architecture:** The new modules remain file-first and append-oriented. Each service validates structured records before writing CSV/YAML/JSON artifacts inside the canonical project stages. Stable IDs, named human actors, timestamps, provenance, and non-overwrite semantics are enforced by shared helpers; the CLI exposes the same contracts to Claude Code, Codex, and generic agents.

**Tech Stack:** Python 3.11+, standard library (`csv`, `xml.etree.ElementTree`, `re`, `hashlib`, `uuid`), PyYAML, jsonschema, pytest, JSON Schema Draft 2020-12.

## Global Constraints

- Preserve Apache-2.0 licensing and English-as-normative documentation.
- Never overwrite a locked or versioned research artifact.
- AI may suggest content but may not be recorded as a final reviewer, extractor, consensus resolver, or protocol approver.
- Full-text final eligibility requires two distinct named human reviewers or an explicit named human adjudicator after a conflict.
- Dual extraction requires two distinct named human extractors before a resolved value can become `VERIFIED`.
- Every imported record retains source database, platform, search date, query ID, export batch, source file, and source-row provenance.
- Deduplication merges reports, not studies; it must retain every source record ID and must not silently discard conflicting metadata.
- Protocol amendments record whether study-level or pooled outcome information had been seen when the change was approved.
- Every validation failure exits fail-closed with a stable `WorkflowError` code.
- Formal active learning, PDF extraction, subscription-database access, construct/estimand adjudication, effect-size computation, R synthesis, and Quarto output remain unavailable in v0.2.0.

---

## File Map

### Production modules

- `src/econ_management_meta/protocol.py`: protocol creation, validation, versioning, amendments, and protocol lock preparation.
- `src/econ_management_meta/search.py`: search-run registry, CSV/RIS/BibTeX/EndNote XML import, record normalization, provenance, and deterministic deduplication.
- `src/econ_management_meta/screening.py`: independent title/abstract and full-text decisions, agreement summaries, conflict resolution, and consensus exports.
- `src/econ_management_meta/reports.py`: report-family assignments and human-verified report-to-study reconciliation.
- `src/econ_management_meta/extraction.py`: dual extraction entries, conflicts, resolutions, verification status, and verified export.
- `src/econ_management_meta/tabular.py`: append-only CSV helpers, exact headers, stable row IDs, and duplicate-key protection.
- `src/econ_management_meta/cli.py`: new protocol, search, screening, report-family, and extraction commands.
- `src/econ_management_meta/errors.py`: additional stable error codes.

### Schemas and templates

- `schemas/protocol.schema.json`
- `schemas/protocol-amendment.schema.json`
- `schemas/search-run.schema.json`
- `schemas/bibliographic-record.schema.json`
- `schemas/screening-decision.schema.json`
- `schemas/report-family.schema.json`
- `schemas/extraction-entry.schema.json`
- `templates/protocol/default.yaml`
- `templates/screening/exclusion-codes.yaml`
- `profiles/ai-innovation/search/concept-blocks.yaml`
- `profiles/ai-innovation/eligibility/boundary-cases.yaml`
- `profiles/ai-innovation/coding/extraction-fields.yaml`

### Tests

- `tests/test_protocol.py`
- `tests/test_search.py`
- `tests/test_screening.py`
- `tests/test_reports.py`
- `tests/test_extraction.py`
- `tests/test_cli_v020.py`
- `tests/test_v020_golden_flow.py`
- update existing skill, project-tree, metadata, and CLI tests.

---

### Task 1: Shared Append-Only Tabular Infrastructure and Error Codes

**Files:**
- Create: `src/econ_management_meta/tabular.py`
- Modify: `src/econ_management_meta/errors.py`
- Test: `tests/test_tabular.py`

**Interfaces:**
- `ensure_csv(path: Path, headers: Sequence[str]) -> None`
- `append_unique_row(path: Path, headers: Sequence[str], row: Mapping[str, object], unique_fields: Sequence[str]) -> None`
- `read_csv_rows(path: Path) -> list[dict[str, str]]`
- `stable_id(prefix: str, *parts: object) -> str`
- New error codes: `ARTIFACT_ALREADY_EXISTS`, `DUPLICATE_DECISION`, `HUMAN_ACTOR_REQUIRED`, `PROTOCOL_INVALID`, `AMENDMENT_INVALID`, `SEARCH_IMPORT_INVALID`, `SCREENING_CONFLICT`, `SCREENING_INVALID`, `REPORT_FAMILY_INVALID`, `EXTRACTION_CONFLICT`, `EXTRACTION_INVALID`.

- [x] Write failing tests that assert headers are created once, duplicate composite keys are blocked, and stable IDs are deterministic.
- [x] Run `PYTHONPATH=src python3 -m pytest tests/test_tabular.py -v` and verify RED.
- [x] Implement only the tested behavior using atomic temporary-file replacement for rewritten CSVs and direct append for unique rows.
- [x] Run the test and verify GREEN.
- [x] Commit with `feat: add append-only tabular infrastructure`.

### Task 2: Versioned Protocol and Amendment Engine

**Files:**
- Create: `schemas/protocol.schema.json`
- Create: `schemas/protocol-amendment.schema.json`
- Create: `src/econ_management_meta/protocol.py`
- Create: `templates/protocol/default.yaml`
- Test: `tests/test_protocol.py`

**Interfaces:**
- `create_protocol(project_dir: Path, version: str, protocol: Mapping[str, object], actor: str, schema_dir: Path) -> Path`
- `validate_protocol(path: Path, schema_dir: Path) -> dict[str, object]`
- `create_amendment(project_dir: Path, amendment: Mapping[str, object], actor: str, schema_dir: Path) -> Path`
- `list_protocol_versions(project_dir: Path) -> list[str]`
- Protocol schema requires question, unit of inference, eligibility, evidence lanes, search plan, screening plan, extraction plan, AI role declaration, and analysis categories.
- Amendment schema requires old/new rule, rationale, change class, affected artifacts, whether study-level or pooled results were seen, and post-change confirmatory status.

- [x] Write failing tests for creating `protocol-v1.0.yaml`, refusing overwrite, rejecting an AI final-decision declaration, and recording a prospective amendment.
- [x] Verify RED.
- [x] Implement schema validation, named-human checks, immutable filenames, and an amendment index.
- [x] Verify GREEN and commit `feat: add versioned protocol and amendment engine`.

### Task 3: Search Registry, Multi-Format Import, and Provenance-Preserving Deduplication

**Files:**
- Create: `schemas/search-run.schema.json`
- Create: `schemas/bibliographic-record.schema.json`
- Create: `src/econ_management_meta/search.py`
- Create: `profiles/ai-innovation/search/concept-blocks.yaml`
- Create: `tests/fixtures/search/sample.csv`
- Create: `tests/fixtures/search/sample.ris`
- Create: `tests/fixtures/search/sample.bib`
- Create: `tests/fixtures/search/sample.xml`
- Test: `tests/test_search.py`

**Interfaces:**
- `register_search_run(project_dir: Path, run: Mapping[str, object], actor: str, schema_dir: Path) -> str`
- `import_search_file(project_dir: Path, search_run_id: str, source_path: Path, source_format: str, actor: str, schema_dir: Path) -> dict[str, int]`
- `deduplicate_records(project_dir: Path, actor: str) -> dict[str, int]`
- Canonical fields include `record_id`, `title`, `authors`, `year`, `doi`, `abstract`, `journal`, `source_record_id`, `search_run_id`, and `verification_status`.
- Deduplication priority: normalized DOI; then normalized exact title + year; otherwise remain distinct. Merged rows retain all source record IDs and provenance links.

- [x] Write failing tests for all four import formats and DOI/title normalization.
- [x] Verify RED.
- [x] Implement parsers with clear unsupported/invalid-format errors.
- [x] Add failing tests for cross-source duplicates and conflicting years.
- [x] Implement deterministic deduplication that retains provenance and emits `deduplication-decisions.csv`.
- [x] Verify GREEN and commit `feat: import and deduplicate search records`.

### Task 4: Human Screening Decisions and Consensus

**Files:**
- Create: `schemas/screening-decision.schema.json`
- Create: `src/econ_management_meta/screening.py`
- Create: `templates/screening/exclusion-codes.yaml`
- Create: `profiles/ai-innovation/eligibility/boundary-cases.yaml`
- Test: `tests/test_screening.py`

**Interfaces:**
- `record_screening_decision(project_dir: Path, stage: str, record_id: str, reviewer: str, decision: str, reason_code: str | None, source_page: str | None, note: str | None, schema_dir: Path) -> str`
- `screening_agreement(project_dir: Path, stage: str) -> dict[str, object]`
- `resolve_screening_conflict(project_dir: Path, stage: str, record_id: str, adjudicator: str, final_decision: str, reason_code: str | None, source_page: str | None, rationale: str) -> str`
- `export_screening_consensus(project_dir: Path, stage: str) -> Path`
- Decisions are `INCLUDE`, `EXCLUDE`, or `UNCERTAIN`; full-text exclusion requires reason and page evidence.

- [x] Write failing tests for two independent decisions, duplicate reviewer rejection, disagreement detection, and full-text evidence requirements.
- [x] Verify RED.
- [x] Implement append-only reviewer decisions and agreement statistics (raw, include, exclude, conflict count, Cohen’s kappa when defined).
- [x] Write failing tests for consensus without conflict and human adjudication after conflict.
- [x] Implement consensus export and verify GREEN.
- [x] Commit `feat: add human screening and consensus workflow`.

### Task 5: Report-Family and Study-Family Reconciliation

**Files:**
- Create: `schemas/report-family.schema.json`
- Create: `src/econ_management_meta/reports.py`
- Test: `tests/test_reports.py`

**Interfaces:**
- `assign_report_family(project_dir: Path, report_id: str, report_family_id: str, study_id: str, version_role: str, actor: str, evidence: str, schema_dir: Path) -> str`
- `validate_report_families(project_dir: Path) -> dict[str, object]`
- `export_report_family_map(project_dir: Path) -> Path`
- Version roles: `WORKING_PAPER`, `CONFERENCE`, `DISSERTATION`, `ACCEPTED_MANUSCRIPT`, `JOURNAL_ARTICLE`, `OTHER`.

- [x] Write failing tests for valid assignments, duplicate report assignment, missing evidence, and one report assigned to two studies.
- [x] Verify RED.
- [x] Implement human-verified assignments and conflict detection.
- [x] Verify GREEN and commit `feat: reconcile reports and studies`.

### Task 6: Dual Extraction and Human-Verified Resolution

**Files:**
- Create: `schemas/extraction-entry.schema.json`
- Create: `src/econ_management_meta/extraction.py`
- Create: `profiles/ai-innovation/coding/extraction-fields.yaml`
- Test: `tests/test_extraction.py`

**Interfaces:**
- `record_extraction(project_dir: Path, report_id: str, study_id: str, field_id: str, extractor: str, value: object, source_page: str, source_quote: str, schema_dir: Path) -> str`
- `list_extraction_conflicts(project_dir: Path) -> list[dict[str, object]]`
- `resolve_extraction(project_dir: Path, report_id: str, study_id: str, field_id: str, resolver: str, resolved_value: object, rationale: str) -> str`
- `export_verified_extraction(project_dir: Path) -> Path`
- One extractor may not submit twice for the same key; verified export requires two distinct extractors plus a named human resolution when values differ.

- [x] Write failing tests for two matching extracts, conflicting extracts, missing source provenance, and duplicate extractor rejection.
- [x] Verify RED.
- [x] Implement append-only extraction JSONL/CSV artifacts and conflict calculation.
- [x] Add failing tests for resolution and verified-only export.
- [x] Implement human resolution and verify GREEN.
- [x] Commit `feat: add dual extraction and verified export`.

### Task 7: CLI and Agent Skill Availability

**Files:**
- Modify: `src/econ_management_meta/cli.py`
- Modify: `SKILL.md`
- Modify: `skills/meta-protocol/SKILL.md`
- Modify: `skills/meta-search/SKILL.md`
- Modify: `skills/meta-screening/SKILL.md`
- Modify: `skills/meta-fulltext/SKILL.md`
- Modify: `skills/meta-extraction/SKILL.md`
- Test: `tests/test_cli_v020.py`
- Modify: `tests/test_skills.py`

**Interfaces:**
- Add CLI command groups: `protocol`, `search`, `screen`, `report-family`, and `extract`.
- Every command emits JSON and returns `0`, `2` for expected workflow errors, or `1` for unexpected internal errors.
- Stage skills mark the implemented actions `AVAILABLE_IN_VERSION` and retain explicit human-only decisions.

- [x] Write failing CLI tests for one happy path and one fail-closed path per command group.
- [x] Verify RED.
- [x] Add argparse routing without adding a CLI framework.
- [x] Update skill contracts and tests.
- [x] Verify GREEN and commit `feat: expose protocol search screening and extraction CLI`.

### Task 8: v0.2.0 Golden Flow, Documentation, and Release Verification

**Files:**
- Create: `tests/test_v020_golden_flow.py`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `CHANGELOG.md`
- Modify: `CITATION.cff`
- Modify: `src/econ_management_meta/__init__.py`
- Modify: `pyproject.toml`
- Modify: `.github/workflows/ci.yml` only when necessary.
- Modify: `docs/superpowers/specs/2026-08-03-econ-management-meta-skill-design.md` to link this plan.

**Interfaces:**
- Golden flow: initialize → protocol create/amend/lock → search register/import/deduplicate → two-reviewer title/abstract consensus → full-text consensus → report-family map → dual extraction → verified export → project validation.
- Version becomes `0.2.0` only after the complete flow passes.

- [x] Write the failing end-to-end test and planted-error variants.
- [x] Verify RED.
- [x] Fix only integration defects and documentation/version metadata.
- [x] Run `PYTHONPATH=src python3 -m pytest -v` and require zero failures and zero warnings.
- [x] Run CLI smoke commands in a fresh temporary project.
- [x] Inspect `git diff --check`, `git status --short`, and the implementation-plan checklist.
- [x] Commit `release: prepare executable workflow v0.2.0`.

---

## Self-Review Checklist

- [x] Protocol and amendment files are immutable and schema validated.
- [x] Search imports support CSV, RIS, BibTeX, and EndNote XML fixtures.
- [x] Deduplication retains all source provenance and does not infer study identity.
- [x] Full-text consensus cannot be produced from one reviewer or AI identity.
- [x] Report-family mappings require named-human evidence.
- [x] Verified extraction requires two distinct extractors and conflict resolution when needed.
- [x] All new CLI commands emit machine-readable JSON and stable error codes.
- [x] Updated stage skills accurately distinguish available from unavailable functions.
- [x] Existing v0.1.0 tests remain green.
- [x] README language does not claim that statistical synthesis or manuscript generation is complete.
