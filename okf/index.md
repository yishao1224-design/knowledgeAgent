---
okf_version: "0.2"
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
* [User Story Analysis Workflow (Ingest After Verify)](concepts/user-story-analysis-workflow.md) - The bundle-integrated pipeline for working a user story — query first, flag contradictions at analysis time, implement and verify, ingest what shipped last.

# Entities

* [MarkItDown](entities/markitdown.md) - Microsoft's Python utility that converts binary formats (PDF, Office, images, audio) to LLM-oriented Markdown — assessed as an optional extraction helper for this bundle's capture step, not adopted into any skill.
* [The Lifecycle Skill Suite](entities/lifecycle-skills.md) - The five lifecycle skills (kb-ingest, kb-query, kb-review, kb-curate, kb-lint) — one per phase, with strict division of responsibility — plus the kb-setup bootstrap skill that scaffolds a bundle in a fresh project.
* [ado-workitem-sync — ADO Retrieval Toolchain](entities/ado-workitem-sync.md) - Removed 2026-08-26 — the scripts/ado.py + ado-workitem-sync skill pair that synced Azure DevOps work items into local analysis folders; kept for the rev-stamp provenance and code-vs-judgment design record. *(deprecated)*
* [codebase-memory-mcp](entities/codebase-memory-mcp.md) - MCP server by DeusData that indexes code, documentation and infrastructure into a local SQLite knowledge graph (tree-sitter + hybrid LSP), kept fresh by session-scoped git watching.
* [okf.py — the Mechanical Toolchain](entities/okf-toolchain.md) - The stdlib-only script (scripts/okf.py) that mechanizes the bundle — init, lint, index, links, log, stats, drift — and the exact conformance/lifecycle rules its lint enforces.
* [openwiki](entities/openwiki.md) - LangChain's openwiki — generates and incrementally maintains linked Markdown wikis (repo docs or a personal brain), run inside coding agents or as a standalone CLI, with evidence-tracked "Grounded Claims" and OKF v0.2 output — the claim-level, auto-reconciling counterpart to this bundle's page-level curated lifecycle.

# Comparisons

* [codebase-memory-mcp vs the kb wiki](comparisons/codebase-memory-mcp-vs-kb-wiki.md) - Why a derived code-knowledge graph and a curated OKF bundle are complementary layers, where they overlap (ADRs), and a phased integration plan.
* [openwiki vs the kb bundle](comparisons/openwiki-vs-kb-bundle.md) - A generator product vs a curation discipline — openwiki reconciles per-claim evidence automatically, this bundle curates per-page trust through a lifecycle; where each wins, how they converged (both now emit OKF v0.2), and what each could borrow.

# Queries

* [Governance for AI-Generated Knowledge at Organisation Scale](queries/governance-for-ai-generated-knowledge.md) - How to validate, approve and version agent-written knowledge before it becomes discoverable across a large organisation — discoverability tiers, roles, a three-stage PR pipeline, git as the version system.
* [OKF as a Unified Knowledge Layer Across Enterprise Tools](queries/okf-unified-knowledge-layer-across-tools.md) - Whether OKF can unify knowledge from Polarion, Azure DevOps, GitHub, Confluence and ServiceNow while preserving permissions and source-of-truth ownership — yes, as a federation of bundles, with three permission rules.
* [Token Cost of an LLM-Maintained Wiki](queries/token-cost-of-the-llm-wiki.md) - Rough token counts per ingest, review and question, where the wiki adds or saves tokens versus re-reading raw documents and RAG, and the main growth driver (index size).

# Sources

* [DeusData codebase-memory-mcp README](sources/2026-07-06-codebase-memory-mcp.md) - Condensed capture of the codebase-memory-mcp project README from GitHub (fetched 2026-07-06).
* [DeusData codebase-memory-mcp README](sources/2026-11-10-codebase-memory-mcp.md) - Condensed capture of the codebase-memory-mcp project README from GitHub (fetched 2026-11-10), covering its 17 MCP tools, 162-language indexing, session-scoped git watching, ADR storage, 46-client installer, CBM Lens UI and release security.
* [Lifecycle skills (canonical SKILL.md files)](sources/2026-07-06-lifecycle-skills.md) - Faithful condensation of the five canonical lifecycle skills under skills/ (kb-ingest, kb-query, kb-review, kb-curate, kb-lint) as of 2026-07-06.
* [Microsoft MarkItDown README](sources/2026-07-11-markitdown.md) - Condensed capture of the microsoft/markitdown project README from GitHub (fetched 2026-07-11).
* [Microsoft MarkItDown README](sources/2026-11-10-markitdown.md) - Condensed capture of the microsoft/markitdown project README from GitHub (fetched 2026-11-10); a faithful condensation, not verbatim, taken from raw main/README.md.
* [Open Knowledge Format (OKF) v0.1 Specification](sources/2026-07-05-okf-spec-v0-1.md) - Condensed capture of the OKF v0.1 spec from GoogleCloudPlatform/knowledge-catalog.
* [Open Knowledge Format (OKF) v0.2 Specification](sources/2026-08-27-okf-spec-v0-2.md) - Condensed capture of the OKF v0.2 spec from the format's new standalone repository, GoogleCloudPlatform/open-knowledge-format.
* [Q&A: governance, cross-tool federation, and token cost of an LLM Wiki](sources/2026-11-10-governance-federation-cost-qa.md) - Faithful condensation of three audience questions on the LLM Wiki × OKF talk and the answers given in a Claude Code session (2026-11-09/10) — agent-generated recommendations, not externally verified.
* [ado.py + ado-workitem-sync skill (retrieval toolchain pair)](sources/2026-07-09-ado-workitem-sync.md) - Faithful condensation of scripts/ado.py and skills/ado-workitem-sync/SKILL.md — subcommands, normalization port provenance, rev-stamp staleness model — as of 2026-07-09.
* [langchain-ai/openwiki README](sources/2026-07-12-openwiki.md) - Condensed capture of the openwiki project README from GitHub (fetched 2026-07-12) — CLI that auto-generates agent-optimized wikis for codebases and personal knowledge.
* [langchain-ai/openwiki README](sources/2026-11-10-openwiki.md) - Condensed capture of the openwiki project README from GitHub (fetched 2026-11-10) — coding-agent integrations, code and personal modes, Grounded Claims evidence tracking, OKF v0.2 output, connectors, model providers, scheduled CI updates, and wiki workspaces.
* [okf.py — mechanical toolchain (scripts/okf.py)](sources/2026-07-07-okf-toolchain.md) - Faithful condensation of scripts/okf.py — the six subcommands and the exact conformance/lifecycle rules its lint enforces, as of 2026-07-07.
