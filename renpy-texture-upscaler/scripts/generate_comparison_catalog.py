#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Before / After Visual Comparison Catalog Generator
Creates side-by-side visual comparisons and an interactive Markdown/HTML catalog
to inspect upscale quality and verify that character portraits and texture atlases
remain complete, crisp, and properly aligned.
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
import cv2
import numpy as np

def create_side_by_side_image(orig_path, up_path, out_path, label_left="BEFORE (Original)", label_right="AFTER (GPU AI)"):
    img_orig = cv2.imread(str(orig_path), cv2.IMREAD_UNCHANGED)
    img_up = cv2.imread(str(up_path), cv2.IMREAD_UNCHANGED)

    if img_orig is None or img_up is None:
        return False

    # Convert RGBA to BGR on dark background for consistent presentation
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

    h_target = 720
    # Resize both for equal vertical comparison
    w_orig = int(bgr_orig.shape[1] * (h_target / bgr_orig.shape[0]))
    w_up = int(bgr_up.shape[1] * (h_target / bgr_up.shape[0]))

    disp_orig = cv2.resize(bgr_orig, (w_orig, h_target), interpolation=cv2.INTER_NEAREST)
    disp_up = cv2.resize(bgr_up, (w_up, h_target), interpolation=cv2.INTER_LANCZOS4)

    # Add divider line
    divider = np.zeros((h_target, 6, 3), dtype=np.uint8) + 80
    combined = np.hstack([disp_orig, divider, disp_up])

    # Add Top Banner
    banner_h = 48
    canvas = np.zeros((h_target + banner_h, combined.shape[1], 3), dtype=np.uint8) + 20
    canvas[banner_h:, :] = combined

    # Text overlays
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(canvas, f"{label_left} [{img_orig.shape[1]}x{img_orig.shape[0]}]", (20, 32), font, 0.7, (180, 180, 180), 2, cv2.LINE_AA)
    cv2.putText(canvas, f"{label_right} [{img_up.shape[1]}x{img_up.shape[0]}]", (w_orig + 26, 32), font, 0.7, (80, 220, 120), 2, cv2.LINE_AA)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), canvas, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return True

def generate_catalog(status_file='upscale_workspace/status.json', backup_dir='backup_textures/original_textures', out_dir='upscale_workspace/catalog'):
    if not os.path.exists(status_file):
        print(f"Status file not found: {status_file}")
        return

    with open(status_file, 'r', encoding='utf-8') as f:
        status = json.load(f)

    catalog_path = Path(out_dir)
    catalog_path.mkdir(parents=True, exist_ok=True)
    comp_images_dir = catalog_path / 'comparisons'
    comp_images_dir.mkdir(parents=True, exist_ok=True)

    items = [v for v in status.values() if v.get('status') == 'completed']
    print(f"Generating Before/After Catalog for {len(items)} upscaled assets...")

    md_lines = [
        "# Visual Before / After Catalog (Ren'Py Texture Upscaling)",
        "",
        "> [!IMPORTANT]",
        f"> **Total Upscaled Assets**: {len(items)} files",
        "> **Engine**: Real-ESRGAN Anime 6B + DirectML Hardware Acceleration",
        "",
        "## Summary Progress Table",
        "| Asset Path | Category | Strategy | Original Size | Upscaled Size | Elapsed |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for item in items:
        rel = item['rel_path']
        cat = item.get('category', 'unknown')
        strat = item.get('strategy', 'native')
        orig = f"{item['orig_size'][0]}x{item['orig_size'][1]}"
        up = f"{item['upscaled_size'][0]}x{item['upscaled_size'][1]}"
        sec = f"{item.get('elapsed_sec', 0)}s"
        md_lines.append(f"| `{rel}` | {cat} | {strat} | `{orig}` | **`{up}`** | `{sec}` |")

    md_lines.append("\n---\n")
    md_lines.append("## Before vs After Visual Comparisons\n")

    for idx, item in enumerate(items, 1):
        rel = item['rel_path']
        safe_name = rel.replace('/', '__').replace('\\', '__')
        orig_img_path = Path(backup_dir) / safe_name
        up_img_path = Path(item.get('workspace_path', ''))

        if not orig_img_path.exists() or not up_img_path.exists():
            continue

        comp_filename = f"comp_{Path(safe_name).stem}.jpg"
        comp_dest = comp_images_dir / comp_filename

        created = create_side_by_side_image(
            orig_img_path,
            up_img_path,
            comp_dest,
            label_left=f"ORIGINAL ({item['orig_size'][0]}x{item['orig_size'][1]})",
            label_right=f"AI UPSCALE ({item['upscaled_size'][0]}x{item['upscaled_size'][1]})"
        )

        if created:
            md_lines.append(f"### {idx}. `{rel}`")
            md_lines.append(f"- **Category**: `{item.get('category')}` | **Strategy**: `{item.get('strategy')}`")
            md_lines.append(f"- **GPU Time**: `{item.get('elapsed_sec', 0)}s` on `{item.get('provider', 'GPU')}`")
            md_lines.append(f"\n![Comparison {idx}]({comp_dest.as_posix()})\n")
            md_lines.append("---\n")

    md_out_path = catalog_path / 'upscale_catalog.md'
    with open(md_out_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))

    print(f"Catalog successfully generated: {md_out_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate Before/After visual catalog.")
    parser.add_argument('--status', default='upscale_workspace/status.json', help="Path to status.json")
    parser.add_argument('--backup-dir', default='backup_textures/original_textures', help="Directory of original textures")
    parser.add_argument('--out-dir', default='upscale_workspace/catalog', help="Catalog output directory")
    args = parser.parse_args()

    generate_catalog(args.status, args.backup_dir, args.out_dir)

