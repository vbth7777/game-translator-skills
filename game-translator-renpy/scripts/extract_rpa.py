#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universal Ren'Py RPA Archive Extractor
Supports RPA-3.0 and RPA-2.0 archives without external dependencies.
"""

import os
import sys
import zlib
import pickle
import argparse
from pathlib import Path
import fnmatch

# Ensure utf-8 stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


class RPAArchive:
    def __init__(self, rpa_path: Path):
        self.rpa_path = rpa_path
        self.index = {}
        self.key = 0
        self.version = "unknown"
        self._load_index()

    def _load_index(self):
        with open(self.rpa_path, "rb") as f:
            header = f.readline().decode("latin1").strip()
            parts = header.split()
            if not parts or not parts[0].startswith("RPA-"):
                raise ValueError(f"Not a valid Ren'Py RPA archive: {header}")

            self.version = parts[0]
            offset = int(parts[1], 16)
            self.key = int(parts[2], 16) if len(parts) > 2 else 0

            f.seek(offset)
            compressed_index = f.read()
            decompressed_index = zlib.decompress(compressed_index)
            self.index = pickle.loads(decompressed_index)

    def list_files(self) -> list[str]:
        return sorted(list(self.index.keys()))

    def extract(self, targets: list[str] | None, out_dir: Path, pattern: str | None = None) -> int:
        out_dir.mkdir(parents=True, exist_ok=True)
        count = 0

        with open(self.rpa_path, "rb") as f:
            for filename, chunks in self.index.items():
                if pattern and not fnmatch.fnmatch(filename, pattern):
                    continue
                if targets and filename not in targets:
                    continue

                dest_path = out_dir / filename
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                with open(dest_path, "wb") as out_f:
                    for chunk in chunks:
                        offset = chunk[0] ^ self.key
                        length = chunk[1] ^ self.key
                        prefix = chunk[2] if len(chunk) > 2 and chunk[2] else b""
                        f.seek(offset)
                        data = f.read(length)
                        out_f.write(prefix + data)

                count += 1
        return count


def main():
    parser = argparse.ArgumentParser(description="Extract Ren'Py RPA archives.")
    parser.add_argument("rpa_file", help="Path to .rpa archive")
    parser.add_argument("--out", "-o", default="extracted", help="Destination folder (default: 'extracted')")
    parser.add_argument("--list", "-l", action="store_true", help="List files in archive")
    parser.add_argument("--pattern", "-p", help="Filter files by glob pattern (e.g. '*.rpyc', 'fonts/*')")
    parser.add_argument("--files", "-f", nargs="+", help="Specific files to extract")
    args = parser.parse_args()

    rpa_path = Path(args.rpa_file).resolve()
    if not rpa_path.is_file():
        print(f"❌ Error: Archive not found at {rpa_path}")
        sys.exit(1)

    try:
        archive = RPAArchive(rpa_path)
    except Exception as e:
        print(f"❌ Failed to read RPA header: {e}")
        sys.exit(1)

    print(f"📦 Archive: {rpa_path.name} | Format: {archive.version} | Total items: {len(archive.index)}")

    if args.list:
        files = archive.list_files()
        if args.pattern:
            files = [f for f in files if fnmatch.fnmatch(f, args.pattern)]
        print(f"📄 Matching files ({len(files)}):")
        for f in files:
            print(f"   {f}")
        return

    out_dir = Path(args.out).resolve()
    print(f"🚀 Extracting to: {out_dir}...")
    extracted_count = archive.extract(targets=args.files, out_dir=out_dir, pattern=args.pattern)
    print(f"✅ Successfully extracted {extracted_count} files!")


if __name__ == "__main__":
    main()

