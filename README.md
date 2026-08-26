# knowledgeAgent

An agent-maintained knowledge base built on the
[Open Knowledge Format (OKF) v0.1](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md),
extended with a knowledge-lifecycle profile inspired by the
[Hermes llm-wiki pattern](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/llm-wiki/SKILL.md).

Knowledge here is treated as perishable: every page carries a lifecycle
`status`, active pages carry a `review_after` date, raw sources are
immutable and hash-verified, and a lint toolchain keeps the whole thing
honest.

## Layout

```
knowledgeAgent/
├── CLAUDE.md            # agent operating contract (session protocol, hard rules)
├── okf/                # the OKF bundle — all knowledge lives here
│   ├── SCHEMA.md        #   bundle conventions: types, tags, templates, cadences
│   ├── index.md         #   generated catalog (okf.py index)
│   ├── log.md           #   append-only change history
│   ├── concepts/ entities/ comparisons/ queries/ archive/
│   └── sources/         #   IMMUTABLE raw captures, sha256-verified
├── skills/              # canonical lifecycle skills (edit these)
│   ├── kb-setup/        #   bootstrap: scaffold okf/ + okf.py into a fresh project
│   │   └── okf.py       #     toolchain bundled for `npx skills add` (auto-synced)
│   ├── kb-ingest/       #   capture: source → snapshot → concept pages
│   ├── kb-query/        #   serve: answer with citations + trust labels
│   ├── kb-review/       #   verify: work the review queue against sources
│   ├── kb-curate/       #   garden: merge, split, archive, restructure
│   └── kb-lint/         #   audit: mechanical health, fix or queue
├── AGENTS.md            # cross-agent entry point (Copilot coding agent, Codex, …)
├── .claude/skills/      # generated copies for Claude Code discovery (okf.py init)
├── .github/
│   ├── copilot-instructions.md   # GitHub Copilot repo instructions
│   └── prompts/         # generated Copilot prompt files (/kb-ingest, …)
└── scripts/
    └── okf.py           # stdlib-only bundle toolchain
```

## Quickstart

```sh
python scripts/okf.py init     # bootstrap okf/ skeleton + sync skills
python scripts/okf.py lint     # health check (exit 1 on errors)
```

Then open the repo in Claude Code and say e.g. *"add this article to the
knowledge base"* — the `kb-ingest` skill drives the rest.

## Install into another project (`npx skills add`)

The lifecycle skills are published through the open
[agent-skills ecosystem](https://github.com/vercel-labs/skills), so any
project can pull them with the `skills` CLI — no clone required. It works
with Claude Code, Cursor, Codex, Copilot, and
[70+ other agents](https://github.com/vercel-labs/skills#supported-agents).

```sh
# the kb-* skills (--skill takes exact names, not globs)
npx skills add yishao1224-design/knowledgeAgent \
  --skill kb-setup --skill kb-ingest --skill kb-query \
  --skill kb-review --skill kb-curate --skill kb-lint

# or just what you need
npx skills add yishao1224-design/knowledgeAgent --skill kb-setup --skill kb-ingest --skill kb-query

# preview what's available first
npx skills add yishao1224-design/knowledgeAgent --list
```

A bare `SKILL.md` doesn't carry the `okf.py` toolchain or the `okf/`
bundle, so **run `kb-setup` once first** in the target project — just ask
your agent to *"set up the knowledge base"*. It drops `scripts/okf.py`
(bundled inside the skill) into place and runs `okf.py init` to scaffold
`okf/`. The other skills detect a missing bundle and point you at
`kb-setup` automatically. After that, `kb-ingest` / `kb-query` / etc.
behave exactly as they do in this repo.

## Agent support

One canonical workflow definition (`skills/*/SKILL.md`), surfaced to
each tool by `okf.py init`:

| Tool | Surface | Committed? |
|------|---------|-----------|
| Claude Code | `CLAUDE.md` + `.claude/skills/` | instructions yes; skill copies regenerated locally (gitignored) |
| GitHub Copilot (VS Code chat) | `.github/copilot-instructions.md` + `.github/prompts/*.prompt.md` (type `/kb-…`) | yes — Copilot reads them from the repo |
| Copilot coding agent / other agents | `AGENTS.md` | yes |

`CLAUDE.md` is the single authoritative operating contract; the Copilot
and AGENTS.md files restate the hard rules briefly and defer to it.
Edit workflows only in `skills/`, then re-run
`python scripts/okf.py init` to regenerate the wrappers.

## The lifecycle

```
draft ──> active ──> needs_review ──> active     (re-verified)
                            │
                            └───────> deprecated ──> archived
```

| Phase | Skill | Trigger |
|-------|-------|---------|
| Capture | `kb-ingest` | new source or takeaways to incorporate |
| Serve | `kb-query` | a question the bundle should answer |
| Verify | `kb-review` | review queue non-empty (`okf.py stats`) |
| Garden | `kb-curate` | duplicates, bloat, restructuring, archiving |
| Audit | `kb-lint` | periodic health check |

## Toolchain

```sh
python scripts/okf.py init                 # bootstrap + sync skills → .claude/skills/
python scripts/okf.py lint                 # OKF conformance + lifecycle audit
python scripts/okf.py lint --inbound /p.md # who links here? (safe-delete check)
python scripts/okf.py index                # regenerate okf/index.md
python scripts/okf.py log "**Verb**: msg"  # prepend a dated log entry
python scripts/okf.py stats                # counts + review queue
python scripts/okf.py drift                # verify source hashes
python scripts/okf.py drift --hash FILE    # hash a new capture's body
```

No dependencies beyond Python 3 stdlib (PyYAML used if present).

### Where the bundle lives

`okf/` is the default. Nothing records the choice in a config file —
**the directory itself is the record**: every command finds the bundle
by looking for a top-level directory containing `SCHEMA.md`. So a
project that predates this default, or that picked its own name at
setup, keeps working with no flag and no migration.

```sh
python scripts/okf.py init                    # → okf/
python scripts/okf.py init --bundle knowledge # → knowledge/
python scripts/okf.py lint --bundle knowledge # only needed to disambiguate
```

`kb-setup` asks which name you want before scaffolding. Pass
`--bundle` to later commands only when a project genuinely holds more
than one bundle — `okf.py` reports the ambiguity rather than guessing.
The default is deliberately **not** dot-prefixed: the bundle is content
people read and edit, not tooling config, so it stays visible in `ls`,
in file explorers, and in GitHub's root listing.

## Relationship to OKF

The bundle is strictly OKF v0.1 conformant — any plain OKF consumer can
read it. The lifecycle fields (`status`, `confidence`, `review_after`,
`sources`, `supersedes`, `superseded_by`) are extension frontmatter keys
under OKF §4, and the body prose always restates deprecation/contest
status so nothing is lost when those keys are ignored.

Improvements layered on top of the base spec:

1. **Lifecycle states** with enforced exit criteria (OKF has no trust model).
2. **Expiring truth** — `active` requires `review_after`; lint feeds an
   automatic review queue.
3. **Tamper-evident sources** — immutable captures, body hashes checked
   by `okf.py drift`.
4. **Graph-aware deprecation** — `superseded_by` plus inbound-link
   queries mean links are never silently broken.
5. **Governed vocabulary** — types and tags registered in `okf/SCHEMA.md`
   before first use.

Skills live canonically in `skills/`; edit them there and re-run
`python scripts/okf.py init` to sync the copies Claude Code discovers in
`.claude/skills/`.
