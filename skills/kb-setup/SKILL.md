---
name: kb-setup
description: Scaffold the OKF knowledge bundle (default okf/) and its okf.py toolchain into a project that doesn't have them yet. Run this once before the other kb-* lifecycle skills (kb-ingest, kb-query, kb-review, kb-curate, kb-lint) when the project has no bundle directory — for example right after installing the skills with `npx skills add`.
---

# kb-setup — Bootstrap the knowledge bundle

The other `kb-*` skills assume the project already has:

- `scripts/okf.py` — the mechanical toolchain they call.
- an **OKF bundle** directory — `SCHEMA.md`, `index.md`, `log.md`, and
  the `concepts/ entities/ comparisons/ queries/ sources/ archive/`
  subdirectories. The default location is `okf/`; the user may pick a
  different name at Step 2 below, and every skill discovers it
  automatically thereafter.

When those don't exist yet (a fresh project, or right after
`npx skills add …`), run this skill once to lay them down. It is
idempotent: it never overwrites an existing `scripts/okf.py` or an
existing bundle.

## Step 0 — Check whether setup is even needed

From the project root:

- If `scripts/okf.py` exists **and** some top-level directory holds a
  `SCHEMA.md` (`okf/SCHEMA.md`, or whatever name this project chose),
  the bundle is set up. Stop here and tell the user there's nothing to
  do — point them at `kb-ingest` / `kb-query` instead.
- Otherwise continue.

## Step 1 — Place the toolchain at `scripts/okf.py`

This skill ships `okf.py` **in its own directory, right next to this
SKILL.md**. Copy that file to `scripts/okf.py` at the project root
(create `scripts/` first if needed). Do **not** overwrite an existing
`scripts/okf.py` — if one is already there, keep it.

To find the bundled copy:

1. Prefer the copy next to this SKILL.md (the skill's install directory).
2. If you can't resolve this skill's own path, search for it with your
   file tools — it lands under whichever agent skills directory the CLI
   installed to, e.g. `.claude/skills/kb-setup/okf.py`,
   `.agents/skills/kb-setup/okf.py`, `.cursor/skills/kb-setup/okf.py`,
   or the global `~/…` equivalent. A glob like `**/kb-setup/okf.py`
   finds it.
3. Last resort (only if the bundled file truly isn't on disk): fetch it
   from the source repo —
   `https://raw.githubusercontent.com/yishao1224-design/knowledgeAgent/master/scripts/okf.py`
   — and save it to `scripts/okf.py`.

`okf.py` is stdlib-only Python 3; it uses PyYAML if present but falls
back to a built-in frontmatter parser otherwise, so no install step is
required. It resolves the bundle relative to itself
(`<project>/scripts/okf.py` → `<project>/okf/`), which is why it must
live at `scripts/okf.py`.

## Step 2 — Ask where the bundle should live, then scaffold

**Ask the user what to name the bundle directory before creating it.**
Offer `okf/` as the default and accept it without further discussion if
they don't care. Some projects will want a name that says what the
knowledge is rather than what format it's in — `knowledge/`, `wiki/`,
`docs/kb/` — and any of those work identically.

Do not suggest a dot-prefixed name. The bundle is content people read
and edit, so hiding it from `ls` and from file explorers works against
it; dot-directories are for tooling config.

Then run `init`, passing `--bundle` only when they chose a non-default name:

```
python scripts/okf.py init                      # → okf/
python scripts/okf.py init --bundle knowledge   # → knowledge/
```

This creates the skeleton (empty type directories, a seed `SCHEMA.md`,
a seed `log.md`), regenerates `index.md`, and runs a health check. It
only creates what's missing — existing files are left untouched.

**The name is recorded by the directory itself, not by a config file.**
Every later `okf.py` call finds the bundle by looking for a top-level
directory containing `SCHEMA.md`, so no flag is needed again. Pass
`--bundle` afterwards only to disambiguate when a project genuinely
holds more than one bundle — okf.py errors out rather than guessing.

> The `init` command also tries to sync a canonical `skills/` folder to
> per-tool copies. In an installed project there usually is no top-level
> `skills/` folder, so that step simply reports "(none found)" — that's
> expected, not an error.

### Team wiki with several projects

When one bundle will hold knowledge for several projects, initialise
the bundle as above, then add each project as its own scope:

```
python scripts/okf.py init --project payments   # → okf/payments/
```

That writes `okf/payments/SCHEMA.md` (the project's own type registry,
tags and `# Code repositories` table), `log.md` and `sources/`, and
lists the project in the root `index.md`. The root `SCHEMA.md` then
holds only team-wide rules; each project fills in its own SCHEMA.md
in Step 3. Add `.okf-cache/` to `.gitignore` if projects will pin code
from other repositories (`okf.py drift` keeps blob-less clones there).

## Step 3 — Make the schema real

The seed `SCHEMA.md` is a starter. Before the first real ingestion,
fill in — with the user — the **Domain** paragraph (what this knowledge
base covers and for whom) and extend the **type registry** and **tag
taxonomy** to fit their material. Everything else in the lifecycle keys
off SCHEMA.md, so this is worth doing early. Keep the frontmatter and
section headings the seed established.

## Step 4 — Confirm and hand off

Run `python scripts/okf.py lint` and report the result. Then tell the
user the bundle is ready and which skill to reach for next:

- add material → **kb-ingest**
- ask a question → **kb-query**
- verify/refresh → **kb-review**
- restructure/dedupe → **kb-curate**
- health check → **kb-lint**
