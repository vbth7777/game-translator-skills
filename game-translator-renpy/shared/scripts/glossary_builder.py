#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared Project Glossary & Terminology Manager
Maintains consistent proper nouns, character names, and locked terms across subagents.
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


class GlossaryManager:
    def __init__(self, glossary_path: Path):
        self.path = glossary_path
        self.data = self._load()

    def _load(self) -> dict:
        if self.path.is_file():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"character_names": {}, "locations": {}, "items_and_skills": {}, "locked_terms": {}}

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def add_term(self, category: str, original: str, vietnamese: str):
        if category not in self.data:
            self.data[category] = {}
        self.data[category][original] = vietnamese
        self.save()

    def check_text(self, text: str) -> list[dict]:
        """Checks if any original term appears where it should have been translated."""
        warnings = []
        for cat, terms in self.data.items():
            for orig, vi in terms.items():
                if orig.lower() in text.lower() and vi.lower() not in text.lower():
                    warnings.append({
                        "category": cat,
                        "untranslated_term": orig,
                        "expected_translation": vi
                    })
        return warnings


def main():
    parser = argparse.ArgumentParser(description="Manage translation glossary.")
    parser.add_argument("--glossary", "-g", default="GLOSSARY.json", help="Path to GLOSSARY.json")
    parser.add_argument("--add", nargs=3, metavar=("CATEGORY", "ORIGINAL", "VIETNAMESE"), help="Add a term")
    parser.add_argument("--list", "-l", action="store_true", help="List all terms")
    args = parser.parse_args()

    gm = GlossaryManager(Path(args.glossary).resolve())

    if args.add:
        cat, orig, vi = args.add
        gm.add_term(cat, orig, vi)
        print(f"✅ Added to [{cat}]: '{orig}' -> '{vi}'")
        return

    if args.list:
        print("=" * 60)
        print(f"📚 GLOSSARY ENTRIES ({args.glossary})")
        print("=" * 60)
        for cat, terms in gm.data.items():
            print(f"\n📂 [{cat.upper()}] ({len(terms)} items):")
            for o, v in terms.items():
                print(f"   • {o} -> {v}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()

