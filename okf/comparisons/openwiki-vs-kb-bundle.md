---
type: Comparison
title: openwiki vs the kb bundle
description: A generator product vs a curation discipline — openwiki reconciles per-claim evidence automatically, this bundle curates per-page trust through a lifecycle; where each wins, how they converged (both now emit OKF v0.2), and what each could borrow.
status: stable
lifecycle: active
confidence: medium
created: 2026-07-12
updated: 2026-11-10
stale_after: 2026-12-10
tags: []
sources:
  - resource: /sources/2026-07-12-openwiki.md
    id: openwiki
    title: openwiki README capture (2026-07-12)
  - resource: /sources/2026-11-10-openwiki.md
    id: openwiki-2026-11
    title: openwiki README capture (2026-11-10)
generated:
  by: claude-code/2.1.322
  at: 2026-11-10
---

# openwiki vs the kb bundle

Analysis first filed 2026-07-12 from a comparison discussion and
re-verified 2026-11-10 against a fresh capture, which overturned
several of the original contrasts (openwiki had been "own format, no
per-page lifecycle"). Verdict still: same problem — an agent-maintained,
agent-consumed knowledge base — approached from different ends, but the
ends are much closer than they were. [openwiki](/entities/openwiki.md)
is a **product that generates and reconciles docs**; the OKF bundle is
a **discipline the agent follows**. There is no engine here: the
hosting agent plus [the lifecycle skill suite](/entities/lifecycle-skills.md)
and [okf.py](/entities/okf-toolchain.md) *are* the engine. openwiki
ships its own runtime (a Deep Agents CLI), connector layer and provider
integrations — though its recommended mode now runs *inside* the coding
agent, which writes the pages while openwiki's MCP tools keep the books
[openwiki-2026-11].

# Schema

| | openwiki | the OKF bundle ([OKF](/concepts/open-knowledge-format.md) + lifecycle) |
|---|---|---|
| Core bet | Reconcile continuously: re-synthesize only what evidence says changed [openwiki-2026-11] | Track trust explicitly and curate |
| Knowledge model | OKF v0.2 bundles in both modes, with `generated` / `verified` / `sources` front matter [openwiki-2026-11] | OKF v0.2 pages with typed frontmatter plus the `lifecycle` extension |
| Unit of trust | The **claim**: Grounded Claims confirmed, revised or retired; a page gets `verified` only after its Claims reconcile; no draft/deprecated states [openwiki-2026-11] | The **page**: `draft → active → needs_review → deprecated → archived`, with `stale_after` |
| Staleness/drift | Evidence-version check on every Claim before each update, at line-range grain (repo wikis only) [openwiki-2026-11] | Whole-file `blob:` pins checked by `okf.py drift` where the repo can answer; review queue, `needs_review` flag and `stale_after` expiry otherwise |
| Provenance | Code: Claims sidecars in `openwiki/.claims/` pointing at `repo://path#Lx-Ly`, projected into `sources`; personal: raw connector manifests [openwiki-2026-11] | Immutable dated captures in `/sources/`, never edited, plus `blob:`-pinned live repo files |
| Ingestion | Nine built-in connectors (git, Gmail, Notion, X, Slack, HN, Tavily, custom MCP, LangSmith traces) [openwiki-2026-11] | Conversational (kb-ingest), any source an agent can read; bespoke scripts where needed (e.g. the retired [ado-workitem-sync](/entities/ado-workitem-sync.md)) |
| Deletion story | Stale facts retracted on update; `--init` replaces the whole wiki and its Claims; no deprecation or archive [openwiki-2026-11] | Deprecate-don't-delete, supersession links, archive at zero inbound links |
| LLM dependency | None inside a coding agent (uses the host's model session); the standalone CLI has its own fifteen-provider layer [openwiki-2026-11] | None — runs inside whatever agent hosts the session |
| Automation | First-class: scheduled CI jobs (GitHub, GitLab, Bitbucket) open docs PRs, optional auto-merge gated by branch checks [openwiki-2026-11] | Session-driven; automation is a documented aspiration |

The remaining philosophical split follows the ground truth. openwiki's
flagship use is codebase documentation, where the code is always
available to re-check against, so it can *retract* a fact once its
evidence changes instead of keeping it as history [openwiki-2026-11].
The bundle's sources can be ephemeral (a web page, a conversation, a
verification already performed), so it snapshots immutably and audits
instead — the same index-vs-corpus distinction drawn in
[codebase-memory-mcp vs the kb wiki](/comparisons/codebase-memory-mcp-vs-kb-wiki.md),
with openwiki sitting between the two: an LLM-synthesized corpus kept
honest like an index. Its Claims stop at repository evidence;
connector-derived facts are not claimed [openwiki-2026-11].

## Independent convergences

Ideas both projects arrived at separately:

1. **Raw evidence separated from synthesis** — personal mode's
   `connectors/<name>/raw/` vs `/sources/`; code mode's Claims
   sidecars vs `blob:` pins [openwiki-2026-11].
2. **Evidence-driven staleness** — Grounded Claims and `okf.py drift`
   both fire on a change to the evidence rather than on the clock.
3. **OKF v0.2 as the output format** — so in principle each can read
   the other's bundles; untested.
4. **Agent-agnostic entry points** — openwiki maintains a marker block
   in `AGENTS.md` (and `CLAUDE.md` only when one exists) and installs
   skills plus MCP into coding agents [openwiki-2026-11]; this repo
   maintains `CLAUDE.md`, `AGENTS.md`, Copilot instructions and
   generated skill copies.
5. **Readers: agents first, humans too** — openwiki adds a graph
   visualizer for people [openwiki-2026-11]; the bundle optimizes for
   agent reading and stays plain markdown.

## What each could borrow

- **Bundle ← openwiki: claim-level evidence pins.** `blob:` pins a
  whole file, so any edit re-opens the page; openwiki pins line ranges
  per fact and can tell *which* claim moved [openwiki-2026-11].
- **Bundle ← openwiki: the scheduled CI refresh that opens a PR.**
  Running kb-review on a schedule with a PR as output is openwiki's
  update loop with page-level bookkeeping — the pattern
  [automating the lifecycle](/concepts/automating-the-lifecycle.md)
  recommends, gated by [PR quality gates](/concepts/pr-quality-gates.md).
  openwiki's `examples/openwiki-update.yml` shows the loop working, and
  its auto-merge variant explicitly relies on branch checks and reviews
  [openwiki-2026-11].
- **openwiki ← bundle: a deprecation story.** Grounded Claims can retire
  a stale fact [openwiki-2026-11], but nothing described keeps "wrong
  but historically important" knowledge or records that two sources
  contradict each other — the lifecycle's supersession links and
  `contested` handling do.

## Friction if used together

Both write root agent-guidance files — openwiki an `AGENTS.md` block
(and `CLAUDE.md` only if present) [openwiki-2026-11] — and both would
claim "the knowledge base" role in a repo. If a project adopting the
bundle pattern (see
[adopting the bundle pattern](/concepts/adopting-the-bundle-pattern.md))
also ran openwiki code mode, the routing rule would mirror the
codebase-memory-mcp resolution: generated, code-derived docs belong to
openwiki's side (reconciled against the code); decisions, external
facts and verified knowledge go to the bundle. Both being OKF v0.2
bundles makes a federated read possible. Unresolved and untested —
noted as an open question, not a plan.
