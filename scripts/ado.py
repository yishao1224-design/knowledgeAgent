#!/usr/bin/env python3
"""ado.py — Azure DevOps work-item retrieval toolchain (stdlib only).

Python port of example/normalize-devops-story.mjs plus the retrieval and
staleness mechanics that previously lived in skill prose.

Subcommands:
  retrieve  --id N            fetch work item + comments + attachments into
                              <dest>/<US|BUG>_<id>_<slug>/raw/, normalized
  normalize --work-item-file F --raw-dir D
                              offline normalization of a saved payload
                              (byte-compatible with the JS normalizer when
                              --rev/--retrieved-at are not supplied)
  staleness FOLDER [--remote] compare analysis.md rev stamp vs raw rev
                              (and raw vs live ADO with --remote)
  stamp     FOLDER            print the rev-stamp line for analysis.md

Configuration (flag > environment):
  --org      / ADO_ORG_URL    e.g. https://dev.azure.com/yourorg
  --project  / ADO_PROJECT    e.g. CRM
  PAT: ADO_PAT or AZURE_DEVOPS_EXT_PAT (the same variable az uses)

Exit codes for staleness: 0 fresh; 1 analysis behind raw; 2 raw behind
remote; 3 both; 4 not determinable (missing stamps/rev).
"""

import argparse
import base64
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_VERSION = "7.1"
COMMENTS_API_VERSION = "7.1-preview.3"
UUID_RE = re.compile(r"^[0-9a-fA-F-]{36}$")
IMAGE_URL_PATTERN = re.compile(
    r"_apis/wit/attachments/([0-9a-fA-F-]{36})(?:\?fileName=([^\"'&>\s]+))?", re.I)
IMAGE_TAG_PATTERN = re.compile(r"<img[^>]*src=[\"']([^\"']+)[\"'][^>]*>", re.I)
REV_STAMP_RE = re.compile(r"ado-rev:\s*(\d+)")


# ---------------------------------------------------- normalization (JS port)

def decode_html(value):
    """Entity decoding in the exact order of the JS normalizer (including
    its double-decode of '&amp;lt;' -> '<'), so outputs stay comparable."""
    value = value.replace("&nbsp;", " ")
    value = value.replace("&amp;", "&")
    value = value.replace("&lt;", "<")
    value = value.replace("&gt;", ">")
    value = value.replace("&quot;", '"')
    value = value.replace("&#39;", "'")
    value = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), value)
    value = re.sub(r"&#x([0-9a-f]+);", lambda m: chr(int(m.group(1), 16)),
                   value, flags=re.I)
    return value


def sanitize_file_name(file_name):
    if not file_name:
        return "attachment.bin"
    return re.sub(r"[^A-Za-z0-9._-]", "_", file_name)


def slugify_label(label):
    slug = re.sub(r"[^a-z0-9]+", "_", label.lower())
    slug = re.sub(r"^_+|_+$", "", slug)
    return re.sub(r"_{2,}", "_", slug)


def read_assigned_to(value):
    if not value:
        return ""
    if isinstance(value, str):
        return value
    return value.get("displayName") or value.get("uniqueName") or ""


class AttachmentCollector:
    """Collects attachment references in first-seen order, preserving any
    'attachment analysis' values from a previous manifest across refreshes."""

    def __init__(self, previous_manifest, org_url=""):
        self.entries = {}
        self.previous = previous_manifest
        self.org_url = org_url.rstrip("/") if org_url else ""

    def _build_url(self, match_url, attachment_id, file_name):
        if match_url:
            return match_url
        base = self.org_url or "https://dev.azure.com/unknown-org"
        suffix = f"?fileName={urllib.parse.quote(file_name)}" if file_name else ""
        return f"{base}/_apis/wit/attachments/{attachment_id}{suffix}"

    def _record(self, attachment_id, file_name, source, source_type, url,
                suggested_local_file_name):
        if not attachment_id or attachment_id in self.entries:
            return
        previous = self.previous.get(attachment_id, {})
        analysis = previous.get("attachmentAnalysis",
                                previous.get("attachment analysis", ""))
        self.entries[attachment_id] = {
            "attachmentId": attachment_id,
            "fileName": file_name,
            "source": source,
            "sourceType": source_type,
            "url": url,
            "suggestedLocalFileName": suggested_local_file_name,
            "attachmentAnalysis": analysis,
        }

    def record_inline(self, url, source, source_type, file_prefix):
        match = IMAGE_URL_PATTERN.search(url)
        if not match:
            return None
        attachment_id = match.group(1)
        file_name = urllib.parse.unquote(match.group(2) or "image.png")
        suggested = (f"{slugify_label(file_prefix)}_{attachment_id[:8]}_"
                     f"{sanitize_file_name(file_name)}")
        self._record(attachment_id, file_name, source, source_type,
                     self._build_url(url, attachment_id, file_name), suggested)
        return attachment_id

    def record_attached_file(self, entry):
        attachment_id = entry.get("attachmentId")
        if not attachment_id:
            return
        name = entry.get("name") or entry.get("fileName") or "attachment.bin"
        self._record(
            attachment_id, name,
            entry.get("source") or "relation:AttachedFile", "attachedFile",
            self._build_url(entry.get("url"), attachment_id, name),
            sanitize_file_name(name))


def normalize_text(html, collector, source, file_prefix):
    if not html:
        return ""

    def replace_img(match):
        attachment_id = collector.record_inline(
            match.group(1), source, "inlineImage", file_prefix)
        if not attachment_id:
            return " "
        return f" [IMGID:{attachment_id}] "

    text = IMAGE_TAG_PATTERN.sub(replace_img, html)
    text = decode_html(text)
    text = re.sub(r"</(div|p|h1|h2|h3|h4|h5|h6|li|ul|ol|tr)>", "\n", text,
                  flags=re.I)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<li[^>]*>", "- ", text, flags=re.I)
    text = re.sub(r"<a [^>]*>", "", text, flags=re.I)
    text = re.sub(r"</a>", "", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\r", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_relation_attached_files(work_item):
    relations = work_item.get("relations")
    if not isinstance(relations, list):
        return []
    out = []
    for relation in relations:
        if relation.get("rel") != "AttachedFile":
            continue
        url = relation.get("url") or ""
        out.append({
            "attachmentId": url.rstrip("/").split("/")[-1] if url else None,
            "name": (relation.get("attributes") or {}).get("name"),
            "url": url,
            "source": "relation:AttachedFile",
        })
    return out


def extract_work_item_fields(work_item, bug_description_fallback=True):
    if "fields" in work_item:
        fields = work_item["fields"]
        description_html = fields.get("System.Description", "")
        work_item_type = fields.get("System.WorkItemType", "")
        if bug_description_fallback and work_item_type == "Bug":
            description_html = combine_bug_description(fields)
        return {
            "IterationPath": fields.get("System.IterationPath", ""),
            "State": fields.get("System.State", ""),
            "AssignedTo": read_assigned_to(fields.get("System.AssignedTo")),
            "Title": fields.get("System.Title", ""),
            "DescriptionHtml": description_html,
            "AcceptanceCriteriaHtml": fields.get(
                "Microsoft.VSTS.Common.AcceptanceCriteria", ""),
            "workItemId": work_item.get("id"),
        }
    return {
        "IterationPath": work_item.get("IterationPath",
                                       work_item.get("iterationPath", "")),
        "State": work_item.get("State", work_item.get("state", "")),
        "AssignedTo": work_item.get("AssignedTo",
                                    work_item.get("assignedTo", "")),
        "Title": work_item.get("Title", work_item.get("title", "")),
        "DescriptionHtml": work_item.get("descriptionHtml",
                                         work_item.get("Description", "")),
        "AcceptanceCriteriaHtml": work_item.get(
            "acceptanceCriteriaHtml", work_item.get("AcceptanceCriteria", "")),
        "workItemId": work_item.get("id", work_item.get("workItemId")),
    }


def combine_bug_description(fields):
    """Bugs often carry the defect narrative in SystemInfo/ReproSteps rather
    than System.Description; combine all non-empty parts, labeled."""
    parts = [
        ("System Info", fields.get("Microsoft.VSTS.TCM.SystemInfo", "")),
        ("Repro Steps", fields.get("Microsoft.VSTS.TCM.ReproSteps", "")),
        ("Description", fields.get("System.Description", "")),
    ]
    non_empty = [(label, html) for label, html in parts
                 if html and re.sub(r"<[^>]+>|&nbsp;|\s", "", html)]
    if len(non_empty) <= 1:
        return non_empty[0][1] if non_empty else ""
    return "".join(f"<div><b>{label}:</b></div>{html}<br>"
                   for label, html in non_empty)


def extract_comments(comments_source, work_item):
    if comments_source and isinstance(comments_source.get("comments"), list):
        return comments_source["comments"]
    legacy = work_item.get("Comment")
    if isinstance(legacy, list):
        return [{
            "id": comment.get("id", index),
            "createdDate": comment.get("CreatedDate"),
            "createdBy": {"displayName": comment.get("CreatedBy")},
            "text": comment.get("Text"),
        } for index, comment in enumerate(legacy)]
    return []


def read_previous_manifest(raw_dir, preserve):
    if not preserve:
        return {}
    try:
        previous = json.loads(
            (Path(raw_dir) / "attachments.json").read_text(encoding="utf-8"))
        return {entry["attachmentId"]: entry
                for entry in previous.get("attachments", [])
                if entry.get("attachmentId")}
    except (OSError, json.JSONDecodeError, KeyError):
        return {}


def dump_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")


def normalize_payload(work_item, comments_source, raw_dir, *,
                      preserve_existing_status=True, org_url="",
                      rev=None, retrieved_at=None):
    """Normalize a raw work-item payload into raw_dir/work-item.json and
    raw_dir/attachments.json. Returns the collector (for downloads)."""
    raw_dir = Path(raw_dir)
    previous = read_previous_manifest(raw_dir, preserve_existing_status)
    collector = AttachmentCollector(previous, org_url)
    fields = extract_work_item_fields(work_item)

    for entry in (work_item.get("attachedFiles")
                  if isinstance(work_item.get("attachedFiles"), list) else []):
        collector.record_attached_file(entry)
    for entry in extract_relation_attached_files(work_item):
        collector.record_attached_file(entry)

    description = normalize_text(fields["DescriptionHtml"], collector,
                                 "System.Description", "description")
    acceptance = normalize_text(
        fields["AcceptanceCriteriaHtml"], collector,
        "Microsoft.VSTS.Common.AcceptanceCriteria", "acceptance_criteria")
    comments = [{
        "CreatedDate": c.get("createdDate") or c.get("CreatedDate") or "",
        "CreatedBy": ((c.get("createdBy") or {}).get("displayName")
                      if isinstance(c.get("createdBy"), dict)
                      else c.get("createdBy")) or c.get("CreatedBy") or "",
        "Text": normalize_text(c.get("text") or c.get("Text") or "",
                               collector, f"comment:{c.get('id', i)}",
                               f"comment_{c.get('id', i)}"),
    } for i, c in enumerate(extract_comments(comments_source, work_item))]

    if rev is None:
        rev = work_item.get("rev", work_item.get("Rev"))

    output = {
        "IterationPath": fields["IterationPath"],
        "State": fields["State"],
        "AssignedTo": fields["AssignedTo"],
        "Title": fields["Title"],
    }
    if rev is not None:
        output["Rev"] = rev
    if retrieved_at is not None:
        output["RetrievedAt"] = retrieved_at
    output["Description"] = description
    output["AcceptanceCriteria"] = acceptance
    output["Comment"] = comments

    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "comments.json").unlink(missing_ok=True)
    dump_json(raw_dir / "work-item.json", output)
    dump_json(raw_dir / "attachments.json", {
        "workItemId": fields["workItemId"],
        "attachmentCount": len(collector.entries),
        "attachments": [{"attachmentId": e["attachmentId"],
                         "attachment analysis": e["attachmentAnalysis"]}
                        for e in collector.entries.values()],
    })
    return collector


# ----------------------------------------------------------------- REST bits

def resolve_config(args, need_project=True):
    org = (getattr(args, "org", None) or os.environ.get("ADO_ORG_URL", "")).rstrip("/")
    project = getattr(args, "project", None) or os.environ.get("ADO_PROJECT", "")
    pat = os.environ.get("ADO_PAT") or os.environ.get("AZURE_DEVOPS_EXT_PAT", "")
    missing = []
    if not org:
        missing.append("organization URL (--org or ADO_ORG_URL)")
    if need_project and not project:
        missing.append("project (--project or ADO_PROJECT)")
    if not pat:
        missing.append("PAT (ADO_PAT or AZURE_DEVOPS_EXT_PAT)")
    if missing:
        sys.exit("ERROR: missing configuration: " + "; ".join(missing))
    return org, project, pat


def ado_request(url, pat, binary=False):
    token = base64.b64encode(f":{pat}".encode()).decode()
    request = urllib.request.Request(url, headers={
        "Authorization": f"Basic {token}",
        "Accept": "application/octet-stream" if binary else "application/json",
    })
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()
    return data if binary else json.loads(data.decode("utf-8"))


def fetch_work_item(org, project, work_item_id, pat):
    url = (f"{org}/{urllib.parse.quote(project)}/_apis/wit/workitems/"
           f"{work_item_id}?$expand=all&api-version={API_VERSION}")
    return ado_request(url, pat)


def fetch_comments(org, project, work_item_id, pat):
    url = (f"{org}/{urllib.parse.quote(project)}/_apis/wit/workItems/"
           f"{work_item_id}/comments?api-version={COMMENTS_API_VERSION}")
    try:
        return ado_request(url, pat)
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f"WARN: could not fetch comments: {exc}")
        return {"comments": []}


def download_attachment(entry, raw_dir, pat):
    url = entry["url"]
    url += ("&" if "?" in url else "?") + f"download=true&api-version={API_VERSION}"
    target_dir = Path(raw_dir) / entry["attachmentId"]
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / sanitize_file_name(entry["fileName"])
    target.write_bytes(ado_request(url, pat, binary=True))
    return target


def prune_stale_attachment_dirs(raw_dir, current_ids):
    """Refresh idempotency: drop attachment-ID folders no longer referenced."""
    for child in Path(raw_dir).iterdir():
        if child.is_dir() and UUID_RE.match(child.name) \
                and child.name not in current_ids:
            shutil.rmtree(child)
            print(f"removed stale attachment folder {child.name}")


def work_item_folder(dest, prefix, work_item_id, title):
    slug = slugify_label(title)
    if len(slug) > 60 and "_" in slug[:60]:
        slug = slug[:60].rsplit("_", 1)[0]
    return Path(dest) / f"{prefix}_{work_item_id}_{slug}"


# ------------------------------------------------------------------ commands

def cmd_retrieve(args):
    org, project, pat = resolve_config(args)
    payload = fetch_work_item(org, project, args.id, pat)
    work_item_type = payload.get("fields", {}).get("System.WorkItemType", "")
    prefix = {"User Story": "US", "Bug": "BUG"}.get(work_item_type)
    if not prefix:
        sys.exit(f"ERROR: work item {args.id} is a '{work_item_type}', "
                 f"not a User Story or Bug")
    title = payload["fields"].get("System.Title", str(args.id))
    folder = work_item_folder(args.dest, prefix, args.id, title)
    raw_dir = folder / "raw"
    comments = fetch_comments(org, project, args.id, pat)
    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    collector = normalize_payload(
        payload, comments, raw_dir, org_url=org,
        rev=payload.get("rev"), retrieved_at=retrieved_at)

    if args.keep_payload:
        dump_json(raw_dir / "work-item-payload.json", payload)

    failures = []
    for entry in collector.entries.values():
        try:
            target = download_attachment(entry, raw_dir, pat)
            print(f"downloaded {entry['attachmentId']} -> {target.name}")
        except (urllib.error.URLError, OSError) as exc:
            failures.append(f"{entry['attachmentId']} ({entry['fileName']}): {exc}")
    prune_stale_attachment_dirs(raw_dir, set(collector.entries))

    print(f"\n{prefix} {args.id} rev {payload.get('rev')} "
          f"({work_item_type}, state {payload['fields'].get('System.State')})")
    print(f"folder: {folder}")
    print(f"attachments: {len(collector.entries)}, "
          f"comments: {len(comments.get('comments', []))}")
    for failure in failures:
        print(f"WARN: attachment download failed: {failure}")
    print("raw/ is ready for analysis"
          + (" (with warnings above)" if failures else ""))
    return 0


def cmd_normalize(args):
    work_item = json.loads(Path(args.work_item_file).read_text(encoding="utf-8"))
    comments = None
    if args.comments_file:
        comments = json.loads(Path(args.comments_file).read_text(encoding="utf-8"))
    normalize_payload(
        work_item, comments, args.raw_dir,
        preserve_existing_status=not args.no_preserve_existing_status,
        org_url=args.org or os.environ.get("ADO_ORG_URL", ""),
        rev=args.rev, retrieved_at=args.retrieved_at)
    print(f"Normalized Azure DevOps story payload into {args.raw_dir}.")
    return 0


def read_raw_rev(folder):
    try:
        data = json.loads((Path(folder) / "raw" / "work-item.json")
                          .read_text(encoding="utf-8"))
        return data.get("Rev")
    except (OSError, json.JSONDecodeError):
        return None


def cmd_staleness(args):
    folder = Path(args.folder)
    raw_rev = read_raw_rev(folder)
    if raw_rev is None:
        print("cannot determine: raw/work-item.json missing or has no Rev "
              "(re-run retrieve to stamp it)")
        return 4

    code = 0
    analysis = folder / "analysis.md"
    if analysis.exists():
        match = REV_STAMP_RE.search(analysis.read_text(encoding="utf-8",
                                                       errors="replace"))
        if not match:
            print("analysis.md exists but carries no 'ado-rev:' stamp "
                  "(add one via 'ado.py stamp')")
            code = 4
        elif int(match.group(1)) < int(raw_rev):
            print(f"STALE: analysis.md is based on rev {match.group(1)}, "
                  f"raw/ holds rev {raw_rev} — re-run the analysis")
            code = 1
        else:
            print(f"analysis.md rev {match.group(1)} matches raw rev {raw_rev}")
    else:
        print("no analysis.md yet — nothing to compare locally")

    if args.remote:
        org, project, pat = resolve_config(args)
        match = re.match(r"(?:US|BUG)_(\d+)_", folder.name)
        if not match:
            print(f"cannot parse work item id from folder name {folder.name}")
            return 4
        remote = fetch_work_item(org, project, int(match.group(1)), pat)
        remote_rev = remote.get("rev")
        if remote_rev is not None and int(remote_rev) > int(raw_rev):
            print(f"STALE: raw/ holds rev {raw_rev}, ADO is at rev "
                  f"{remote_rev} — re-run retrieve")
            code = 3 if code == 1 else 2
        else:
            print(f"raw rev {raw_rev} is current with ADO (rev {remote_rev})")

    if code == 0:
        print("fresh")
    return code


def cmd_stamp(args):
    folder = Path(args.folder)
    raw_rev = read_raw_rev(folder)
    if raw_rev is None:
        sys.exit("ERROR: raw/work-item.json missing or has no Rev")
    try:
        data = json.loads((folder / "raw" / "work-item.json")
                          .read_text(encoding="utf-8"))
        retrieved = data.get("RetrievedAt", "")
    except (OSError, json.JSONDecodeError):
        retrieved = ""
    print(f"<!-- ado-rev: {raw_rev} retrieved: {retrieved} -->")
    return 0


# ---------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("retrieve")
    p.add_argument("--id", type=int, required=True)
    p.add_argument("--org")
    p.add_argument("--project")
    p.add_argument("--dest", default="azure")
    p.add_argument("--keep-payload", action="store_true")

    p = sub.add_parser("normalize")
    p.add_argument("--work-item-file", required=True)
    p.add_argument("--comments-file")
    p.add_argument("--raw-dir", required=True)
    p.add_argument("--no-preserve-existing-status", action="store_true")
    p.add_argument("--org")
    p.add_argument("--rev", type=int)
    p.add_argument("--retrieved-at")

    p = sub.add_parser("staleness")
    p.add_argument("folder")
    p.add_argument("--remote", action="store_true")
    p.add_argument("--org")
    p.add_argument("--project")

    p = sub.add_parser("stamp")
    p.add_argument("folder")

    args = ap.parse_args()
    return {"retrieve": cmd_retrieve, "normalize": cmd_normalize,
            "staleness": cmd_staleness, "stamp": cmd_stamp}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
