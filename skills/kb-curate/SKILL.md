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
Trigger: the page covers 2+ subjects that each pass SCHEMA.md's
page-creation threshold on their own. Earlier symptoms worth acting on:
one volatile claim repeatedly dragging a stable page into
`needs_review` (trust granularity no longer matches page granularity);
sections citing disjoint `sources`; the page's one-sentence
`description` no longer honest.

1. Move content **verbatim** — split changes structure, not claims. A
   wrong claim noticed mid-split gets flagged `needs_review`, never
   fixed in the same operation.
2. New pages' frontmatter: `status` carries over from the parent (the
   content was already verified; only its address changed);
   `confidence` and `review_after` set **per part** — this is the
   payoff: the volatile part gets the short cadence, the stable part
   the long one; `sources` and `# Citations` distributed to the parts
   they back; tags per part; keep the parent's `created`, set
   `updated` to today.
3. The original stays alive as a summary + links to the parts — **not
   deprecated** (unlike merge's loser). Its URL keeps working, so
   inbound links don't break; optionally repoint linkers that clearly
   targeted a moved section.
4. Cross-link all parts, relationship stated in prose (this also
   satisfies the 2-link minimum immediately).

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
