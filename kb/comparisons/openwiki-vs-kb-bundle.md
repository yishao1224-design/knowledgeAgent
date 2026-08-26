---
type: Comparison
title: openwiki vs the kb bundle
description: A generator product vs a curation discipline — where openwiki's regenerate-often bet and this bundle's lifecycle bet each win, their independent convergences, and what each could borrow.
status: active
confidence: medium
created: 2026-07-12
updated: 2026-07-12
review_after: 2026-10-12
tags: []
sources:
  - /sources/2026-07-12-openwiki.md
---

# openwiki vs the kb bundle

Analysis filed 2026-07-12 from a comparison discussion. Verdict: same
problem (an agent-maintained, agent-consumed knowledge base), opposite
ends — [openwiki](/entities/openwiki.md) is a **product that generates
docs**; the kb/ bundle is a **discipline the agent follows**. There is
no engine here: the hosting agent plus
[the lifecycle skill suite](/entities/lifecycle-skills.md) and
[okf.py](/entities/okf-toolchain.md) *are* the engine, while openwiki
ships its own TypeScript runtime, connector layer, and LLM-provider
integrations [1].

# Schema

| | openwiki | kb/ bundle ([OKF](/concepts/open-knowledge-format.md) + lifecycle) |
|---|---|---|
| Core bet | Regenerate often enough that staleness doesn't matter | Track staleness explicitly and curate |
| Knowledge model | Synthesized wiki pages, own format [1] | OKF v0.1 pages with typed frontmatter, readable by any plain OKF consumer |
| Lifecycle | Implicit — pages rewritten on the next run | Explicit: `draft → active → needs_review → deprecated → archived` with `review_after` |
| Staleness/drift | Scheduled re-runs (LaunchAgents, CI) [1] | Review queue (kb-review), `needs_review` flag, source-hash drift detection |
| Provenance | Raw connector manifests in `~/.openwiki/connectors/<name>/raw/` [1] | Immutable dated captures in `/sources/`, never edited |
| Ingestion | Built-in connectors: git, Gmail, Notion, X, HN, Tavily [1] | Conversational (kb-ingest) plus bespoke scripts (e.g. the retired [ado-workitem-sync](/entities/ado-workitem-sync.md)) |
| Deletion story | Overwritten on regeneration | Deprecate-don't-delete, supersession links, archive at zero inbound links |
| LLM dependency | Own provider layer + API keys [1] | None — runs inside whatever agent hosts the session |
| Automation | First-class: CI PRs, schedulers [1] | Session-driven; automation is a documented aspiration |

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
   in `AGENTS.md`/`CLAUDE.md` [1]; this repo maintains `CLAUDE.md`,
   `AGENTS.md`, Copilot instructions, and generated skill copies.
3. **Docs written for agent consumption first**, humans second.

## What each could borrow

- **Bundle ← openwiki: the scheduled CI refresh that opens a PR.**
  Running kb-review on a schedule with a PR as output is openwiki's
  update loop with better bookkeeping — precisely the pattern
  [automating the lifecycle](/concepts/automating-the-lifecycle.md)
  recommends (scheduled skills, no orchestration framework), gated by
  [PR quality gates](/concepts/pr-quality-gates.md). openwiki's
  `openwiki-update.yml` is proof the loop works in practice [1].
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

# Citations

[1] [openwiki README capture](/sources/2026-07-12-openwiki.md)
