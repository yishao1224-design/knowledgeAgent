---
type: Source
title: Microsoft MarkItDown README
description: Condensed capture of the microsoft/markitdown project README from GitHub (fetched 2026-11-10); a faithful condensation, not verbatim, taken from raw main/README.md.
source_url: https://github.com/microsoft/markitdown
ingested: 2026-11-10
---

# MarkItDown (condensed capture)

A lightweight Python utility for converting various files to Markdown
for use with LLMs and related text analysis pipelines. Described as most
comparable to textract, but focused on preserving important document
structure as Markdown (headings, lists, tables, links). Output is
"often reasonably presentable" but meant for text analysis tools, and
"may not be the best option for high-fidelity document conversions for
human consumption." Maintained by Microsoft.

Not stated in the README text (fetched from raw main, so the GitHub page
sidebar was not captured): licence, current release version, star or
release counts. Checked separately the same day: the repository's
`LICENSE` file is the MIT License (Copyright (c) Microsoft Corporation),
and PyPI lists the latest release as **0.1.9** with
`requires_python >=3.10,<3.15`.

## Why Markdown (project rationale)

Markdown is close to plain text yet represents document structure;
mainstream LLMs (GPT-4o named) natively "speak" Markdown, so it is well
understood and highly token-efficient.

## Supported input formats

- PDF, PowerPoint, Word, Excel
- Images (EXIF metadata and **captioning**)
- Audio (EXIF metadata and speech transcription)
- HTML; text-based formats (CSV, JSON, XML)
- ZIP files (iterates over contents)
- YouTube URLs
- EPubs
- "... and more!" (an `[outlook]` extra exists for Outlook messages)

NOTE (README): image captioning and speech transcription rely on
web-hosted services.

## Requirements & installation

- Python **3.10 through 3.14**; a virtual environment is recommended
  (venv, `uv venv --python=3.12`, or conda examples given).
- `pip install 'markitdown[all]'`, or from source:
  `pip install -e 'packages/markitdown[all]'`.
- Selective extras, e.g. `pip install 'markitdown[pdf, docx, pptx]'`:
  `[all]`, `[pptx]`, `[docx]`, `[xlsx]`, `[xls]`, `[pdf]`, `[outlook]`,
  `[az-doc-intel]`, `[az-content-understanding]`,
  `[audio-transcription]` (wav and mp3), `[youtube-transcription]`.
- Docker: `docker build -t markitdown:latest .` then
  `docker run --rm -i markitdown:latest < file.pdf > output.md`.

## Usage

CLI:

```bash
markitdown path-to-file.pdf > document.md
markitdown path-to-file.pdf -o document.md
cat path-to-file.pdf | markitdown
```

Python API (result attribute is now `markdown`):

```python
from markitdown import MarkItDown
md = MarkItDown(enable_plugins=False)  # True to enable plugins
result = md.convert("test.xlsx")
print(result.markdown)
```

LLM image descriptions — "currently only for pptx and image files":
`MarkItDown(llm_client=..., llm_model=..., llm_prompt="optional")`
(OpenAI client example). Retries are the client's (`max_retries`); if
the LLM call ultimately fails, MarkItDown tries other applicable
converters and raises `FileConversionException` only if none succeeds.

## Extensions

- **Plugins**: third-party, **disabled by default**.
  `markitdown --list-plugins`; enable with `--use-plugins` (CLI) or
  `enable_plugins=True` (API). Discover via GitHub hashtag
  `#markitdown-plugin`; template in `packages/markitdown-sample-plugin`.
  The project prefers new formats arrive as plugins.
- **markitdown-ocr plugin** (`pip install markitdown-ocr` + an
  OpenAI-compatible client): OCR for embedded images in PDF, DOCX, PPTX
  and XLSX via LLM vision, reusing `llm_client`/`llm_model`. No new ML or
  binary dependencies. Without an `llm_client` OCR is silently skipped
  and the built-in converter is used.
- **Azure Document Intelligence** (`[az-doc-intel]`): CLI
  `markitdown file.pdf -o out.md -d -e "<endpoint>"`, or set
  `MARKITDOWN_DOCINTEL_ENDPOINT` and pass only `-d`. Key from
  `AZURE_API_KEY`, else `DefaultAzureCredential`. Options:
  `--docintel-model-id` (e.g. `prebuilt-layout`), `--docintel-features`
  (`barcodes`, `formulas`, `keyValuePairs`, `languages`,
  `ocrHighResolution`, `styleFont`; none by default; some cost extra),
  `--docintel-query-fields`. API equivalents `docintel_endpoint`,
  `docintel_credential`, `docintel_model_id`, `docintel_features`,
  `docintel_query_fields`. Models returning structured fields prepend
  them as YAML front matter (`fields`, or a `documents` list for
  multi-document results).
- **Azure Content Understanding** (`[az-content-understanding]`):
  cloud multimodal extraction (documents, images, audio, **video**),
  structured fields as YAML front matter, prebuilt or custom analyzers.
  CLI `--use-cu --cu-endpoint "<endpoint>"` or `MARKITDOWN_CU_ENDPOINT`;
  API `cu_endpoint`, `cu_analyzer_id`, `cu_file_types` (restrict which
  formats route to CU). Each CU-routed `convert()` is a billable call.
- README comparison table: built-in converters are offline,
  local-compute only, no structured fields, basic audio and no video;
  Doc Intel and CU are billable cloud calls.
- **MCP**: a `markitdown-mcp` package is maintained in this repository
  (listed as in scope under "What to Contribute"; no usage section in
  the README).

## Contribution scope

In scope: converter fidelity, bug/performance/security fixes, the CLI,
the `markitdown-mcp` package, tests and docs. New formats added
sparingly. Out of scope: web servers/REST APIs/hosted services, web
frontends, desktop/mobile apps — build those as separate packages
depending on `markitdown` from PyPI. CLA required; tests via `hatch test`
in `packages/markitdown`; `pre-commit run --all-files`.

## Security considerations

- MarkItDown performs I/O with the privileges of the current process
  (like `open()` or `requests.get()`).
- **Sanitize inputs**: do not pass untrusted input directly; in hosted
  or server-side use, restrict file paths, URI schemes and network
  destinations, and block private, loopback, link-local and
  metadata-service addresses.
- **Call the narrowest method**: `convert()` is intentionally permissive
  (local files, remote URIs, byte streams). Prefer `convert_local()` for
  local files, `convert_response()` with your own `requests.get()`, or
  `convert_stream()` for maximum control.
- Image captioning, speech transcription, Doc Intel and Content
  Understanding rely on web-hosted services; for local-only operation
  install only the extras you need.

## Caveats (from the README)

- Output is aimed at machine consumption, not high-fidelity human
  rendering.
- The README makes no specific claim that PDF headings flatten or
  tables degrade; it states a focus on preserving headings, lists,
  tables and links as Markdown.
