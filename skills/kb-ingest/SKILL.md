---
name: kb-ingest
description: Capture a source (URL, file, pasted text, or conversation takeaways) into the kb/ knowledge bundle — snapshot it immutably, then create or update concept pages. Use when the user shares material to remember, says "add this to the knowledge base", "ingest", "save this", or provides articles/docs/notes to incorporate.
---

# kb-ingest — Capture phase of the knowledge lifecycle

Turn an external source into immutable evidence plus linked, living
concept pages.

## Step 0 — Orient (mandatory)

Read `kb/SCHEMA.md`, `kb/index.md`, and the last ~20 lines of
`kb/log.md`. Identify existing pages that overlap the new material.
**Update beats create** — see the page-creation threshold in SCHEMA.md.

## Step 1 — Capture the source

1. Fetch/read the source. For URLs use WebFetch; for files read them.
2. Write `kb/sources/YYYY-MM-DD-<slug>.md` with the Source frontmatter
   template from SCHEMA.md. The body is the captured content (verbatim
   or a faithful condensation — say which in the description).
3. Compute the hash and put it in the frontmatter:
   `python scripts/okf.py drift --hash kb/sources/<file>.md`
4. Never overwrite an existing capture. Same source again → new dated
   file; the old one stays for drift comparison.

Skip this step only when ingesting pure conversation takeaways with no
external source; then concepts cite no `sources` and get
`confidence: low` + tag `unverified`.

## Step 2 — Discuss before writing

Before touching concept pages, tell the user (briefly): the key
takeaways, which existing pages you'll update, which new pages meet the
creation threshold, and any contradictions with existing content. If
the material contradicts an existing `active` page, do NOT silently
overwrite: add a `## Contradictions` section to that page, tag it
`contested`, set `status: needs_review`.

## Step 3 — Write/update concepts

For each page:
- Full frontmatter per SCHEMA.md template. New pages start
  `status: draft`; set `review_after` from the confidence table.
- `sources:` lists the capture(s) from Step 1.
- Externally-derived claims get a `# Citations` section.
- Domain concepts (business rules, processes, system behavior) follow
  the **domain-concept body template** in SCHEMA.md: required sections
  `## Definition`, `## Key Behaviors` and/or `## Invariants`,
  `## Related Concepts`; optional sections only when they have real
  content — never `N/A` placeholders. Method/meta pages keep free
  structure.
- ≥ 2 outbound bundle-relative links, with the relationship stated in
  surrounding prose. Link to not-yet-written pages freely if they'd
  meet the threshold later.
- Bump `updated:` on every touched page.

Promote `draft → active` only when the page is cross-linked, cited, and
you'd stand behind its claims.

## Step 4 — Close out

1. `python scripts/okf.py index`
2. `python scripts/okf.py log "**Ingestion**: <what> from [source](/sources/<file>.md); created/updated [page](/path.md)."`
3. `python scripts/okf.py lint` — fix errors, report warnings.
4. Summarize for the user: pages created/updated, status assigned,
   contradictions flagged.
