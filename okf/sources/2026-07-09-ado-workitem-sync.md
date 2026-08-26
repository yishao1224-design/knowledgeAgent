---
type: Source
title: ado.py + ado-workitem-sync skill (retrieval toolchain pair)
description: Faithful condensation of scripts/ado.py and skills/ado-workitem-sync/SKILL.md — subcommands, normalization port provenance, rev-stamp staleness model — as of 2026-07-09.
source_url: repo://scripts/ado.py
ingested: 2026-07-09
sha256: 945b3214fea5cfdb5129a9acfa72e20b74abc3d0eda9788d3c825e574789c3ac
---

# ado.py + ado-workitem-sync (as of 2026-07-09)

## scripts/ado.py — stdlib-only Python, four subcommands

- **retrieve --id N** — GET work item (`$expand=all`, api-version 7.1),
  comments (7.1-preview.3), attachments (binary, `download=true`) into
  `<dest>/<US|BUG>_<id>_<slug>/raw/`. Attachment files land in
  per-attachment-ID folders (collision-proof against generic
  `image.png` names). Idempotent refresh: prunes attachment-ID folders
  no longer referenced, preserves `attachment analysis` values from the
  previous manifest, deletes legacy `comments.json`, never touches
  files outside `raw/`. `--keep-payload` saves the raw API payload for
  fixtures. Only `User Story` and `Bug` types accepted (US/BUG prefix).
- **normalize** — offline normalization of a saved payload; flag-
  compatible with the retired JS normalizer
  (`example/normalize-devops-story.mjs`) and byte-compatible in output
  shape when no rev/timestamp is supplied.
- **staleness FOLDER [--remote]** — exit 0 fresh; 1 `analysis.md`
  rev-stamp behind `raw/` rev; 2 raw behind live ADO rev; 3 both;
  4 undeterminable (missing stamps).
- **stamp FOLDER** — prints `<!-- ado-rev: N retrieved: T -->` for
  embedding in `analysis.md`.

Configuration, flag > env: `--org`/`ADO_ORG_URL`, `--project`/
`ADO_PROJECT`, PAT from `ADO_PAT` or `AZURE_DEVOPS_EXT_PAT` (az-
compatible). No hardcoded org (the JS predecessor hardcoded one).

## Normalized output contract

`raw/work-item.json`: `IterationPath`, `State`, `AssignedTo`, `Title`,
`Rev`, `RetrievedAt`, `Description`, `AcceptanceCriteria`, `Comment[]`
(CreatedDate/CreatedBy/Text). Plain text, HTML stripped, inline images
replaced by `[IMGID:<attachmentId>]` markers resolved through
`raw/attachments.json` (`workItemId`, `attachmentCount`,
`attachments[]` of `{attachmentId, "attachment analysis"}`). For bugs,
Description is a labeled combination of SystemInfo + ReproSteps +
System.Description when more than one is non-empty.

## Port provenance

Ported 2026-07-09 from the battle-tested JS normalizer used in the CRM
project. Behavior locked by `scripts/test_ado.py` (23 tests), including
three JS quirks confirmed by tracing when naive expectations failed:
only *closing* block tags become newlines; 3+ newlines collapse to
exactly 2 (never 1); `&amp;lt;` double-decodes to `<` (entity order).
Caveats at capture time: no byte-level JS-vs-Python golden diff run yet
(no Node on the porting machine); `retrieve` not yet exercised against
a live ADO org (comments api-version most likely to need adjustment).

## skills/ado-workitem-sync/SKILL.md — the thin routing skill

Judgment-only (~40 lines, replacing a ~150-line mechanics-laden
predecessor `devops-userstory-retrieve-refresh`): (1) identify the work
item — ID given, folder name parsed, or fuzzy description resolved via
MCP/WIQL search (the one real judgment call); (2) run
`ado.py retrieve`; (3) report script output verbatim enough that
failures are visible, never silently retry; (4) if `analysis.md`
exists, run `staleness` and report. Boundaries: retrieval only; no
related/child items unless asked; never hand-roll normalization — a
wrong-looking script behavior is reported as a script bug, not worked
around.
