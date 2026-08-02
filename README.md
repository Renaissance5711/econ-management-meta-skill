# Econ–Management Meta Skill

`econ-management-meta-skill` is a fail-closed, file-first workflow for systematic reviews and meta-analyses in economics, management, innovation, entrepreneurship, marketing, and information systems.

## Version status

Version **0.2.0** is an executable evidence-acquisition and coding workflow. It provides:

- a callable root `SKILL.md` and bounded stage skills;
- schema-governed domain profiles;
- deterministic project initialization and pipeline state;
- immutable protocol versions and classified amendments;
- search-run provenance and CSV, RIS, BibTeX, and EndNote XML import;
- deterministic report-level deduplication that retains all source provenance;
- independent human screening, agreement summaries, adjudication, and consensus exports;
- human-verified report-family and study-family mappings;
- dual extraction, conflict detection, adjudication, and verified-only exports;
- versioned SHA-256 integrity locks;
- Claude Code, Codex, and generic-agent adapters.

The publication-grade workflow is not yet implemented. Live database querying, active-learning screening, PDF extraction, construct and estimand adjudication, effect-size computation, R synthesis, missing-evidence models, Quarto manuscript generation, and clean-room release reproduction remain future phases.

## Quick start

```bash
uv sync --dev
uv run emm validate-profile profiles/ai-innovation
uv run emm init "AI and innovation" --profile profiles/ai-innovation --output demo-project
uv run emm validate-project demo-project
```

Create a structured protocol:

```bash
uv run emm protocol create demo-project 1.0 protocol.yaml --actor principal-investigator
uv run emm protocol validate demo-project/01_protocol/protocol-v1.0.yaml
```

Register and import a search export:

```bash
uv run emm search register demo-project search-run.yaml --actor information-specialist
uv run emm search import demo-project SEARCH_RUN_ID export.ris --format ris --actor information-specialist
uv run emm search deduplicate demo-project --actor review-lead
```

Use `emm screen`, `emm report-family`, and `emm extract` for independent human screening, report-family reconciliation, and dual extraction. Run `uv run emm --help` for exact subcommands.

## Agent invocation

Load the repository root [`SKILL.md`](SKILL.md). The root skill validates the profile and project, reads the pipeline state, and delegates only to the matching stage skill. It must stop with `UNAVAILABLE_IN_VERSION` for functions not implemented in v0.2.0.

## Safety boundaries

AI may suggest records, fields, mappings, or code, but may not be recorded as a final reviewer, adjudicator, extractor, protocol approver, effect verifier, model selector, or causal-claim approver. Profiles may strengthen but cannot weaken the core gates.

## Development

```bash
uv sync --dev
uv run pytest -v
```

The approved design specification and implementation plans are in `docs/superpowers/`.

## License

Apache License 2.0. See `LICENSE` and `NOTICE`.
