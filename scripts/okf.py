#!/usr/bin/env python3
"""okf.py — mechanical toolchain for an OKF bundle (default: okf/).

Subcommands:
  init             bootstrap the bundle skeleton + sync skills/ to per-tool
                   copies (.claude/skills/, .github/prompts/ for Copilot)
  lint             conformance + lifecycle audit (exit 1 on errors)
  lint --inbound P list files linking to bundle path P (safe-delete check)
  index            regenerate the bundle's index.md from tree + frontmatter
  links            expand [[slug]] shorthand into canonical bundle links
  log "MESSAGE"    prepend a log entry under today's date
  stats            counts by type/lifecycle, review queue
  drift            recheck pinned sources against their current git blob
  drift --hash F   print the blob sha to pin for file F

Every subcommand takes --bundle NAME to point at a differently-named
bundle directory. Without it the bundle is auto-detected (any top-level
directory holding a SCHEMA.md), falling back to the okf/ default.

The bundle targets OKF v0.2: `status` carries a standard v0.2 value and
this bundle's richer five-state lifecycle lives in the `lifecycle`
extension key, derived from it by LIFECYCLE_STATUS below.

Stdlib only. Uses PyYAML if installed, else a minimal frontmatter parser
sufficient for the SCHEMA.md templates (scalars, inline lists and maps,
block lists of scalars or mappings, one level of nested mapping).
"""

import argparse
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BUNDLE = "okf"
# Resolved by main() before any subcommand runs; see resolve_bundle().
KB = ROOT / DEFAULT_BUNDLE
# Never scanned when sniffing for an existing bundle.
NON_BUNDLE_DIRS = {".git", ".github", ".claude", ".agents", ".cursor",
                   "node_modules", "scripts", "skills", "dist", "__pycache__"}
RESERVED = {"index.md", "log.md"}
OKF_VERSION = "0.2"
# OKF v0.2 defines `status` with exactly these three values. This bundle's
# five-state lifecycle is richer, so it lives in the `lifecycle` extension
# key and `status` is derived from it: a plain v0.2 consumer reads a legal
# standard field, a lifecycle-aware one reads the detail.
OKF_STATUSES = {"draft", "stable", "deprecated"}
LIFECYCLE = {"draft", "active", "needs_review", "deprecated", "archived"}
LIFECYCLE_STATUS = {"draft": "draft", "active": "stable",
                    "needs_review": "stable", "deprecated": "deprecated",
                    "archived": "deprecated"}
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
WIKILINK_RE = re.compile(r"\[\[([^\]|\n]+?)(?:\|([^\]\n]+?))?\]\]")
TAG_DEF_RE = re.compile(r"^\s*[-*]\s+`([A-Za-z0-9_-]+)`", re.M)

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


# ---------------------------------------------------------------- parsing

def split_frontmatter(text):
    """Return (frontmatter_str_or_None, body)."""
    if text.startswith("﻿"):
        text = text[1:]
    if not text.startswith("---"):
        return None, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not m:
        return None, text
    return m.group(1), text[m.end():]


# `key:` must be followed by whitespace or end-of-line, so a bare list
# item like `- https://example.com` is not mistaken for a `https:` key.
KEY_RE = re.compile(r"^([A-Za-z0-9_.-]+):(?:[ 	]+(.*))?$")


def _scalar(val):
    val = (val or "").strip()
    if val.startswith("[") and val.endswith("]"):
        return [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
    if val.startswith("{") and val.endswith("}"):
        out = {}
        for part in val[1:-1].split(","):
            if ":" in part:
                k, v = part.split(":", 1)
                out[k.strip()] = v.strip().strip("'\"")
        return out
    return val.split(" #")[0].strip().strip("'\"")


def _indent(line):
    return len(line) - len(line.lstrip())


def _skip_blank(lines, i):
    while i < len(lines) and (not lines[i].strip()
                              or lines[i].lstrip().startswith("#")):
        i += 1
    return i


def _parse_list(lines, i, indent):
    """Block list at `indent`; items are scalars or mappings."""
    items = []
    while i < len(lines):
        i = _skip_blank(lines, i)
        if i >= len(lines):
            break
        cur, stripped = _indent(lines[i]), lines[i].lstrip()
        if cur < indent or not stripped.startswith("- "):
            break
        rest = stripped[2:].strip()
        m = KEY_RE.match(rest)
        if not m:
            items.append(_scalar(rest))
            i += 1
            continue
        item = {m.group(1): _scalar(m.group(2))}
        i += 1
        while i < len(lines):                       # continuation keys
            i = _skip_blank(lines, i)
            if i >= len(lines):
                break
            c2, s2 = _indent(lines[i]), lines[i].lstrip()
            if c2 <= cur or s2.startswith("- "):
                break
            m2 = KEY_RE.match(s2.rstrip())
            if m2:
                item[m2.group(1)] = _scalar(m2.group(2))
            i += 1
        items.append(item)
    return items, i


def _parse_block(lines, i, indent):
    """Mapping block at `indent`. Returns (dict, next_index)."""
    data = {}
    while i < len(lines):
        i = _skip_blank(lines, i)
        if i >= len(lines):
            break
        cur, stripped = _indent(lines[i]), lines[i].lstrip()
        if cur < indent or stripped.startswith("- "):
            break
        m = KEY_RE.match(stripped.rstrip())
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2)
        if val is not None and val.strip():
            data[key] = _scalar(val)
            i += 1
            continue
        j = _skip_blank(lines, i + 1)               # block list or sub-map?
        if j < len(lines):
            nind, nstr = _indent(lines[j]), lines[j].lstrip()
            if nstr.startswith("- ") and nind >= cur:
                data[key], i = _parse_list(lines, j, nind)
                continue
            if nind > cur:
                data[key], i = _parse_block(lines, j, nind)
                continue
        data[key] = []
        i += 1
    return data, i


def parse_yaml_min(src):
    """Minimal YAML subset: scalars, inline [a, b] / {k: v}, block lists of
    scalars or mappings, and one level of nested mapping — enough for the
    OKF v0.2 frontmatter shapes in SCHEMA.md."""
    return _parse_block(src.splitlines(), 0, 0)[0]


def parse_frontmatter(src):
    if yaml is not None:
        try:
            d = yaml.safe_load(src)
            return d if isinstance(d, dict) else None
        except yaml.YAMLError:
            return None
    try:
        return parse_yaml_min(src)
    except Exception:
        return None


def load(path):
    """Return (meta_or_None, body, raw_fm_present)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    fm, body = split_frontmatter(text)
    if fm is None:
        return None, body, False
    return parse_frontmatter(fm), body, True


def concept_files():
    """All non-reserved .md files in the bundle."""
    return sorted(
        p for p in KB.rglob("*.md")
        if p.name not in RESERVED
    )


def rel(path):
    """Bundle-relative path with leading slash, forward slashes."""
    return "/" + path.relative_to(KB).as_posix()


def resolve_link(target, from_file):
    """Resolve a markdown link target to a bundle Path, or None if external."""
    target = target.split("#")[0]
    if not target or "://" in target or target.startswith("mailto:"):
        return None
    if target.startswith("/"):
        return (KB / target.lstrip("/")).resolve()
    return (from_file.parent / target).resolve()


def strip_code(text):
    """Remove fenced code blocks and inline code spans so example links
    in templates/snippets aren't linted as real links."""
    text = re.sub(r"^```.*?^```", "", text, flags=re.M | re.S)
    return re.sub(r"`[^`\n]*`", "", text)


def code_spans(text):
    """(start, end) offset ranges of fenced code blocks and inline code
    spans — regions where wiki-links must NOT be expanded (they may be
    literal examples, e.g. in SCHEMA.md)."""
    spans = []
    for m in re.finditer(r"```.*?```", text, re.S):
        spans.append((m.start(), m.end()))
    for m in re.finditer(r"`[^`\n]*`", text):
        if any(s <= m.start() < e for s, e in spans):
            continue
        spans.append((m.start(), m.end()))
    return spans


def build_resolver(files):
    """Map lower-cased filename stems and titles to bundle Paths, so
    [[slug]] shorthand can be resolved to a concrete page. A key that maps
    to more than one page is ambiguous."""
    by_key = {}
    for p in files:
        meta, _, _ = load(p)
        keys = {p.stem.lower()}
        title = str((meta or {}).get("title") or "").strip().lower()
        if title:
            keys.add(title)
        for k in keys:
            bucket = by_key.setdefault(k, [])
            if p not in bucket:
                bucket.append(p)
    return by_key


def resolve_wikilink(target, by_key):
    """Resolve a [[target]] to (Path, status), status in
    {ok, ambiguous, missing}. A target containing '/' or ending '.md' is
    treated as an explicit bundle path; otherwise it is matched by stem
    or title (case-insensitive)."""
    t = target.strip()
    if t.startswith("/") or "/" in t or t.lower().endswith(".md"):
        cand = (KB / t.lstrip("/")).resolve()
        return (cand, "ok") if cand.exists() else (None, "missing")
    hits = by_key.get(t.lower(), [])
    if len(hits) == 1:
        return hits[0], "ok"
    if len(hits) > 1:
        return None, "ambiguous"
    return None, "missing"


def taxonomy():
    schema = KB / "SCHEMA.md"
    if not schema.exists():
        return None
    text = schema.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^#+\s*Tag taxonomy\s*$(.*?)(?=^#\s)", text, re.M | re.S)
    if not m:
        return None
    return set(TAG_DEF_RE.findall(m.group(1)))


TYPE_ROW_RE = re.compile(r"^\|\s*`([A-Za-z0-9_-]+)`\s*\|([^|]*)\|", re.M)


def type_registry():
    """Parse SCHEMA.md's 'Type registry' table into {type: top-level dir}
    ('' = bundle root). None if SCHEMA.md or the section is absent."""
    schema = KB / "SCHEMA.md"
    if not schema.exists():
        return None
    text = schema.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^#+\s*Type registry\s*$(.*?)(?=^#\s)", text, re.M | re.S)
    if not m:
        return None
    reg = {}
    for typ, where in TYPE_ROW_RE.findall(m.group(1)):
        where = where.strip().strip("`").strip().rstrip("/")
        reg[typ] = "" if where == "root" else where
    return reg or None


def parse_date(s):
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


# ------------------------------------------------------------------ drift

def git_blob(path):
    """Current git blob sha of a working-tree file, or None when git is
    unavailable. Hashing the working tree (not HEAD) means an uncommitted
    edit to pinned evidence still registers as drift."""
    import subprocess
    try:
        out = subprocess.run(["git", "hash-object", str(path)], cwd=str(ROOT),
                             capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip() or None


def resolve_resource(resource, page):
    """Resolve a sources[].resource to a filesystem path, or None when it is
    not a local file (absolute URL, or a scope descriptor). Relative paths
    are document-relative per OKF v0.2 — that is what lets a page reach repo
    files outside the bundle (`../../scripts/okf.py`)."""
    t = str(resource or "").split("#")[0].strip()
    if not t or "://" in t or t.startswith("mailto:"):
        return None
    if t.startswith("/"):
        return (KB / t.lstrip("/")).resolve()
    return (page.parent / t).resolve()


def check_drift(files):
    """Compare each pinned source entry's `blob:` against the file's current
    blob sha. Returns (results, git_available); results are tuples of
    (page, resource, state, pinned, current), state in ok|moved|gone."""
    results = []
    if git_blob(Path(__file__)) is None:
        return results, False
    for p in files:
        meta, _, _ = load(p)
        entries = (meta or {}).get("sources") or []
        if isinstance(entries, str):
            entries = [entries]
        for entry in entries:
            if not isinstance(entry, dict) or not entry.get("blob"):
                continue
            pinned = str(entry["blob"]).strip()
            res = str(entry.get("resource", ""))
            target = resolve_resource(res, p)
            if target is None:
                continue
            if not target.exists():
                results.append((rel(p), res, "gone", pinned, None))
                continue
            cur = git_blob(target)
            if cur is None:
                continue
            state = "ok" if cur.startswith(pinned) else "moved"
            results.append((rel(p), res, state, pinned, cur))
    return results, True


def cmd_drift(args):
    if args.hash:
        h = git_blob(Path(args.hash))
        if h is None:
            print(f"ERROR: cannot hash {args.hash}", file=sys.stderr)
            return 2
        print(h[:12])
        return 0
    files = concept_files()
    results, git_ok = check_drift(files)
    if not git_ok:
        print("drift: git unavailable — no pinned source checked")
        return 0
    stale = [x for x in results if x[2] != "ok"]
    for page, res, state, pinned, cur in results:
        if state == "gone":
            print(f"GONE:  {page} -> {res} (pinned {pinned}; file is missing)")
        elif state == "moved":
            print(f"MOVED: {page} -> {res} (pinned {pinned}, now {cur[:12]})")
    print(f"\ndrift: {len(stale)} stale of {len(results)} pinned source(s)")
    if stale:
        print("re-verify each page against its file, then restamp with "
              "'okf.py drift --hash <file>' — and set lifecycle: needs_review "
              "if the claims themselves moved")
    return 1 if stale else 0


# ------------------------------------------------------------------- lint

def cmd_lint(args):
    errors, warns, infos = [], [], []
    files = concept_files()
    tags_known = taxonomy()
    types_known = type_registry()
    by_key = build_resolver(files)   # for wiki-link resolution
    inbound = {}          # bundle path -> set of linking files
    all_paths = {p.resolve() for p in files}

    # collect inbound links from every md file, including index/log
    for p in sorted(KB.rglob("*.md")):
        _, body, _ = load(p)
        src = body if p.name not in RESERVED else p.read_text(encoding="utf-8", errors="replace")
        for t in LINK_RE.findall(strip_code(src)):
            tgt = resolve_link(t, p)
            if tgt is not None:
                inbound.setdefault(tgt, set()).add(p)

    if args.inbound:
        target = (KB / args.inbound.lstrip("/")).resolve()
        linkers = sorted(inbound.get(target, ()))
        print(f"inbound links to {args.inbound}: {len(linkers)}")
        for l in linkers:
            print(f"  {rel(l)}")
        return 0

    today = date.today()
    for p in files:
        r = rel(p)
        meta, body, had_fm = load(p)
        if not had_fm:
            errors.append(f"{r}: missing frontmatter")
            continue
        if meta is None:
            errors.append(f"{r}: unparseable frontmatter")
            continue

        # OKF conformance
        typ = str(meta.get("type", "")).strip()
        if not typ:
            errors.append(f"{r}: frontmatter has no non-empty 'type' (OKF §9)")
        elif types_known is not None:
            parts = p.relative_to(KB).parts
            top = parts[0] if len(parts) > 1 else ""
            if typ not in types_known:
                warns.append(f"{r}: type '{typ}' not in SCHEMA.md type "
                             f"registry — add it there before first use")
            elif top != "archive" and top != types_known[typ]:
                expected = (f"/{types_known[typ]}/" if types_known[typ]
                            else "the bundle root")
                errors.append(f"{r}: type '{typ}' belongs in {expected} "
                              f"per SCHEMA.md type registry")

        # lifecycle profile — OKF v0.2 `status` plus this bundle's `lifecycle`
        status = str(meta.get("status", "")).strip()
        life = str(meta.get("lifecycle", "")).strip()
        if status and status not in OKF_STATUSES:
            errors.append(f"{r}: status '{status}' is not an OKF v0.2 value "
                          f"({'|'.join(sorted(OKF_STATUSES))}) — the five-state "
                          f"lifecycle belongs in 'lifecycle:'")
        if life and life not in LIFECYCLE:
            errors.append(f"{r}: unknown lifecycle '{life}'")
        if life in LIFECYCLE and status and LIFECYCLE_STATUS[life] != status:
            errors.append(f"{r}: lifecycle '{life}' implies status "
                          f"'{LIFECYCLE_STATUS[life]}', found '{status}'")
        is_source = p.is_relative_to(KB / "sources")
        if p == KB / "SCHEMA.md":
            continue  # meta-file: OKF conformance applies, lifecycle rules don't

        if is_source:
            if not meta.get("source_url"):
                warns.append(f"{r}: source capture missing source_url")
            continue  # sources are exempt from the rest

        for field in ("title", "description", "status", "lifecycle", "updated"):
            if not meta.get(field):
                warns.append(f"{r}: missing '{field}'")
        if meta.get("review_after"):
            warns.append(f"{r}: legacy 'review_after' — OKF v0.2 names this "
                         f"field 'stale_after'")
        if life == "active" and not meta.get("stale_after"):
            warns.append(f"{r}: active but no stale_after")
        if life == "deprecated" and not meta.get("superseded_by") \
                and "## Deprecation" not in body:
            errors.append(f"{r}: deprecated without superseded_by or '## Deprecation' section")
        if life == "archived" and not p.is_relative_to(KB / "archive"):
            warns.append(f"{r}: archived but not under /archive/")

        sa = parse_date(meta.get("stale_after"))
        if life == "active" and sa and sa < today:
            warns.append(f"{r}: review overdue since {sa} — set "
                         f"lifecycle: needs_review or re-verify")

        # sources shape — OKF v0.2 entries are mappings carrying a `resource`
        srcs = meta.get("sources") or []
        if isinstance(srcs, str):
            srcs = [srcs]
        seen_ids = set()
        for entry in srcs:
            if not isinstance(entry, dict):
                warns.append(f"{r}: legacy source entry '{entry}' — v0.2 wants "
                             f"a mapping with 'resource:'")
                continue
            if not str(entry.get("resource", "")).strip():
                errors.append(f"{r}: source entry without 'resource'")
            sid = str(entry.get("id", "")).strip()
            if sid and sid in seen_ids:
                errors.append(f"{r}: duplicate source id '{sid}'")
            if sid:
                seen_ids.add(sid)
        if re.search(r"^#+\s*Citations\s*$", body, re.M):
            warns.append(f"{r}: '# Citations' section — v0.2 replaced it with "
                         f"the 'sources' frontmatter; cite as [<source id>]")

        # tags
        if tags_known is not None:
            tags = meta.get("tags") or []
            if isinstance(tags, str):
                tags = [tags]
            for t in tags:
                if t not in tags_known:
                    warns.append(f"{r}: tag '{t}' not in SCHEMA.md taxonomy")

        # links
        n_out = 0
        for t in LINK_RE.findall(strip_code(body)):
            tgt = resolve_link(t, p)
            if tgt is None:
                continue
            n_out += 1
            if tgt.suffix == ".md" and tgt not in all_paths \
                    and tgt.name not in RESERVED and not tgt.exists():
                infos.append(f"{r}: link to not-yet-written page ({t})")
        if life in ("active", "needs_review") and n_out < 2:
            warns.append(f"{r}: only {n_out} outbound bundle link(s); minimum is 2")

        # wiki-links — authoring sugar that must be expanded before commit
        for m in WIKILINK_RE.finditer(strip_code(body)):
            tgt = m.group(1).strip()
            _, st = resolve_wikilink(tgt, by_key)
            if st == "ambiguous":
                warns.append(f"{r}: ambiguous wiki-link [[{tgt}]] — matches "
                             f"multiple pages; use [[/path.md|text]]")
            elif st == "missing":
                infos.append(f"{r}: unresolved wiki-link [[{tgt}]] "
                             f"(target not yet written)")
            else:
                warns.append(f"{r}: unexpanded wiki-link [[{tgt}]] — run "
                             f"'python scripts/okf.py links'")

        # orphan check (not linked from anywhere, incl. index)
        if p.resolve() not in inbound and p.name != "SCHEMA.md":
            warns.append(f"{r}: orphan — no inbound links and not in index.md "
                         f"(run 'okf.py index')")

    # pinned-source drift (skipped silently when git is unavailable)
    for page, res, state, pinned, cur in check_drift(files)[0]:
        if state == "moved":
            warns.append(f"{page}: pinned source {res} changed since "
                         f"{pinned} — run 'okf.py drift' and re-verify")
        elif state == "gone":
            warns.append(f"{page}: pinned source {res} no longer exists")

    # reserved-file rules
    for idx in KB.rglob("index.md"):
        fm, _, had = load(idx)
        if had and idx.parent != KB:
            errors.append(f"{rel(idx)}: index.md may only carry frontmatter at bundle root (OKF §6/§11)")

    for label, items in (("ERROR", errors), ("WARN", warns), ("INFO", infos)):
        for msg in items:
            print(f"{label}: {msg}")
    print(f"\nlint: {len(errors)} error(s), {len(warns)} warning(s), "
          f"{len(infos)} info(s) across {len(files)} concept file(s)")
    return 1 if errors else 0


# ------------------------------------------------------------------ index

SECTION_ORDER = ["concepts", "entities", "comparisons", "queries",
                 "sources", "archive"]


def cmd_index(args):
    entries = {}
    for p in concept_files():
        meta, _, _ = load(p)
        meta = meta or {}
        top = p.relative_to(KB).parts[0]
        section = top if (KB / top).is_dir() else "_root"
        title = meta.get("title") or p.stem
        desc = str(meta.get("description") or "").strip()
        life = str(meta.get("lifecycle") or "").strip()
        badge = f" *({life})*" if life in ("needs_review", "deprecated", "archived") else ""
        entries.setdefault(section, []).append(
            f"* [{title}]({p.relative_to(KB).as_posix()}) - {desc}{badge}")

    total = sum(len(v) for v in entries.values())
    lines = ['---', f'okf_version: "{OKF_VERSION}"', '---', '',
             '# Bundle Index', '']
    for e in sorted(entries.pop("_root", [])):
        lines.append(e)
    order = SECTION_ORDER + sorted(set(entries) - set(SECTION_ORDER))
    for sec in order:
        if sec not in entries:
            continue
        lines += ["", f"# {sec.capitalize()}", ""]
        lines += sorted(entries[sec])
    (KB / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8",
                                 newline="\n")
    print(f"index.md regenerated: {total} entries")
    return 0


# ------------------------------------------------------------------ links

def cmd_links(args):
    """Expand [[slug]] / [[slug|display text]] authoring shorthand into
    canonical bundle-relative markdown links, in place. Targets that are
    ambiguous or not-yet-written are left untouched and reported, so the
    committed bundle only ever contains plain-OKF-readable links."""
    files = concept_files()
    by_key = build_resolver(files)
    title_of = {}
    for p in files:
        meta, _, _ = load(p)
        title_of[p.resolve()] = str((meta or {}).get("title") or p.stem).strip()

    expanded = amb = missing = changed = 0
    for p in files:
        text = p.read_text(encoding="utf-8", errors="replace")
        spans = code_spans(text)
        out, last, n = [], 0, 0
        for m in WIKILINK_RE.finditer(text):
            if any(s <= m.start() < e for s, e in spans):
                continue  # literal example inside code — never rewrite
            target, disp = m.group(1), m.group(2)
            path, st = resolve_wikilink(target, by_key)
            if st != "ok":
                amb += st == "ambiguous"
                missing += st == "missing"
                continue  # leave unresolved shorthand in place
            label = (disp or title_of.get(path.resolve()) or target).strip()
            out.append(text[last:m.start()])
            out.append(f"[{label}]({rel(path)})")
            last = m.end()
            n += 1
        if n:
            out.append(text[last:])
            p.write_text("".join(out), encoding="utf-8", newline="\n")
            changed += 1
            expanded += n
    print(f"links: expanded {expanded} wiki-link(s) in {changed} file(s)")
    if amb:
        print(f"  {amb} ambiguous — left as-is; disambiguate with [[/path.md|text]]")
    if missing:
        print(f"  {missing} unresolved — left as-is; target page not written yet")
    return 0


# -------------------------------------------------------------------- log

def cmd_log(args):
    logf = KB / "log.md"
    text = logf.read_text(encoding="utf-8") if logf.exists() else "# Bundle Update Log\n"
    today = date.today().isoformat()
    entry = f"* {args.message.strip()}"
    heading = f"## {today}"
    if heading in text:
        text = text.replace(heading, f"{heading}\n{entry}", 1)
    else:
        # insert after the H1 line
        lines = text.splitlines()
        h1 = next((i for i, l in enumerate(lines) if l.startswith("# ")), 0)
        lines[h1 + 1:h1 + 1] = ["", heading, entry]
        text = "\n".join(lines) + ("\n" if not text.endswith("\n") else "")
    logf.write_text(text, encoding="utf-8", newline="\n")
    n = text.count("\n* ") + text.count("\n*\t")
    print(f"logged under {heading} ({n} entries total)")
    if n > 500:
        print(f"WARN: log.md exceeds 500 entries — rotate old years to "
              f"{KB.name}/archive/log-YYYY.md")
    return 0


# ------------------------------------------------------------------ stats

def cmd_stats(args):
    by_type, by_life, queue = {}, {}, []
    today = date.today()
    files = concept_files()
    for p in files:
        meta, _, _ = load(p)
        meta = meta or {}
        by_type[str(meta.get("type", "?"))] = by_type.get(str(meta.get("type", "?")), 0) + 1
        life = str(meta.get("lifecycle", "?"))
        by_life[life] = by_life.get(life, 0) + 1
        sa = parse_date(meta.get("stale_after"))
        if life == "needs_review" or (life == "active" and sa and sa < today):
            queue.append((sa or date.min, rel(p)))
    print(f"{len(files)} concept file(s)\n\nby type:")
    for k, v in sorted(by_type.items(), key=lambda kv: -kv[1]):
        print(f"  {k}: {v}")
    print("\nby lifecycle:")
    for k, v in sorted(by_life.items(), key=lambda kv: -kv[1]):
        print(f"  {k}: {v}")
    print(f"\nreview queue ({len(queue)}):")
    for sa, r in sorted(queue):
        print(f"  {r}" + (f" (due {sa})" if sa != date.min else ""))
    results, git_ok = check_drift(files)
    if git_ok:
        stale = [x for x in results if x[2] != "ok"]
        print(f"\npinned sources: {len(results)} ({len(stale)} stale)")
    return 0


# ------------------------------------------------------------------- init

BUNDLE_DIRS = ["concepts", "entities", "comparisons", "queries",
               "archive", "sources"]

SCHEMA_SEED = """---
type: Schema
title: Bundle Schema & Conventions
description: Authoritative conventions for this OKF bundle — types, tags, frontmatter templates, lifecycle rules.
status: stable
lifecycle: active
updated: {today}
---

# Bundle Schema & Conventions

*(Starter schema written by `okf.py init`. Flesh out the Domain, type
registry, and tag taxonomy on first real ingestion — see the full
template in the knowledgeAgent repo's SCHEMA.md.)*

# Domain

*(one paragraph: what this knowledge base covers and for whom)*

# Type registry

| type | lives in | meaning |
|------|----------|---------|
| `Concept` | `concepts/` | An idea, definition, method, or explanation |
| `Entity` | `entities/` | A concrete nameable thing (person, org, system, dataset, tool) |
| `Comparison` | `comparisons/` | Structured X-vs-Y |
| `Query` | `queries/` | A filed answer to a real question |
| `Source` | `sources/` | Immutable raw capture |
| `Schema` | root | This file only |

Add new types here before first use. Lint enforces this table: an
unlisted `type` is a warning; a known `type` in the wrong directory is
an error (`archive/` is exempt).

# Page frontmatter template (all types)

Shared by every page type. Set `type` and the directory to match the
registry above — **do not default to `type: Concept`** just because
this example shows it.

```yaml
---
type: Concept            # match to directory — see type registry above
title: Human Readable Title
description: One sentence for index/previews.
status: draft            # OKF v0.2: draft | stable | deprecated
lifecycle: draft         # draft | active | needs_review | deprecated | archived
confidence: medium       # low | medium | high
created: {today}
updated: {today}
stale_after: {today}     # required once lifecycle: active
tags: []
sources:
  - resource: /sources/{today}-example.md   # capture, bundle-relative
    id: example                             # cite in the body as [example]
    title: Example capture
  - resource: ../../src/thing.py            # live repo file, doc-relative
    id: thing-impl
    title: thing.py implementation
    last_modified: {today}
    blob: 0000000000aa                      # pin: okf.py drift --hash <file>
verified:                # append one entry per real re-verification
  - by: human:you        # actor: human:<id> | <tool>/<version> | process:<id>
    at: {today}
---
```

`status` is the OKF v0.2 standard field; `lifecycle` is this bundle's
five-state extension and `status` is derived from it (`active` and
`needs_review` are both `stable`; `archived` is `deprecated`). Lint
errors if the two disagree.

Cite sources by `id` in the body — `…as the README states [example]` —
not with a `# Citations` section, which v0.2 replaced with `sources`.
Pin `blob:` only on re-readable local files; `okf.py drift` rechecks
those and lint reports the ones that moved.

Only `type: Concept` pages describing **domain** knowledge (business
rules, processes, system behavior) use the domain-concept body template
(`## Definition`, `## Key Behaviors`/`## Invariants`,
`## Related Concepts` — see the full template in the knowledgeAgent
repo's SCHEMA.md). `Entity`/`Comparison`/`Query` pages and
method/meta `Concept` pages keep free structure instead.

# Tag taxonomy

- `unverified` — claims not yet checked against a second source
- `contested` — sources actively disagree
"""

LOG_SEED = """# Bundle Update Log

## {today}
* **Initialization**: Bundle skeleton created by `okf.py init`.
"""

PROMPT_TMPL = """---
mode: agent
description: {desc}
---

<!-- GENERATED by `python scripts/okf.py init` from skills/{name}/SKILL.md.
     Edit the SKILL.md, not this wrapper. -->

You are working in the knowledgeAgent repo. If you have not already
this session, read `.github/copilot-instructions.md` (operating
contract) and the bundle's `SCHEMA.md` (bundle conventions).

Then read `skills/{name}/SKILL.md` and execute its workflow for the
user's request. Do not skip Step 0 (orientation) or the close-out
steps (index, log, lint).
"""


def cmd_init(args):
    import shutil
    made = []

    # 1 — bundle skeleton
    for d in BUNDLE_DIRS:
        p = KB / d
        if not p.exists():
            p.mkdir(parents=True)
            made.append(f"{KB.name}/{d}/")
    today = date.today().isoformat()
    seeds = {
        KB / "SCHEMA.md": SCHEMA_SEED.format(today=today),
        KB / "log.md": LOG_SEED.format(today=today),
    }
    for path, content in seeds.items():
        if not path.exists():
            path.write_text(content, encoding="utf-8", newline="\n")
            made.append(f"{KB.name}/{path.name}")

    # 2 — sync canonical skills/ to per-tool copies:
    #     .claude/skills/ (Claude Code) and .github/prompts/ (Copilot)
    src = ROOT / "skills"
    dst = ROOT / ".claude" / "skills"

    # 2a — refresh toolchain copies bundled inside skills FIRST, so the
    #      `npx skills add` install ships current scripts. The files in
    #      scripts/ stay the single source of truth.
    scripts_dir = Path(__file__).resolve().parent
    bundles = [
        ("okf.py", src / "kb-setup" / "okf.py"),
    ]
    for fname, bundled in bundles:
        source_file = scripts_dir / fname
        if not source_file.exists() or not bundled.parent.exists():
            continue
        if bundled.resolve() == source_file.resolve():
            continue
        if not bundled.exists() or bundled.read_bytes() != source_file.read_bytes():
            shutil.copyfile(source_file, bundled)
            made.append(f"skills/{bundled.parent.name}/{fname} "
                        f"(refreshed toolchain bundle)")

    prompts = ROOT / ".github" / "prompts"
    synced = []
    if src.exists():
        prompts.mkdir(parents=True, exist_ok=True)
        for skill_dir in sorted(src.iterdir()):
            skill_md = skill_dir / "SKILL.md"
            if not (skill_dir.is_dir() and skill_md.exists()):
                continue
            shutil.copytree(skill_dir, dst / skill_dir.name,
                            dirs_exist_ok=True)
            meta, _, _ = load(skill_md)
            name = (meta or {}).get("name", skill_dir.name)
            desc = (meta or {}).get("description", "")
            (prompts / f"{name}.prompt.md").write_text(
                PROMPT_TMPL.format(name=name, desc=desc), encoding="utf-8",
                newline="\n")
            synced.append(name)

    # 3 — regenerate index and report health
    cmd_index(args)
    for m in made:
        print(f"created {m}")
    print(f"synced {len(synced)} skill(s) to .claude/skills/ and "
          f".github/prompts/: {', '.join(synced) or '(none found)'}")
    print("\nhealth check:")
    return cmd_lint(argparse.Namespace(inbound=None))


# ------------------------------------------------------------- resolution

def detect_bundle(root):
    """Return the existing bundle directory under root, or None.

    A bundle is any top-level directory holding a SCHEMA.md. This is what
    keeps projects that predate the okf default — or that chose their own
    name at setup — working with no flag and no config file. Ambiguity is
    reported rather than guessed at: two candidates mean the caller must
    say which with --bundle.
    """
    found = [p for p in sorted(root.iterdir())
             if p.is_dir() and p.name not in NON_BUNDLE_DIRS
             and (p / "SCHEMA.md").is_file()]
    if len(found) > 1:
        names = ", ".join(p.name for p in found)
        print(f"ERROR: several bundles found ({names}) — pick one with "
              f"--bundle NAME", file=sys.stderr)
        raise SystemExit(2)
    return found[0] if found else None


def resolve_bundle(args):
    """Set the module-level KB from --bundle, detection, or the default."""
    global KB
    if getattr(args, "bundle", None):
        KB = (ROOT / args.bundle).resolve()
        return
    existing = detect_bundle(ROOT)
    KB = existing if existing else ROOT / DEFAULT_BUNDLE


# ------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    # --bundle is accepted after any subcommand, e.g. `okf.py init --bundle wiki`
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--bundle", metavar="NAME",
                        help=f"bundle directory (default: auto-detect, "
                             f"else {DEFAULT_BUNDLE}/)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", parents=[common])
    p = sub.add_parser("lint", parents=[common])
    p.add_argument("--inbound", metavar="PATH")
    sub.add_parser("index", parents=[common])
    sub.add_parser("links", parents=[common])
    p = sub.add_parser("log", parents=[common]);   p.add_argument("message")
    sub.add_parser("stats", parents=[common])
    p = sub.add_parser("drift", parents=[common])
    p.add_argument("--hash", metavar="FILE",
                   help="print the blob sha to pin for FILE and exit")
    args = ap.parse_args()
    resolve_bundle(args)
    if args.cmd == "init":
        KB.mkdir(exist_ok=True)
    elif not KB.exists():
        print(f"ERROR: bundle not found at {KB} — run 'okf.py init'"
              f" (or pass --bundle NAME)", file=sys.stderr)
        return 2
    return {"init": cmd_init, "lint": cmd_lint, "index": cmd_index,
            "links": cmd_links, "log": cmd_log, "stats": cmd_stats,
            "drift": cmd_drift}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
