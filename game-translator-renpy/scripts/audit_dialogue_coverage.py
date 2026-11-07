#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ren'Py Comprehensive Dialogue & Translation Coverage Auditor
Compares original dialogue blocks (game/*.rpy) with translated blocks (game/tl/vietnamese/*.rpy)
Detects missing files, untranslated blocks, corrupted formatting, and computes 100% exact coverage.
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


def count_say_blocks_in_orig(rpy_path: Path) -> list[dict]:
    """Finds all dialogue say statements and menu choices in original .rpy file."""
    try:
        content = rpy_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    blocks = []
    lines = content.splitlines()
    re_say = re.compile(r'^\s*(?:([a-zA-Z0-9_]+)\s+)?["\']([^"\']{2,})["\']\s*$')
    re_choice = re.compile(r'^\s*["\']([^"\']+)["\']\s*:\s*$')

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m_say = re_say.match(line)
        if m_say:
            speaker = m_say.group(1) or ""
            text = m_say.group(2).strip()
            # Ignore code keywords
            if speaker not in ["define", "default", "image", "transform", "style", "python"]:
                blocks.append({"line": idx, "type": "say", "speaker": speaker, "text": text[:60]})
        elif re_choice.match(line):
            blocks.append({"line": idx, "type": "choice", "text": stripped[:60]})

    return blocks


def count_translated_blocks(tl_rpy_path: Path) -> list[dict]:
    """Finds all translate <language> blocks and string translations."""
    if not tl_rpy_path.is_file():
        return []

    try:
        content = tl_rpy_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    # Check for escaped single-line corruption (e.g. whole file on 1 line with literal \n)
    lines = content.splitlines()
    if len(lines) <= 2 and "\\n" in content and len(content) > 500:
        return [{"corrupted": True, "error": "File appears corrupted (single line with escaped literal \\n)"}]

    blocks = []
    re_tl_block = re.compile(r'^\s*translate\s+([a-zA-Z0-9_]+)\s+([a-zA-Z0-9_]+):', re.MULTILINE)
    re_tl_string = re.compile(r'^\s*old\s+["\']', re.MULTILINE)

    for m in re_tl_block.finditer(content):
        blocks.append({"type": "block", "label": m.group(2)})

    for m in re_tl_string.finditer(content):
        blocks.append({"type": "string"})

    return blocks


def audit_coverage(game_dir: Path, target_lang: str = "vietnamese") -> dict:
    game_path = game_dir / "game" if (game_dir / "game").is_dir() else game_dir
    tl_dir = game_path / "tl" / target_lang

    orig_files = [f for f in game_path.glob("*.rpy") if "tl" not in f.parts]
    report = {
        "game_path": str(game_path),
        "target_language": target_lang,
        "files": [],
        "total_orig_dialogues": 0,
        "total_translated_dialogues": 0,
        "overall_coverage_percent": 0.0,
        "corrupted_files": []
    }

    for orig in sorted(orig_files):
        # Ignore system configs
        if orig.name in ["options.rpy", "gui.rpy", "vietnamese_init.rpy", "language_toggle.rpy", "tl_bubbles_patch.rpy"]:
            continue

        tl_file = tl_dir / orig.name
        orig_dialogues = count_say_blocks_in_orig(orig)
        tl_blocks = count_translated_blocks(tl_file)

        is_corrupted = False
        if tl_blocks and tl_blocks[0].get("corrupted"):
            is_corrupted = True
            report["corrupted_files"].append(orig.name)
            tl_count = 0
        else:
            tl_count = len(tl_blocks)

        coverage = (tl_count / len(orig_dialogues) * 100) if orig_dialogues else 100.0

        report["total_orig_dialogues"] += len(orig_dialogues)
        report["total_translated_dialogues"] += tl_count

        report["files"].append({
            "name": orig.name,
            "orig_count": len(orig_dialogues),
            "tl_count": tl_count,
            "coverage_percent": round(coverage, 1),
            "tl_file_exists": tl_file.is_file(),
            "corrupted": is_corrupted
        })

    if report["total_orig_dialogues"] > 0:
        report["overall_coverage_percent"] = round(
            (report["total_translated_dialogues"] / report["total_orig_dialogues"]) * 100, 1
        )
    else:
        report["overall_coverage_percent"] = 100.0

    return report


def main():
    parser = argparse.ArgumentParser(description="Audit Ren'Py translation dialogue coverage.")
    parser.add_argument("game_dir", help="Path to Ren'Py game folder")
    parser.add_argument("--lang", default="vietnamese", help="Target language (default: vietnamese)")
    parser.add_argument("--json", action="store_true", help="Output pure JSON")
    args = parser.parse_args()

    target = Path(args.game_dir).resolve()
    if not target.exists():
        print(f"❌ Error: Not found: {target}")
        sys.exit(1)

    rep = audit_coverage(target, args.lang)

    if args.json:
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        return

    print("=" * 70)
    print(f"📊 REN'PY TRANSLATION COVERAGE AUDIT: {rep['target_language'].upper()}")
    print(f"📁 Game Directory: {rep['game_path']}")
    print("=" * 70)

    for f in rep["files"]:
        status_icon = "✅" if f["coverage_percent"] >= 95 else ("⚠️" if f["coverage_percent"] > 0 else "❌")
        if f["corrupted"]:
            status_icon = "💥 CORRUPTED FORMAT"
        print(f"{status_icon} {f['name']:25s} : {f['tl_count']:4d} / {f['orig_count']:4d} lines ({f['coverage_percent']}%)")

    print("-" * 70)
    print(f"🎯 TOTAL OVERALL COVERAGE: {rep['total_translated_dialogues']} / {rep['total_orig_dialogues']} lines ({rep['overall_coverage_percent']}%)")

    if rep["corrupted_files"]:
        print(f"\n🚨 WARNING: The following translation files are corrupted (escaped formatting):")
        for cf in rep["corrupted_files"]:
            print(f"   - {cf} (Requires unescaping newlines into multi-line Ren'Py code!)")

    print("=" * 70)


if __name__ == "__main__":
    main()

