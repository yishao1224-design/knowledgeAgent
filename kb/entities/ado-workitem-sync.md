---
type: Entity
title: ado-workitem-sync — ADO Retrieval Toolchain
description: The scripts/ado.py + ado-workitem-sync skill pair that syncs Azure DevOps work items into local analysis folders — retrieve/normalize/staleness/stamp, rev-stamped provenance, judgment-only skill.
status: active
confidence: medium
created: 2026-07-09
updated: 2026-07-09
review_after: 2026-10-09
tags: []
sources:
  - /sources/2026-07-09-ado-workitem-sync.md
---

# ado-workitem-sync — ADO Retrieval Toolchain

The code/skill pair that implements the *retrieve* leg of the
[user story analysis workflow](/concepts/user-story-analysis-workflow.md):
`scripts/ado.py` owns every mechanical rule, and the thin
`ado-workitem-sync` skill supplies only routing and judgment [1]. It is
the concrete instance of the script-for-pipelines rule in
[ingesting requirements from ticket systems](/concepts/ingesting-requirements-from-ticket-systems.md) —
the same code-vs-judgment split that pairs
[okf.py](/entities/okf-toolchain.md) with the lifecycle skills, applied
to the tracker boundary.

# Schema

## ado.py subcommands

| Command | Role |
|---------|------|
| `retrieve --id N` | Fetch work item + comments + attachments into `azure/<US\|BUG>_<id>_<slug>/raw/`; idempotent refresh (prunes stale attachment folders, preserves manifest analysis values, never touches files outside `raw/`) |
| `normalize` | Offline normalization of a saved payload; flag- and output-compatible with the retired JS normalizer |
| `staleness FOLDER [--remote]` | Rev comparison — exit 0 fresh, 1 analysis behind raw, 2 raw behind live ADO, 3 both, 4 undeterminable |
| `stamp FOLDER` | Print the `<!-- ado-rev: N retrieved: T -->` line for `analysis.md` |

Configuration is flag > env (`ADO_ORG_URL`, `ADO_PROJECT`, PAT via
`ADO_PAT`/`AZURE_DEVOPS_EXT_PAT`) — nothing org-specific is hardcoded,
so the tool ports across projects.

## The rev-stamp staleness model

`retrieve` records the tracker's revision (`Rev` = ADO `System.Rev`)
and `RetrievedAt` in `work-item.json`; analyses embed the rev they were
based on; `staleness` turns "is this analysis stale?" into a mechanical
comparison (analysis rev vs raw rev vs live rev). This is the
tracker-flavored equivalent of the sha256 drift check — provenance for
a *mutable* local cache, where the ADO revision history is the archive
and dated immutable captures are unnecessary.

## Normalized contract

`raw/work-item.json` (plain-text fields, comments embedded, inline
images as `[IMGID:<attachmentId>]` markers) plus `raw/attachments.json`
as the marker lookup table; attachment files in per-attachment-ID
folders to survive ADO's generic `image.png` names. Bugs get a labeled
SystemInfo + ReproSteps + Description combination so defect context is
never lost to an empty Description field.

## Division of labor with the skill

The skill retains exactly what cannot be code: resolving a fuzzy story
description to a work item ID (MCP/WIQL search), relaying script
output and failures honestly, and running `staleness` when an existing
analysis might be invalidated. Everything that previously lived as
~150 lines of defensive prompt rules (savePath forms, folder naming,
collision avoidance, refresh hygiene) is now unviolatable code paths —
prompt scar tissue converted to tested mechanics.

## Verification state

Normalization and staleness logic are locked by `scripts/test_ado.py`
(23 tests), including three traced JS-pipeline quirks. Two claims
remain unverified, which caps this page at `confidence: medium`:
no byte-level golden diff against the JS normalizer has run (requires
Node), and `retrieve` has not yet hit a live ADO org (the comments
api-version is the most likely adjustment). First live run should
prompt a review of this page.

# Related pages

- [User Story Analysis Workflow](/concepts/user-story-analysis-workflow.md)
  — this tool is its retrieve step; `staleness` is the analyze step's
  mechanical precondition.
- [Ingesting Requirements from Ticket Systems](/concepts/ingesting-requirements-from-ticket-systems.md)
  — the access-path and rev-stamp rules this tool implements.
- [okf.py — the Mechanical Toolchain](/entities/okf-toolchain.md) — the
  sibling tool for the bundle side; same design philosophy.

# Citations

[1] [ado.py + skill capture](/sources/2026-07-09-ado-workitem-sync.md)
