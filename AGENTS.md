# AGENTS.md - Game Translator Skills Project Memory & Knowledge Store

## 1. Project Overview & Mission
- **Project**: Game Translator Skills (`game-translator-skills`)
- **Location**: `d:\Development\Projects\game-translator-skills`
- **Goal**: Build an extensible, enterprise-grade AI skill system for translating video games into Vietnamese (and other target languages) with human-grade quality, engine-specific deep hooks, and end-to-end automation via specialized subagents.
- **Initial Engines**:
  1. **Ren'Py Engine** (Visual Novels, Ren'Py 7/8, Python 2/3, RPA archives, RPYC AST, Live2D, Python in-memory dictionaries).
  2. **Unity Engine** (Mono & IL2CPP 64-bit, TextMeshPro, UGUI, BepInEx 5/6, MelonLoader, XUnity.AutoTranslator, UnityPy, AssetStudio, JSON/TSV hooks).

---

## 2. Core Pillars & Localization Quality Standards
1. **STRICT HUMAN-GRADE TRANSLATION**:
   - Zero tolerance for dry machine translation (Google Translate / DeepL / Bing style literal word-by-word conversion).
   - Natural, lively, genre-fitting Vietnamese localization (detective suspense, fantasy RPG, anime visual novel, slice of life, or eroge).
   - **Tone Preservation & Anti-Sanitization**: Respect original author intent, characters' personality, slang, swearing, and adult/eroge vocabulary without euphemistic censorship (preserve raw intensity where appropriate, no awkward medical/Hán-Việt convert slop).
2. **Context & Lore Primacy**:
   - Always conduct proactive web/wiki reconnaissance (Google, VNDB, Steam, Fandom, F95zone) before translating to map character personalities, relationships, pronouns, and universe lore.
3. **Subagent Orchestration**:
   - Parallel execution across modular subagents: Orchestrator, Lore Researcher, String Extractor, Glossary Curator, Chunk Translators, Quality Linter / Reviewer, Graphic Asset Localizer, and Engine Re-packer.
4. **Technical Engine Integrity**:
   - 100% preservation of escape tags (`{b}`, `{color}`, `[var]`, `<sprite=0>`, `<voffset>`).
   - Font Tofu (`[?]`) Zero-Tolerance: Unicode Vietnamese diacritics audit and font fallback patching.
   - Transparent canvas and alpha preservation in image asset editing.

---

## 3. Reference Case Studies
- **Unity Benchmark**: `C:\Users\ADMIN\Downloads\Compressed\CIRCLEMATE-ENG - Copy` (Unity 6000.3.5f2 IL2CPP, BepInEx 6, custom hooks, 2,843 dialogue/UI entries, image localization, TSV review workflow).
- **Ren'Py Benchmark**: `C:\Users\ADMIN\Downloads\Compressed\PAWGVERSE-0.05.22-pc\PAWGVERSE-0.05.22-pc` (Ren'Py 8.5.2, 1,998 dialogue blocks + 5,100 UI/notification/menu strings, Python dict Live2D patch, font tofu resolution, 41 transparent PNG graphic assets).

---

## 4. Architecture & Directory Map
- `game-translator/`: Master router and pipeline orchestrator.
  - `SKILL.md`: Main entrypoint for agent dispatch.
  - `scripts/detect_engine.py`: Engine classifier (Ren'Py, Unity, RPG Maker, Godot, Unreal).
  - `scripts/search_game_lore.py`: Reconnaissance queries & lore builder.
  - `references/subagent_prompts.md`: Prompts and specs for 7 subagent roles.
  - `references/engine_fingerprints.md`: Architecture signatures.
- `game-translator-renpy/`: Ren'Py specialized engine skill.
  - `SKILL.md`: Ren'Py translation guide and sub-skill entrypoint.
  - `scripts/extract_rpa.py`: Pure-Python RPA 2.0/3.0 archive extractor.
  - `scripts/extract_python_strings.py`: AST scanner for screen UI, buttons, dictionaries, and notifications.
  - `scripts/audit_fonts.py`: Font tofu box auditor (146 Vietnamese Unicode glyphs).
  - `scripts/generate_tl_framework.py`: Injects `tl/vietnamese`, default language config, and language toggle screen.
  - `scripts/verify_renpy_syntax.py`: Ren'Py syntax linter and bytecode compilation runner.
  - `templates/live_language_toggle.rpy`: Real-time Vietnamese/English switcher.
  - `templates/memory_patch_template.rpy`: In-memory monkey-patch for persistent dictionaries.
  - `references/font_tofu_guide.md`: Tofu box resolution guide.
  - `references/renpy_translation_rules.md`: Tag and syntax specifications.
- `game-translator-unity/`: Unity specialized engine skill.
  - `SKILL.md`: Unity translation guide and sub-skill entrypoint.
  - `scripts/detect_unity_type.py`: Mono vs IL2CPP profiler.
  - `scripts/slice_and_batch.py`: Splits large JSON dictionaries for parallel subagents.
  - `scripts/compile_unity_dictionaries.py`: Merges translated chunks.
  - `scripts/export_tsv_editor.py`: Bidirectional JSON <-> TSV converter for spreadsheet review.
  - `scripts/verify_unity_rich_text.py`: TextMeshPro rich text and sprite tag parity linter.
  - `templates/TranslationPlugin_Template/Plugin.cs`: C# BepInEx hook template.
  - `references/unity_il2cpp_hooking.md`: C# Harmony detours guide.
  - `references/tmp_font_fallback_guide.md`: TextMeshPro SDF fallback font setup.
- `shared/`: Shared tools across all engines.
  - `scripts/glossary_builder.py`: Multi-category glossary manager.
  - `scripts/image_supersampling_inpaint.py`: 4x supersampled UI banner/button inpainter.
  - `scripts/linter_qc.py`: Universal placeholder, tag, and untranslated leak detector.
  - `assets/fonts/`: Standard Unicode fonts (`OpenSans_SemiCondensed`, `RobotoMono`).

---

## 5. Verification Status & Test Benchmarks
- Engine detection: Tested on `PAWGVERSE` (Ren'Py 3, 99% confidence) and `CIRCLEMATE` (Unity IL2CPP 64-bit, 99% confidence).
- Font auditing: Verified against 4 failing fonts (`CC Wild Words`, `HPSimplified`, `GenEiKiwamiGo`, `Franklin Gothic`) and passed with `OpenSans` and `RobotoMono`.
- Unity rich text linter: Audited 2,397 entries in `CIRCLEMATE` dialogue and 10 misc entries with 100% precision.
- Universal QC linter: Audited 2,397 entries in `CIRCLEMATE` dialogue with 0 variable mismatches.
