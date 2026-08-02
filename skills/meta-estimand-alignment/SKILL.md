---
name: meta-estimand-alignment
description: Assign results to estimand-first evidence lanes.
version: 0.2.0
license: Apache-2.0
status: experimental
---

# meta-estimand-alignment

## Accepted inputs

verified design, contrast, adjustment set, unit, time horizon, functional form.

## Human-only decisions

Estimand family, causal status, evidence lane, and pooling compatibility. AI suggestions must remain unverified until a named human confirms them.

## Permitted artifacts

Create new, versioned files inside the corresponding project stage and append decision history. Do not overwrite locked artifacts, earlier protocol versions, source exports, or human reviewer records.

## Blocking conditions

Stop on missing provenance, invalid profile or project schema, unresolved reviewer conflict, an unlocked prerequisite stage, a stale integrity lock, or any attempt to weaken core gates.

## v0.2.0 availability

Estimand adjudication is UNAVAILABLE_IN_VERSION.
