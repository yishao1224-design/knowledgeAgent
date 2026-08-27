---
type: Comparison
title: openwiki vs the kb bundle
description: A generator product vs a curation discipline — where openwiki's regenerate-often bet and this bundle's lifecycle bet each win, their independent convergences, and what each could borrow.
status: stable
lifecycle: needs_review
confidence: medium
created: 2026-07-12
updated: 2026-08-27
stale_after: 2026-10-12
tags: []
sources:
  - resource: /sources/2026-07-12-openwiki.md
    id: openwiki
    title: openwiki README capture
---

# openwiki vs the kb bundle
## Why this page is flagged

Set `needs_review` on 2026-08-27. The openwiki side of this page is
sourced from a capture taken 2026-07-12; a later look at the project
found its README materially changed — it now emits OKF v0.2 bundles
with `status`/`stale_after`, tracks evidence with per-claim "Grounded
Claims" sidecars, and installs into coding agents including Claude
Code. Several claims below ("own format", "lifecycle: implicit", "no
per-page lifecycle") are contradicted by that. The bundle side has been
corrected in place; the openwiki side needs a fresh capture before it
can be trusted, which is kb-ingest work, not a lint fix.

Analysis filed 2026-07-12 from a comparison discussion. Verdict: same
problem (an agent-maintained, agent-consumed knowledge base), opposite
ends — [openwiki](/entities/openwiki.md) is a **product that generates
docs**; the OKF bundle is a **discipline the agent follows**. There is
no engine here: the hosting agent plus
[the lifecycle skill suite](/entities/lifecycle-skills.md) and
[okf.py](/entities/okf-toolchain.md) *are* the engine, while openwiki
ships its own TypeScript runtime, connector layer, and LLM-provider
integrations [openwiki].

# Schema

| | openwiki | the OKF bundle ([OKF](/concepts/open-knowledge-format.md) + lifecycle) |
|---|---|---|
| Core bet | Regenerate often enough that staleness doesn't matter | Track staleness explicitly and curate |
| Knowledge model | Synthesized wiki pages, own format [openwiki] | OKF v0.2 pages with typed frontmatter, readable by any plain OKF consumer |
| Lifecycle | Implicit — pages rewritten on the next run | Explicit: `draft → active → needs_review → deprecated → archived` in a `lifecycle` key, with `stale_after` |
| Staleness/drift | Scheduled re-runs (LaunchAgents, CI) [openwiki] | Pinned-file drift (`okf.py drift`) where the repo can answer; review queue (kb-review), `needs_review` flag, `stale_after` expiry otherwise |
| Provenance | Raw connector manifests in `~/.openwiki/connectors/<name>/raw/` [openwiki] | Immutable dated captures in `/sources/`, never edited, plus `blob:`-pinned live repo files |
| Ingestion | Built-in connectors: git, Gmail, Notion, X, HN, Tavily [openwiki] | Conversational (kb-ingest) plus bespoke scripts (e.g. the retired [ado-workitem-sync](/entities/ado-workitem-sync.md)) |
| Deletion story | Overwritten on regeneration | Deprecate-don't-delete, supersession links, archive at zero inbound links |
| LLM dependency | Own provider layer + API keys [openwiki] | None — runs inside whatever agent hosts the session |
| Automation | First-class: CI PRs, schedulers [openwiki] | Session-driven; automation is a documented aspiration |

The philosophical split follows the ground truth: openwiki's flagship
use is codebase documentation, where the code is always available to
re-synthesize from, so throwing pages away is safe. The bundle's
sources can be ephemeral (a web page, a conversation, a verification
already performed), so it snapshots immutably and audits instead — the
same index-vs-corpus distinction drawn in
[codebase-memory-mcp vs the kb wiki](/comparisons/codebase-memory-mcp-vs-kb-wiki.md),
with openwiki sitting between the two: an LLM-synthesized corpus
managed like an index.

## Independent convergences

Three structural ideas both projects arrived at separately:

1. **Raw captures separated from synthesis** — `connectors/<name>/raw/`
   vs `/sources/`.
2. **Agent-agnostic entry points** — openwiki maintains marker blocks
   in `AGENTS.md`/`CLAUDE.md` [openwiki]; this repo maintains `CLAUDE.md`,
   `AGENTS.md`, Copilot instructions, and generated skill copies.
3. **Docs written for agent consumption first**, humans second.

## What each could borrow

- **Bundle ← openwiki: the scheduled CI refresh that opens a PR.**
  Running kb-review on a schedule with a PR as output is openwiki's
  update loop with better bookkeeping — precisely the pattern
  [automating the lifecycle](/concepts/automating-the-lifecycle.md)
  recommends (scheduled skills, no orchestration framework), gated by
  [PR quality gates](/concepts/pr-quality-gates.md). openwiki's
  `openwiki-update.yml` is proof the loop works in practice [openwiki].
- **openwiki ← bundle: a deprecation story.** Regeneration has no
  answer to "this page is wrong but historically important" or "these
  sources contradict each other" — the lifecycle's supersession links
  and `contested` handling do.

## Friction if used together

Both want to own root `AGENTS.md`/`CLAUDE.md` guidance and both would
claim "the knowledge base" role in a repo. If a project adopting the
bundle pattern (see
[adopting the bundle pattern](/concepts/adopting-the-bundle-pattern.md))
also ran openwiki code mode, the routing rule would need to mirror the
codebase-memory-mcp resolution: generated code-derived docs are an
index (regenerable, openwiki's side); decisions, external facts, and
verified knowledge go to the bundle. Unresolved and untested — noted
as an open question, not a plan.
