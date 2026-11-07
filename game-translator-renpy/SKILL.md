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
      ├──> Step 2: Extract Strings, Dynamic Lists & Speech Bubbles (`extract_python_strings.py`)
      ├──> Step 3: Audit Fonts & Fix Tofu Boxes (`audit_fonts.py` & font override)
      ├──> Step 4: Generate Vietnamese tl Framework (`generate_tl_framework.py`)
      ├──> Step 5: Parallel Chunk Translation via Subagents (Mandatory)
      ├──> Step 6: Dynamic Speech Bubble & In-Memory Hooks (`templates/dynamic_bubbles_patch.rpy`)
      ├──> Step 7: Bypass Patreon / Gallery Code Gates (`references/patreon_gallery_unlock_guide.md`)
      ├──> Step 8: Comprehensive Dialogue Coverage Audit (`audit_dialogue_coverage.py`)
      └──> Step 9: Syntax Validation & Bytecode Compilation (`verify_renpy_syntax.py`)
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

### Step 3: Deep Extract Strings & Dynamic Text
Run the deep AST scanner to collect dialogue, menu options, notifications, speech bubbles, and Python dictionary/list entries:
```bash
python game-translator-renpy/scripts/extract_python_strings.py "<GAME_PATH>/game" --out "<GAME_PATH>/renpy_extracted_strings.json"
```

### Step 4: Setup Vietnamese Framework
Initialize `game/tl/vietnamese/` and the live language toggle:
```bash
python game-translator-renpy/scripts/generate_tl_framework.py "<GAME_PATH>"
```

### Step 5: Translate via Parallel Subagents (MANDATORY)
- **BẮT BUỘC**: Chia nhỏ các file lớn thành batch 200–500 chuỗi và gọi `invoke_subagent` để dịch song song. Tuyệt đối không dịch một mình tuần tự trong luồng chat chính.
- Đảm bảo định dạng chuẩn đa dòng (multi-line), không bao giờ xuất file bị gộp thành 1 dòng chứa ký tự escaped `\n`.
- Tuân thủ nghiêm ngặt [renpy_translation_rules.md](file:///d:/Development/Projects/game-translator-skills/game-translator-renpy/references/renpy_translation_rules.md).

### Step 6: Dynamic Speech Bubbles & In-Memory Hooks
Nếu game có các câu thoại bong bóng (speech bubbles), phản ứng ngẫu nhiên (`WOMAN_TALK`, `FLAVOR`), hoặc thông báo không qua lệnh `say`:
- Thêm [dynamic_bubbles_patch.rpy](file:///d:/Development/Projects/game-translator-skills/game-translator-renpy/templates/dynamic_bubbles_patch.rpy) vào `game/`.
- Đăng ký toàn bộ chuỗi động vào `game/tl/vietnamese/dynamic_dialogues.rpy` dưới dạng `translate vietnamese strings:`.

### Step 7: Handle Patreon & Gallery Locks
Nếu game có mã khóa Patreon / Gallery (ví dụ kiểm tra SHA256 + Salt trong `patreon_gate.rpy`):
- Tham khảo [patreon_gallery_unlock_guide.md](file:///d:/Development/Projects/game-translator-skills/game-translator-renpy/references/patreon_gallery_unlock_guide.md).
- Thêm danh sách mã vạn năng (`UNLOCK`, `ALL`, `BETA`) hoặc nạp patch tự động mở khóa để phục vụ tester kiểm tra toàn bộ CG / H-scene.

### Step 8: Comprehensive Dialogue Coverage Audit
Trước khi bàn giao, BẮT BUỘC chạy công cụ kiểm định độ phủ để đảm bảo không sót câu thoại nào:
```bash
python game-translator-renpy/scripts/audit_dialogue_coverage.py "<GAME_PATH>"
```
Nếu bất kỳ tệp kịch bản nào có độ phủ < 95% hoặc bị đánh dấu `CORRUPTED FORMAT`, lập tức khắc phục trước khi báo cáo hoàn tất.

### Step 9: Compile & Verify
Lint cú pháp và biên dịch kịch bản sang `.rpyc`:
```bash
python game-translator-renpy/scripts/verify_renpy_syntax.py "<GAME_PATH>/game" --compile
```

