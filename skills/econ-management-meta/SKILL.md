---
name: econ-management-meta
description: Coordinate the complete governed workflow.
version: 0.1.0
license: Apache-2.0
status: experimental
---

# econ-management-meta

## Accepted inputs

project manifest, profile manifest, pipeline state, lock files.

## Human-only decisions

Human approval of every consequential research decision. AI suggestions must remain unverified until a named human confirms them.

## Permitted artifacts

Create new, versioned files inside the corresponding project stage and append decision history. Do not overwrite locked artifacts, earlier protocol versions, source exports, or human reviewer records.

## Blocking conditions

Stop on missing provenance, invalid profile or project schema, unresolved reviewer conflict, an unlocked prerequisite stage, a stale integrity lock, or any attempt to weaken core gates.

## v0.1.0 availability

Core orchestration and CLI governance are AVAILABLE; substantive research stages return UNAVAILABLE_IN_VERSION.
