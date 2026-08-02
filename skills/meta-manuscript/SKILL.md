---
name: meta-manuscript
description: Generate journal-ready outputs from locked statistical result objects.
version: 0.1.0
license: Apache-2.0
status: experimental
---

# meta-manuscript

## Accepted inputs

verified R results, claim registry, reporting profile, protocol deviations.

## Human-only decisions

Interpretive claims, causal language, journal selection, and final manuscript approval. AI suggestions must remain unverified until a named human confirms them.

## Permitted artifacts

Create new, versioned files inside the corresponding project stage and append decision history. Do not overwrite locked artifacts, earlier protocol versions, source exports, or human reviewer records.

## Blocking conditions

Stop on missing provenance, invalid profile or project schema, unresolved reviewer conflict, an unlocked prerequisite stage, a stale integrity lock, or any attempt to weaken core gates.

## v0.1.0 availability

Quarto manuscript and supplement generation are UNAVAILABLE_IN_VERSION.
