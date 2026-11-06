#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ren'Py Vietnamese Localization Framework Generator
Sets up tl/vietnamese folder, configuration initialization, and language switcher.
"""

import os
import sys
import argparse
from pathlib import Path

# Ensure utf-8 stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

INIT_RPY_TEMPLATE = """# Vietnamese Localization Initialization & Language Enforcer
init -999 python:
    config.language = "vietnamese"
    config.default_language = "vietnamese"

init 999 python:
    def _enforce_vietnamese():
        if _preferences.language is None or _preferences.language == "":
            renpy.change_language("vietnamese", force=True)

    if _enforce_vietnamese not in config.start_callbacks:
        config.start_callbacks.append(_enforce_vietnamese)
    if hasattr(config, "after_load_callbacks") and _enforce_vietnamese not in config.after_load_callbacks:
        config.after_load_callbacks.append(_enforce_vietnamese)
"""

LANGUAGE_TOGGLE_SCREEN = """# Floating Live Language Switcher Screen
screen language_toggle_overlay():
    zorder 1000
    frame:
        xalign 0.98
        yalign 0.02
        background "#000000aa"
        xpadding 10
        ypadding 6
        has hbox:
            spacing 8

        textbutton "🇻🇳 Tiếng Việt":
            action [Language("vietnamese"), SelectedIf(_preferences.language == "vietnamese")]
            text_size 16
            text_selected_color "#ffdd44"
            text_idle_color "#ffffff"

        textbutton "🇬🇧 English":
            action [Language(None), SelectedIf(_preferences.language is None or _preferences.language == "")]
            text_size 16
            text_selected_color "#ffdd44"
            text_idle_color "#ffffff"

init 999 python:
    # Auto-display toggle overlay on main menu and in-game
    config.overlay_screens.append("language_toggle_overlay")
"""


def setup_tl_framework(game_dir: Path):
    tl_vn_dir = game_dir / "tl" / "vietnamese"
    tl_vn_dir.mkdir(parents=True, exist_ok=True)

    common_rpy = tl_vn_dir / "common.rpy"
    if not common_rpy.exists():
        with open(common_rpy, "w", encoding="utf-8") as f:
            f.write("# Vietnamese System and Common UI Strings\ntranslate vietnamese strings:\n    old \"\"\n    new \"\"\n")
        print(f"✅ Created: {common_rpy}")

    init_rpy = game_dir / "vietnamese_init.rpy"
    with open(init_rpy, "w", encoding="utf-8") as f:
        f.write(INIT_RPY_TEMPLATE)
    print(f"✅ Created: {init_rpy}")

    toggle_rpy = game_dir / "language_toggle.rpy"
    with open(toggle_rpy, "w", encoding="utf-8") as f:
        f.write(LANGUAGE_TOGGLE_SCREEN)
    print(f"✅ Created: {toggle_rpy}")


def main():
    parser = argparse.ArgumentParser(description="Initialize Vietnamese localization framework for Ren'Py game.")
    parser.add_argument("game_dir", help="Path to the 'game/' directory")
    args = parser.parse_args()

    target = Path(args.game_dir).resolve()
    if target.name != "game" and (target / "game").is_dir():
        target = target / "game"

    if not target.is_dir():
        print(f"❌ Error: 'game' directory not found at: {target}")
        sys.exit(1)

    print(f"🚀 Setting up Vietnamese localization framework in: {target}")
    setup_tl_framework(target)
    print("✨ Setup complete! Ren'Py will boot directly in Vietnamese.")


if __name__ == "__main__":
    main()

