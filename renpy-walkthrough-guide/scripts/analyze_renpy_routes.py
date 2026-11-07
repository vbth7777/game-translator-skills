#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ren'Py Route & Decision Tree Logic Analyzer
Extracts labels, choices, condition flags, item requirements, and Game Over traps
from .rpy files to ensure walkthroughs are 100% logically authentic without hallucinated steps.
"""

import os
import sys
import re
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


class RouteAnalyzer:
    def __init__(self):
        self.re_label = re.compile(r'^\s*label\s+([a-zA-Z0-9_]+)(?:\s*\((.*?)\))?:\s*$')
        self.re_menu = re.compile(r'^\s*menu(?:\s+([a-zA-Z0-9_]+))?:\s*$')
        self.re_choice = re.compile(r'^\s*["\']([^"\']+)["\'](?:\s+if\s+(.*?))?:\s*$')
        self.re_jump = re.compile(r'^\s*jump\s+([a-zA-Z0-9_]+)\s*$')
        self.re_call = re.compile(r'^\s*call\s+([a-zA-Z0-9_]+)(?:\s*\((.*?)\))?\s*$')
        self.re_var_set = re.compile(r'^\s*\$\s*([a-zA-Z0-9_\.\[\]\"\']+\s*(?:\+=|-=|=)\s*[^#\n]+)')
        self.re_scene = re.compile(r'^\s*scene\s+([a-zA-Z0-9_\s]+)')
        self.re_show = re.compile(r'^\s*show\s+([a-zA-Z0-9_\s]+)')

    def analyze_file(self, file_path: Path) -> dict:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return {}

        lines = content.splitlines()
        labels = {}
        current_label = "__global__"
        labels[current_label] = {
            "file": file_path.name,
            "line": 1,
            "choices": [],
            "jumps": [],
            "calls": [],
            "scenes": [],
            "shows": [],
            "flag_changes": [],
            "game_over_risk": False
        }

        in_menu = False
        current_menu = None

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Check label
            m_lbl = self.re_label.match(line)
            if m_lbl:
                current_label = m_lbl.group(1)
                labels[current_label] = {
                    "file": file_path.name,
                    "line": idx,
                    "choices": [],
                    "jumps": [],
                    "calls": [],
                    "scenes": [],
                    "shows": [],
                    "flag_changes": [],
                    "game_over_risk": False
                }
                in_menu = False
                continue

            # Check scene / show
            m_scene = self.re_scene.match(line)
            if m_scene:
                sc = m_scene.group(1).strip()
                labels[current_label]["scenes"].append({"line": idx, "name": sc})
                if "game_over" in sc.lower() or "dead" in sc.lower():
                    labels[current_label]["game_over_risk"] = True

            m_show = self.re_show.match(line)
            if m_show:
                labels[current_label]["shows"].append({"line": idx, "name": m_show.group(1).strip()})

            # Check menu
            if self.re_menu.match(line):
                in_menu = True
                current_menu = {"line": idx, "options": []}
                labels[current_label]["choices"].append(current_menu)
                continue

            # Check choice inside menu
            if in_menu:
                m_choice = self.re_choice.match(line)
                if m_choice:
                    text = m_choice.group(1)
                    cond = m_choice.group(2) or "True"
                    current_menu["options"].append({"text": text, "condition": cond, "line": idx})
                    continue

            # Check jump
            m_jump = self.re_jump.match(line)
            if m_jump:
                target = m_jump.group(1)
                labels[current_label]["jumps"].append(target)
                if "game_over" in target.lower() or "bad_end" in target.lower():
                    labels[current_label]["game_over_risk"] = True
                continue

            # Check call
            m_call = self.re_call.match(line)
            if m_call:
                labels[current_label]["calls"].append(m_call.group(1))
                continue

            # Check python variable mutation
            m_var = self.re_var_set.match(line)
            if m_var:
                labels[current_label]["flag_changes"].append(m_var.group(1).strip())

        return labels


def scan_game_routes(game_dir: Path) -> dict:
    analyzer = RouteAnalyzer()
    game_path = game_dir / "game" if (game_dir / "game").is_dir() else game_dir
    rpy_files = list(game_path.glob("*.rpy"))

    all_routes = {}
    for f in rpy_files:
        if "tl" in f.parts:
            continue
        res = analyzer.analyze_file(f)
        all_routes.update(res)

    return all_routes


def main():
    parser = argparse.ArgumentParser(description="Extract Ren'Py decision trees and route logic for walkthroughs.")
    parser.add_argument("path", help="Ren'Py game path or .rpy file")
    parser.add_argument("--out", "-o", default="renpy_route_tree.json", help="Output JSON path")
    args = parser.parse_args()

    target = Path(args.path).resolve()
    if not target.exists():
        print(f"❌ Error: Not found: {target}")
        sys.exit(1)

    print(f"🔍 Analyzing route logic in: {target}...")
    if target.is_file():
        analyzer = RouteAnalyzer()
        routes = analyzer.analyze_file(target)
    else:
        routes = scan_game_routes(target)

    out_file = Path(args.out).resolve()
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(routes, f, indent=2, ensure_ascii=False)

    total_choices = sum(len(l["choices"]) for l in routes.values())
    game_over_nodes = [k for k, l in routes.items() if l["game_over_risk"]]

    print("=" * 65)
    print("📊 REN'PY ROUTE LOGIC ANALYSIS COMPLETE")
    print(f"📁 Target: {target}")
    print(f"🏷️ Total Labels Mapped: {len(routes)}")
    print(f"📋 Interactive Menus Detected: {total_choices}")
    print(f"⚠️ Game Over / Trap Labels Identified: {len(game_over_nodes)}")
    if game_over_nodes:
        print(f"   Traps: {', '.join(game_over_nodes[:8])}...")
    print(f"💾 Full Route Tree Saved: {out_file}")
    print("=" * 65)


if __name__ == "__main__":
    main()
