---
okf_version: "0.1"
---

# Bundle Index

* [Bundle Schema & Conventions](SCHEMA.md) - Authoritative conventions for this OKF bundle — types, tags, frontmatter templates, lifecycle rules.

# Concepts

* [Open Knowledge Format (OKF)](concepts/open-knowledge-format.md) - The storage format this bundle conforms to — markdown + YAML frontmatter bundles with reserved index/log files and permissive consumption.
* [The Knowledge Lifecycle](concepts/knowledge-lifecycle.md) - How concepts in this bundle move through draft, active, needs_review, deprecated, and archived — and which skill drives each transition.

# Entities

* [codebase-memory-mcp](entities/codebase-memory-mcp.md) - MCP server by DeusData that indexes codebases into a queryable SQLite knowledge graph (tree-sitter + hybrid LSP) with automatic freshness via git watching.

# Comparisons

* [codebase-memory-mcp vs the kb wiki](comparisons/codebase-memory-mcp-vs-kb-wiki.md) - Why a derived code-knowledge graph and a curated OKF bundle are complementary layers, where they overlap (ADRs), and a phased integration plan.

# Sources

* [DeusData codebase-memory-mcp README](sources/2026-07-06-codebase-memory-mcp.md) - Condensed capture of the codebase-memory-mcp project README from GitHub (fetched 2026-07-06).
* [Open Knowledge Format (OKF) v0.1 Specification](sources/2026-07-05-okf-spec-v0-1.md) - Condensed capture of the OKF v0.1 spec from GoogleCloudPlatform/knowledge-catalog.
