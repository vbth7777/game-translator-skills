---
name: renpy-walkthrough-guide
description: Specialized skill for generating authentic, visually rich playthrough walkthroughs and guidelines for Ren'Py games. Extracts route decision trees, generates in-game mockup screenshots, enforces mandatory QC subagent review, and exports both Markdown and interactive HTML guides.
---

# Ren'Py Walkthrough & Guideline Generator

This skill produces authentic, step-by-step in-game walkthroughs and guidelines for Ren'Py visual novels and RPGs, styled as if an expert player played through the game and captured real screenshots at every decision point.

## 1. Core Operating Principles

1. **Authentic In-Game Visuals**: Every step is accompanied by a faithful in-game screenshot showing the exact background, character sprite, textbox with translated dialogue, choice buttons, and coordinate pointers.
2. **Source-Code Backed Accuracy**: Routes, flags, and item dependencies are derived directly from the game's script AST (`.rpy` / `.rpyc`) to prevent missing prerequisite items or false paths.
3. **MANDATORY Quality Check Subagent Protocol**:
   - A dedicated **Quality Check Subagent (`walkthrough-qc-verifier`)** MUST inspect every generated screenshot and verify logic continuity before final delivery.
   - Zero tolerance for text overlapping, overflowing dialog boxes, misaligned character sprites, or broken image paths.
4. **Dual Format Delivery**: Always outputs both portable Markdown (`.md`) and interactive Linear-dark HTML (`.html`).

---

## 2. Step-by-Step Execution Workflow

```
[Target Game Folder]
        │
        ├──> Step 1: Extract Route Tree & Choices (`analyze_renpy_routes.py`)
        ├──> Step 2: Plan Sequential Step Architecture (Parts I, II, III...)
        ├──> Step 3: Render In-Game Mockup Screenshots (`generate_walkthrough_screens.py`)
        ├──> Step 4: Dispatch QC Subagent & Run Automated Audit (`audit_walkthrough_qc.py`)
        └──> Step 5: Export Markdown & Interactive HTML Guide (`export_html_walkthrough.py`)
```

---

## 3. Tool Commands & Usage

### Step 1: Analyze Route Logic & Traps
Extract decision trees, flags, and Game Over risks:
```bash
python renpy-walkthrough-guide/scripts/analyze_renpy_routes.py "<GAME_PATH>/game" --out "<OUT_DIR>/route_tree.json"
```

### Step 2: Generate Playthrough Screenshot Mockups
Render authentic in-game screens with auto line-wrapping:
```bash
python renpy-walkthrough-guide/scripts/generate_walkthrough_screens.py \
    --out "<OUT_DIR>/images/step_01.png" \
    --bg "<GAME_PATH>/game/images/bg/beach.png" \
    --title "BƯỚC 1: BÃI BIỂN PHÂN KHU 3" \
    --action "Tiếp cận Nami để nhận nhiệm vụ truy tìm kho báu" \
    --speaker "Miêu Tặc" \
    --dialogue "Chào cậu~ Cậu có nghe thấy tin đồn nào về kho báu bí mật giấu trên hòn đảo này không?" \
    --sprite "<GAME_PATH>/game/images/bust/nami/idle.png"
```

### Step 3: Quality Check Subagent Audit (MANDATORY)
Deploy the `walkthrough-qc-verifier` subagent and execute the automated QC engine:
```bash
python renpy-walkthrough-guide/scripts/audit_walkthrough_qc.py "<OUT_DIR>/walkthrough.md"
```
- Health Score must be >= 95/100.
- Check generated images for text collisions or sprite misplacement.

### Step 4: Export to Interactive HTML Guide
```bash
python renpy-walkthrough-guide/scripts/export_html_walkthrough.py "<OUT_DIR>/walkthrough.md" --out "<OUT_DIR>/walkthrough.html"
```

---

## 4. References & Guides

- [walkthrough_methodology.md](file:///d:/Development/Projects/game-translator-skills/renpy-walkthrough-guide/references/walkthrough_methodology.md): Core methodology and lessons learned.
- [qc_subagent_rubric.md](file:///d:/Development/Projects/game-translator-skills/renpy-walkthrough-guide/references/qc_subagent_rubric.md): Comprehensive rubric for the QC Subagent.
