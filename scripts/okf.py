#!/usr/bin/env python3
"""okf.py — mechanical toolchain for the OKF bundle in kb/.

Subcommands:
  init             bootstrap kb/ skeleton + sync skills/ into .claude/skills/
  lint             conformance + lifecycle audit (exit 1 on errors)
  lint --inbound P list files linking to bundle path P (safe-delete check)
  index            regenerate kb/index.md from the tree + frontmatter
  log "MESSAGE"    prepend a log entry under today's date
  stats            counts by type/status, review queue
  drift            verify sha256 of sources/ captures
  drift --hash F   print sha256 of a file's body (for new captures)

Stdlib only. Uses PyYAML if installed, else a minimal frontmatter parser
sufficient for the SCHEMA.md templates (scalars, inline lists, block lists).
"""

import argparse
import hashlib
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "kb"
RESERVED = {"index.md", "log.md"}
STATUSES = {"draft", "active", "needs_review", "deprecated", "archived"}
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
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


def parse_yaml_min(src):
    """Minimal YAML subset: 'key: value', inline [a, b] lists, block lists."""
    data, key = {}, None
    for line in src.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val == "":
                data[key] = []          # assume block list follows
            elif val.startswith("[") and val.endswith("]"):
                items = [v.strip().strip("'\"") for v in val[1:-1].split(",")]
                data[key] = [v for v in items if v]
            else:
                data[key] = val.split(" #")[0].strip().strip("'\"")
        elif re.match(r"^\s+-\s+", line) and key is not None:
            item = re.sub(r"^\s+-\s+", "", line).strip().strip("'\"")
            if isinstance(data.get(key), list):
                data[key].append(item)
    return data


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


def taxonomy():
    schema = KB / "SCHEMA.md"
    if not schema.exists():
        return None
    text = schema.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^#+\s*Tag taxonomy\s*$(.*?)(?=^#\s)", text, re.M | re.S)
    if not m:
        return None
    return set(TAG_DEF_RE.findall(m.group(1)))


def parse_date(s):
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


# ------------------------------------------------------------------- lint

def cmd_lint(args):
    errors, warns, infos = [], [], []
    files = concept_files()
    tags_known = taxonomy()
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
        if not str(meta.get("type", "")).strip():
            errors.append(f"{r}: frontmatter has no non-empty 'type' (OKF §9)")

        # lifecycle profile
        status = str(meta.get("status", "")).strip()
        if status and status not in STATUSES:
            errors.append(f"{r}: unknown status '{status}'")
        is_source = p.is_relative_to(KB / "sources")
        if p == KB / "SCHEMA.md":
            continue  # meta-file: OKF conformance applies, lifecycle rules don't

        if is_source:
            if not meta.get("sha256"):
                warns.append(f"{r}: source capture missing sha256 (drift check impossible)")
            if not meta.get("source_url"):
                warns.append(f"{r}: source capture missing source_url")
            continue  # sources are exempt from the rest

        for field in ("title", "description", "status", "updated"):
            if not meta.get(field):
                warns.append(f"{r}: missing '{field}'")
        if status == "active" and not meta.get("review_after"):
            warns.append(f"{r}: active but no review_after")
        if status == "deprecated" and not meta.get("superseded_by") \
                and "## Deprecation" not in body:
            errors.append(f"{r}: deprecated without superseded_by or '## Deprecation' section")
        if status == "archived" and not p.is_relative_to(KB / "archive"):
            warns.append(f"{r}: archived but not under /archive/")

        ra = parse_date(meta.get("review_after"))
        if status == "active" and ra and ra < today:
            warns.append(f"{r}: review overdue since {ra} — set status: needs_review or re-verify")

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
        if status in ("active", "needs_review") and n_out < 2:
            warns.append(f"{r}: only {n_out} outbound bundle link(s); minimum is 2")

        # orphan check (not linked from anywhere, incl. index)
        if p.resolve() not in inbound and p.name != "SCHEMA.md":
            warns.append(f"{r}: orphan — no inbound links and not in index.md "
                         f"(run 'okf.py index')")

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
        badge = f" *({status})*" if status in ("needs_review", "deprecated", "archived") else ""
        entries.setdefault(section, []).append(
            f"* [{title}]({p.relative_to(KB).as_posix()}) - {desc}{badge}")

    total = sum(len(v) for v in entries.values())
    lines = ['---', 'okf_version: "0.1"', '---', '', '# Bundle Index', '']
    for e in sorted(entries.pop("_root", [])):
        lines.append(e)
    order = SECTION_ORDER + sorted(set(entries) - set(SECTION_ORDER))
    for sec in order:
        if sec not in entries:
            continue
        lines += ["", f"# {sec.capitalize()}", ""]
        lines += sorted(entries[sec])
    (KB / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"index.md regenerated: {total} entries")
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
    logf.write_text(text, encoding="utf-8")
    n = text.count("\n* ") + text.count("\n*\t")
    print(f"logged under {heading} ({n} entries total)")
    if n > 500:
        print("WARN: log.md exceeds 500 entries — rotate old years to kb/archive/log-YYYY.md")
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
        st = str(meta.get("status", "?"))
        by_status[st] = by_status.get(st, 0) + 1
        ra = parse_date(meta.get("review_after"))
        if st == "needs_review" or (st == "active" and ra and ra < today):
            queue.append((ra or date.min, rel(p)))
    print(f"{len(files)} concept file(s)\n\nby type:")
    for k, v in sorted(by_type.items(), key=lambda kv: -kv[1]):
        print(f"  {k}: {v}")
    print("\nby status:")
    for k, v in sorted(by_status.items(), key=lambda kv: -kv[1]):
        print(f"  {k}: {v}")
    print(f"\nreview queue ({len(queue)}):")
    for ra, r in sorted(queue):
        print(f"  {r}" + (f" (due {ra})" if ra != date.min else ""))
    return 0


# ------------------------------------------------------------------ drift

def body_hash(path):
    _, body, _ = load(path)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def cmd_drift(args):
    if args.hash:
        print(body_hash(Path(args.hash)))
        return 0
    src_dir = KB / "sources"
    bad = 0
    files = sorted(src_dir.rglob("*.md")) if src_dir.exists() else []
    for p in files:
        if p.name in RESERVED:
            continue
        meta, _, _ = load(p)
        recorded = (meta or {}).get("sha256", "")
        actual = body_hash(p)
        if not recorded:
            print(f"WARN: {rel(p)}: no sha256 recorded (actual: {actual})")
        elif recorded != actual:
            print(f"DRIFT: {rel(p)}: body changed since ingestion "
                  f"(recorded {recorded[:12]}…, actual {actual[:12]}…)")
            bad += 1
    print(f"drift: {bad} drifted of {len(files)} source(s)")
    return 1 if bad else 0


# ------------------------------------------------------------------- init

BUNDLE_DIRS = ["concepts", "entities", "comparisons", "queries",
               "archive", "sources"]

SCHEMA_SEED = """---
type: Schema
title: Bundle Schema & Conventions
description: Authoritative conventions for this OKF bundle — types, tags, frontmatter templates, lifecycle rules.
status: active
updated: {today}
---

# Bundle Schema & Conventions

*(Starter schema written by `okf.py init`. Flesh out the Domain, type
registry, and tag taxonomy on first real ingestion — see the full
template in the knowledgeAgent repo's kb/SCHEMA.md.)*

# Domain

*(one paragraph: what this knowledge base covers and for whom)*

# Concept frontmatter template

```yaml
---
type: Concept
title: Human Readable Title
description: One sentence for index/previews.
status: draft            # draft | active | needs_review | deprecated | archived
confidence: medium       # low | medium | high
created: {today}
updated: {today}
review_after: {today}    # required once active; set per cadence
tags: []
sources: []
---
```

# Tag taxonomy

- `unverified` — claims not yet checked against a second source
- `contested` — sources actively disagree
"""

LOG_SEED = """# Bundle Update Log

## {today}
* **Initialization**: Bundle skeleton created by `okf.py init`.
"""


def cmd_init(args):
    import shutil
    made = []

    # 1 — bundle skeleton
    for d in BUNDLE_DIRS:
        p = KB / d
        if not p.exists():
            p.mkdir(parents=True)
            made.append(f"kb/{d}/")
    today = date.today().isoformat()
    seeds = {
        KB / "SCHEMA.md": SCHEMA_SEED.format(today=today),
        KB / "log.md": LOG_SEED.format(today=today),
    }
    for path, content in seeds.items():
        if not path.exists():
            path.write_text(content, encoding="utf-8")
            made.append(f"kb/{path.name}")

    # 2 — sync canonical skills/ into .claude/skills/ (discovery path)
    src = ROOT / "skills"
    dst = ROOT / ".claude" / "skills"
    synced = []
    if src.exists():
        for skill_dir in sorted(src.iterdir()):
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                shutil.copytree(skill_dir, dst / skill_dir.name,
                                dirs_exist_ok=True)
                synced.append(skill_dir.name)

    # 3 — regenerate index and report health
    cmd_index(args)
    for m in made:
        print(f"created {m}")
    print(f"synced {len(synced)} skill(s) to .claude/skills/: "
          f"{', '.join(synced) or '(none found)'}")
    print("\nhealth check:")
    return cmd_lint(argparse.Namespace(inbound=None))


# ------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    p = sub.add_parser("lint");  p.add_argument("--inbound", metavar="PATH")
    sub.add_parser("index")
    p = sub.add_parser("log");   p.add_argument("message")
    sub.add_parser("stats")
    p = sub.add_parser("drift"); p.add_argument("--hash", metavar="FILE")
    args = ap.parse_args()
    if args.cmd == "init":
        KB.mkdir(exist_ok=True)
    elif not KB.exists():
        print(f"ERROR: bundle not found at {KB} — run 'okf.py init'",
              file=sys.stderr)
        return 2
    return {"init": cmd_init, "lint": cmd_lint, "index": cmd_index,
            "log": cmd_log, "stats": cmd_stats, "drift": cmd_drift}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
