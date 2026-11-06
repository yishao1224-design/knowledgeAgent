# Agent instructions

This repo is an agent-maintained knowledge base. The operating contract
lives in [CLAUDE.md](CLAUDE.md) — despite the filename it is
agent-agnostic. **Read it in full before touching anything under
`okf/`**, then read `okf/SCHEMA.md` (content conventions), `okf/index.md`
(what exists), and the recent entries of `okf/log.md` (what changed).
In a multi-project bundle (a subdirectory with its own `SCHEMA.md` is a
project), read the root `SCHEMA.md` plus the project's `SCHEMA.md`,
`index.md` and `log.md`, and log with `okf.py log --project NAME`.

Non-negotiables, restated:

1. Files under `okf/sources/` are immutable — re-ingest under a new
   dated filename, never edit. Git history is the tamper record.
2. Every edit to `okf/` gets a log entry:
   `python scripts/okf.py log "**Verb**: message"`.
3. Deprecate, don't delete. `lifecycle: deprecated` requires
   `superseded_by` or a `## Deprecation` section.
4. Run `python scripts/okf.py lint` before finishing any session that
   modified `okf/`; errors must be zero.
5. `status` is OKF v0.2's standard field (`draft | stable |
   deprecated`); this bundle's five-state machine lives in `lifecycle`
   and the two must agree. Cite sources inline by `sources[].id`, never
   with a `# Citations` section.

Lifecycle workflows (capture / serve / verify / garden / audit) are
defined in `skills/kb-*/SKILL.md`. Match the user's request to a
workflow and follow it end to end, including Step 0 (orientation) and
the close-out steps (index, log, lint).

After editing anything in `skills/`, run `python scripts/okf.py init`
to regenerate the per-tool copies (`.claude/skills/`,
`.github/prompts/`).
