#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Installer for HD_Texture_Scale.js Plugin in RPG Maker MV/MZ
Copies plugin to js/plugins and registers/activates in plugins.js.
"""

import os
import sys
import shutil
import re
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR.parent / "templates" / "HD_Texture_Scale.js"

def find_plugins_dir(game_root):
    candidates = [
        os.path.join(game_root, "www", "js", "plugins"),
        os.path.join(game_root, "js", "plugins")
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.isdir(c):
            return c
    return None

def find_plugins_js(game_root):
    candidates = [
        os.path.join(game_root, "www", "js", "plugins.js"),
        os.path.join(game_root, "js", "plugins.js")
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

def install_plugin(game_root="."):
    game_path = Path(game_root).resolve()
    plugins_dir = find_plugins_dir(str(game_path))
    plugins_js_path = find_plugins_js(str(game_path))

    if not plugins_dir or not plugins_js_path:
        raise FileNotFoundError(f"Could not locate plugins directory or plugins.js in: {game_path}")

    # 1. Copy plugin script
    target_plugin_path = os.path.join(plugins_dir, "HD_Texture_Scale.js")
    print(f"[Plugin Installer] Copying {TEMPLATE_PATH.name} to {target_plugin_path}...")
    shutil.copy2(str(TEMPLATE_PATH), target_plugin_path)

    # 2. Backup plugins.js
    backup_js_path = plugins_js_path + ".bak"
    if not os.path.exists(backup_js_path):
        print(f"[Plugin Installer] Backing up plugins.js to {backup_js_path}...")
        shutil.copy2(plugins_js_path, backup_js_path)

    # 3. Read and modify plugins.js
    with open(plugins_js_path, 'r', encoding='utf-8') as f:
        content = f.read()

    plugin_entry = '{"name":"HD_Texture_Scale","status":true,"description":"High-DPI 2x WebGL Canvas & Smart HD Texture Scaler","parameters":{}}'

    if 'HD_Texture_Scale' in content:
        print("[Plugin Installer] HD_Texture_Scale is already registered in plugins.js.")
        # Ensure it is enabled
        content = re.sub(r'\{"name":"HD_Texture_Scale","status":(?:false|true)', '{"name":"HD_Texture_Scale","status":true', content)
        with open(plugins_js_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("[Plugin Installer] Confirmed HD_Texture_Scale status is active (true).")
        return True

    # Find $plugins array
    match = re.search(r'var\s+\$plugins\s*=\s*\[', content)
    if not match:
        print("[Plugin Installer] Warning: Could not find var $plugins = [ in plugins.js.")
        return False

    # Insert entry right after the bracket
    insert_pos = match.end()
    # Check if array is empty
    rest = content[insert_pos:].strip()
    if rest.startswith('];'):
        new_content = content[:insert_pos] + "\n" + plugin_entry + "\n" + content[insert_pos:]
    else:
        new_content = content[:insert_pos] + "\n" + plugin_entry + ",\n" + content[insert_pos:]

    with open(plugins_js_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("[Plugin Installer] Successfully registered and enabled HD_Texture_Scale.js in plugins.js!")
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Install HD_Texture_Scale plugin into RPG Maker game.")
    parser.add_argument("--game-dir", default=".", help="Root game directory")
    args = parser.parse_args()

    install_plugin(args.game_dir)
