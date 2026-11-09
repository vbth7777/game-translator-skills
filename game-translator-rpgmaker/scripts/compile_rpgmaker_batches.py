#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RPG Maker Batch Compiler
Merges individual subagent-translated batch files into a unified translation_vietnamese.json.
Supports multiple batch input conventions (batch_XXX_translated.json, batch_XXX.json with translation field, etc.).
"""

import os
import sys
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


def compile_batches(batches_dir: str, source_path: str = None, out_file: str = None) -> dict:
    """Merges all translated batch files into a single dictionary."""
    if not os.path.isdir(batches_dir):
        print(f"Error: Batches directory not found: {batches_dir}")
        return {}

    all_translations = {}
    batch_files = sorted([f for f in os.listdir(batches_dir) if f.endswith('.json')])

    translated_count = 0
    total_batches = 0

    for fname in batch_files:
        fpath = os.path.join(batches_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8-sig") as f:
                data = json.load(f)

            # Case A: Translated map directly { "Key": "Translated" }
            if isinstance(data, dict) and "items" not in data and "batch_id" not in data:
                total_batches += 1
                for k, v in data.items():
                    if isinstance(v, str) and v.strip():
                        all_translations[k] = v
                        translated_count += 1

            # Case B: Batch structure with items array
            elif isinstance(data, dict) and "items" in data:
                total_batches += 1
                for it in data["items"]:
                    k = it.get("key")
                    t = it.get("translated")
                    if k and isinstance(t, str) and t.strip():
                        all_translations[k] = t
                        translated_count += 1

            # Case C: Direct translated output file (e.g. batch_001_translated.json)
            elif isinstance(data, list):
                total_batches += 1
                for it in data:
                    if isinstance(it, dict) and "key" in it and "translated" in it:
                        all_translations[it["key"]] = it["translated"]
                        translated_count += 1

        except Exception as e:
            print(f"Warning: Failed to parse {fname}: {e}")

    # Compare against source if provided
    total_sources = None
    if source_path and os.path.isfile(source_path):
        try:
            with open(source_path, "r", encoding="utf-8-sig") as f:
                src_db = json.load(f)
            total_sources = len(src_db)
            coverage = (len(all_translations) / total_sources * 100) if total_sources > 0 else 0
            print(f"[Compiler] Processed {total_batches} batches.")
            print(f"[Compiler] Compiled {len(all_translations)} / {total_sources} entries ({coverage:.1f}% coverage).")
        except Exception:
            pass
    else:
        print(f"[Compiler] Compiled {len(all_translations)} entries from {total_batches} batch files.")

    if out_file:
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(all_translations, f, ensure_ascii=False, indent=2)
        print(f"[Compiler] Saved compiled translations to: {out_file}")

    return all_translations


def main():
    parser = argparse.ArgumentParser(description="Compile translated RPG Maker batch files.")
    parser.add_argument("batches_dir", help="Directory containing batch JSON files")
    parser.add_argument("--source", default=None, help="Path to original translation_source.json for coverage check")
    parser.add_argument("--out", default=None, help="Output path for translation_vietnamese.json")
    args = parser.parse_args()

    batches_dir = os.path.abspath(args.batches_dir)
    default_out = os.path.join(os.path.dirname(batches_dir), "translation_vietnamese.json")
    out_file = args.out or default_out

    compile_batches(batches_dir, args.source, out_file)


if __name__ == "__main__":
    main()

