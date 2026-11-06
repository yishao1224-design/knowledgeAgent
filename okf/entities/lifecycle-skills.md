---
type: Entity
title: The Lifecycle Skill Suite
description: The five canonical skills (kb-ingest, kb-query, kb-review, kb-curate, kb-lint) that drive the knowledge lifecycle — one per phase, with strict division of responsibility.
status: stable
lifecycle: active
confidence: high
created: 2026-07-06
updated: 2026-11-06
stale_after: 2026-10-06
tags: []
sources:
  - resource: /sources/2026-07-06-lifecycle-skills.md
    id: lifecycle-skills
    title: Lifecycle skills capture
  - resource: ../../skills/kb-ingest/SKILL.md
    id: kb-ingest
    title: kb-ingest SKILL.md
    last_modified: 2026-11-06
    blob: e71e0050d703
  - resource: ../../skills/kb-query/SKILL.md
    id: kb-query
    title: kb-query SKILL.md
    last_modified: 2026-11-06
    blob: 3d9970846fd0
  - resource: ../../skills/kb-review/SKILL.md
    id: kb-review
    title: kb-review SKILL.md
    last_modified: 2026-11-06
    blob: f11b57800f1e
  - resource: ../../skills/kb-curate/SKILL.md
    id: kb-curate
    title: kb-curate SKILL.md
    last_modified: 2026-11-06
    blob: adee4accf1c1
  - resource: ../../skills/kb-lint/SKILL.md
    id: kb-lint
    title: kb-lint SKILL.md
    last_modified: 2026-11-06
    blob: 41e3cba48529
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

# Schema

| Skill | Phase | One-line contract |
|-------|-------|-------------------|
| kb-ingest | Capture | Immutable source snapshot → linked concept pages; update beats create; discuss before writing |
| kb-query | Serve | Answer with citations and explicit trust labels; file synthesis-worthy answers as Query pages |
| kb-review | Verify | Work the queue (`stats`, `drift`, plus git history on `/sources/`); keep `active` a meaningful promise; verdict table from bump-and-extend down to deprecate |
| kb-curate | Garden | Structure only — merge/split/archive/move; never changes what pages claim |
| kb-lint | Audit | Mechanical health only — fix errors now, queue semantic issues for review/curate |

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

## Project scopes

Since 2026-11-06 every skill's Step 0 is project-aware: in a bundle
holding project scopes (a subdirectory with its own `SCHEMA.md`, see
[SCHEMA.md](/SCHEMA.md)), a session first settles which project it is
in, then reads the root SCHEMA (team rules) plus the project's own
SCHEMA, `index.md` and `log.md`, and passes `--project` to `okf.py
log`/`stats`/`drift`. Types and directories come from the project's
registry; kb-query maps types across projects by their stated meaning;
kb-ingest pins code in other repositories by `repo:` + `path:` [kb-ingest].

## Editing the skills

The canonical copies live in `skills/`; `.claude/skills/` and
`.github/prompts/` are generated — edit the canonical file and re-run
`python scripts/okf.py init`. Skill changes alter the rules every
future session plays by, so they sit in the highest human-review tier
of the PR gates (CODEOWNERS territory).
