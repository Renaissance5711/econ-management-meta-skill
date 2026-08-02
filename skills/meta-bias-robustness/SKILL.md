---
name: meta-bias-robustness
description: Assess heterogeneity, missing evidence, and robustness without mechanical correction claims.
version: 0.1.0
license: Apache-2.0
status: experimental
---

# meta-bias-robustness

## Accepted inputs

model results, search coverage, missing outcomes, risk-of-bias records.

## Human-only decisions

Applicability of diagnostics, missing-evidence judgment, and claim restrictions. AI suggestions must remain unverified until a named human confirms them.

## Permitted artifacts

Create new, versioned files inside the corresponding project stage and append decision history. Do not overwrite locked artifacts, earlier protocol versions, source exports, or human reviewer records.

## Blocking conditions

Stop on missing provenance, invalid profile or project schema, unresolved reviewer conflict, an unlocked prerequisite stage, a stale integrity lock, or any attempt to weaken core gates.

## v0.1.0 availability

Bias, heterogeneity, and sensitivity models are UNAVAILABLE_IN_VERSION.
