---
type: Entity
title: openwiki
description: LangChain's openwiki — generates and incrementally maintains linked Markdown wikis (repo docs or a personal brain), run inside coding agents or as a standalone CLI, with evidence-tracked "Grounded Claims" and OKF v0.2 output — the claim-level, auto-reconciling counterpart to this bundle's page-level curated lifecycle.
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

# openwiki

A tool by langchain-ai that generates and maintains a linked Markdown
wiki for coding agents and humans; MIT-licensed, Node.js ≥ 22.22,
built on Deep Agents [openwiki-2026-11]. The recommended entry point is
a **coding-agent integration** (`openwiki integrations install <host>`
for Codex, Claude Code, OpenCode, Cursor, Copilot CLI, Kiro and
others): the host agent researches and writes pages with its own model
session, while openwiki's MCP tools own the durable page queue, claim
validation and finalization [openwiki-2026-11]. A **standalone CLI**
(its own documentation agent, fifteen selectable model providers) adds
personal wikis and unattended runs [openwiki-2026-11].

Two modes: *code mode* (default) writes an `openwiki/` directory,
maintains a block in root `AGENTS.md` and refreshes `CLAUDE.md` only
when one already exists, rewriting only its own
`<!-- OPENWIKI:START -->…<!-- OPENWIKI:END -->` block; *personal mode*
builds a "personal brain" in `~/.openwiki/wiki` from nine built-in
connectors — git repos, Gmail, Notion, X/Twitter, Slack, Hacker News,
Tavily web search, custom MCP servers, plus a LangSmith-traces
connector that enriches code wikis [openwiki-2026-11].

Repository pages carry **Grounded Claims**: each fact points at
versioned evidence (e.g. `repo://src/server.ts#L40-L82`) in
`openwiki/.claims/` sidecars; before an update every evidence version
is rechecked, and only facts whose evidence changed are "confirmed,
rewritten, or retired" — clean updates skip model work
[openwiki-2026-11]. Output is an **OKF v0.2 bundle in both modes**,
with `generated`, Claims-derived `sources`, and `verified` stamped only
after a page's Claims reconcile; `status`/`stale_after` are validated
when present but not described as emitted [openwiki-2026-11].
Personal-mode ingestion stays a two-stage pipeline (raw manifests under
`~/.openwiki/connectors/<name>/raw/`, then per-source agent synthesis),
and connector-derived facts are not claimed [openwiki-2026-11].
Scheduling is CI-based — GitHub Actions (optionally auto-merge), GitLab
or Bitbucket workflows that open docs PRs [openwiki-2026-11]. The
macOS LaunchAgents scheduling described at the first capture
[openwiki] is no longer mentioned.

## Relation to this bundle

Same problem as the OKF bundle, with closer answers than the 2026-07
capture suggested. Both now track staleness against evidence —
openwiki's Grounded Claims pin each fact to a versioned code range,
much as `blob:` pins plus `okf.py drift` do here (see
[okf-toolchain](/entities/okf-toolchain.md)) — and both emit OKF v0.2
[openwiki-2026-11]. The remaining split is **granularity and scope**:
openwiki tracks trust per *claim*, only for repository evidence, and
reconciles automatically; the bundle tracks trust per *page* through
[the knowledge lifecycle](/concepts/knowledge-lifecycle.md), covers
ephemeral sources that cannot be re-read (web pages, conversations),
and keeps deprecated knowledge instead of retracting it. The full
analysis is in
[openwiki vs the kb bundle](/comparisons/openwiki-vs-kb-bundle.md).

Convergences worth noting:

- Raw captures separated from synthesized knowledge — personal mode's
  `connectors/<name>/raw/` mirrors this bundle's immutable `/sources/`
  convention; code mode instead pins evidence in `openwiki/.claims/`,
  the counterpart of `blob:` pins [openwiki-2026-11].
- Agent-agnostic entry points — an `AGENTS.md` block (plus `CLAUDE.md`
  only if present) and installable skills plus MCP for coding agents
  [openwiki-2026-11], the same move this repo makes for Claude Code and
  Copilot.
- Both emit OKF v0.2 bundles, so in principle each can read the other's
  output — untested.
- Its scheduled CI-update workflow is a working instance of the
  scheduled-skills pattern recommended in
  [automating the lifecycle](/concepts/automating-the-lifecycle.md),
  and its docs-update PRs are exactly what
  [PR quality gates](/concepts/pr-quality-gates.md) would review — the
  auto-merge variant explicitly relies on branch checks and reviews
  [openwiki-2026-11].
