---
name: meta-fulltext
description: Reconcile reports, studies, and full-text eligibility decisions.
version: 0.2.0
license: Apache-2.0
status: experimental
---

# meta-fulltext

## Accepted inputs

screened records, full texts, report-family candidates, reviewer decisions.

## Human-only decisions

Full-text eligibility, exclusion reason, report-family membership, and inaccessible-report disposition. AI suggestions must remain unverified until a named human confirms them.

## Permitted artifacts

Create new, versioned files inside the corresponding project stage and append decision history. Do not overwrite locked artifacts, earlier protocol versions, source exports, or human reviewer records.

## Blocking conditions

Stop on missing provenance, invalid profile or project schema, unresolved reviewer conflict, an unlocked prerequisite stage, a stale integrity lock, or any attempt to weaken core gates.

## v0.2.0 availability

Human-verified report-family and study-family assignments are AVAILABLE_IN_VERSION. PDF acquisition, text extraction, and automated family matching remain UNAVAILABLE_IN_VERSION.
