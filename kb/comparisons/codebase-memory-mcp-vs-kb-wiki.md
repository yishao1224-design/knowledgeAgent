---
type: Comparison
title: codebase-memory-mcp vs the kb wiki
description: Why a derived code-knowledge graph and a curated OKF bundle are complementary layers, where they overlap (ADRs), and a phased integration plan.
status: active
confidence: medium
created: 2026-07-06
updated: 2026-07-06
review_after: 2026-10-06
tags: []
sources:
  - /sources/2026-07-06-codebase-memory-mcp.md
---

# codebase-memory-mcp vs the kb wiki

Analysis filed 2026-07-06 from a design discussion. Verdict:
**complementary, not competing** — they solve opposite halves of the
agent-memory problem, and each covers the other's weakness.

# Schema

| | [codebase-memory-mcp](/entities/codebase-memory-mcp.md) | kb/ bundle ([OKF](/concepts/open-knowledge-format.md) + lifecycle) |
|---|---|---|
| Nature | **Index** (cache) | **Corpus** (asset) |
| Content | What the code *is*: definitions, call graphs, imports [1] | What we *decided and learned*: rationale, external facts, contradictions |
| Ground truth | The code itself | Verification work already done |
| Regenerable? | Fully — delete DB, re-index | No — hence immutable sources, deprecate-don't-delete |
| Staleness model | Mechanical: git watcher, seconds [1] | Semantic: `review_after` + [kb-review], months |
| Storage | SQLite graph in a cache dir [1] | Portable markdown, git-versioned, human-readable |

The division-of-labor rule that follows: **code-structure questions go
to the graph; decisions, rationale, and external knowledge go to the
bundle.** Filing code-structure facts as concepts is the main failure
mode — they rot in seconds while the review cadence in
[the knowledge lifecycle](/concepts/knowledge-lifecycle.md) operates in
months.

## Friction points

1. **ADRs have two candidate homes.** The tool's `manage_adr` stores
   decision records in its own storage [1]; the bundle is built for
   exactly that content with a better deal (portable, versioned,
   lifecycle-managed, readable by any OKF consumer). Resolution: kb/
   wins; don't use `manage_adr`.
2. **Divergent staleness clocks** are a feature only if content is
   routed to the right side (see rule above).
3. **Trust boundary**: single-binary `curl | bash` installer that
   auto-rewrites 11 coding agents' configs [1] — vet and pin before
   adoption.

## Integration opportunity: code-aware review triggers

The bundle's `review_after` is purely time-based. Concepts that are
*about* code could carry an extension field, e.g.
`code_refs: [src/auth/login.py::AuthFlow]`, and a review step could
query the graph's `detect_changes` [1] to demote affected concepts to
`needs_review` immediately when referenced symbols change — the same
pattern as the bundle's source-hash drift detection, extended from
documents to code. OKF-legal (extension key) and degrades gracefully
without the MCP server.

## Adoption plan (not yet started as of 2026-07-06)

- **Phase 0 — coexist**: install the MCP server (after vetting) in
  repos with real code; add the routing rule to agent instructions.
- **Phase 1 — code-aware reviews**: add `code_refs` to the schema and
  a `detect_changes` check to the review workflow.
- **Phase 2 — one home for decisions**: skip `manage_adr`; ingest any
  existing ADRs as a `Decision` concept type.

Caveat: for the knowledgeAgent repo itself the pairing is moot (no
code to index); it pays off where the kb/ pattern is deployed inside
an actual codebase.

# Citations

[1] [codebase-memory-mcp README capture](/sources/2026-07-06-codebase-memory-mcp.md)
