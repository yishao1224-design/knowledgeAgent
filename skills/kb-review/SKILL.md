---
name: kb-review
description: Work the review queue of the kb/ knowledge bundle — re-verify overdue or flagged concepts against their sources, resolve contradictions, and promote or demote lifecycle status. Use when the user asks to review, verify, refresh, or check staleness of the knowledge base, or on a maintenance schedule.
---

# kb-review — Verify phase of the knowledge lifecycle

Keep `active` a meaningful promise: everything active has been checked
recently enough to trust.

## Step 0 — Orient and build the queue

1. Read `kb/SCHEMA.md`; skim recent `kb/log.md`.
2. `python scripts/okf.py stats` — the review queue lists every
   `needs_review` page and every `active` page past `review_after`.
3. `python scripts/okf.py drift` — drifted sources put their dependent
   concepts in scope too (find them via frontmatter `sources`).

If the queue is large, triage: contested pages first, then drifted
sources' dependents, then oldest overdue. Tell the user the queue size
and how much you'll cover this session.

## Step 1 — Re-verify each page

For each page in scope:

1. Re-read the page and its `sources` captures. If a capture references
   a `sources/assets/` image (e.g. an architecture diagram), **re-read
   the image itself**, not just the capture's description of it — dense
   visuals yield claims on later passes that earlier ingests missed,
   and a mismatch between the image and the capture's description is
   itself a review flag (assets sit outside the drift check).
2. If a source drifted or claims are time-sensitive, re-fetch the
   original `source_url`. Changed upstream → capture a NEW dated file
   in `kb/sources/` (never edit the old one) and diff against the old
   capture.
3. Decide per claim: still true / changed / can't verify.

## Step 2 — Apply the verdict

| Verdict | Action |
|---------|--------|
| All claims hold | Bump `updated`, set new `review_after` per the SCHEMA.md cadence table, `status: active`. Consider raising `confidence`. |
| Some claims changed | Rewrite those claims, cite the new capture, bump `updated`, reset `review_after`, keep `active`. |
| Contested (sources disagree) | Write/refresh `## Contradictions` with both positions and citations; tag `contested`; keep `needs_review` until resolved. |
| Substantially wrong or superseded | `status: deprecated` + `superseded_by` (write the successor page if needed, or a `## Deprecation` section explaining why with no successor). |
| Can't verify, low stakes | Lower `confidence`, tag `unverified`, keep `needs_review`. Note it for the user. |

Never delete during review — deprecation is the strongest verdict here;
deletion belongs to kb-curate.

## Step 3 — Close out

1. `okf.py index` (status badges may have changed).
2. One log entry per page:
   `okf.py log "**Review**: re-verified [page](/path.md) — <verdict>."`
3. `okf.py lint` — fix errors.
4. Report to the user: pages verified / updated / deprecated /
   still-contested, and remaining queue size.
