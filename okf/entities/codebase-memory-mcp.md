---
type: Entity
title: codebase-memory-mcp
description: MCP server by DeusData that indexes code, documentation and infrastructure into a local SQLite knowledge graph (tree-sitter + hybrid LSP), kept fresh by session-scoped git watching.
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

# codebase-memory-mcp

An MCP (Model Context Protocol) server, MIT-licensed, that indexes a
repository into a persistent local knowledge graph — definitions, call
graphs, imports, routes — stored as SQLite under
`~/.cache/codebase-memory-mcp/` (override with `CBM_CACHE_DIR`)
[codebase-memory-mcp-2026-11]. It exposes 17 tools for structural
queries, path tracing, semantic search (a `search_graph` parameter, not
a separate tool), coverage checks, snapshot comparison and read-only
openCypher [codebase-memory-mcp-2026-11]. Parsing is tree-sitter based
(162 languages), with a Hybrid LSP layer for type resolution in Python,
TypeScript/JavaScript, PHP, C#, Go, C/C++, Java, Kotlin, Rust and Perl
[codebase-memory-mcp-2026-11]. Beyond code it now also indexes
documentation (Markdown, reStructuredText, AsciiDoc, text PDFs), ADR
metadata and infrastructure files (Docker, Kubernetes, Helm, Terraform,
CI), with `MENTIONS` edges from documents to code
[codebase-memory-mcp-2026-11].

Almost everything it stores is **derived and regenerable** from the
repository: delete the database and re-index. The exceptions are the
`manage_adr` decision record, which sits next to the index and is
deleted with it, and ingested runtime traces
[codebase-memory-mcp-2026-11]. Freshness is mechanical but
session-scoped: a background watcher polls the git projects registered
by connected MCP sessions (or permanently under `daemon start`) and
re-indexes them incrementally; non-git roots are not watched by default
[codebase-memory-mcp-2026-11]. This makes it an *index* (cache), in
contrast to a curated corpus like this bundle; the division of labor is
analyzed in
[codebase-memory-mcp vs the kb wiki](/comparisons/codebase-memory-mcp-vs-kb-wiki.md).

Notable for integration purposes:

- `detect_changes` maps uncommitted changes to affected symbols with
  risk classification, and `compare_graphs` diffs two indexed snapshots
  [codebase-memory-mcp-2026-11] — either could serve as a symbol-level
  staleness signal for
  [the knowledge lifecycle](/concepts/knowledge-lifecycle.md).
- `manage_adr` keeps one project-wide decision record (sectioned
  markdown) next to the index, not in the repository
  [codebase-memory-mcp-2026-11] — overlapping with what a knowledge
  bundle does. Separately, indexing extracts ADR metadata from
  documentation files in the repo.
- A team-shareable snapshot (`.codebase-memory/graph.db.zst`) is now
  opt-in (`persistence: true`) and can be committed; upstream warns to
  commit it deliberately, since every refresh adds a full blob to git
  history [codebase-memory-mcp-2026-11].
- Distribution is a self-contained native executable (fully static only
  in the Linux `-portable` builds), installed via `curl | bash` or
  package managers. `install` configures up to 46 client surfaces with
  MCP entries, skills, agent profiles and — by default — context hooks,
  and an account-wide coordination daemon starts automatically
  [codebase-memory-mcp-2026-11]. Releases carry SLSA 3 provenance,
  cosign signatures and checksums the installers verify. Still a
  trust-boundary consideration before adoption: pin a release, or use
  `--skip-config` / `--no-hooks`.

At the first capture (2026-07-06) the counts were 14 tools, 158
languages and 11 auto-configured agents, and the snapshot was written
by default [codebase-memory-mcp].
