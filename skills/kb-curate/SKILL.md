---
name: kb-curate
description: Garden the kb/ knowledge bundle structure — merge duplicate pages, split bloated ones, deprecate and archive, fix taxonomy drift, refactor directories while keeping links whole. Use when the user asks to clean up, reorganize, dedupe, merge, archive, or restructure the knowledge base.
---

# kb-curate — Garden phase of the knowledge lifecycle

Structure work only. Curation changes where knowledge lives and how it
connects, not what it claims — claim verification belongs to kb-review.

## Step 0 — Orient

Read `kb/SCHEMA.md`, `kb/index.md`, recent `kb/log.md`. Run
`python scripts/okf.py lint` and `okf.py stats` for a health picture:
orphans, under-linked pages, taxonomy violations, status distribution.

Propose a short curation plan to the user before large refactors
(anything touching >5 pages or renaming directories). Small fixes:
just do them.

## Operations

### Merge duplicates
1. Pick the survivor (better title/location/inbound links).
2. Fold unique content and `sources` in; union the tags; keep the
   earliest `created`; bump `updated`.
3. The loser becomes `status: deprecated`, body replaced by a one-line
   pointer, `superseded_by: /path/to/survivor.md`.
4. Repoint inbound links to the survivor:
   `okf.py lint --inbound /path/to/loser.md` lists the linkers.

### Split a bloated page
Page covers 2+ threshold-worthy subjects → create the new pages, move
content, leave a summary + link on the original, cross-link all parts.

### Archive
Only `deprecated` pages with **zero inbound links** (verify with
`okf.py lint --inbound`) and no historical value in place: move the
file to `kb/archive/`, set `status: archived`. Deletion (rare) only
with explicit user approval, and only for pages that never carried
unique knowledge (e.g., accidental duplicates).

### Move / rename
Bundle-relative links (`/dir/page.md`) break on moves — after any move,
Grep `kb/` for the old path and update every referrer in the same
change. This is why moves are batched here rather than done ad hoc.

### Taxonomy & schema upkeep
Tags used but undefined → either add to SCHEMA.md taxonomy (if earning
their keep across 2+ pages) or replace with an existing tag. New
directory or type → register in SCHEMA.md **in the same change**.

### Log rotation
`log.md` past ~500 entries → move whole old years to
`kb/archive/log-YYYY.md`, leave the current year in place.

## Close out

1. `okf.py index`
2. One log entry per operation (**Merge**/**Split**/**Archive**/**Update**),
   linking survivor and casualty.
3. `okf.py lint` must come back with **zero errors and zero broken-link
   regressions** — curation that breaks links is worse than no curation.
4. Summarize the before/after structure for the user.
