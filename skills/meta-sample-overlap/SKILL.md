---
name: meta-sample-overlap
description: Represent article, study, sample, and dataset-family dependencies.
version: 0.2.0
license: Apache-2.0
status: experimental
---

# meta-sample-overlap

## Accepted inputs

verified extraction records, sample descriptions, periods, geographies, datasets.

## Human-only decisions

Dataset-family assignment and overlap handling strategy. AI suggestions must remain unverified until a named human confirms them.

## Permitted artifacts

Create new, versioned files inside the corresponding project stage and append decision history. Do not overwrite locked artifacts, earlier protocol versions, source exports, or human reviewer records.

## Blocking conditions

Stop on missing provenance, invalid profile or project schema, unresolved reviewer conflict, an unlocked prerequisite stage, a stale integrity lock, or any attempt to weaken core gates.

## v0.2.0 availability

Overlap detection and dependency routing are UNAVAILABLE_IN_VERSION.
