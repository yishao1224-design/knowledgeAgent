---
name: kb-lint
description: Audit the kb/ knowledge bundle's mechanical health — OKF conformance, frontmatter completeness, broken links, orphans, overdue reviews, source drift — and fix what's safe to fix. Use when the user asks for a health check, lint, audit, or integrity check of the knowledge base.
---

# kb-lint — Audit phase of the knowledge lifecycle

Mechanical health only. Lint tells you a page is overdue; deciding
whether its claims still hold is kb-review's job — don't drift into
content verification here.

## Step 1 — Run the tooling

```
python scripts/okf.py lint
python scripts/okf.py drift
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
- Missing `title`/`description`/`updated`/`review_after` → fill from
  content and the SCHEMA.md cadence table.
- Orphans → add the page to a linking context (or run `okf.py index`
  if it's just missing from the index); if nothing should link to it,
  that's a curation question — flag for kb-curate.
- Unknown tags → per kb-curate taxonomy rules.
- Under-linked pages (<2 outbound) → add genuinely meaningful links
  only. **Never add filler links to satisfy the count** — if no second
  real relationship exists, note the page for kb-curate (it may not
  meet the page threshold).
- Overdue reviews → set `status: needs_review`; do NOT re-verify
  content here. Tell the user the review queue grew.

**DRIFT findings:** a source body changed post-ingestion — that's a
tamper/corruption signal since sources are immutable. Restore from git
history if available; otherwise report to the user before touching it.

**INFOs (links to not-yet-written pages):** fine by design (OKF §5).
Only report a summary count, plus any that have accumulated 3+
referrers — those have crossed the page-creation threshold and are
worth writing (suggest kb-ingest).

## Step 3 — Close out

1. Re-run `okf.py lint` — errors must be zero.
2. `okf.py log "**Lint-fix**: <n> errors, <m> warnings fixed; <k> queued for review/curation."`
3. Report: what was fixed, what was queued for kb-review/kb-curate and
   why it wasn't safe to fix mechanically.
