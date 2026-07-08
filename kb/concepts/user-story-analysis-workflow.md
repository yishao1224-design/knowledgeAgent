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

## Capture rule

Snapshot the story text **as-shipped at ingest time** (final acceptance
criteria, post-negotiation), not as-analyzed. If the story changed
materially mid-flight and the evolution itself matters, use the dated
re-capture audit-trail pattern — but do not capture twice by default;
that is backlog-mirroring creep.

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
