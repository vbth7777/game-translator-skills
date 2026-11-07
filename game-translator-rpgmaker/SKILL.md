---
name: game-translator-rpgmaker
description: Specialized game translation skill for RPG Maker MV, MZ, VX Ace, and XP engines. Deep-extracts JSON databases, maps, and common events, preserves control codes (\N[n], \V[n]), synthesizes long-context lorebooks with multi-phase pronoun rules, detects scene moods (H-scenes, combat, drama), and performs parallel batch translation via subagents.
---

# RPG Maker Game Translator Sub-Skill

This sub-skill provides a complete, battle-tested, end-to-end pipeline for localizing RPG Maker games (MV, MZ, VX Ace, XP) into Vietnamese with human-grade quality, engine integrity, and zero machine translation awkwardness.

Modeled directly on the proven architecture of `rpg-translate`, this skill gives Antigravity the exact contextual superpowers—**Omniscient Lorebook, Multi-Phase Pairwise Pronoun Rules, Facial Expression Analysis, Scene Mood Detection, and Semantic Chunking**—with the agent and parallel subagents performing the translation directly.

---

## 1. Pipeline Overview

```
[Target RPG Maker Game Folder]
       │
       ├──> Step 1: Deep Data & Dialogue Extraction (`extract_rpgmaker.py`)
       │            - Aggregates consecutive 401 Show Text into multi-line paragraphs
       │            - Extracts speaker, face expression (0-7), and scene coordinates
       │
       ├──> Step 2: Build Lorebook & Context (`build_lorebook_context.py`)
       │            - Generates character matrix & actor escape code map (\N[1])
       │            - Builds Pairwise Pronoun Rules with Multi-Phase States
       │            - Sets Scoped Glossary & Soft-Constraint Directives
       │
       ├──> Step 3: Semantic Scene Slicing (`slice_rpgmaker_batches.py`)
       │            - Groups entries by narrative scene boundaries (not arbitrary numbers)
       │            - Detects Scene Mood (H-Scene / Combat / Drama / General)
       │            - Resolves active characters, pronouns, glossary & sliding window
       │
       ├──> Step 4: Parallel Subagent Translation (Mandatory Protocol)
       │            - Dispatches parallel `game-chunk-translator` subagents
       │
       ├──> Step 5: Compile Batches (`compile_rpgmaker_batches.py`)
       │            - Combines translated chunks into `translation_vietnamese.json`
       │
       ├──> Step 6: Safe Injection & 401 Code Rebuild (`inject_rpgmaker.py`)
       │            - Auto-backup of pristine game data to `data_original_backup/`
       │            - Splits dialogue back into 401 Show Text codes with matching indent
       │            - Injects 102 Show Choices & database terms via dot-paths
       │            - Restores escape codes & XML tags
       │
       ├──> Step 7: Auto Word Wrap Plugin Setup (`install_wordwrap_plugin.py`)
       │            - Injects `AutoWordWrap.js` and registers in `plugins.js`
       │            - Auto-measures pixel width & shrinks font if > 4 lines
       │
       └──> Step 8: Quality Control & 100% Coverage Audit (`audit_rpgmaker_coverage.py`)
                    - Verifies 1-1 coverage %, tag parity, and checks for untranslated leaks
```

---

## 2. Step-by-Step Execution Guide

### Step 1: Deep Extraction
Extract all dialogue, choices, and database entries:
```bash
python game-translator-rpgmaker/scripts/extract_rpgmaker.py "<PATH_TO_GAME>"
```
- Outputs `<GAME_DIR>/translation_source.json` (dialogue & terms).
- Outputs `<GAME_DIR>/translation_metadata.json` (speaker, scene, face expression index).

### Step 2: Build Lorebook & Persona Matrix
Synthesize character profiles and multi-phase pairwise pronoun rules:
```bash
python game-translator-rpgmaker/scripts/build_lorebook_context.py "<PATH_TO_GAME>"
```
- Outputs `<GAME_DIR>/LOREBOOK.json`.
- Tra cứu mã nhân vật `\N[1]`, `\N[2]` và thiết lập xưng hô đôi với các giai đoạn tâm lý (`phases`: Mặc định, Hắc hóa/Biến chất, Tình nhân).

### Step 3: Semantic Chunking & Batch Slicing
Group dialogue into coherent narrative scenes with rich context:
```bash
python game-translator-rpgmaker/scripts/slice_rpgmaker_batches.py "<PATH_TO_GAME>" --batch-size 40
```
- Creates `<GAME_DIR>/batches/batch_001.json`, `batch_002.json`, ...
- Each batch file includes:
  * `mood`: Scene mood detection (`erotic_18+`, `combat_action`, `dramatic_tragic`, `general`).
  * `escape_codes_reference`: Table cross-referencing `\N[X]` to character names.
  * `active_context`: Active characters, pairwise pronoun rules, and active glossary terms.
  * `previous_context`: Sliding window of previous dialogue for emotional momentum.
  * `formatted_prompt`: Ready-to-run prompt for subagent translation.

### Step 4: Parallel Subagent Translation (MANDATORY)

> [!IMPORTANT]
> **MANDATORY SUBAGENT PROTOCOL (BẮT BUỘC SỬ DỤNG SUBAGENTS)**:
> Tuyệt đối **KHÔNG ĐƯỢC** dịch tuần tự toàn bộ kịch bản game trong một luồng chat chính.
> Hãy gọi `invoke_subagent` để phân chia các file batch trong `<GAME_DIR>/batches/` cho các subagent `game-chunk-translator` xử lý đồng thời song song.

Ví dụ lời gọi:
```json
{
  "TypeName": "game-chunk-translator",
  "Role": "RPG Maker Senior Dialogue Localizer",
  "Prompt": "Dịch tệp batch kịch bản: <GAME_DIR>/batches/batch_001.json. Đọc kỹ mood_directive, escape_codes_reference, active_context. Giữ nguyên 100% các mã \\V[n], \\N[n], \\C[n]. Tuân thủ Anti-Sanitization Directive đối với phân cảnh 18+/rên rỉ. Ghi bản dịch vào <GAME_DIR>/batches/batch_001_translated.json."
}
```

### Step 5: Compile Batches
Sau khi các subagent hoàn tất, gộp toàn bộ bản dịch vào một tệp duy nhất:
```bash
python game-translator-rpgmaker/scripts/compile_rpgmaker_batches.py "<GAME_DIR>/batches" --source "<GAME_DIR>/translation_source.json"
```
- Tạo tệp `<GAME_DIR>/translation_vietnamese.json`.

### Step 6: Safe Injection & 401 Command Rebuild
Nhúng bản dịch vào các tệp JSON của RPG Maker:
```bash
python game-translator-rpgmaker/scripts/inject_rpgmaker.py "<GAME_DIR>" "<GAME_DIR>/translation_vietnamese.json" --wrap 50
```
- Tự động tạo bản sao lưu nguyên bản tại `<GAME_DIR>/data_original_backup/`.
- Tách các câu thoại nhiều dòng trở lại thành chuỗi các lệnh mã `401` với thụt lề chuẩn.
- Cập nhật các lựa chọn `102` và các mục database qua đường dẫn chấm (`set_by_path`).
- Tự động khôi phục các mã điều khiển `\V[n]`, `\N[n]`, `\C[n]`, `\I[n]` và thẻ `<...>`.

### Step 7: Auto Word Wrap Plugin Setup
Để tránh hiện tượng câu thoại tiếng Việt bị tràn khung hộp thoại hoặc bị mất chữ:
```bash
python game-translator-rpgmaker/scripts/install_wordwrap_plugin.py "<GAME_DIR>"
```
- Tự động copy `AutoWordWrap.js` vào thư mục plugin của game.
- Đăng ký và kích hoạt plugin trong `plugins.js` mà không gây xung đột với các plugin hiện có (Yanfly, VisuStella, v.v.).

### Step 8: Quality Control & Coverage Audit
Trước khi bàn giao cho người dùng, BẮT BUỘC chạy công cụ kiểm định chất lượng:
```bash
python game-translator-rpgmaker/scripts/audit_rpgmaker_coverage.py "<GAME_DIR>/translation_source.json" "<GAME_DIR>/translation_vietnamese.json"
```
- Kiểm tra độ phủ 1-1 giữa bản gốc và bản dịch (yêu cầu đạt >= 95%).
- Phát hiện các câu sót tiếng Anh hoặc còn vướng ký tự tiếng Nhật/Trung (CJK leaks).
- Kiểm tra tính tương ứng của các mã điều khiển (`\N[n]`, `\V[n]`, `\C[n]`).

---

## 3. Sub-Skill References
- [rpgmaker_architecture_guide.md](file:///d:/Development/Projects/game-translator-skills/game-translator-rpgmaker/references/rpgmaker_architecture_guide.md): Cấu trúc engine MV/MZ/VX Ace/XP, danh sách mã lệnh 101, 102, 401, 405.
- [rpgmaker_escape_codes_guide.md](file:///d:/Development/Projects/game-translator-skills/game-translator-rpgmaker/references/rpgmaker_escape_codes_guide.md): Bảng tra cứu toàn diện các mã điều khiển trong hộp thoại.
- [h_scene_and_moan_rules.md](file:///d:/Development/Projects/game-translator-skills/game-translator-rpgmaker/references/h_scene_and_moan_rules.md): Quy tắc dịch phân cảnh 18+, dirty talk, tiếng rên rỉ (moan) và âm thanh bú mút theo chuẩn Anti-Sanitization.
- [rpgmaker_subagent_prompts.md](file:///d:/Development/Projects/game-translator-skills/game-translator-rpgmaker/references/rpgmaker_subagent_prompts.md): Prompts mẫu chuẩn xác cho các subagents điều phối.
