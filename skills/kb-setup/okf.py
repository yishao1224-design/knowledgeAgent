#!/usr/bin/env python3
"""okf.py — mechanical toolchain for an OKF bundle (default: okf/).

Subcommands:
  init             bootstrap the bundle skeleton + sync skills/ to per-tool
                   copies (.claude/skills/, .github/prompts/ for Copilot)
  lint             conformance + lifecycle audit (exit 1 on errors)
  lint --inbound P list files linking to bundle path P (safe-delete check)
  index            regenerate the bundle's index.md from tree + frontmatter
  links            expand [[slug]] shorthand into canonical bundle links
  init --project P add project scope P (its own SCHEMA.md, index.md, log.md)
  log "MESSAGE"    prepend a log entry under today's date
  stats            counts by type/lifecycle/project, review queue
  drift            recheck pinned sources against their current git blob
                   (repo files, and code repos named in SCHEMA.md tables)
  drift --hash F   print the blob sha to pin for file F, or for REPO:PATH

Every subcommand takes --bundle NAME to point at a differently-named
bundle directory. Without it the bundle is auto-detected (any top-level
directory holding a SCHEMA.md), falling back to the okf/ default.

Projects: any directory inside the bundle that holds its own SCHEMA.md is
a project scope. Its pages follow that SCHEMA.md's type registry, tags and
code-repository table (plus the root's non-negotiable rules); `index`
writes one index.md per scope, and `log`/`stats`/`drift` take --project P.
A bundle without project SCHEMA.md files behaves exactly as before.

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


def resolve_wikilink(target, by_key, from_file=None):
    """Resolve a [[target]] to (Path, status), status in
    {ok, ambiguous, missing}. A target containing '/' or ending '.md' is
    treated as an explicit bundle path; otherwise it is matched by stem
    or title (case-insensitive). When several pages match, one in the
    linking page's own scope (project) wins; otherwise it is ambiguous."""
    t = target.strip()
    if t.startswith("/") or "/" in t or t.lower().endswith(".md"):
        cand = (KB / t.lstrip("/")).resolve()
        return (cand, "ok") if cand.exists() else (None, "missing")
    hits = by_key.get(t.lower(), [])
    if len(hits) == 1:
        return hits[0], "ok"
    if len(hits) > 1 and from_file is not None:
        home = scope_of(from_file)
        local = [h for h in hits if scope_of(h) == home]
        if len(local) == 1:
            return local[0], "ok"
    if len(hits) > 1:
        return None, "ambiguous"
    return None, "missing"


# ---------------------------------------------------------------- scopes
#
# A *scope* is a directory carrying its own SCHEMA.md: the bundle root
# (team-wide rules) plus any project directory below it. Every page belongs
# to the nearest scope above it, and that scope's SCHEMA.md supplies its
# type registry, tag taxonomy and code-repository table; the root SCHEMA.md
# keeps the rules no scope may loosen. A bundle with no project SCHEMA.md
# is a single root scope — exactly the pre-scope behaviour.

def scope_of(path):
    """The scope directory a bundle path belongs to (nearest ancestor
    holding a SCHEMA.md), falling back to the bundle root."""
    d = path.parent
    while d != KB and KB in d.parents:
        if (d / "SCHEMA.md").is_file():
            return d
        d = d.parent
    return KB


def scope_dirs():
    """Every scope: the bundle root first, then each project by path."""
    subs = sorted(p.parent for p in KB.rglob("SCHEMA.md") if p.parent != KB)
    return [KB] + subs


def scope_label(scope):
    """'' for the bundle root, else the bundle-relative project path."""
    return "" if scope == KB else scope.relative_to(KB).as_posix()


def under(path, scope):
    """True when path lies inside scope (nested projects included)."""
    return scope == KB or scope in path.parents


def project_scope(name):
    """Resolve a --project NAME to its scope directory, or exit."""
    if not name:
        return KB
    scope = (KB / name.strip("/")).resolve()
    if KB.resolve() not in scope.parents or not (scope / "SCHEMA.md").is_file():
        print(f"ERROR: no project '{name}' — a project is a directory under "
              f"{KB.name}/ holding its own SCHEMA.md (create one with "
              f"'okf.py init --project {name}')", file=sys.stderr)
        raise SystemExit(2)
    return KB / scope.relative_to(KB.resolve())


_SCHEMA_CACHE = {}


def schema_section(scope, heading):
    """Body of the `# <heading>` section of scope/SCHEMA.md (up to the next
    H1 or end of file), or None when the file or the section is absent."""
    schema = scope / "SCHEMA.md"
    if schema not in _SCHEMA_CACHE:
        _SCHEMA_CACHE[schema] = (schema.read_text(encoding="utf-8", errors="replace")
                                 if schema.exists() else None)
    text = _SCHEMA_CACHE[schema]
    if text is None:
        return None
    m = re.search(rf"^#+\s*{heading}\s*$(.*?)(?=^#\s|\Z)", text, re.M | re.S | re.I)
    return m.group(1) if m else None


def table_rows(section):
    """Data rows of the first markdown table in a section, as stripped cell
    lists (header and separator rows dropped, backticks removed)."""
    rows = []
    for line in (section or "").splitlines():
        line = line.strip()
        if not line.startswith("|"):
            if rows:
                break
            continue
        cells = [c.strip().strip("`").strip() for c in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        rows.append(cells)
    return rows[1:]  # first row is the header


def taxonomy(scope=None):
    """Tags a page in `scope` may use: the root taxonomy plus the scope's
    own. None when neither SCHEMA.md declares one (tags then unchecked)."""
    scope = scope or KB
    found = None
    for s in ([KB] if scope == KB else [KB, scope]):
        sec = schema_section(s, "Tag taxonomy")
        if sec is not None:
            found = (found or set()) | set(TAG_DEF_RE.findall(sec))
    return found


def type_registry(scope=None):
    """Parse a scope's 'Type registry' table into {type: dir relative to
    the scope} ('' = scope root). Types are NOT inherited from the root:
    each project names its own. None if the scope declares no registry."""
    sec = schema_section(scope or KB, "Type registry")
    if sec is None:
        return None
    reg = {}
    for cells in table_rows(sec):
        if len(cells) < 2 or not cells[0]:
            continue
        where = cells[1].strip("`").strip().rstrip("/")
        reg[cells[0]] = "" if where in ("root", "") else where
    return reg or None


def code_repos(scope):
    """{name: {url, branch}} from the 'Code repositories' table of the scope
    and its ancestors — a project's own entry wins over a team-wide one."""
    chain = [scope] + [p for p in scope.parents
                       if p == KB or KB in p.parents]   # scope … up to KB
    repos = {}
    for s in reversed(chain):
        for cells in table_rows(schema_section(s, "Code repositories")):
            if len(cells) >= 2 and cells[0] and cells[1]:
                repos[cells[0]] = {"url": cells[1],
                                   "branch": cells[2] if len(cells) > 2 else ""}
    return repos


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


REPO_CACHE = ROOT / ".okf-cache" / "repos"


def _git(*args, cwd=None, timeout=300):
    import subprocess
    try:
        out = subprocess.run(["git", *args], cwd=str(cwd) if cwd else None,
                             capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)
    return out.returncode, (out.stdout.strip() if out.returncode == 0
                            else out.stderr.strip())


class RemoteRepos:
    """Blob lookups in code repositories that live outside this repo.

    A source entry `{repo: NAME, path: P, blob: SHA}` names a repository
    from a SCHEMA.md 'Code repositories' table. Each is kept as a bare,
    blob-less, depth-1 clone under .okf-cache/repos/ — trees only, so even
    a large repo costs little — and `<branch>:<path>` is resolved with
    rev-parse. The blob sha is git's own, so this works the same against
    GitHub, Azure DevOps, GitLab or a local path. With fetch=False (lint)
    only an existing cache is consulted: lint never touches the network.
    """

    def __init__(self, fetch):
        self.fetch = fetch
        self.ready = {}    # cache dir -> (ref or None, error or None)

    def _dir(self, name, spec):
        import hashlib
        key = hashlib.sha1(f"{spec['url']}#{spec['branch']}".encode()).hexdigest()[:8]
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
        return REPO_CACHE / f"{safe}-{key}"

    def _prepare(self, name, spec):
        d = self._dir(name, spec)
        if d in self.ready:
            return d, self.ready[d]
        ref, err = None, None
        if self.fetch:
            if not d.exists():
                d.parent.mkdir(parents=True, exist_ok=True)
                args = ["clone", "--quiet", "--bare", "--depth=1",
                        "--filter=blob:none"]
                if spec["branch"]:
                    args += ["--branch", spec["branch"]]
                rc, msg = _git(*args, spec["url"], str(d))
                if rc != 0:
                    err = f"clone failed: {msg.splitlines()[-1] if msg else rc}"
            else:
                rc, head = _git("symbolic-ref", "HEAD", cwd=d)
                branch = spec["branch"] or (head.rsplit("/", 1)[-1] if rc == 0 else "HEAD")
                rc, msg = _git("fetch", "--quiet", "--depth=1", "--filter=blob:none",
                               "origin", f"+refs/heads/{branch}:refs/heads/{branch}", cwd=d)
                if rc != 0:
                    err = f"fetch failed: {msg.splitlines()[-1] if msg else rc}"
        if err is None:
            if not d.exists():
                err = "not fetched yet — run 'okf.py drift'"
            else:
                ref = f"refs/heads/{spec['branch']}" if spec["branch"] else "HEAD"
        self.ready[d] = (ref, err)
        return d, (ref, err)

    def blob(self, name, spec, path):
        """(sha or None, error or None); sha None + no error = path gone."""
        d, (ref, err) = self._prepare(name, spec)
        if err:
            return None, err
        rc, out = _git("rev-parse", "--verify", "--quiet",
                       f"{ref}:{path.lstrip('/')}", cwd=d)
        return (out, None) if rc == 0 and out else (None, None)


def check_drift(files, fetch=False):
    """Compare each pinned source entry's `blob:` against the file's current
    blob sha. Returns (results, git_available); results are tuples of
    (page, resource, state, pinned, current), state in
    ok|moved|gone|unchecked (unchecked: a remote repo that could not be
    reached, or is not fetched yet — `current` then carries the reason)."""
    results = []
    if git_blob(Path(__file__)) is None:
        return results, False
    remote = RemoteRepos(fetch)
    for p in files:
        meta, _, _ = load(p)
        entries = (meta or {}).get("sources") or []
        if isinstance(entries, str):
            entries = [entries]
        for entry in entries:
            if not isinstance(entry, dict) or not entry.get("blob"):
                continue
            pinned = str(entry["blob"]).strip()
            if entry.get("repo"):
                name = str(entry["repo"]).strip()
                path = str(entry.get("path", "")).strip()
                res = f"{name}:{path}"
                spec = code_repos(scope_of(p)).get(name)
                if spec is None or not path:
                    continue  # reported by lint as a malformed entry
                cur, err = remote.blob(name, spec, path)
                if err:
                    results.append((rel(p), res, "unchecked", pinned, err))
                elif cur is None:
                    results.append((rel(p), res, "gone", pinned, None))
                else:
                    state = "ok" if cur.startswith(pinned) else "moved"
                    results.append((rel(p), res, state, pinned, cur))
                continue
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
    scope = project_scope(getattr(args, "project", None))
    if args.hash:
        target = args.hash
        if not Path(target).exists() and ":" in target:
            name, path = target.split(":", 1)
            spec = code_repos(scope).get(name)
            if spec is None:
                print(f"ERROR: repo '{name}' is not in the Code repositories "
                      f"table of {rel(scope / 'SCHEMA.md')} or the root "
                      f"SCHEMA.md", file=sys.stderr)
                return 2
            h, err = RemoteRepos(fetch=not args.offline).blob(name, spec, path)
            if h is None:
                print(f"ERROR: cannot hash {target}: {err or 'no such path'}",
                      file=sys.stderr)
                return 2
        else:
            h = git_blob(Path(target))
        if h is None:
            print(f"ERROR: cannot hash {target}", file=sys.stderr)
            return 2
        print(h[:12])
        return 0
    files = [p for p in concept_files() if under(p, scope)]
    results, git_ok = check_drift(files, fetch=not args.offline)
    if not git_ok:
        print("drift: git unavailable — no pinned source checked")
        return 0
    stale = [x for x in results if x[2] in ("moved", "gone")]
    unchecked = [x for x in results if x[2] == "unchecked"]
    for page, res, state, pinned, cur in results:
        if state == "gone":
            print(f"GONE:  {page} -> {res} (pinned {pinned}; file is missing)")
        elif state == "moved":
            print(f"MOVED: {page} -> {res} (pinned {pinned}, now {cur[:12]})")
        elif state == "unchecked":
            print(f"SKIP:  {page} -> {res} ({cur})")
    print(f"\ndrift: {len(stale)} stale of {len(results)} pinned source(s)"
          + (f", {len(unchecked)} unchecked" if unchecked else ""))
    if stale:
        print("re-verify each page against its file, then restamp with "
              "'okf.py drift --hash <file>' (or '--hash <repo>:<path> "
              "--project <p>') — and set lifecycle: needs_review "
              "if the claims themselves moved")
    return 1 if stale else 0


# ------------------------------------------------------------------- lint

def cmd_lint(args):
    errors, warns, infos = [], [], []
    files = concept_files()
    scopes = scope_dirs()
    tags_by_scope = {s: taxonomy(s) for s in scopes}
    types_by_scope = {s: type_registry(s) for s in scopes}
    repos_by_scope = {s: code_repos(s) for s in scopes}
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
        scope = scope_of(p)
        types_known = types_by_scope[scope]
        tags_known = tags_by_scope[scope]
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
        elif types_known is not None and not (p.name == "SCHEMA.md"
                                              and p.parent == scope):
            schema_r = rel(scope / "SCHEMA.md")
            rel_dir = p.parent.relative_to(scope).as_posix()
            rel_dir = "" if rel_dir == "." else rel_dir
            home = types_known.get(typ)
            if typ not in types_known:
                warns.append(f"{r}: type '{typ}' not in {schema_r} type "
                             f"registry — add it there before first use")
            elif rel_dir.split("/")[0] != "archive" and not (
                    rel_dir == home or (home and rel_dir.startswith(home + "/"))):
                base = "" if scope == KB else rel(scope)
                expected = f"{base}/{home}/" if home else (
                    f"{base}/" if base else "the bundle root")
                errors.append(f"{r}: type '{typ}' belongs in {expected} "
                              f"per {schema_r} type registry")

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
        is_source = p.is_relative_to(scope / "sources")
        if p.name == "SCHEMA.md" and p.parent == scope:
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
        if life == "archived" and not p.is_relative_to(scope / "archive"):
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
            if entry.get("repo"):
                name = str(entry["repo"]).strip()
                if not str(entry.get("path", "")).strip():
                    errors.append(f"{r}: source entry pins repo '{name}' "
                                  f"without 'path'")
                elif name not in repos_by_scope[scope]:
                    errors.append(f"{r}: repo '{name}' is not in the Code "
                                  f"repositories table of "
                                  f"{rel(scope / 'SCHEMA.md')} (or the root's)")
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
                    warns.append(f"{r}: tag '{t}' not in "
                                 f"{rel(scope / 'SCHEMA.md')} taxonomy")

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
            _, st = resolve_wikilink(tgt, by_key, p)
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
            warns.append(f"{r}: orphan — no inbound links and not in its "
                         f"index.md (run 'okf.py index')")

    # pinned-source drift (skipped silently when git is unavailable)
    for page, res, state, pinned, cur in check_drift(files)[0]:
        if state == "moved":
            warns.append(f"{page}: pinned source {res} changed since "
                         f"{pinned} — run 'okf.py drift' and re-verify")
        elif state == "gone":
            warns.append(f"{page}: pinned source {res} no longer exists")
        elif state == "unchecked":
            infos.append(f"{page}: pinned source {res} not checked ({cur})")

    # every project scope keeps its own catalog and history (OKF §8/§9
    # allow index.md and log.md at any level)
    for s in scopes[1:]:
        for fname, fix in (("index.md", "okf.py index"),
                           ("log.md", f"okf.py log --project {scope_label(s)} ...")):
            if not (s / fname).is_file():
                warns.append(f"{rel(s)}/: project has no {fname} (run '{fix}')")

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

def _section_order(scope, sections):
    """Index sections in type-registry order, then any other directory
    alphabetically, with sources/ and archive/ always last."""
    tail = ["sources", "archive"]
    reg = [d.split("/")[0] for d in (type_registry(scope) or {}).values() if d]
    head = [d for d in dict.fromkeys(reg) if d in sections and d not in tail]
    rest = sorted(set(sections) - set(head) - set(tail))
    return head + rest + [d for d in tail if d in sections]


def _scope_title(scope):
    meta, _, _ = load(scope / "SCHEMA.md")
    return str((meta or {}).get("description") or "").strip()


def write_scope_index(scope, files, scopes):
    """Write scope/index.md: the scope's own pages grouped by top-level
    directory, plus a 'Projects' section linking each directly nested
    project's own index. Only the bundle root carries frontmatter."""
    entries = {}
    for p in files:
        if scope_of(p) != scope:
            continue  # belongs to a nested project, which indexes itself
        meta, _, _ = load(p)
        meta = meta or {}
        relp = p.relative_to(scope)
        top = relp.parts[0]
        section = top if len(relp.parts) > 1 else "_root"
        title = meta.get("title") or p.stem
        desc = str(meta.get("description") or "").strip()
        life = str(meta.get("lifecycle") or "").strip()
        badge = f" *({life})*" if life in ("needs_review", "deprecated", "archived") else ""
        entries.setdefault(section, []).append(
            f"* [{title}]({relp.as_posix()}) - {desc}{badge}")

    children = [c for c in scopes if c != scope and scope_of(c) == scope]
    total = sum(len(v) for v in entries.values())
    if scope == KB:
        lines = ['---', f'okf_version: "{OKF_VERSION}"', '---', '',
                 '# Bundle Index', '']
    else:
        lines = [f"# {scope_label(scope)} Index", ""]
    for e in sorted(entries.pop("_root", [])):
        lines.append(e)
    if children:
        lines += ["", "# Projects", ""]
        for c in children:
            name = c.relative_to(scope).as_posix()
            lines.append(f"* [{name}]({name}/index.md) - {_scope_title(c)}")
    for sec in _section_order(scope, entries):
        lines += ["", f"# {sec.capitalize()}", ""]
        lines += sorted(entries[sec])
    (scope / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8",
                                    newline="\n")
    return total


def cmd_index(args):
    files = concept_files()
    scopes = scope_dirs()
    for scope in scopes:
        n = write_scope_index(scope, files, scopes)
        where = "index.md" if scope == KB else f"{scope_label(scope)}/index.md"
        print(f"{where} regenerated: {n} entries")
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
            path, st = resolve_wikilink(target, by_key, p)
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
    scope = project_scope(getattr(args, "project", None))
    logf = scope / "log.md"
    heading_1 = ("# Bundle Update Log" if scope == KB
                 else f"# {scope_label(scope)} Update Log")
    text = logf.read_text(encoding="utf-8") if logf.exists() else heading_1 + "\n"
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
    where = "log.md" if scope == KB else f"{scope_label(scope)}/log.md"
    print(f"logged to {where} under {heading} ({n} entries total)")
    if n > 500:
        print(f"WARN: {where} exceeds 500 entries — rotate old years to "
              f"{(scope / 'archive').relative_to(KB.parent).as_posix()}/log-YYYY.md")
    return 0


# ------------------------------------------------------------------ stats

def cmd_stats(args):
    by_type, by_life, by_scope, queue = {}, {}, {}, []
    today = date.today()
    scope = project_scope(getattr(args, "project", None))
    files = [p for p in concept_files() if under(p, scope)]
    for p in files:
        meta, _, _ = load(p)
        meta = meta or {}
        label = scope_label(scope_of(p)) or "(root)"
        by_scope[label] = by_scope.get(label, 0) + 1
        by_type[str(meta.get("type", "?"))] = by_type.get(str(meta.get("type", "?")), 0) + 1
        life = str(meta.get("lifecycle", "?"))
        by_life[life] = by_life.get(life, 0) + 1
        sa = parse_date(meta.get("stale_after"))
        if life == "needs_review" or (life == "active" and sa and sa < today):
            queue.append((sa or date.min, rel(p)))
    print(f"{len(files)} concept file(s)\n\nby type:")
    for k, v in sorted(by_type.items(), key=lambda kv: -kv[1]):
        print(f"  {k}: {v}")
    if len(by_scope) > 1:
        print("\nby project:")
        for k, v in sorted(by_scope.items()):
            print(f"  {k}: {v}")
    print("\nby lifecycle:")
    for k, v in sorted(by_life.items(), key=lambda kv: -kv[1]):
        print(f"  {k}: {v}")
    print(f"\nreview queue ({len(queue)}):")
    for sa, r in sorted(queue):
        print(f"  {r}" + (f" (due {sa})" if sa != date.min else ""))
    results, git_ok = check_drift(files)
    if git_ok:
        stale = [x for x in results if x[2] in ("moved", "gone")]
        unchecked = [x for x in results if x[2] == "unchecked"]
        print(f"\npinned sources: {len(results)} ({len(stale)} stale"
              + (f", {len(unchecked)} unchecked" if unchecked else "") + ")")
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
generated:               # who produced this content, stamped at write time
  by: agent/version      # actor: human:<id> | <tool>/<version> | process:<id>
  at: {today}
verified:                # append one entry per real re-verification
  - by: human:you        # only for a real check — never on freshly written text
    at: {today}
---
```

`status` is the OKF v0.2 standard field; `lifecycle` is this bundle's
five-state extension and `status` is derived from it (`active` and
`needs_review` are both `stable`; `archived` is `deprecated`). Lint
errors if the two disagree.

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
"""

LOG_SEED = """# Bundle Update Log

## {today}
* **Initialization**: Bundle skeleton created by `okf.py init`.
"""

PROJECT_SCHEMA_SEED = """---
type: Schema
title: {name} — Project Schema
description: (one sentence on what the {name} project is — shown in the parent index)
status: stable
lifecycle: active
updated: {today}
---

# {name} — Project Schema

*(Written by `okf.py init --project {name}`.)* This file governs every
page under `{name}/`. The **bundle-root `SCHEMA.md` still applies**:
its frontmatter, lifecycle, source-immutability, linking and logging
rules hold here and cannot be loosened — this file may only add to
them or tighten them. What it owns outright: the project's types and
directory layout, its tags, its code repositories and its cadence.

# Project

*(What this project is, who owns it, who reads this knowledge.)*

# Type registry

This project's **own** types — names are not inherited from the root
and need not match other projects' (OKF registers no types centrally).
Rename, drop or add rows freely; say in `meaning` what each is, since
agents comparing projects map types by meaning. Lint enforces this
table for pages under `{name}/`: an unlisted `type` is a warning, a
listed one outside its directory is an error (`archive/` is exempt).

| type | lives in | meaning |
|------|----------|---------|
| `Concept` | `concepts/` | An idea, definition, method, or explanation |
| `Entity` | `entities/` | A concrete nameable thing (service, system, team, dataset) |
| `Decision` | `decisions/` | A decision taken and why |
| `Query` | `queries/` | A filed answer to a real question |
| `Source` | `sources/` | Immutable raw capture |

# Tag taxonomy

Tags this project adds; the root taxonomy is usable here too.

- `{name}` — belongs to the {name} project (optional; the path already says so)

# Code repositories

Code this project's pages pin as evidence. A `sources` entry names a
row with `repo:` plus `path:` and `blob:` (from
`okf.py drift --hash <repo>:<path> --project {name}`); `okf.py drift`
re-checks it against the branch below. `url` is any git URL or path
the machine running drift can clone; blank `branch` = default branch.

| repo | url | branch |
|------|-----|--------|

# Review cadence

*(Optional: project-specific `stale_after` defaults, e.g. "Decision
pages: 12 months". Without this section the root table applies.)*
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


def init_project(args):
    name = args.project.strip("/")
    if not (KB / "SCHEMA.md").is_file():
        print(f"ERROR: no bundle at {KB} — run 'okf.py init' first, then add "
              f"projects", file=sys.stderr)
        return 2
    if not re.fullmatch(r"[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*", name) \
            or ".." in name.split("/"):
        print(f"ERROR: bad project name '{args.project}'", file=sys.stderr)
        return 2
    scope = KB / name
    today = date.today().isoformat()
    label = name.rsplit("/", 1)[-1]
    made = []
    for d in (scope, scope / "sources"):
        if not d.exists():
            d.mkdir(parents=True)
            made.append(f"{d.relative_to(KB.parent).as_posix()}/")
    seeds = {
        scope / "SCHEMA.md": PROJECT_SCHEMA_SEED.format(name=label, today=today),
        scope / "log.md": (f"# {name} Update Log\n\n## {today}\n"
                           f"* **Initialization**: Project scope created by "
                           f"`okf.py init --project {name}`.\n"),
    }
    for path, content in seeds.items():
        if not path.exists():
            path.write_text(content, encoding="utf-8", newline="\n")
            made.append(path.relative_to(KB.parent).as_posix())
    _SCHEMA_CACHE.clear()
    cmd_index(args)
    for m in made:
        print(f"created {m}")
    if not made:
        print(f"project '{name}' already exists — nothing created")
    print("\nhealth check:")
    return cmd_lint(argparse.Namespace(inbound=None))


def cmd_init(args):
    import shutil
    if getattr(args, "project", None):
        return init_project(args)
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
    # --project picks a project scope: a directory under the bundle holding
    # its own SCHEMA.md (see the scopes section above)
    proj = argparse.ArgumentParser(add_help=False)
    proj.add_argument("--project", metavar="NAME",
                      help="project directory under the bundle "
                           "(default: the whole bundle / its root)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", parents=[common, proj])
    p = sub.add_parser("lint", parents=[common])
    p.add_argument("--inbound", metavar="PATH")
    sub.add_parser("index", parents=[common])
    sub.add_parser("links", parents=[common])
    p = sub.add_parser("log", parents=[common, proj]); p.add_argument("message")
    sub.add_parser("stats", parents=[common, proj])
    p = sub.add_parser("drift", parents=[common, proj])
    p.add_argument("--hash", metavar="FILE",
                   help="print the blob sha to pin for FILE (or REPO:PATH, a "
                        "repo from a Code repositories table) and exit")
    p.add_argument("--offline", action="store_true",
                   help="do not fetch code repositories; use the cache only")
    args = ap.parse_args()
    resolve_bundle(args)
    if args.cmd == "init" and not getattr(args, "project", None):
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
