---
name: meta-analysis-r
description: Run dependency-aware statistical synthesis in the locked R environment.
version: 0.1.0
license: Apache-2.0
status: experimental
---

# meta-analysis-r

## Accepted inputs

locked effect pool, analysis-spec lock, covariance strategy, R environment.

## Human-only decisions

Primary model, moderator status, sensitivity grid, and interpretation. AI suggestions must remain unverified until a named human confirms them.

## Permitted artifacts

Create new, versioned files inside the corresponding project stage and append decision history. Do not overwrite locked artifacts, earlier protocol versions, source exports, or human reviewer records.

## Blocking conditions

Stop on missing provenance, invalid profile or project schema, unresolved reviewer conflict, an unlocked prerequisite stage, a stale integrity lock, or any attempt to weaken core gates.

## v0.1.0 availability

R synthesis, CR2 inference, and figures are UNAVAILABLE_IN_VERSION.
