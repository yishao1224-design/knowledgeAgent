---
type: Comparison
title: codebase-memory-mcp vs the kb wiki
description: Why a derived code-knowledge graph and a curated OKF bundle are complementary layers, where they overlap (ADRs), and a phased integration plan.
status: stable
lifecycle: active
confidence: medium
created: 2026-07-06
updated: 2026-11-10
stale_after: 2026-12-10
tags: []
sources:
  - resource: /sources/2026-07-06-codebase-memory-mcp.md
    id: codebase-memory-mcp
    title: codebase-memory-mcp README capture (2026-07-06)
  - resource: /sources/2026-11-10-codebase-memory-mcp.md
    id: codebase-memory-mcp-2026-11
    title: codebase-memory-mcp README capture (2026-11-10)
generated:
  by: claude-code/2.1.322
  at: 2026-11-10
---

# codebase-memory-mcp vs the kb wiki

Analysis filed 2026-07-06 from a design discussion; re-verified
2026-11-10 against a fresh capture. Verdict unchanged:
**complementary, not competing** — they solve opposite halves of the
agent-memory problem, and each covers the other's weakness.

# Schema

| | [codebase-memory-mcp](/entities/codebase-memory-mcp.md) | the OKF bundle ([OKF](/concepts/open-knowledge-format.md) + lifecycle) |
|---|---|---|
| Nature | **Index** (cache) | **Corpus** (asset) |
| Content | What the repository *is*: definitions, call graphs, imports, plus document sections and infrastructure relationships [codebase-memory-mcp-2026-11] | What we *decided and learned*: rationale, external facts, contradictions |
| Ground truth | The repository itself | Verification work already done |
| Regenerable? | Almost — the code graph can be rebuilt, but the `manage_adr` record and ingested traces cannot [codebase-memory-mcp-2026-11] | No — hence immutable sources, deprecate-don't-delete |
| Staleness model | Mechanical: session-scoped git polling, incremental re-index [codebase-memory-mcp-2026-11] | Mechanical for pinned repo files (`okf.py drift`), semantic otherwise: `stale_after` + [kb-review](/entities/lifecycle-skills.md), one to several months |
| Storage | SQLite graph in a cache dir [codebase-memory-mcp-2026-11] | Portable markdown, git-versioned, human-readable |

The division-of-labor rule that follows: **code-structure questions go
to the graph; decisions, rationale, and external knowledge go to the
bundle.** Filing code-structure facts as concepts is the main failure
mode — they change with every commit while the review cadence in
[the knowledge lifecycle](/concepts/knowledge-lifecycle.md) operates in
weeks to months.

## Friction points

1. **ADRs have two candidate homes.** The tool's `manage_adr` keeps one
   decision record next to its index, deleted with the project
   [codebase-memory-mcp-2026-11]; the bundle is built for exactly that
   content with a better deal (portable, versioned, lifecycle-managed,
   readable by any OKF consumer, never silently deleted). Resolution:
   the bundle wins; don't use `manage_adr`. Since the graph now indexes
   ADR metadata from documentation files in the repo, decision pages in
   an in-repo bundle could still appear in the graph — the two can
   coexist without a second record.
2. **Divergent staleness clocks** are a feature only if content is
   routed to the right side (see rule above).
3. **Trust boundary**: a `curl | bash` installer that configures up to
   46 client surfaces, including skills, agent profiles and default-on
   hooks, plus an auto-started daemon [codebase-memory-mcp-2026-11].
   Releases are signed, SLSA-3 and checksum-verified; still vet and pin
   before adoption.

## Integration opportunity: code-aware review triggers

**Partly built as of 2026-08-27, without the MCP server.** This section
originally proposed a `code_refs:` extension key plus a call to the
graph's `detect_changes` [codebase-memory-mcp] to demote affected
concepts the moment referenced symbols change. What shipped instead
achieves the same trigger with no dependency: a `sources` entry pins a
file with `blob:`, and `okf.py drift` compares it against git — see
[okf.py](/entities/okf-toolchain.md). Same idea, cheaper, and OKF-legal
by riding the standard `sources` field (the `blob:` key inside an entry
is itself an extension key that plain consumers ignore).

What the graph would still add is **granularity**: `drift` fires on any
change to a whole file, where the graph can tell which specific symbols
a change touches — `detect_changes` for uncommitted changes,
`compare_graphs` between indexed snapshots
[codebase-memory-mcp-2026-11]. For pages about one function in a large,
busy file that difference is the gap between a useful trigger and
noise — which is the case that would justify Phase 1 below.

## Adoption plan (not started as of 2026-11-10)

- **Phase 0 — coexist**: install the MCP server (after vetting) in
  repos with real code; add the routing rule to agent instructions.
- **Phase 1 — symbol-level review triggers**: only if file-level
  `blob:` pins prove too noisy — swap the file pin for a symbol check
  against `compare_graphs` since the pin.
- **Phase 2 — one home for decisions**: skip `manage_adr`; ingest any
  existing ADRs as a `Decision` concept type (register the type in
  [SCHEMA.md](/SCHEMA.md) first — it is not in the registry yet).

Caveat: for the knowledgeAgent repo itself the pairing is low-value
(one Python script; the graph would mostly index the bundle's own
markdown); it pays off where the bundle pattern is deployed inside an
actual codebase.
