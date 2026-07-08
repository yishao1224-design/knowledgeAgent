---
type: Entity
title: okf.py — the Mechanical Toolchain
description: The stdlib-only script (scripts/okf.py) that mechanizes the bundle — init, lint, index, links, log, stats, drift — and the exact conformance/lifecycle rules its lint enforces.
status: active
confidence: high
created: 2026-07-07
updated: 2026-07-08
review_after: 2027-01-07
tags: []
sources:
  - /sources/2026-07-07-okf-toolchain.md
---

# okf.py — the Mechanical Toolchain

`scripts/okf.py` is the single stdlib-only script that mechanizes this
bundle. It is the "mechanical health only" layer: it enforces structure
and detects drift, but never judges whether a claim is *true* — that
authority belongs to [kb-review](/entities/lifecycle-skills.md) [1].
Every one of the [lifecycle skills](/entities/lifecycle-skills.md) closes
out through it (`index` → `log` → `lint`), which is what makes the
[PR quality gates](/concepts/pr-quality-gates.md) Tier-1 CorrectnessCI a
formality for skill-driven changes. It is also what keeps the bundle a
conformant [OKF v0.1](/concepts/open-knowledge-format.md) reader target.

# Schema

Seven subcommands; `lint` and `drift` are the only ones that gate (exit 1
on failure).

| Command | Role |
|---------|------|
| `init` | Create dir skeleton + seed SCHEMA/log; sync canonical `skills/` → `.claude/skills/` and `.github/prompts/`; then index + lint |
| `lint` | Conformance + lifecycle audit (exit 1 on errors). `--inbound PATH` lists linkers to a bundle path |
| `index` | Regenerate `kb/index.md` from tree + frontmatter, with status badges |
| `links` | Expand `[[slug]]`/`[[slug\|text]]` authoring shorthand into canonical bundle-relative links, in place |
| `log "MSG"` | Prepend an entry under today's `## YYYY-MM-DD` heading |
| `stats` | Counts by type/status + the review queue |
| `drift` | Verify each source capture's `sha256`. `--hash FILE` prints a body hash |

## What lint actually enforces

The rules below are the load-bearing part — they are how the
[lifecycle](/concepts/knowledge-lifecycle.md)'s status discipline is kept
honest mechanically rather than by memory.

**Errors (block, exit 1):**
- missing or unparseable frontmatter;
- no non-empty `type` (OKF §9);
- unknown `status`;
- `deprecated` without `superseded_by` *and* without a `## Deprecation`
  section — i.e. deprecation must always leave a prose trail;
- a non-root `index.md` carrying frontmatter.

**Warnings (report, don't block):** missing `title`/`description`/
`status`/`updated`; `active` without `review_after`; `active` past its
`review_after` (overdue → should go `needs_review`); `archived` outside
`/archive/`; tag not in the SCHEMA taxonomy; `active`/`needs_review`
page with < 2 outbound bundle links; orphan pages (no inbound links);
source captures missing `sha256`/`source_url`.

**Info:** links to not-yet-written pages — allowed by design, never an
error.

**Exemptions:** `SCHEMA.md` is checked for OKF conformance but skips
lifecycle rules; `sources/*` only get the sha256/source_url warnings.

## Drift model (immutability enforcement)

`drift` hashes the source body **below** the frontmatter and compares it
to the recorded `sha256`. This is the mechanism behind the "never modify
`kb/sources/`" hard rule: editing a capture changes its body hash and
`drift` reports DRIFT. Adding a new capture is a two-step move —
`drift --hash <file>` to get the hash, paste it into the frontmatter.
Because the hash covers only the body, frontmatter fixes are invisible
to drift.

## Parsing notes

- Prefers PyYAML; falls back to a minimal parser covering `key: value`,
  inline `[a, b]` lists, and block `- item` lists only. Keep source
  frontmatter within that subset so the tool works without PyYAML.
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

# Citations

[1] [okf.py toolchain capture](/sources/2026-07-07-okf-toolchain.md)
