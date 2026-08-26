---
type: Source
title: okf.py — mechanical toolchain (scripts/okf.py)
description: Faithful condensation of scripts/okf.py — the six subcommands and the exact conformance/lifecycle rules its lint enforces, as of 2026-07-07.
source_url: repo://scripts/okf.py
ingested: 2026-07-07
sha256: 638fa5f9220f5e0c92671df2ece378d9d5f50ab016a56b38a4b449e9663cbf95
---

# okf.py — mechanical toolchain

Condensation of `scripts/okf.py` (stdlib-only; uses PyYAML if installed,
else a minimal frontmatter parser). `ROOT` = repo root, `KB` = `ROOT/kb`.
Reserved files: `index.md`, `log.md`. Statuses: draft, active,
needs_review, deprecated, archived.

## Subcommands

- **init** — Create bundle skeleton dirs (`concepts`, `entities`,
  `comparisons`, `queries`, `archive`, `sources`); seed `SCHEMA.md` and
  `log.md` if absent. Sync canonical `skills/` to two generated copies:
  `.claude/skills/` (copytree) and `.github/prompts/<name>.prompt.md`
  (generated wrapper per skill). Then regenerate index and run lint.
- **lint** — Conformance + lifecycle audit; exit 1 if any errors.
  `lint --inbound PATH` lists every md file linking to a bundle path
  (safe-delete check).
- **index** — Regenerate `kb/index.md` from the tree + frontmatter.
  Sections ordered: concepts, entities, comparisons, queries, sources,
  archive, then any others alphabetically. Root pages listed first.
  Status badge appended for needs_review / deprecated / archived.
- **log "MESSAGE"** — Prepend `* MESSAGE` under today's `## YYYY-MM-DD`
  heading (creates the heading after the H1 if absent). Warns above 500
  entries.
- **stats** — Counts by type and status; prints the review queue
  (needs_review, or active with review_after in the past).
- **drift** — Verify sha256 of every `sources/` capture against its
  recorded frontmatter hash. `drift --hash FILE` prints the sha256 of a
  file's body (used to fill in a new capture's frontmatter).

## Parsing model

- `split_frontmatter` strips a leading BOM, then matches a leading
  `---\n...\n---` block. PyYAML `safe_load` if available; otherwise
  `parse_yaml_min` handles `key: value`, inline `[a, b]` lists, and
  block (`- item`) lists only.
- `rel(path)` → bundle-relative path with leading slash, forward slashes.
- `resolve_link` resolves markdown link targets; treats `://` and
  `mailto:` as external (ignored), leading `/` as bundle-root-relative,
  else relative to the linking file's parent.
- `strip_code` removes fenced blocks and inline spans so example links
  in templates aren't linted as real links.
- `taxonomy()` scrapes known tags from the `# Tag taxonomy` section of
  `SCHEMA.md` (backtick-quoted list items).
- `body_hash` = sha256 of the body **below** the frontmatter (drift is
  blind to frontmatter edits).

## Exact lint rules

Iterates all non-reserved `*.md` under `kb/`. First collects inbound
links from every md file (including index/log).

**Errors (exit 1):**
- missing frontmatter; unparseable frontmatter.
- frontmatter has no non-empty `type` (OKF §9).
- unknown `status` value.
- `deprecated` without `superseded_by` and without a `## Deprecation`
  section in the body.
- an `index.md` outside the bundle root carrying frontmatter (only the
  root index may).

**Warnings:**
- source capture missing `sha256` or `source_url`.
- missing any of `title`, `description`, `status`, `updated`.
- `active` but no `review_after`.
- `archived` but not under `/archive/`.
- `active` with `review_after` in the past → "review overdue … set
  status: needs_review or re-verify".
- tag not in the SCHEMA.md taxonomy.
- `active`/`needs_review` page with fewer than 2 outbound bundle links.
- orphan: not linked from anywhere (including index.md).

**Info:** link to a not-yet-written page (allowed, not an error).

**Exemptions:** `SCHEMA.md` — OKF conformance applies but lifecycle
rules are skipped. `sources/*` — only the sha256/source_url warnings
apply; the rest are skipped.
