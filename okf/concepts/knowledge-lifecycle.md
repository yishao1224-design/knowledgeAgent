---
type: Concept
title: The Knowledge Lifecycle
description: How concepts in this bundle move through draft, active, needs_review, deprecated, and archived — and which skill drives each transition.
status: stable
confidence: high
created: 2026-07-05
updated: 2026-11-23
stale_after: 2027-01-05
tags: []
sources:
  - resource: /sources/2026-07-05-okf-spec-v0-1.md
    id: okf-spec
    title: OKF v0.1 spec capture
  - resource: https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md
    id: hermes-llm-wiki
    title: Hermes llm-wiki skill
---

# The Knowledge Lifecycle

This bundle treats knowledge as perishable: every page carries a
`status` and `stable` (active) pages carry a `stale_after` date, after
which they are no longer presumed true. The five states are read off
OKF v0.2's three-value `status` plus two derived signals — the
`needs-review` tag or an overdue `stale_after` on a stable page, and
the `archive/` folder for a deprecated one — so no extension key has to
be kept in sync (an earlier `lifecycle` key did that; it is retired) —
see
[OKF](/concepts/open-knowledge-format.md) and [SCHEMA.md](/SCHEMA.md)
for the mapping [okf-spec]. The profile borrows its operating discipline
(orient-first, immutable sources, lint audits) from the Hermes llm-wiki
pattern [hermes-llm-wiki].

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
| active → needs_review | kb-lint / kb-review | a pinned source's `blob:` moved, `stale_after` passed, source changed upstream, or contradiction found |
| needs_review → active | kb-review | claims re-verified against sources |
| any → deprecated | kb-review / kb-curate | superseded or wrong; requires `superseded_by` or `## Deprecation` |
| deprecated → archived | kb-curate | zero inbound links; moved to `/archive/` |

Two invariants make the cycle trustworthy: captures under `/sources/`
are immutable (an edit there is a corruption signal, not an update —
git history is what surfaces one), and pages are deprecated rather than deleted so inbound links
never dangle silently. Conventions for fields and cadences live in
[SCHEMA.md](/SCHEMA.md). The lifecycle and its toolchain can be
installed into any project repository — see
[adopting the bundle pattern](/concepts/adopting-the-bundle-pattern.md).

## Trust semantics — the page is the unit of trust

`status` (with the `needs-review` tag), `confidence`, and `stale_after` are page-level, but a page
accumulates claims of different ages and provenance (e.g. a concept
contributed to by several user stories — see the
[user story analysis workflow](/concepts/user-story-analysis-workflow.md)).
The fields resolve this by **weakest-link semantics**:

- The page's state = the *weakest* claim's state. One contested claim
  puts the whole page in needs review (tag `needs-review`); over-warning beats silently serving
  the one bad claim.
- `stale_after` = the *soonest* check any claim needs — the page's
  cadence follows its most volatile / least-recently-verified claim.
  Corollary: an edit that touches one claim must **not re-warrant the
  rest** — bump `stale_after` only for claims actually re-verified,
  even though `updated:` moves on any touch.
- Claim-level provenance still scales: `sources` accumulates one entry
  per contribution, and each entry's `id` is what body prose cites, so
  a claim resolves to the exact material behind it.
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
| A pinned repo file changed | `okf.py drift` — exact, fires on the change |
| Time passed, nothing re-affirmed | overdue `stale_after` (the backstop) |
| Sources disagree | contradiction found at ingest or query |
| Code changed | story DoD trigger / analysis-time cross-check |
| A page's own open questions undermine its claims | SCHEMA's open-questions rule |

Many fallible detectors, one uniform response — cheap, reversible,
frontmatter-only. Any skill may *flag* (tag the page `needs-review`); only
kb-review may *resolve* (promote back or deprecate) — see the division
of responsibility in
[the lifecycle skill suite](/entities/lifecycle-skills.md). Flagging is
democratized, verdicts are centralized, so no doubt is ever settled
silently.
