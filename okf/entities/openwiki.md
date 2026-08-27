---
type: Entity
title: openwiki
description: LangChain's TypeScript CLI that auto-generates and schedule-refreshes agent-optimized wikis (repo docs or a personal brain) from pluggable connectors — the regenerate-often counterpart to this bundle's curated lifecycle.
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

# openwiki

A CLI tool by langchain-ai that generates and maintains documentation
wikis optimized for AI-agent consumption [openwiki]. Two modes: *code mode*
writes an `openwiki/` docs directory into the current repo and injects
a pointer block into root `AGENTS.md`/`CLAUDE.md` (rewriting only its
own `<!-- OPENWIKI:START -->…<!-- OPENWIKI:END -->` block); *personal
mode* builds a "personal brain" wiki in `~/.openwiki/wiki` fed by
connectors — git repos, Gmail, Notion, X/Twitter, Hacker News, Tavily
web search [openwiki].

Its architecture is a deterministic pipeline: connectors dump raw
manifests under `~/.openwiki/connectors/<name>/raw/`, then per-source
LLM agent runs synthesize them into wiki pages [openwiki]. It carries its own
LLM-provider layer (OpenAI, Anthropic, OpenRouter, Fireworks, Baseten,
NVIDIA NIM, OpenAI-compatible/LiteLLM) and its own scheduling: macOS
LaunchAgents locally, or GitHub/GitLab CI workflows that open PRs with
documentation updates [openwiki].

## Why this page is flagged

Set `needs_review` on 2026-08-27: a later look at the project found the
README materially changed since the 2026-07-12 capture below, including
OKF v0.2 output, evidence-tracked "Grounded Claims", and coding-agent
integrations. The claims on this page predate all of that and need a
fresh capture — kb-ingest work. See the same note on
[openwiki vs the kb bundle](/comparisons/openwiki-vs-kb-bundle.md).

## Relation to this bundle

Same problem as the OKF bundle — an agent-maintained, agent-consumed
knowledge base — solved with the opposite bet: openwiki treats
knowledge as **cheap and regenerable** (staleness is handled by
scheduled re-synthesis, with no per-page lifecycle), where the bundle
treats it as **accumulated and audited** via
[the knowledge lifecycle](/concepts/knowledge-lifecycle.md). The full
analysis is in
[openwiki vs the kb bundle](/comparisons/openwiki-vs-kb-bundle.md).

Convergences worth noting:

- Raw captures separated from synthesized knowledge — its
  `connectors/<name>/raw/` mirrors this bundle's immutable
  `/sources/` convention [openwiki].
- Agent-agnostic entry points (`AGENTS.md` + `CLAUDE.md` blocks),
  the same move this repo makes for Claude Code and Copilot.
- Its scheduled CI-update workflow is a working instance of the
  scheduled-skills pattern recommended in
  [automating the lifecycle](/concepts/automating-the-lifecycle.md),
  and its docs-update PRs are exactly what
  [PR quality gates](/concepts/pr-quality-gates.md) would review.
