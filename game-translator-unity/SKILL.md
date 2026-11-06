---
name: game-translator-unity
description: Specialized game translation sub-skill for Unity Engine games (Mono & IL2CPP 64-bit). Handles architecture detection, BepInEx 5/6 hooking, TextMeshPro fallback fonts, chunk slicing for parallel subagents, TSV review workflows, and rich text tag validation.
---

# Unity Game Translator Sub-Skill

This sub-skill provides a complete pipeline for translating Unity games (both Mono .NET and IL2CPP 64-bit native) into Vietnamese (or any target language) with human-grade quality and engine-level integrity.

## 1. Pipeline Overview

```
[Unity Game Root]
       │
       ├──> Step 1: Profile Architecture (`detect_unity_type.py`)
       ├──> Step 2: Extract & Dump Text Assets (`extract_unity_strings.py`)
       ├──> Step 3: Slice Dictionaries for Subagents (`slice_and_batch.py`)
       ├──> Step 4: Parallel Chunk Translation via Subagents
       ├──> Step 5: Merge & Compile Translations (`compile_unity_dictionaries.py`)
       ├──> Step 6: TSV Review & Bulk Refinement (`export_tsv_editor.py`)
       ├──> Step 7: TextMeshPro Rich Text & Tag Audit (`verify_unity_rich_text.py`)
       └──> Step 8: BepInEx Hook Injection & Launch Verification
```

---

## 2. Step-by-Step Execution Guide

### Step 1: Detect Architecture (Mono vs IL2CPP)
```bash
python game-translator-unity/scripts/detect_unity_type.py "<GAME_PATH>"
```
- If **IL2CPP**: Use BepInEx 6 IL2CPP + Detour Plugin hooking `TMP_Text.set_text`.
- If **Mono**: Use BepInEx 5 or modify assemblies / AssetBundles.

### Step 2: Slice Dictionaries for Parallel Translation
To prevent subagent context overloading and accelerate speed, slice large JSON dictionaries:
```bash
python game-translator-unity/scripts/slice_and_batch.py "<GAME_PATH>/raw_dialogue.json" --size 250 --out "<GAME_PATH>/chunks"
```

### Step 3: Dispatch Subagents
- Allocate chunk files to worker subagents.
- Ensure all Rich Text tags (`<color>`, `<size>`, `<sprite>`, `<voffset>`) are strictly retained.

### Step 4: Compile & Merge Chunks
```bash
python game-translator-unity/scripts/compile_unity_dictionaries.py "<GAME_PATH>/chunks" --out "<GAME_PATH>/BepInEx/plugins/GameTranslation/translations/dialogue.json"
```

### Step 5: Export / Import TSV for Review
Allows offline bulk review in Excel or Notepad++:
```bash
# Export to TSV
python game-translator-unity/scripts/export_tsv_editor.py export "<GAME_PATH>/translations/dialogue.json" "<GAME_PATH>/Dialogue_Review.tsv"

# Import edited TSV back
python game-translator-unity/scripts/export_tsv_editor.py import "<GAME_PATH>/Dialogue_Review.tsv" "<GAME_PATH>/translations/dialogue.json"
```

### Step 6: Audit Rich Text Tags
Verify that no closing tags were dropped and sprite IDs match:
```bash
python game-translator-unity/scripts/verify_unity_rich_text.py "<GAME_PATH>/translations/dialogue.json"
```

