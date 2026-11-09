#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Before / After Visual Comparison Catalog Generator for RPG Maker MV/MZ
Creates side-by-side visual comparisons directly decrypting .rpgmvp files
to verify that illustrations and sprites are razor-sharp without pixelation artifacts.
"""

import os
import sys
import json
import argparse
from pathlib import Path
import cv2
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rpgmv_crypto import RPGMVCrypto

def create_side_by_side_image(img_orig, img_up, out_path, label_left="BEFORE (Original)", label_right="AFTER (Native 2x)"):
    if img_orig is None or img_up is None:
        return False

    def to_bgr(im):
        if len(im.shape) > 2 and im.shape[2] == 4:
            b, g, r, a = cv2.split(im)
            alpha = a.astype(float) / 255.0
            bg = np.zeros_like(b, dtype=float) + 30 # Dark gray background
            b_out = (b.astype(float) * alpha + bg * (1 - alpha)).astype(np.uint8)
            g_out = (g.astype(float) * alpha + bg * (1 - alpha)).astype(np.uint8)
            r_out = (r.astype(float) * alpha + bg * (1 - alpha)).astype(np.uint8)
            return cv2.merge([b_out, g_out, r_out])
        return im

    bgr_orig = to_bgr(img_orig)
    bgr_up = to_bgr(img_up)

    h_target = 600
    w_orig = int(bgr_orig.shape[1] * (h_target / bgr_orig.shape[0]))
    w_up = int(bgr_up.shape[1] * (h_target / bgr_up.shape[0]))

    disp_orig = cv2.resize(bgr_orig, (w_orig, h_target), interpolation=cv2.INTER_NEAREST)
    disp_up = cv2.resize(bgr_up, (w_up, h_target), interpolation=cv2.INTER_LANCZOS4)

    divider = np.zeros((h_target, 6, 3), dtype=np.uint8) + 80
    combined = np.hstack([disp_orig, divider, disp_up])

    banner_h = 48
    canvas = np.zeros((h_target + banner_h, combined.shape[1], 3), dtype=np.uint8) + 20
    canvas[banner_h:, :] = combined

    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(canvas, f"{label_left} [{img_orig.shape[1]}x{img_orig.shape[0]}]", (20, 32), font, 0.65, (180, 180, 180), 2, cv2.LINE_AA)
    cv2.putText(canvas, f"{label_right} [{img_up.shape[1]}x{img_up.shape[0]}]", (w_orig + 26, 32), font, 0.65, (80, 220, 120), 2, cv2.LINE_AA)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), canvas, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return True

def generate_catalog(game_root=".", samples=5):
    game_path = Path(game_root).resolve()
    backup_root = game_path / "backup_textures"
    orig_backup_dir = backup_root / "original_textures"
    manifest_path = backup_root / "manifest.json"
    status_path = backup_root / "status.json"
    catalog_dir = backup_root / "catalog"
    comp_images_dir = catalog_dir / "comparisons"

    if not status_path.exists():
        print(f"[Catalog] status.json not found: {status_path}")
        return False

    with open(status_path, 'r', encoding='utf-8') as sf:
        status = json.load(sf)

    crypto = RPGMVCrypto(game_root=str(game_path))
    processed = status.get("processed", {})
    if not processed:
        print("[Catalog] No processed assets found in status.json.")
        return False

    catalog_dir.mkdir(parents=True, exist_ok=True)
    comp_images_dir.mkdir(parents=True, exist_ok=True)

    items = list(processed.items())
    if samples and samples > 0:
        items = items[:samples]

    md_lines = [
        "# RPG Maker MV/MZ Texture Upscale Before / After Catalog",
        "",
        "> [!IMPORTANT]",
        f"> **Total Processed Assets**: {len(processed)} files",
        "> **Strategy**: Native 2x Super-Resolution + WebGL High-DPI Canvas",
        "",
        "## Summary Progress Table",
        "| Asset Path | Category | Strategy | Original Size | Upscaled Size | Elapsed |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for rel_path, data in processed.items():
        cat = data.get("category", "")
        mode = data.get("mode", "native2x")
        orig_s = data.get("orig_size", "")
        new_s = data.get("new_size", "")
        sec = f"{data.get('duration_sec', 0)}s"
        md_lines.append(f"| `{rel_path}` | {cat} | {mode} | `{orig_s}` | **`{new_s}`** | `{sec}` |")

    md_lines.append("\n---\n")
    md_lines.append("## Before vs After Visual Comparisons\n")

    for idx, (rel_path, data) in enumerate(items, 1):
        orig_file = orig_backup_dir / rel_path
        cur_file = game_path / rel_path

        if not orig_file.exists() or not cur_file.exists():
            continue

        try:
            img_b, _ = crypto.load_image(str(orig_file))
            img_a, _ = crypto.load_image(str(cur_file))
        except Exception:
            continue

        comp_name = f"comp_{idx}_{Path(rel_path).stem}.jpg"
        comp_dest = comp_images_dir / comp_name

        created = create_side_by_side_image(
            img_b, img_a, comp_dest,
            label_left=f"ORIGINAL ({data.get('orig_size')})",
            label_right=f"NATIVE 2X ({data.get('new_size')})"
        )

        if created:
            md_lines.append(f"### {idx}. `{rel_path}`")
            md_lines.append(f"- **Category**: `{data.get('category')}` | **Mode**: `{data.get('mode')}`")
            md_lines.append(f"- **Time**: `{data.get('duration_sec')}s`")
            md_lines.append(f"\n![Comparison {idx}]({comp_dest.as_posix()})\n")
            md_lines.append("---\n")

    md_path = catalog_dir / "upscale_catalog.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))

    print(f"[Catalog SUCCESS] Visual comparison catalog generated at: {md_path}")
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate Before/After catalog for RPG Maker textures.")
    parser.add_argument("--game-dir", default=".", help="Root game directory")
    parser.add_argument("--samples", type=int, default=10, help="Number of image comparisons to generate (default: 10)")
    args = parser.parse_args()

    generate_catalog(args.game_dir, args.samples)
