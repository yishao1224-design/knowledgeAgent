#!/usr/bin/env python3
"""Tests for the normalization port in ado.py.

Locks the Python behavior to the semantics of
example/normalize-devops-story.mjs, including its quirks (entity-decode
ordering, decode-before-tag-strip, [IMGID] marker spacing, manifest
'attachment analysis' preservation across refreshes).

Run: python scripts/test_ado.py
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ado  # noqa: E402

ATT_DESC = "11111111-2222-3333-4444-555555555555"
ATT_REL = "99999999-8888-7777-6666-555555555555"
ATT_COMMENT = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def payload():
    return {
        "id": 4242,
        "rev": 7,
        "fields": {
            "System.WorkItemType": "User Story",
            "System.IterationPath": "CRM\\Team\\sprint.1",
            "System.State": "Active",
            "System.AssignedTo": {"displayName": "Jane Dev",
                                  "uniqueName": "jane@example.com"},
            "System.Title": "Fix the WOLI & make it read-only",
            "System.Description":
                '<div>Line one&nbsp;with &amp; entity</div>'
                '<img src="https://dev.azure.com/o/_apis/wit/attachments/'
                + ATT_DESC + '?fileName=shot%201.png">'
                '<ul><li>first</li><li>second</li></ul>',
            "Microsoft.VSTS.Common.AcceptanceCriteria":
                "<p>Given X<br>then <a href='https://x'>link text</a></p>",
        },
        "relations": [
            {"rel": "AttachedFile",
             "url": "https://dev.azure.com/o/_apis/wit/attachments/" + ATT_REL,
             "attributes": {"name": "spec doc.pdf"}},
            {"rel": "System.LinkTypes.Hierarchy-Reverse",
             "url": "https://dev.azure.com/o/_apis/wit/workItems/1"},
        ],
    }


def comments_payload():
    return {"comments": [
        {"id": 1, "createdDate": "2026-07-01T10:00:00Z",
         "createdBy": {"displayName": "PO Person"},
         "text": '<div>see <img src="/_apis/wit/attachments/'
                 + ATT_COMMENT + '?fileName=image.png"> above</div>'},
    ]}


class DecodeHtmlTests(unittest.TestCase):
    def test_basic_entities(self):
        self.assertEqual(ado.decode_html("a&nbsp;b &amp; c&#39;d &#65;&#x42;"),
                         "a b & c'd AB")

    def test_js_double_decode_quirk(self):
        # JS replaces &amp; before &lt;, so '&amp;lt;' decodes twice to '<'.
        self.assertEqual(ado.decode_html("&amp;lt;tag&amp;gt;"), "<tag>")


class NormalizeTextTests(unittest.TestCase):
    def norm(self, html, collector=None):
        collector = collector or ado.AttachmentCollector({}, "")
        return ado.normalize_text(html, collector, "src", "prefix")

    def test_decode_runs_before_tag_strip(self):
        # '&lt;div&gt;' decodes to '<div>' and is then stripped as a tag —
        # matches the JS pipeline order.
        self.assertEqual(self.norm("real &lt;div&gt; text"), "real text")

    def test_structure_conversion(self):
        # Only CLOSING block tags become newlines (JS pipeline); the double
        # newline after </ul></p> is kept — only 3+ collapse.
        out = self.norm("<div>a</div><ul><li>x</li><li>y</li></ul><p>b<br>c</p>")
        self.assertEqual(out, "a\n- x\n- y\n\nb\nc")

    def test_anchor_text_preserved_tag_dropped(self):
        self.assertEqual(self.norm("see <a href='u'>docs</a> now"),
                         "see docs now")

    def test_img_becomes_marker_and_records(self):
        collector = ado.AttachmentCollector({}, "")
        out = ado.normalize_text(
            '<div>x <img src="/_apis/wit/attachments/' + ATT_DESC
            + '?fileName=a.png"> y</div>', collector, "s", "p")
        self.assertEqual(out, f"x [IMGID:{ATT_DESC}] y")
        self.assertIn(ATT_DESC, collector.entries)

    def test_non_attachment_img_dropped(self):
        self.assertEqual(self.norm('a <img src="https://cdn/x.png"> b'), "a b")

    def test_whitespace_collapse(self):
        # 4 newlines collapse to exactly 2 (JS \n{3,} -> \n\n), not 1.
        self.assertEqual(self.norm("<div>a</div>\n\n\n<div>b</div>"), "a\n\nb")


class HelperTests(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(
            ado.slugify_label("Fix the WOLI & make it read-only"),
            "fix_the_woli_make_it_read_only")

    def test_sanitize_file_name(self):
        self.assertEqual(ado.sanitize_file_name("shot 1 (final).png"),
                         "shot_1__final_.png")
        self.assertEqual(ado.sanitize_file_name(""), "attachment.bin")

    def test_assigned_to_shapes(self):
        self.assertEqual(ado.read_assigned_to({"displayName": "A"}), "A")
        self.assertEqual(ado.read_assigned_to("plain"), "plain")
        self.assertEqual(ado.read_assigned_to(None), "")

    def test_folder_name(self):
        folder = ado.work_item_folder("azure", "US", 4242,
                                      "Fix the WOLI & make it read-only")
        self.assertEqual(folder.name, "US_4242_fix_the_woli_make_it_read_only")

    def test_bug_description_combination(self):
        fields = {"Microsoft.VSTS.TCM.SystemInfo": "<div>env</div>",
                  "Microsoft.VSTS.TCM.ReproSteps": "<div>steps</div>",
                  "System.Description": ""}
        combined = ado.combine_bug_description(fields)
        self.assertIn("System Info", combined)
        self.assertIn("steps", combined)
        # single non-empty part passes through unlabeled
        self.assertEqual(ado.combine_bug_description(
            {"System.Description": "<div>only</div>"}), "<div>only</div>")


class EndToEndNormalizeTests(unittest.TestCase):
    def normalize(self, tmp, **kwargs):
        raw = Path(tmp) / "raw"
        ado.normalize_payload(payload(), comments_payload(), raw, **kwargs)
        work_item = json.loads((raw / "work-item.json").read_text("utf-8"))
        manifest = json.loads((raw / "attachments.json").read_text("utf-8"))
        return raw, work_item, manifest

    def test_work_item_shape_and_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, wi, _ = self.normalize(tmp)
            self.assertEqual(
                list(wi), ["IterationPath", "State", "AssignedTo", "Title",
                           "Rev", "Description", "AcceptanceCriteria",
                           "Comment"])
            self.assertEqual(wi["Rev"], 7)  # auto-read from payload rev
            self.assertEqual(wi["AssignedTo"], "Jane Dev")
            # <ul> is an opening tag -> becomes a space, not a newline, so
            # the marker and first list item share a line (JS behavior).
            self.assertEqual(
                wi["Description"],
                f"Line one with & entity\n[IMGID:{ATT_DESC}] - first\n- second")
            self.assertEqual(wi["AcceptanceCriteria"],
                             "Given X\nthen link text")
            self.assertEqual(wi["Comment"][0]["CreatedBy"], "PO Person")
            self.assertEqual(wi["Comment"][0]["Text"],
                             f"see [IMGID:{ATT_COMMENT}] above")

    def test_rev_and_retrieved_at_stamping(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, wi, _ = self.normalize(tmp, rev=9,
                                      retrieved_at="2026-07-09T00:00:00+00:00")
            self.assertEqual(wi["Rev"], 9)
            self.assertEqual(wi["RetrievedAt"], "2026-07-09T00:00:00+00:00")

    def test_js_compatible_shape_without_stamps(self):
        # Without rev in payload or flags, output keys match the JS normalizer.
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw"
            source = payload()
            del source["rev"]
            ado.normalize_payload(source, comments_payload(), raw)
            wi = json.loads((raw / "work-item.json").read_text("utf-8"))
            self.assertEqual(
                list(wi), ["IterationPath", "State", "AssignedTo", "Title",
                           "Description", "AcceptanceCriteria", "Comment"])

    def test_manifest_order_and_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, manifest = self.normalize(tmp)
            self.assertEqual(manifest["workItemId"], 4242)
            self.assertEqual(manifest["attachmentCount"], 3)
            # relation attachments recorded before inline ones (JS main order)
            self.assertEqual(
                [e["attachmentId"] for e in manifest["attachments"]],
                [ATT_REL, ATT_DESC, ATT_COMMENT])
            self.assertEqual(list(manifest["attachments"][0]),
                             ["attachmentId", "attachment analysis"])

    def test_refresh_preserves_attachment_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw, _, _ = self.normalize(tmp)
            manifest = json.loads((raw / "attachments.json").read_text("utf-8"))
            manifest["attachments"][1]["attachment analysis"] = "analyze"
            (raw / "attachments.json").write_text(
                json.dumps(manifest), encoding="utf-8")
            ado.normalize_payload(payload(), comments_payload(), raw)
            refreshed = json.loads((raw / "attachments.json").read_text("utf-8"))
            self.assertEqual(refreshed["attachments"][1]["attachment analysis"],
                             "analyze")

    def test_refresh_removes_comments_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw"
            raw.mkdir(parents=True)
            (raw / "comments.json").write_text("{}", encoding="utf-8")
            ado.normalize_payload(payload(), comments_payload(), raw)
            self.assertFalse((raw / "comments.json").exists())


class StalenessTests(unittest.TestCase):
    def make_folder(self, tmp, raw_rev, analysis_rev=None):
        folder = Path(tmp) / "US_4242_slug"
        raw = folder / "raw"
        raw.mkdir(parents=True)
        (raw / "work-item.json").write_text(
            json.dumps({"Rev": raw_rev, "RetrievedAt": "t"}), encoding="utf-8")
        if analysis_rev is not None:
            (folder / "analysis.md").write_text(
                f"<!-- ado-rev: {analysis_rev} retrieved: t -->\n# x",
                encoding="utf-8")
        return folder

    def run_staleness(self, folder):
        class Args:
            remote = False
        args = Args()
        args.folder = str(folder)
        return ado.cmd_staleness(args)

    def test_fresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                self.run_staleness(self.make_folder(tmp, 7, 7)), 0)

    def test_analysis_behind_raw(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                self.run_staleness(self.make_folder(tmp, 9, 7)), 1)

    def test_no_analysis_is_fresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                self.run_staleness(self.make_folder(tmp, 7)), 0)

    def test_missing_rev_not_determinable(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "US_1_x"
            (folder / "raw").mkdir(parents=True)
            (folder / "raw" / "work-item.json").write_text("{}",
                                                           encoding="utf-8")
            self.assertEqual(self.run_staleness(folder), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
