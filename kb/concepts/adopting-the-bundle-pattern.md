---
type: Concept
title: Adopting the Bundle Pattern in a Project Repo
description: How to install the OKF bundle + lifecycle skills into a real project repository — same-repo vs separate-repo decision, adoption steps, and what to tune.
status: active
confidence: low
created: 2026-07-06
updated: 2026-07-09
review_after: 2026-08-06
tags: [unverified]
---

# Adopting the Bundle Pattern in a Project Repo

The knowledgeAgent repo is a *template*, not just a standalone knowledge
base. Its toolchain is drop-in portable: `scripts/okf.py` resolves the
bundle root relative to its own file location (`ROOT = script dir's
parent`), so copying the script into any repo and running
`python scripts/okf.py init` bootstraps a `kb/` bundle there. The bundle
it creates follows [OKF](/concepts/open-knowledge-format.md) plus the
[knowledge lifecycle](/concepts/knowledge-lifecycle.md) profile.

# Schema

## Same repo or separate repo?

| Knowledge is about… | Put the bundle… | Why |
|---------------------|-----------------|-----|
| One project (architecture decisions, domain concepts, gotchas, ingested vendor docs) | Inside that project repo (`kb/` at root) — **default choice** | Agent has KB in context during coding sessions; knowledge changes ride in the same PRs as the code; CI can run `okf.py lint` |
| One project spanning multiple repos (tightly-integrated modules, each with its own repo) | A standalone project-level KB repo, checked out as a **sibling** of the module repos | The highest-value knowledge is cross-module (contracts, shared invariants) and has no single owning codebase; bundle links cannot cross repos, so splitting per module would tear it apart |
| Multiple unrelated projects, personal notes, team practices | A standalone KB repo (like knowledgeAgent itself) | No single codebase owns it |

Git submodules are technically possible but add sync friction; avoid
unless one bundle genuinely must be shared across repos.

## One project, multiple repos (the hybrid row)

A standalone project-level bundle loses the two same-repo advantages;
recover both deliberately:

- **The DoD trigger is a process link, not a repo link.** Stories live
  in one project-level tracker, so the Definition-of-Done gate from
  [ingesting requirements from ticket systems](/concepts/ingesting-requirements-from-ticket-systems.md)
  still works — the KB update is a *sibling* PR to the code PR rather
  than the same one. The story still doesn't close until the KB is
  current. Stories that touch several modules produce knowledge that
  only makes sense at project level — the strongest argument for the
  single bundle.
- **The analysis-time cross-check needs all repos in context.** The
  [user story analysis workflow](/concepts/user-story-analysis-workflow.md)'s
  code cross-check assumes the agent can see the code. Fix by
  convention: check the repos out as siblings
  (`project/module-a/`, `project/module-b/`, `project/kb/`) and add a
  pointer to **each module repo's `CLAUDE.md`**: "project KB lives at
  `../kb` — read its index before cross-module work; follow its
  session protocol before writing to it." That pointer is the
  cross-repo glue; without it module sessions won't know the KB exists.

Structure inside the bundle:

- **Scope by tags, not directories** — seed `module-a`, `module-b`,
  `integration` in the taxonomy before the first ingest. Pages spanning
  modules (many of the best ones) then have no directory identity
  crisis.
- **One `Entity` hub page per module** — its repo, boundary,
  responsibilities; cross-module concepts link both hubs.
- **Integration contracts are the crown jewels** — cross-module
  invariants belong in the domain-concept template's `## Invariants`,
  where the analysis-time cross-check can verify them against *both*
  codebases.
- **Don't ingest module internals** — the page-creation threshold and
  the don't-mirror rule apply with extra force; the bundle earns its
  keep on what spans the seam.

Accepted trade-off: the KB cannot version atomically with either
module, so brief skew between a module release and its KB update is
possible. Don't fight it with submodule machinery — the lifecycle's
`needs_review` flags and in-flight-window logic exist to label exactly
this.

## Adoption steps (in-repo)

1. Copy `scripts/okf.py` and the canonical `skills/` directory (the five
   `kb-*` skills) into the target repo.
2. Run `python scripts/okf.py init` at the repo root. This creates the
   `kb/` skeleton (SCHEMA.md, index.md, log.md, and the standard
   directories) and syncs `skills/` → `.claude/skills/` (Claude Code)
   and `.github/prompts/` (GitHub Copilot).
3. Merge the governance rules into the project's existing `CLAUDE.md` as
   a "Knowledge base" section — minimally the session protocol
   (SCHEMA.md → index.md → recent log before touching `kb/`) and the
   hard-rules list. Restate briefly in `AGENTS.md` /
   `.github/copilot-instructions.md` if non-Claude agents are used.
4. Carry over the committed-vs-generated convention: gitignore
   `.claude/skills/` (regenerated by `init` per clone) but **commit**
   `.github/prompts/` (Copilot reads them from the repo). Note in the
   project docs that fresh clones run `init` once.
5. Optionally add a CI step running `python scripts/okf.py lint` so
   frontmatter errors, dead links, and drift fail the build — for teams
   merging via PR, the full guardrail set is in
   [PR quality gates](/concepts/pr-quality-gates.md).

## Populating after bootstrap

There is no separate "initialization ingest": once bootstrapped, the
bundle grows by invoking `kb-ingest` repeatedly, and *update beats
create* keeps it converging instead of duplicating. Seed the SCHEMA.md
taxonomy before the first ingest (below) so early ingestions don't
churn it. When requirements live in an external tracker, follow
[ingesting requirements from ticket systems](/concepts/ingesting-requirements-from-ticket-systems.md).

## What to tune on adoption

- **Tag taxonomy and Domain section in the generated `kb/SCHEMA.md`** —
  written generically; set project-appropriate tags *before* the first
  real ingestion (hard rule: tags come from the taxonomy).
- **Directory layout** — SCHEMA.md permits renaming bundle directories
  to fit the domain; update SCHEMA.md and re-run `okf.py index` if so.
- Conventions in this bundle's own [SCHEMA.md](/SCHEMA.md) are the
  reference implementation to compare against.
