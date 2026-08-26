---
type: Source
title: DeusData codebase-memory-mcp README
description: Condensed capture of the codebase-memory-mcp project README from GitHub (fetched 2026-07-06).
source_url: https://github.com/DeusData/codebase-memory-mcp
ingested: 2026-07-06
sha256: a97b5d1d87a4c1d623fb1eb5d07c706d1ebd52a7dbdfeda94894d929e0862cf7
---

# codebase-memory-mcp (condensed capture)

A high-performance code intelligence server built on the Model Context
Protocol (MCP). Indexes entire codebases into a persistent knowledge
graph so AI coding agents can query code structure cheaply. Claims:
average repository indexed in milliseconds; Linux kernel (28M LOC) in
3 minutes.

## Architecture

Multi-pass indexing pipeline:

```
Tree-sitter AST parsing → definition extraction → call graph
construction → HTTP/service linking → semantic enrichment → SQLite
persistence
```

- Tree-sitter parses 158 vendored languages.
- Hybrid LSP layer (lightweight C) does type resolution for 9
  languages: Python, TypeScript/JavaScript, PHP, C#, Go, C, C++, Java,
  Kotlin, Rust.
- SQLite backend with FTS5 full-text search and spatial indices.
- RAM-first pipeline with LZ4 compression; only the final dump
  persists.

## Storage

Knowledge graph persists as SQLite databases at
`~/.cache/codebase-memory-mcp/`.

- Node types: Project, Package, Folder, File, Module, Class, Function,
  Method, Interface, Enum, Type, Route, Resource.
- Edge types: CALLS, IMPORTS, DEFINES, IMPLEMENTS, INHERITS,
  HTTP_CALLS, ASYNC_CALLS, EMITS, LISTENS_ON, DATA_FLOWS, SIMILAR_TO,
  SEMANTICALLY_RELATED.
- Team sharing: `.codebase-memory/graph.db.zst` (zstd-compressed
  SQLite snapshot) can be committed to a repo for teammates'
  incremental indexing.

## MCP tools (14, in 4 categories)

- Indexing: index_repository, list_projects, delete_project,
  index_status
- Querying: search_graph, trace_path, detect_changes, query_graph,
  get_graph_schema
- Analysis: get_code_snippet, get_architecture, search_code,
  manage_adr, ingest_traces

Read-only openCypher query language: pattern matching, WHERE with
regex, aggregations; sub-1ms typical queries.

## Semantic search

Bundled Nomic embeddings (768-dim, int8-quantized) with 11-signal
scoring: TF-IDF, RRI, API signatures, AST profiles, data flow,
Halstead complexity, MinHash similarity, module proximity, graph
diffusion.

Efficiency claim from docs: "Five structural queries consumed ~3,400
tokens via codebase-memory-mcp versus ~412,000 tokens via
file-by-file grep exploration — a 99.2% reduction."

## Freshness / staleness handling

- Background watcher detects file changes via git polling with
  adaptive intervals.
- Optional auto-index on MCP session start (default limit 50K files).
- Incremental updates: fast zstd -3 export tier for watcher updates;
  full export at zstd -9.
- Previously indexed projects track staleness via git diff mapping.

## Distribution

Single static binary (macOS/Linux/Windows), no dependencies.
Installer: `curl -fsSL .../install.sh | bash`. Auto-detects and
configures 11 coding agents (Claude Code, Codex, Gemini CLI, Zed,
Aider, etc.) with MCP entries and instruction hooks.
