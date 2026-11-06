#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Game Engine Fingerprinter & Classifier
Detects the game engine, architecture (Mono vs IL2CPP, Python 2 vs 3),
and recommends the appropriate game-translator sub-skill.
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


def detect_renpy(game_path: Path) -> dict | None:
    has_renpy_dir = (game_path / "renpy").is_dir()
    game_dir = game_path / "game"
    has_game_dir = game_dir.is_dir()

    rpa_files = list(game_dir.glob("*.rpa")) if has_game_dir else []
    rpyc_files = list(game_dir.glob("*.rpyc")) if has_game_dir else []
    rpy_files = list(game_dir.glob("*.rpy")) if has_game_dir else []

    py_libs = list((game_path / "lib").glob("py*")) if (game_path / "lib").is_dir() else []

    python_version = "Unknown"
    for lib in py_libs:
        name = lib.name.lower()
        if "py3" in name:
            python_version = "Python 3"
            break
        elif "py2" in name:
            python_version = "Python 2"
            break

    if has_renpy_dir or rpa_files or rpyc_files or (has_game_dir and py_libs):
        return {
            "engine": "renpy",
            "name": "Ren'Py Visual Novel Engine",
            "python_runtime": python_version,
            "has_rpa": len(rpa_files) > 0,
            "rpa_count": len(rpa_files),
            "rpa_files": [f.name for f in rpa_files],
            "rpyc_count": len(rpyc_files),
            "recommended_skill": "game-translator-renpy",
            "confidence": 0.99 if (has_renpy_dir and has_game_dir) else 0.85
        }
    return None


def detect_unity(game_path: Path) -> dict | None:
    unity_player = list(game_path.glob("UnityPlayer.dll"))
    game_assembly = list(game_path.glob("GameAssembly.dll"))
    crash_handler = list(game_path.glob("UnityCrashHandler*.exe"))
    
    # Check for Data folder
    data_dirs = [d for d in game_path.iterdir() if d.is_dir() and d.name.endswith("_Data")]
    
    is_il2cpp = len(game_assembly) > 0
    is_mono = False
    mono_managed_dir = None

    if data_dirs:
        managed = data_dirs[0] / "Managed"
        if managed.is_dir() and (managed / "Assembly-CSharp.dll").is_file():
            is_mono = True
            mono_managed_dir = str(managed)

    # Check for existing BepInEx or mod loader
    bepinex_dir = game_path / "BepInEx"
    has_bepinex = bepinex_dir.is_dir()

    if unity_player or data_dirs or is_il2cpp or crash_handler:
        arch = "IL2CPP (64-bit Native)" if is_il2cpp else ("Mono (.NET Managed)" if is_mono else "Unity Unknown")
        return {
            "engine": "unity",
            "name": "Unity Engine",
            "architecture": arch,
            "is_il2cpp": is_il2cpp,
            "is_mono": is_mono,
            "data_directory": data_dirs[0].name if data_dirs else None,
            "has_bepinex": has_bepinex,
            "recommended_skill": "game-translator-unity",
            "confidence": 0.99 if (unity_player and data_dirs) else 0.80
        }
    return None


def detect_rpgmaker(game_path: Path) -> dict | None:
    package_json = game_path / "package.json"
    www_dir = game_path / "www"
    game_exe = game_path / "Game.exe"

    # MV / MZ
    if package_json.is_file():
        try:
            with open(package_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "main" in data and ("index.html" in data["main"] or "www" in data["main"]):
                    is_mz = (game_path / "rmmz_core.js").is_file() or (game_path / "js" / "rmmz_core.js").is_file()
                    return {
                        "engine": "rpgmaker",
                        "name": "RPG Maker MZ" if is_mz else "RPG Maker MV",
                        "type": "JavaScript / NW.js",
                        "recommended_skill": "game-translator-rpgmaker",
                        "confidence": 0.95
                    }
        except Exception:
            pass

    # VX Ace / XP
    rgss3a = list(game_path.glob("*.rgss3a"))
    rgssad = list(game_path.glob("*.rgssad"))
    if rgss3a or rgssad or (game_exe.is_file() and (game_path / "Data").is_dir()):
        return {
            "engine": "rpgmaker",
            "name": "RPG Maker VX Ace / XP",
            "type": "Ruby / RGSS",
            "recommended_skill": "game-translator-rpgmaker",
            "confidence": 0.90
        }
    return None


def detect_unreal(game_path: Path) -> dict | None:
    pak_files = list(game_path.rglob("*.pak"))
    engine_dir = game_path / "Engine"
    if pak_files or engine_dir.is_dir():
        return {
            "engine": "unreal",
            "name": "Unreal Engine",
            "pak_count": len(pak_files),
            "recommended_skill": "game-translator-unreal",
            "confidence": 0.85
        }
    return None


def detect_godot(game_path: Path) -> dict | None:
    pck_files = list(game_path.glob("*.pck"))
    if pck_files:
        return {
            "engine": "godot",
            "name": "Godot Engine",
            "pck_file": pck_files[0].name,
            "recommended_skill": "game-translator-godot",
            "confidence": 0.90
        }
    return None


def classify_game(path_str: str) -> dict:
    target_path = Path(path_str).resolve()
    if not target_path.exists():
        return {"status": "error", "message": f"Path not found: {target_path}"}

    # Order of checks
    detectors = [detect_renpy, detect_unity, detect_rpgmaker, detect_godot, detect_unreal]

    for detector in detectors:
        res = detector(target_path)
        if res:
            res["status"] = "success"
            res["target_path"] = str(target_path)
            return res

    return {
        "status": "unknown",
        "message": "Engine signature could not be identified automatically.",
        "target_path": str(target_path),
        "recommended_skill": "manual_inspection"
    }


def main():
    parser = argparse.ArgumentParser(description="Detect game engine and output translation metadata.")
    parser.add_argument("path", help="Path to the game directory")
    parser.add_argument("--json", action="store_true", help="Output pure JSON")
    args = parser.parse_args()

    result = classify_game(args.path)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("=" * 60)
        print(f"🎯 GAME ENGINE DETECTION REPORT")
        print(f"📂 Path: {result.get('target_path', args.path)}")
        if result["status"] == "success":
            print(f"🎮 Engine: {result['name']} ({result['engine']})")
            print(f"🛠️ Recommended Sub-Skill: {result['recommended_skill']}")
            for k, v in result.items():
                if k not in ["status", "target_path", "name", "engine", "recommended_skill"]:
                    print(f"   - {k}: {v}")
        else:
            print(f"⚠️ {result.get('message')}")
        print("=" * 60)


if __name__ == "__main__":
    main()

