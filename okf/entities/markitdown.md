---
type: Entity
title: MarkItDown
description: Microsoft's Python utility that converts binary formats (PDF, Office, images, audio) to LLM-oriented Markdown — assessed as an optional extraction helper for this bundle's capture step, not adopted into any skill.
status: stable
lifecycle: active
confidence: medium
created: 2026-07-11
updated: 2026-11-10
stale_after: 2026-12-10
tags: []
sources:
  - resource: /sources/2026-07-11-markitdown.md
    id: markitdown
    title: MarkItDown README capture (2026-07-11)
  - resource: /sources/2026-11-10-markitdown.md
    id: markitdown-2026-11
    title: MarkItDown README capture (2026-11-10)
generated:
  by: claude-code/2.1.322
  at: 2026-11-10
---

# MarkItDown

A lightweight Python (3.10–3.14) library and CLI from Microsoft that
converts many file formats — PDF, Word, PowerPoint, Excel, images (EXIF
metadata and LLM captioning), audio (transcription), HTML,
CSV/JSON/XML, ZIP, EPub, YouTube URLs — into Markdown meant for LLM use
rather than high-fidelity rendering [markitdown-2026-11]. OCR of images
embedded in PDF and Office files is a separate plugin
(`markitdown-ocr`) that needs an LLM-vision client; captioning and
transcription call web-hosted services [markitdown-2026-11].
MIT-licensed; 0.1.9 on PyPI as of 2026-11-10 (0.1.6 at the first
capture) [markitdown-2026-11] [markitdown]. Install with
`pip install 'markitdown[all]'` or per-format extras; usage is one
command (`markitdown file.pdf -o out.md`) or a three-line Python API
(`MarkItDown().convert(path).markdown`) [markitdown-2026-11]. The
project also maintains a `markitdown-mcp` package [markitdown-2026-11].

# Fit with this bundle's capture step

*(Assessment from the 2026-07-11 ingestion conversation, re-checked
against the 2026-11-10 README — an option on the shelf, not an adopted
dependency; the [lifecycle skill suite](/entities/lifecycle-skills.md)
was deliberately left unchanged.)*

kb-ingest's capture rule for binaries with an authoritative home
elsewhere (decks, PDFs: extract the content, point `source_url` at the
original, do not commit the binary) currently relies on the agent's own
file-reading tools. Load-bearing diagrams are a separate case: they are
kept under `sources/assets/` (see [SCHEMA.md](/SCHEMA.md),
*Source assets*). MarkItDown offers a scriptable extraction path for
the extract step — useful for large PDFs (agent PDF reading is
page-limited), Office formats, and agents without native binary
readers (e.g. the Copilot entry points; `markitdown-mcp` is a possible
route there). Its built-in converters run offline and deterministically;
image captioning, transcription, OCR and the Azure converters call LLM
or cloud services and are not deterministic [markitdown-2026-11]. It
needs Python 3.10–3.14 plus pip dependencies — a step up from the
stdlib-only [okf.py toolchain](/entities/okf-toolchain.md), though no
new runtime. A concrete candidate use: converting work-item attachments
when
[ingesting requirements from ticket systems](/concepts/ingesting-requirements-from-ticket-systems.md).

Boundaries of the fit:

- **It knows nothing about OKF.** No lifecycle fields; the Azure
  Document Intelligence and Content Understanding converters can
  prepend their own YAML front matter of extracted fields
  [markitdown-2026-11], which must be removed or merged before the
  Source template is applied. Its output is only ever a capture *body*.
- **Output is a condensation, not verbatim.** The project aims at
  machine consumption, not high-fidelity rendering
  [markitdown-2026-11]; captures built from it must say so in their
  `description`, per the Source convention.
- **Plain URLs don't need it** — WebFetch already yields Markdown; it
  earns its keep on binary formats only.
- **Security posture**: it performs I/O with the privileges of the
  current process; the project advises sanitizing untrusted inputs
  (restricting paths, URI schemes and private or metadata network
  addresses) and calling the narrowest converter (`convert_local`,
  `convert_stream`) [markitdown-2026-11].

Deeper integration ideas discussed but not pursued: a note in the
kb-ingest skill, or an `okf.py convert` subcommand wrapping it to emit
a pre-filled Source capture skeleton.
