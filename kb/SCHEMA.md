---
type: Schema
title: Bundle Schema & Conventions
description: Authoritative conventions for this OKF bundle — types, tags, frontmatter templates, lifecycle rules.
status: active
updated: 2026-07-05
---

# Bundle Schema & Conventions

This bundle follows **OKF v0.1** plus the lifecycle profile described
here. When this file and habit disagree, this file wins. When this file
and `CLAUDE.md` disagree, this file wins for content conventions;
`CLAUDE.md` wins for process.

# Domain

*(Fill in on first real ingestion: one paragraph on what this knowledge
base is about and who consumes it. The directory layout below may be
renamed to fit the domain — update this file and re-run
`python scripts/okf.py index` if you do.)*

# Directory layout

```
kb/
├── index.md          # generated catalog (okf.py index)
├── log.md            # append-only history (okf.py log)
├── SCHEMA.md         # this file
├── concepts/         # ideas, definitions, explanations
├── entities/         # concrete things: people, orgs, systems, datasets
├── comparisons/      # X-vs-Y analyses
├── queries/          # filed answers from kb-query worth keeping
├── archive/          # archived concepts (status: archived)
└── sources/          # IMMUTABLE raw captures
    └── YYYY-MM-DD-<slug>.md
```

# Concept frontmatter template

```yaml
---
type: Concept            # required (OKF). See type registry below.
title: Human Readable Title
description: One sentence, used in index.md and previews.
status: draft            # draft | active | needs_review | deprecated | archived
confidence: medium       # low | medium | high — how well-sourced the claims are
created: 2026-07-05
updated: 2026-07-05
review_after: 2026-10-05 # required once status: active
tags: [tag-from-taxonomy]
sources:                 # bundle-relative paths into /sources/
  - /sources/2026-07-05-example.md
supersedes: /concepts/old-page.md      # optional
superseded_by: /concepts/new-page.md   # required when status: deprecated
---
```

# Source-capture frontmatter template

Files under `sources/` are verbatim or near-verbatim captures. Immutable
after creation.

```yaml
---
type: Source
title: Original Article Title
description: One sentence on what this source covers.
source_url: https://example.com/article
ingested: 2026-07-05
sha256: <hash of the body below the frontmatter — okf.py drift checks it>
---
```

# Type registry

No central registry is required by OKF, but *this bundle* uses:

| type | lives in | meaning |
|------|----------|---------|
| `Concept` | `concepts/` | An idea, definition, method, or explanation |
| `Entity` | `entities/` | A concrete nameable thing |
| `Comparison` | `comparisons/` | Structured X-vs-Y |
| `Query` | `queries/` | A filed answer to a real question |
| `Source` | `sources/` | Immutable raw capture |
| `Schema` | root | This file only |

Add new types here before first use.

# Tag taxonomy

*(Seed list — extend here BEFORE using a new tag anywhere.)*

- `unverified` — claims not yet checked against a second source
- `contested` — sources actively disagree; body must have a `## Contradictions` section

# Body conventions

- Prefer structure (headings, tables, lists, code blocks) over prose.
- Conventional headings with defined meaning: `# Schema`, `# Examples`,
  `# Citations` (per OKF), plus bundle-local `## Contradictions` and
  `## Deprecation`.
- Every non-draft concept: **≥ 2 outbound bundle-relative links** in the
  body. Links assert relationships; say the relationship in prose around
  the link.
- Claims from outside the bundle get a `# Citations` section with
  numbered references; frontmatter `sources` points at the captured copy.

# Page-creation threshold

Create a new page only if the subject (a) is referenced by 2+ sources or
existing pages, or (b) is central enough that other pages need to link
to it. Otherwise fold the material into the closest existing page.

# Review cadence defaults

| confidence | review_after offset from `updated` |
|-----------|-------------------------------------|
| high | +6 months |
| medium | +3 months |
| low | +1 month |

Volatile topics (pricing, versions, org charts): 1 month regardless.

# Log conventions

`## YYYY-MM-DD` headings, newest first; entries as
`* **Verb**: text with [links](/path.md).` Verbs in use: **Creation**,
**Update**, **Review**, **Merge**, **Split**, **Deprecation**,
**Archive**, **Ingestion**, **Lint-fix**. Rotate at ~500 entries
(`okf.py log` warns; move old entries to `kb/archive/log-YYYY.md`).
