---
type: Concept
title: Automating the Lifecycle (LangGraph and Alternatives)
description: Whether to put an orchestration framework like LangGraph in charge of the knowledge lifecycle — verdict, rules if you do, and the simpler scheduled-skills alternative.
status: active
confidence: low
created: 2026-07-06
updated: 2026-07-06
review_after: 2026-08-06
tags: [unverified]
---

# Automating the Lifecycle (LangGraph and Alternatives)

Should an orchestration framework (LangGraph, or similar graph/workflow
engines) manage the [knowledge lifecycle](/concepts/knowledge-lifecycle.md)?
**Mostly no — and never as the owner of lifecycle state.** The narrower
version that works: orchestration as a *thin driver* over the existing
skills-and-frontmatter system, for autonomous pipelines only.

# Schema

## Why the design resists an external state machine

- The lifecycle state machine (`draft → active → needs_review →
  deprecated → archived`) lives in **frontmatter**, not running code.
  That is the load-bearing decision: any agent or human can drive a
  transition because state travels with the data. A graph engine's
  checkpointed state would be a second representation that drifts from
  the frontmatter, and the graph becomes the only tool that knows how
  to garden the bundle — killing the any-agent-can-operate property.
- Most of what makes the system work is **judgment, not control flow**
  (distilling concepts, resolving contradictions, page-creation
  threshold calls) — encoded in the skills. An orchestration framework
  adds engineering surface without improving any of that.
- The parts that benefit from deterministic code are already
  deterministic: `okf.py lint/index/drift/log`.

## When orchestration earns its keep

An **autonomous production pipeline**: webhook-triggered ingestion
(e.g. per [ticket-system ingestion](/concepts/ingesting-requirements-from-ticket-systems.md)),
scheduled review-queue work, human approval before merge. There,
durable execution, retries, checkpointing, and human-in-the-loop
interrupts (LangGraph's `interrupt()` maps to kb-ingest's
"discuss before writing" gate) are real needs.

Three rules keep it honest:

1. **The bundle stays the single source of truth** — nodes read
   `status` from frontmatter at run start and write it back; the graph
   never persists lifecycle state beyond a single run.
2. **Nodes call `okf.py` for everything mechanical**; the LLM is used
   only for judgment steps.
3. **Git is the transaction boundary** — each run ends in a branch +
   PR gated by [PR quality gates](/concepts/pr-quality-gates.md), so a
   half-finished run cannot corrupt the bundle.

## The simpler alternative to try first

The lifecycle logic already exists as prose skills. **Schedule the
existing skills headless** — cron / GitHub Actions / a scheduled cloud
agent running `kb-review` weekly and `kb-lint` nightly via a headless
agent session that opens a PR with its changes. This yields most of the
autonomous pipeline with no new code, and the skills remain the single
implementation used both interactively and on schedule. Reach for a
graph framework only when a concrete need appears (multi-step
webhook-triggered flows with mid-run approval gates), and even then as
a driver, not a replacement.
