---
type: Query
title: OKF as a Unified Knowledge Layer Across Enterprise Tools
description: Whether OKF can unify knowledge from Polarion, Azure DevOps, GitHub, Confluence and ServiceNow while preserving permissions and source-of-truth ownership — yes, as a federation of bundles, with three permission rules.
status: draft
lifecycle: draft
confidence: low
created: 2026-11-10
updated: 2026-11-10
stale_after: 2026-12-10
tags: [unverified]
sources:
  - resource: /sources/2026-11-10-governance-federation-cost-qa.md
    id: qa-2026-11-10
    title: "Q&A capture: governance, federation, token cost"
generated:
  by: claude-code/2.1.322
  at: 2026-11-10
---

# OKF as a Unified Knowledge Layer Across Enterprise Tools

> **Question:** Can OKF be used to create a unified knowledge layer
> across tools such as Polarion, Azure DevOps, GitHub, Confluence, and
> ServiceNow while preserving permissions and source-of-truth
> ownership? [qa-2026-11-10]

**Status:** draft, unverified — design reasoning, not a tested
integration.

## Answer

**Yes, as a federation — not one central store.**
[OKF](/concepts/open-knowledge-format.md) unifies *format and
provenance*: `type`, `sources[]` with a stable id and revision,
`generated`/`verified`, `status`, `stale_after`. It has **no permission
model, identity, sync or cross-bundle search**; those must come from
where each bundle is stored and from the source tools
[qa-2026-11-10].

### Three permission rules

1. **One bundle per access boundary.** A bundle inherits its git repo's
   permissions; per-page access inside one repo is not meaningful. The
   unified layer is a federation of bundles plus an organisation
   catalog holding metadata only. This generalises the same-repo /
   separate-repo choice in
   [adopting the bundle pattern](/concepts/adopting-the-bundle-pattern.md).
2. **No downgrade on capture.** A capture copies content, so it may only
   land in a bundle whose readers are a subset of the source's readers;
   otherwise link and summarise what the audience may see. A lint rule
   could require a page's classification to be at least as strict as
   every source it cites.
3. **Query as the user, never as a super-user.** Read bundles and call
   tool APIs/MCP servers with the asking user's identity; one
   all-seeing service account is the classic permission bypass of
   enterprise AI search [qa-2026-11-10].

### Source-of-truth ownership

Each tool stays the system of record — the same split as the
don't-mirror-the-backlog rule in
[ingesting requirements from ticket systems](/concepts/ingesting-requirements-from-ticket-systems.md):

| Tool | Stays owner of | Bundle cites |
|------|----------------|--------------|
| Polarion | Requirements, baselines under change control | Work-item id + revision/baseline; wiki is not the authority |
| Azure DevOps | Stories, status, sprints; code in Repos | Work-item id + `System.Rev`; blob pins for repos |
| GitHub | Code, PRs, decision records | Commit/blob pins via `okf.py drift` |
| Confluence | Hand-written pages | Page id + version; one owner per topic, never two editable wikis |
| ServiceNow | Incidents, changes, KB articles | Record id + update time; only recurring patterns, personal data removed |

The bundle earns its place on what spans tools (requirement → code →
test → incident), not on copying them. Freshness ties back by comparing
cited revisions and by a Definition-of-Done item "affected knowledge
pages updated" [qa-2026-11-10].

## What exists vs what is missing

GitHub and ADO Repos work natively through blob pins. The ADO Boards
pattern is documented, but its retrieval script was removed
(see [ado-workitem-sync](/entities/ado-workitem-sync.md)); connectors
for Boards, Polarion, Confluence and ServiceNow would need building.
Suggested next step: pilot one product domain spanning two tools before
building the organisation catalog.

## Related pages

- [Governance for AI-generated knowledge](/queries/governance-for-ai-generated-knowledge.md) —
  the approval and discoverability tiers that sit on top of this
  federation.
