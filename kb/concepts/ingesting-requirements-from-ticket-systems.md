---
type: Concept
title: Ingesting Requirements from Ticket Systems
description: How to feed user stories from a work-item tracker (e.g. Azure DevOps) into the bundle — access paths, immutable captures, and the don't-mirror-the-backlog rule.
status: active
confidence: low
created: 2026-07-06
updated: 2026-07-06
review_after: 2026-08-06
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

## Review cadence

Requirements are volatile: give distilled requirement pages the
**1-month `review_after` offset regardless of confidence** (SCHEMA.md's
volatile-topic rule). `kb-review` is then the mechanism that notices
the bundle drifting from the backlog.
