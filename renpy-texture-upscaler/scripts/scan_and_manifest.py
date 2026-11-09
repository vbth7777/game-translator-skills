#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ren'Py Game Texture Scanner & Manifest Builder
Deeply audits game/ directory and RPA archives to categorize assets into:
1. Live2D Texture Atlases (Normalized UVs -> Native 2K/4K Upscale)
2. Static 2D Images (Screen Coords -> SSAA Lanczos Resampling to prevent 2x Zoom Overflow)
"""

import os
import sys
import json
import pickle
import zlib
import argparse
import shutil
from pathlib import Path
from PIL import Image
import io

def parse_rpa_index(rpa_path):
    """Parses RPA-3.0 or RPA-2.0 archive header and index."""
    if not os.path.exists(rpa_path):
        return {}
    try:
        with open(rpa_path, 'rb') as f:
            header = f.readline()
            parts = header.split()
            if not parts or not parts[0].startswith(b'RPA-'):
                return {}
            pos = int(parts[1], 16)
            key = int(parts[2], 16)
            f.seek(pos)
            index = pickle.loads(zlib.decompress(f.read()))
            return {'index': index, 'key': key, 'path': rpa_path}
    except Exception as e:
        print(f"[scan_and_manifest] Error reading {rpa_path}: {e}")
        return {}

def extract_rpa_entry(rpa_info, filename):
    """Extracts raw file bytes from RPA archive."""
    index = rpa_info['index']
    key = rpa_info['key']
    rpa_path = rpa_info['path']
    if filename not in index:
        return None
    entry = index[filename][0]
    offset = entry[0] ^ key
    length = entry[1] ^ key
    prefix = entry[2] if len(entry) > 2 else b''
    with open(rpa_path, 'rb') as f:
        f.seek(offset)
        data = prefix + f.read(length)
    return data

def is_live2d_texture(rel_path):
    """Checks whether a relative path points to a Live2D texture atlas."""
    p = rel_path.lower().replace('\\', '/')
    if '/texture_' in p and (p.endswith('.png') or p.endswith('.webp')):
        return True
    if any(k in p for k in ['.moc3', '.model3.json', 'live2d', 'live_']):
        if p.endswith(('.png', '.webp', '.jpg')):
            return True
    return False

def classify_asset(rel_path, width, height):
    """
    Classifies image into asset category and determines optimal target upscale strategy.
    """
    rel_lower = rel_path.lower().replace('\\', '/')
    min_dim = min(width, height)
    max_dim = max(width, height)

    if is_live2d_texture(rel_path):
        category = 'live2d'
        # If atlas is already 4096, it's considered native high-res
        if max_dim >= 4096:
            is_low_res = False
            scale = 1
            mode = 'native_retained'
        elif min_dim <= 512:
            is_low_res = True
            scale = 4  # 512x1024 -> 2048x4096
            mode = 'live2d_native_4k'
        else:
            is_low_res = True
            scale = 2  # 1024x1024 -> 2048x2048 or 1024x2048 -> 2048x4096
            mode = 'live2d_native_4k'
        target_size = [width * scale, height * scale]

    elif any(k in rel_lower for k in ['/cg/', '/cgs/', 'event_']):
        category = 'cg'
        is_low_res = True
        scale = 2
        mode = 'ssaa_lanczos' # AI 2x/4x denoise + Lanczos resample back to (width, height)
        target_size = [width, height]

    elif any(k in rel_lower for k in ['/bust/', '/busts/', '/portraits/', '/sprites/']):
        category = 'bust'
        is_low_res = True
        scale = 2
        mode = 'ssaa_lanczos'
        target_size = [width, height]

    elif any(k in rel_lower for k in ['/bg/', '/backgrounds/', 'main_menu', 'title', 'wallpaper', 'splash']):
        category = 'wallpaper_or_bg'
        is_low_res = True
        scale = 2
        mode = 'ssaa_lanczos'
        target_size = [width, height]

    elif any(k in rel_lower for k in ['/gui/', '/assets/', 'thumb', 'icon', 'button']):
        category = 'ui_or_thumb'
        is_low_res = (max_dim <= 1024)
        scale = 2
        mode = 'ssaa_lanczos'
        target_size = [width, height]

    else:
        category = 'misc_static'
        is_low_res = (max_dim <= 2048)
        scale = 2
        mode = 'ssaa_lanczos'
        target_size = [width, height]

    return {
        'category': category,
        'is_low_res': is_low_res,
        'recommended_scale': scale,
        'mode': mode,
        'target_size': target_size
    }

def scan_game_assets(game_dir, output_dir='backup_textures'):
    game_path = Path(game_dir).resolve()
    if not game_path.exists():
        raise FileNotFoundError(f"Game directory not found: {game_path}")

    # If user pointed to game folder or root
    actual_game_dir = game_path / 'game' if (game_path / 'game').exists() else game_path

    print(f"========================================================")
    print(f"Ren'Py Texture Scanner & Manifest Builder")
    print(f"Scanning Target: {actual_game_dir}")
    print(f"========================================================")

    backup_orig_dir = Path(output_dir) / 'original_textures'
    backup_orig_dir.mkdir(parents=True, exist_ok=True)

    manifest = []
    seen_paths = set()

    # 1. Scan loose files in game directory
    image_exts = {'.png', '.webp', '.jpg', '.jpeg'}
    print("[1/3] Scanning loose image files in game/ directory...")
    for file_path in actual_game_dir.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in image_exts:
            rel_path = file_path.relative_to(actual_game_dir).as_posix()
            if rel_path in seen_paths:
                continue
            seen_paths.add(rel_path)

            try:
                with Image.open(file_path) as img:
                    w, h = img.size
                    img_mode = img.mode
            except Exception:
                continue

            classification = classify_asset(rel_path, w, h)
            safe_name = rel_path.replace('/', '__').replace('\\', '__')
            backup_file = backup_orig_dir / safe_name

            if not backup_file.exists():
                shutil.copy2(file_path, backup_file)

            manifest.append({
                'rel_path': rel_path,
                'source': 'loose_file',
                'source_path': str(file_path),
                'backup_file': safe_name,
                'original_size': [w, h],
                'mode_format': img_mode,
                **classification
            })

    # 2. Scan RPA archives in game directory
    print("[2/3] Scanning packed RPA archives...")
    rpa_files = list(actual_game_dir.glob('*.rpa'))
    for rpa_file in rpa_files:
        print(f"  Inspecting archive: {rpa_file.name}...")
        rpa_info = parse_rpa_index(str(rpa_file))
        if not rpa_info:
            continue

        for filename in rpa_info['index'].keys():
            ext = os.path.splitext(filename)[1].lower()
            if ext not in image_exts:
                continue

            # In Ren'Py, loose files override RPA files. If already seen as loose file, skip or note.
            if filename in seen_paths:
                continue
            seen_paths.add(filename)

            raw_bytes = extract_rpa_entry(rpa_info, filename)
            if not raw_bytes:
                continue

            try:
                with Image.open(io.BytesIO(raw_bytes)) as img:
                    w, h = img.size
                    img_mode = img.mode
            except Exception:
                continue

            classification = classify_asset(filename, w, h)
            safe_name = filename.replace('/', '__').replace('\\', '__')
            backup_file = backup_orig_dir / safe_name

            if not backup_file.exists():
                with open(backup_file, 'wb') as bf:
                    bf.write(raw_bytes)

            manifest.append({
                'rel_path': filename,
                'source': f'rpa:{rpa_file.name}',
                'rpa_name': rpa_file.name,
                'backup_file': safe_name,
                'original_size': [w, h],
                'mode_format': img_mode,
                **classification
            })

    # 3. Summary & Output Manifest
    manifest_path = Path(output_dir) / 'manifest.json'
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    live2d_targets = [m for m in manifest if m['category'] == 'live2d' and m['is_low_res']]
    static_targets = [m for m in manifest if m['category'] != 'live2d' and m['is_low_res']]

    print(f"\n[3/3] Audit & Manifest Complete!")
    print(f"  Total Image Assets Indexed: {len(manifest)}")
    print(f"  Live2D Textures Requiring 2K/4K Upscale: {len(live2d_targets)}")
    print(f"  Static 2D Images (CG/Bust/UI/BG) for SSAA Resampling: {len(static_targets)}")
    print(f"  Manifest written to: {manifest_path}")
    print(f"  Original textures securely backed up to: {backup_orig_dir}")
    print(f"========================================================")

    return manifest

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Scan and classify Ren'Py game textures for upscaling.")
    parser.add_argument('--game-dir', required=True, help="Path to Ren'Py project root or game/ directory")
    parser.add_argument('--output-dir', default='backup_textures', help="Output directory for backups & manifest")
    args = parser.parse_args()

    scan_game_assets(args.game_dir, args.output_dir)
