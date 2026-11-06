#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unity Translation Slicer & Parallel Subagent Batcher
Splits large JSON translation dictionaries into smaller chunks (e.g. 200 items)
and produces a manifest for parallel subagent workers.
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


def slice_dictionary(json_path: Path, chunk_size: int, out_dir: Path) -> dict:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        items = list(data.items())
    elif isinstance(data, list):
        items = list(enumerate(data))
    else:
        raise ValueError("Unsupported JSON root type (must be dict or list)")

    total_items = len(items)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "source_file": json_path.name,
        "total_items": total_items,
        "chunk_size": chunk_size,
        "chunks": []
    }

    chunk_idx = 1
    for i in range(0, total_items, chunk_size):
        chunk_slice = items[i:i + chunk_size]
        chunk_dict = dict(chunk_slice)
        chunk_filename = f"{json_path.stem}_chunk_{chunk_idx:02d}.json"
        chunk_path = out_dir / chunk_filename

        with open(chunk_path, "w", encoding="utf-8") as out_f:
            json.dump(chunk_dict, out_f, indent=2, ensure_ascii=False)

        manifest["chunks"].append({
            "chunk_id": chunk_idx,
            "filename": chunk_filename,
            "start_index": i,
            "count": len(chunk_slice),
            "status": "pending"
        })
        chunk_idx += 1

    manifest_path = out_dir / f"{json_path.stem}_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return manifest


def main():
    parser = argparse.ArgumentParser(description="Slice JSON translation dictionaries into batches.")
    parser.add_argument("json_file", help="Path to source JSON dictionary")
    parser.add_argument("--size", "-s", type=int, default=250, help="Items per chunk (default: 250)")
    parser.add_argument("--out", "-o", default="chunks", help="Output directory (default: 'chunks')")
    args = parser.parse_args()

    json_path = Path(args.json_file).resolve()
    if not json_path.is_file():
        print(f"❌ Error: File not found: {json_path}")
        sys.exit(1)

    out_dir = Path(args.out).resolve()
    print(f"🔪 Slicing '{json_path.name}' into chunks of {args.size} items...")
    manifest = slice_dictionary(json_path, args.size, out_dir)
    print(f"✅ Generated {len(manifest['chunks'])} chunks ({manifest['total_items']} items total) in {out_dir}")
    print(f"📋 Manifest created: {json_path.stem}_manifest.json")


if __name__ == "__main__":
    main()

