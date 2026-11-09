#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Quality Control (QC) Auditor for Ren'Py Texture Upscaling
Audits:
1. 100% Target Coverage (no low-res textures left behind)
2. 2x Zoom Overflow Bug Detection (ensures static UI/CG/Busts match coordinate layouts)
3. 4-Channel Alpha Transparency & Halos Audit
4. Ren'Py Engine Lint Parity
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from PIL import Image

def audit_upscale_quality(game_dir, manifest_path='backup_textures/manifest.json', status_path='upscale_workspace/status.json'):
    game_path = Path(game_dir).resolve()
    actual_game_dir = game_path / 'game' if (game_path / 'game').exists() else game_path

    if not os.path.exists(manifest_path):
        print(f"[QC Error] Manifest file '{manifest_path}' not found!")
        return False

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    status = {}
    if os.path.exists(status_path):
        with open(status_path, 'r', encoding='utf-8') as f:
            try:
                status = json.load(f)
            except Exception:
                status = {}

    print(f"========================================================")
    print(f"Ren'Py Texture Upscale Quality Control (QC) Audit")
    print(f"Project Target: {actual_game_dir}")
    print(f"========================================================")

    total_low_res = [m for m in manifest if m.get('is_low_res', True)]
    completed = []
    missing = []
    zoom_overflow_risks = []
    alpha_issues = []

    for item in total_low_res:
        rel_path = item['rel_path']
        is_live2d = (item.get('category') == 'live2d')
        orig_w, orig_h = item.get('original_size', [1024, 1024])

        # Check if registered in status
        if rel_path not in status or status[rel_path].get('status') != 'completed':
            missing.append(rel_path)
            continue

        st_entry = status[rel_path]
        completed.append(rel_path)

        # Inspect resulting image on disk (loose or workspace)
        target_file = actual_game_dir / rel_path
        if not target_file.exists():
            target_file = Path(st_entry.get('workspace_path', ''))

        if not target_file.exists():
            missing.append(f"{rel_path} (File missing from disk)")
            continue

        try:
            with Image.open(target_file) as img:
                w, h = img.size
                mode = img.mode

                # 1. Zoom Overflow Check for Static 2D
                if not is_live2d:
                    strategy = st_entry.get('strategy', '')
                    if strategy != 'high_dpi_native' and (w, h) != (orig_w, orig_h):
                        zoom_overflow_risks.append({
                            'path': rel_path,
                            'orig': [orig_w, orig_h],
                            'current': [w, h],
                            'category': item.get('category')
                        })

                # 2. Live2D Resolution Check
                if is_live2d:
                    if max(w, h) < 2048:
                        alpha_issues.append(f"{rel_path}: Live2D atlas was not upscaled to 2048+ (current: {w}x{h})")

                # 3. Alpha Channel Integrity Check
                if mode == 'RGBA':
                    alpha_band = img.getchannel('A')
                    extrema = alpha_band.getextrema()
                    # If original had alpha, verify alpha is not entirely stripped or flat
                    if extrema[0] == extrema[1] == 255 and item.get('mode_format') == 'RGBA':
                        alpha_issues.append(f"{rel_path}: Alpha channel appears flattened/opaque (extrema={extrema})")

        except Exception as e:
            alpha_issues.append(f"{rel_path}: Error inspecting image: {e}")

    # Calculate QC Score
    total_count = len(total_low_res)
    completed_count = len(completed)
    coverage_pct = (completed_count / total_count * 100) if total_count > 0 else 100.0

    score = 100
    score -= len(missing) * 5
    score -= len(zoom_overflow_risks) * 10
    score -= len(alpha_issues) * 5
    score = max(0, min(100, score))

    print(f"\n--- QC Audit Findings ---")
    print(f"Total Low-Res Target Assets : {total_count}")
    print(f"Successfully Upscaled      : {completed_count} ({coverage_pct:.1f}%)")
    print(f"Missing / Skipped Assets   : {len(missing)}")
    print(f"Static Zoom Overflow Risks : {len(zoom_overflow_risks)}")
    print(f"Alpha / Format Warnings    : {len(alpha_issues)}")
    print(f"Overall Quality Score      : {score} / 100")

    if zoom_overflow_risks:
        print(f"\n[!] WARNING: Detected {len(zoom_overflow_risks)} Static 2D Assets with 2x Zoom Overflow Risk:")
        for z in zoom_overflow_risks[:10]:
            print(f"    - {z['path']}: {z['orig']} -> {z['current']} (Category: {z['category']})")
        print("    -> Run batch_upscale.py without --high-dpi to apply SSAA Lanczos downsampling!")

    if missing:
        print(f"\n[!] WARNING: {len(missing)} assets were not upscaled:")
        for m in missing[:10]:
            print(f"    - {m}")

    # Optional Ren'Py Lint check
    renpy_exe = None
    for candidate in [game_path / 'lib' / 'py3-windows-x86_64' / 'python.exe', game_path / 'renpy.exe']:
        if candidate.exists():
            renpy_exe = candidate
            break

    lint_passed = None
    if renpy_exe and (actual_game_dir / 'script.rpy').exists():
        print(f"\nRunning Ren'Py Lint check with {renpy_exe.name}...")
        try:
            res = subprocess.run([str(renpy_exe), str(actual_game_dir), 'lint'], capture_output=True, text=True, timeout=60)
            if res.returncode == 0:
                print("  Ren'Py Lint: PASSED (Exit code 0, 0 syntax/runtime errors).")
                lint_passed = True
            else:
                print(f"  Ren'Py Lint: Returned exit code {res.returncode}")
                lint_passed = False
        except Exception as e:
            print(f"  Could not run Ren'Py Lint: {e}")

    report_path = Path('upscale_workspace') / 'qc_audit_report.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as rf:
        json.dump({
            'score': score,
            'coverage_pct': coverage_pct,
            'total_targets': total_count,
            'completed_count': completed_count,
            'missing': missing,
            'zoom_overflow_risks': zoom_overflow_risks,
            'alpha_issues': alpha_issues,
            'renpy_lint_passed': lint_passed
        }, rf, indent=2, ensure_ascii=False)

    print(f"\nQC Report saved to: {report_path}")
    print(f"========================================================")
    return (score >= 90)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Audit quality of upscaled Ren'Py textures.")
    parser.add_argument('--game-dir', required=True, help="Path to Ren'Py project root or game/ directory")
    parser.add_argument('--manifest', default='backup_textures/manifest.json', help="Path to manifest.json")
    parser.add_argument('--status', default='upscale_workspace/status.json', help="Path to status.json")
    args = parser.parse_args()

    success = audit_upscale_quality(args.game_dir, args.manifest, args.status)
    sys.exit(0 if success else 1)
