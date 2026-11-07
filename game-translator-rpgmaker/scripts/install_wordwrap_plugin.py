#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RPG Maker AutoWordWrap Plugin Installer
Injects and activates the AutoWordWrap.js plugin in RPG Maker MV/MZ games
to ensure Vietnamese text never overflows the dialogue window or gets truncated.
"""

import os
import sys
import json
import re
import shutil
import argparse
from pathlib import Path

# Ensure utf-8 stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def find_plugin_paths(game_dir: str) -> tuple[str, str] | None:
    """Finds plugins.js and plugins directory for MV or MZ."""
    if not game_dir or not os.path.isdir(game_dir):
        return None

    candidates = [
        (os.path.join(game_dir, "www", "js", "plugins.js"), os.path.join(game_dir, "www", "js", "plugins")),
        (os.path.join(game_dir, "js", "plugins.js"), os.path.join(game_dir, "js", "plugins")),
    ]

    for p_js, p_dir in candidates:
        if os.path.isfile(p_js) and os.path.isdir(p_dir):
            return p_js, p_dir

    # Search recursively for plugins.js
    for root, dirs, files in os.walk(game_dir):
        if "plugins.js" in files and os.path.basename(root).lower() == "js":
            p_js = os.path.join(root, "plugins.js")
            p_dir = os.path.join(root, "plugins")
            if os.path.isdir(p_dir):
                return p_js, p_dir
        if root[len(game_dir):].count(os.sep) > 3:
            del dirs[:]

    return None


def parse_plugins_json(content: str):
    """Safely extracts JSON array from var $plugins = [...];"""
    match = re.search(r'var\s+\$plugins\s*=\s*(\[.*?\])\s*;?\s*$', content, re.DOTALL)
    if not match:
        return None
    json_str = match.group(1)
    try:
        data = json.loads(json_str)
        return match.start(1), match.end(1), data
    except Exception:
        # Fallback heuristic if trailing commas
        cleaned = re.sub(r',\s*([\]\}])', r'\1', json_str)
        try:
            data = json.loads(cleaned)
            return match.start(1), match.end(1), data
        except Exception:
            return None


def install_plugin(game_dir: str, enable: bool = True) -> bool:
    """Installs AutoWordWrap.js and registers it in plugins.js."""
    paths = find_plugin_paths(game_dir)
    if not paths:
        print(f"Error: Could not locate RPG Maker MV/MZ js/plugins structure in: {game_dir}")
        return False

    plugins_js, plugins_dir = paths
    plugin_dest = os.path.join(plugins_dir, "AutoWordWrap.js")

    # Locate template AutoWordWrap.js
    template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates", "AutoWordWrap.js")

    if enable:
        if not os.path.isfile(template_path):
            print(f"Error: Template AutoWordWrap.js not found at: {template_path}")
            return False

        os.makedirs(plugins_dir, exist_ok=True)
        shutil.copyfile(template_path, plugin_dest)
        print(f"[WordWrap] Copied plugin to: {plugin_dest}")

        with open(plugins_js, "r", encoding="utf-8") as f:
            content = f.read()

        parsed = parse_plugins_json(content)
        if not parsed:
            print(f"Error: Could not parse {plugins_js}")
            return False

        start_idx, end_idx, plugin_array = parsed
        found = False
        for p in plugin_array:
            if isinstance(p, dict) and p.get("name") == "AutoWordWrap":
                p["status"] = True
                found = True
                break

        if not found:
            plugin_array.append({
                "name": "AutoWordWrap",
                "status": True,
                "description": "Smart Auto Word Wrap & Auto-Shrink for Vietnamese & long text",
                "parameters": {}
            })

        new_json = json.dumps(plugin_array, ensure_ascii=False, indent=2)
        new_content = content[:start_idx] + new_json + content[end_idx:]

        with open(plugins_js, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"[WordWrap] Successfully registered and enabled AutoWordWrap in: {plugins_js}")
        return True
    else:
        # Disable plugin
        if os.path.isfile(plugins_js):
            with open(plugins_js, "r", encoding="utf-8") as f:
                content = f.read()
            parsed = parse_plugins_json(content)
            if parsed:
                start_idx, end_idx, plugin_array = parsed
                for p in plugin_array:
                    if isinstance(p, dict) and p.get("name") == "AutoWordWrap":
                        p["status"] = False
                new_json = json.dumps(plugin_array, ensure_ascii=False, indent=2)
                new_content = content[:start_idx] + new_json + content[end_idx:]
                with open(plugins_js, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"[WordWrap] Disabled AutoWordWrap in: {plugins_js}")
        return True


def main():
    parser = argparse.ArgumentParser(description="Install or manage AutoWordWrap plugin for RPG Maker MV/MZ.")
    parser.add_argument("game_dir", help="Path to RPG Maker game root")
    parser.add_argument("--disable", action="store_true", help="Disable the plugin")
    args = parser.parse_args()

    game_dir = os.path.abspath(args.game_dir)
    install_plugin(game_dir, enable=not args.disable)


if __name__ == "__main__":
    main()
