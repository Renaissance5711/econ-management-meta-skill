---
name: meta-search
description: Design and audit reproducible literature-search provenance.
version: 0.2.0
license: Apache-2.0
status: experimental
---

# meta-search

## Accepted inputs

locked protocol, profile search blocks, database list, imported exports.

## Human-only decisions

Final database selection, query approval, legal credential use, and search-completeness judgment. AI suggestions must remain unverified until a named human confirms them.

## Permitted artifacts

Create new, versioned files inside the corresponding project stage and append decision history. Do not overwrite locked artifacts, earlier protocol versions, source exports, or human reviewer records.

## Blocking conditions

Stop on missing provenance, invalid profile or project schema, unresolved reviewer conflict, an unlocked prerequisite stage, a stale integrity lock, or any attempt to weaken core gates.

## v0.2.0 availability

Search-run registration, CSV/RIS/BibTeX/EndNote XML import, provenance retention, and deterministic report-level deduplication are AVAILABLE_IN_VERSION. Live database execution, API harvesting, and citation chasing remain UNAVAILABLE_IN_VERSION.
