---
type: Source
title: Microsoft MarkItDown README
description: Condensed capture of the microsoft/markitdown project README from GitHub (fetched 2026-07-11).
source_url: https://github.com/microsoft/markitdown
ingested: 2026-07-11
sha256: 21d1de911a17df0f68633b16925c8e4937e899deee7e66caafbefafa91127e45
---

# MarkItDown (condensed capture)

A lightweight Python utility that converts many file formats to
Markdown, optimized for consumption by Large Language Models and text
analysis pipelines rather than for high-fidelity human-readable
conversion. Maintained by Microsoft, MIT license. At capture time:
version 0.1.6 (released May 26, 2026), ~165k GitHub stars, 19 releases.

## Why Markdown (project rationale)

Markdown is close to plain text yet preserves document structure;
major LLMs "natively speak Markdown" and are extensively trained on
it, so Markdown output is token-efficient and directly consumable.

## Supported input formats

- PDF, PowerPoint (pptx), Word (docx), Excel (xlsx/xls)
- Images (EXIF metadata + OCR)
- Audio (EXIF metadata + speech transcription)
- HTML, CSV, JSON, XML
- ZIP archives (iterates over contents)
- YouTube URLs (transcripts)
- EPub
- Outlook email messages (optional extra)

## Requirements & installation

- Python **3.10+**.
- `pip install 'markitdown[all]'` for everything, or selective extras:
  `[pptx]`, `[docx]`, `[xlsx]`, `[xls]`, `[pdf]`, `[outlook]`,
  `[audio-transcription]`, `[youtube-transcription]`,
  `[az-doc-intel]`, `[az-content-understanding]`.
- Dockerfile provided for containerized use.

## Usage

CLI:

```bash
markitdown path-to-file.pdf > document.md
markitdown path-to-file.pdf -o document.md
cat path-to-file.pdf | markitdown
```

Python API:

```python
from markitdown import MarkItDown
md = MarkItDown()
result = md.convert("test.xlsx")
print(result.text_content)
```

Optional LLM client can be attached for image descriptions
(`MarkItDown(llm_client=..., llm_model=...)`).

## Extensions

- **Plugin system**: third-party converter plugins, enabled with
  `--use-plugins` (e.g. `markitdown-ocr` for LLM-vision OCR).
- **Azure Document Intelligence**: cloud-based extraction via
  `markitdown file.pdf -d -e "<endpoint>"`.
- **Azure Content Understanding**: higher-quality conversion with
  structured field extraction emitted as YAML front matter,
  multi-modal support, custom analyzers.

## Caveats (from the project docs)

- Output is optimized for machine consumption; formatting fidelity is
  not the goal (PDF headings often flatten, tables can degrade).
- MarkItDown performs I/O with the privileges of the current process —
  sanitize inputs in untrusted environments and call the narrowest
  conversion function appropriate to the use case.
