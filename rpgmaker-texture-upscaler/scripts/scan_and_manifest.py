#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scan and Manifest Auditor for RPG Maker MV/MZ Textures
Audits all graphic assets in www/img (or img/), categorizes them, creates safe backup,
and generates backup_textures/manifest.json.
"""

import os
import sys
import json
import shutil
import hashlib
import struct
import argparse
from pathlib import Path

# Add script directory to path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rpgmv_crypto import RPGMVCrypto, PNG_MAGIC

def get_png_dimensions(png_bytes):
    """Extracts (width, height) directly from PNG IHDR chunk (bytes 16-24)."""
    if len(png_bytes) >= 24 and png_bytes[:8] == PNG_MAGIC:
        w, h = struct.unpack('>II', png_bytes[16:24])
        return w, h
    return None, None

def compute_sha256(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def find_img_directory(game_root):
    """Finds img directory whether game is MV (www/img) or MZ (img)."""
    candidates = [
        os.path.join(game_root, "www", "img"),
        os.path.join(game_root, "img"),
        game_root
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.isdir(c):
            # Check if common subfolders exist
            if any(os.path.exists(os.path.join(c, sub)) for sub in ['pictures', 'faces', 'characters', 'tilesets', 'system']):
                return c
    return os.path.join(game_root, "www", "img") if os.path.exists(os.path.join(game_root, "www")) else os.path.join(game_root, "img")

def classify_rpgmaker_asset(category, width, height):
    """
    Classifies RPG Maker asset into its optimal 2x Super-Resolution strategy.
    
    CRITICAL LESSON FROM SESSION 67fa5fe0:
    In RPG Maker MV ($816x624 canvas), SSAA downsampling creates severe pixel staircasing
    and makes drawings look like 16-bit retro pixel games ('bị rỗ hạt').
    Therefore, all RPG Maker assets use Native 2x/4x Super-Resolution combined with
    the in-game PixiJS HDTextureScale plugin.
    """
    scale = 2
    if category == 'pictures':
        mode = 'native_2x_picture'
        note = "Native 2x Super-Resolution. In-game HD plugin hooks Sprite_Picture (scale *= 0.5) for crisp rendering."
    elif category == 'faces':
        mode = 'native_2x_face'
        note = "Native 2x Super-Resolution (288x288 per face). In-game HD plugin hooks Window_Base.drawFace."
    elif category == 'characters':
        mode = 'native_2x_character'
        note = "Native 2x Super-Resolution. In-game HD plugin hooks Sprite_Character for smooth walking sprites."
    elif category == 'animations':
        mode = 'native_2x_animation'
        note = "Native 2x Super-Resolution for battle VFX cells."
    elif category in ['battlebacks1', 'battlebacks2', 'titles1', 'titles2', 'parallaxes']:
        mode = 'native_2x_background'
        note = "Native 2x Super-Resolution for scene backgrounds."
    elif category == 'tilesets':
        mode = 'native_2x_tileset'
        note = "Map tileset (96x96 tiles). Requires High-DPI canvas to prevent tilemap grid bleeding."
    else:
        mode = 'native_2x_system'
        note = "System/UI graphic element."

    target_size = [width * scale, height * scale] if (width and width > 0) else None

    return {
        'recommended_scale': scale,
        'mode': mode,
        'target_size': target_size,
        'note': note
    }

def scan_and_manifest(game_root=".", do_backup=True):
    game_path = Path(game_root).resolve()
    img_dir = find_img_directory(str(game_path))
    backup_root = game_path / "backup_textures"
    orig_backup_dir = backup_root / "original_textures"
    manifest_path = backup_root / "manifest.json"

    if not os.path.exists(img_dir):
        raise FileNotFoundError(f"Texture directory not found in: {game_path} (looked for {img_dir})")

    backup_root.mkdir(parents=True, exist_ok=True)
    if do_backup:
        orig_backup_dir.mkdir(parents=True, exist_ok=True)

    crypto = RPGMVCrypto(game_root=str(game_path))
    manifest = {
        "version": "2.0",
        "engine": "RPG Maker MV/MZ",
        "game_root": str(game_path),
        "img_dir": img_dir,
        "encryption_key": crypto.key.hex(),
        "total_files": 0,
        "total_bytes": 0,
        "categories": {},
        "files": []
    }

    print(f"========================================================")
    print(f"RPG Maker Texture Scanner & Manifest Builder")
    print(f"Target Directory: {img_dir}")
    print(f"Encryption Key  : 0x{crypto.key.hex()}")
    print(f"========================================================")

    valid_extensions = ('.rpgmvp', '.png', '.jpg', '.jpeg', '.webp')

    all_files = []
    for root, _, files in os.walk(img_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in valid_extensions:
                all_files.append(os.path.join(root, f))

    all_files.sort()
    manifest["total_files"] = len(all_files)
    print(f"[Scanner] Discovered {len(all_files)} total texture assets.")

    for idx, full_path in enumerate(all_files, 1):
        rel_path = os.path.relpath(full_path, str(game_path)).replace('\\', '/')
        rel_to_img = os.path.relpath(full_path, img_dir).replace('\\', '/')
        category = rel_to_img.split('/')[0] if '/' in rel_to_img else "root"
        
        file_size = os.path.getsize(full_path)
        manifest["total_bytes"] += file_size
        sha256 = compute_sha256(full_path)

        # Extract dimensions directly from header
        w, h = None, None
        try:
            with open(full_path, 'rb') as f:
                raw_bytes = f.read(64)
            if full_path.endswith('.rpgmvp'):
                png_head = crypto.decrypt_bytes_to_png(raw_bytes)
                w, h = get_png_dimensions(png_head)
            elif full_path.endswith('.png'):
                w, h = get_png_dimensions(raw_bytes)
        except Exception:
            w, h = -1, -1

        classification = classify_rpgmaker_asset(category, w, h)

        item = {
            "rel_path": rel_path,
            "category": category,
            "filename": os.path.basename(full_path),
            "size_bytes": file_size,
            "sha256": sha256,
            "original_size": [w, h],
            "format": os.path.splitext(full_path)[1].lower()[1:],
            **classification
        }
        manifest["files"].append(item)

        if category not in manifest["categories"]:
            manifest["categories"][category] = {"count": 0, "size_bytes": 0}
        manifest["categories"][category]["count"] += 1
        manifest["categories"][category]["size_bytes"] += file_size

        # Backup pristine file if requested
        if do_backup:
            backup_dest = orig_backup_dir / rel_path
            backup_dest.parent.mkdir(parents=True, exist_ok=True)
            if not backup_dest.exists():
                shutil.copy2(full_path, backup_dest)

        if idx % 200 == 0 or idx == len(all_files):
            print(f"[Scanner] Progress: {idx}/{len(all_files)} ({(idx/len(all_files))*100:.1f}%)")

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n========================================================")
    print(f"[Scanner] Scan & Manifest Complete!")
    print(f"[Scanner] Manifest written to: {manifest_path}")
    print(f"[Scanner] Breakdown by category:")
    for cat, data in sorted(manifest["categories"].items()):
        print(f"  - {cat:15}: {data['count']:4} assets ({data['size_bytes'] / (1024*1024):.2f} MB)")
    if do_backup:
        print(f"[Scanner] All original files backed up to: {orig_backup_dir}")
    print(f"========================================================")

    return manifest

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Scan and manifest RPG Maker MV/MZ textures.")
    parser.add_argument("--game-dir", default=".", help="Root game directory")
    parser.add_argument("--no-backup", action="store_true", help="Skip creating backup copies")
    args = parser.parse_args()

    scan_and_manifest(args.game_dir, do_backup=not args.no_backup)
