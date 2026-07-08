---
type: Concept
title: Ingesting Requirements from Ticket Systems
description: How to feed user stories from a work-item tracker (e.g. Azure DevOps) into the bundle — access paths, immutable captures, and the don't-mirror-the-backlog rule.
status: active
confidence: low
created: 2026-07-06
updated: 2026-07-08
review_after: 2026-08-08
tags: [unverified]
---

# Ingesting Requirements from Ticket Systems

When business requirements live in a work-item tracker (Azure DevOps
Boards, Jira, …), the bundle ingests from it like any other source —
but the tracker **stays the system of record** for stories, status,
sprints, and assignment. The bundle's job is the durable knowledge
distilled from those stories, maintained through the
[knowledge lifecycle](/concepts/knowledge-lifecycle.md). Bootstrap the
bundle first per
[adopting the bundle pattern](/concepts/adopting-the-bundle-pattern.md);
in particular, seed the tag taxonomy with requirement-shaped tags
(`requirement`, `business-rule`, `persona`, per-module tags) before the
first ingest.

# Schema

## The don't-mirror-the-backlog rule

A bundle that mirrors every work item is permanently stale and adds
nothing over the tracker. Split responsibilities:

| Lives in the tracker | Lives in the bundle |
|----------------------|---------------------|
| Story status, sprint, assignment, acceptance-criteria churn | Business rules and constraints distilled from stories (`Concept`) |
| The authoritative current story text | Personas, external systems, features (`Entity`) |
| — | Raw story text *as fetched*, only as immutable dated `/sources/` captures backing the pages above |

## Access paths to Azure DevOps (in order of preference)

1. **Azure DevOps MCP server** — Microsoft publishes an official one
   (`microsoft/azure-devops-mcp`); the agent queries work items
   directly, so "ingest epic 1234 and its children" is a single
   request. Best for recurring use.
2. **`az boards` CLI** (Azure CLI + `azure-devops` extension) — the
   agent runs `az boards work-item show --id N` or WIQL queries during
   ingestion. No MCP setup; needs `az login` or a PAT.
3. **Paste/export into chat** — zero setup, fine occasionally, but the
   fetch time and provenance live only in the capture file you write.

Record the org/project and where the PAT lives in the project's
`CLAUDE.md` so sessions don't rediscover it.

## Capture mechanics and re-ingestion

Fetched story text is snapshotted to
`/sources/YYYY-MM-DD-ado-<epic-or-story-slug>.md` with its hash, per
the immutability rule in [SCHEMA.md](/SCHEMA.md). When a story changes
in the tracker, re-ingest under a **new dated file** — the sequence of
captures becomes an audit trail of how the requirement evolved, and
`okf.py drift` guards the old ones.

## Keeping code knowledge fresh

The freshness question for a distilled requirement/behavior page is
*when does a code change make this page wrong* — and time can't answer
it. A page goes stale the moment a story ships, not on a fixed cadence.
The work item that drove the change **is** the freshness signal, so tie
the KB refresh to it rather than to the clock:

- **Definition-of-Done gate.** Add "affected `kb/` pages updated or
  re-ingested" to a story's Definition of Done, the way
  [PR quality gates](/concepts/pr-quality-gates.md) make conformance a
  merge condition. The obligation then lives where the change lives —
  the story doesn't close until the knowledge it changed is current.
- **Trace the link both ways.** Have the story reference the concept
  page(s) it affects, and/or the page's `sources` cite the story's
  dated capture. A closed story can then flag exactly those pages for
  [kb-review](/concepts/knowledge-lifecycle.md) — change-triggered, not
  memory-triggered.
- **`review_after` is only the backstop.** Per the scoped cadence in
  [SCHEMA.md](/SCHEMA.md), story-driven pages lengthen `review_after`
  well past the baseline and rely on the DoD trigger as primary; the
  timer just catches what slips the process — e.g. an external fact
  that changed with no story behind it.

This keeps `active` an honest promise without a permanently-noisy
queue: the story stream refreshes what actually changed, and the
backstop covers the rest.

## Review cadence

Distilled requirement pages are **story-driven**, so treat
`review_after` as the backstop and the story's Definition of Done as
the primary freshness trigger (see *Keeping code knowledge fresh* above
and the scoped cadence in [SCHEMA.md](/SCHEMA.md)). `kb-review` still
works the queue — for whatever the process misses, and for pages that
drift from external volatility rather than a tracked story.
