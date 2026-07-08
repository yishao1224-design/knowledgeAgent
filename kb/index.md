---
okf_version: "0.1"
---

# Bundle Index

* [Bundle Schema & Conventions](SCHEMA.md) - Authoritative conventions for this OKF bundle — types, tags, frontmatter templates, lifecycle rules.

# Concepts

* [Adopting the Bundle Pattern in a Project Repo](concepts/adopting-the-bundle-pattern.md) - How to install the OKF bundle + lifecycle skills into a real project repository — same-repo vs separate-repo decision, adoption steps, and what to tune.
* [Automating the Lifecycle (LangGraph and Alternatives)](concepts/automating-the-lifecycle.md) - Whether to put an orchestration framework like LangGraph in charge of the knowledge lifecycle — verdict, rules if you do, and the simpler scheduled-skills alternative.
* [Ingesting Requirements from Ticket Systems](concepts/ingesting-requirements-from-ticket-systems.md) - How to feed user stories from a work-item tracker (e.g. Azure DevOps) into the bundle — access paths, immutable captures, and the don't-mirror-the-backlog rule.
* [Open Knowledge Format (OKF)](concepts/open-knowledge-format.md) - The storage format this bundle conforms to — markdown + YAML frontmatter bundles with reserved index/log files and permissive consumption.
* [PR Quality Gates for a Team-Shared Bundle](concepts/pr-quality-gates.md) - Three-tier merge guardrails for a git-managed wiki/bundle — blocking mechanical CI, advisory LLM review, human gates scoped by blast radius; conformance at merge, truth via lifecycle.
* [The Knowledge Lifecycle](concepts/knowledge-lifecycle.md) - How concepts in this bundle move through draft, active, needs_review, deprecated, and archived — and which skill drives each transition.

# Entities

* [The Lifecycle Skill Suite](entities/lifecycle-skills.md) - The five canonical skills (kb-ingest, kb-query, kb-review, kb-curate, kb-lint) that drive the knowledge lifecycle — one per phase, with strict division of responsibility.
* [codebase-memory-mcp](entities/codebase-memory-mcp.md) - MCP server by DeusData that indexes codebases into a queryable SQLite knowledge graph (tree-sitter + hybrid LSP) with automatic freshness via git watching.
* [okf.py — the Mechanical Toolchain](entities/okf-toolchain.md) - The stdlib-only script (scripts/okf.py) that mechanizes the bundle — init, lint, index, log, stats, drift — and the exact conformance/lifecycle rules its lint enforces.

# Comparisons

* [codebase-memory-mcp vs the kb wiki](comparisons/codebase-memory-mcp-vs-kb-wiki.md) - Why a derived code-knowledge graph and a curated OKF bundle are complementary layers, where they overlap (ADRs), and a phased integration plan.

# Sources

* [DeusData codebase-memory-mcp README](sources/2026-07-06-codebase-memory-mcp.md) - Condensed capture of the codebase-memory-mcp project README from GitHub (fetched 2026-07-06).
* [Lifecycle skills (canonical SKILL.md files)](sources/2026-07-06-lifecycle-skills.md) - Faithful condensation of the five canonical lifecycle skills under skills/ (kb-ingest, kb-query, kb-review, kb-curate, kb-lint) as of 2026-07-06.
* [Open Knowledge Format (OKF) v0.1 Specification](sources/2026-07-05-okf-spec-v0-1.md) - Condensed capture of the OKF v0.1 spec from GoogleCloudPlatform/knowledge-catalog.
* [okf.py — mechanical toolchain (scripts/okf.py)](sources/2026-07-07-okf-toolchain.md) - Faithful condensation of scripts/okf.py — the six subcommands and the exact conformance/lifecycle rules its lint enforces, as of 2026-07-07.
