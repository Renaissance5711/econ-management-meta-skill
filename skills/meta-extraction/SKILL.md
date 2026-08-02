---
name: meta-extraction
description: Govern dual extraction with source provenance and conflict resolution.
version: 0.1.0
license: Apache-2.0
status: experimental
---

# meta-extraction

## Accepted inputs

included reports, extraction schema, source pages, reviewer values.

## Human-only decisions

Resolved extraction values, quotations, provenance, and human verification. AI suggestions must remain unverified until a named human confirms them.

## Permitted artifacts

Create new, versioned files inside the corresponding project stage and append decision history. Do not overwrite locked artifacts, earlier protocol versions, source exports, or human reviewer records.

## Blocking conditions

Stop on missing provenance, invalid profile or project schema, unresolved reviewer conflict, an unlocked prerequisite stage, a stale integrity lock, or any attempt to weaken core gates.

## v0.1.0 availability

Automated extraction and reconciliation are UNAVAILABLE_IN_VERSION.
