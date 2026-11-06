---
type: Entity
title: okf.py — the Mechanical Toolchain
description: The stdlib-only script (scripts/okf.py) that mechanizes the bundle — init, lint, index, links, log, stats, drift — the exact conformance/lifecycle rules its lint enforces, project scopes, and drift on code in other repositories.
status: stable
lifecycle: active
confidence: high
created: 2026-07-07
updated: 2026-11-06
stale_after: 2027-05-06
tags: []
sources:
  - resource: /sources/2026-07-07-okf-toolchain.md
    id: okf-toolchain
    title: okf.py toolchain capture
  - resource: ../../scripts/okf.py
    id: okf-py
    title: scripts/okf.py implementation
    last_modified: 2026-11-06
    blob: 24824342325f
---

# okf.py — the Mechanical Toolchain

`scripts/okf.py` is the single stdlib-only script that mechanizes this
bundle. It is the "mechanical health only" layer: it enforces structure,
but never judges whether a claim is *true* — that
authority belongs to [kb-review](/entities/lifecycle-skills.md) [okf-toolchain].
Every one of the [lifecycle skills](/entities/lifecycle-skills.md) closes
out through it (`index` → `log` → `lint`), which is what makes the
[PR quality gates](/concepts/pr-quality-gates.md) Tier-1 CorrectnessCI a
formality for skill-driven changes. It is also what keeps the bundle a
conformant [OKF v0.2](/concepts/open-knowledge-format.md) reader target.

# Schema

Seven subcommands; `lint` and `drift` gate (exit 1 on failure).

| Command | Role |
|---------|------|
| `init` | Create dir skeleton + seed SCHEMA/log; sync canonical `skills/` → `.claude/skills/` and `.github/prompts/`; then index + lint. `--project NAME` instead scaffolds a project scope (own SCHEMA.md, log.md, sources/) |
| `lint` | Conformance + lifecycle audit (exit 1 on errors). `--inbound PATH` lists linkers to a bundle path; `--inbound URL` lists pages whose `sources` cite that external document, with the `last_modified` each was written against — the manual review trigger for SharePoint/LeanIX-style sources |
| `index` | Regenerate `index.md` from tree + frontmatter, with lifecycle badges — one per scope: the root lists its own pages plus a `# Projects` section, each project gets its own |
| `links` | Expand `[[slug]]`/`[[slug\|text]]` authoring shorthand into canonical bundle-relative links, in place |
| `log "MSG"` | Prepend an entry under today's `## YYYY-MM-DD` heading; `--project NAME` writes the project's `log.md` |
| `stats` | Counts by type/lifecycle/project, the review queue, and pinned-source drift; `--project` narrows it |
| `drift` | Recheck every pinned `sources[].blob` against the file's current git blob (exit 1 if any moved), fetching code repos named in SCHEMA.md (`--offline`: cache only). `--hash FILE` or `--hash REPO:PATH` prints the sha to pin; `--project` narrows it |

## What lint actually enforces

The rules below are the load-bearing part — they are how the
[lifecycle](/concepts/knowledge-lifecycle.md)'s status discipline is kept
honest mechanically rather than by memory.

**Errors (block, exit 1):**
- missing or unparseable frontmatter;
- no non-empty `type` (OKF §9);
- a `status` outside OKF v0.2's `draft | stable | deprecated`, an
  unknown `lifecycle`, or the two disagreeing with the mapping in
  [SCHEMA.md](/SCHEMA.md);
- a known `type` outside the directory its scope's type registry gives
  it (`archive/` exempt);
- a `sources` entry with no `resource`, or two entries sharing an `id`;
- a `repo:` source entry without `path:`, or naming a repo absent from
  every `# Code repositories` table in its scope chain;
- a `capture:` key that is not bundle-relative or points at a missing
  file;
- `deprecated` without `superseded_by` *and* without a `## Deprecation`
  section — i.e. deprecation must always leave a prose trail;
- a non-root `index.md` carrying frontmatter.

**Warnings (report, don't block):** missing `title`/`description`/
`status`/`lifecycle`/`updated`; `active` without `stale_after`; `active` past its
`stale_after` (overdue → should go `needs_review`); a pinned source that
moved or vanished; `archived` outside
`/archive/`; a `type` its scope's registry doesn't list; tag not in
the scope's taxonomy (root tags count everywhere); `active`/`needs_review`
page with < 2 outbound bundle links; orphan pages (no inbound links);
source captures missing `source_url`; a malformed `generated`/
`verified` entry (present but not a `{ by, at }` mapping); legacy v0.1
shapes — a `review_after` field, a bare-string `sources` entry, or a
surviving `# Citations` section; a project scope lacking its own
`index.md` or `log.md`; a `capture:` outside any `sources/` directory,
or beside a `resource` that is already local.

Note what lint deliberately does *not* warn about: a page with **no**
`generated` or `verified` at all. An absent stamp is an honest "nobody
recorded this"; warning would push whoever clears the queue into
inventing authorship or verification records, which is the one failure
those fields cannot survive. Shape is mechanical and gets checked;
presence is a claim and does not.

**Info:** links to not-yet-written pages — allowed by design, never an
error; a `repo:` pin not checked because its repository is not in the
local cache yet (lint never fetches); a SharePoint sharing or path
link (`/:w:/…`, `?e=`) cited as a source, since those expire, are
per-user or break on rename — the ID-based `Doc.aspx?sourcedoc=` form
is preferred.

**Exemptions:** each scope's `SCHEMA.md` is checked for OKF conformance
but skips lifecycle and type-registry rules; a scope's `sources/*` only
get the `source_url` warning.

## Project scopes (2026-11-06)

Any directory inside the bundle holding its own `SCHEMA.md` is a
project scope; a page belongs to the nearest one above it, else to the
root. Per page, lint reads that scope's type registry (no inheritance
from the root — OKF registers no types centrally, so each project names
its own, and a `lives in` may be nested, e.g. `docs/adr/`) and the
union of the root and scope tag taxonomies. Everything not
scope-specific — lifecycle, `status` mapping, source shape, links —
is enforced identically everywhere, which is how the root SCHEMA's
rules stay un-loosenable. `[[slug]]` matching pages in several projects
resolves to the linking page's own project before being called
ambiguous. A bundle with no project `SCHEMA.md` is one root scope and
behaves exactly as before; the conventions are in
[SCHEMA.md](/SCHEMA.md) under *Project scopes*.

## Immutability enforcement

The "never modify `sources/`" hard rule is enforced by **git, not by the
toolchain**. `git log -- okf/sources/` surfaces any post-ingestion edit
to a capture, and the pre-edit content stays recoverable — strictly more
than a stored hash offered, since a hash reports only *that* something
changed.

A `drift` subcommand previously stored a `sha256` of each capture body
in its own frontmatter and re-checked it. It was removed on 2026-08-27
as redundant with git: because it compared a local file against a number
stored in that same local file, it detected local tampering only. It
never detected the thing its name implied — a source changing *upstream*
— which requires re-fetching `source_url`, something no command does.
Captures written before that date may still carry a now-inert `sha256:`
key; it is an extension field and nothing reads it.

## Pinned-source drift (the `drift` rebuilt, 2026-08-27)

The `drift` subcommand was reintroduced the same day on a different
mechanism, and the distinction is the whole point: the pin now lives in
the **citing page**, and the content it describes lives in a **different
file**. A `sources` entry may carry `blob:`, twelve characters of the
git blob sha of a re-readable local file at the moment its claims were
verified; `drift` re-hashes that file and reports `moved` or `gone`,
and `lint` repeats the finding as a warning.

That is a real change detector, not a self-referential one — it fires
when the evidence moves, which the removed version structurally could
not. Its scope is equally specific:

- **Covers** files inside this repo, hashed from the working tree, so
  an uncommitted edit registers too.
- **Covers code in other git repositories** (since 2026-11-06): an
  entry with `repo:` + `path:` names a row of a SCHEMA.md
  `# Code repositories` table; `drift` keeps a bare, depth-1,
  `--filter=blob:none` clone of it under `.okf-cache/` (trees only, so
  cheap even for large repos) and compares `rev-parse <branch>:<path>`.
  A blank `branch` follows the remote's current default branch, asked
  afresh (`ls-remote --symref`) on every fetch, so switching the
  primary branch upstream surfaces as moved pins rather than going
  unnoticed.
  The blob id is git's own, so any host behaves the same. `lint` reads
  only that cache and never fetches; an unreachable or not-yet-fetched
  repo is reported as `unchecked`, never as stale.
- **Does not cover** non-git upstreams — a web page behind a
  `source_url`, or a SharePoint/LeanIX document cited by URL, still
  changes silently. That is deliberate: review of those is triggered by
  hand (`lint --inbound <url>`) and done by an agent re-opening the URL
  in a signed-in browser inside
  [kb-review](/entities/lifecycle-skills.md), not by API polling.
- **Does not cover** captures under `/sources/`: they are immutable, so
  drift on them is meaningless by construction.
- **Never edits frontmatter.** A moved pin is a prompt to re-verify;
  whether the change invalidates the page is judgment, and belongs to
  [kb-review](/entities/lifecycle-skills.md), which restamps `blob:`
  with `okf.py drift --hash <file>` (or `<repo>:<path>`) once the
  claims are re-checked.

This is what lets the cadence rules in [SCHEMA.md](/SCHEMA.md) treat
the clock as a backstop rather than the primary signal for anything the
repo can answer for.

## Parsing notes

- Prefers PyYAML; falls back to a minimal indentation-aware parser
  covering `key: value`, inline `[a, b]` lists and `{k: v}` maps, block
  lists of scalars *or* mappings (which is what `sources` entries are),
  and one level of nested mapping (`generated:`/`verified:`). Keep
  frontmatter within that subset so the tool works without PyYAML. A
  `key:` is only recognised when followed by whitespace, so a bare list
  item like `- https://example.com` is not misread as an `https:` key.
- `strip_code` blanks fenced blocks and inline code before link
  extraction, so example links inside templates/snippets are not linted
  as real outbound links or counted toward the 2-link minimum.
- Link tracking (graph, orphan/inbound checks, 2-link minimum) only
  understands bundle-relative markdown links. Wiki `[[slug]]` shorthand is
  an *authoring* convenience: `links` resolves each `slug` (by filename
  stem, title, or explicit `/path.md`) and rewrites it to the canonical
  form, skipping code spans and leaving ambiguous / not-yet-written
  targets in place. Run it before `index`/`lint`; `lint` warns on any
  surviving unexpanded or ambiguous `[[...]]` and files a missing target
  as info.

# Related pages

- [The Lifecycle Skill Suite](/entities/lifecycle-skills.md) — the
  prompt-based skills that *call* this toolchain at close-out; the tool
  is their mechanical gate.
- [The Knowledge Lifecycle](/concepts/knowledge-lifecycle.md) — the
  status machine whose invariants `lint` enforces.
- [Open Knowledge Format (OKF)](/concepts/open-knowledge-format.md) —
  the spec whose conformance clauses (`type`, reserved files, index/log
  rules) `lint` checks.
- [PR Quality Gates](/concepts/pr-quality-gates.md) — treats `lint` as
  the blocking Tier-1 mechanical check.
