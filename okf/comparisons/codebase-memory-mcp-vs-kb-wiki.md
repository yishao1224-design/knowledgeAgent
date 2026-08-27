---
type: Comparison
title: codebase-memory-mcp vs the kb wiki
description: Why a derived code-knowledge graph and a curated OKF bundle are complementary layers, where they overlap (ADRs), and a phased integration plan.
status: stable
lifecycle: active
confidence: medium
created: 2026-07-06
updated: 2026-08-27
stale_after: 2026-10-06
tags: []
sources:
  - resource: /sources/2026-07-06-codebase-memory-mcp.md
    id: codebase-memory-mcp
    title: codebase-memory-mcp README capture
---

# codebase-memory-mcp vs the kb wiki

Analysis filed 2026-07-06 from a design discussion. Verdict:
**complementary, not competing** — they solve opposite halves of the
agent-memory problem, and each covers the other's weakness.

# Schema

| | [codebase-memory-mcp](/entities/codebase-memory-mcp.md) | the OKF bundle ([OKF](/concepts/open-knowledge-format.md) + lifecycle) |
|---|---|---|
| Nature | **Index** (cache) | **Corpus** (asset) |
| Content | What the code *is*: definitions, call graphs, imports [codebase-memory-mcp] | What we *decided and learned*: rationale, external facts, contradictions |
| Ground truth | The code itself | Verification work already done |
| Regenerable? | Fully — delete DB, re-index | No — hence immutable sources, deprecate-don't-delete |
| Staleness model | Mechanical: git watcher, seconds [codebase-memory-mcp] | Mechanical for pinned repo files (`okf.py drift`), semantic otherwise: `stale_after` + [kb-review], months |
| Storage | SQLite graph in a cache dir [codebase-memory-mcp] | Portable markdown, git-versioned, human-readable |

The division-of-labor rule that follows: **code-structure questions go
to the graph; decisions, rationale, and external knowledge go to the
bundle.** Filing code-structure facts as concepts is the main failure
mode — they rot in seconds while the review cadence in
[the knowledge lifecycle](/concepts/knowledge-lifecycle.md) operates in
months.

## Friction points

1. **ADRs have two candidate homes.** The tool's `manage_adr` stores
   decision records in its own storage [codebase-memory-mcp]; the bundle is built for
   exactly that content with a better deal (portable, versioned,
   lifecycle-managed, readable by any OKF consumer). Resolution: the
   wins; don't use `manage_adr`.
2. **Divergent staleness clocks** are a feature only if content is
   routed to the right side (see rule above).
3. **Trust boundary**: single-binary `curl | bash` installer that
   auto-rewrites 11 coding agents' configs [codebase-memory-mcp] — vet and pin before
   adoption.

## Integration opportunity: code-aware review triggers

**Partly built as of 2026-08-27, without the MCP server.** This section
originally proposed a `code_refs:` extension key plus a call to the
graph's `detect_changes` [codebase-memory-mcp] to demote affected
concepts the moment referenced symbols change. What shipped instead
achieves the same trigger with no dependency: a `sources` entry pins a
file with `blob:`, and `okf.py drift` compares it against git — see
[okf.py](/entities/okf-toolchain.md). Same idea, cheaper, and OKF-legal
by riding the standard `sources` field rather than a private key.

What the graph would still add is **granularity**: `drift` fires on any
change to a whole file, where `detect_changes` fires on the specific
symbol a page actually cites. For pages about one function in a large,
busy file that difference is the gap between a useful trigger and
noise — which is the case that would justify Phase 1 below.

## Adoption plan (not yet started as of 2026-07-06)

- **Phase 0 — coexist**: install the MCP server (after vetting) in
  repos with real code; add the routing rule to agent instructions.
- **Phase 1 — symbol-level review triggers**: only if file-level
  `blob:` pins prove too noisy — swap the file pin for a
  `detect_changes` check on the cited symbol.
- **Phase 2 — one home for decisions**: skip `manage_adr`; ingest any
  existing ADRs as a `Decision` concept type.

Caveat: for the knowledgeAgent repo itself the pairing is moot (no
code to index); it pays off where the bundle pattern is deployed inside
an actual codebase.
