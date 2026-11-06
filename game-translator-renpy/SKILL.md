---
name: game-translator-renpy
description: Specialized game translation sub-skill for Ren'Py Visual Novels and RPGs. Handles RPA archive extraction, AST and Python in-memory string extraction, font tofu box resolution, Vietnamese tl layer generation, and bytecode compilation.
---

# Ren'Py Game Translator Sub-Skill

This sub-skill provides a complete, battle-tested pipeline for localizing Ren'Py visual novels and RPGs into Vietnamese (or any target language).

## 1. Pipeline Overview

```
[Ren'Py Game Root]
      │
      ├──> Step 1: Extract RPA Archives (`extract_rpa.py`)
      ├──> Step 2: Extract Strings & Python Dictionaries (`extract_python_strings.py`)
      ├──> Step 3: Audit Fonts & Fix Tofu Boxes (`audit_fonts.py` & font override)
      ├──> Step 4: Generate Vietnamese tl Framework (`generate_tl_framework.py`)
      ├──> Step 5: Parallel Chunk Translation via Subagents
      ├──> Step 6: In-Memory Monkey-Patching for Dynamic Text (`templates/memory_patch_template.rpy`)
      └──> Step 7: Syntax Validation & Bytecode Compilation (`verify_renpy_syntax.py`)
```

---

## 2. Step-by-Step Execution Guide

### Step 1: Extract RPA Archives
If dialogue, scripts, or fonts are packed inside `game/*.rpa`:
```bash
python game-translator-renpy/scripts/extract_rpa.py "<GAME_PATH>/game/archive.rpa" --out "<GAME_PATH>/scratch" --pattern "*.rpyc"
```

### Step 2: Audit & Fix Font Tofu
1. Scan extracted fonts:
   ```bash
   python game-translator-renpy/scripts/audit_fonts.py "<GAME_PATH>/scratch/fonts"
   ```
2. For any font missing Vietnamese glyphs, copy a complete Unicode font (e.g. `DejaVuSans.ttf`, `OpenSans`, or `Segoe UI`) into `<GAME_PATH>/game/fonts/` matching the original filename. See [font_tofu_guide.md](file:///d:/Development/Projects/game-translator-skills/game-translator-renpy/references/font_tofu_guide.md).

### Step 3: Extract Translatable Strings
Run the deep AST scanner to collect dialogue, menu options, notifications, and Python dictionary entries:
```bash
python game-translator-renpy/scripts/extract_python_strings.py "<GAME_PATH>/game" --out "<GAME_PATH>/renpy_extracted_strings.json"
```

### Step 4: Setup Vietnamese Framework
Initialize `game/tl/vietnamese/` and the live language toggle:
```bash
python game-translator-renpy/scripts/generate_tl_framework.py "<GAME_PATH>"
```

### Step 5: Translate via Parallel Subagents
- Dispatch batches of 200–500 strings to `game-chunk-translator` subagents.
- Ensure strict adherence to [renpy_translation_rules.md](file:///d:/Development/Projects/game-translator-skills/game-translator-renpy/references/renpy_translation_rules.md).

### Step 6: Compile & Verify
Lint translation files and compile into `.rpyc`:
```bash
python game-translator-renpy/scripts/verify_renpy_syntax.py "<GAME_PATH>/game" --compile
```

