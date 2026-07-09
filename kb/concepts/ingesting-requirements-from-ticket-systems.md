---
type: Concept
title: Ingesting Requirements from Ticket Systems
description: How to feed user stories from a work-item tracker (e.g. Azure DevOps) into the bundle — access paths, immutable captures, and the don't-mirror-the-backlog rule.
status: active
confidence: low
created: 2026-07-06
updated: 2026-07-09
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

## Access paths to Azure DevOps (pick by use shape, not one ranking)

Field experience (first real retrieval pipeline, CRM project, 2026-07)
refined the original MCP-first ranking: the right access path depends
on whether the step is *judgment* or *mechanical* — the same
code-vs-judgment split the bundle applies to its own
[toolchain](/entities/okf-toolchain.md) vs skills.

1. **Interactive identification and ad-hoc queries → MCP server**
   (`microsoft/azure-devops-mcp`). "Find the story about the WOLI
   layout change", exploratory WIQL, targeted parent-feature lookups
   mid-analysis — conversation-shaped work where the agent's judgment
   is the point.
2. **Recurring retrieval pipeline → a script calling the REST API with
   a PAT.** Fetch + attachment download + normalization + rev-stamping
   is deterministic; putting it in a prompt means an LLM re-executes
   (and can violate) every mechanical rule per run — in practice the
   prompt accumulates defensive rules that are scar tissue from tool
   misbehavior. A script with a version-pinned `api-version` is the
   most stable interface, needs no CLI install, and the skill shrinks
   to "run the script, report what it says." This bundle's concrete
   implementation is the
   [ado-workitem-sync toolchain](/entities/ado-workitem-sync.md).
3. **`az boards` CLI** — middle ground when a script is overkill; no
   MCP setup, needs `az login` or a PAT; comments/attachments get
   awkward.
4. **Paste/export into chat** — zero setup, fine occasionally, but the
   fetch time and provenance live only in the capture file you write.

Record the org/project and where the PAT lives in the project's
`CLAUDE.md` so sessions don't rediscover it.

When the local retrieval cache is *mutable* (a refresh overwrites the
raw payload rather than adding a dated capture), preserve provenance
mechanically: record the tracker's revision number (ADO `System.Rev`)
plus a retrieval timestamp in the normalized payload, and stamp any
derived analysis with the revision it was based on. "Is this analysis
stale?" then becomes a mechanical rev comparison — the tracker-flavored
equivalent of the sha256 drift check.

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

The end-to-end pipeline that operationalizes this — query the bundle at
analysis time, flag contradictions immediately, ingest only what
shipped after verification — is the
[user story analysis workflow](/concepts/user-story-analysis-workflow.md).

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
