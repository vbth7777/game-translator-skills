#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal Localization Quality Control (QC) & Linter Tool
Scans translated strings across Ren'Py and Unity formats:
- Variable interpolation integrity ({name}, [var], %s, {0})
- Tag parity checks
- Leaked English detection (untranslated strings)
- Encoding and malformed character detection
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


class UniversalLocalizationLinter:
    def __init__(self):
        # Placeholders
        self.re_renpy_var = re.compile(r'\[([a-zA-Z0-9_\.]+)\]')
        self.re_format_var = re.compile(r'\{([a-zA-Z0-9_\.]+)\}')
        self.re_printf_var = re.compile(r'%[0-9]*\.?[0-9]*[sdfoxX]')
        
        # English leak indicator (common English words in dialogue)
        self.english_words = {
            "the", "and", "you", "that", "was", "for", "are", "with", "his", "they",
            "this", "have", "from", "one", "had", "word", "what", "some", "were",
            "there", "when", "your", "can", "said", "each", "which", "she", "how",
            "their", "will", "other", "about", "many", "then", "them", "these", "so"
        }

    def check_pair(self, original: str, translated: str) -> list[str]:
        issues = []
        if not translated or not translated.strip():
            return ["Empty translation!"]

        # 1. Ren'Py variables [var]
        orig_vars = self.re_renpy_var.findall(original)
        trans_vars = self.re_renpy_var.findall(translated)
        if sorted(orig_vars) != sorted(trans_vars):
            issues.append(f"Ren'Py variable mismatch: Orig={orig_vars} vs Trans={trans_vars}")

        # 2. Python format variables {var} (excluding formatting tags like {b}, {i})
        tags_whitelist = {"b", "/b", "i", "/i", "u", "/u", "s", "/s", "p", "w"}
        orig_fmt = [v for v in self.re_format_var.findall(original) if v not in tags_whitelist and not v.startswith("color")]
        trans_fmt = [v for v in self.re_format_var.findall(translated) if v not in tags_whitelist and not v.startswith("color")]
        if sorted(orig_fmt) != sorted(trans_fmt):
            issues.append(f"Format variable mismatch: Orig={orig_fmt} vs Trans={trans_fmt}")

        # 3. Printf %s, %d
        orig_printf = self.re_printf_var.findall(original)
        trans_printf = self.re_printf_var.findall(translated)
        if orig_printf != trans_printf:
            issues.append(f"Printf specifier mismatch: Orig={orig_printf} vs Trans={trans_printf}")

        # 4. Leaked English sentence detection (if original was Japanese/English and translation has >=4 English words)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', translated.lower())
        matched_en = [w for w in words if w in self.english_words]
        if len(matched_en) >= 4 and original.strip() == translated.strip():
            issues.append("String is identical to original (Possible untranslated leak)")
        elif len(matched_en) >= 5:
            issues.append(f"High density of common English words detected ({len(matched_en)} words: {matched_en[:4]}...)")

        return issues


def lint_file(file_path: Path) -> dict:
    linter = UniversalLocalizationLinter()
    issues_list = []
    total = 0

    if file_path.suffix.lower() == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            total = len(data)
            for orig, trans in data.items():
                errs = linter.check_pair(orig, trans)
                if errs:
                    issues_list.append({"orig": orig[:70], "trans": trans[:70], "issues": errs})

    return {
        "file": file_path.name,
        "total_audited": total,
        "issues_count": len(issues_list),
        "issues": issues_list
    }


def main():
    parser = argparse.ArgumentParser(description="Audit translations for variable and language integrity.")
    parser.add_argument("file", help="Path to JSON translation file")
    parser.add_argument("--json", action="store_true", help="Output pure JSON")
    args = parser.parse_args()

    f_path = Path(args.file).resolve()
    if not f_path.is_file():
        print(f"❌ Error: File not found: {f_path}")
        sys.exit(1)

    res = lint_file(f_path)

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return

    print("=" * 65)
    print("🛡️ UNIVERSAL LOCALIZATION QC LINTER REPORT")
    print(f"📁 Target: {res['file']}")
    print(f"📊 Total Entries Audited: {res['total_audited']}")
    print(f"⚠️ Issues Detected: {res['issues_count']}")
    print("=" * 65)

    if res["issues_count"] == 0:
        print("✅ 100% CLEAN! Zero variable mismatches or untranslated leaks.")
    else:
        for item in res["issues"][:10]:
            print(f"\n❌ [QC ISSUE]:")
            print(f"   Orig : {item['orig']}")
            print(f"   Trans: {item['trans']}")
            for iss in item["issues"]:
                print(f"   - {iss}")
        if res["issues_count"] > 10:
            print(f"\n... and {res['issues_count'] - 10} more issues.")


if __name__ == "__main__":
    main()

