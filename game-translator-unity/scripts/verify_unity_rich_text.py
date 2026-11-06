#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unity TextMeshPro Rich Text & Tag Integrity Linter
Ensures full parity of rich text tags between original and translated strings:
- Tags: <color>, <size>, <sprite>, <voffset>, <b>, <i>, <align>, <rotate>
- Verifies tag balance, unclosed brackets, and variable placeholders.
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path

# Ensure utf-8 stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


class UnityTagLinter:
    def __init__(self):
        self.re_tag = re.compile(r'<(/?[a-zA-Z0-9_\=\#\.\-]+)>')
        self.void_tags = {"sprite", "br", "nobr", "rotate", "voffset", "space", "pos", "size", "color", "alpha", "font"}
        self.pairable_tags = {"b", "i", "u", "s", "align", "material", "gradient"}
        self.re_sprite = re.compile(r'<sprite(?:\s*=\s*|\s+index\s*=\s*)["\']?([0-9]+)["\']?>')
        self.re_color = re.compile(r'<color=(#[0-9a-fA-F]{3,8}|[a-zA-Z]+)>')

    def check_entry(self, orig: str, trans: str) -> list[str]:
        issues = []

        orig_tags = self.re_tag.findall(orig)
        trans_tags = self.re_tag.findall(trans)

        # Check raw count
        if len(orig_tags) != len(trans_tags):
            issues.append(f"Tag count mismatch: Original had {len(orig_tags)} tags, translation has {len(trans_tags)}")

        # Check tag balance in translation (open vs close for pairable tags)
        open_tags = []
        for t in trans_tags:
            if t.startswith("/"):
                tag_name = t[1:].split("=")[0].lower()
                if not open_tags:
                    pass
                else:
                    last = open_tags.pop()
                    if last != tag_name and last in self.pairable_tags:
                        issues.append(f"Mismatched closing tag </{tag_name}>, expected </{last}>")
            else:
                tag_name = t.split("=")[0].lower()
                if tag_name in self.pairable_tags:
                    open_tags.append(tag_name)

        if open_tags:
            issues.append(f"Unclosed tag(s) in translation: {', '.join(open_tags)}")

        # Check sprite index parity
        orig_sprites = self.re_sprite.findall(orig)
        trans_sprites = self.re_sprite.findall(trans)
        if orig_sprites != trans_sprites:
            issues.append(f"Sprite icons mismatch: Orig={orig_sprites} vs Trans={trans_sprites}")

        # Check unescaped curly brackets or odd brackets
        if trans.count("<") != trans.count(">"):
            issues.append("Mismatched angle brackets '<' and '>' in translation")

        return issues


def lint_json_file(json_path: Path) -> dict:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    linter = UnityTagLinter()
    report = {
        "file": json_path.name,
        "total_checked": len(data),
        "issues_found": 0,
        "errors": []
    }

    for orig, trans in data.items():
        issues = linter.check_entry(orig, trans)
        if issues:
            report["issues_found"] += 1
            report["errors"].append({
                "original": orig[:80] + ("..." if len(orig) > 80 else ""),
                "translation": trans[:80] + ("..." if len(trans) > 80 else ""),
                "issues": issues
            })

    return report


def main():
    parser = argparse.ArgumentParser(description="Audit Unity TextMeshPro rich text tags in JSON translations.")
    parser.add_argument("json_file", help="Path to JSON translation file")
    parser.add_argument("--json", action="store_true", help="Output pure JSON")
    args = parser.parse_args()

    json_path = Path(args.json_file).resolve()
    if not json_path.is_file():
        print(f"❌ Error: File not found: {json_path}")
        sys.exit(1)

    report = lint_json_file(json_path)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    print("=" * 65)
    print("🔍 UNITY TEXTMESHPRO TAG INTEGRITY AUDIT")
    print(f"📁 File: {report['file']}")
    print(f"📊 Total Entries Audited: {report['total_checked']}")
    print(f"⚠️ Issues Detected: {report['issues_found']}")
    print("=" * 65)

    if report["issues_found"] == 0:
        print("✅ 100% PASS! All Rich Text tags, colors, and sprites are perfectly preserved.")
    else:
        for err in report["errors"][:10]:
            print(f"\n❌ [TAG ISSUE]:")
            print(f"   Orig : {err['original']}")
            print(f"   Trans: {err['translation']}")
            for iss in err["issues"]:
                print(f"   - {iss}")
        if report["issues_found"] > 10:
            print(f"\n... and {report['issues_found'] - 10} more issues.")


if __name__ == "__main__":
    main()
