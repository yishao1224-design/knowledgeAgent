---
name: kb-ingest
description: Capture a source (URL, file, pasted text, or conversation takeaways) into the OKF knowledge bundle — snapshot it immutably, then create or update concept pages. Use when the user shares material to remember, says "add this to the knowledge base", "ingest", "save this", or provides articles/docs/notes to incorporate.
---

# kb-ingest — Capture phase of the knowledge lifecycle

Turn an external source into immutable evidence plus linked, living
concept pages.

## Step 0 — Orient (mandatory)

> **First run in this project?** If there's no bundle directory or no
> `scripts/okf.py`, run the **kb-setup** skill first to scaffold them,
> then continue.
>
> Paths below assume the default bundle location, `okf/`. A project
> may have chosen another name at setup — whichever top-level directory
> holds `SCHEMA.md` is the bundle, and `okf.py` finds it on its own.

Read `okf/SCHEMA.md`, `okf/index.md`, and the last ~20 lines of
`okf/log.md`. Identify existing pages that overlap the new material.
**Update beats create** — see the page-creation threshold in SCHEMA.md.

## Step 1 — Capture the source

1. Fetch/read the source. For URLs use WebFetch; for files read them.
2. Write `okf/sources/YYYY-MM-DD-<slug>.md` with the Source frontmatter
   template from SCHEMA.md. The body is the captured content (verbatim
   or a faithful condensation — say which in the description).
3. Never overwrite an existing capture. Same source again → new dated
   file; the old one stays for diffing against the new one. Git is the
   tamper record — `git log -- okf/sources/` shows any edit to a
   capture after ingestion, with the original recoverable.
4. **Load-bearing visuals get kept, not just described.** When the
   source is or contains an image whose pixels are the evidence —
   especially a dense architecture diagram that can't be fully
   extracted in one pass — copy it to
   `okf/sources/assets/YYYY-MM-DD-<slug>.<ext>`, link it from the
   capture, and state in the capture what the asset shows, what you
   extracted this pass, and what remains unread (later ingests and
   reviews will re-read it). Assets are immutable like captures; rules
   and the trust caveat live in SCHEMA.md's *Source assets* section.
   Binaries with an authoritative home elsewhere (decks, PDFs) are NOT
   copied — extract their content and point `source_url` at the
   original.

Skip this step only when ingesting pure conversation takeaways with no
external source; then concepts cite no `sources` and get
`confidence: low` + tag `unverified`.

## Step 2 — Discuss before writing

Before touching concept pages, tell the user (briefly): the key
takeaways, which existing pages you'll update, which new pages meet the
creation threshold, and any contradictions with existing content. If
the material contradicts an existing `active` page, do NOT silently
overwrite: add a `## Contradictions` section to that page, tag it
`contested`, set `lifecycle: needs_review`.

## Step 3 — Write/update concepts

For each page:
- Pick `type` from SCHEMA.md's type registry and put the page in the
  matching directory — `Entity` in `entities/` for a concrete nameable
  thing (person, org, system, dataset, tool), `Comparison` in
  `comparisons/`, `Query` in `queries/`, `Concept` in `concepts/` for
  an idea/definition/explanation. **Never default to `type: Concept`**
  just because the frontmatter template example shows it.
- Full frontmatter per SCHEMA.md's page frontmatter template, `type`
  set per the above. New pages start `lifecycle: draft` (`status:
  draft`); set `stale_after` from the confidence table.
- Stamp `generated: { by, at }` on every page you write or materially
  rewrite — `by` is your own agent identity as `<tool>/<version>`, `at`
  is today. Never stamp `verified:` here: writing a page is not
  confirming it, and that field belongs to kb-review.
- `sources:` lists the capture(s) from Step 1 as OKF v0.2 mappings —
  `resource:` (bundle-relative for a capture), `id:`, `title:`.
- **Pin re-readable repo files.** When a claim rests on a file in this
  repo rather than on a capture, add a second kind of `sources` entry:
  a document-relative `resource:` (`../../scripts/okf.py`), plus
  `last_modified:` (today) and `blob:` from
  `python scripts/okf.py drift --hash <file>`. That is what lets
  `okf.py drift` re-trigger review when the file changes, instead of
  waiting on the clock. Never pin a `/sources/` capture — captures are
  immutable, so drift on them is meaningless.
- Externally-derived claims are cited inline by source id —
  `…ships its own provider layer [openwiki]`. Do **not** write a
  `# Citations` section; OKF v0.2 replaced it with `sources`.
- Domain concepts (`type: Concept` describing business rules,
  processes, system behavior) follow the **domain-concept body
  template** in SCHEMA.md: required sections `## Definition`,
  `## Key Behaviors` and/or `## Invariants`, `## Related Concepts`;
  optional sections only when they have real content — never `N/A`
  placeholders. Everything else — `Entity`/`Comparison`/`Query` pages
  and method/meta `Concept` pages — keeps free structure (see
  SCHEMA.md's linked Entity example).
- ≥ 2 outbound bundle-relative links, with the relationship stated in
  surrounding prose. Link to not-yet-written pages freely if they'd
  meet the threshold later. You may write links as `[[slug]]` or
  `[[slug|display text]]` shorthand (`slug` = a page's filename stem or
  title); close-out expands them to canonical form.
- Bump `updated:` on every touched page.

Promote `draft → active` only when the page is cross-linked, cited, and
you'd stand behind its claims.

## Step 4 — Close out

1. `python scripts/okf.py links` — expand any `[[slug]]` shorthand to
   canonical links; resolve anything it reports as ambiguous/unresolved.
2. `python scripts/okf.py index`
3. `python scripts/okf.py log "**Ingestion**: <what> from [source](/sources/<file>.md); created/updated [page](/path.md)."`
4. `python scripts/okf.py lint` — fix errors, report warnings.
5. Summarize for the user: pages created/updated, status assigned,
   contradictions flagged.
