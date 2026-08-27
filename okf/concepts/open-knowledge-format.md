---
type: Concept
title: Open Knowledge Format (OKF)
description: The storage format this bundle conforms to — markdown + YAML frontmatter bundles with reserved index/log files and permissive consumption.
status: stable
lifecycle: active
confidence: high
created: 2026-07-05
updated: 2026-08-27
stale_after: 2027-01-05
tags: []
sources:
  - resource: /sources/2026-08-27-okf-spec-v0-2.md
    id: okf-spec-v2
    title: OKF v0.2 spec capture
  - resource: /sources/2026-07-05-okf-spec-v0-1.md
    id: okf-spec-v1
    title: OKF v0.1 spec capture
---

# Open Knowledge Format (OKF)

OKF defines a knowledge bundle as a directory of markdown files with
YAML frontmatter. The only hard conformance rule is that every
non-reserved `.md` file carries parseable frontmatter with a non-empty
`type`; everything else is convention, and consumers must be permissive
about unknown fields, types, and broken links [okf-spec-v2].

The spec moved out of `GoogleCloudPlatform/knowledge-catalog` into its
own repository, `GoogleCloudPlatform/open-knowledge-format`; the copy
this bundle was originally seeded from is a frozen snapshot, no longer
maintained [okf-spec-v2]. **This bundle targets v0.2.**

This bundle conforms to OKF and extends it with the lifecycle profile
described in [the knowledge lifecycle](/concepts/knowledge-lifecycle.md);
the extension fields ride on OKF's explicit allowance for arbitrary
keys — producers may add any, and consumers must not reject documents
carrying them [okf-spec-v2] — so the bundle stays readable by plain OKF
consumers. The bundle-local conventions built on top of OKF are defined
in [SCHEMA.md](/SCHEMA.md).

## What v0.2 changed

Two breaking changes from v0.1 [okf-spec-v2]:

- `timestamp` was replaced by `generated: { by, at }`.
- The numbered `# Citations` body list was replaced by the `sources`
  frontmatter field, whose entries carry a required `resource` and an
  optional `id` used to attribute individual claims.

The additions matter more here: v0.2 promoted **provenance**
(`sources`), **trust** (`generated`, `verified`) and **lifecycle**
(`status`, `stale_after`) from things a profile had to invent into
standard fields [okf-spec-v2]. Identity fields use an actor convention —
`human:<id>`, `<tool>/<version>`, `process:<id>` — and consumers that
classify trust key off the `human:` prefix.

### The one place this bundle bends

v0.2's `status` is a *standard* field with exactly three values:
`draft | stable | deprecated` [okf-spec-v2]. Under v0.1 this bundle's
five-state lifecycle was a harmless extension key; under v0.2 writing
`status: active` would put an illegal value in a standard field —
conformance lost for a formatting habit. So the five states moved to a
`lifecycle` extension key and `status` is derived from it, per the
mapping in [SCHEMA.md](/SCHEMA.md). Plain consumers read a legal
`status`; lifecycle-aware ones read the detail; nothing load-bearing
lives only in the extension.

# Schema

| Element | Rule |
|---------|------|
| Concept file | frontmatter (`type` required) + markdown body |
| `index.md` | reserved catalog; frontmatter only at bundle root (`okf_version`) |
| `log.md` | reserved history; `## YYYY-MM-DD` headings, newest first |
| Links | `[t](/bundle/relative.md)` preferred; untyped edges, meaning in prose; broken links tolerated |
| Conventional headings | `# Schema`, `# Examples`, `# Computation` |
| Provenance | `sources[]`: required `resource`, optional `id`/`title`/`author`/`last_modified` |
| Trust | `generated: { by, at }`, `verified: [{ by, at }]`, actor convention |
| Lifecycle | `status: draft \| stable \| deprecated` (default `stable`), `stale_after` |
| Extensions | any additional key; consumers must preserve and must not reject |
