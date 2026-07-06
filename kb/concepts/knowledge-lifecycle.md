---
type: Concept
title: The Knowledge Lifecycle
description: How concepts in this bundle move through draft, active, needs_review, deprecated, and archived — and which skill drives each transition.
status: active
confidence: high
created: 2026-07-05
updated: 2026-07-06
review_after: 2027-01-05
tags: []
sources:
  - /sources/2026-07-05-okf-spec-v0-1.md
---

# The Knowledge Lifecycle

This bundle treats knowledge as perishable: every page carries a
`status` and `active` pages carry a `review_after` date, after which
they are no longer presumed true. The profile extends
[OKF](/concepts/open-knowledge-format.md) via its extension-key
mechanism [1], and borrows its operating discipline (orient-first,
immutable sources, lint audits) from the Hermes llm-wiki pattern [2].

# Schema

```
draft ──> active ──> needs_review ──> active     (re-verified)
                            │
                            └───────> deprecated ──> archived
```

| Transition | Driven by | Trigger |
|-----------|-----------|---------|
| (new) → draft | kb-ingest | source captured, page written |
| draft → active | kb-ingest | cross-linked, cited, claims stood behind |
| active → needs_review | kb-lint / kb-review | `review_after` passed, source drift, or contradiction found |
| needs_review → active | kb-review | claims re-verified against sources |
| any → deprecated | kb-review / kb-curate | superseded or wrong; requires `superseded_by` or `## Deprecation` |
| deprecated → archived | kb-curate | zero inbound links; moved to `/archive/` |

Two invariants make the cycle trustworthy: captures under `/sources/`
are immutable (drift in their hashes is a corruption signal, not an
update), and pages are deprecated rather than deleted so inbound links
never dangle silently. Conventions for fields and cadences live in
[SCHEMA.md](/SCHEMA.md). The lifecycle and its toolchain can be
installed into any project repository — see
[adopting the bundle pattern](/concepts/adopting-the-bundle-pattern.md).

# Citations

[1] [OKF v0.1 spec capture](/sources/2026-07-05-okf-spec-v0-1.md)
[2] [Hermes llm-wiki skill](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md)
