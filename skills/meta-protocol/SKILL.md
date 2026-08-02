---
name: meta-protocol
description: Develop and version the review protocol and analysis-registration boundaries.
version: 0.1.0
license: Apache-2.0
status: experimental
---

# meta-protocol

## Accepted inputs

research question, theoretical dispute, profile, eligibility draft, pipeline state.

## Human-only decisions

Final research question, eligibility criteria, evidence lanes, protocol amendments, and lock approval. AI suggestions must remain unverified until a named human confirms them.

## Permitted artifacts

Create new, versioned files inside the corresponding project stage and append decision history. Do not overwrite locked artifacts, earlier protocol versions, source exports, or human reviewer records.

## Blocking conditions

Stop on missing provenance, invalid profile or project schema, unresolved reviewer conflict, an unlocked prerequisite stage, a stale integrity lock, or any attempt to weaken core gates.

## v0.1.0 availability

Protocol artifact authoring is guidance-only; automated protocol production is UNAVAILABLE_IN_VERSION.
