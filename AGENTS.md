# Agent instructions

This repo is an agent-maintained knowledge base. The operating contract
lives in [CLAUDE.md](CLAUDE.md) — despite the filename it is
agent-agnostic. **Read it in full before touching anything under
`okf/`**, then read `okf/SCHEMA.md` (content conventions), `okf/index.md`
(what exists), and the recent entries of `okf/log.md` (what changed).

Non-negotiables, restated:

1. Files under `okf/sources/` are immutable — re-ingest under a new
   dated filename, never edit.
2. Every edit to `okf/` gets a log entry:
   `python scripts/okf.py log "**Verb**: message"`.
3. Deprecate, don't delete. `status: deprecated` requires
   `superseded_by` or a `## Deprecation` section.
4. Run `python scripts/okf.py lint` before finishing any session that
   modified `okf/`; errors must be zero.

Lifecycle workflows (capture / serve / verify / garden / audit) are
defined in `skills/kb-*/SKILL.md`. Match the user's request to a
workflow and follow it end to end, including Step 0 (orientation) and
the close-out steps (index, log, lint).

After editing anything in `skills/`, run `python scripts/okf.py init`
to regenerate the per-tool copies (`.claude/skills/`,
`.github/prompts/`).
