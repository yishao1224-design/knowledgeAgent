---
type: Entity
title: The Lifecycle Skill Suite
description: The five canonical skills (kb-ingest, kb-query, kb-review, kb-curate, kb-lint) that drive the knowledge lifecycle — one per phase, with strict division of responsibility.
status: active
confidence: high
created: 2026-07-06
updated: 2026-07-07
review_after: 2026-10-06
tags: []
sources:
  - /sources/2026-07-06-lifecycle-skills.md
---

# The Lifecycle Skill Suite

Five prompt-based skills, canonical under `skills/<name>/SKILL.md` and
synced to per-tool copies by `okf.py init`, each driving one phase of
the [knowledge lifecycle](/concepts/knowledge-lifecycle.md) [1]. They
are the "running code" of the lifecycle — which is why
[automating the lifecycle](/concepts/automating-the-lifecycle.md)
recommends scheduling them headless rather than porting them to an
orchestration framework, and why
[adopting the bundle pattern](/concepts/adopting-the-bundle-pattern.md)
copies `skills/` into a target repo as one of two required pieces.

# Schema

| Skill | Phase | One-line contract |
|-------|-------|-------------------|
| kb-ingest | Capture | Immutable source snapshot → linked concept pages; update beats create; discuss before writing |
| kb-query | Serve | Answer with citations and explicit trust labels; file synthesis-worthy answers as Query pages |
| kb-review | Verify | Work the queue (`stats` + `drift`); keep `active` a meaningful promise; verdict table from bump-and-extend down to deprecate |
| kb-curate | Garden | Structure only — merge/split/archive/move; never changes what pages claim |
| kb-lint | Audit | Mechanical health only — fix errors now, queue semantic issues for review/curate |

## Division of responsibility (the load-bearing rules)

The skills partition authority so no phase silently does another's job:

- **Claim truth belongs to kb-review alone.** kb-lint flags a page as
  overdue but must not re-verify content; kb-curate moves and merges
  but must not change what a page claims.
- **Deletion belongs to kb-curate alone**, and only for zero-inbound
  `deprecated` pages (or, rarely, with explicit user approval).
  kb-review's strongest verdict is deprecation.
- **Contradictions are never resolved silently.** Both kb-ingest and
  kb-review handle them the same way: `## Contradictions` section,
  `contested` tag, `status: needs_review`; kb-query presents both
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
`python scripts/okf.py init`. Skill changes alter the rules every
future session plays by, so they sit in the highest human-review tier
of the PR gates (CODEOWNERS territory).

# Citations

[1] [Lifecycle skills capture](/sources/2026-07-06-lifecycle-skills.md)
