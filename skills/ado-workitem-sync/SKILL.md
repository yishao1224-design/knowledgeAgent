---
name: ado-workitem-sync
description: "Retrieve or refresh an Azure DevOps user story or bug into azure/<US|BUG>_<id>_<slug>/raw/ by running scripts/ado.py, which owns all mechanics (fetch, attachment download, normalization, rev-stamping). Use when the user asks to retrieve, download, refresh, or initialize a work item's local folder before analysis."
argument-hint: "Provide a user story ID, bug ID, or an existing azure work-item folder path to refresh. Optionally an org URL / project override."
---

# ADO Work Item Sync

Retrieve or refresh the local source data for one Azure DevOps user
story or bug. **All mechanics live in `scripts/ado.py`** — folder
naming, attachment-ID folders, HTML normalization, `[IMGID:]` markers,
manifest preservation, refresh idempotency, and `Rev`/`RetrievedAt`
stamping are code, not instructions. Your job is the judgment around
one script call.

## Configuration

The script resolves, in order flag > environment:

- `--org` / `ADO_ORG_URL` — e.g. `https://dev.azure.com/<org>`
- `--project` / `ADO_PROJECT`
- PAT from `ADO_PAT` or `AZURE_DEVOPS_EXT_PAT`

If the script reports missing configuration, relay exactly what it
asked for; check the project's `CLAUDE.md` for recorded org/project
values before asking the user.

## Workflow

1. **Identify the work item.** If the user gave a numeric ID, use it.
   If they gave a folder path, parse the ID from the
   `US_<id>_...`/`BUG_<id>_...` name. If they described the story in
   words, find the ID (ADO MCP search / WIQL if available, else ask) —
   this identification step is the one judgment call retrieval needs.
2. **Run the script:**
   `python scripts/ado.py retrieve --id <N> [--org URL] [--project P] [--dest DIR]`
   The same command is both initialize and refresh — it is idempotent,
   prunes stale attachment folders, preserves `attachment analysis`
   values in the manifest, and never touches files outside `raw/`
   (`analysis.md` / `IML.md` are safe by construction).
3. **Report the script's output**: work item type, rev, state, folder,
   attachment/comment counts, and any download warnings — verbatim
   enough that failures are visible. Do not silently retry a hard
   failure; show it.
4. **State readiness**: the folder is ready for the analysis skill.
   If an `analysis.md` already exists, run
   `python scripts/ado.py staleness <folder>` and report whether the
   existing analysis is now behind the refreshed raw data.

## Boundaries

- Retrieval only — never draft or update `analysis.md` here.
- Do not fetch related/linked/child work items unless explicitly asked.
- Do not hand-roll normalization, folder naming, or attachment handling
  in shell or by editing files — if the script's behavior looks wrong,
  report it as a script bug instead of working around it.

## Example triggers

- `Retrieve user story 1999851.`
- `Refresh azure/US_1999851_add_asset_details_failure_categorization with the latest DevOps data.`
- `Initialize the local folder for bug 2101492.`
- `Download story 1900000 with comments and attachments; no analysis yet.`
