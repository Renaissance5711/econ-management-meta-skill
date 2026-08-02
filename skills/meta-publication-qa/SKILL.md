---
name: meta-publication-qa
description: Run fail-closed cross-artifact checks before release.
version: 0.1.0
license: Apache-2.0
status: experimental
---

# meta-publication-qa

## Accepted inputs

all locks, manifests, results, figures, manuscript, environment metadata.

## Human-only decisions

Resolution of P0/P1 findings and release approval. AI suggestions must remain unverified until a named human confirms them.

## Permitted artifacts

Create new, versioned files inside the corresponding project stage and append decision history. Do not overwrite locked artifacts, earlier protocol versions, source exports, or human reviewer records.

## Blocking conditions

Stop on missing provenance, invalid profile or project schema, unresolved reviewer conflict, an unlocked prerequisite stage, a stale integrity lock, or any attempt to weaken core gates.

## v0.1.0 availability

Full publication QA and clean-room reproduction are UNAVAILABLE_IN_VERSION.
