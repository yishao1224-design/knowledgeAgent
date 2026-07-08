---
type: Source
title: Lifecycle skills (canonical SKILL.md files)
description: Faithful condensation of the five canonical lifecycle skills under skills/ (kb-ingest, kb-query, kb-review, kb-curate, kb-lint) as of 2026-07-06.
source_url: skills/ (this repository, canonical copies)
ingested: 2026-07-06
sha256: e31abbea3f0009a5edb2d4553ef769918767d8d35a10818c906e80f81c24ab54
---

# Lifecycle skills — condensed capture

Five skills under `skills/<name>/SKILL.md`, each driving one phase of
the knowledge lifecycle. Condensed from the canonical files; step
numbering and rule wording preserved where load-bearing.

## kb-ingest — Capture phase

"Turn an external source into immutable evidence plus linked, living
concept pages."

- Step 0 Orient (mandatory): read SCHEMA.md, index.md, last ~20 lines
  of log.md; identify overlapping pages. **Update beats create.**
- Step 1 Capture: snapshot to `kb/sources/YYYY-MM-DD-<slug>.md` with
  Source frontmatter + sha256 via `okf.py drift --hash`; never
  overwrite an existing capture (same source again → new dated file).
  Skipped only for pure conversation takeaways → no `sources`,
  `confidence: low` + tag `unverified`.
- Step 2 Discuss before writing: takeaways, pages to update/create,
  contradictions. Contradiction with an `active` page → add
  `## Contradictions`, tag `contested`, `status: needs_review` — never
  silently overwrite.
- Step 3 Write/update: full frontmatter, new pages start `draft`,
  `review_after` from cadence table, `# Citations` for external claims,
  domain concepts follow SCHEMA.md's domain-concept body template,
  ≥2 outbound bundle-relative links, bump `updated`. Promote
  draft → active only when cross-linked, cited, claims stood behind.
- Step 4 Close out: `okf.py index`, `okf.py log`, `okf.py lint`,
  summarize.

## kb-query — Serve phase

"Answer from the bundle, honestly labeled, and feed durable answers
back into it."

- Orient via index; Grep for terms the index doesn't surface.
- Gather: read relevant pages AND one hop of links; note `status`,
  `confidence`, `review_after`.
- Answer: cite every load-bearing claim with its bundle path; label
  trust explicitly — `needs_review`/overdue → "may be stale";
  `deprecated` → answer from `superseded_by`; `contested` → present
  both positions, never pick a side silently; `draft`/low confidence →
  say unverified. If the bundle can't answer, say so plainly and offer
  to research + ingest; don't pad thin content.
- File as `kb/queries/<slug>.md` (type Query) when the answer took real
  synthesis across 2+ pages or exposed a gap/contradiction; not for
  trivial single-page lookups. Original question as H1.

## kb-review — Verify phase

"Keep `active` a meaningful promise: everything active has been checked
recently enough to trust."

- Queue from `okf.py stats` (needs_review + active past review_after)
  plus dependents of drifted sources (`okf.py drift`). Triage:
  contested first, then drift dependents, then oldest overdue.
- Re-verify each page against its source captures; re-fetch changed
  upstreams into a NEW dated capture (never edit the old one).
- Verdict table: all hold → bump `updated`, new `review_after`, stay
  active, maybe raise confidence; some changed → rewrite those claims
  with new capture; contested → `## Contradictions` + `contested` tag,
  keep needs_review; substantially wrong → `deprecated` +
  `superseded_by` or `## Deprecation`; can't verify (low stakes) →
  lower confidence, tag `unverified`, keep needs_review.
- **Never delete during review** — deprecation is the strongest verdict
  here; deletion belongs to kb-curate.

## kb-curate — Garden phase

"Structure work only. Curation changes where knowledge lives and how it
connects, not what it claims — claim verification belongs to
kb-review."

- Propose a plan before large refactors (>5 pages or directory
  renames); small fixes just happen.
- Merge duplicates: survivor keeps content/sources/earliest `created`;
  loser becomes `deprecated` one-line pointer with `superseded_by`;
  repoint inbound links (`okf.py lint --inbound`).
- Split bloated pages covering 2+ threshold-worthy subjects.
- Archive: only `deprecated` pages with zero inbound links → move to
  `kb/archive/`, `status: archived`. Deletion rare, explicit user
  approval, only for pages that never carried unique knowledge.
- Moves/renames: bundle-relative links break — Grep and update every
  referrer in the same change.
- Taxonomy/schema upkeep in SCHEMA.md in the same change; log rotation
  past ~500 entries to `kb/archive/log-YYYY.md`.
- Close-out lint must show zero errors and zero broken-link
  regressions.

## kb-lint — Audit phase

"Mechanical health only. Lint tells you a page is overdue; deciding
whether its claims still hold is kb-review's job."

- Run `okf.py lint`, `drift`, `stats`.
- ERRORs fixed now mechanically (frontmatter reconstruction, deprecated
  without successor → write `## Deprecation`, frontmatter on non-root
  index.md removed).
- WARNs: fill missing fields from content + cadence table; orphans →
  add linking context or flag for kb-curate; unknown tags → kb-curate
  taxonomy rules; under-linked pages → only genuinely meaningful links,
  **never filler links to satisfy the count**; overdue reviews → set
  `needs_review` but do NOT re-verify content here.
- DRIFT findings = tamper/corruption signal (sources are immutable):
  restore from git history, else report before touching.
- INFOs (links to not-yet-written pages) fine by design; report ones
  with 3+ referrers as having crossed the page-creation threshold.
