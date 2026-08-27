---
name: kb-review
description: Work the review queue of the OKF knowledge bundle — re-verify overdue or flagged concepts against their sources, resolve contradictions, and promote or demote lifecycle status. Use when the user asks to review, verify, refresh, or check staleness of the knowledge base, or on a maintenance schedule.
---

# kb-review — Verify phase of the knowledge lifecycle

Keep `active` a meaningful promise: everything active has been checked
recently enough to trust.

## Step 0 — Orient and build the queue

> **First run in this project?** If there's no bundle directory or no
> `scripts/okf.py`, run the **kb-setup** skill first to scaffold them,
> then continue.
>
> Paths below assume the default bundle location, `okf/`. A project
> may have chosen another name at setup — whichever top-level directory
> holds `SCHEMA.md` is the bundle, and `okf.py` finds it on its own.

1. Read `okf/SCHEMA.md`; skim recent `okf/log.md`.
2. `python scripts/okf.py stats` — the review queue lists every
   `needs_review` page and every `active` page past `stale_after`.
   `python scripts/okf.py drift` lists every page whose pinned repo
   file moved or vanished; those are in scope too, and they are the
   highest-signal entries in the queue because something actually
   changed.
3. `git log --since=<last review> -- okf/sources/` — a capture edited
   or re-captured since the last pass puts its dependent concepts in
   scope too (find them via frontmatter `sources`).

If the queue is large, triage: contested pages first, then dependents
of changed captures, then oldest overdue. Tell the user the queue size
and how much you'll cover this session.

## Step 1 — Re-verify each page

For each page in scope:

1. Re-read the page and its `sources` captures. If a capture references
   a `sources/assets/` image (e.g. an architecture diagram), **re-read
   the image itself**, not just the capture's description of it — dense
   visuals yield claims on later passes that earlier ingests missed,
   and a mismatch between the image and the capture's description is
   itself a review flag.
2. **Re-fetching `source_url` is the only upstream-change detection in
   the system** — `drift` covers files in this repo, nothing covers a
   web page, so do the re-fetch for any page whose claims are
   time-sensitive or whose source is a living document. Changed
   upstream → capture a NEW dated file in `okf/sources/` (never edit the
   old one) and diff against the old capture.
3. For a page `drift` reported: read the file's current content and
   diff it against what the page claims. A moved `blob:` means the
   evidence changed, not necessarily that the page is wrong — decide
   per claim, then restamp `blob:` with `okf.py drift --hash <file>`
   and set `last_modified:` to today. **Restamping without re-reading
   the file is falsifying the record**; it is the one thing this
   mechanism cannot survive.
4. Decide per claim: still true / changed / can't verify.

## Step 2 — Apply the verdict

| Verdict | Action |
|---------|--------|
| All claims hold | Bump `updated`, set new `stale_after` per the SCHEMA.md cadence table, `lifecycle: active`, restamp any pinned `blob:` you re-read. Append a `verified:` entry (`by: human:<id>` if a person confirmed it, else your own `<tool>/<version>`). Consider raising `confidence`. |
| Some claims changed | Rewrite those claims, cite the new capture or file, bump `updated`, reset `stale_after`, restamp pinned `blob:`, **replace `generated` entirely** with your own `{ by, at }`, keep `active`. |
| Contested (sources disagree) | Write/refresh `## Contradictions` with both positions and citations; tag `contested`; keep `needs_review` until resolved. |
| Substantially wrong or superseded | `lifecycle: deprecated` + `superseded_by` (write the successor page if needed, or a `## Deprecation` section explaining why with no successor). |
| Can't verify, low stakes | Lower `confidence`, tag `unverified`, keep `needs_review`. Note it for the user. |

`generated` is replaced wholesale, never half-updated. It is a single
provenance event — *this producer made this text on this date* — so the
producer and the timestamp move together. Advancing only `at` while
leaving a previous agent's `by` in place attributes your rewrite to
them, which is worse than no stamp at all: it reads as a confident,
specific claim and is false. If you did not touch the body, leave the
whole field alone.

Never delete during review — deprecation is the strongest verdict here;
deletion belongs to kb-curate.

## Step 3 — Close out

1. `okf.py index` (lifecycle badges may have changed).
2. One log entry per page:
   `okf.py log "**Review**: re-verified [page](/path.md) — <verdict>."`
3. `okf.py lint` — fix errors. `okf.py drift` should come back clean
   for every page you restamped.
4. Report to the user: pages verified / updated / deprecated /
   still-contested, and remaining queue size.
