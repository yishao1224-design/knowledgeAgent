---
name: kb-lint
description: Audit the OKF knowledge bundle's mechanical health — OKF conformance, frontmatter completeness, broken links, orphans, overdue reviews — and fix what's safe to fix. Use when the user asks for a health check, lint, audit, or integrity check of the knowledge base.
---

# kb-lint — Audit phase of the knowledge lifecycle

Mechanical health only. Lint tells you a page is overdue; deciding
whether its claims still hold is kb-review's job — don't drift into
content verification here.

> **First run in this project?** If there's no bundle directory or no
> `scripts/okf.py`, run the **kb-setup** skill first to scaffold them,
> then continue.
>
> Paths below assume the default bundle location, `okf/`. A project
> may have chosen another name at setup — whichever top-level directory
> holds `SCHEMA.md` is the bundle, and `okf.py` finds it on its own.
>
> **Projects.** If the bundle holds project directories (a subdirectory
> with its own `SCHEMA.md`, listed under *Projects* in the root
> `index.md`), work inside one: settle which project the request
> belongs to, read the root `SCHEMA.md` (team rules, never loosened)
> **plus** that project's `SCHEMA.md`, `index.md` and recent `log.md`.
> Those project files stand in for the `okf/…` ones in the steps
> below; captures go in `<project>/sources/`; `okf.py log`, `stats` and
> `drift` take `--project <name>`. Types and directories are the
> project's own — take them from its type registry, never assume
> `concepts/`/`entities/`. The root `log.md` is only for team-level
> changes (root SCHEMA, root-level shared pages, adding or moving
> projects).

## Step 1 — Run the tooling

```
python scripts/okf.py lint
python scripts/okf.py stats
```

## Step 2 — Fix by severity

**ERRORs — fix now, mechanically:**
- Missing/unparseable frontmatter or empty `type` → reconstruct from
  the page content and SCHEMA.md templates.
- `deprecated` without `superseded_by`/`## Deprecation` → find the
  successor via log.md/index history; if none exists, write the
  `## Deprecation` rationale.
- Frontmatter on a non-root `index.md` → remove it.

**WARNs — fix the mechanical ones, queue the semantic ones:**
- Missing `title`/`description`/`updated`/`stale_after`/`lifecycle` →
  fill from content and the SCHEMA.md cadence table.
- Legacy v0.1 shapes — a `review_after` field, a bare-string `sources`
  entry, a surviving `# Citations` section → migrate to the v0.2 shapes
  in SCHEMA.md (`stale_after`, `sources` mappings, inline `[source-id]`
  citations). Mechanical; do it here.
- Orphans → add the page to a linking context (or run `okf.py index`
  if it's just missing from the index); if nothing should link to it,
  that's a curation question — flag for kb-curate.
- Unknown tags → per kb-curate taxonomy rules.
- Under-linked pages (<2 outbound) → add genuinely meaningful links
  only. **Never add filler links to satisfy the count** — if no second
  real relationship exists, note the page for kb-curate (it may not
  meet the page threshold).
- Overdue reviews → set `lifecycle: needs_review`; do NOT re-verify
  content here. Tell the user the review queue grew.

**Pinned-source drift** (`pinned source ... changed` / `no longer
exists`, also reported by `okf.py drift`): the file a page cites has
moved on. This is a *semantic* finding — queue it for kb-review, do
**not** restamp `blob:` here. Restamping is a claim that someone
re-read the file, and lint never reads content. Set
`lifecycle: needs_review` and tell the user.

**A source capture edited after ingestion** is a tamper/corruption
signal, since captures are immutable. `git log -- okf/sources/`
surfaces it. Restore from git history if available; otherwise report to
the user before touching it.

**INFOs (links to not-yet-written pages):** fine by design (OKF §5).
Only report a summary count, plus any that have accumulated 3+
referrers — those have crossed the page-creation threshold and are
worth writing (suggest kb-ingest).

## Step 3 — Close out

1. Re-run `okf.py lint` — errors must be zero.
2. `okf.py log "**Lint-fix**: <n> errors, <m> warnings fixed; <k> queued for review/curation."`
3. Report: what was fixed, what was queued for kb-review/kb-curate and
   why it wasn't safe to fix mechanically.
