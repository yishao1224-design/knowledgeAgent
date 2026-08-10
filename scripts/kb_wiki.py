#!/usr/bin/env python3
"""kb_wiki.py — render the kb/ OKF bundle into an Azure DevOps wiki tree.

Publishes the bundle *out* as a browsable ADO wiki (one-way): kb/ stays
the source of truth, the generated tree is a rendered view you push into
a `<Project>.wiki` Git repo (or point "publish code as wiki" at).

What it does that a raw folder can't:
  - strips YAML frontmatter and renders a compact status/trust banner
    (⚠ needs_review, 🛑 deprecated, 📝 draft) plus a metadata line;
  - rewrites bundle-relative links (`/concepts/foo.md`) to ADO wiki
    page paths (`/Concepts/Foo-Title`); links to excluded pages degrade
    to plain text, and citations to excluded sources fall back to the
    source's `source_url`;
  - lays pages out under `Section.md` + `Section/` with `.order` files
    so ADO builds a real table of contents;
  - names files from each page's `title` (ADO shows hyphen-as-space).

Usage:
  python scripts/kb_wiki.py export [--out DIR] [--include-sources]
                                   [--include-archive] [--no-schema]
                                   [--no-log] [--force]

Default --out is dist/ado-wiki. The output dir is fully regenerated each
run; a `.kb-wiki-export` marker guards against clobbering an unrelated
directory (e.g. a live .wiki checkout) unless --force is given.

Stdlib only. Reuses the bundle parser from okf.py.
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import okf  # noqa: E402  (frontmatter loader, link resolver, KB root)

MARKER = ".kb-wiki-export"
LINK_RE = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)\)")

# dir (top-level bundle folder) -> (wiki section title, sort order)
SECTIONS = [
    ("concepts", "Concepts"),
    ("entities", "Entities"),
    ("comparisons", "Comparisons"),
    ("queries", "Queries"),
]
DISALLOWED = '/\\#:<>*?|"'


def wiki_name(title):
    """Turn a page title into an ADO-legal file stem (spaces -> hyphens)."""
    s = str(title or "").strip()
    for ch in DISALLOWED:
        s = s.replace(ch, "")
    s = re.sub(r"\s+", "-", s)
    s = s.strip(".-")
    return s or "Untitled"


def load_page(path):
    meta, body, had_fm = okf.load(path)
    return (meta or {}), body


def banner(meta, from_file, path_to_wiki):
    """Status/trust callout + metadata line rendered from frontmatter."""
    status = str(meta.get("status", "")).strip()
    out = []
    if status == "needs_review":
        out.append("> ⚠️ **Needs review** — overdue for verification or "
                   "flagged; treat these claims with caution.")
    elif status == "deprecated":
        note = ""
        sb = meta.get("superseded_by")
        if sb:
            tgt = okf.resolve_link(str(sb), from_file)
            wp = path_to_wiki.get(tgt) if tgt else None
            note = (f" Superseded by [{wp.rsplit('/', 1)[-1]}]({wp})."
                    if wp else f" Superseded by `{sb}`.")
        out.append(f"> 🛑 **Deprecated** — do not rely on this page.{note}")
    elif status == "draft":
        out.append("> 📝 **Draft** — captured but not yet verified.")

    bits = []
    if status:
        bits.append(f"Status: {status}")
    if meta.get("updated"):
        bits.append(f"Updated: {meta['updated']}")
    if meta.get("review_after"):
        bits.append(f"Review after: {meta['review_after']}")
    tags = meta.get("tags") or []
    if isinstance(tags, list) and tags:
        bits.append("Tags: " + ", ".join(str(t) for t in tags))
    if out:
        out.append("")
    if bits:
        out.append("*" + " · ".join(bits) + "*")
    return ("\n".join(out) + "\n\n") if out or bits else ""


def rewrite_links(body, from_file, path_to_wiki, source_urls):
    spans = okf.code_spans(body)

    def in_code(pos):
        return any(s <= pos < e for s, e in spans)

    def repl(m):
        if in_code(m.start()):
            return m.group(0)
        bang, text, target = m.group(1), m.group(2), m.group(3)
        if target.startswith("#") or "://" in target or \
                target.startswith("mailto:"):
            return m.group(0)
        frag = ""
        tgt = target
        if "#" in tgt:
            tgt, f = tgt.split("#", 1)
            frag = "#" + f
        resolved = okf.resolve_link(tgt, from_file)
        if resolved is None:
            return m.group(0)
        wp = path_to_wiki.get(resolved)
        if wp:
            return f"{bang}[{text}]({wp}{frag})"
        url = source_urls.get(resolved)
        if url:                       # excluded source -> original URL
            return f"[{text}]({url})"
        return text                   # excluded/missing page -> plain text

    return LINK_RE.sub(repl, body)


def insert_banner(body, banner_md):
    if not banner_md:
        return body
    lines = body.splitlines(keepends=True)
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("# "):
            rest = "".join(lines[i + 1:]).lstrip("\n")
            return "".join(lines[:i + 1]) + "\n" + banner_md + rest
    return banner_md + body


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8", newline="\n")


def cmd_export(args):
    kb = okf.KB
    if not kb.exists():
        print(f"ERROR: no bundle at {kb} — run 'okf.py init' first",
              file=sys.stderr)
        return 2

    out = Path(args.out)
    if not out.is_absolute():
        out = okf.ROOT / out
    if out.exists():
        if not (out / MARKER).exists() and not args.force:
            print(f"ERROR: {out} exists and is not a prior export "
                  f"(no {MARKER}). Refusing to overwrite — pass --force "
                  f"or choose another --out.", file=sys.stderr)
            return 2
        shutil.rmtree(out)
    out.mkdir(parents=True)
    write(out / MARKER, "Generated by kb_wiki.py — do not edit; regenerate.\n")

    # ---- 1. decide what's included, group pages by section ----------------
    grouped = {}                      # dir -> list[(title, stem, meta, path)]
    for dirname, section in SECTIONS:
        d = kb / dirname
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.md")):
            meta, _ = load_page(p)
            title = str(meta.get("title") or p.stem)
            grouped.setdefault(dirname, []).append(
                (title, wiki_name(title), meta, p))

    if args.include_archive and (kb / "archive").is_dir():
        for p in sorted((kb / "archive").rglob("*.md")):
            meta, _ = load_page(p)
            title = str(meta.get("title") or p.stem)
            grouped.setdefault("archive", []).append(
                (title, wiki_name(title), meta, p))

    # ---- 2. build path -> wiki-link map, and source-url fallbacks ---------
    dir_to_section = dict(SECTIONS)
    dir_to_section["archive"] = "Archive"
    path_to_wiki = {}
    for dirname, pages in grouped.items():
        section = dir_to_section[dirname]
        for title, stem, meta, p in pages:
            path_to_wiki[p.resolve()] = f"/{section}/{stem}"

    source_urls = {}
    for p in sorted((kb / "sources").rglob("*.md")) if (kb / "sources").is_dir() else []:
        meta, _ = load_page(p)
        if args.include_sources:
            title = str(meta.get("title") or p.stem)
            grouped.setdefault("sources", []).append(
                (title, wiki_name(title), meta, p))
            path_to_wiki[p.resolve()] = f"/Sources/{wiki_name(title)}"
        else:
            url = meta.get("source_url")
            if url:
                source_urls[p.resolve()] = str(url)
    dir_to_section["sources"] = "Sources"

    if not args.no_schema and (kb / "SCHEMA.md").exists():
        path_to_wiki[(kb / "SCHEMA.md").resolve()] = "/Conventions"
    if not args.no_log and (kb / "log.md").exists():
        path_to_wiki[(kb / "log.md").resolve()] = "/Change-Log"

    def render_body(body, from_file, meta=None):
        body = rewrite_links(body, from_file, path_to_wiki, source_urls)
        if meta is not None:
            body = insert_banner(body, banner(meta, from_file, path_to_wiki))
        return body

    # ---- 3. write section landing pages + child pages + .order -----------
    section_order = []                # top-level TOC order
    ordered_dirs = [d for d, _ in SECTIONS] + ["sources", "archive"]
    for dirname in ordered_dirs:
        pages = grouped.get(dirname)
        if not pages:
            continue
        section = dir_to_section[dirname]
        pages.sort(key=lambda t: t[0].lower())
        section_order.append(section)

        landing = [f"# {section}", "", f"{len(pages)} page"
                   f"{'s' if len(pages) != 1 else ''} in this section.", ""]
        child_order = []
        for title, stem, meta, p in pages:
            desc = str(meta.get("description") or "").strip()
            landing.append(f"* [{title}](/{section}/{stem})"
                           + (f" — {desc}" if desc else ""))
            child_order.append(stem)
            _, body = load_page(p)
            write(out / section / f"{stem}.md",
                  render_body(body, p, meta))
        write(out / f"{section}.md", "\n".join(landing))
        write(out / section / ".order", "\n".join(child_order))

    # ---- 4. meta pages (Conventions, Change-Log) ------------------------
    meta_order = []
    if not args.no_schema and (kb / "SCHEMA.md").exists():
        _, body = load_page(kb / "SCHEMA.md")
        write(out / "Conventions.md", render_body(body, kb / "SCHEMA.md"))
        meta_order.append("Conventions")
    if not args.no_log and (kb / "log.md").exists():
        text = (kb / "log.md").read_text(encoding="utf-8", errors="replace")
        body = re.sub(r"^#\s+.*\n", "", text, count=1).lstrip("\n")
        body = "# Change Log\n\n" + body
        write(out / "Change-Log.md",
              render_body(body, kb / "log.md"))
        meta_order.append("Change-Log")

    # ---- 5. Home + root .order ------------------------------------------
    home = ["# Knowledge Base", "",
            "Rendered from the OKF knowledge bundle. Each page carries a "
            "status banner — heed ⚠️ *needs review* and 🛑 *deprecated* "
            "notices.", ""]
    for section in section_order:
        home.append(f"## {section}")
        home.append(f"See **[{section}](/{section})**.")
        home.append("")
    write(out / "Home.md", "\n".join(home))

    root_order = ["Home"] + section_order + meta_order
    write(out / ".order", "\n".join(root_order))

    n_pages = sum(len(v) for v in grouped.values())
    print(f"exported {n_pages} page(s) across {len(section_order)} section(s) "
          f"to {out}")
    print(f"  sections: {', '.join(section_order) or '(none)'}")
    print(f"  meta: {', '.join(meta_order) or '(none)'}")
    if not args.include_sources:
        print(f"  sources: excluded ({len(source_urls)} citation link(s) "
              f"kept as source_url; use --include-sources to publish them)")
    print("\nNext: copy the contents of this directory into your "
          "<Project>.wiki checkout (or point 'publish code as wiki' at it), "
          "then commit & push to the wikiMain branch.")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export", help="render the bundle to an ADO wiki tree")
    e.add_argument("--out", default="dist/ado-wiki")
    e.add_argument("--include-sources", action="store_true",
                   help="publish kb/sources/ captures as wiki pages")
    e.add_argument("--include-archive", action="store_true",
                   help="publish kb/archive/ pages")
    e.add_argument("--no-schema", action="store_true",
                   help="omit the Conventions page (from SCHEMA.md)")
    e.add_argument("--no-log", action="store_true",
                   help="omit the Change-Log page (from log.md)")
    e.add_argument("--force", action="store_true",
                   help="overwrite --out even without an export marker")
    args = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):   # tolerate cp1252 consoles
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    return {"export": cmd_export}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
