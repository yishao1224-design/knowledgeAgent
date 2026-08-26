---
type: Concept
title: User Story Analysis Workflow (Ingest After Verify)
description: The bundle-integrated pipeline for working a user story — query first, flag contradictions at analysis time, implement and verify, ingest what shipped last.
status: active
confidence: low
created: 2026-07-08
updated: 2026-07-08
review_after: 2026-08-08
tags: [unverified]
---

# User Story Analysis Workflow (Ingest After Verify)

How a user story flows through the bundle: the story is analyzed
*against* existing knowledge at the start, and its verified outcome is
captured *into* the bundle at the end. Distilled from a design
conversation (2026-07-08); a proposed practice, not yet exercised on a
real story — hence `unverified`.

```
query → analyze → implement → test/verify → ingest → story closes
```

## The pipeline

1. **Query the bundle first** (kb-query behavior — see the
   [lifecycle skill suite](/entities/lifecycle-skills.md)): what do we
   already know about the modules, business rules, and personas this
   story touches? Trust labels matter here — a `needs_review` page
   about the affected module is exactly what the analyst must see
   before writing acceptance criteria on top of it.
2. **Analyze the story** — gaps against documented invariants, impacted
   concepts, questions for the PO. The single most valuable output is
   "this story's acceptance criteria contradict a documented invariant"
   — which only querying first can produce.
3. **Implement, test, verify** — outside the bundle's concern, except
   for the in-flight caveat below.
4. **Ingest last** (kb-ingest behavior): capture the story
   **as-shipped**, update the affected concept pages, close the
   Definition-of-Done gate defined in
   [ingesting requirements from ticket systems](/concepts/ingesting-requirements-from-ticket-systems.md).

## Why ingest comes last

- **You capture what shipped, not what was planned.** Stories mutate
  between analysis and done — acceptance criteria get renegotiated,
  edge cases surface, scope gets cut. Ingest-at-analysis captures
  intent that decays within days; ingest-after-verify captures
  verified behavior.
- **Verification earns real confidence.** A page distilled from a
  passing, verified implementation legitimately starts `active` with
  `confidence: medium/high` — the claims were just executed against
  reality. A pre-implementation page would honestly be `draft`/`low`
  and owe a re-verification pass later; ingest-last collapses two weak
  writes into one strong one.
- **The DoD gate sits where the story already closes.** The knowledge
  update and the story's final gate become the same act.

## Carve-outs

1. **Contradiction flagging cannot wait for the end.** If the query
   step reveals the story conflicts with a documented invariant, flag
   the affected page **at analysis time**: `## Contradictions` section,
   `contested` tag, `status: needs_review`. It might mean the *story*
   is wrong and implementation should pause; and until resolved,
   anyone else querying that page must see it is contested. Flagging
   changes no claims — it defers the writing of knowledge, not the
   raising of alarms.
2. **The in-flight window is a known cost.** While implementation runs,
   the bundle is knowingly behind. The flags from carve-out 1 cover
   pages *known* to be affected; the `review_after` backstop (scoped
   per [SCHEMA.md](/SCHEMA.md)) covers the rest.

## Analysis-time code cross-check

During steps 1–2 the agent has both the affected code and the affected
KB pages in context — so it **cross-checks the pages' claims against
the live code and updates trust labels**. This is the change-triggered
detector the rest of the machinery lacks: `drift` only guards captures,
`review_after` only watches the clock, and the DoD gate only fires when
the process is followed. The cross-check works from the current state
of the code, so it also catches hotfixes with no story and gate-skipped
changes — and it makes freshness *attention-driven*: pages about hot
code get re-verified on every story that touches them, cold pages fall
back to the backstop.

Guardrails:

1. **Scope**: only the pages whose claims the analysis actually leans
   on (acceptance criteria, implementation plan) — not a sweep of
   everything one hop away. General audits stay with
   [kb-review](/entities/lifecycle-skills.md)'s queue.
2. **Asymmetric authority** — demote freely, affirm carefully, never
   rewrite:

   | Finding | Analyst-agent may… |
   |---------|--------------------|
   | Code contradicts a page claim | Flag immediately: `needs_review` + `## Contradictions` note with file refs (status-only, same as carve-out 1) |
   | Code confirms the claims checked | Bump `review_after` — only for a genuine verification, with a `**Review**` log entry (kb-review work done opportunistically) |
   | Page wrong, fix obvious | Still no mid-analysis rewrite — content correction belongs to the ingest step or kb-review |

3. **A mismatch is a three-way question.** Page stale, code buggy
   relative to intent, or story assumptions wrong — a page can state
   the business rule correctly while the code violates it, and
   auto-"fixing" the page would launder a bug into documented behavior.
   Flag as contested; a human or kb-review resolves.

A derived code index (see
[codebase-memory-mcp vs the kb wiki](/comparisons/codebase-memory-mcp-vs-kb-wiki.md))
is what makes this check cheap enough to run on every story instead of
hand-grepping.

## Capture rule

Snapshot the story text **as-shipped at ingest time** (final acceptance
criteria, post-negotiation), not as-analyzed. If the story changed
materially mid-flight and the evolution itself matters, use the dated
re-capture audit-trail pattern — but do not capture twice by default;
that is backlog-mirroring creep.

## When many stories feed one concept

A concept page normally accumulates contributions from multiple
stories over time; trust fields then follow the **weakest-link
semantics** defined in
[the knowledge lifecycle](/concepts/knowledge-lifecycle.md). Two
ingest-step disciplines follow:

- **Don't re-warrant untouched claims.** Ingesting story #N's outcome
  updates one section and bumps `updated:` — but resetting
  `review_after` from `updated` would silently vouch for claims from
  earlier stories nobody looked at. Either genuinely re-check the old
  claims while they're in context (the analysis-time cross-check
  usually already has), or set `review_after` for the
  least-recently-verified claim on the page.
- **Story-vs-story disagreement is usually evolution, not
  contradiction.** If story #N changes the rule an earlier story
  established, rewrite the claim and cite the new capture — the old
  capture stays in `/sources/` as the audit trail of how the
  requirement evolved. Reserve `contested`/`## Contradictions` for
  genuine ambiguity about whether the new story supersedes a
  still-valid rule — that ambiguity is a PO question, which is exactly
  what analysis-time flagging exists for.

## Composition principle

Reference the lifecycle skills, do not copy their steps. A
story-analysis skill says "perform kb-query's workflow for the affected
concepts" and "close via kb-ingest," so the suite's division of
responsibility stays intact and skill edits propagate. One deviation by
default: skip kb-query's Query-page filing — the analysis output
belongs in the story (tracker comment / AC) and in updated concept
pages, not as a third artifact.

## Open Questions

- One skill with a pause point, or two thin skills (`story-analyze` /
  `story-close`)? Leaning two — the analysis-to-verify gap can be
  weeks, sessions are the natural unit, and "run story-close on story
  #N" is a cleaner DoD checklist item. Undecided.
- The reverse trace (story → affected pages) has no mechanism yet;
  today it is a habit, not a check.
