#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vietnamese Unicode Font Auditor & Tofu Detector
Scans TTF/OTF fonts for all 134 Vietnamese accented glyphs.
Prevents [?] (tofu box) rendering defects in Ren'Py and Unity games.
"""

import os
import sys
import argparse
from pathlib import Path

# Ensure utf-8 stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Full Vietnamese character set (lower + upper + diacritics)
VN_LOWER = "aáàảãạăắằẳẵặâấầẩẫậeéèẻẽẹêếềểễệiíìỉĩịoóòỏõọôốồổỗộơớờởỡợuúùủũụưứừửữựyýỳỷỹỵđ"
VN_FULL = VN_LOWER + VN_LOWER.upper()


def check_font_cmap(font_path: Path) -> dict:
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        return {
            "path": str(font_path),
            "status": "error",
            "message": "fonttools not installed. Run: pip install fonttools"
        }

    try:
        tt = TTFont(str(font_path))
        cmap = tt.getBestCmap() or {}
        missing = [ch for ch in VN_FULL if ord(ch) not in cmap]
        total_required = len(VN_FULL)
        present = total_required - len(missing)
        coverage_pct = (present / total_required) * 100

        return {
            "name": font_path.name,
            "path": str(font_path),
            "status": "pass" if len(missing) == 0 else "fail",
            "missing_count": len(missing),
            "missing_sample": "".join(missing[:15]),
            "coverage_percent": round(coverage_pct, 2)
        }
    except Exception as e:
        return {
            "name": font_path.name,
            "path": str(font_path),
            "status": "error",
            "message": str(e)
        }


def scan_directory(dir_path: Path) -> list[dict]:
    font_extensions = {".ttf", ".otf"}
    results = []
    for f in dir_path.rglob("*"):
        if f.is_file() and f.suffix.lower() in font_extensions:
            results.append(check_font_cmap(f))
    return results


def main():
    parser = argparse.ArgumentParser(description="Audit font files for complete Vietnamese Unicode diacritic support.")
    parser.add_argument("target", help="Font file or directory containing fonts")
    parser.add_argument("--json", action="store_true", help="Output pure JSON")
    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    if not target_path.exists():
        print(f"❌ Error: Path not found: {target_path}")
        sys.exit(1)

    if target_path.is_file():
        results = [check_font_cmap(target_path)]
    else:
        results = scan_directory(target_path)

    if args.json:
        import json
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    print("=" * 70)
    print("🔍 VIETNAMESE FONT UNICODE AUDIT REPORT")
    print(f"📁 Target: {target_path}")
    print(f"🔤 Total Vietnamese Glyphs Tested: {len(VN_FULL)}")
    print("=" * 70)

    pass_count = 0
    fail_count = 0

    for r in results:
        if r["status"] == "pass":
            pass_count += 1
            print(f"✅ [100% PASS] {r['name']} -> Full Vietnamese Unicode support!")
        elif r["status"] == "fail":
            fail_count += 1
            print(f"❌ [TOFU RISK] {r['name']} -> Missing {r['missing_count']} glyphs ({r['coverage_percent']}% coverage)")
            print(f"   Missing sample: {r['missing_sample']}...")
        else:
            print(f"⚠️ [ERROR] {r.get('name', 'Font')}: {r.get('message')}")

    print("-" * 70)
    print(f"📊 Summary: {pass_count} Passed | {fail_count} Failed (Tofu Risk)")
    if fail_count > 0:
        print("💡 Recommendation: Override failing fonts with Unicode-complete fonts (e.g. DejaVuSans, Segoe UI, OpenSans).")
    print("=" * 70)


if __name__ == "__main__":
    main()

