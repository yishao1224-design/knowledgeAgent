---
name: kb-query
description: Answer a question from the kb/ knowledge bundle with citations, flagging stale or deprecated content, and optionally file the answer back as a Query page. Use when the user asks what the knowledge base knows about something, or asks a question the bundle should answer.
---

# kb-query — Serve phase of the knowledge lifecycle

Answer from the bundle, honestly labeled, and feed durable answers back
into it.

## Step 0 — Orient

Read `kb/SCHEMA.md` and `kb/index.md`. Locate candidate pages from the
index descriptions; Grep `kb/` for terms the index doesn't surface.

## Step 1 — Gather

Read the relevant pages AND the pages they link to (one hop) — links
assert relationships that change answers. Note each page's `status`,
`confidence`, and `review_after`.

## Step 2 — Answer

- Synthesize across pages; cite every load-bearing claim with its
  bundle path, e.g. `(see /concepts/foo.md)`.
- **Label trust explicitly in the answer**:
  - `needs_review` or overdue `review_after` → "may be stale (last
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

File the answer as `kb/queries/<slug>.md` (type `Query`) when it took
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
