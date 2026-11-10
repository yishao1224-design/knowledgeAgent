---
type: Query
title: Token Cost of an LLM-Maintained Wiki
description: Rough token counts per ingest, review and question, where the wiki adds or saves tokens versus re-reading raw documents and RAG, and the main growth driver (index size).
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

# Token Cost of an LLM-Maintained Wiki

> **Question:** How substantial is the token cost to use this system?
> Any indication of added or maybe reduced total costs? [qa-2026-11-10]

**Status:** draft, unverified — estimates from this repository's file
sizes on 2026-11-10 (~4 characters per token), excluding the agent
tool's own fixed overhead. Replace with measured usage from a pilot.

## Added

- **Ingest:** a typical source (~10k tokens) ≈ 50–100k tokens read +
  10–20k written; a large spec (~100k tokens) ≈ 150k in total. RAG
  ingest only creates embeddings [qa-2026-11-10].
- **Review:** ≈ 20–40k tokens per page (page, its sources, any pinned
  code file). Human reviewer time, not tokens, is the biggest cost —
  which is why the
  [governance model](/queries/governance-for-ai-generated-knowledge.md)
  spends review only where content becomes widely discoverable.
- **Lint, drift, index:** zero tokens — deterministic Python in
  [okf.py](/entities/okf-toolchain.md); keeping mechanics out of the
  model is itself a cost control.

## Saved

- **No re-reading raw documents:** a question against a 100k-token spec
  re-reads 100k tokens each time; ingesting costs ~150k once, then each
  question reads ~5k of curated pages. **Break-even after ~2–3
  questions**, ~1/20 of the tokens per question afterwards
  [qa-2026-11-10].
- **People's time:** fewer repeated explanations, faster onboarding —
  larger than the token bill, but unmeasured.

Versus RAG: ~5–10k tokens per question either way (raw chunks vs
curated pages); the difference is answer quality, not tokens.

## Growth driver

Measured: `index.md` costs ~55 tokens per entry (~1.4k tokens for 24
entries), so a 1,000-page bundle has a ~55k-token index read at the
start of every session. Past a few hundred pages, split bundles by
domain, use per-domain indexes, or add a search tool — consistent with
keeping bundles scoped per project in
[adopting the bundle pattern](/concepts/adopting-the-bundle-pattern.md).
