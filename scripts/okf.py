#!/usr/bin/env python3
"""okf.py — mechanical toolchain for an OKF bundle (default: okf/).

Subcommands:
  init             bootstrap the bundle skeleton + sync skills/ to per-tool
                   copies (.claude/skills/, .github/prompts/ for Copilot)
  lint             conformance + review-state audit (exit 1 on errors)
  lint --inbound P list files linking to bundle path P (safe-delete check)
  index            regenerate the bundle's index.md from tree + frontmatter
  links            expand [[slug]] shorthand into canonical bundle links
  log "MESSAGE"    prepend a log entry under today's date
  stats            counts by type/status, review queue
  migrate          drop the legacy `lifecycle` key (needs_review -> tag
                   needs-review); --dry-run lists the changes only
  drift            recheck pinned sources against their current git blob
  drift --hash F   print the blob sha to pin for file F

Every subcommand takes --bundle NAME to point at a differently-named
bundle directory. Without it the bundle is auto-detected (any top-level
directory holding a SCHEMA.md), falling back to the okf/ default.

The bundle targets OKF v0.2 and uses its standard `status` alone
(draft | stable | deprecated). The finer review states are derived, not
stored: a stable page *needs review* when it carries the `needs-review`
tag or its `stale_after` date has passed; a deprecated page is
*archived* when it lives under archive/. Bundles written before this
carried a five-state `lifecycle` extension key; `okf.py migrate` folds
it into `status` + tag, and lint warns until that is done.

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
# The toolchain's own version, as a date. Bump it on every change to this
# file: tools that ship a copy (e.g. a team-wiki plugin seeding hub repos)
# compare it to decide whether a repository's copy is out of date.
TOOLCHAIN_VERSION = "2026.11.23"
# OKF v0.2 defines `status` with exactly these three values; it is the
# only state field a page carries.
OKF_STATUSES = {"draft", "stable", "deprecated"}
# The persistent "re-check this" flag on a stable page (a contradiction
# found, a source changed). An overdue `stale_after` needs no flag.
REVIEW_TAG = "needs-review"
# The retired `lifecycle` extension key and the status each value maps to;
# read only to lint and migrate bundles written before it was dropped.
LEGACY_LIFECYCLE_STATUS = {"draft": "draft", "active": "stable",
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


def tags_of(meta):
    """A page's tags as a list of strings."""
    tags = meta.get("tags") or []
    if isinstance(tags, str):
        tags = [tags]
    return [str(t) for t in tags]


def review_due(meta, today):
    """Why a stable page is in the review queue, or None.

    The two signals that need no git: the `needs-review` tag (a person or
    agent flagged it) and an overdue `stale_after`. Pinned sources that
    moved are the third, reported by drift and lint separately.
    """
    if str(meta.get("status", "")).strip() != "stable":
        return None
    if REVIEW_TAG in tags_of(meta):
        return "tagged needs-review"
    sa = parse_date(meta.get("stale_after"))
    if sa and sa < today:
        return f"due {sa}"
    return None


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
              "'okf.py drift --hash <file>' — and tag the page needs-review "
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

        # review state — OKF v0.2 `status` alone; see review_due()
        status = str(meta.get("status", "")).strip()
        if status and status not in OKF_STATUSES:
            errors.append(f"{r}: status '{status}' is not an OKF v0.2 value "
                          f"({'|'.join(sorted(OKF_STATUSES))}) — flag a page "
                          f"for review with the '{REVIEW_TAG}' tag instead")
        if "lifecycle" in meta:
            life = str(meta.get("lifecycle") or "").strip()
            if life in LEGACY_LIFECYCLE_STATUS and status \
                    and LEGACY_LIFECYCLE_STATUS[life] != status:
                errors.append(f"{r}: legacy lifecycle '{life}' implies status "
                              f"'{LEGACY_LIFECYCLE_STATUS[life]}', found '{status}'")
            warns.append(f"{r}: legacy 'lifecycle' key — run 'okf.py migrate' "
                         f"to fold it into status (+ tag {REVIEW_TAG})")
        is_source = p.is_relative_to(KB / "sources")
        if p == KB / "SCHEMA.md":
            continue  # meta-file: OKF conformance applies, lifecycle rules don't

        if is_source:
            if not meta.get("source_url"):
                warns.append(f"{r}: source capture missing source_url")
            continue  # sources are exempt from the rest

        for field in ("title", "description", "status", "updated"):
            if not meta.get(field):
                warns.append(f"{r}: missing '{field}'")
        if meta.get("review_after"):
            warns.append(f"{r}: legacy 'review_after' — OKF v0.2 names this "
                         f"field 'stale_after'")
        archived = p.is_relative_to(KB / "archive")
        if status == "stable" and not meta.get("stale_after"):
            warns.append(f"{r}: stable but no stale_after")
        if status == "deprecated" and not archived and not meta.get("superseded_by") \
                and "## Deprecation" not in body:
            errors.append(f"{r}: deprecated without superseded_by or '## Deprecation' section")
        if archived and status and status != "deprecated":
            warns.append(f"{r}: under /archive/ but status is '{status}' — "
                         f"archived pages are 'deprecated'")

        sa = parse_date(meta.get("stale_after"))
        if status == "stable" and sa and sa < today and REVIEW_TAG not in tags_of(meta):
            warns.append(f"{r}: review overdue since {sa} — re-verify, or "
                         f"tag it {REVIEW_TAG} if it cannot be done now")

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
        # trust fields — validated only when present; a page without
        # them is not flagged, since an absent stamp is an honest
        # "nobody recorded this" and backfilling one would be worse.
        gen = meta.get("generated")
        if gen is not None:
            if not isinstance(gen, dict) or not gen.get("by") or not gen.get("at"):
                warns.append(f"{r}: 'generated' must be a mapping with "
                             f"'by' and 'at' (OKF v0.2)")
        ver = meta.get("verified")
        if ver is not None:
            events = ver if isinstance(ver, list) else [ver]
            for ev in events:
                if not isinstance(ev, dict) or not ev.get("by") or not ev.get("at"):
                    warns.append(f"{r}: 'verified' entries must be mappings "
                                 f"with 'by' and 'at' (OKF v0.2)")
                    break

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
        if status == "stable" and n_out < 2:
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
        status = str(meta.get("status") or "").strip()
        if top == "archive":
            badge = " *(archived)*"
        elif status == "deprecated":
            badge = " *(deprecated)*"
        elif status == "stable" and REVIEW_TAG in tags_of(meta):
            badge = " *(needs review)*"
        else:
            badge = ""
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
    by_type, by_status, queue = {}, {}, []
    today = date.today()
    files = concept_files()
    for p in files:
        meta, _, _ = load(p)
        meta = meta or {}
        by_type[str(meta.get("type", "?"))] = by_type.get(str(meta.get("type", "?")), 0) + 1
        status = str(meta.get("status", "?"))
        if p.is_relative_to(KB / "archive") and status == "deprecated":
            status = "deprecated (archived)"
        by_status[status] = by_status.get(status, 0) + 1
        why = review_due(meta, today)
        if why is not None:
            sa = parse_date(meta.get("stale_after"))
            queue.append((sa or date.min, rel(p), why))
    print(f"{len(files)} concept file(s)\n\nby type:")
    for k, v in sorted(by_type.items(), key=lambda kv: -kv[1]):
        print(f"  {k}: {v}")
    print("\nby status:")
    for k, v in sorted(by_status.items(), key=lambda kv: -kv[1]):
        print(f"  {k}: {v}")
    print(f"\nreview queue ({len(queue)}):")
    for _, r, why in sorted(queue):
        print(f"  {r} ({why})")
    results, git_ok = check_drift(files)
    if git_ok:
        stale = [x for x in results if x[2] != "ok"]
        print(f"\npinned sources: {len(results)} ({len(stale)} stale)")
    return 0


# ---------------------------------------------------------------- migrate

FM_RE = re.compile(r"^(\ufeff?---[ \t]*\r?\n)(.*?\r?\n)(---[ \t]*(?:\r?\n|$))", re.S)


def migrate_text(text):
    """Fold a page's legacy `lifecycle` key into `status` (+ tag).

    Edits the frontmatter as text so every other key, comment and
    ordering survives. Returns (new_text, note) or (text, None) when the
    page has no `lifecycle` key.
    """
    m = FM_RE.match(text)
    if not m:
        return text, None
    nl = "\r\n" if "\r\n" in m.group(2) else "\n"
    lines = m.group(2).splitlines()
    life_at = next((i for i, ln in enumerate(lines)
                    if re.match(r"^lifecycle\s*:", ln)), None)
    if life_at is None:
        return text, None
    life = re.sub(r"\s+#.*$", "", lines[life_at].split(":", 1)[1]).strip().strip("'\"")
    del lines[life_at]
    notes = [f"lifecycle {life or '(empty)'} dropped"]

    want = LEGACY_LIFECYCLE_STATUS.get(life)
    st_at = next((i for i, ln in enumerate(lines) if re.match(r"^status\s*:", ln)), None)
    if want is not None:
        if st_at is None:
            lines.insert(min(life_at, len(lines)), f"status: {want}")
            st_at = min(life_at, len(lines) - 1)
            notes.append(f"status: {want} added")
        else:
            cur = re.sub(r"\s+#.*$", "", lines[st_at].split(":", 1)[1]).strip().strip("'\"")
            if cur != want:
                lines[st_at] = f"status: {want}"
                notes.append(f"status {cur or '(empty)'} -> {want}")

    if life == "needs_review":
        tag_at = next((i for i, ln in enumerate(lines) if re.match(r"^tags\s*:", ln)), None)
        if tag_at is None:
            lines.insert((st_at if st_at is not None else len(lines) - 1) + 1,
                         f"tags: [{REVIEW_TAG}]")
        else:
            value = re.sub(r"\s+#.*$", "", lines[tag_at].split(":", 1)[1]).strip()
            if value.startswith("["):
                inner = value.strip("[]").strip()
                items = [t.strip() for t in inner.split(",") if t.strip()]
                if REVIEW_TAG not in [t.strip("'\"") for t in items]:
                    lines[tag_at] = f"tags: [{', '.join(items + [REVIEW_TAG])}]"
            elif value == "":
                block = tag_at + 1
                items, indent = [], "  "
                while block < len(lines) and re.match(r"^\s+-\s", lines[block]):
                    indent = re.match(r"^(\s+)-", lines[block]).group(1)
                    items.append(lines[block].split("-", 1)[1].strip().strip("'\""))
                    block += 1
                if REVIEW_TAG not in items:
                    lines.insert(block, f"{indent}- {REVIEW_TAG}")
            else:
                single = value.strip("'\"")
                if single != REVIEW_TAG:
                    lines[tag_at] = f"tags: [{single}, {REVIEW_TAG}]"
        notes.append(f"tag {REVIEW_TAG}")

    fm = nl.join(lines) + nl
    return m.group(1) + fm + m.group(3) + text[m.end():], ", ".join(notes)


def cmd_migrate(args):
    changed = []
    for p in concept_files():
        if p.is_relative_to(KB / "sources"):
            continue  # captures are immutable
        raw = p.read_bytes().decode("utf-8")
        new, note = migrate_text(raw)
        if note is None:
            continue
        changed.append((rel(p), note))
        if not args.dry_run:
            p.write_bytes(new.encode("utf-8"))
    for r, note in changed:
        print(f"{'would migrate' if args.dry_run else 'migrated'} {r}: {note}")
    print(f"\nmigrate: {len(changed)} page(s) "
          f"{'to change' if args.dry_run else 'changed'}")
    if changed and not args.dry_run:
        print("next: add 'needs-review' to SCHEMA.md's tag taxonomy if it is "
              "missing, drop lifecycle from its templates, then run index, "
              "log and lint")
    return 0


# ------------------------------------------------------------------- init

BUNDLE_DIRS = ["concepts", "entities", "comparisons", "queries",
               "archive", "sources"]

SCHEMA_SEED = """---
type: Schema
title: Bundle Schema & Conventions
description: Authoritative conventions for this OKF bundle — types, tags, frontmatter templates, review rules.
status: stable
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
confidence: medium       # low | medium | high
created: {today}
updated: {today}
stale_after: {today}     # required once status: stable
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
generated:               # who produced this content, stamped at write time
  by: agent/version      # actor: human:<id> | <tool>/<version> | process:<id>
  at: {today}
verified:                # append one entry per real re-verification
  - by: human:you        # only for a real check — never on freshly written text
    at: {today}
---
```

`status` (OKF v0.2) is the only state field: `draft` until verified,
`stable` once verified, `deprecated` when superseded (archived pages
are `deprecated` pages under `archive/`). A stable page needs review
when its `stale_after` has passed or it carries the `needs-review` tag
(a contradiction found, a source changed); `okf.py stats` lists them.

`generated` says what produced the page; `verified` says who confirmed
it. Stamp `generated` whenever you write, and `verified` only after a
real re-check — an agent verifying its own fresh output records nothing.

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
- `needs-review` — a stable page to re-check (contradiction found, source changed)
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
    ap.add_argument("--version", action="version",
                    version=f"okf.py {TOOLCHAIN_VERSION} (OKF {OKF_VERSION})")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", parents=[common])
    p = sub.add_parser("lint", parents=[common])
    p.add_argument("--inbound", metavar="PATH")
    sub.add_parser("index", parents=[common])
    sub.add_parser("links", parents=[common])
    p = sub.add_parser("log", parents=[common]);   p.add_argument("message")
    sub.add_parser("stats", parents=[common])
    p = sub.add_parser("migrate", parents=[common])
    p.add_argument("--dry-run", action="store_true",
                   help="list the pages that would change, write nothing")
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
            "drift": cmd_drift, "migrate": cmd_migrate}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
