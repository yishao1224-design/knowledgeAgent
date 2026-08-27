---
type: Entity
title: codebase-memory-mcp
description: MCP server by DeusData that indexes codebases into a queryable SQLite knowledge graph (tree-sitter + hybrid LSP) with automatic freshness via git watching.
status: stable
lifecycle: active
confidence: medium
created: 2026-07-06
updated: 2026-07-06
stale_after: 2026-10-06
tags: []
sources:
  - resource: /sources/2026-07-06-codebase-memory-mcp.md
    id: codebase-memory-mcp
    title: codebase-memory-mcp README capture
---

# codebase-memory-mcp

An MCP (Model Context Protocol) server that indexes a codebase into a
persistent knowledge graph — definitions, call graphs, imports,
routes — stored as SQLite under `~/.cache/codebase-memory-mcp/`, and
exposes 14 tools for structural queries, path tracing, semantic
search, and read-only openCypher [codebase-memory-mcp]. Parsing is tree-sitter based
(158 languages) with a hybrid LSP layer for type resolution in 9
mainstream languages [codebase-memory-mcp].

Everything it stores is **derived and regenerable** from the code:
delete the database and re-index, nothing is lost. Freshness is
mechanical — a background watcher maps git diffs to stale graph
regions and re-indexes incrementally [codebase-memory-mcp]. This makes it an *index*
(cache), in contrast to a curated corpus like this bundle; the
division of labor is analyzed in
[codebase-memory-mcp vs the kb wiki](/comparisons/codebase-memory-mcp-vs-kb-wiki.md).

Notable for integration purposes:

- `detect_changes` reports what changed since a given point — usable
  as an external staleness signal for
  [the knowledge lifecycle](/concepts/knowledge-lifecycle.md).
- `manage_adr` stores architecture decision records inside the tool's
  own storage — overlapping with what a knowledge bundle does.
- A team-shareable snapshot (`.codebase-memory/graph.db.zst`) can be
  committed to a repo [codebase-memory-mcp].
- Distribution is a single static binary via a `curl | bash` installer
  that auto-rewrites the configuration of 11 coding agents [codebase-memory-mcp] — a
  trust-boundary consideration before adoption.
