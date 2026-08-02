---
name: econ-management-meta
description: Orchestrate a fail-closed economics and management meta-analysis project using verified file artifacts.
version: 0.2.0
license: Apache-2.0
status: experimental
---

# Econ–Management Meta Skill

Use this skill to initialize, validate, and govern a file-first meta-analysis project. Version 0.2.0 executes protocol versioning, bibliographic import and deduplication, human screening consensus, report-family mapping, and dual extraction.

## Mandatory invocation sequence

1. Validate the selected profile with `emm validate-profile PROFILE_DIR`.
2. Create a project with `emm init TOPIC --profile PROFILE_DIR --output PROJECT_DIR`, or validate an existing project with `emm validate-project PROJECT_DIR`.
3. Read `PROJECT_DIR/state/pipeline-state.yaml` and identify the current unlocked stage.
4. Use only the matching stage skill under `skills/`.
5. Record human review before moving a stage to `VERIFIED`, and create an immutable lock before starting the next stage.
6. Verify every relevant lock before relying on downstream artifacts.

## Non-negotiable human authority

AI may not make final eligibility decisions, finalize construct mappings, approve estimand assignments, verify effect sizes, select the primary statistical model, or approve causal claims. AI-generated suggestions remain `AI_SUGGESTED` or `UNVERIFIED` until a named human reviewer confirms them.

## Fail-closed behavior

Stop on invalid profiles, missing mandatory artifacts, illegal state transitions, unlocked prerequisites, stale locks, or conflicting identifiers. Return the stable error code supplied by the CLI. Never replace a blocking error with a warning and continue.

## Version boundary

Structured protocol creation/amendment, search-run registration, CSV/RIS/BibTeX/EndNote XML import, deterministic report deduplication, human screening decisions, report-family reconciliation, and dual extraction are available. Live database querying, active-learning prioritization, PDF extraction, construct/estimand adjudication, effect-size computation, R synthesis, publication-bias modeling, Quarto rendering, and submission-package generation must stop with `UNAVAILABLE_IN_VERSION`.

## Core commands

```bash
emm version
emm validate-profile profiles/ai-innovation
emm init "AI and innovation" --profile profiles/ai-innovation --output review-project
emm validate-project review-project
emm transition review-project 00_intake IN_PROGRESS --actor researcher-1 --note "start feasibility scan"
emm lock review-project protocol 1.0 review-project/01_protocol/protocol-v1.0.yaml --actor researcher-2
emm verify-lock review-project review-project/locks/protocol-v1.0.lock.yaml
```
