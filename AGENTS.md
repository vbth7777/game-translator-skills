# AGENTS.md - Game Translator Skills Project Memory & Knowledge Store

## 1. Project Overview & Mission
- **Project**: Game Translator Skills (`game-translator-skills`)
- **Location**: `d:\Development\Projects\game-translator-skills`
- **GitHub Repository**: https://github.com/vbth7777/game-translator-skills
- **Goal**: Build an extensible, enterprise-grade AI skill system for translating video games into Vietnamese (and other target languages) with human-grade quality, engine-specific deep hooks, and end-to-end automation via specialized subagents.
- **Initial Engines**:
  1. **Ren'Py Engine** (Visual Novels, Ren'Py 7/8, Python 2/3, RPA archives, RPYC AST, Live2D, Python in-memory dictionaries, dynamic speech bubbles).
  2. **Unity Engine** (Mono & IL2CPP 64-bit, TextMeshPro, UGUI, BepInEx 5/6, MelonLoader, XUnity.AutoTranslator, UnityPy, AssetStudio, JSON/TSV hooks).

---

## 2. Core Pillars & Localization Quality Standards
1. **STRICT HUMAN-GRADE TRANSLATION**:
   - Zero tolerance for dry machine translation (Google Translate / DeepL / Bing style literal word-by-word conversion).
   - Natural, lively, genre-fitting Vietnamese localization (detective suspense, fantasy RPG, anime visual novel, slice of life, or eroge).
   - **Tone Preservation & Anti-Sanitization**: Respect original author intent, characters' personality, slang, swearing, and adult/eroge vocabulary without euphemistic censorship (preserve raw intensity where appropriate, no awkward medical/Hán-Việt convert slop).
2. **Context & Lore Primacy**:
   - Always conduct proactive web/wiki reconnaissance (Google, VNDB, Steam, Fandom, F95zone) before translating to map character personalities, relationships, pronouns, and universe lore.
3. **MANDATORY SUBAGENT ENFORCEMENT PROTOCOL**:
   - BẮT BUỘC sử dụng Subagents (`invoke_subagent`): Nghiêm cấm Agent tự dịch tuần tự (single-threaded) trong một luồng chat chính nếu dự án có trên 100 câu thoại hoặc nhiều tệp. Phải phân chia batch (200–500 câu) và giao việc song song cho `game-chunk-translator`, `game-lore-researcher`, `game-qc-linter`.
4. **Technical Engine Integrity**:
   - 100% preservation of escape tags (`{b}`, `{color}`, `[var]`, `<sprite=0>`, `<voffset>`).
   - Font Tofu (`[?]`) Zero-Tolerance: Unicode Vietnamese diacritics audit and font fallback patching.
   - Transparent canvas and alpha preservation in image asset editing.
5. **Coverage Audit Requirement**:
   - BẮT BUỘC chạy `audit_dialogue_coverage.py` trước khi báo cáo hoàn thành. Đảm bảo 100% tệp kịch bản đạt độ phủ và không có tệp nào bị lỗi định dạng (single-line escaped string).

---

## 3. Reference Case Studies & Hard Lessons Learned
- **Unity Benchmark**: `C:\Users\ADMIN\Downloads\Compressed\CIRCLEMATE-ENG - Copy` (Unity 6000.3.5f2 IL2CPP, BepInEx 6, custom hooks, 2,843 dialogue/UI entries, image localization, TSV review workflow).
- **Ren'Py Benchmark 1**: `C:\Users\ADMIN\Downloads\Compressed\PAWGVERSE-0.05.22-pc\PAWGVERSE-0.05.22-pc` (Ren'Py 8.5.2, 1,998 dialogue blocks + 5,100 UI/notification/menu strings, Python dict Live2D patch, font tofu resolution, 41 transparent PNG graphic assets).
- **Ren'Py Benchmark 2 (Session `7e42637f-0dbf-43d6-a898-8ca961edb805`)**: `c:\Users\ADMIN\Downloads\Compressed\NTR\Rebelliounv0.1-PC\Rebellioun-Patreon-v0.1-pc` (Ren'Py 8.3+, 1,088 dialogue blocks + 441 dynamic speech bubble strings):
  - *Sự cố 1 (Bỏ quên Subagents)*: Agent ban đầu dịch tuần tự một mình gây chậm trễ và sai lệch quy trình -> **Giải pháp**: Thiết lập giao thức bắt buộc gọi `invoke_subagent`.
  - *Sự cố 2 (Sót hội thoại tiếng Anh & Lỗi intro.rpy)*: Xuất tệp `intro.rpy` bị gộp thành 1 dòng chứa escaped `\n` khiến Ren'Py bỏ qua và fallback về tiếng Anh gốc -> **Giải pháp**: Viết `audit_dialogue_coverage.py` tự động phát hiện `CORRUPTED FORMAT` và đo chính xác % dòng thoại từng file.
  - *Sự cố 3 (Dynamic Speech Bubbles & Python Lists)*: Các câu thoại ngẫu nhiên (`WOMAN_TALK`, `_emit_talk_steps`, `add_notification`) không qua lệnh `say` thông thường -> **Giải pháp**: Nâng cấp `extract_python_strings.py` quét mảng chuỗi Python và cung cấp template `dynamic_bubbles_patch.rpy` móc hàm runtime vào `renpy.translation.translate_string()`.
  - *Sự cố 4 (Khóa mã Patreon / Gallery)*: Khóa SHA256 + Salt trong `patreon_gate.rpy` cản trở kiểm tra CG/H-scenes -> **Giải pháp**: Cung cấp cẩm nang `patreon_gallery_unlock_guide.md` với kỹ thuật inject mã vạn năng (`UNLOCK`, `ALL`, `BETA`) hoặc bypass gate.

---

## 4. Architecture & Directory Map
- `game-translator/`: Master router and pipeline orchestrator.
  - `SKILL.md`: Main entrypoint for agent dispatch & mandatory subagent rules.
  - `scripts/detect_engine.py`: Engine classifier (Ren'Py, Unity, RPG Maker, Godot, Unreal).
  - `scripts/search_game_lore.py`: Reconnaissance queries & lore builder.
  - `scripts/orchestrate_pipeline.py`: Master pipeline runner.
  - `references/subagent_prompts.md`: Prompts and specs for 7 subagent roles.
  - `references/engine_fingerprints.md`: Architecture signatures.
- `game-translator-renpy/`: Ren'Py specialized engine skill.
  - `SKILL.md`: Ren'Py translation guide and sub-skill entrypoint.
  - `scripts/extract_rpa.py`: Pure-Python RPA 2.0/3.0 archive extractor.
  - `scripts/extract_python_strings.py`: AST scanner for screen UI, buttons, dictionaries, dynamic lists, and speech bubbles.
  - `scripts/audit_dialogue_coverage.py`: So sánh độ phủ 1-1 giữa thoại gốc và thoại dịch, phát hiện lỗi định dạng.
  - `scripts/decompile_rpyc.py`: RPYC bytecode decompiler & heuristic string extractor.
  - `scripts/audit_fonts.py`: Font tofu box auditor (146 Vietnamese Unicode glyphs).
  - `scripts/generate_tl_framework.py`: Injects `tl/vietnamese`, default language config, and language toggle screen.
  - `scripts/verify_renpy_syntax.py`: Ren'Py syntax linter and bytecode compilation runner.
  - `templates/live_language_toggle.rpy`: Real-time Vietnamese/English switcher.
  - `templates/dynamic_bubbles_patch.rpy`: Runtime hook cho speech bubbles, flavor text, và notifications.
  - `templates/memory_patch_template.rpy`: In-memory monkey-patch for persistent dictionaries.
  - `references/font_tofu_guide.md`: Tofu box resolution guide.
  - `references/renpy_translation_rules.md`: Tag and syntax specifications.
  - `references/patreon_gallery_unlock_guide.md`: Hướng dẫn mở khóa Patreon gate & Gallery.
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

## 5. Deployment & Antigravity Global Installation
- **Global Skills Directory**: `C:\Users\ADMIN\.gemini\config\skills\`
  - `game-translator` -> `C:\Users\ADMIN\.gemini\config\skills\game-translator\`
  - `game-translator-renpy` -> `C:\Users\ADMIN\.gemini\config\skills\game-translator-renpy\`
  - `game-translator-unity` -> `C:\Users\ADMIN\.gemini\config\skills\game-translator-unity\`
- **GitHub Status**: Pushed to `https://github.com/vbth7777/game-translator-skills` (branch `master`).
