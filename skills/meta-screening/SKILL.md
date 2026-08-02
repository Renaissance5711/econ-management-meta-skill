---
name: meta-screening
description: Govern human screening and active-learning prioritization.
version: 0.1.0
license: Apache-2.0
status: experimental
---

# meta-screening

## Accepted inputs

locked protocol, deduplicated records, reviewer identities, exclusion codes.

## Human-only decisions

Every final include/exclude decision and every accelerated-stopping approval. AI suggestions must remain unverified until a named human confirms them.

## Permitted artifacts

Create new, versioned files inside the corresponding project stage and append decision history. Do not overwrite locked artifacts, earlier protocol versions, source exports, or human reviewer records.

## Blocking conditions

Stop on missing provenance, invalid profile or project schema, unresolved reviewer conflict, an unlocked prerequisite stage, a stale integrity lock, or any attempt to weaken core gates.

## v0.1.0 availability

Screening execution and active learning are UNAVAILABLE_IN_VERSION.
