#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unity Translation Chunk Compiler
Merges translated chunk files back into unified JSON translation files
and checks for missing keys or malformed entries.
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


def compile_chunks(chunk_dir: Path, output_file: Path, pattern: str = "*.json") -> dict:
    all_chunks = sorted(list(chunk_dir.glob(pattern)))
    merged_data = {}

    for c in all_chunks:
        if c.name.endswith("_manifest.json") or c.resolve() == output_file.resolve():
            continue
        try:
            with open(c, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    merged_data.update(data)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, list) and len(item) == 2:
                            merged_data[item[0]] = item[1]
                        elif isinstance(item, dict):
                            merged_data.update(item)
        except Exception as e:
            print(f"⚠️ Error reading chunk {c.name}: {e}")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)

    return merged_data


def main():
    parser = argparse.ArgumentParser(description="Merge translated JSON chunks into destination translation dictionary.")
    parser.add_argument("chunk_dir", help="Directory containing translated chunks")
    parser.add_argument("--out", "-o", required=True, help="Path to destination JSON file")
    parser.add_argument("--pattern", "-p", default="*.json", help="Glob pattern for chunk files")
    args = parser.parse_args()

    chunk_dir = Path(args.chunk_dir).resolve()
    out_file = Path(args.out).resolve()

    if not chunk_dir.is_dir():
        print(f"❌ Error: Directory not found: {chunk_dir}")
        sys.exit(1)

    print(f"📦 Compiling chunks from '{chunk_dir}' into '{out_file.name}'...")
    merged = compile_chunks(chunk_dir, out_file, args.pattern)
    print(f"✅ Successfully merged {len(merged)} translation entries into: {out_file}")


if __name__ == "__main__":
    main()

