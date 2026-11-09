#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master GPU Batch Texture Upscaler for Ren'Py Games
Orchestrates high-throughput, tiled, 4-channel alpha-preserving upscaling
using DirectML and Real-ESRGAN Anime 6B.

Enforces the Dual-Path Strategy:
1. Live2D Textures -> Native 2K/4K resolution (Normalized UV coordinates never zoom or shift).
2. Static 2D Images (CG/Bust/UI/BG) -> SSAA Lanczos Resampling (AI super-resolution denoise
   followed by subpixel downsampling to native resolution to eliminate the 2x zoom/clipping bug).
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
import cv2

# Add scripts directory to path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from gpu_upscaler import GPURealESRGAN

def find_default_onnx_model():
    """Searches common local paths for Real-ESRGAN ONNX weights."""
    candidates = [
        Path('upscale_workspace/realesrgan_anime_6b.onnx'),
        Path('models/realesrgan_anime_6b.onnx'),
        Path('c:/Users/ADMIN/Downloads/Compressed/PAWGVERSE-0.05.22-pc/PAWGVERSE-0.05.22-pc/upscale_workspace/realesrgan_anime_6b.onnx'),
        Path('d:/Development/Projects/game-translator-skills/renpy-texture-upscaler/models/realesrgan_anime_6b.onnx')
    ]
    for c in candidates:
        if c.exists():
            return str(c.resolve())
    return None

def run_batch_upscale(
    game_dir,
    manifest_path='backup_textures/manifest.json',
    onnx_path=None,
    category='all',
    high_dpi=False,
    device_id=0,
    workspace_dir='upscale_workspace',
    deploy_live=True
):
    game_path = Path(game_dir).resolve()
    actual_game_dir = game_path / 'game' if (game_path / 'game').exists() else game_path

    if not onnx_path:
        onnx_path = find_default_onnx_model()
    if not onnx_path or not os.path.exists(onnx_path):
        raise FileNotFoundError(
            f"ONNX Model not found at '{onnx_path}'. "
            "Please provide a valid Real-ESRGAN ONNX model via --model-path."
        )

    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}. Please run scan_and_manifest.py first.")

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    # Filter targets based on category
    if category == 'all':
        targets = [m for m in manifest if m.get('is_low_res', True)]
    elif category == 'live2d':
        targets = [m for m in manifest if m.get('category') == 'live2d' and m.get('is_low_res', True)]
    elif category == 'static':
        targets = [m for m in manifest if m.get('category') != 'live2d' and m.get('is_low_res', True)]
    elif category == 'missing':
        targets = [m for m in manifest if m.get('is_low_res', True)]
    else:
        targets = [m for m in manifest if m.get('category') == category and m.get('is_low_res', True)]

    # Load or initialize status registry
    ws_path = Path(workspace_dir)
    ws_path.mkdir(parents=True, exist_ok=True)
    upscaled_storage = ws_path / 'upscaled_textures'
    upscaled_storage.mkdir(parents=True, exist_ok=True)

    status_file = ws_path / 'status.json'
    if status_file.exists():
        with open(status_file, 'r', encoding='utf-8') as sf:
            try:
                status = json.load(sf)
            except Exception:
                status = {}
    else:
        status = {}

    pending_targets = [t for t in targets if t['rel_path'] not in status or status[t['rel_path']].get('status') != 'completed']

    print(f"========================================================")
    print(f"Master GPU Batch Texture Upscaler (DirectML Engine)")
    print(f"Target Project: {actual_game_dir}")
    print(f"ONNX Model: {onnx_path}")
    print(f"Filter Category: {category} | High-DPI Static: {high_dpi}")
    print(f"Total Targets: {len(targets)} | Pending: {len(pending_targets)}")
    print(f"========================================================")

    if not pending_targets:
        print("All targets in the selected category are already completed! Nothing to do.")
        return status

    # Initialize GPU Real-ESRGAN
    print("\nInitializing GPU Real-ESRGAN session...")
    upscaler = GPURealESRGAN(onnx_path, device_id=device_id, tile_size=512, tile_pad=16)

    total_t0 = time.time()
    for idx, item in enumerate(pending_targets, 1):
        rel_path = item['rel_path']
        safe_name = item['backup_file']
        src_path = Path('backup_textures') / 'original_textures' / safe_name
        dest_game_path = actual_game_dir / rel_path
        dest_workspace_path = upscaled_storage / safe_name

        if not src_path.exists():
            # If not in backup folder, try source_path
            src_path = Path(item.get('source_path', ''))
            if not src_path.exists():
                print(f"[{idx}/{len(pending_targets)}] Warning: Source image not found: {rel_path} (Skipping)")
                continue

        is_live2d = (item.get('category') == 'live2d')
        orig_w, orig_h = item.get('original_size', [1024, 1024])
        scale_factor = item.get('recommended_scale', 2)

        print(f"\n[{idx}/{len(pending_targets)}] [{upscaler.active_provider}] Processing: {rel_path}")
        print(f"  Category: {item.get('category')} | Original: {orig_w}x{orig_h}")

        t0 = time.time()
        img = cv2.imread(str(src_path), cv2.IMREAD_UNCHANGED)
        if img is None:
            print(f"  Error: Failed to read image file: {src_path}")
            continue

        # Execution Strategy Selection
        if is_live2d or high_dpi:
            # Path A: Native Super-Resolution (keep full upscaled size)
            target_size = None
            out_img = upscaler.enhance(img, outscale=scale_factor)
            strategy_used = 'live2d_native_super_resolution' if is_live2d else 'high_dpi_native'
        else:
            # Path B: SSAA Lanczos Resampling for Static 2D (prevents 2x screen overflow/zooming)
            target_size = (orig_w, orig_h)
            out_img = upscaler.enhance(img, outscale=scale_factor, target_size=target_size)
            strategy_used = 'ssaa_lanczos_resampling'

        out_h, out_w = out_img.shape[:2]
        elapsed = time.time() - t0

        # Save to workspace storage
        cv2.imwrite(str(dest_workspace_path), out_img)

        # Save to live game directory for zero-touch filesystem override
        if deploy_live:
            dest_game_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(dest_game_path), out_img)

        # Update persistent status registry
        status[rel_path] = {
            'rel_path': rel_path,
            'category': item.get('category'),
            'status': 'completed',
            'strategy': strategy_used,
            'provider': upscaler.active_provider,
            'orig_size': [orig_w, orig_h],
            'upscaled_size': [out_w, out_h],
            'scale': scale_factor,
            'elapsed_sec': round(elapsed, 2),
            'timestamp': time.time(),
            'game_path': str(dest_game_path),
            'workspace_path': str(dest_workspace_path)
        }

        with open(status_file, 'w', encoding='utf-8') as sf:
            json.dump(status, sf, indent=2, ensure_ascii=False)

        print(f"  SUCCESS! ({out_w}x{out_h}) in {elapsed:.2f}s | Strategy: {strategy_used}")
        if deploy_live:
            print(f"  Live Override Deployed: {dest_game_path}")

    total_time = time.time() - total_t0
    print(f"\n========================================================")
    print(f"GPU Batch Upscale Complete!")
    print(f"Successfully processed {len(pending_targets)} assets in {total_time:.1f}s ({total_time/60:.2f} min)!")
    print(f"Updated status saved to: {status_file}")
    print(f"========================================================")
    return status

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Master GPU Batch Upscaler for Ren'Py Game Textures.")
    parser.add_argument('--game-dir', required=True, help="Path to Ren'Py project root or game/ directory")
    parser.add_argument('--manifest', default='backup_textures/manifest.json', help="Path to manifest.json")
    parser.add_argument('--model-path', default=None, help="Path to Real-ESRGAN ONNX weights")
    parser.add_argument('--category', default='all', choices=['all', 'live2d', 'static', 'cg', 'bust', 'wallpaper_or_bg', 'ui_or_thumb', 'missing'])
    parser.add_argument('--high-dpi', action='store_true', help="Retain 2x/4x dimensions for static images instead of SSAA downsampling")
    parser.add_argument('--device-id', type=int, default=0, help="DirectML / GPU Device ID")
    parser.add_argument('--workspace', default='upscale_workspace', help="Workspace cache directory")
    parser.add_argument('--no-deploy', action='store_true', help="Do not write directly to game/ folder")
    args = parser.parse_args()

    run_batch_upscale(
        game_dir=args.game_dir,
        manifest_path=args.manifest,
        onnx_path=args.model_path,
        category=args.category,
        high_dpi=args.high_dpi,
        device_id=args.device_id,
        workspace_dir=args.workspace,
        deploy_live=(not args.no_deploy)
    )
