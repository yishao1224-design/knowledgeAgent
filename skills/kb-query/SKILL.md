---
name: kb-query
description: Answer a question from the OKF knowledge bundle with citations, flagging stale or deprecated content, and optionally file the answer back as a Query page. Use when the user asks what the knowledge base knows about something, or asks a question the bundle should answer.
---

# kb-query — Serve phase of the knowledge lifecycle

Answer from the bundle, honestly labeled, and feed durable answers back
into it.

## Step 0 — Orient

> **First run in this project?** If there's no bundle directory or no
> `scripts/okf.py`, run the **kb-setup** skill first to scaffold them,
> then continue.
>
> Paths below assume the default bundle location, `okf/`. A project
> may have chosen another name at setup — whichever top-level directory
> holds `SCHEMA.md` is the bundle, and `okf.py` finds it on its own.

Read `okf/SCHEMA.md` and `okf/index.md`. Locate candidate pages from the
index descriptions; Grep `okf/` for terms the index doesn't surface.

## Step 1 — Gather

Read the relevant pages AND the pages they link to (one hop) — links
assert relationships that change answers. Note each page's `status`,
`confidence`, and `stale_after`.

## Step 2 — Answer

- Synthesize across pages; cite every load-bearing claim with its
  bundle path, e.g. `(see /concepts/foo.md)`.
- **Label trust explicitly in the answer**:
  - `needs_review` or overdue `stale_after` → "may be stale (last
    verified <updated>)".
  - `deprecated` → answer from `superseded_by` instead; mention the
    deprecation only if relevant.
  - `contested` tag → present both positions from the
    `## Contradictions` section; never pick a side silently.
  - `draft`/`confidence: low` → say the claim is unverified.
- If the bundle can't answer: say so plainly, list nearest pages, and
  offer to research + `kb-ingest` the result. Do not pad thin content
  into a confident-sounding answer.

## Step 3 — File it (when worth keeping)

File the answer as `okf/queries/<slug>.md` (type `Query`) when it took
real synthesis across 2+ pages, or exposed a gap or contradiction.
Don't file trivial single-page lookups.

A filed Query uses the standard concept frontmatter, links to every
page used, and records the original question as an H1. Gaps found
become links to not-yet-written pages. Contradictions found: update the
affected page per kb-ingest Step 2 rules.

## Step 4 — Close out (only if you wrote anything)

`okf.py index`, then
`okf.py log "**Update**: filed [query](/queries/<slug>.md) on <topic>."`,
then `okf.py lint`.
