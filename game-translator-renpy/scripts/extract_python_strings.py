#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ren'Py Python Dictionaries, Screen UI & Hidden String Extractor
Extracts translatable text that standard `renpy translate` ignores:
- Python dictionaries in `init python:` (e.g. Live2D dialogue, minigames)
- Screen text elements (`text "..."`, `textbutton "..."`)
- Notifications (`renpy.notify(...)`, `long_notify(...)`)
- Menu choice options (`menu:` blocks)
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


class RenpyStringScanner:
    def __init__(self):
        # Patterns
        self.re_screen_text = re.compile(r'^\s*(?:text|textbutton)\s+["\']([^"\']+)["\']', re.MULTILINE)
        self.re_notify = re.compile(r'(?:renpy\.notify|long_notify|add_notification)\s*\(\s*["\']([^"\']+)["\']', re.MULTILINE)
        self.re_menu_choice = re.compile(r'^\s*["\']([^"\']+)["\']\s*:\s*$', re.MULTILINE)
        self.re_dict_str_val = re.compile(r'["\']([A-Za-z0-9_\-\.\s]{2,100})["\']\s*:\s*["\']([^"\']+)["\']')
        self.re_list_str_item = re.compile(r'^\s*["\']([A-Z0-9a-z][^"\']{3,})["\']\s*,?\s*(?:#.*)?$', re.MULTILINE)
        self.re_tuple_step = re.compile(r'\(\s*["\'][a-zA-Z0-9_]+["\']\s*,\s*["\']([^"\']{3,})["\']\s*\)')
        self.re_dialogue_say = re.compile(r'^\s*(?:([a-zA-Z0-9_]+)\s+)?["\']([^"\']{2,})["\']\s*$', re.MULTILINE)

    def is_translatable(self, text: str) -> bool:
        """Filter out code, file paths, variables, colors, or pure symbols."""
        s = text.strip()
        if len(s) < 2:
            return False
        # Filter color codes, extensions, python identifiers
        if s.startswith("#") and (len(s) == 4 or len(s) == 7 or len(s) == 9):
            return False
        if any(s.endswith(ext) for ext in [".png", ".jpg", ".webp", ".rpy", ".rpyc", ".mp3", ".ogg", ".wav", ".ttf", ".otf"]):
            return False
        if re.match(r'^[a-zA-Z0-9_]+$', s) and (" " not in s) and (s.islower() or s.isupper()):
            return False
        if re.match(r'^[0-9\.\,\:\;\-\_\+\*\/\=\%\$\#\@\!]+$', s):
            return False
        return True

    def scan_file(self, file_path: Path) -> dict[str, list[dict]]:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return {}

        results = {
            "screen_buttons": [],
            "notifications": [],
            "menu_choices": [],
            "dictionary_entries": [],
            "dialogue": []
        }

        # 1. Screen texts & buttons
        for match in self.re_screen_text.finditer(content):
            t = match.group(1).strip()
            if self.is_translatable(t):
                results["screen_buttons"].append({"text": t, "file": file_path.name})

        # 2. Notifications
        for match in self.re_notify.finditer(content):
            t = match.group(1).strip()
            if self.is_translatable(t):
                results["notifications"].append({"text": t, "file": file_path.name})

        # 3. Menu choices
        for match in self.re_menu_choice.finditer(content):
            t = match.group(1).strip()
            if self.is_translatable(t):
                results["menu_choices"].append({"text": t, "file": file_path.name})

        # 4. Dict entries
        for match in self.re_dict_str_val.finditer(content):
            k, v = match.group(1).strip(), match.group(2).strip()
            if self.is_translatable(k) and self.is_translatable(v):
                results["dictionary_entries"].append({"key": k, "value": v, "file": file_path.name})

        # 5. List items and Speech Bubble arrays (in python/init blocks)
        for match in self.re_list_str_item.finditer(content):
            t = match.group(1).strip()
            if self.is_translatable(t):
                results["dictionary_entries"].append({"key": t, "value": t, "file": file_path.name})

        # 6. Tuple steps (e.g. ("speech", "text..."))
        for match in self.re_tuple_step.finditer(content):
            t = match.group(1).strip()
            if self.is_translatable(t):
                results["dictionary_entries"].append({"key": t, "value": t, "file": file_path.name})

        # 7. Dialogue says
        for match in self.re_dialogue_say.finditer(content):
            speaker = match.group(1) or ""
            text = match.group(2).strip()
            if self.is_translatable(text) and not text.startswith("$") and not text.startswith("define"):
                results["dialogue"].append({"speaker": speaker, "text": text, "file": file_path.name})

        return results


def main():
    parser = argparse.ArgumentParser(description="Extract hidden translatable strings from Ren'Py files.")
    parser.add_argument("target", help="Folder or .rpy file to scan")
    parser.add_argument("--out", "-o", default="renpy_extracted_strings.json", help="Output JSON file")
    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    if not target_path.exists():
        print(f"❌ Error: Target not found: {target_path}")
        sys.exit(1)

    scanner = RenpyStringScanner()
    files = [target_path] if target_path.is_file() else list(target_path.rglob("*.rpy"))

    aggregated = {
        "screen_buttons": set(),
        "notifications": set(),
        "menu_choices": set(),
        "dictionary_strings": set(),
        "dialogue_count": 0
    }
    unique_all = set()

    for f in files:
        # Skip translation folders themselves
        if "tl" in f.parts:
            continue
        res = scanner.scan_file(f)
        for item in res["screen_buttons"]:
            aggregated["screen_buttons"].add(item["text"])
            unique_all.add(item["text"])
        for item in res["notifications"]:
            aggregated["notifications"].add(item["text"])
            unique_all.add(item["text"])
        for item in res["menu_choices"]:
            aggregated["menu_choices"].add(item["text"])
            unique_all.add(item["text"])
        for item in res["dictionary_entries"]:
            aggregated["dictionary_strings"].add(item["key"])
            aggregated["dictionary_strings"].add(item["value"])
            unique_all.add(item["key"])
            unique_all.add(item["value"])
        aggregated["dialogue_count"] += len(res["dialogue"])

    summary = {
        "total_unique_ui_strings": len(unique_all),
        "screen_buttons_count": len(aggregated["screen_buttons"]),
        "notifications_count": len(aggregated["notifications"]),
        "menu_choices_count": len(aggregated["menu_choices"]),
        "dictionary_strings_count": len(aggregated["dictionary_strings"]),
        "dialogue_entries_detected": aggregated["dialogue_count"],
        "strings": sorted(list(unique_all))
    }

    out_file = Path(args.out).resolve()
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("=" * 60)
    print(f"📊 REN'PY STRING EXTRACTION COMPLETE")
    print(f"📁 Target Scanned: {target_path}")
    print(f"📄 Files Scanned: {len(files)}")
    print(f"🔘 Screen/UI Buttons: {summary['screen_buttons_count']}")
    print(f"🔔 Notifications: {summary['notifications_count']}")
    print(f"📋 Menu Choices: {summary['menu_choices_count']}")
    print(f"📚 Dictionary Strings: {summary['dictionary_strings_count']}")
    print(f"💬 Estimated Dialogue Lines: {summary['dialogue_entries_detected']}")
    print(f"🎯 Total Unique Non-Dialogue Strings: {summary['total_unique_ui_strings']}")
    print(f"💾 Output Saved: {out_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()

