#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Game Lore & Universe Context Builder
Generates queries and creates structured LORE_CONTEXT.json for localizers.
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


def generate_recon_queries(game_title: str, genre: str = "visual novel") -> list[str]:
    """Generates high-yield web reconnaissance queries for game lore."""
    queries = [
        f'"{game_title}" wiki characters',
        f'"{game_title}" fandom plot summary',
        f'"{game_title}" VNDB',
        f'"{game_title}" character relationships dialogue style',
        f'"{game_title}" walkthrough guide',
        f'"{game_title}" terms lore concepts'
    ]
    return queries


def create_lore_template(game_title: str, output_path: Path) -> dict:
    """Creates a blank/starter LORE_CONTEXT.json template."""
    template = {
        "game_title": game_title,
        "universe_summary": "Tóm tắt bối cảnh thế giới của game...",
        "tone_and_style": {
            "genre": "Visual Novel / RPG",
            "atmosphere": "Kịch tính, trinh thám, hài hước, hoặc eroge trưởng thành...",
            "anti_sanitization_rules": "Tuyệt đối bảo tồn tính cách nhân vật, lời chửi thề, tiếng lóng, và ngôn ngữ 18+ nguyên bản; tránh văn phong y khoa/convert sáo rỗng."
        },
        "character_matrix": [
            {
                "id": "char_01",
                "original_name": "Tên gốc",
                "vietnamese_name": "Tên tiếng Việt hiển thị",
                "personality": "Tính cách (kiêu kỳ, lạnh lùng, lả lơi, chính trực...)",
                "relationship_to_protagonist": "Quan hệ với người chơi",
                "pronouns_to_protagonist": "Cặp xưng hô (ví dụ: tôi - cậu / ta - ngươi / em - anh)"
            }
        ],
        "locked_glossary": {
            "locations": {},
            "skills_and_items": {},
            "organizations_and_factions": {}
        }
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    return template


def main():
    parser = argparse.ArgumentParser(description="Generate search queries and template for game lore.")
    parser.add_argument("title", help="Game title to research")
    parser.add_argument("--out", default="LORE_CONTEXT.json", help="Output path for LORE_CONTEXT.json")
    parser.add_argument("--queries-only", action="store_true", help="Print search queries only")
    args = parser.parse_args()

    queries = generate_recon_queries(args.title)

    if args.queries_only:
        print(f"🔍 Recommended search queries for '{args.title}':")
        for q in queries:
            print(f"  - {q}")
        return

    out_file = Path(args.out).resolve()
    if not out_file.exists():
        create_lore_template(args.title, out_file)
        print(f"✨ Created lore context template at: {out_file}")
    else:
        print(f"ℹ️ Lore file already exists at: {out_file}")

    print(f"\n🔍 Recommended web research queries for '{args.title}':")
    for q in queries:
        print(f"  - {q}")


if __name__ == "__main__":
    main()

