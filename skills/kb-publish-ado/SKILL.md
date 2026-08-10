---
name: kb-publish-ado
description: Publish the kb/ knowledge bundle out as an Azure DevOps wiki — render the bundle into ADO wiki shape (status banners, rewritten links, .order TOC) with scripts/kb_wiki.py, then sync it into the <Project>.wiki Git repo. Use when the user asks to publish, export, or push the knowledge base to an Azure DevOps wiki.
argument-hint: "Optionally: the path to a local <Project>.wiki checkout to sync into, and any include flags (sources/archive)."
---

# kb-publish-ado — Publish the bundle as an Azure DevOps wiki

One-way publish: `kb/` stays the source of truth; the ADO wiki is a
**generated view**. All rendering mechanics live in
`scripts/kb_wiki.py` — frontmatter stripping, status banners, link
rewriting, `.order`/TOC generation, filename mapping. Your job is the
judgment around one export call plus the git sync into the wiki repo.

## What the export does (don't hand-roll it)

`python scripts/kb_wiki.py export` reads the bundle and writes an
ADO-wiki-shaped tree to `dist/ado-wiki/`:

- YAML frontmatter → a compact banner (⚠️ needs_review, 🛑 deprecated,
  📝 draft) + a `Status · Updated · Review after · Tags` line.
- Bundle-relative links (`/concepts/foo.md`) → wiki paths
  (`/Concepts/Foo-Title`). Links to excluded pages degrade to plain
  text; citations to excluded sources fall back to the source's
  `source_url`.
- `Section.md` + `Section/` folders with `.order` files so ADO renders a
  real table of contents; a generated `Home.md`.
- Pages named from each page's `title` (ADO shows hyphen as space).

Flags: `--include-sources`, `--include-archive`, `--no-schema`,
`--no-log`, `--out DIR`, `--force`. Sources are **excluded by default**
(their captures can be large/verbatim); citations still resolve via
`source_url`. Pass `--include-sources` only if the user wants raw
captures on the wiki.

## Step 0 — Orient

Confirm there's a bundle (`kb/SCHEMA.md` exists). If not, this is the
wrong skill — point the user at **kb-setup**. Ask/confirm two things if
unknown: (a) which sections to include (default: concepts, entities,
comparisons, queries + Conventions + Change-Log; sources excluded);
(b) where the wiki lives — a local `<Project>.wiki` checkout path, or
whether they'll use ADO's "publish code as wiki".

## Step 1 — Export

> **Installed via `npx skills add`?** This skill ships `kb_wiki.py` next
> to this SKILL.md. If `scripts/kb_wiki.py` is missing, copy the bundled
> file there. It imports `scripts/okf.py`, so run **kb-setup** first if
> the bundle/toolchain isn't in place yet.

```
python scripts/kb_wiki.py export
```

Add flags per Step 0. Report the summary it prints (page/section counts,
what was excluded). Spot-check `dist/ado-wiki/Home.md` and one section
page so you can vouch for the output before anything leaves the machine.

## Step 2 — Sync into the wiki repo

An ADO wiki is a Git repo named `<Project>.wiki` on branch `wikiMain`
(see the ADO docs: *Wiki files, folder structure, Git repo
conventions*). Two ways to publish:

- **Provisioned wiki** — clone the `<Project>.wiki` repo, copy the
  **contents** of `dist/ado-wiki/` into the checkout root (replacing the
  previous export), and commit.
- **Publish code as wiki** — commit `dist/ado-wiki/` into a normal code
  repo and point ADO's "Publish code as wiki" at that folder.

Copy the tree with the user's tools; do not reimplement the export in
shell. If a previous export is present in the target, replace it wholly
so removed pages don't linger (the generated tree is disposable).

## Step 3 — Push (needs explicit confirmation)

Pushing updates a shared/published wiki. **Do not push automatically.**
Show the user the diff (`git status` / `git diff` in the wiki checkout)
and the exact command, and let them confirm or run it:

```
git -C <path-to-Project.wiki> add -A && \
  git -C <path-to-Project.wiki> commit -m "Update wiki from kb bundle" && \
  git -C <path-to-Project.wiki> push origin wikiMain
```

## Boundaries

- Publish only — never edit `kb/` here (curation is kb-curate, etc.).
- Never edit files under `dist/ado-wiki/` by hand; they are regenerated.
- The export is one-way. To bring wiki content *into* the bundle, that's
  an ingest job (kb-ingest), not this skill.
- Images/attachments beyond `source_url` citations aren't wired to ADO's
  `.attachments` yet — flag any load-bearing images to the user.

## Example triggers

- "Publish the knowledge base to our Azure DevOps wiki."
- "Export the kb bundle as an ADO wiki, include the sources."
