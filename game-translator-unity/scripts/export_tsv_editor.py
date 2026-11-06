#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unity JSON <-> TSV Offline Review & Editing Tool
Exports translation dictionaries to TSV (Tab-Separated Values) for spreadsheet review,
and imports modified TSV back into JSON in one command.
"""

import os
import sys
import csv
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


def export_to_tsv(json_path: Path, tsv_path: Path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    if isinstance(data, dict):
        for idx, (orig, trans) in enumerate(data.items(), 1):
            rows.append({
                "Index": idx,
                "Original": orig,
                "Vietnamese": trans
            })
    elif isinstance(data, list):
        for idx, item in enumerate(data, 1):
            if isinstance(item, dict):
                orig = item.get("orig", item.get("jp", item.get("en", "")))
                trans = item.get("trans", item.get("vi", ""))
                rows.append({"Index": idx, "Original": orig, "Vietnamese": trans})

    with open(tsv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Index", "Original", "Vietnamese"], delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Exported {len(rows)} entries to TSV: {tsv_path}")


def import_from_tsv(tsv_path: Path, json_path: Path):
    if not tsv_path.is_file():
        raise FileNotFoundError(f"TSV file not found: {tsv_path}")

    data = {}
    with open(tsv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            orig = row.get("Original", "").strip()
            trans = row.get("Vietnamese", "").strip()
            if orig:
                data[orig] = trans

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Imported {len(data)} entries back to JSON: {json_path}")


def main():
    parser = argparse.ArgumentParser(description="Convert between JSON translation dictionary and TSV spreadsheet.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    exp_parser = subparsers.add_parser("export", help="Export JSON to TSV")
    exp_parser.add_argument("json_file", help="Path to JSON file")
    exp_parser.add_argument("tsv_file", help="Path to output TSV file")

    imp_parser = subparsers.add_parser("import", help="Import TSV to JSON")
    imp_parser.add_argument("tsv_file", help="Path to TSV file")
    imp_parser.add_argument("json_file", help="Path to destination JSON file")

    args = parser.parse_args()

    if args.command == "export":
        export_to_tsv(Path(args.json_file), Path(args.tsv_file))
    elif args.command == "import":
        import_from_tsv(Path(args.tsv_file), Path(args.json_file))


if __name__ == "__main__":
    main()

