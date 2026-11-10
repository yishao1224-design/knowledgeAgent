---
type: Source
title: "Q&A: governance, cross-tool federation, and token cost of an LLM Wiki"
description: Faithful condensation of three audience questions on the LLM Wiki × OKF talk and the answers given in a Claude Code session (2026-11-09/10) — agent-generated recommendations, not externally verified.
source_url: https://claude.ai/code/session_01FWdSvbSLWjmFTKjgvW1ukd
ingested: 2026-11-10
---

# Q&A: governance, cross-tool federation, and token cost (condensed capture)

Faithful condensation of a conversation held while preparing the
"LLM Wiki × OKF" tech talk. Three questions were asked, phrased as an
audience would ask them at Danfoss; the answers were written by the
coding agent from the bundle's existing pages (pr-quality-gates,
ingesting-requirements-from-ticket-systems, adopting-the-bundle-pattern,
knowledge-lifecycle) and from measurements of this repository. The
answers are **recommendations, not verified practice** — nothing below
has been tried at organisation scale. The cost answer was revised twice
at the asker's request; this capture records the final, token-only
version.

## Q1 — Governance

> What governance model do you recommend for validating, approving, and
> versioning AI-generated knowledge before it becomes discoverable across
> the Danfoss organization?

Answer, condensed:

- **Principle: gate discoverability, not writing.** AI writes, humans
  attest, git records. Keep OKF v0.2's `generated` (who produced it)
  separate from `verified` (a `human:` who confirmed it); an agent never
  stamps `verified` on its own output and the AI-generated marker is
  never removed.
- **Discoverability tiers.**
  - Tier 0 — `draft`, generated only: visible in the owning team's
    bundle, labelled AI-generated and unverified; any contributor via an
    agent.
  - Tier 1 — `active` + a `human:` verification: discoverable within the
    domain; a domain reviewer has checked each claim against its cited
    source.
  - Tier 2 — published: in the organisation-wide catalog and search; a
    named page owner approved and a classification check passed.
- **Roles.** Contributors (anyone, through an agent); page/domain owners
  via CODEOWNERS per path or tag; a knowledge platform team owning
  SCHEMA.md, skills, toolchain and CI; an information-security reviewer
  only when content crosses an access boundary.
- **Validation pipeline, every change via pull request.** (1) Blocking
  deterministic CI: OKF lint, sources append-only, log entry present,
  index fresh, drift on pinned evidence, plus a secrets/personal-data
  scan and a classification check. (2) Advisory LLM review: duplicates,
  unflagged contradictions, claims the cited source does not support —
  comments only, never blocking. (3) Human approval scaled by impact:
  platform owner for schema/toolchain, domain owner for org-wide
  publication, one teammate for ordinary pages.
- **Versioning.** Git is the version system; sources are immutable dated
  captures; claims about code pin git blobs; deprecate with
  `superseded_by`, never delete silently; tag organisation-wide releases
  of the published catalog so answers can cite "knowledge as of
  release X".
- **After approval.** `stale_after` makes every approval expire; drift
  and contradictions send pages to `needs_review` (still served,
  flagged). Track % verified, review-queue age, drifted pins, pages
  without an owner.
- **Built vs missing.** Built: lifecycle, generated/verified split,
  lint, drift. Designed but not wired: the three-tier PR gates (no CI
  job yet). Missing for organisation use: a classification field and
  its lint check, the organisation-wide catalog, secrets/personal-data
  scanning.

## Q2 — Unified layer across tools

> Can OKF be used to create a unified knowledge layer across tools such
> as Polarion, Azure DevOps, GitHub, Confluence, and ServiceNow while
> preserving permissions and source-of-truth ownership?

Answer, condensed: **yes, as a federation, not one central store.** OKF
unifies format and provenance (`type`, `sources[]` with stable id +
revision, `generated`/`verified`, `status`, `stale_after`). It has **no
permission model, identity, sync, or cross-bundle search** — those come
from where each bundle is stored and from the source tools.

Three rules keep permissions intact:

1. **One bundle per access boundary.** A bundle lives in a git repo and
   inherits that repo's permissions; per-page access inside one repo is
   not meaningful. The unified layer is a federation of bundles plus an
   organisation catalog of metadata only (titles, owners, links).
2. **No downgrade on capture.** A capture copies content, so it may only
   land in a bundle whose readers are a subset of the source's readers;
   otherwise link to the item and summarise only what that audience may
   see. Lint could enforce: a page's classification is at least as
   strict as every source it cites.
3. **Query as the user, never as a super-user.** The agent reads bundles
   and calls each tool's API or MCP server with the asking user's
   identity; one all-seeing service account is how enterprise AI search
   bypasses permissions.

Each tool stays the system of record:

| Tool | Stays owner of | Bundle cites |
|---|---|---|
| Polarion | Requirements and baselines under formal change control | Work-item id + revision/baseline; the wiki is explicitly not the authority |
| Azure DevOps | Stories, status, sprints; code in Repos | Work-item id + `System.Rev`; commit/blob pins for repos |
| GitHub | Code, PRs, architecture decision records | Commit or blob pins (`okf.py drift`) |
| Confluence | Hand-written pages | Page id + version; decide ownership per topic, never two editable wikis on one subject |
| ServiceNow | Incidents, changes, KB articles | Record id + update timestamp; ingest only recurring patterns with personal data removed; long tail stays with search/RAG |

Don't mirror source tools; the bundle earns its place on what spans
them. Freshness ties back to the source by comparing cited revisions,
and by a Definition-of-Done item "affected knowledge pages updated".
Today: GitHub and ADO Repos work natively via blob pins; the ADO Boards
pattern is documented but its retrieval script was removed in 2026-08;
connectors for Boards, Polarion, Confluence and ServiceNow would need
building. Suggested next step: a pilot in one product domain spanning at
least two tools, measuring % verified, review time, and questions
answered without asking a colleague, before building the catalog.

## Q3 — Token cost

> How substantial is the token cost to use this system? Any indication of
> added or maybe reduced total costs?

Final answer, token counts only (the asker asked to drop prices).
Figures are estimates from this repository's measured file sizes
(~4 characters per token, measured 2026-11-10: SCHEMA.md ~4.2k tokens,
index.md ~1.4k for 24 entries, average page ~1.2k, average capture
~0.9k) and exclude the agent tool's own fixed overhead.

Added:

- **Ingest:** a typical source (~10k tokens) takes ~50–100k tokens of
  reading plus 10–20k of writing; a large spec (~100k tokens) ~150k in
  total. RAG ingest only creates embeddings, almost no LLM tokens.
- **Review:** ~20–40k tokens per page (page, its sources, any pinned
  code file). Human reviewer time, not tokens, is the biggest cost.

Saved:

- **No re-reading raw documents:** asking directly against a 100k-token
  spec re-reads 100k tokens every time; ingesting it costs ~150k once,
  then each question reads ~5k of curated pages. Break-even after about
  2–3 questions; afterwards ~1/20 of the tokens per question.
- **People's time:** fewer repeated explanations, faster onboarding;
  outweighs token cost but must be measured in a pilot.

Compared with RAG: tokens per question are about the same (5–10k of raw
chunks vs 5–10k of curated pages); the difference is answer quality.

Main growth driver: each index.md entry is ~55 tokens, so a 1,000-page
bundle has a ~55k-token index read at the start of every session. Past
a few hundred pages, split bundles by domain, use per-domain indexes, or
add a search tool.
