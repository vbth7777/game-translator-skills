#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ren'Py RPYC Bytecode Decompiler & String Dumper
Inspects and decodes .rpyc files, extracts AST Say / Menu statements,
and dumps translatable text even without full decompilation tools.
"""

import os
import sys
import zlib
import pickle
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


class RPYCParser:
    def __init__(self, rpyc_path: Path):
        self.path = rpyc_path
        self.raw_data = None

    def read_slot1(self) -> bytes | None:
        """Reads Slot 1 (AST data) from .rpyc container."""
        with open(self.path, "rb") as f:
            header = f.read(10)
            if not header.startswith(b"RENPY RPC"):
                return None

            # Read slot offset table
            f.seek(10)
            try:
                # Format: 10 bytes header, then slot table
                slot_info = []
                while True:
                    slot_bytes = f.read(8)
                    if len(slot_bytes) < 8:
                        break
                    slot_num = int.from_bytes(slot_bytes[:4], "big")
                    slot_offset = int.from_bytes(slot_bytes[4:], "big")
                    if slot_num == 0:
                        break
                    slot_info.append((slot_num, slot_offset))

                # Read slot 1 or compressed stream
                f.seek(0)
                content = f.read()
                # Find zlib streams
                pos = content.find(b"\x78\x9c")
                if pos != -1:
                    decompressed = zlib.decompress(content[pos:])
                    return decompressed
            except Exception:
                pass
        return None

    def dump_strings_heuristic(self) -> list[str]:
        """Extracts readable UTF-8 strings from binary stream."""
        content = self.path.read_bytes()
        # Find all null-terminated or len-prefixed strings
        extracted = []
        # Pattern for printable strings >= 4 chars
        matches = re.findall(b'[\x20-\x7E\xC2-\xDF][\x20-\x7E\x80-\xBF]{3,}', content)
        for m in matches:
            try:
                s = m.decode("utf-8").strip()
                if len(s) > 3 and not s.startswith("__") and not s.endswith(".py"):
                    extracted.append(s)
            except UnicodeDecodeError:
                continue
        return extracted


def main():
    parser = argparse.ArgumentParser(description="Decompile or extract translatable strings from .rpyc files.")
    parser.add_argument("rpyc_file", help="Path to .rpyc file or folder")
    parser.add_argument("--out", "-o", help="Output text file")
    args = parser.parse_args()

    target = Path(args.rpyc_file).resolve()
    if not target.exists():
        print(f"❌ Error: Not found: {target}")
        sys.exit(1)

    files = [target] if target.is_file() else list(target.rglob("*.rpyc"))
    print(f"🔍 Scanning {len(files)} .rpyc files...")

    total_strings = 0
    all_extracted = {}

    for f in files:
        parser_inst = RPYCParser(f)
        strings = parser_inst.dump_strings_heuristic()
        if strings:
            all_extracted[f.name] = strings
            total_strings += len(strings)

    print(f"✅ Extracted {total_strings} string candidates across {len(files)} files.")

    if args.out:
        out_path = Path(args.out).resolve()
        import json
        with open(out_path, "w", encoding="utf-8") as out_f:
            json.dump(all_extracted, out_f, indent=2, ensure_ascii=False)
        print(f"💾 Saved to: {out_path}")


if __name__ == "__main__":
    main()

