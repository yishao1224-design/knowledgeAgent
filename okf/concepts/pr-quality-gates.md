---
type: Concept
title: PR Quality Gates for a Team-Shared Bundle
description: Three-tier merge guardrails for a git-managed wiki/bundle — blocking mechanical CI, advisory LLM review, human gates scoped by blast radius; conformance at merge, truth via lifecycle.
status: stable
lifecycle: active
confidence: low
created: 2026-07-06
updated: 2026-08-27
stale_after: 2026-08-06
tags: [unverified]
---

# PR Quality Gates for a Team-Shared Bundle

When a team maintains the bundle through git PRs, merge-time guardrails
are worth adding — the toolchain anticipates it (`okf.py lint` exits 1
on errors precisely so CI can consume it). The governing principle:
**block on cheap deterministic checks; keep judgment checks advisory.**
A knowledge base dies from friction faster than from errors — if
updating the wiki is painful, people stop, and a stale wiki is worse
than an imperfect one.

# Schema

## Tier 1 — blocking CI (deterministic, seconds)

Maps directly onto the hard rules; no LLM required:

| Check | Enforces | Mechanism |
|-------|----------|-----------|
| `python scripts/okf.py lint` | Frontmatter, OKF conformance, taxonomy | Exits 1 on errors |
| Source immutability | Hard rule 1 | `git diff --name-status base...HEAD -- okf/sources/` — reject anything not `A` (added) |
| Log discipline | Hard rule 2 | Diff touching the bundle must also touch its `log.md` |
| Index freshness | Regenerated catalog | Run `okf.py index` in CI; fail if the tree becomes dirty |

Source immutability is the guardrail most worth automating: a silent
edit to a capture corrupts the audit trail, and nothing in the
toolchain blocks one — a CI job diffing the PR against `okf/sources/`
and failing on any modification to an existing file is the gate that
would.

## Tier 2 — advisory review (judgment, non-blocking)

Things lint cannot see: duplicate concepts vs the index, pages that
fail the page-creation threshold, contradictions with `active` pages
missing a `## Contradictions` section, citations unsupported by the
cited capture. An LLM PR-review step posting *comments* fits here — do
not make it blocking, or false positives on judgment calls train the
team to rubber-stamp overrides.

## Tier 3 — human gates, scoped by blast radius

- **the bundle's `SCHEMA.md`, `skills/`, `scripts/okf.py`** define the rules
  everyone plays by — require a designated owner's approval
  (CODEOWNERS).
- **Ordinary concept pages** — one teammate's review suffices.

## Conformance at merge, truth via lifecycle

Do not try to guarantee correctness at merge time. The
[knowledge lifecycle](/concepts/knowledge-lifecycle.md) exists so that
"captured but not yet verified" is a legitimate, visible state
(`draft`, `needs_review`, `confidence`) rather than something a PR gate
must prevent: merged pages carry `stale_after` and get caught by
kb-review later. The PR bar is *structure and immutability*; truth is
enforced over time. Teams adopting the bundle (see
[adopting the bundle pattern](/concepts/adopting-the-bundle-pattern.md))
should wire Tier 1 in from day one; automated pipelines writing to the
bundle rely on the same gates as their transaction boundary — see
[automating the lifecycle](/concepts/automating-the-lifecycle.md).
