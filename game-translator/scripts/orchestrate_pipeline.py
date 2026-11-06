#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Master Game Localization Pipeline Orchestrator
Coordinates the entire translation lifecycle:
1. Engine fingerprinting and classification
2. Project workspace initialization
3. Lore reconnaissance setup (LORE_CONTEXT.json)
4. Translatable string extraction (engine-specific)
5. Slicing into batches for subagents
6. Status reporting & next-step instructions
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

# Ensure utf-8 stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def run_cmd(cmd: list[str]) -> tuple[int, str]:
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return res.returncode, res.stdout + ("\n" + res.stderr if res.stderr else "")


def orchestrate(game_path_str: str, project_name: str | None = None, chunk_size: int = 250) -> dict:
    game_path = Path(game_path_str).resolve()
    if not game_path.exists():
        return {"status": "error", "message": f"Path not found: {game_path}"}

    title = project_name or game_path.name
    print("=" * 70)
    print(f"🚀 INITIALIZING GAME LOCALIZATION PIPELINE: {title}")
    print(f"📂 Game Directory: {game_path}")
    print("=" * 70)

    # 1. Detect Engine
    print("\n[Phase 1] 🔍 Detecting Engine Architecture...")
    detect_script = ROOT_DIR / "game-translator" / "scripts" / "detect_engine.py"
    code, out = run_cmd([sys.executable, str(detect_script), str(game_path), "--json"])
    if code != 0:
        return {"status": "error", "message": f"Detection failed: {out}"}

    engine_info = json.loads(out)
    engine = engine_info.get("engine")
    print(f"   -> Detected: {engine_info.get('name')} (Engine ID: {engine})")
    print(f"   -> Confidence: {engine_info.get('confidence') * 100:.0f}%")

    # 2. Setup Project Workspace
    work_dir = game_path / "localization_workspace"
    work_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n[Phase 2] 📁 Initialized Workspace: {work_dir}")

    # 3. Lore Reconnaissance
    print("\n[Phase 3] 🌐 Setting up Lore & Context Reconnaissance...")
    lore_script = ROOT_DIR / "game-translator" / "scripts" / "search_game_lore.py"
    lore_file = work_dir / "LORE_CONTEXT.json"
    run_cmd([sys.executable, str(lore_script), title, "--out", str(lore_file)])
    print(f"   -> Lore configuration template ready: {lore_file.name}")

    # 4. Engine-specific String Extraction & Setup
    print(f"\n[Phase 4] ⚙️ Executing {engine.upper()} Extraction Workflow...")
    extracted_strings_file = work_dir / "raw_extracted_strings.json"

    if engine == "renpy":
        # Ren'Py pipeline
        extract_py_script = ROOT_DIR / "game-translator-renpy" / "scripts" / "extract_python_strings.py"
        run_cmd([sys.executable, str(extract_py_script), str(game_path), "--out", str(extracted_strings_file)])
        
        # Setup tl framework
        tl_script = ROOT_DIR / "game-translator-renpy" / "scripts" / "generate_tl_framework.py"
        run_cmd([sys.executable, str(tl_script), str(game_path)])
        print(f"   -> Ren'Py tl/vietnamese/ framework and language switcher injected.")

    elif engine == "unity":
        # Unity pipeline
        profile_script = ROOT_DIR / "game-translator-unity" / "scripts" / "detect_unity_type.py"
        _, prof_out = run_cmd([sys.executable, str(profile_script), str(game_path), "--json"])
        try:
            profile = json.loads(prof_out)
            print(f"   -> Unity Type: {profile.get('architecture')} | Mod Loader: {profile.get('mod_loader')}")
        except Exception:
            pass

    # 5. Summary & Next Steps
    report = {
        "status": "success",
        "title": title,
        "engine": engine,
        "engine_info": engine_info,
        "workspace": str(work_dir),
        "lore_file": str(lore_file),
        "extracted_strings_file": str(extracted_strings_file) if extracted_strings_file.exists() else None
    }

    report_file = work_dir / "pipeline_status.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("✨ PIPELINE ORCHESTRATION BOOTSTRAP COMPLETE!")
    print(f"📄 Status Report: {report_file}")
    print("\n👉 NEXT ACTIONS FOR SUBAGENTS:")
    print("   1. 'game-lore-researcher' -> Populate character matrix in LORE_CONTEXT.json")
    print("   2. 'game-glossary-curator' -> Lock terms in GLOSSARY.json")
    print("   3. 'game-chunk-translator' -> Begin batch translation of extracted strings")
    print("=" * 70)

    return report


def main():
    parser = argparse.ArgumentParser(description="Master Game Localization Orchestrator.")
    parser.add_argument("game_path", help="Path to game directory")
    parser.add_argument("--name", "-n", help="Project / Game Title")
    parser.add_argument("--chunk-size", "-s", type=int, default=250, help="Chunk size for parallel workers")
    args = parser.parse_args()

    orchestrate(args.game_path, args.name, args.chunk_size)


if __name__ == "__main__":
    main()
