#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unity Engine & Modding Architecture Profiler
Detects Unity version, Mono (.NET) vs IL2CPP (64-bit native),
existing mod loaders (BepInEx, MelonLoader), and TextMeshPro assets.
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Ensure utf-8 stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def profile_unity_game(game_dir: Path) -> dict:
    unity_player = game_dir / "UnityPlayer.dll"
    game_assembly = game_dir / "GameAssembly.dll"
    
    data_dirs = [d for d in game_dir.iterdir() if d.is_dir() and d.name.endswith("_Data")]
    data_dir = data_dirs[0] if data_dirs else None

    is_il2cpp = game_assembly.is_file()
    is_mono = False
    managed_dir = None

    if data_dir:
        cand_managed = data_dir / "Managed"
        if cand_managed.is_dir() and (cand_managed / "Assembly-CSharp.dll").is_file():
            is_mono = True
            managed_dir = str(cand_managed)

    # Mod loaders
    has_bepinex = (game_dir / "BepInEx").is_dir()
    bepinex_version = "Unknown"
    if has_bepinex:
        core_dir = game_dir / "BepInEx" / "core"
        if (core_dir / "BepInEx.IL2CPP.dll").is_file() or is_il2cpp:
            bepinex_version = "BepInEx 6 (IL2CPP)"
        else:
            bepinex_version = "BepInEx 5 (Mono)"

    has_melon = (game_dir / "MelonLoader").is_dir()

    # Asset files check
    assets_files = list(data_dir.glob("*.assets")) if data_dir else []

    return {
        "engine": "unity",
        "game_directory": str(game_dir),
        "data_directory": data_dir.name if data_dir else None,
        "is_il2cpp": is_il2cpp,
        "is_mono": is_mono,
        "architecture": "IL2CPP (Native C++)" if is_il2cpp else ("Mono (.NET Managed)" if is_mono else "Unknown"),
        "mod_loader": bepinex_version if has_bepinex else ("MelonLoader" if has_melon else "None"),
        "has_bepinex": has_bepinex,
        "has_melonloader": has_melon,
        "asset_files_count": len(assets_files),
        "recommended_hook_method": "BepInEx 6 IL2CPP Detour Plugin" if is_il2cpp else "BepInEx 5 Harmony Hook / Mono Injection"
    }


def main():
    parser = argparse.ArgumentParser(description="Profile Unity game architecture.")
    parser.add_argument("game_dir", help="Path to Unity game directory")
    parser.add_argument("--json", action="store_true", help="Output pure JSON")
    args = parser.parse_args()

    target = Path(args.game_dir).resolve()
    if not target.is_dir():
        print(f"❌ Error: Directory not found: {target}")
        sys.exit(1)

    profile = profile_unity_game(target)

    if args.json:
        print(json.dumps(profile, indent=2, ensure_ascii=False))
        return

    print("=" * 60)
    print("🎮 UNITY ARCHITECTURE PROFILE")
    print(f"📂 Path: {profile['game_directory']}")
    print(f"⚙️ Architecture: {profile['architecture']}")
    print(f"📦 Data Folder: {profile['data_directory']}")
    print(f"🔌 Mod Loader: {profile['mod_loader']}")
    print(f"🛠️ Recommended Strategy: {profile['recommended_hook_method']}")
    print("=" * 60)


if __name__ == "__main__":
    main()

