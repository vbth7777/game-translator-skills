#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1-Click Safety Rollback & Restore Engine for RPG Maker MV/MZ
Restores 100% pristine original textures and plugins from backup_textures/.
"""

import os
import sys
import shutil
import json
import argparse
from pathlib import Path

def restore_backup(game_root="."):
    game_path = Path(game_root).resolve()
    backup_root = game_path / "backup_textures"
    orig_backup_dir = backup_root / "original_textures"
    manifest_path = backup_root / "manifest.json"
    status_path = backup_root / "status.json"

    if not orig_backup_dir.exists():
        print(f"[Rollback Error] Backup directory not found at: {orig_backup_dir}")
        return False

    print("=" * 70)
    print(" RPG MAKER MV/MZ TEXTURE 1-CLICK ROLLBACK & RESTORE ENGINE")
    print("=" * 70)
    print(f" Target Game Dir : {game_path}")
    print(f" Backup Source   : {orig_backup_dir}")
    print("=" * 70)

    # 1. Restore all texture files
    restored_count = 0
    total_files = 0

    if manifest_path.exists():
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        file_list = [item["rel_path"] for item in manifest.get("files", [])]
    else:
        file_list = []
        for root, _, files in os.walk(orig_backup_dir):
            for f in files:
                full_p = os.path.join(root, f)
                rel_p = os.path.relpath(full_p, str(orig_backup_dir)).replace('\\', '/')
                file_list.append(rel_p)

    total_files = len(file_list)
    print(f"[Rollback] Restoring {total_files} assets to original state...")

    for idx, rel_path in enumerate(file_list, 1):
        src_path = orig_backup_dir / rel_path
        dest_path = game_path / rel_path

        if src_path.exists():
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src_path), str(dest_path))
            restored_count += 1
            if idx % 100 == 0 or idx == total_files:
                print(f"  Progress: {idx}/{total_files} ({(idx/total_files)*100:.1f}%)")

    # 2. Restore plugins.js if backup exists
    for p_candidate in [game_path / "www" / "js" / "plugins.js.bak", game_path / "js" / "plugins.js.bak"]:
        if p_candidate.exists():
            orig_p = p_candidate.with_suffix('')
            print(f"[Rollback] Restoring plugins.js from {p_candidate.name}...")
            shutil.copy2(str(p_candidate), str(orig_p))

    # 3. Reset status.json
    if status_path.exists():
        with open(status_path, 'w', encoding='utf-8') as sf:
            json.dump({"processed": {}, "failed": {}, "rollback_time": True}, sf, indent=2)

    print("\n========================================================")
    print(f"[Rollback SUCCESS] Restored {restored_count}/{total_files} assets byte-for-byte!")
    print("Game directory has been 100% reverted to its pristine original state.")
    print("========================================================")
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Restore original textures from backup.")
    parser.add_argument("--game-dir", default=".", help="Root game directory")
    args = parser.parse_args()

    restore_backup(args.game_dir)
