---
name: meta-effect-size
description: Convert verified source statistics into traceable effect sizes.
version: 0.2.0
license: Apache-2.0
status: experimental
---

# meta-effect-size

## Accepted inputs

verified statistics, construct decision, estimand decision, conversion registry.

## Human-only decisions

Source-statistic approval, conversion rule, approximation status, and effect-pool lock. AI suggestions must remain unverified until a named human confirms them.

## Permitted artifacts

Create new, versioned files inside the corresponding project stage and append decision history. Do not overwrite locked artifacts, earlier protocol versions, source exports, or human reviewer records.

## Blocking conditions

Stop on missing provenance, invalid profile or project schema, unresolved reviewer conflict, an unlocked prerequisite stage, a stale integrity lock, or any attempt to weaken core gates.

## v0.2.0 availability

Effect-size computation and verification are UNAVAILABLE_IN_VERSION.
