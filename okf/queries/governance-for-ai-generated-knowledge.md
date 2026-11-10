---
type: Query
title: Governance for AI-Generated Knowledge at Organisation Scale
description: How to validate, approve and version agent-written knowledge before it becomes discoverable across a large organisation — discoverability tiers, roles, a three-stage PR pipeline, git as the version system.
status: draft
lifecycle: draft
confidence: low
created: 2026-11-10
updated: 2026-11-10
stale_after: 2026-12-10
tags: [unverified]
sources:
  - resource: /sources/2026-11-10-governance-federation-cost-qa.md
    id: qa-2026-11-10
    title: "Q&A capture: governance, federation, token cost"
generated:
  by: claude-code/2.1.322
  at: 2026-11-10
---

# Governance for AI-Generated Knowledge at Organisation Scale

> **Question:** What governance model do you recommend for validating,
> approving, and versioning AI-generated knowledge before it becomes
> discoverable across the Danfoss organization? [qa-2026-11-10]

**Status:** draft, unverified — an agent-written recommendation that
has not been tried at organisation scale. Treat it as a design
proposal until a pilot confirms it.

## Answer

**Gate discoverability, not writing.** Anyone may let an agent write;
content becomes widely findable only after a named human verifies it.
The mechanism already exists in OKF v0.2 and this bundle's
[lifecycle](/concepts/knowledge-lifecycle.md): `generated` records
what produced a page, `verified` records a `human:` who confirmed it,
and the two never merge [qa-2026-11-10].

| Tier | State | Discoverable by | Gate |
|------|-------|-----------------|------|
| 0 | `draft`, generated only | Owning team's bundle, labelled unverified | Any contributor, via an agent |
| 1 | `active` + `human:` verification | The domain | Reviewer checked each claim against its cited source |
| 2 | Published | Organisation-wide catalog and search | Named page owner approved; classification check passed |

**Roles:** contributors; page/domain owners via CODEOWNERS; a knowledge
platform team owning `SCHEMA.md`, skills, toolchain and CI; an
information-security reviewer only when content crosses an access
boundary [qa-2026-11-10].

**Pipeline** — the three tiers of
[PR quality gates](/concepts/pr-quality-gates.md), extended for
organisation use:

1. Blocking deterministic CI — lint, append-only sources, log
   discipline, index freshness, drift, **plus** a secrets/personal-data
   scan and a classification check.
2. Advisory LLM review — duplicates, unflagged contradictions,
   unsupported citations; comments only.
3. Human approval scaled by blast radius — platform owner for the
   rules, domain owner for org-wide publication, one teammate otherwise.

**Versioning:** git commits per change; immutable dated captures;
blob pins for claims about code (see
[okf-toolchain](/entities/okf-toolchain.md)); deprecate with
`superseded_by`; tag organisation-wide catalog releases so answers can
cite a knowledge version [qa-2026-11-10].

**After approval:** `stale_after` makes approval expire; drift and
contradictions return pages to `needs_review`. Health metrics: %
verified, review-queue age, drifted pins, ownerless pages.

## What exists vs what is missing

- Built: lifecycle, generated/verified split, lint, drift.
- Designed, not wired: the PR gates — no CI job exists yet.
- Missing for organisation use: a classification field and its lint
  check, the organisation catalog, secrets/personal-data scanning.

## Related pages

- [Unified knowledge layer across tools](/queries/okf-unified-knowledge-layer-across-tools.md) —
  the permissions half of the same question: what discoverability means
  when bundles span access boundaries.
- [Token cost of the LLM Wiki](/queries/token-cost-of-the-llm-wiki.md) —
  why human review time, not tokens, dominates the cost of this model.
