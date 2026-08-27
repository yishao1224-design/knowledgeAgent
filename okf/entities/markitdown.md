---
type: Entity
title: MarkItDown
description: Microsoft's Python utility that converts binary formats (PDF, Office, images, audio) to LLM-optimized Markdown — assessed as an optional extraction helper for this bundle's capture step, not adopted into any skill.
status: stable
lifecycle: active
confidence: medium
created: 2026-07-11
updated: 2026-08-27
stale_after: 2026-08-11
tags: []
sources:
  - resource: /sources/2026-07-11-markitdown.md
    id: markitdown
    title: MarkItDown README capture
---

# MarkItDown

A lightweight Python (3.10+) library and CLI from Microsoft that
converts many file formats — PDF, Word, PowerPoint, Excel, images
(OCR), audio (transcription), HTML, CSV/JSON/XML, ZIP, EPub, YouTube
URLs — into Markdown optimized for LLM consumption rather than
high-fidelity rendering [markitdown]. MIT-licensed; v0.1.6 at capture time.
Install with `pip install 'markitdown[all]'` or per-format extras;
usage is one command (`markitdown file.pdf -o out.md`) or a two-line
Python API [markitdown].

# Fit with this bundle's capture step

*(Assessment from the 2026-07-11 ingestion conversation — an option on
the shelf, not an adopted dependency; the
[lifecycle skill suite](/entities/lifecycle-skills.md) was deliberately
left unchanged.)*

kb-ingest's capture rule for binaries (decks, PDFs: extract the
content, point `source_url` at the authoritative copy, do not commit
the binary) currently relies on the agent's own file-reading tools.
MarkItDown offers a deterministic, scriptable extraction path for
exactly that step — useful for large PDFs (agent PDF reading is
page-limited), Office formats, and agents without native binary
readers (e.g. the Copilot entry points). Same Python runtime the
[okf.py toolchain](/entities/okf-toolchain.md) already requires, so no
new infrastructure. A concrete candidate use: converting work-item
attachments when
[ingesting requirements from ticket systems](/concepts/ingesting-requirements-from-ticket-systems.md).

Boundaries of the fit:

- **It knows nothing about OKF.** No frontmatter, no lifecycle fields —
  the Source template and linking still happen in the skill/okf.py
  layer. Its output is only ever a capture *body*.
- **Output is a condensation, not verbatim.** PDF headings flatten and
  tables can degrade [markitdown]; captures built from it must say so in their
  `description`, per the Source convention.
- **Plain URLs don't need it** — WebFetch already yields Markdown; it
  earns its keep on binary formats only.
- **Security posture**: it performs I/O with the privileges of the
  current process; the project itself advises sanitizing untrusted
  inputs and calling the narrowest converter [markitdown].

Deeper integration ideas discussed but not pursued: a note in the
kb-ingest skill, or an `okf.py convert` subcommand wrapping it to emit
a pre-filled Source capture skeleton.
