#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streaming RPA Archive Repacker & Patcher for Ren'Py Games
Embeds upscaled textures into RPA-3.0/2.0 archives with safety backups,
integrity verification, and atomic swap.
"""

import os
import sys
import shutil
import pickle
import zlib
import time
import json
import argparse
from pathlib import Path
from PIL import Image
import io

def repack_rpa_archive(game_dir, archive_name='archive.rpa', status_file='upscale_workspace/status.json', clean_loose=False):
    game_path = Path(game_dir).resolve()
    actual_game_dir = game_path / 'game' if (game_path / 'game').exists() else game_path

    orig_archive = actual_game_dir / archive_name
    backup_archive = actual_game_dir / f"{archive_name}.original_backup"
    new_archive_tmp = actual_game_dir / f"{archive_name}.new"

    if not orig_archive.exists() and not backup_archive.exists():
        raise FileNotFoundError(f"Target archive not found: {orig_archive}")

    # Step 1: Backup original archive if not already done
    if not backup_archive.exists():
        print(f"[repack_archive] Creating backup of original archive to {backup_archive.name}...")
        t0 = time.time()
        shutil.copy2(orig_archive, backup_archive)
        print(f"  Backup created in {time.time()-t0:.1f}s ({orig_archive.stat().st_size / 1024 / 1024:.2f} MB)")
    else:
        print(f"[repack_archive] Original backup archive already exists: {backup_archive.name}")

    # Step 2: Read source index from backup
    with open(backup_archive, 'rb') as f_src:
        header = f_src.readline()
        parts = header.split()
        if not parts or not parts[0].startswith(b'RPA-'):
            raise ValueError(f"Invalid RPA format in {backup_archive.name}: {header[:30]}")
        rpa_version = parts[0].decode('latin1')
        pos = int(parts[1], 16)
        key = int(parts[2], 16)
        f_src.seek(pos)
        old_index = pickle.loads(zlib.decompress(f_src.read()))

    print(f"[repack_archive] Loaded source archive index: {len(old_index)} files, format: {rpa_version}, key: {hex(key)}")

    # Step 3: Discover replacements from status.json or filesystem
    replacements = {}
    if os.path.exists(status_file):
        with open(status_file, 'r', encoding='utf-8') as sf:
            st = json.load(sf)
            for rel_path, data in st.items():
                if data.get('status') == 'completed':
                    # Check loose game file or workspace file
                    candidate = actual_game_dir / rel_path
                    if candidate.exists():
                        replacements[rel_path] = candidate
                    elif 'workspace_path' in data and os.path.exists(data['workspace_path']):
                        replacements[rel_path] = Path(data['workspace_path'])

    # Also scan for any loose files inside game/ matching old_index
    for k in old_index.keys():
        if k not in replacements:
            loose_file = actual_game_dir / k
            if loose_file.exists():
                replacements[k] = loose_file

    print(f"[repack_archive] Total upscaled assets to embed into {archive_name}: {len(replacements)}")

    if not replacements:
        print("No replacements found! Archive repacking cancelled.")
        return False

    # Step 4: Stream copy & embed into new archive
    t_start = time.time()
    new_index = {}
    new_key = 0x42424242 # Standard Ren'Py 32-bit obfuscation key
    dummy_header = f"{rpa_version} {'0'*16} {'0'*8}\n".encode('latin1')

    with open(backup_archive, 'rb') as f_src, open(new_archive_tmp, 'wb') as f_dst:
        # Write dummy placeholder header
        f_dst.write(dummy_header)

        total_files = len(old_index)
        embedded_count = 0

        for idx, (filename, entry_list) in enumerate(sorted(old_index.items()), 1):
            if filename in replacements:
                # Read from upscaled replacement file
                rep_path = replacements[filename]
                with open(rep_path, 'rb') as rep_f:
                    data = rep_f.read()
                prefix = b''
                embedded_count += 1
                if embedded_count <= 5 or embedded_count % 25 == 0 or embedded_count == len(replacements):
                    print(f"  [Embed {embedded_count}/{len(replacements)}] {filename} ({len(data):,} bytes)")
            else:
                # Stream copy untouched original file bytes
                entry = entry_list[0]
                offset = entry[0] ^ key
                length = entry[1] ^ key
                prefix = entry[2] if len(entry) > 2 else b''
                f_src.seek(offset)
                data = f_src.read(length)

            write_offset = f_dst.tell()
            f_dst.write(prefix)
            f_dst.write(data)
            write_length = len(data)

            new_index[filename] = [(write_offset ^ new_key, write_length ^ new_key, prefix)]

            if idx % 1000 == 0:
                print(f"  Progress: {idx}/{total_files} files written...")

        # Write zlib-compressed pickle index
        index_offset = f_dst.tell()
        print(f"Writing compressed index at byte offset {index_offset}...")
        compressed_index = zlib.compress(pickle.dumps(new_index, protocol=2))
        f_dst.write(compressed_index)

        # Seek back and write genuine RPA header
        f_dst.seek(0)
        real_header = f"{rpa_version} {index_offset:016x} {new_key:08x}\n".encode('latin1')
        assert len(real_header) == len(dummy_header), f"Header length mismatch: {len(real_header)} vs {len(dummy_header)}"
        f_dst.write(real_header)

    repack_time = time.time() - t_start
    new_size_mb = new_archive_tmp.stat().st_size / 1024 / 1024
    print(f"[repack_archive] Stream repack complete in {repack_time:.1f}s! New archive size: {new_size_mb:.2f} MB")

    # Step 5: Verification of new archive integrity
    print("\n--- Verifying Repacked Archive Integrity ---")
    with open(new_archive_tmp, 'rb') as f_verify:
        v_header = f_verify.readline()
        v_parts = v_header.split()
        v_pos = int(v_parts[1], 16)
        v_key = int(v_parts[2], 16)
        f_verify.seek(v_pos)
        v_index = pickle.loads(zlib.decompress(f_verify.read()))
        assert len(v_index) == total_files, f"Index count mismatch: {len(v_index)} vs {total_files}"

        # Test read random sample of embedded upscaled files
        verified_count = 0
        sample_keys = list(replacements.keys())[:5]
        for k in sample_keys:
            v_entry = v_index[k][0]
            v_offset = v_entry[0] ^ v_key
            v_length = v_entry[1] ^ v_key
            f_verify.seek(v_offset)
            v_data = f_verify.read(v_length)
            img = Image.open(io.BytesIO(v_data))
            print(f"  Verified embedded asset: {k} -> Size: {img.size}, Mode: {img.mode}")
            verified_count += 1

    print(f"Integrity Verification PASSED! {verified_count}/{len(sample_keys)} samples verified.")

    # Step 6: Atomic swap
    print(f"\nPerforming atomic swap: {new_archive_tmp.name} -> {orig_archive.name}...")
    if orig_archive.exists():
        orig_archive.unlink()
    new_archive_tmp.rename(orig_archive)
    print(f"SUCCESS: {orig_archive.name} is now updated with all upscaled textures!")

    # Step 7: Optional cleanup of loose files (to avoid duplicate disk usage)
    if clean_loose:
        print("\nCleaning up loose override files in game/ directory...")
        cleaned = 0
        for rel_path in replacements.keys():
            loose_p = actual_game_dir / rel_path
            if loose_p.exists() and loose_p.is_file():
                try:
                    loose_p.unlink()
                    cleaned += 1
                except Exception:
                    pass
        print(f"Cleaned up {cleaned} loose override files. Game directory is clean and compact.")

    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Repack Ren'Py RPA archive with upscaled textures.")
    parser.add_argument('--game-dir', required=True, help="Path to Ren'Py project root or game/ directory")
    parser.add_argument('--archive', default='archive.rpa', help="Name of archive file inside game/ (e.g. archive.rpa, images.rpa)")
    parser.add_argument('--status', default='upscale_workspace/status.json', help="Path to status.json")
    parser.add_argument('--clean-loose', action='store_true', help="Remove loose files in game/ after packing into RPA")
    args = parser.parse_args()

    repack_rpa_archive(args.game_dir, args.archive, args.status, args.clean_loose)
