---
type: Schema
title: Bundle Schema & Conventions
description: Authoritative conventions for this OKF bundle — types, tags, frontmatter templates, lifecycle rules.
status: active
updated: 2026-07-08
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

# Domain-concept body template

Applies to `Concept` pages describing **domain** knowledge (business
rules, processes, behavior of the systems the team builds). Method/meta
pages — how this bundle itself works, engineering practices — keep free
structure. General body conventions above still apply, including
`# Citations` for externally-derived claims.

Required sections: `## Definition`, at least one of `## Key Behaviors`
or `## Invariants`, and `## Related Concepts`. Every other section is
optional — include it only when it has real content. **Never write
`N/A` placeholders**; an absent section reads the same and costs
nothing.

```markdown
# <Concept Name>

## Definition
1–3 sentences: what it is, where it applies, why it matters.

## Key Behaviors
- <behavior>

## Variants                      (optional)
### <Variant A>
- <difference or special requirement>

## Invariants
Rules that must hold regardless of status, entry point, or variant.
- <rule>

## Personas                      (optional)
- <persona> — <what they need from this concept>

## Related Artifacts             (optional)
- `<StableIdentifier>` (<artifact type>) — one-line role

## Related Concepts
- [Concept A](/concepts/concept-a.md) — <relationship>

## Open Questions                (optional)
- <unresolved question>
```

Template rules:

- The **committed** form of a link is always a bundle-relative markdown
  link (`[Title](/concepts/foo.md)`) — lint's link tracking, the graph,
  and the safe-delete check depend on it, and plain OKF readers can only
  follow that form.
- While **authoring**, you may write `[[slug]]` or `[[slug|display text]]`
  shorthand (`slug` = a page's filename stem or title; or an explicit
  `[[/path.md]]`). Run `python scripts/okf.py links` to expand every
  shorthand into the canonical form *before* `index`/`lint`. Expansion
  skips code spans, and leaves ambiguous / not-yet-written targets in
  place — lint then flags any `[[...]]` that survived (unexpanded/
  ambiguous → warning, missing target → info).
- **Artifacts** are deployable code/metadata components (e.g.
  Salesforce Apex classes, LWC, triggers, Flows). Reference them by
  stable identifier plus a one-line role. Do not document an artifact's
  internals here (that belongs in the code), and do not create a page
  per artifact — an artifact gets an `Entity` page only when it meets
  the page-creation threshold below.
- If `## Open Questions` accumulates items that contradict the page's
  own claims, set `status: needs_review` (and tag `contested` where
  sources disagree) instead of only annotating.

# Page-creation threshold

Create a new page only if the subject (a) is referenced by 2+ sources or
existing pages, or (b) is central enough that other pages need to link
to it. Otherwise fold the material into the closest existing page.

# Review cadence defaults

`review_after` is a **backstop, not the primary freshness mechanism** —
a dead-man's-switch that guarantees an `active` page is eventually
re-affirmed even when nothing else prompts it. It fires on the clock,
not on change, so it cannot tell "nothing changed" from "everything
changed." Scope the cadence to whether the page already has a *real
change signal*; running one blunt offset uniformly is what turns the
review queue into ignorable noise.

The `review_after` **date is an internal maintainer field.** Readers
never interpret it — the user-facing signal is the `status:
needs_review` flag surfaced in answers, which the overdue date merely
triggers.

Baseline offset from `updated`, by confidence:

| confidence | offset |
|-----------|--------|
| high | +6 months |
| medium | +3 months |
| low | +1 month |

Then adjust by change signal:

| The page's truth is governed by… | Cadence |
|----------------------------------|---------|
| A change process the bundle already tracks — e.g. domain code driven by user stories (see [ingesting requirements](/concepts/ingesting-requirements-from-ticket-systems.md)) | **Backstop only — lengthen well past the baseline.** The story / Definition-of-Done trigger is the real freshness signal; a short timer here is pure noise. |
| Nothing the bundle can track — external/volatile facts (pricing, versions, org charts, live URLs) | **Short — 1 month regardless of confidence.** This is where `review_after` earns its keep; no other mechanism catches these. |
| `unverified` conversation takeaways with no source | Short (≤ 1 month) — force a second look before the claim is trusted. |

A chronically-ignored review queue means the offsets are wrong for
those pages (too short for backstop-only pages), not that the field is
worthless — retune toward the table above rather than muting the
warning.

# Log conventions

`## YYYY-MM-DD` headings, newest first; entries as
`* **Verb**: text with [links](/path.md).` Verbs in use: **Creation**,
**Update**, **Review**, **Merge**, **Split**, **Deprecation**,
**Archive**, **Ingestion**, **Lint-fix**. Rotate at ~500 entries
(`okf.py log` warns; move old entries to `kb/archive/log-YYYY.md`).
