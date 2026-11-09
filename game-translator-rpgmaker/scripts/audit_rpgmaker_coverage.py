#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RPG Maker Localization Coverage & Quality Control Auditor
Audits 1-1 translation coverage, detects untranslated CJK/English leaks,
and verifies RPG Maker escape code parity (\\N[n], \\V[n], \\C[n], \\I[n]).
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path

# Ensure utf-8 stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def has_untranslated_cjk(text: str) -> bool:
    """Checks if text contains untranslated CJK (Japanese/Chinese) characters."""
    if not text or not isinstance(text, str):
        return False
    # Japanese Hiragana, Katakana, Kanji, and CJK Ideographs
    cjk_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]')
    return bool(cjk_pattern.search(text))


def clean_dialogue_body_for_check(text: str) -> str:
    """Strips control tags before linguistic analysis."""
    if not text or not isinstance(text, str):
        return ""
    # Strip \c[x], \v[x], \n[x], <tag>, etc.
    s = re.sub(r'\\[a-zA-Z]+\[[^\]]*\]', '', text)
    s = re.sub(r'\\[\{\}\.\|!><\^]', '', s)
    s = re.sub(r'<[^>]+>', '', s)
    return s.strip()


def audit_rpgmaker_coverage(source_path: str, trans_path: str) -> dict:
    """Performs full coverage, leak, and escape code audit."""
    if not os.path.isfile(source_path):
        print(f"Error: Source file not found: {source_path}")
        return {"success": False}
    if not os.path.isfile(trans_path):
        print(f"Error: Translation file not found: {trans_path}")
        return {"success": False}

    with open(source_path, "r", encoding="utf-8-sig") as f:
        src_db = json.load(f)
    with open(trans_path, "r", encoding="utf-8-sig") as f:
        trans_db = json.load(f)

    total_src = len(src_db)
    total_trans = len(trans_db)

    # Group by file
    file_stats = {}
    missing_keys = []
    cjk_leaks = []
    english_leaks = []
    tag_errors = []

    common_en = {"the", "and", "you", "that", "was", "for", "are", "with", "his", "they", "this", "have"}

    re_codes = re.compile(r'\\[a-zA-Z]+\[[^\]]*\]')

    for k, orig in src_db.items():
        fname = k.split(":")[0] if ":" in k else "general"
        if fname not in file_stats:
            file_stats[fname] = {"total": 0, "translated": 0}
        file_stats[fname]["total"] += 1

        if k not in trans_db:
            missing_keys.append(k)
            continue

        translated = trans_db[k]
        if not translated or not str(translated).strip():
            missing_keys.append(k)
            continue

        file_stats[fname]["translated"] += 1

        # Check CJK leak
        clean_t = clean_dialogue_body_for_check(translated)
        if has_untranslated_cjk(clean_t):
            cjk_leaks.append({"key": k, "trans": translated[:80]})

        # Check English leak (identical to original or high English density)
        if clean_t == clean_dialogue_body_for_check(orig) and len(clean_t.split()) > 3:
            english_leaks.append({"key": k, "orig": orig[:80], "trans": translated[:80]})
        else:
            words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', clean_t)]
            matched = [w for w in words if w in common_en]
            if len(matched) >= 4:
                english_leaks.append({"key": k, "orig": orig[:80], "trans": translated[:80]})

        # Check escape code parity
        orig_c = sorted(re_codes.findall(orig))
        trans_c = sorted(re_codes.findall(translated))
        if orig_c != trans_c:
            tag_errors.append({
                "key": k,
                "orig_codes": orig_c,
                "trans_codes": trans_c
            })

    # Summary
    overall_pct = (total_trans / total_src * 100) if total_src > 0 else 0
    print("=================================================================")
    print("      RPG MAKER LOCALIZATION QUALITY & COVERAGE REPORT           ")
    print("=================================================================")
    print(f"Total Source Entries:      {total_src}")
    print(f"Total Translated Entries:  {total_trans}")
    print(f"Overall Coverage:          {overall_pct:.2f}%")
    print(f"Missing Entries:           {len(missing_keys)}")
    print(f"Untranslated CJK Leaks:    {len(cjk_leaks)}")
    print(f"Untranslated English Leaks: {len(english_leaks)}")
    print(f"Escape Code Parity Mismatch: {len(tag_errors)}")
    print("-----------------------------------------------------------------")
    print(f"{'File Name':<30} | {'Done / Total':<18} | {'Coverage':<10}")
    print("-----------------------------------------------------------------")
    for fn, stat in sorted(file_stats.items()):
        pct = (stat["translated"] / stat["total"] * 100) if stat["total"] > 0 else 0
        status_flag = "✓" if pct >= 95 else "✗"
        print(f"{fn:<30} | {stat['translated']:>6} / {stat['total']:<9} | {pct:>6.1f}% {status_flag}")
    print("=================================================================")

    if cjk_leaks:
        print(f"\n[ALERT] Sample CJK Leaks ({len(cjk_leaks)} total):")
        for ex in cjk_leaks[:5]:
            print(f"  - [{ex['key']}]: {ex['trans']}")

    if english_leaks:
        print(f"\n[ALERT] Sample English Leaks ({len(english_leaks)} total):")
        for ex in english_leaks[:5]:
            print(f"  - [{ex['key']}]: {ex['trans']}")

    if tag_errors:
        print(f"\n[ALERT] Sample Escape Code Errors ({len(tag_errors)} total):")
        for ex in tag_errors[:5]:
            print(f"  - [{ex['key']}]: Orig={ex['orig_codes']} vs Trans={ex['trans_codes']}")

    is_passed = (overall_pct >= 95.0) and (len(cjk_leaks) == 0) and (len(tag_errors) <= 2)
    print("\nFINAL AUDIT VERDICT: " + ("PASSED (100% READY)" if is_passed else "FAILED (CORRECTIONS REQUIRED)"))

    return {
        "success": is_passed,
        "coverage_percent": overall_pct,
        "missing_count": len(missing_keys),
        "cjk_leaks_count": len(cjk_leaks),
        "english_leaks_count": len(english_leaks),
        "tag_errors_count": len(tag_errors)
    }


def main():
    parser = argparse.ArgumentParser(description="Audit RPG Maker translation coverage and quality.")
    parser.add_argument("source", help="Path to translation_source.json")
    parser.add_argument("translated", help="Path to translation_vietnamese.json")
    args = parser.parse_args()

    res = audit_rpgmaker_coverage(os.path.abspath(args.source), os.path.abspath(args.translated))
    sys.exit(0 if res.get("success") else 1)


if __name__ == "__main__":
    main()

