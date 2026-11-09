#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master GPU Batch Upscaler for RPG Maker MV/MZ Games
DirectML Hardware Accelerated Inference (NVIDIA RTX / AMD / Intel Arc)
Supports in-memory .rpgmvp decryption/re-encryption, Native 2x/4x Super-Resolution,
and atomic file replacement.
"""

import os
import sys
import time
import json
import argparse
import shutil
from pathlib import Path

# Add script directory to path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rpgmv_crypto import RPGMVCrypto
from gpu_upscaler import GPURealESRGAN

def find_default_onnx_model():
    """Searches common local paths for Real-ESRGAN ONNX weights."""
    candidates = [
        SCRIPT_DIR.parent / 'models' / 'realesrgan_anime_6b.onnx',
        Path('models/realesrgan_anime_6b.onnx'),
        Path(r"C:\Users\ADMIN\.gemini\config\skills\renpy-texture-upscaler\models\realesrgan_anime_6b.onnx"),
        Path(r"C:\Users\ADMIN\.gemini\config\skills\rpgmaker-texture-upscaler\models\realesrgan_anime_6b.onnx")
    ]
    for c in candidates:
        if c.exists():
            return str(c.resolve())
    return None

def load_status(status_path):
    if os.path.exists(status_path):
        try:
            with open(status_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"processed": {}, "failed": {}}

def save_status(status_path, status):
    tmp = str(status_path) + ".tmp"
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2, ensure_ascii=False)
    os.replace(tmp, status_path)

def run_batch_upscale(
    game_dir=".",
    category="pictures",
    mode="native2x",
    limit=None,
    force=False,
    tile_size=512,
    tile_pad=16,
    device_id=0,
    model_path=None
):
    game_path = Path(game_dir).resolve()
    backup_root = game_path / "backup_textures"
    manifest_path = backup_root / "manifest.json"
    status_path = backup_root / "status.json"

    if not manifest_path.exists():
        print(f"[Upscaler] Error: manifest.json not found at {manifest_path}.")
        print("[Upscaler] Please run scan_and_manifest.py first!")
        return False

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    if not model_path:
        model_path = find_default_onnx_model()
    if not model_path or not os.path.exists(model_path):
        raise FileNotFoundError(f"Real-ESRGAN ONNX model not found: {model_path}")

    status = load_status(str(status_path))
    crypto = RPGMVCrypto(game_root=str(game_path))

    # Filter target files
    target_files = []
    for item in manifest.get("files", []):
        cat = item.get("category", "")
        if category != "all" and cat.lower() != category.lower():
            continue
        rel_path = item["rel_path"]
        if not force and rel_path in status["processed"]:
            continue
        target_files.append(item)

    if limit and limit > 0:
        target_files = target_files[:limit]

    total_tasks = len(target_files)
    if total_tasks == 0:
        print(f"[Upscaler] All files in category='{category}' have already been processed!")
        return True

    print("=" * 70)
    print(" RPG MAKER MV/MZ AI TEXTURE UPSCALER (DIRECTML GPU ENGINE)")
    print("=" * 70)
    print(f" Target Game Dir : {game_path}")
    print(f" Category        : {category}")
    print(f" Strategy Mode   : {mode.upper()}")
    print(f" Files to Process: {total_tasks}")
    print(f" Tile Size / Pad : {tile_size} / {tile_pad}")
    print(f" Encryption Key  : 0x{crypto.key.hex()}")
    print(f" ONNX Model      : {model_path}")
    print("=" * 70)

    # Initialize GPU Model
    print("[Upscaler] Initializing DirectML GPU Inference Session...")
    t0_init = time.time()
    upscaler = GPURealESRGAN(
        onnx_model_path=model_path,
        device_id=device_id,
        tile_size=tile_size,
        tile_pad=tile_pad,
        scale=4
    )
    print(f"[Upscaler] GPU Engine ready in {time.time() - t0_init:.2f}s! Active Provider: {upscaler.active_provider}")

    t_start = time.time()
    completed_count = 0

    for idx, item in enumerate(target_files, 1):
        rel_path = item["rel_path"]
        cat = item.get("category", "")
        full_path = game_path / rel_path

        if not full_path.exists():
            print(f"[{idx}/{total_tasks}] Skip: File not found: {full_path}")
            continue

        item_t0 = time.time()
        try:
            # 1. Load image (auto-decrypting .rpgmvp in-memory if encrypted)
            img, orig_format = crypto.load_image(str(full_path))
            orig_h, orig_w = img.shape[:2]

            print(f"\n[{idx}/{total_tasks}] [{upscaler.active_provider}] Upscaling: {rel_path}")
            print(f"  Category: {cat} | Original Size: {orig_w}x{orig_h} | Format: {orig_format}")

            # 2. Upscale according to strategy
            if mode == 'native2x':
                # Native 2x: Upscale to 2x (e.g. 816x624 -> 1632x1248)
                result_img = upscaler.enhance(img, outscale=2.0)
            elif mode == 'native4x':
                # Native 4x: Pure 4x model output
                result_img = upscaler.enhance(img, outscale=4.0)
            elif mode == 'ssaa':
                # SSAA Lanczos-4: downscale back to original size (Warning: causes pixelation on small canvases)
                result_img = upscaler.enhance(img, target_size=(orig_w, orig_h))
            else:
                raise ValueError(f"Unknown mode: {mode}")

            new_h, new_w = result_img.shape[:2]

            # MANDATORY BACKUP GUARD: Guarantee pristine original backup exists before writing/replacing
            orig_backup_dir = backup_root / "original_textures"
            backup_dest = orig_backup_dir / rel_path
            if not backup_dest.exists() and full_path.exists():
                backup_dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(full_path), str(backup_dest))
                print(f"  [Backup Guard] Protected original texture to: {backup_dest}")

            # 3. Save to temporary file then atomic replace
            tmp_path = str(full_path) + ".up_tmp"
            crypto.save_image(result_img, tmp_path, orig_format=orig_format)
            os.replace(tmp_path, str(full_path))

            elapsed_item = time.time() - item_t0
            completed_count += 1
            status["processed"][rel_path] = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_sec": round(elapsed_item, 2),
                "mode": mode,
                "orig_size": f"{orig_w}x{orig_h}",
                "new_size": f"{new_w}x{new_h}",
                "category": cat
            }

            # Atomic save status
            save_status(str(status_path), status)

            print(f"  SUCCESS! Upscaled to {new_w}x{new_h} in {elapsed_item:.2f}s (Atomic replace complete)")

        except Exception as e:
            print(f"  ERROR processing {rel_path}: {e}")
            status["failed"][rel_path] = {"error": str(e), "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
            save_status(str(status_path), status)

    total_time = time.time() - t_start
    print("\n========================================================")
    print(f"Batch Upscale Finished!")
    print(f"Successfully processed {completed_count}/{total_tasks} assets in {total_time:.1f}s ({total_time/60:.2f} min).")
    print(f"Status saved to: {status_path}")
    print("========================================================")
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Master GPU Batch Upscaler for RPG Maker MV/MZ.")
    parser.add_argument("--game-dir", default=".", help="Root game directory")
    parser.add_argument("--category", default="pictures", choices=['all', 'pictures', 'faces', 'characters', 'tilesets', 'animations', 'battlebacks1', 'battlebacks2', 'titles1', 'titles2', 'system'])
    parser.add_argument("--mode", default="native2x", choices=['native2x', 'native4x', 'ssaa'], help="Upscaling strategy (default: native2x)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of files to process")
    parser.add_argument("--force", action="store_true", help="Force re-process completed files")
    parser.add_argument("--tile-size", type=int, default=512, help="Tile size for inference (default: 512)")
    parser.add_argument("--tile-pad", type=int, default=16, help="Tile overlap padding (default: 16)")
    parser.add_argument("--device-id", type=int, default=0, help="DirectML Device ID")
    parser.add_argument("--model-path", default=None, help="Path to Real-ESRGAN ONNX weights")
    args = parser.parse_args()

    run_batch_upscale(
        game_dir=args.game_dir,
        category=args.category,
        mode=args.mode,
        limit=args.limit,
        force=args.force,
        tile_size=args.tile_size,
        tile_pad=args.tile_pad,
        device_id=args.device_id,
        model_path=args.model_path
    )
