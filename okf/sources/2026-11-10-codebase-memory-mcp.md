---
type: Source
title: DeusData codebase-memory-mcp README
description: Condensed capture of the codebase-memory-mcp project README from GitHub (fetched 2026-11-10), covering its 17 MCP tools, 162-language indexing, session-scoped git watching, ADR storage, 46-client installer, CBM Lens UI and release security.
source_url: https://github.com/DeusData/codebase-memory-mcp
ingested: 2026-11-10
---

# codebase-memory-mcp (condensed capture)

Self-description: "an MCP server that connects code, documentation,
configuration, and infrastructure in a persistent local knowledge
graph." "The MCP server is the core of the project." Native C backend
exposing **17 MCP tools**; parses **162 languages** with vendored
tree-sitter grammars plus "Hybrid LSP" type resolution. The installer
supports **46 automatic or conditional client integrations**. "Indexing
and graph queries need no hosted service or API key." Licence: MIT.
Optional visual companion **CBM Lens** is in open beta (v0.0.1). The
README's security section cites the v0.11.0 release notes; it does not
state a current version number. An arXiv preprint (2603.27277) is linked.

## Architecture

Multi-pass pipeline (src/pipeline): structure → definitions → calls →
HTTP links → config → tests. Source tree also has `daemon/` (per-account
session coordination, shared jobs/watchers), `mcp/` (17 tools, JSON-RPC
2.0, auto-index), `cli/` (install/uninstall/update/config, 46 client
surfaces), `store/` (SQLite graph, search, Louvain), `cypher/`,
`watcher/` ("Background auto-sync (git polling, adaptive intervals)"),
`traces/`, `ui/` (local HTTP server + embedded CBM Lens).

- 162 vendored tree-sitter grammars compiled into the binary; "counted by
  the vendored grammar directories" in the parser manifest.
- Hybrid LSP: "lightweight C implementation of language type-resolution
  algorithms, structurally inspired by and compatible with major language
  servers" (tsserver/typescript-go, pyright, gopls, Roslyn, Eclipse JDT,
  rust-analyzer); no language-server process. Full Hybrid LSP for Python,
  TypeScript/JavaScript/JSX/TSX, PHP, C#, Go, C/C++, Java, Kotlin, Rust,
  and Perl. Other languages "fall back to textual resolution".
- RAM-first pipeline: LZ4 compression, in-memory SQLite, single dump at
  end; can spill extraction results to disk; memory released after.
- Indexing modes: `full` (default, with semantic analysis), `moderate`,
  `fast` (no semantic analysis), `cross-repo-intelligence`.
- Beyond code, it indexes: Markdown, reStructuredText, AsciiDoc as
  document sections; PDFs with text layers (no OCR); ADR metadata
  (status, deciders, supersession) from documentation files; diagrams and
  OpenAPI; Dockerfiles, Compose, Kubernetes, Helm, Kustomize,
  Terraform/OpenTofu, Terragrunt, Ansible, shell, Make, CI steps.
  Document-to-code references create `MENTIONS` edges "when the target
  can be resolved".
- Benchmarked language tiers on 64 repos: Excellent (>=90%), Good
  (75-89%, incl. Python, TypeScript, Go, Rust, Java), Functional (<75%:
  OCaml, Haskell); the rest "not yet benchmarked".

## Storage

SQLite databases at `~/.cache/codebase-memory-mcp/` (override with
`CBM_CACHE_DIR`); WAL mode. "To reset: `rm -rf ~/.cache/codebase-memory-mcp/`."

- 28 node labels incl. Project, Package, Folder, File, Module, Section,
  Class, Function, Method, Route, Channel, Process, EnvVar, Resource,
  Chart, Image, Branch.
- 42 edge types incl. CALLS, CALL_REFERENCE, USAGE, IMPORTS, DEFINES,
  IMPLEMENTS, INHERITS, HTTP_CALLS, GRPC_CALLS, ASYNC_CALLS, EMITS,
  LISTENS_ON, SPAWNS, CONFIGURES, DEPLOYS, DEPENDS_ON, MENTIONS, TESTS,
  DATA_FLOWS, SIMILAR_TO, SEMANTICALLY_RELATED, FILE_CHANGES_WITH, and
  cross-repo `CROSS_*` edges.
- ADR: `manage_adr` keeps "the project's decision record" stored with
  the index as a sidecar (`<db>.adr.db`); `delete_project` removes it.
  CBM Lens: "Saving changes the indexed decision document, not a file in
  your repository." Editor limit 8,000 UTF-8 bytes; no atomic lock.
- Team-shared artifact `.codebase-memory/graph.db.zst` (zstd SQLite
  snapshot). Now **opt-in**: written only with `persistence: true`
  (default `false`); once present, later indexes refresh it (Best tier
  zstd -9; Fast tier zstd -3 incl. watcher updates). Teammates' clones
  import it then index incrementally. Warns: "Commit it deliberately" —
  every refresh is a new full blob; "one team reached ~6 GB across ~350
  commits of this single path". Git LFS guidance given.

## MCP tools (17)

- Indexing (5): index_repository (sync, or `async: true` + `status: true`
  polling), list_projects, delete_project, index_status,
  check_index_coverage ("A clean result means no recorded gap, not proof
  of completeness").
- Querying (12): search_graph (structural, BM25, semantic), trace_path
  (alias trace_call_path; modes calls, data_flow, cross_service,
  topology, deploy, run; depth 1-15), detect_changes, query_graph,
  get_graph_schema, compare_graphs, get_code_snippet, get_file_outline,
  get_architecture, search_code, manage_adr, ingest_traces.
- New vs July list: check_index_coverage, compare_graphs,
  get_file_outline.
- `detect_changes`: "Map git diff to affected symbols + blast radius with
  risk classification"; Features: "maps uncommitted changes to affected
  symbols with risk classification and can report test impact with
  `scope: \"tests\"`". `compare_graphs` "compares indexed snapshots".
- `manage_adr` modes: get, update (whole document), set_sections
  (rewrite named `## Heading` sections byte-preservingly), sections.
- `query_graph`: read-only openCypher subset (MATCH, OPTIONAL MATCH,
  WITH, UNWIND, UNION, CASE, variable-length paths, regex, EXISTS,
  aggregates); unsupported constructs fail with an explicit error.
- Kiro/Junie tool profiles: Scout exposes 7 tools, Analysis 11.
- Every tool also callable as `codebase-memory-mcp cli <tool>`.

## Semantic search

The `semantic_query` parameter of `search_graph` ("not a separate
tool"). Bundled Nomic `nomic-embed-code` embeddings (768d int8) compiled
into the binary; 11-signal scoring (TF-IDF, RRI, API/Type/Decorator
signatures, AST profiles, data flow, Halstead-lite, MinHash, module
proximity, graph diffusion). BM25 via SQLite FTS5.

## Performance (Apple M3 Pro)

- Linux kernel full index 3 min (28M LOC, 75K files → 4.81M nodes,
  7.72M edges); fast index 1m 12s. Django full index ~6s.
- Cypher query <1ms; name search <10ms; trace depth 5 <10ms.
- Token claim now headlined from the 31-repository preprint: "10× lower
  token use and 2.1× fewer tool calls compared with file-by-file
  exploration". The earlier ~3,400 vs ~412,000-token five-query comparison
  is cited only as "earlier", via a link to an old README revision.
- The July claim "average repository indexed in milliseconds" no longer
  appears.

## Freshness / staleness handling

- `auto_index` (on MCP session start) is **off by default**; limit
  `auto_index_limit 50000`.
- Watching is session-scoped: each long-lived MCP session registers its
  root project and successful `index_repository` targets; "these watches
  belong to the registering sessions and remain while at least one
  owning session is connected; closing the last owner removes the
  watch." Under `daemon start` a watch outlives its sessions.
- `auto_watch` (default true) controls registration; `watcher_enabled`
  (default true) can disable the poll thread entirely.
- "The watcher follows **git** projects only by default"; non-git roots
  stay at their last index unless `watch_non_git true`.
- CLI indexing and failed MCP indexes do not register watches.
- `index_status` reports a `watch` object (poll cadence, last scan, or
  reason not watched). No latency figure is given for re-indexing.
- July wording "track staleness via git diff mapping" is not present.

## Agent integration and distribution

- Install: `curl -fsSL .../install.sh | bash` (macOS/Linux) or a
  download-inspect-run PowerShell flow; `--skip-config` installs the
  binary only. Also npm, PyPI, Homebrew, Scoop, AUR, `go install`, Nix
  flake, Claude Code plugin marketplace (registers the server only).
- `install` configures 46 client surfaces (40 auto-detected, 6
  conditional/explicit), e.g. Claude Code, Codex CLI, Gemini CLI, Zed,
  OpenCode, Aider, Cursor, Windsurf, VS Code, GitHub Copilot CLI, Kiro,
  Cline. It writes MCP config, instructions/skills, Scout/Verify/Auditor
  agent profiles, and session/search/read hooks. "Hooks are enabled by
  default"; `install --no-hooks` removes them. Hooks are "context-only
  and fail-open". Never flips experimental flags or permission bypasses.
- A per-account coordination daemon starts automatically with the first
  daemon-backed session and owns watchers, shared indexing jobs, and the
  optional UI. All CBM processes must run the exact same build.
- Executable is "self-contained; no adjacent data file is required.
  Linux `-portable` archives contain the fully static builds; ordinary
  platform archives use their native system ABI."
- Updates re-run the install script; "cbm makes no network request of its
  own accord"; no telemetry. `uninstall` removes owned config/skills/hooks
  and binary, keeps indexes unless `--delete-indexes`.
- `CBM_ALLOWED_ROOT` can confine `index_repository` paths.

## CBM Lens (open beta v0.0.1)

Bundled in standard releases; served on loopback (default port 9749).
Workspaces: Explore, Galaxy (3D graph), Architecture, ADR, Coverage,
System. Optional local chat runs a small model in-browser via WebGPU
(downloaded from Hugging Face only after opt-in).

## Security

Releases: VirusTotal scans of all candidates, SLSA Level 3 provenance,
Sigstore cosign signatures, SHA-256 `checksums.txt` verified by both
install scripts before extraction, CodeQL SAST gating.

## Experimental: Smart CI

`test-impact select` / `detect_changes` with `scope: "tests"` narrow test
runs; narrowing supports C/C++ only, falling back to `run_all` when
evidence is insufficient.
