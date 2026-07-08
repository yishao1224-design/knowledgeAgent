---
type: Concept
title: The Knowledge Lifecycle
description: How concepts in this bundle move through draft, active, needs_review, deprecated, and archived — and which skill drives each transition.
status: active
confidence: high
created: 2026-07-05
updated: 2026-07-08
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

The skills named below are documented as a suite in
[the lifecycle skill suite](/entities/lifecycle-skills.md).

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

## Trust semantics — the page is the unit of trust

`status`, `confidence`, and `review_after` are page-level, but a page
accumulates claims of different ages and provenance (e.g. a concept
contributed to by several user stories — see the
[user story analysis workflow](/concepts/user-story-analysis-workflow.md)).
The fields resolve this by **weakest-link semantics**:

- `status` = the *weakest* claim's state. One contested claim puts the
  whole page in `needs_review`; over-warning beats silently serving the
  one bad claim.
- `review_after` = the *soonest* check any claim needs — the page's
  cadence follows its most volatile / least-recently-verified claim.
  Corollary: an edit that touches one claim must **not re-warrant the
  rest** — bump `review_after` only for claims actually re-verified,
  even though `updated:` moves on any touch.
- Claim-level provenance still scales: `sources` accumulates one
  capture per contribution, and `# Citations` maps claims to captures.
- When one volatile claim keeps dragging a stable page into
  `needs_review`, that is a granularity mismatch, and the fix is
  structural: kb-curate's split operation gives each part its own
  cadence. Curation is what keeps page granularity matched to trust
  granularity; a page whose claims all decay together is the real
  invariant.

### Why needs_review is load-bearing

Knowledge decays gradually — a stale page is usually still mostly
right. Without a middle state the moment doubt appears forces a false
binary: leave it `active` (silent staleness, readers consume wrong
claims confidently) or deprecate (destroy a mostly-good page over one
claim). `needs_review` is the honest middle: *still served, but
labeled*. It is also what makes `active` a meaningful promise — a
status pages cannot fall out of would vouch for nothing.

Structurally it is the **convergence point** for every doubt detector:

| Doubt source | Detector |
|---|---|
| Time passed, nothing re-affirmed | overdue `review_after` (the backstop) |
| Sources disagree | contradiction found at ingest or query |
| Code changed | story DoD trigger / analysis-time cross-check |
| A page's own open questions undermine its claims | SCHEMA's open-questions rule |

Many fallible detectors, one uniform response — cheap, reversible,
status-only. Any skill may *flag* (demote to `needs_review`); only
kb-review may *resolve* (promote back or deprecate) — see the division
of responsibility in
[the lifecycle skill suite](/entities/lifecycle-skills.md). Flagging is
democratized, verdicts are centralized, so no doubt is ever settled
silently.

# Citations

[1] [OKF v0.1 spec capture](/sources/2026-07-05-okf-spec-v0-1.md)
[2] [Hermes llm-wiki skill](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md)
