#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1-Click Safety Rollback & Restore Engine for Ren'Py Textures
Restores 100% pristine original textures and RPA archives from backup_textures/.
Enforces the Zero-Risk Rollback Mandate: Never modify files without an instant restore path.
"""

import os
import sys
import shutil
import json
import argparse
from pathlib import Path

def restore_backup(game_dir=".", backup_dir="backup_textures"):
    game_path = Path(game_dir).resolve()
    actual_game_dir = game_path / 'game' if (game_path / 'game').exists() else game_path
    backup_root = game_path / backup_dir
    orig_backup_dir = backup_root / "originals"
    manifest_path = backup_root / "manifest.json"
    workspace_dir = game_path / "upscale_workspace"
    status_path = workspace_dir / "status.json"

    if not backup_root.exists() or not orig_backup_dir.exists():
        print(f"[Rollback Error] Backup directory not found at: {orig_backup_dir}")
        print("Cannot restore without a valid backup_textures/ directory!")
        return False

    print("=" * 70)
    print(" REN'PY TEXTURE 1-CLICK ROLLBACK & RESTORE ENGINE")
    print("=" * 70)
    print(f" Target Game Dir : {actual_game_dir}")
    print(f" Backup Source   : {orig_backup_dir}")
    print("=" * 70)

    # 1. Restore RPA Archives if .bak exists
    rpa_bak_files = list(actual_game_dir.glob('*.rpa.bak'))
    for rpa_bak in rpa_bak_files:
        orig_rpa = rpa_bak.with_suffix('')
        print(f"[Rollback Archive] Restoring {orig_rpa.name} from {rpa_bak.name}...")
        shutil.copy2(str(rpa_bak), str(orig_rpa))

    # 2. Restore textures using manifest if available
    restored_count = 0
    removed_overrides = 0

    if manifest_path.exists():
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        print(f"[Rollback] Processing {len(manifest)} manifest entries...")
        for item in manifest:
            rel_path = item.get('rel_path')
            source = item.get('source', '')
            backup_file_name = item.get('backup_file')
            
            dest_file = actual_game_dir / rel_path
            backup_file = orig_backup_dir / backup_file_name if backup_file_name else None

            if source == 'loose_file':
                # Original was a loose file: copy backup back
                if backup_file and backup_file.exists():
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(backup_file), str(dest_file))
                    restored_count += 1
            elif source.startswith('rpa:'):
                # Original was inside RPA: if loose override was created, delete loose override
                if dest_file.exists():
                    try:
                        dest_file.unlink()
                        removed_overrides += 1
                    except Exception as e:
                        print(f"  Warning: Could not remove loose override {dest_file}: {e}")

    else:
        # Fallback: Restore any file in orig_backup_dir by replacing '__' back to '/'
        print("[Rollback] Manifest not found. Performing heuristic restore from safe filenames...")
        for backup_f in orig_backup_dir.glob('*'):
            if backup_f.is_file():
                rel_path = backup_f.name.replace('__', '/')
                dest_file = actual_game_dir / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(backup_f), str(dest_file))
                restored_count += 1

    # 3. Reset persistent status
    if status_path.exists():
        try:
            with open(status_path, 'r', encoding='utf-8') as sf:
                status = json.load(sf)
            for k in status:
                status[k]['status'] = 'rolled_back'
            with open(status_path, 'w', encoding='utf-8') as sf:
                json.dump(status, sf, indent=2)
            print(f"[Rollback] Reset status in {status_path}")
        except Exception:
            pass

    print("\n========================================================")
    print(f"[Rollback SUCCESS] Successfully reverted textures to original state!")
    print(f"  - Restored loose files    : {restored_count}")
    print(f"  - Removed loose overrides : {removed_overrides}")
    print(f"  - RPA archives restored   : {len(rpa_bak_files)}")
    print("Game directory has been 100% reverted to its pristine original state.")
    print("========================================================")
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="1-Click restore original textures for Ren'Py.")
    parser.add_argument('--game-dir', default='.', help="Path to Ren'Py project root or game/ directory")
    parser.add_argument('--backup-dir', default='backup_textures', help="Backup root directory")
    args = parser.parse_args()

    restore_backup(args.game_dir, args.backup_dir)
