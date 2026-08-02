# Econ–Management Meta Skill

`econ-management-meta-skill` is a fail-closed, file-first architecture and schema prototype for systematic reviews and meta-analyses in economics, management, innovation, entrepreneurship, marketing, and information systems.

## Version status

Version **0.1.0** is an architecture and schema prototype. It provides:

- a callable root `SKILL.md` and bounded stage skills;
- schema-governed domain profiles;
- deterministic project initialization;
- fail-closed stage transitions;
- versioned SHA-256 integrity locks;
- Claude Code, Codex, and generic-agent adapters;
- an initial `ai-innovation` profile.

The publication-grade workflow is not yet implemented. Search execution, screening automation, extraction, construct and estimand adjudication, R synthesis, missing-evidence models, Quarto manuscript generation, and clean-room release reproduction remain future phases.

## Quick start

```bash
uv sync --dev
uv run emm validate-profile profiles/ai-innovation
uv run emm init "AI and innovation" --profile profiles/ai-innovation --output demo-project
uv run emm validate-project demo-project
```

In an offline environment that already contains the dependencies, select an installed interpreter and skip dependency synchronization:

```bash
UV_PYTHON=3.13 uv run --no-sync emm version
```

## Agent invocation

Load the repository root [`SKILL.md`](SKILL.md). The root skill validates the selected profile, initializes or validates a project, reads the pipeline state, and delegates to a bounded stage skill. It must stop with `UNAVAILABLE_IN_VERSION` when a requested substantive stage is not implemented in v0.1.0.

## Safety boundaries

AI may suggest records, fields, mappings, or code, but may not make final eligibility decisions, approve construct or estimand assignments, verify effect sizes, select the primary model, or approve causal claims. Profiles may strengthen but cannot weaken the core gates.

## Development

```bash
uv sync --dev
uv run pytest -v
```

The approved design specification is in `docs/superpowers/specs/`. The v0.1.0 implementation plan is in `docs/superpowers/plans/`.

## License

Apache License 2.0. See `LICENSE` and `NOTICE`.
