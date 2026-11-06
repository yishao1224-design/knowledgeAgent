---
type: Schema
title: Bundle Schema & Conventions
description: Authoritative conventions for this OKF bundle — types, tags, frontmatter templates, lifecycle rules.
status: stable
lifecycle: active
updated: 2026-11-06
---

# Bundle Schema & Conventions

This bundle follows **OKF v0.2** plus the lifecycle profile described
here. When this file and habit disagree, this file wins. When this file
and `CLAUDE.md` disagree, this file wins for content conventions;
`CLAUDE.md` wins for process.

The spec now lives at
[GoogleCloudPlatform/open-knowledge-format](https://github.com/GoogleCloudPlatform/open-knowledge-format);
the copy under `knowledge-catalog/okf/` this bundle was seeded from is a
frozen v0.2 snapshot, no longer maintained. See
[Open Knowledge Format (OKF)](/concepts/open-knowledge-format.md) for
what v0.2 changed and why this bundle splits `status` from
`lifecycle`.

# Domain

*(Fill in on first real ingestion: one paragraph on what this knowledge
base is about and who consumes it. The directory layout below may be
renamed to fit the domain — update this file and re-run
`python scripts/okf.py index` if you do.)*

# Directory layout

```
okf/            # default name; a project may choose another
├── index.md          # generated catalog (okf.py index)
├── log.md            # append-only history (okf.py log)
├── SCHEMA.md         # this file
├── concepts/         # ideas, definitions, explanations
├── entities/         # concrete things: people, orgs, systems, datasets
├── comparisons/      # X-vs-Y analyses
├── queries/          # filed answers from kb-query worth keeping
├── archive/          # archived concepts (lifecycle: archived)
└── sources/          # IMMUTABLE raw captures
    ├── YYYY-MM-DD-<slug>.md
    └── assets/       # load-bearing binary evidence (see Source assets)
        └── YYYY-MM-DD-<slug>.<ext>
```

# Project scopes (multi-project bundles)

One bundle can hold several projects. A **project** is any directory
inside the bundle that carries its own `SCHEMA.md`; every page belongs
to the nearest such directory above it (else to the bundle root). This
bundle has none — it is a single root scope — but the toolchain and
skills support them for a team wiki:

```
team-wiki/okf/
├── SCHEMA.md          # team rules — the hard rules below hold everywhere
├── index.md           # root catalog; lists projects under "# Projects"
├── log.md             # team-level changes only
├── <shared pages>     # cross-project knowledge, governed by this file
└── payments/
    ├── SCHEMA.md      # the project's own types, dirs, tags, code repos
    ├── index.md       # generated per project (OKF §8: any directory)
    ├── log.md         # the project's history (OKF §9: "that scope")
    ├── sources/       # its immutable captures
    └── <its own dirs> # e.g. decisions/ runbooks/ — whatever it registers
```

What each level owns:

| Root `SCHEMA.md` (no project may loosen) | Project `SCHEMA.md` (owned outright) |
|---|---|
| Frontmatter minimum, `status`/`lifecycle` mapping, lifecycle states | **Type registry** — its own type names and directories; nothing inherited, since OKF registers no types centrally |
| Source immutability, source-entry shape, bundle-relative links | **Tag taxonomy** — added to the root's, which stays usable |
| Every edit logged, deprecate-don't-delete | **Code repositories** table (overrides a same-named root row) |
| | Review cadence, body templates, the project description |

Types differ across projects by design. Each registry row states the
type's **meaning**, and that column is what lets an agent map one
project's `Decision` to another's `ADR` when a question spans projects.

Tooling: `okf.py init --project NAME` scaffolds a project; `index`
writes one `index.md` per scope; `log`, `stats` and `drift` take
`--project NAME`; lint checks each page against its own scope's
registry and taxonomy, and warns when a project lacks `index.md` or
`log.md`. A `[[slug]]` matching pages in several projects resolves to
the linking page's own project. Links stay bundle-relative
(`/payments/decisions/x.md`), so pages link across projects freely.

# Page frontmatter template (all types)

Shared by every page type — `Concept`, `Entity`, `Comparison`, `Query`.
Set `type` and the directory to match: `Entity` pages live in
`entities/`, `Comparison` in `comparisons/`, `Query` in `queries/`, per
the type registry below. **Do not default to `type: Concept`** just
because this template's example shows it.

```yaml
---
type: Concept            # required (OKF). Match to directory — see type registry below.
title: Human Readable Title
description: One sentence, used in index.md and previews.
status: draft            # OKF v0.2 standard: draft | stable | deprecated
lifecycle: draft         # draft | active | needs_review | deprecated | archived
confidence: medium       # low | medium | high — how well-sourced the claims are
created: 2026-07-05
updated: 2026-07-05
stale_after: 2026-10-05  # required once lifecycle: active
tags: [tag-from-taxonomy]
sources:                 # see "Source entries" below
  - resource: /sources/2026-07-05-example.md
    id: example
    title: Example capture
generated:               # who produced this content, stamped at write time
  by: claude-code/opus-5   # <tool>/<version> — whatever agent is running
  at: 2026-07-05
verified:                # optional; one entry per real re-verification
  - by: human:maintainer
    at: 2026-07-05
supersedes: /concepts/old-page.md      # optional
superseded_by: /concepts/new-page.md   # required when lifecycle: deprecated
---
```

## `status` vs `lifecycle`

OKF v0.2 promoted `status` to a standard field with exactly three
values — `draft | stable | deprecated`. This bundle's five-state
lifecycle is richer than that, so it lives in the `lifecycle`
**extension** key and `status` is derived from it:

| `lifecycle` | `status` |
|-------------|----------|
| `draft` | `draft` |
| `active` | `stable` |
| `needs_review` | `stable` — still served, flagged in answers |
| `deprecated` | `deprecated` |
| `archived` | `deprecated` |

Write both; lint errors if they disagree. A plain v0.2 consumer that
ignores extension keys still reads a legal `status`; a lifecycle-aware
one reads the detail. Per the conformance rule, the body prose must
still say when a page is deprecated or contested — the extension key
alone is not allowed to carry that meaning.

`generated` and `verified` both use the v0.2 actor convention:
`human:<id>` for a person, `<tool>/<version>` for an agent or tool,
`process:<id>` for automation. Consumers classify trust off the
`human:` prefix, so use it for anything a person actually confirmed.

The two are **not** interchangeable, and keeping them apart is what
makes either worth reading:

- `generated` records what **produced** the content. kb-ingest stamps
  it on every page it writes or rewrites — it is a fact about
  authorship, costs nothing, and needs no verification to be true.
  Whoever rewrites a body replaces the **whole** field with their own
  `{ by, at }`: it is one provenance event, so bumping `at` while
  leaving someone else's `by` behind attributes the new text to the
  wrong producer.
- `verified` records who **confirmed** it, and only kb-review writes
  it. An agent stamping `verified` on a page it just wrote would be
  attesting to its own output in the same motion; that is `generated`,
  not confirmation.

So the ordinary state of a fresh page is *generated by an agent, never
verified* — legible, honest, and exactly what it says. Do not backfill
either field for pages whose authorship or verification you cannot
actually establish.

# Source-capture frontmatter template

Files under `sources/` are verbatim or near-verbatim captures. Immutable
after creation — git history is the tamper record; `git log -- sources/`
surfaces any post-ingestion edit, with the original recoverable.

```yaml
---
type: Source
title: Original Article Title
description: One sentence on what this source covers.
source_url: https://example.com/article
ingested: 2026-07-05
---
```

# Source entries (frontmatter `sources`)

Every entry is a mapping with a required `resource`, per OKF v0.2.
Three kinds live in the same list:

```yaml
sources:
  - resource: /sources/2026-07-12-example.md   # frozen capture
    id: example-readme
    title: Example README capture
  - resource: ../../scripts/okf.py             # live repo file
    id: okf-py
    title: scripts/okf.py implementation
    last_modified: 2026-08-27
    blob: 9a37baf0dd06
  - resource: https://github.com/acme/payments-svc/blob/main/src/refund.py
    id: refund-py                              # code in another repo
    title: refund.py in payments-svc
    repo: payments-svc                         # a row in # Code repositories
    path: src/refund.py
    last_modified: 2026-11-06
    blob: 3f9a1c0d2e44
```

- **Frozen captures** are bundle-relative (`/sources/...`) and immutable.
  Use them for anything that cannot be re-read later — a web page, a
  conversation, a verification already performed.
- **Live files** are document-relative, so a page in `entities/` reaches
  repo files as `../../path` — that form resolves both on disk and as a
  rendered link. Pin them with `blob:` (12 chars of the git blob sha,
  from `okf.py drift --hash <file>`) and record `last_modified:` as the
  date you checked.
- **Code in another repository** — the normal case for a wiki kept
  apart from the code it describes. `repo:` names a row of a
  `# Code repositories` table (`| repo | url | branch |`) in the page's
  project `SCHEMA.md` or the root one; `path:` is the file within it;
  `resource:` is a browse URL for humans and plain OKF readers. Get
  `blob:` from `okf.py drift --hash <repo>:<path> --project <name>`.
  `drift` keeps a blob-less, depth-1 clone of each repo under
  `.okf-cache/` (gitignored) and re-resolves `<branch>:<path>` — git's
  own blob id, so GitHub, Azure DevOps, GitLab and local paths behave
  the same; credentials are whatever git on that machine already has.
  A blank `branch` follows the remote's *current* default branch,
  re-read on every fetch. The wiki describes one branch per repo row:
  when the primary branch changes, edit the row (or the remote's
  default), run `drift`, and re-verify what it flags as moved.
  Lint never fetches: it reads the cache and reports an unfetched repo
  as info. Never freeze such code into a capture instead — that blinds
  drift to it.

Pinning is what turns review from calendar-driven into signal-driven:
`okf.py drift` recomputes each pinned file's blob and reports `moved`
or `gone`, and lint surfaces the same as warnings. A moved pin is a
prompt to re-verify, **not** an automatic status change — deciding
whether a changed file invalidates the page is judgment, and belongs to
`kb-review`.

Pin only what a claim actually rests on. If a page's whole content is
re-derivable from the file it points at, the page should not exist:
delete it and let the agent read the file. Do not pin a capture under
`/sources/` — captures never change, so drift on them is meaningless.

`id` is the citation key: cite it in the body as `[okf-py]`. Ids must be
unique within a page (lint errors on duplicates).

# Source assets (binary evidence)

Most binaries are **not** kept: extract their knowledge into the `.md`
capture and point `source_url` at the authoritative copy (SharePoint,
the tracker, a URL). Keep a binary in `sources/assets/` only when
**the pixels are the evidence** and there is no authoritative home —
above all, dense architecture diagrams and annotated screenshots that
cannot be fully extracted in one pass and will be re-read on later
ingests and reviews.

- Name: `assets/YYYY-MM-DD-<slug>.<ext>`, referenced from at least one
  source capture, whose body says what the asset shows and what has
  been extracted from it *so far* (an asset may yield more on a later
  pass — note what remains unread).
- Assets are **immutable like captures**: an updated diagram is a new
  dated file, never an overwrite.
- The capture's written description of the asset is what a reviewer
  checks it against; a mismatch between description and image is a
  review flag.
- Size discipline: small images only. Decks/PDFs/videos stay at their
  authoritative home; when in doubt, extract harder rather than commit
  bigger.

# Type registry

No central registry is required by OKF, but *this bundle* uses:

| type | lives in | meaning |
|------|----------|---------|
| `Concept` | `concepts/` | An idea, definition, method, or explanation |
| `Entity` | `entities/` | A concrete nameable thing |
| `Comparison` | `comparisons/` | Structured X-vs-Y |
| `Query` | `queries/` | A filed answer to a real question |
| `Source` | `sources/` | Immutable raw capture |
| `Schema` | root | This file only |

Add new types here before first use. **Lint enforces this table**: a
`type` not listed here is a warning; a known `type` in the wrong
directory is an error (`archive/` is exempt — archived pages keep
their original type).

# Tag taxonomy

*(Seed list — extend here BEFORE using a new tag anywhere.)*

- `unverified` — claims not yet checked against a second source
- `contested` — sources actively disagree; body must have a `## Contradictions` section

# Body conventions

- Prefer structure (headings, tables, lists, code blocks) over prose.
- Conventional headings with defined meaning: `# Schema`, `# Examples`
  (per OKF), plus bundle-local `## Contradictions` and `## Deprecation`.
- Every non-draft concept: **≥ 2 outbound bundle-relative links** in the
  body. Links assert relationships; say the relationship in prose around
  the link.
- Claims from outside the bundle are cited inline by source id —
  `…ships its own provider layer [openwiki]` — resolving against the
  `sources` frontmatter. v0.2 replaced the numbered `# Citations`
  section with `sources`; lint warns if one reappears.

# Domain-concept body template

Applies **only** to `Concept` pages describing **domain** knowledge
(business rules, processes, behavior of the systems the team builds).

It does **not** apply to `Entity`, `Comparison`, or `Query` pages, nor
to method/meta `Concept` pages (how this bundle itself works,
engineering practices) — all of those keep free structure instead:
pick headings that fit the subject (e.g. `# Schema`, `# Related pages`)
rather than forcing `## Definition`/`## Key Behaviors`. See
[okf-toolchain.md](/entities/okf-toolchain.md) for a worked
`Entity` example. General body conventions above still apply to every
type regardless of body structure, including inline `[source-id]`
citation of externally-derived claims and the ≥2-outbound-link rule.

Required sections: `## Definition`, at least one of `## Key Behaviors`
or `## Invariants`, and `## Related Concepts`. Every other section is
optional — include it only when it has real content. **Never write
`N/A` placeholders**; an absent section reads the same and costs
nothing.

```markdown
# <Concept Name>

## Definition
1–3 sentences: what it is, where it applies, why it matters.

## Key Behaviors
- <behavior>

## Variants                      (optional)
### <Variant A>
- <difference or special requirement>

## Invariants
Rules that must hold regardless of status, entry point, or variant.
- <rule>

## Personas                      (optional)
- <persona> — <what they need from this concept>

## Related Artifacts             (optional)
- `<StableIdentifier>` (<artifact type>) — one-line role

## Related Concepts
- [Concept A](/concepts/concept-a.md) — <relationship>

## Open Questions                (optional)
- <unresolved question>
```

Template rules:

- The **committed** form of a link is always a bundle-relative markdown
  link (`[Title](/concepts/foo.md)`) — lint's link tracking, the graph,
  and the safe-delete check depend on it, and plain OKF readers can only
  follow that form.
- While **authoring**, you may write `[[slug]]` or `[[slug|display text]]`
  shorthand (`slug` = a page's filename stem or title; or an explicit
  `[[/path.md]]`). Run `python scripts/okf.py links` to expand every
  shorthand into the canonical form *before* `index`/`lint`. Expansion
  skips code spans, and leaves ambiguous / not-yet-written targets in
  place — lint then flags any `[[...]]` that survived (unexpanded/
  ambiguous → warning, missing target → info).
- **Artifacts** are deployable code/metadata components (e.g.
  Salesforce Apex classes, LWC, triggers, Flows). Reference them by
  stable identifier plus a one-line role. Do not document an artifact's
  internals here (that belongs in the code), and do not create a page
  per artifact — an artifact gets an `Entity` page only when it meets
  the page-creation threshold below.
- If `## Open Questions` accumulates items that contradict the page's
  own claims, set `lifecycle: needs_review` (and tag `contested` where
  sources disagree) instead of only annotating.

# Page-creation threshold

Create a new page only if the subject (a) is referenced by 2+ sources or
existing pages, or (b) is central enough that other pages need to link
to it. Otherwise fold the material into the closest existing page.

# Review cadence defaults

`stale_after` is a **backstop, not the primary freshness mechanism** —
a dead-man's-switch that guarantees an `active` page is eventually
re-affirmed even when nothing else prompts it. It fires on the clock,
not on change, so it cannot tell "nothing changed" from "everything
changed." Scope the cadence to whether the page already has a *real
change signal*; running one blunt offset uniformly is what turns the
review queue into ignorable noise.

The `stale_after` **date is an internal maintainer field.** Readers
never interpret it — the user-facing signal is the `lifecycle:
needs_review` flag surfaced in answers, which the overdue date merely
triggers.

Prefer a real change signal over the clock wherever one exists. In
order of precedence:

1. **A pinned `blob:` that moved** (`okf.py drift`) — exact, mechanical,
   fires on the change itself. Available for any claim resting on a file
   in this repo; pin it and lengthen the timer.
2. **A tracked change process** — the story / Definition-of-Done trigger
   in [ingesting requirements](/concepts/ingesting-requirements-from-ticket-systems.md).
   Human discipline, so it needs (1) or (3) behind it.
3. **`stale_after` expiry** — the only mechanism left for external or
   ephemeral facts, and the one that fires blind.

Baseline offset from `updated`, by confidence:

| confidence | offset |
|-----------|--------|
| high | +6 months |
| medium | +3 months |
| low | +1 month |

Then adjust by change signal:

| The page's truth is governed by… | Cadence |
|----------------------------------|---------|
| A file in this repo, pinned with `blob:` | **Backstop only — lengthen well past the baseline.** Drift detection fires on the change itself; the timer only catches claims the pin does not cover. |
| A change process the bundle already tracks — e.g. domain code driven by user stories (see [ingesting requirements](/concepts/ingesting-requirements-from-ticket-systems.md)) | **Backstop only — lengthen well past the baseline.** The story / Definition-of-Done trigger is the real freshness signal; a short timer here is pure noise. |
| Nothing the bundle can track — external/volatile facts (pricing, versions, org charts, live URLs) | **Short — 1 month regardless of confidence.** This is where `stale_after` earns its keep; no other mechanism catches these. |
| `unverified` conversation takeaways with no source | Short (≤ 1 month) — force a second look before the claim is trusted. |

A chronically-ignored review queue means the offsets are wrong for
those pages (too short for backstop-only pages), not that the field is
worthless — retune toward the table above rather than muting the
warning. If a queue entry keeps coming back with nothing to change, ask
whether the page could carry a pin instead of a shorter timer.

# Log conventions

`## YYYY-MM-DD` headings, newest first; entries as
`* **Verb**: text with [links](/path.md).` Verbs in use: **Creation**,
**Update**, **Review**, **Merge**, **Split**, **Deprecation**,
**Archive**, **Ingestion**, **Lint-fix**. Rotate at ~500 entries
(`okf.py log` warns; move old entries to `archive/log-YYYY.md`).

In a multi-project bundle each project keeps its own `log.md`
(`okf.py log --project NAME "..."`), and orientation reads the
project's log, not the root's. The root `log.md` records only
team-level changes — the root SCHEMA, root-level shared pages, adding,
renaming or moving projects — so it stays short and is read only when
doing team-level work.
