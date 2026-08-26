---
type: Concept
title: Open Knowledge Format (OKF)
description: The storage format this bundle conforms to — markdown + YAML frontmatter bundles with reserved index/log files and permissive consumption.
status: active
confidence: high
created: 2026-07-05
updated: 2026-07-05
review_after: 2027-01-05
tags: []
sources:
  - /sources/2026-07-05-okf-spec-v0-1.md
---

# Open Knowledge Format (OKF)

OKF v0.1 defines a knowledge bundle as a directory of markdown files
with YAML frontmatter. The only hard conformance rule is that every
non-reserved `.md` file carries parseable frontmatter with a non-empty
`type`; everything else is convention, and consumers must be permissive
about unknown fields, types, and broken links [1].

This bundle conforms to OKF and extends it with the lifecycle profile
described in [the knowledge lifecycle](/concepts/knowledge-lifecycle.md);
all extension fields ride on OKF's explicit allowance for arbitrary
frontmatter keys, so the bundle stays readable by plain OKF consumers.
The bundle-local conventions built on top of OKF are defined in
[SCHEMA.md](/SCHEMA.md).

# Schema

| Element | Rule |
|---------|------|
| Concept file | frontmatter (`type` required) + markdown body |
| `index.md` | reserved catalog; frontmatter only at bundle root (`okf_version`) |
| `log.md` | reserved history; `## YYYY-MM-DD` headings, newest first |
| Links | `[t](/bundle/relative.md)` preferred; untyped edges, meaning in prose; broken links tolerated |
| Conventional headings | `# Schema`, `# Examples`, `# Citations` |

# Citations

[1] [OKF v0.1 spec capture](/sources/2026-07-05-okf-spec-v0-1.md)
