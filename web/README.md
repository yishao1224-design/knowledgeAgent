# Knowledge Workspace

A database-free web workspace for OKF knowledge bundles. Each import, question,
and ingest preview performs a new, in-memory, depth-one clone of the selected
public Git repository. No repository clone or conversation is retained by the
server.

## What is included

- GitHub, GitLab, Bitbucket, and Gitee HTTPS repository validation.
- `depth: 1`, `singleBranch: true`, no-tag clone through `isomorphic-git`.
- Stateless Pi Agent Core tool loops for query and ingest execution.
- Hash-verified, fixed-version `kb-query` and `kb-ingest` skills loaded as Pi's mandatory first tool call.
- The original `scripts/okf.py` bundled with a pinned source commit and SHA-256 manifest.
- OKF frontmatter parsing, lifecycle badges, Markdown rendering, and bundle links.
- Autonomous file discovery through restricted list, literal-search, and read tools.
- Patch-first ingest for pasted Markdown or text files.
- No D1, R2, Redis, PostgreSQL, repository cache, or server session state.

## Pi Agent execution

Query gives Pi read-only repository tools and lets the model decide which files
to search and read before answering with citations. Ingest adds one constrained
`draft_ingest` tool: Pi must inspect the schema and related pages first, while
the deterministic tool preserves source immutability and generates a validated
reviewable patch. There is no session store, so every invocation is isolated.
The UI displays the clone and tool-call trace with each answer or patch preview.

Each agent run must call `load_skill` before any repository tool. The fixed
runtime assets live under `runtime/knowledge-agent/`; the build fails if their
content does not match the committed manifest hashes. Cloudflare Workers cannot
spawn Python, so this deployment keeps the original `okf.py` available and
verified while the existing TypeScript adapter performs the mechanical ingest
checks. A future container runtime can execute the same pinned Python file.

The browser supplies an OpenAI-compatible endpoint, model name, and request-scoped
API key. Endpoint and model preferences may be saved locally, but the API key is
kept only in the active tab and is never retained by the server.

The first ingest implementation creates an immutable source capture and a low
confidence draft concept, then updates `kb/index.md` and `kb/log.md`. The
downloaded patch must still pass the repository's canonical
`python scripts/okf.py lint` before it is committed.

## Local development

```sh
npm install
npm run dev
```

The development server prints the local URL. External Git requests can be
blocked by a corporate proxy in the local Cloudflare simulator even when the
site itself loads; the deployed Worker executes those requests directly.

## Validation

```sh
npm run lint
npx tsc --noEmit
npm test
```

## Execution limits

- Public HTTPS repositories only.
- Maximum 1,200 Markdown files under `kb/`.
- Maximum 1 MB per KB Markdown file and 12 MB total KB Markdown content.
- Requires `kb/SCHEMA.md`, `kb/index.md`, and `kb/log.md`.
- Does not fetch submodules or Git LFS objects.
- Pi is capped at 10 turns, 24 repository tool calls, and a 50-second run.
- Query tools cannot write files or execute repository code.
