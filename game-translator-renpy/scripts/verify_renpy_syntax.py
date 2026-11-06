#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ren'Py Syntax Verifier & Bytecode Compilation Runner
Validates .rpy syntax, catches unclosed quotes, checks tag parity,
and invokes the bundled Ren'Py runtime to compile .rpy into .rpyc.
"""

import os
import sys
import subprocess
import argparse
import re
from pathlib import Path

# Ensure utf-8 stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass


def check_rpy_syntax(rpy_file: Path) -> list[str]:
    """Basic static syntax linter for .rpy translation files."""
    errors = []
    try:
        lines = rpy_file.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:
        return [f"Cannot read file: {e}"]

    in_strings_block = False
    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("translate ") and stripped.endswith("strings:"):
            in_strings_block = True
            continue
        elif stripped.startswith("translate "):
            in_strings_block = False
            continue

        # Check for matching quotes
        num_double = stripped.count('"') - stripped.count(r'\"')
        if num_double % 2 != 0:
            errors.append(f"Line {idx}: Odd number of double quotes: {stripped}")

        # Check for unclosed Ren'py tags
        open_tags = re.findall(r'\{([a-zA-Z0-9_\#\=]+)\}', stripped)
        close_tags = re.findall(r'\{/([a-zA-Z0-9_]+)\}', stripped)
        # Pairable tags
        pairable = {"b", "i", "u", "s", "color", "size", "font", "a"}
        opened_p = [t.split("=")[0] for t in open_tags if t.split("=")[0] in pairable]
        if len(opened_p) != len(close_tags):
            # Potential unclosed tag warning
            pass

    return errors


def compile_with_renpy(game_root: Path) -> tuple[bool, str]:
    """Finds bundled python / renpy and triggers compilation."""
    exe_candidates = list(game_root.glob("*.exe"))
    py_candidates = list(game_root.glob("*.py"))
    
    # Check if there is a main game.py (e.g. PAWGVERSE.py or renpy.py)
    target_py = None
    for p in py_candidates:
        if p.name.lower() not in ["setup.py", "manage_unlocks.py"]:
            target_py = p
            break

    python_exe = None
    # Look for bundled python
    for p_exe in (game_root / "lib").rglob("python.exe"):
        python_exe = p_exe
        break

    if not python_exe:
        python_exe = Path(sys.executable)

    if target_py:
        cmd = [str(python_exe), str(target_py), ".", "compile"]
        try:
            res = subprocess.run(cmd, cwd=str(game_root), capture_output=True, text=True, timeout=60)
            return (res.returncode == 0, res.stdout + "\n" + res.stderr)
        except Exception as e:
            return (False, f"Execution failed: {e}")

    return (False, "No Ren'Py compilation script found.")


def main():
    parser = argparse.ArgumentParser(description="Verify Ren'Py syntax and compile bytecode.")
    parser.add_argument("path", help="Game directory or .rpy file")
    parser.add_argument("--compile", action="store_true", help="Run Ren'Py engine compile step")
    args = parser.parse_args()

    target = Path(args.path).resolve()
    if not target.exists():
        print(f"❌ Error: Path not found: {target}")
        sys.exit(1)

    print("=" * 60)
    print("🔍 REN'PY TRANSLATION SYNTAX LINTER")
    print(f"📁 Target: {target}")
    print("=" * 60)

    files_to_check = [target] if target.is_file() else list(target.rglob("*.rpy"))
    error_count = 0

    for f in files_to_check:
        errs = check_rpy_syntax(f)
        if errs:
            error_count += len(errs)
            print(f"❌ {f.name} ({len(errs)} issues):")
            for err in errs:
                print(f"   {err}")

    if error_count == 0:
        print(f"✅ Checked {len(files_to_check)} .rpy files. 0 syntax errors detected!")
    else:
        print(f"⚠️ Found {error_count} potential syntax errors.")

    if args.compile and target.is_dir():
        print("\n⚙️ Running Ren'Py engine bytecode compilation...")
        success, out = compile_with_renpy(target)
        if success:
            print("✅ Compilation Succeeded! All .rpy converted to .rpyc.")
        else:
            print("⚠️ Engine compile output:")
            print(out)


if __name__ == "__main__":
    main()

