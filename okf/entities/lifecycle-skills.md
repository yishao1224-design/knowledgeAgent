---
type: Entity
title: The Lifecycle Skill Suite
description: The five lifecycle skills (kb-ingest, kb-query, kb-review, kb-curate, kb-lint) — one per phase, with strict division of responsibility — plus the kb-setup bootstrap skill that scaffolds a bundle in a fresh project.
status: stable
lifecycle: active
confidence: high
created: 2026-07-06
updated: 2026-11-10
stale_after: 2027-05-10
tags: []
sources:
  - resource: /sources/2026-07-06-lifecycle-skills.md
    id: lifecycle-skills
    title: Lifecycle skills capture
  - resource: ../../skills/kb-ingest/SKILL.md
    id: kb-ingest
    title: kb-ingest SKILL.md
    last_modified: 2026-11-10
    blob: 53fdfb22b31c
  - resource: ../../skills/kb-query/SKILL.md
    id: kb-query
    title: kb-query SKILL.md
    last_modified: 2026-11-10
    blob: ffff4aa8f998
  - resource: ../../skills/kb-review/SKILL.md
    id: kb-review
    title: kb-review SKILL.md
    last_modified: 2026-11-10
    blob: 6ce3390450f6
  - resource: ../../skills/kb-curate/SKILL.md
    id: kb-curate
    title: kb-curate SKILL.md
    last_modified: 2026-11-10
    blob: b20099f5cf73
  - resource: ../../skills/kb-lint/SKILL.md
    id: kb-lint
    title: kb-lint SKILL.md
    last_modified: 2026-11-10
    blob: 2b4c59b3df75
  - resource: ../../skills/kb-setup/SKILL.md
    id: kb-setup
    title: kb-setup SKILL.md
    last_modified: 2026-11-10
    blob: 20b0caa5157f
generated:
  by: claude-code/2.1.322
  at: 2026-11-10
---

# The Lifecycle Skill Suite

Five prompt-based skills, canonical under `skills/<name>/SKILL.md` and
synced to per-tool copies by `okf.py init`, each driving one phase of
the [knowledge lifecycle](/concepts/knowledge-lifecycle.md) [lifecycle-skills]. They
are the "running code" of the lifecycle — which is why
[automating the lifecycle](/concepts/automating-the-lifecycle.md)
recommends scheduling them headless rather than porting them to an
orchestration framework, and why
[adopting the bundle pattern](/concepts/adopting-the-bundle-pattern.md)
copies `skills/` into a target repo as one of two required pieces.

A sixth skill, **kb-setup**, drives no lifecycle phase: it bootstraps a
project that installed the skills with `npx skills add` — copies the
`okf.py` bundled next to its SKILL.md to `scripts/okf.py`, asks the user
for the bundle directory name (default `okf/`), runs `okf.py init`, and
hands off to the other five [kb-setup]. The other skills' Step 0 points
at it when no bundle or toolchain exists.

# Schema

| Skill | Phase | One-line contract |
|-------|-------|-------------------|
| kb-ingest | Capture | Immutable source snapshot → linked concept pages; update beats create; discuss before writing |
| kb-query | Serve | Answer with citations and explicit trust labels; file synthesis-worthy answers as Query pages |
| kb-review | Verify | Work the queue (`stats`, `drift`, plus git history on `/sources/`); keep `active` a meaningful promise; verdict table from bump-and-extend down to deprecate |
| kb-curate | Garden | Structure only — merge/split/archive/move; never changes what pages claim |
| kb-lint | Audit | Mechanical health only — fix errors now, queue semantic issues for review/curate |
| kb-setup | Bootstrap (no phase) | Scaffold `scripts/okf.py` + the bundle once; idempotent, never overwrites [kb-setup] |

Adjacent tooling: [MarkItDown](/entities/markitdown.md) is an assessed
(not adopted) extraction helper for kb-ingest's binary-source capture
rule — the skill itself does not reference it.

## Division of responsibility (the load-bearing rules)

The skills partition authority so no phase silently does another's job:

- **Claim truth belongs to kb-review alone.** kb-lint flags a page as
  overdue but must not re-verify content; kb-curate moves and merges
  but must not change what a page claims.
- **Only kb-review restamps evidence.** A `sources[].blob` pin and a
  `verified:` entry are assertions that someone re-read the thing. Any
  skill may *report* drift — `okf.py drift` and kb-lint both do — but
  restamping without re-reading turns the freshest-looking signal in
  the bundle into a lie, so the write belongs to the one phase that
  actually reads sources. This is the same flag-widely / resolve-
  centrally split that makes `needs_review` work.
- **Deletion belongs to kb-curate alone**, and only for zero-inbound
  `deprecated` pages (or, rarely, with explicit user approval).
  kb-review's strongest verdict is deprecation.
- **Contradictions are never resolved silently.** Both kb-ingest and
  kb-review handle them the same way: `## Contradictions` section,
  `contested` tag, `lifecycle: needs_review`; kb-query presents both
  positions when serving contested content.
- **No filler links.** kb-lint fixes under-linked pages only with
  genuinely meaningful links; a page with no second real relationship
  is a curation question, not a link-count problem.
- **Every skill closes out through the same mechanical gate**:
  the [okf.py toolchain](/entities/okf-toolchain.md)'s
  `index` → `log` → `lint`, which is what makes the
  [PR quality gates](/concepts/pr-quality-gates.md) Tier-1 checks a
  formality for skill-driven changes rather than a hurdle.

## Editing the skills

The canonical copies live in `skills/`; `.claude/skills/` and
`.github/prompts/` are generated — edit the canonical file and re-run
`python scripts/okf.py init`. `skills/kb-setup/okf.py` is likewise a
copy of `scripts/okf.py` that `init` refreshes, never edited directly. Skill changes alter the rules every
future session plays by, so they sit in the highest human-review tier
of the PR gates (CODEOWNERS territory).
